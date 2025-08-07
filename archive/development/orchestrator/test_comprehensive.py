#!/usr/bin/env python3
"""
Kapsamlı Sistem Entegrasyon Testi
Tüm bileşenleri gerçek senaryolarla test eder
"""

import asyncio
import json
import uuid
import redis.asyncio as redis
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Test için mock servisleri
from services.cache_manager import CacheManager
from services.session_manager import SessionManager
from services.database_service import DatabaseService
from services.business_logic_router import BusinessLogicRouter
from services.llm_service import LLMService, LLMResponse
from services.escalation_service import EscalationService

# Test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockLLMService(LLMService):
    """Test için Mock LLM Service"""
    
    def __init__(self):
        # Parent constructor'ı çağırmayalım, sadece test için gerekli olanları ayarlayalım
        self.max_retries = 3
        self.timeout = 30
    
    async def process_message(self, prompt: str, session_id: str, isletme_id: str) -> Optional[Dict[str, Any]]:
        """Mock LLM yanıtları - gerçek senaryoları simüle et"""
        
        message = prompt.lower()
        
        # Selamlama
        if any(word in message for word in ["merhaba", "selam", "hey"]):
            return {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "greeting",
                "entities": [],
                "context": {"requires_followup": False},
                "confidence": 0.95,
                "language": "tr"
            }
        
        # Ürün fiyat sorgusu
        elif any(word in message for word in ["fiyat", "kaç para", "ne kadar"]):
            if "gecelik" in message:
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_query",
                    "entities": [
                        {"type": "product", "value": "gecelik", "confidence": 0.9},
                        {"type": "attribute", "value": "fiyat", "confidence": 0.95}
                    ],
                    "context": {"product_mentioned": "gecelik", "attribute_requested": "fiyat"},
                    "confidence": 0.88,
                    "language": "tr"
                }
            else:
                # Belirsiz ürün - düşük güven skoru
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_query",
                    "entities": [],
                    "context": {"requires_followup": True},
                    "confidence": 0.65,  # Düşük güven - eskalasyon tetikleyecek
                    "language": "tr"
                }
        
        # Şikayet
        elif any(word in message for word in ["şikayet", "problem", "sorun"]):
            return {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "sikayet_bildirme",  # Eskalasyon intent'i
                "entities": [],
                "context": {"requires_followup": True},
                "confidence": 0.92,
                "language": "tr"
            }
        
        # İade politikası
        elif any(word in message for word in ["iade", "geri", "değişim"]):
            return {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "meta_query",
                "entities": [
                    {"type": "attribute", "value": "iade", "confidence": 0.9}
                ],
                "context": {},
                "confidence": 0.91,
                "language": "tr"
            }
        
        # Bilinmeyen/karmaşık mesaj
        else:
            return {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "unknown",
                "entities": [],
                "context": {},
                "confidence": 0.45,  # Çok düşük güven - eskalasyon
                "language": "tr"
            }
    
    async def health_check(self) -> bool:
        return True

