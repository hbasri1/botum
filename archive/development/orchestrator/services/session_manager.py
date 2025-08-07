"""
Session Manager - Kullanıcı oturumlarını yönetir
Redis tabanlı session storage
"""

import redis.asyncio as redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.session_ttl = 3600 * 24  # 24 saat
    
    async def get_or_create_session(self, kullanici_id: str, isletme_id: str) -> str:
        """Kullanıcı için session ID oluştur veya mevcut olanı getir"""
        session_key = f"session:{isletme_id}:{kullanici_id}"
        
        # Mevcut session var mı kontrol et
        existing_session = await self.redis_client.get(session_key)
        
        if existing_session:
            session_data = json.loads(existing_session)
            session_id = session_data["session_id"]
            
            # TTL'yi yenile
            await self.redis_client.expire(session_key, self.session_ttl)
            
            logger.info(f"Existing session found: {session_id}")
            return session_id
        
        # Yeni session oluştur
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "kullanici_id": kullanici_id,
            "isletme_id": isletme_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "context": {},
            "state": "active"
        }
        
        await self.redis_client.setex(
            session_key, 
            self.session_ttl, 
            json.dumps(session_data)
        )
        
        logger.info(f"New session created: {session_id}")
        return session_id
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Session context'ini getir"""
        session_key = f"session_data:{session_id}"
        session_data = await self.redis_client.get(session_key)
        
        if session_data:
            data = json.loads(session_data)
            return data.get("context", {})
        
        return {}
    
    async def update_session_context(self, session_id: str, context: Dict[str, Any]):
        """Session context'ini güncelle"""
        session_key = f"session_data:{session_id}"
        
        # Mevcut session'ı getir
        existing_data = await self.redis_client.get(session_key)
        if existing_data:
            session_data = json.loads(existing_data)
        else:
            session_data = {"context": {}}
        
        # Context'i güncelle
        session_data["context"].update(context)
        session_data["last_activity"] = datetime.now().isoformat()
        
        # Kaydet
        await self.redis_client.setex(
            session_key,
            self.session_ttl,
            json.dumps(session_data)
        )
    
    async def set_session_state(self, session_id: str, state: str, data: Optional[Dict] = None):
        """
        Session durumunu ayarla (waiting_for_product, waiting_for_confirmation, etc.)
        Gelişmiş state management için
        """
        context = await self.get_session_context(session_id)
        
        # Önceki state'i kaydet (geri dönüş için)
        if context.get("state") != "active":
            context["previous_state"] = context.get("state")
            context["previous_state_data"] = context.get("state_data", {})
        
        context["state"] = state
        context["state_data"] = data or {}
        context["state_timestamp"] = datetime.now().isoformat()
        
        # State geçiş logunu kaydet
        logger.info(f"Session state changed: {session_id} -> {state}")
        
        await self.update_session_context(session_id, context)
    
    async def get_session_state(self, session_id: str) -> tuple[str, Dict]:
        """Session durumunu getir"""
        context = await self.get_session_context(session_id)
        state = context.get("state", "active")
        state_data = context.get("state_data", {})
        
        return state, state_data
    
    async def clear_session_state(self, session_id: str):
        """Session durumunu temizle"""
        await self.set_session_state(session_id, "active", {})
    
    async def revert_session_state(self, session_id: str) -> bool:
        """
        Session'ı önceki state'e geri döndür
        """
        try:
            context = await self.get_session_context(session_id)
            
            previous_state = context.get("previous_state")
            previous_state_data = context.get("previous_state_data", {})
            
            if previous_state:
                await self.set_session_state(session_id, previous_state, previous_state_data)
                logger.info(f"Session state reverted: {session_id} -> {previous_state}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Session state revert error: {str(e)}")
            return False
    
    async def set_session_context_value(self, session_id: str, key: str, value: Any):
        """
        Session context'inde belirli bir değeri ayarla
        Örnek: beklenen_bilgi, onceki_niyet, last_product_mentioned
        """
        try:
            context = await self.get_session_context(session_id)
            context[key] = value
            await self.update_session_context(session_id, context)
            
            logger.debug(f"Session context updated: {session_id}:{key} = {value}")
            
        except Exception as e:
            logger.error(f"Session context update error: {str(e)}")
    
    async def get_session_context_value(self, session_id: str, key: str, default: Any = None) -> Any:
        """Session context'inden belirli bir değeri getir"""
        try:
            context = await self.get_session_context(session_id)
            return context.get(key, default)
        except Exception as e:
            logger.error(f"Session context get error: {str(e)}")
            return default
    
    async def is_session_waiting_for(self, session_id: str, expected_info: str) -> bool:
        """
        Session belirli bir bilgi bekliyor mu kontrol et
        """
        try:
            state, state_data = await self.get_session_state(session_id)
            
            if state == "waiting_for_input":
                return state_data.get("beklenen_bilgi") == expected_info
            
            return False
            
        except Exception as e:
            logger.error(f"Session waiting check error: {str(e)}")
            return False
    
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> list:
        """Konuşma geçmişini getir"""
        history_key = f"history:{session_id}"
        history = await self.redis_client.lrange(history_key, 0, limit-1)
        
        return [json.loads(item) for item in history]
    
    async def add_to_conversation_history(self, session_id: str, user_message: str, 
                                        bot_response: str, intent: str, 
                                        confidence_score: float = None):
        """Konuşma geçmişine ekle"""
        history_key = f"history:{session_id}"
        
        history_item = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "intent": intent,
            "confidence_score": confidence_score
        }
        
        # Listeye ekle (en yeni başta)
        await self.redis_client.lpush(history_key, json.dumps(history_item))
        
        # Maksimum 50 mesaj tut
        await self.redis_client.ltrim(history_key, 0, 49)
        
        # TTL ayarla
        await self.redis_client.expire(history_key, self.session_ttl)
    
    async def delete_session(self, session_id: str):
        """Session'ı sil"""
        keys_to_delete = [
            f"session_data:{session_id}",
            f"history:{session_id}"
        ]
        
        for key in keys_to_delete:
            await self.redis_client.delete(key)
    
    async def health_check(self) -> bool:
        """Redis bağlantı kontrolü"""
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self):
        """Süresi dolmuş session'ları temizle (background task)"""
        try:
            # Bu fonksiyon cron job olarak çalıştırılabilir
            pattern = "session:*"
            async for key in self.redis_client.scan_iter(match=pattern):
                ttl = await self.redis_client.ttl(key)
                if ttl == -1:  # TTL yok, manuel temizlik gerekli
                    await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Session cleanup failed: {str(e)}")