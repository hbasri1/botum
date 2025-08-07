"""
Business Logic Router - Intent'lere göre iş mantığını yönlendirir
Güven skoru kontrolü ve eskalasyon mantığı dahil
"""

from typing import Dict, Any, Optional
import logging
from .database_service import DatabaseService
from .session_manager import SessionManager
from .escalation_service import EscalationService

logger = logging.getLogger(__name__)

class BusinessLogicRouter:
    def __init__(self):
        self.db_service = DatabaseService()
        self.session_manager = SessionManager()
        self.escalation_service = EscalationService()
        
        # Güven skoru eşiği
        self.confidence_threshold = 0.80
        
        # Eskalasyon gerektiren intent'ler
        self.escalation_intents = {
            "sikayet_bildirme", 
            "insana_aktar", 
            "karmasik_sorun",
            "ozel_durum",
            "hukuki_konu"
        }
        
        # Intent handler mapping
        self.intent_handlers = {
            "greeting": self._handle_greeting,
            "thanks": self._handle_thanks,
            "meta_query": self._handle_meta_query,
            "product_query": self._handle_product_query,
            "clarify": self._handle_clarify,
            "contact": self._handle_contact,
            "unknown": self._handle_unknown
        }
    
    async def route_intent(self, llm_response: Dict[str, Any], session_id: str, 
                          isletme_id: str, original_message: str) -> str:
        """
        Intent'e göre uygun handler'ı çağır
        Güven skoru kontrolü ve eskalasyon mantığı dahil
        """
        
        intent = llm_response.get("intent", "unknown")
        confidence_score = llm_response.get("confidence", 0.0)
        
        logger.info(f"Routing intent '{intent}' (confidence: {confidence_score}) for session {session_id}")
        
        # 1. GÜVEN SKORU KONTROLÜ
        if confidence_score < self.confidence_threshold:
            logger.warning(f"Low confidence score ({confidence_score}) for session {session_id}")
            return await self._escalate_to_human(
                session_id=session_id,
                isletme_id=isletme_id,
                original_message=original_message,
                reason="low_confidence",
                llm_response=llm_response
            )
        
        # 2. ESKALASYON İNTENT'LERİ KONTROLÜ
        if intent in self.escalation_intents:
            logger.info(f"Escalation intent '{intent}' detected for session {session_id}")
            return await self._escalate_to_human(
                session_id=session_id,
                isletme_id=isletme_id,
                original_message=original_message,
                reason="escalation_intent",
                llm_response=llm_response
            )
        
        # 3. JSON DOĞRULAMA KONTROLÜ
        if not self._validate_llm_response(llm_response):
            logger.warning(f"Invalid LLM response structure for session {session_id}")
            return await self._escalate_to_human(
                session_id=session_id,
                isletme_id=isletme_id,
                original_message=original_message,
                reason="invalid_response",
                llm_response=llm_response
            )
        
        # 4. NORMAL İŞ MANTIK AKIŞI
        handler = self.intent_handlers.get(intent, self._handle_unknown)
        
        try:
            response = await handler(
                llm_response=llm_response,
                session_id=session_id,
                isletme_id=isletme_id,
                original_message=original_message
            )
            
            # Session history'ye ekle
            await self.session_manager.add_to_conversation_history(
                session_id=session_id,
                user_message=original_message,
                bot_response=response,
                intent=intent,
                confidence_score=confidence_score
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Handler error for intent '{intent}': {str(e)}")
            # Hata durumunda da eskalasyon
            return await self._escalate_to_human(
                session_id=session_id,
                isletme_id=isletme_id,
                original_message=original_message,
                reason="handler_error",
                error_details=str(e)
            )
    
    async def _handle_greeting(self, llm_response: Dict, session_id: str, 
                             isletme_id: str, original_message: str) -> str:
        """Selamlama intent'i işle"""
        
        # İşletme özel selamlama mesajı var mı kontrol et
        business_info = await self.db_service.get_business_info(isletme_id)
        
        if business_info and business_info.get("greeting_message"):
            return business_info["greeting_message"]
        
        # Varsayılan selamlama
        return "Merhaba! Size nasıl yardımcı olabilirim?"
    
    async def _handle_thanks(self, llm_response: Dict, session_id: str, 
                           isletme_id: str, original_message: str) -> str:
        """Teşekkür intent'i işle"""
        
        business_info = await self.db_service.get_business_info(isletme_id)
        
        if business_info and business_info.get("thanks_message"):
            return business_info["thanks_message"]
        
        return "Rica ederim! Başka bir sorunuz var mı?"
    
    async def _handle_meta_query(self, llm_response: Dict, session_id: str, 
                                isletme_id: str, original_message: str) -> str:
        """Meta bilgi sorgusu işle - Intent cache ile"""
        
        entities = llm_response.get("entities", [])
        
        # Hangi meta bilgi isteniyor?
        requested_info = None
        for entity in entities:
            if entity.get("type") == "attribute":
                requested_info = entity.get("value")
                break
        
        if not requested_info:
            # LLM'den çıkaramadıysak, orijinal mesajdan tahmin et
            message_lower = original_message.lower()
            if "telefon" in message_lower:
                requested_info = "telefon"
            elif "iade" in message_lower:
                requested_info = "iade"
            elif "kargo" in message_lower:
                requested_info = "kargo"
            elif "adres" in message_lower:
                requested_info = "adres"
            elif "ödeme" in message_lower:
                requested_info = "ödeme"
        
        if requested_info:
            # Önce intent cache'den kontrol et
            from .cache_manager import CacheManager
            cache_manager = CacheManager()
            
            cached_response = await cache_manager.get_intent_cache(
                isletme_id, f"meta_{requested_info}"
            )
            
            if cached_response:
                logger.info(f"Intent cache hit for meta_{requested_info}")
                return cached_response
            
            # Veritabanından meta bilgiyi getir
            meta_info = await self.db_service.get_business_meta_info(
                isletme_id, requested_info
            )
            
            if meta_info:
                # Intent cache'e kaydet (24 saat TTL)
                await cache_manager.set_intent_cache(
                    isletme_id, f"meta_{requested_info}", meta_info, ttl=86400
                )
                return meta_info
        
        return "Bu bilgi şu anda mevcut değil. Müşteri hizmetlerimizle iletişime geçebilirsiniz."
    
    async def _handle_product_query(self, llm_response: Dict, session_id: str, 
                                   isletme_id: str, original_message: str) -> str:
        """Ürün sorgusu işle"""
        
        entities = llm_response.get("entities", [])
        
        # Ürün ve attribute'u çıkar
        product_name = None
        attribute = "fiyat"  # Default
        
        for entity in entities:
            if entity.get("type") == "product":
                product_name = entity.get("value")
            elif entity.get("type") == "attribute":
                attribute = entity.get("value")
        
        # Eğer ürün adı yoksa, session context'inden kontrol et
        if not product_name:
            context = await self.session_manager.get_session_context(session_id)
            product_name = context.get("last_product_mentioned")
        
        if not product_name:
            # Clarify durumuna geç
            await self.session_manager.set_session_state(
                session_id, "waiting_for_product", {"attribute": attribute}
            )
            return "Hangi ürün hakkında bilgi almak istiyorsunuz?"
        
        # Ürün bilgisini getir
        product_info = await self.db_service.get_product_info(
            isletme_id, product_name, attribute
        )
        
        if product_info:
            # Context'e ürünü kaydet
            await self.session_manager.update_session_context(
                session_id, {"last_product_mentioned": product_name}
            )
            
            return product_info
        else:
            # Ürün bulunamadı
            similar_products = await self.db_service.find_similar_products(
                isletme_id, product_name
            )
            
            if similar_products:
                products_list = ", ".join(similar_products[:3])
                return f"'{product_name}' bulunamadı. Şunları kastedebilir misiniz: {products_list}?"
            else:
                return f"'{product_name}' ürünü bulunamadı. Mevcut ürünlerimizi görmek için katalog diyebilirsiniz."
    
    async def _handle_clarify(self, llm_response: Dict, session_id: str, 
                            isletme_id: str, original_message: str) -> str:
        """Belirsiz sorgu işle"""
        
        # Session state'ini kontrol et
        state, state_data = await self.session_manager.get_session_state(session_id)
        
        if state == "waiting_for_product":
            # Kullanıcı ürün adı verdi
            attribute = state_data.get("attribute", "fiyat")
            
            # Bu mesajı ürün adı olarak kabul et
            product_info = await self.db_service.get_product_info(
                isletme_id, original_message, attribute
            )
            
            # State'i temizle
            await self.session_manager.clear_session_state(session_id)
            
            if product_info:
                return product_info
            else:
                return f"'{original_message}' ürünü bulunamadı."
        
        # Genel belirsizlik
        return "Lütfen daha spesifik olabilir misiniz? Hangi ürün veya hizmet hakkında bilgi almak istiyorsunuz?"
    
    async def _handle_contact(self, llm_response: Dict, session_id: str, 
                            isletme_id: str, original_message: str) -> str:
        """İletişim/karmaşık durum işle"""
        
        # İşletme iletişim bilgilerini getir
        contact_info = await self.db_service.get_business_contact_info(isletme_id)
        
        if contact_info:
            return f"Detaylı yardım için iletişim bilgilerimiz:\n{contact_info}"
        
        return "Sorularınız için müşteri hizmetlerimizle iletişime geçebilirsiniz."
    
    async def _handle_unknown(self, llm_response: Dict, session_id: str, 
                            isletme_id: str, original_message: str) -> str:
        """Bilinmeyen intent işle"""
        
        return "Anlayamadım. Ürünlerimiz, fiyatlar veya hizmetlerimiz hakkında soru sorabilirsiniz."
    
    def _validate_llm_response(self, llm_response: Dict[str, Any]) -> bool:
        """LLM yanıtının yapısal doğruluğunu kontrol et"""
        try:
            # Zorunlu alanları kontrol et
            required_fields = ["session_id", "isletme_id", "intent", "confidence"]
            for field in required_fields:
                if field not in llm_response:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Confidence değerinin geçerli olduğunu kontrol et
            confidence = llm_response.get("confidence", 0)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                logger.error(f"Invalid confidence value: {confidence}")
                return False
            
            # Intent'in geçerli olduğunu kontrol et
            valid_intents = {
                "greeting", "thanks", "meta_query", "product_query", 
                "clarify", "contact", "unknown", "sikayet_bildirme", 
                "insana_aktar", "karmasik_sorun", "ozel_durum", "hukuki_konu"
            }
            
            intent = llm_response.get("intent")
            if intent not in valid_intents:
                logger.warning(f"Unknown intent: {intent}")
                # Unknown intent'i geçerli kabul et ama logla
            
            return True
            
        except Exception as e:
            logger.error(f"Response validation error: {str(e)}")
            return False
    
    async def _escalate_to_human(self, session_id: str, isletme_id: str, 
                               original_message: str, reason: str, 
                               llm_response: Dict[str, Any] = None, 
                               error_details: str = None) -> str:
        """
        İnsana eskalasyon işlemi
        Ticket oluştur ve kullanıcıya bilgi ver
        """
        
        logger.info(f"Escalating session {session_id} to human - Reason: {reason}")
        
        try:
            # Eskalasyon ticket'ı oluştur
            ticket_id = await self.escalation_service.create_ticket(
                session_id=session_id,
                isletme_id=isletme_id,
                user_message=original_message,
                escalation_reason=reason,
                llm_response=llm_response,
                error_details=error_details,
                conversation_history=await self.session_manager.get_conversation_history(session_id)
            )
            
            # Session'ı eskalasyon durumuna al
            await self.session_manager.set_session_state(
                session_id, 
                "escalated", 
                {"ticket_id": ticket_id, "escalation_reason": reason}
            )
            
            # İşletme özel eskalasyon mesajı
            business_info = await self.db_service.get_business_info(isletme_id)
            escalation_message = None
            
            if business_info and business_info.get("escalation_message"):
                escalation_message = business_info["escalation_message"].format(
                    ticket_id=ticket_id
                )
            
            if not escalation_message:
                escalation_message = (
                    f"Sorununuzu bir müşteri temsilcimize aktarıyorum. "
                    f"Ticket numaranız: {ticket_id}. "
                    f"En kısa sürede size dönüş yapılacaktır."
                )
            
            # Eskalasyon istatistiklerini güncelle
            await self.db_service.update_escalation_stats(
                isletme_id=isletme_id,
                reason=reason
            )
            
            return escalation_message
            
        except Exception as e:
            logger.error(f"Escalation failed for session {session_id}: {str(e)}")
            
            # Eskalasyon bile başarısız olursa, genel hata mesajı
            return (
                "Üzgünüm, şu anda size yardımcı olamıyorum ve "
                "müşteri temsilcimize de ulaşamıyorum. "
                "Lütfen daha sonra tekrar deneyin veya "
                "doğrudan iletişim kanallarımızı kullanın."
            )
    
    async def _handle_error(self, isletme_id: str, error_message: str) -> str:
        """Hata durumu işle"""
        
        logger.error(f"Business logic error for {isletme_id}: {error_message}")
        
        # İşletme özel hata mesajı
        business_info = await self.db_service.get_business_info(isletme_id)
        
        if business_info and business_info.get("error_message"):
            return business_info["error_message"]
        
        return "Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin."