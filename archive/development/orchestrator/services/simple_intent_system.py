"""
Simple Intent System - Basit ve etkili
"""

import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleIntentSystem:
    """Basit ve etkili intent sistemi"""
    
    def __init__(self):
        # KESIN PATTERN'LER - bunlar için LLM'e gerek yok
        self.exact_patterns = {
            # Selamlama
            "merhaba": {"intent": "greeting", "response": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"},
            "selam": {"intent": "greeting", "response": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"},
            "hello": {"intent": "greeting", "response": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"},
            "hi": {"intent": "greeting", "response": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"},
            
            # Teşekkür
            "teşekkürler": {"intent": "thanks", "response": "Rica ederim! Başka sorunuz var mı?"},
            "teşekkür": {"intent": "thanks", "response": "Rica ederim! Başka sorunuz var mı?"},
            "sağol": {"intent": "thanks", "response": "Rica ederim! Başka sorunuz var mı?"},
            "thanks": {"intent": "thanks", "response": "Rica ederim! Başka sorunuz var mı?"},
            
            # Vedalaşma
            "hoşça kal": {"intent": "farewell", "response": "Hoşça kalın! Tekrar bekleriz. 😊"},
            "güle güle": {"intent": "farewell", "response": "Hoşça kalın! Tekrar bekleriz. 😊"},
            "görüşürüz": {"intent": "farewell", "response": "Hoşça kalın! Tekrar bekleriz. 😊"},
            "bye": {"intent": "farewell", "response": "Hoşça kalın! Tekrar bekleriz. 😊"},
            
            # Onay/Anlama
            "tamam": {"intent": "acknowledgment", "response": "Başka bir sorunuz var mı?"},
            "ok": {"intent": "acknowledgment", "response": "Başka bir sorunuz var mı?"},
            "peki": {"intent": "acknowledgment", "response": "Başka bir sorunuz var mı?"},
            "anladım": {"intent": "acknowledgment", "response": "Başka bir sorunuz var mı?"},
            "evet": {"intent": "acknowledgment", "response": "Başka bir sorunuz var mı?"},
            
            # Red/Olumsuz
            "yok": {"intent": "negative", "response": "Teşekkür ederiz! İyi günler dileriz. 😊"},
            "hayır": {"intent": "negative", "response": "Başka bir konuda yardımcı olabilirim."},
            "istemiyorum": {"intent": "negative", "response": "Başka bir konuda yardımcı olabilirim."},
        }
        
        # İŞLETME BİLGİ PATTERN'LERİ
        self.business_patterns = {
            "telefon": ["telefon", "phone", "iletişim", "numar", "ara"],
            "iade": ["iade", "return", "geri", "değişim", "değiştir"],
            "kargo": ["kargo", "teslimat", "shipping", "cargo"],
            "site": ["site", "web", "website"]
        }
        
        # ÜRÜN SORGU PATTERN'LERİ
        self.product_patterns = [
            "fiyat", "kaç para", "ne kadar", "price",
            "stok", "var mı", "mevcut", "stock",
            "renk", "color", "beden", "size"
        ]
        
        # ÜRÜN ADI PATTERN'LERİ
        self.product_names = [
            "gecelik", "pijama", "elbise", "sabahlık", "takım",
            "hamile", "lohusa", "afrika", "dantelli", "siyah", "beyaz"
        ]
        
        # ANLAMSIZ PATTERN'LER - gerçekten anlamsız olanlar
        self.nonsense_patterns = [
            # Sadece gerçek nonsense - küfür ve spam
            "annen", "baban", "kardeşin", "ablan", "ağabeyin",
            "asdfgh", "qwerty", "123456", "test test", "deneme deneme",
            "amk", "amına", "sik", "götü", "orospu"
        ]
        
        # TÜRKÇE GELECEK ZAMAN EKLERİ - ÖNEMLİ!
        self.future_tense_patterns = [
            "fiyat soracaktım", "fiyat soracağım", "fiyat öğreneceğim",
            "fiyat sormak istiyorum", "fiyat bilmek istiyorum", 
            "fiyat öğrenmek istiyorum", "fiyat almak istiyorum",
            "stok soracaktım", "stok öğreneceğim", "stok sormak istiyorum",
            "bilgi alacaktım", "bilgi almak istiyorum", "soru soracaktım"
        ]
    
    async def detect_intent(self, message: str) -> Dict[str, Any]:
        """Basit ve etkili intent detection"""
        
        if not message or not message.strip():
            return {
                "intent": "clarification_needed",
                "confidence": 0.9,
                "method": "empty_message",
                "response": "Merhaba! Size nasıl yardımcı olabilirim?"
            }
        
        message_clean = message.lower().strip()
        
        # 1. ÖNCE TÜRKÇE GELECEK ZAMAN EKLERİNE BAK - ÖNEMLİ!
        for future_pattern in self.future_tense_patterns:
            if future_pattern in message_clean:
                # Fiyat sorusu mu?
                if "fiyat" in future_pattern:
                    return {
                        "intent": "product_inquiry",
                        "confidence": 0.9,
                        "method": "future_tense_price",
                        "use_intelligent_search": True,
                        "context_hint": "user_wants_price_info"
                    }
                # Stok sorusu mu?
                elif "stok" in future_pattern:
                    return {
                        "intent": "product_inquiry", 
                        "confidence": 0.9,
                        "method": "future_tense_stock",
                        "use_intelligent_search": True,
                        "context_hint": "user_wants_stock_info"
                    }
                # Genel bilgi sorusu
                else:
                    return {
                        "intent": "clarification_needed",
                        "confidence": 0.8,
                        "method": "future_tense_general",
                        "response": "Hangi ürün hakkında bilgi almak istiyorsunuz?"
                    }
        
        # 2. SONRA ANLAMSIZ PATTERN'LERE BAK - daha akıllı
        # Sadece mesaj tamamen nonsense ise algıla
        nonsense_count = sum(1 for nonsense in self.nonsense_patterns if nonsense in message_clean)
        meaningful_count = sum(1 for pattern in self.product_patterns + self.product_names if pattern in message_clean)
        
        # Eğer nonsense çok fazla ve meaningful az ise nonsense
        if nonsense_count > 0 and meaningful_count == 0 and len(message_clean.split()) <= 3:
            return {
                "intent": "clarification_needed",
                "confidence": 0.9,
                "method": "nonsense_detection",
                "response": "Anlayamadım. Ürün, fiyat, iade veya iletişim hakkında sorabilirsiniz."
            }
        
        # 3. KESIN PATTERN'LERE BAK
        if message_clean in self.exact_patterns:
            pattern = self.exact_patterns[message_clean]
            return {
                "intent": pattern["intent"],
                "confidence": 0.95,
                "method": "exact_pattern",
                "response": pattern["response"]
            }
        
        # 4. İŞLETME BİLGİ PATTERN'LERİNE BAK
        for info_type, patterns in self.business_patterns.items():
            if any(pattern in message_clean for pattern in patterns):
                # Ürün adı da varsa ürün sorgusu olabilir
                has_product = any(product in message_clean for product in self.product_names)
                if not has_product:
                    return {
                        "intent": "business_info",
                        "confidence": 0.9,
                        "method": "business_pattern",
                        "info_type": info_type,
                        "function_call": {"name": "getGeneralInfo", "args": {"info_type": info_type}}
                    }
        
        # 5. ÜRÜN SORGUSU MU KONTROL ET - DAHA AKILLI
        has_product_query = any(pattern in message_clean for pattern in self.product_patterns)
        has_product_name = any(product in message_clean for product in self.product_names)
        
        # GELİŞMİŞ ÜRÜN ADI ÇIKARMA
        extracted_product = self._extract_enhanced_product_name(message_clean)
        if extracted_product:
            has_product_name = True
        
        # Sadece ürün sorgu kelimesi varsa ve ürün adı yoksa belirsiz
        if has_product_query and not has_product_name:
            # Tek kelime ise clarification iste
            if len(message_clean.split()) <= 1:
                return {
                    "intent": "clarification_needed",
                    "confidence": 0.9,
                    "method": "incomplete_query",
                    "response": f"Hangi ürün hakkında bilgi almak istiyorsunuz?"
                }
        
        # Hem ürün sorgusu hem ürün adı varsa ürün sorgusu
        if has_product_query and has_product_name:
            return {
                "intent": "product_inquiry",
                "confidence": 0.8,
                "method": "product_pattern",
                "use_intelligent_search": True
            }
        
        # Sadece ürün adı varsa da ürün sorgusu
        if has_product_name:
            return {
                "intent": "product_inquiry",
                "confidence": 0.7,
                "method": "product_name_only",
                "use_intelligent_search": True
            }
        
        # 6. KISA VE BELİRSİZ MESAJLAR - daha akıllı
        words = message_clean.split()
        if len(words) <= 2:
            # Tek kelime ürün sorguları - belirsiz
            if len(words) == 1 and words[0] in ["fiyat", "stok", "renk", "beden"]:
                return {
                    "intent": "clarification_needed",
                    "confidence": 0.9,
                    "method": "incomplete_query",
                    "response": f"Hangi ürünün {words[0]} bilgisini öğrenmek istiyorsunuz?"
                }
            
            # Diğer kısa mesajlar
            return {
                "intent": "clarification_needed",
                "confidence": 0.8,
                "method": "short_message",
                "response": "Tam olarak ne hakkında bilgi almak istiyorsunuz? Ürün, fiyat, iade veya iletişim konularında yardımcı olabilirim."
            }
        
        # 7. LLM'E GÖNDERİLECEK - karmaşık durumlar
        return {
            "intent": "needs_llm",
            "confidence": 0.6,
            "method": "needs_llm",
            "use_llm": True,
            "original_message": message
        }
    
    def _extract_enhanced_product_name(self, message: str) -> str:
        """Gelişmiş ürün adı çıkarma"""
        
        # Compound products - birleşik ürün adları
        compound_products = {
            "afrika gecelik": ["afrika", "gecelik"],
            "africa gecelik": ["africa", "gecelik"], 
            "hamile gecelik": ["hamile", "gecelik"],
            "lohusa takım": ["lohusa", "takım"],
            "dantelli gecelik": ["dantelli", "gecelik"],
            "çiçekli pijama": ["çiçek", "pijama"],
            "desenli takım": ["desen", "takım"],
            "çiçek desenli": ["çiçek", "desen"],
            "yaprak desenli": ["yaprak", "desen"]
        }
        
        for product_name, keywords in compound_products.items():
            if all(keyword in message for keyword in keywords):
                return product_name
        
        # Descriptive features
        descriptive_features = ["çiçek", "yaprak", "desenli", "dantelli", "dekolteli"]
        base_products = ["gecelik", "pijama", "takım", "elbise", "sabahlık"]
        
        # Feature + product combinations
        for feature in descriptive_features:
            if feature in message:
                for product in base_products:
                    if product in message:
                        return f"{feature} {product}"
        
        return ""
    
    def should_use_llm(self, message: str) -> bool:
        """Bu mesaj için LLM kullanılmalı mı?"""
        result = asyncio.run(self.detect_intent(message))
        return result.get("use_llm", False)

# Global instance
simple_intent_system = SimpleIntentSystem()