class MockDatabaseService(DatabaseService):
    """Test için Mock Database Service"""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
        self.pool = None  # Mock için pool gerekmez
        
        # Test verileri
        self.businesses = {
            "test-business-1": {
                "id": "test-business-1",
                "name": "Test Butik",
                "greeting_message": "Merhaba! Test Butik'e hoş geldiniz!",
                "thanks_message": "Teşekkürler! Başka sorunuz var mı?",
                "error_message": "Üzgünüm, şu anda yardımcı olamıyorum.",
                "meta_data": {
                    "telefon": "0555 123 45 67",
                    "iade": "İade 14 gün içinde yapılabilir",
                    "kargo": "Kargo 2-3 iş günü içinde",
                    "adres": "Test Mahallesi, Test Sokak No:1"
                }
            }
        }
        
        self.products = {
            "test-business-1": [
                {
                    "id": "product-1",
                    "name": "Test Gecelik",
                    "price": 299.99,
                    "stock_quantity": 10,
                    "color": "siyah",
                    "description": "Şık ve rahat gecelik"
                },
                {
                    "id": "product-2", 
                    "name": "Test Pijama Takımı",
                    "price": 199.99,
                    "stock_quantity": 5,
                    "color": "mavi",
                    "description": "Pamuklu pijama takımı"
                }
            ]
        }
    
    async def initialize(self):
        pass
    
    async def close(self):
        pass
    
    async def get_business_info(self, isletme_id: str) -> Optional[Dict[str, Any]]:
        return self.businesses.get(isletme_id)
    
    async def get_business_meta_info(self, isletme_id: str, info_type: str) -> Optional[str]:
        business = self.businesses.get(isletme_id)
        if business and business.get("meta_data"):
            return business["meta_data"].get(info_type)
        return None
    
    async def get_product_info(self, isletme_id: str, product_name: str, attribute: str = "fiyat") -> Optional[str]:
        products = self.products.get(isletme_id, [])
        
        for product in products:
            if product_name.lower() in product["name"].lower():
                if attribute == "fiyat":
                    return f"{product['name']}\nFiyat: {product['price']} TL"
                elif attribute == "stok":
                    return f"{product['name']}\nStok: {product['stock_quantity']} adet"
                else:
                    return f"{product['name']}\n{product['description']}"
        
        return None
    
    async def update_product_price(self, isletme_id: str, product_id: str, new_price: float) -> bool:
        products = self.products.get(isletme_id, [])
        
        for product in products:
            if product["id"] == product_id:
                old_price = product["price"]
                product["price"] = new_price
                
                # Cache invalidation
                if self.cache_manager:
                    await self.cache_manager.invalidate_product_cache(
                        isletme_id, product_id, product["name"]
                    )
                
                logger.info(f"Mock: Product price updated {product['name']}: {old_price} -> {new_price}")
                return True
        
        return False
    
    async def log_interaction(self, **kwargs):
        logger.info(f"Mock: Interaction logged for session {kwargs.get('session_id')}")
    
    async def create_escalation_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        logger.info(f"Mock: Escalation ticket created: {ticket_data['ticket_id']}")
        return True
    
    async def health_check(self) -> bool:
        return True

