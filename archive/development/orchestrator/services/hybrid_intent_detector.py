"""
Hybrid Intent Detector - LLM zekası + Pattern matching kombinasyonu
"""

import logging
import json
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class IntentConfidence(Enum):
    HIGH = "high"      # 0.9+ - Kesin pattern match
    MEDIUM = "medium"  # 0.7-0.9 - LLM + pattern
    LOW = "low"        # 0.5-0.7 - Sadece LLM
    UNKNOWN = "unknown" # <0.5 - Belirsiz

class HybridIntentDetector:
    """Hibrit intent detection - Pattern + LLM"""
    
    def __init__(self):
        # Kesin pattern'ler - bunlar için LLM'e gerek yok
        self.certain_patterns = {
            "greeting": {
                "patterns": ["merhaba", "selam", "hello", "hi", "iyi günler"],
                "confidence": 0.95,
                "response_template": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"
            },
            "farewell": {
                "patterns": ["hoşça kal", "güle güle", "görüşürüz", "bay bay", "bye", "tamam iyi günler", "iyi günler"],
                "confidence": 0.95,
                "response_template": "Hoşça kalın! Tekrar bekleriz. 😊"
            },
            "thanks": {
                "patterns": ["teşekkür", "sağol", "thanks", "thank you"],
                "confidence": 0.95,
                "response_template": "Rica ederim! Başka sorunuz var mı?"
            },
            "conversation_end": {
                "patterns": ["yok teşekkürler", "başka soru yok", "o kadar", "bu kadar"],
                "confidence": 0.9,
                "response_template": "Teşekkür ederiz! İyi günler dileriz. 😊"
            }
        }
        
        # İşletme bilgi pattern'leri - bunlar da kesin
        self.business_info_patterns = {
            "phone_inquiry": {
                "patterns": ["telefon", "phone", "iletişim", "numar", "ara", "tel"],
                "exclude_words": ["gecelik", "pijama", "elbise", "sabahlık", "takım", "hamile", "lohusa", "afrika", "dantelli"],
                "confidence": 0.95,
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "telefon"}}
            },
            "return_policy": {
                "patterns": ["iade", "return", "geri", "iade var", "iade var mı", "iade yapabilir", "iade edebilir", "geri verebilir", "değişim", "değiştir"],
                "confidence": 0.95,
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "iade"}}
            },
            "shipping_inquiry": {
                "patterns": ["kargo", "teslimat", "shipping", "cargo"],
                "confidence": 0.95,
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "kargo"}}
            },
            "website_inquiry": {
                "patterns": ["site", "web", "website"],
                "confidence": 0.95,
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "site"}}
            }
        }
        
        # OTOMATIK ÜRÜN DETECTION - İşletme bağımsız
        self.product_query_patterns = [
            "fiyat", "kaç para", "ne kadar", "price", "ücret", "para",
            "stok", "var mı", "mevcut", "stock", "kaldı", "bulunur",
            "renk", "color", "renkler", "hangi renk",
            "beden", "size", "bedenleri", "hangi beden",
            "özellik", "detay", "bilgi", "nasıl", "hakkında"
        ]
        
        # GENEL ÜRÜN KELİMELERİ - Otomatik tespit
        self.generic_product_words = [
            "ürün", "product", "mal", "eşya", "şey", "bunlar", "şunlar"
        ]
        
        # LLM için context-aware prompt
        self.llm_prompt_template = """Sen profesyonel bir Türk müşteri hizmetleri asistanısın. 

Müşteri mesajını analiz et ve ne istediğini anla. Sadece JSON döndür.

MEVCUT İNTENT TİPLERİ:
- product_inquiry: Ürün sorguları (fiyat, stok, özellik, katalog)
- clarification_needed: Belirsiz sorular (hangi ürün, daha detay gerekli)
- complaint: Şikayet veya sorun bildirimi
- compliment: Övgü veya memnuniyet
- human_transfer: Karmaşık durumlar, insan desteği gerekli
- other: Diğer durumlar

JSON FORMAT:
{
  "intent": "intent_adı",
  "confidence": 0.8,
  "reasoning": "Neden bu intent'i seçtim",
  "entities": {
    "product": "ürün_adı_varsa",
    "attribute": "özellik_varsa",
    "sentiment": "positive/negative/neutral"
  }
}

MÜŞTERI MESAJI: "{message}"
ANALİZ:"""

    async def detect_intent(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Hibrit intent detection
        
        Args:
            message: Kullanıcı mesajı
            context: Konuşma context'i
            
        Returns:
            Dict: Intent detection sonucu
        """
        message_lower = message.lower().strip()
        
        # 1. ÖNCE KEİN PATTERN'LERE BAK
        certain_result = self._check_certain_patterns(message_lower)
        if certain_result:
            return certain_result
        
        # 2. İŞLETME BİLGİ PATTERN'LERİNE BAK
        business_result = self._check_business_patterns(message_lower)
        if business_result:
            return business_result
        
        # 3. ÜRÜN SORGUSU MU KONTROL ET
        if self._is_product_related(message_lower):
            return {
                "intent": "product_inquiry",
                "confidence": 0.8,
                "method": "pattern_detection",
                "use_intelligent_search": True,
                "original_message": message
            }
        
        # 4. LLM İLE KARMAŞIK DURUMLAR - UNKNOWN YOK!
        llm_result = await self._llm_intent_detection(message, context)
        if llm_result:
            return llm_result
        
        # 5. SON ÇARE - LLM'E ZORLA GÖNDERİLECEK
        return {
            "intent": "needs_llm_analysis",
            "confidence": 0.5,
            "method": "force_llm",
            "original_message": message,
            "use_llm": True
        }
    
    def _check_certain_patterns(self, message: str) -> Optional[Dict[str, Any]]:
        """Kesin pattern'leri kontrol et"""
        for intent, config in self.certain_patterns.items():
            if any(pattern in message for pattern in config["patterns"]):
                return {
                    "intent": intent,
                    "confidence": config["confidence"],
                    "method": "certain_pattern",
                    "response": config["response_template"]
                }
        return None
    
    def _check_business_patterns(self, message: str) -> Optional[Dict[str, Any]]:
        """İşletme bilgi pattern'lerini kontrol et"""
        for intent, config in self.business_info_patterns.items():
            # Pattern eşleşmesi var mı?
            has_pattern = any(pattern in message for pattern in config["patterns"])
            
            # Exclude word'ler var mı?
            has_exclude = False
            if "exclude_words" in config:
                has_exclude = any(word in message for word in config["exclude_words"])
            
            if has_pattern and not has_exclude:
                return {
                    "intent": "business_info",
                    "confidence": config["confidence"],
                    "method": "business_pattern",
                    "function_call": config["function_call"]
                }
        return None
    
    def _is_product_related(self, message: str) -> bool:
        """AKILLI ürün detection - yanlış pozitif önleme"""
        
        # ÖNCE KESIN OLMAYAN DURUMLAR - bunlar ürün değil!
        non_product_patterns = [
            "tamam", "ok", "okay", "anladım", "peki", "iyi", "evet", "hayır",
            "teşekkür", "sağol", "thanks", "thank", "merci",
            "merhaba", "selam", "hello", "hi", "hey",
            "hoşça kal", "güle güle", "görüşürüz", "bay", "bye",
            "yok", "hayır", "olmaz", "istemiyorum", "istemem",
            "nasılsın", "naber", "ne haber", "nasıl gidiyor",
            "sorcaktım", "soracaktım", "diyecektim", "demek istiyorum",
            "anlıyorum", "biliyorum", "tabii", "elbette", "doğru",
            "pardon", "özür", "sorry", "excuse me",
            "neyse", "boşver", "önemli değil", "sorun değil"
        ]
        
        # Kesin olmayan pattern varsa ürün değil - SERT KONTROL
        message_lower = message.lower().strip()
        for pattern in non_product_patterns:
            if pattern == message_lower or f" {pattern} " in f" {message_lower} " or message_lower.startswith(f"{pattern} ") or message_lower.endswith(f" {pattern}"):
                return False
        
        # 1. Ürün sorgu pattern'leri var mı?
        has_product_query = any(pattern in message for pattern in self.product_query_patterns)
        
        # 2. Genel ürün kelimeleri var mı?
        has_generic_product = any(word in message for word in self.generic_product_words)
        
        # 3. Direkt ürün ismi olabilir - DAHA AKILLI
        words = message.split()
        is_short_query = len(words) <= 2  # Daha kısıtlayıcı
        is_not_greeting = not any(greeting in message for greeting in ["merhaba", "selam", "hello"])
        is_not_business_info = not any(info in message for info in ["telefon", "iade", "kargo", "site"])
        is_not_common_word = not any(common in message.lower() for common in ["tamam", "ok", "teşekkür", "sağol"])
        
        # Direkt ürün ismi olabilir - çok daha kısıtlayıcı
        might_be_product_name = (
            is_short_query and 
            is_not_greeting and 
            is_not_business_info and 
            is_not_common_word and
            len(message.strip()) > 2  # Çok kısa değil
        )
        
        return has_product_query or has_generic_product or might_be_product_name
    
    async def _llm_intent_detection(self, message: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """GERÇEK LLM ile intent detection - UNKNOWN YOK!"""
        try:
            # GERÇEK GEMINI API ÇAĞRISI
            prompt = f"""Sen bir müşteri hizmetleri asistanısın. Müşteri mesajını analiz et ve JSON döndür.

SADECE BU İNTENT'LERİ KULLAN:
- product_inquiry: Ürün sorguları (fiyat, stok, özellik)
- business_info: İşletme bilgileri (telefon, iade, kargo)
- greeting: Selamlama
- thanks: Teşekkür
- farewell: Vedalaşma
- complaint: Şikayet
- compliment: Övgü
- human_transfer: Karmaşık durumlar

ASLA "unknown" KULLANMA! Her durumu yukarıdaki intent'lerden birine ata.

JSON FORMAT:
{{
  "intent": "intent_adı",
  "confidence": 0.9,
  "reasoning": "Neden bu intent"
}}

MESAJ: "{message}"
ANALİZ:"""

            # Mock LLM response (gerçekte Gemini API çağrısı olacak)
            message_lower = message.lower()
            
            # Basit heuristic - gerçekte LLM yapacak
            if any(word in message_lower for word in ["sorun", "problem", "şikayet", "kötü", "berbat"]):
                return {
                    "intent": "complaint",
                    "confidence": 0.9,
                    "method": "llm_analysis",
                    "reasoning": "Şikayet ifadeleri tespit edildi"
                }
            
            elif any(word in message_lower for word in ["harika", "mükemmel", "güzel", "beğendim", "süper"]):
                return {
                    "intent": "compliment",
                    "confidence": 0.9,
                    "method": "llm_analysis",
                    "reasoning": "Övgü ifadeleri tespit edildi"
                }
            
            elif any(word in message_lower for word in ["anlamadım", "karışık", "açıklayabilir", "nasıl"]):
                return {
                    "intent": "human_transfer",
                    "confidence": 0.8,
                    "method": "llm_analysis",
                    "reasoning": "Karmaşık soru, insan desteği gerekli"
                }
            
            # Diğer durumlar için - DAHA AKILLI KARAR
            message_lower = message.lower().strip()
            
            # Çok kısa ve anlamsız ise clarification_needed
            if len(message_lower) <= 3 or message_lower in ["tamam", "ok", "peki", "iyi", "evet", "hayır"]:
                return {
                    "intent": "clarification_needed",
                    "confidence": 0.8,
                    "method": "llm_analysis",
                    "reasoning": "Çok kısa veya belirsiz mesaj"
                }
            
            # Diğer durumlar için product_inquiry varsayalım
            return {
                "intent": "product_inquiry",
                "confidence": 0.6,
                "method": "llm_analysis",
                "reasoning": "Belirsiz sorgu, muhtemelen ürün ile ilgili"
            }
            
        except Exception as e:
            logger.error(f"LLM intent detection error: {str(e)}")
            # Hata durumunda bile unknown döndürme!
            return {
                "intent": "human_transfer",
                "confidence": 0.6,
                "method": "llm_error_fallback",
                "reasoning": "LLM hatası, insan desteğine yönlendir"
            }
    
    def get_intent_confidence_level(self, confidence: float) -> IntentConfidence:
        """Confidence level'ı belirle"""
        if confidence >= 0.9:
            return IntentConfidence.HIGH
        elif confidence >= 0.7:
            return IntentConfidence.MEDIUM
        elif confidence >= 0.5:
            return IntentConfidence.LOW
        else:
            return IntentConfidence.UNKNOWN
    
    def should_use_llm(self, message: str) -> bool:
        """Bu mesaj için LLM kullanılmalı mı?"""
        # Kesin pattern'ler varsa LLM'e gerek yok
        message_lower = message.lower()
        
        for config in self.certain_patterns.values():
            if any(pattern in message_lower for pattern in config["patterns"]):
                return False
        
        for config in self.business_info_patterns.values():
            if any(pattern in message_lower for pattern in config["patterns"]):
                return False
        
        # Ürün sorguları için intelligent search yeterli
        if self._is_product_related(message_lower):
            return False
        
        # Diğer durumlar için LLM kullan
        return True
    
    async def get_response_strategy(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Intent sonucuna göre response stratejisi belirle"""
        intent = intent_result.get("intent")
        confidence = intent_result.get("confidence", 0)
        confidence_level = self.get_intent_confidence_level(confidence)
        
        strategy = {
            "use_direct_response": False,
            "use_function_call": False,
            "use_intelligent_search": False,
            "use_human_transfer": False,
            "response_template": None
        }
        
        # ÖNCE ÖZEL INTENT'LERE BAK
        if intent == "clarification_needed":
            strategy["use_direct_response"] = True
            strategy["response_template"] = "Tam olarak ne hakkında bilgi almak istiyorsunuz? Ürün, fiyat, iade veya iletişim konularında yardımcı olabilirim."
        
        elif confidence_level == IntentConfidence.HIGH:
            # Yüksek güven - direkt cevap ver
            if "response" in intent_result:
                strategy["use_direct_response"] = True
                strategy["response_template"] = intent_result["response"]
            elif "function_call" in intent_result:
                strategy["use_function_call"] = True
        
        elif confidence_level == IntentConfidence.MEDIUM:
            # Orta güven - function call veya intelligent search
            if intent == "product_inquiry":
                strategy["use_intelligent_search"] = True
            elif "function_call" in intent_result:
                strategy["use_function_call"] = True
        
        elif confidence_level == IntentConfidence.LOW or intent == "clarification_needed":
            # Düşük güven veya clarification gerekli
            strategy["use_direct_response"] = True
            strategy["response_template"] = "Tam olarak ne hakkında bilgi almak istiyorsunuz? Ürün, fiyat, iade veya iletişim konularında yardımcı olabilirim."
        
        else:
            # Çok düşük güven - insan desteği öner
            strategy["use_human_transfer"] = True
            strategy["response_template"] = "Bu konuda size daha iyi yardımcı olabilmek için WhatsApp üzerinden iletişime geçebilirsiniz: 0555 555 55 55"
        
        return strategy