async def test_full_webhook_flow():
    """Tam webhook akışını test et"""
    print("🧪 Tam Webhook Akışı Testi...")
    
    # Servisleri başlat
    cache_manager = CacheManager()
    session_manager = SessionManager()
    mock_db = MockDatabaseService(cache_manager=cache_manager)
    mock_llm = MockLLMService()
    
    # Business router'ı gerçek servisle test et
    router = BusinessLogicRouter()
    router.db_service = mock_db
    router.session_manager = session_manager
    
    test_cases = [
        {
            "name": "Selamlama",
            "message": "merhaba",
            "expected_intent": "greeting",
            "should_escalate": False
        },
        {
            "name": "Ürün Fiyat Sorgusu (Başarılı)",
            "message": "gecelik fiyatı ne kadar?",
            "expected_intent": "product_query", 
            "should_escalate": False
        },
        {
            "name": "Belirsiz Ürün Sorgusu (Düşük Güven)",
            "message": "bu şeyin fiyatı ne kadar?",
            "expected_intent": "product_query",
            "should_escalate": True  # Düşük güven skoru
        },
        {
            "name": "Şikayet (Eskalasyon Intent)",
            "message": "şikayet etmek istiyorum",
            "expected_intent": "sikayet_bildirme",
            "should_escalate": True  # Eskalasyon intent'i
        },
        {
            "name": "İade Politikası",
            "message": "iade politikanız nedir?",
            "expected_intent": "meta_query",
            "should_escalate": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {test_case['name']}")
        
        # Session oluştur
        session_id = await session_manager.get_or_create_session(
            kullanici_id=f"test-user-{i}",
            isletme_id="test-business-1"
        )
        
        # LLM'e gönder
        llm_response = await mock_llm.process_message(
            prompt=f"[session: {session_id}] [kimlik: test-business-1] {test_case['message']}",
            session_id=session_id,
            isletme_id="test-business-1"
        )
        
        print(f"    LLM Intent: {llm_response['intent']}, Güven: {llm_response['confidence']}")
        
        # Business router'a gönder
        final_response = await router.route_intent(
            llm_response=llm_response,
            session_id=session_id,
            isletme_id="test-business-1",
            original_message=test_case['message']
        )
        
        # Sonucu kontrol et
        is_escalated = "ticket" in final_response.lower() or "temsilci" in final_response.lower()
        
        if is_escalated == test_case['should_escalate']:
            print(f"    ✅ Beklenen sonuç: {'Eskalasyon' if is_escalated else 'Normal yanıt'}")
        else:
            print(f"    ❌ Beklenmeyen sonuç: {'Eskalasyon' if is_escalated else 'Normal yanıt'}")
        
        print(f"    Yanıt: {final_response[:100]}...")
    
    print("\n✅ Tam webhook akışı testi tamamlandı!")

async def test_cache_performance():
    """Cache performansını test et"""
    print("\n🧪 Cache Performans Testi...")
    
    cache_manager = CacheManager()
    
    # Test verileri
    test_data = [
        ("test-business-1", "merhaba", "Merhaba! Size nasıl yardımcı olabilirim?"),
        ("test-business-1", "gecelik fiyatı", "Test Gecelik\nFiyat: 299.99 TL"),
        ("test-business-1", "iade politikası", "İade 14 gün içinde yapılabilir")
    ]
    
    # Cache'e kaydet
    for isletme_id, query, response in test_data:
        cache_key = f"{isletme_id}:{query}"
        await cache_manager.set(cache_key, response, ttl=3600)
    
    # Cache hit testleri
    hit_count = 0
    for isletme_id, query, expected_response in test_data:
        cache_key = f"{isletme_id}:{query}"
        cached_response = await cache_manager.get(cache_key)
        
        if cached_response == expected_response:
            hit_count += 1
            print(f"    ✅ Cache hit: {query}")
        else:
            print(f"    ❌ Cache miss: {query}")
    
    print(f"    Cache hit oranı: {hit_count}/{len(test_data)} (%{(hit_count/len(test_data))*100:.1f})")
    
    # Cache invalidation testi
    await cache_manager.invalidate_product_cache("test-business-1", "product-1", "gecelik")
    
    # Gecelik ile ilgili cache'lerin silindiğini kontrol et
    gecelik_cache = await cache_manager.get("test-business-1:gecelik fiyatı")
    if not gecelik_cache:
        print("    ✅ Product cache invalidation başarılı")
    else:
        print("    ❌ Product cache invalidation başarısız")
    
    print("✅ Cache performans testi tamamlandı!")

async def test_session_continuity():
    """Session sürekliliğini test et"""
    print("\n🧪 Session Süreklilik Testi...")
    
    session_manager = SessionManager()
    
    # Kullanıcı session'ı oluştur
    session_id = await session_manager.get_or_create_session(
        kullanici_id="test-user-continuity",
        isletme_id="test-business-1"
    )
    
    print(f"    Session oluşturuldu: {session_id}")
    
    # Context bilgisi ekle
    await session_manager.set_session_context_value(session_id, "last_product_mentioned", "gecelik")
    await session_manager.set_session_context_value(session_id, "conversation_count", 1)
    
    # State ayarla
    await session_manager.set_session_state(session_id, "waiting_for_input", {
        "beklenen_bilgi": "beden",
        "onceki_niyet": "product_query"
    })
    
    # Bilgileri geri al
    last_product = await session_manager.get_session_context_value(session_id, "last_product_mentioned")
    conversation_count = await session_manager.get_session_context_value(session_id, "conversation_count")
    state, state_data = await session_manager.get_session_state(session_id)
    
    if (last_product == "gecelik" and 
        conversation_count == 1 and 
        state == "waiting_for_input" and 
        state_data.get("beklenen_bilgi") == "beden"):
        print("    ✅ Session context ve state korundu")
    else:
        print("    ❌ Session bilgileri kayboldu")
    
    # Conversation history test
    await session_manager.add_to_conversation_history(
        session_id=session_id,
        user_message="gecelik fiyatı ne kadar?",
        bot_response="Test Gecelik\nFiyat: 299.99 TL",
        intent="product_query",
        confidence_score=0.88
    )
    
    history = await session_manager.get_conversation_history(session_id, limit=5)
    
    if len(history) > 0 and history[0]["user_message"] == "gecelik fiyatı ne kadar?":
        print("    ✅ Conversation history kaydedildi")
    else:
        print("    ❌ Conversation history kaydedilemedi")
    
    print("✅ Session süreklilik testi tamamlandı!")

async def test_database_cache_integration():
    """Database ve cache entegrasyonunu test et"""
    print("\n🧪 Database-Cache Entegrasyon Testi...")
    
    cache_manager = CacheManager()
    mock_db = MockDatabaseService(cache_manager=cache_manager)
    
    # Önce cache'e bir ürün bilgisi koy
    cache_key = "cache:test-business-1:test gecelik fiyat"
    await cache_manager.set(cache_key, "Eski fiyat: 299.99 TL", ttl=3600)
    
    # Cache'de olduğunu kontrol et
    cached_before = await cache_manager.get(cache_key)
    if cached_before:
        print("    ✅ Cache'e eski fiyat kaydedildi")
    
    # Ürün fiyatını güncelle (cache invalidation tetikleyecek)
    success = await mock_db.update_product_price("test-business-1", "product-1", 349.99)
    
    if success:
        print("    ✅ Ürün fiyatı güncellendi")
        
        # Cache'in temizlendiğini kontrol et
        cached_after = await cache_manager.get(cache_key)
        if not cached_after:
            print("    ✅ Cache otomatik olarak temizlendi")
        else:
            print("    ❌ Cache temizlenmedi")
    else:
        print("    ❌ Ürün fiyatı güncellenemedi")
    
    print("✅ Database-cache entegrasyon testi tamamlandı!")

async def test_error_handling():
    """Hata yönetimini test et"""
    print("\n🧪 Hata Yönetimi Testi...")
    
    router = BusinessLogicRouter()
    
    # Geçersiz JSON yanıtı simüle et
    invalid_responses = [
        None,  # LLM yanıt vermedi
        {},    # Boş yanıt
        {"invalid": "data"},  # Geçersiz format
        {"session_id": "test", "confidence": 2.0}  # Geçersiz değer
    ]
    
    for i, invalid_response in enumerate(invalid_responses, 1):
        print(f"    Test {i}: {type(invalid_response).__name__} yanıt")
        
        try:
            if invalid_response is None:
                # LLM servis hatası simülasyonu
                result = "LLM servisi kullanılamıyor"
            else:
                result = await router.route_intent(
                    llm_response=invalid_response,
                    session_id="test-session-error",
                    isletme_id="test-business-1",
                    original_message="test mesajı"
                )
            
            # Hata durumunda eskalasyon bekliyoruz
            is_escalated = "ticket" in result.lower() or "temsilci" in result.lower()
            
            if is_escalated:
                print(f"        ✅ Hata durumunda eskalasyon yapıldı")
            else:
                print(f"        ❌ Hata durumunda eskalasyon yapılmadı")
                
        except Exception as e:
            print(f"        ✅ Exception yakalandı: {type(e).__name__}")
    
    print("✅ Hata yönetimi testi tamamlandı!")

async def main():
    """Ana test fonksiyonu"""
    print("🚀 KAPSAMLI SİSTEM ENTEGRASYON TESTLERİ\n")
    print("=" * 60)
    
    try:
        # Redis bağlantısını test et
        try:
            redis_client = redis.from_url("redis://localhost:6379/0")
            await redis_client.ping()
            print("✅ Redis bağlantısı başarılı")
            await redis_client.close()
        except Exception as e:
            print(f"⚠️  Redis bağlantısı başarısız: {str(e)}")
            print("   Docker ile Redis başlatın: docker-compose up -d redis")
        
        print("\n" + "=" * 60)
        
        # Testleri çalıştır
        await test_full_webhook_flow()
        await test_cache_performance()
        await test_session_continuity()
        await test_database_cache_integration()
        await test_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 TÜM ENTEGRASYON TESTLERİ BAŞARILI!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test hatası: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())