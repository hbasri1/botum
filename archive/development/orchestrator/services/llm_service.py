"""
LLM Service - Enhanced with Intelligent Search Integration
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
import google.generativeai as genai

try:
    from .intelligent_search_engine import IntelligentSearchEngine
    from .conversation_context_manager import ConversationContextManager
    from .context_aware_query_resolver import ContextAwareQueryResolver
    from .contextual_intent_detector import ContextualIntentDetector
    from .confidence_based_presenter import ConfidenceBasedPresenter
except ImportError:
    # Fallback imports for testing
    IntelligentSearchEngine = None
    ConversationContextManager = None
    ContextAwareQueryResolver = None
    ContextualIntentDetector = None
    ConfidenceBasedPresenter = None

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, enable_function_calling: bool = True, enable_intelligent_search: bool = True):
        self.enable_function_calling = enable_function_calling
        self.enable_intelligent_search = enable_intelligent_search
        self.model = None
        self.function_model = None
        self.fallback_handler = None
        
        # Initialize Gemini
        self._initialize_gemini()
        
        # Initialize intelligent search components
        self._initialize_intelligent_search()
    
    def _initialize_gemini(self):
        """Initialize Gemini API"""
        try:
            import os
            api_key = os.getenv('GEMINI_API_KEY', 'test-key')
            genai.configure(api_key=api_key)
            
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.function_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            logger.info("Gemini initialized successfully")
        except Exception as e:
            logger.error(f"Gemini initialization error: {str(e)}")
            self.model = None
            self.function_model = None
    
    def _initialize_intelligent_search(self):
        """Initialize intelligent search components"""
        try:
            if self.enable_intelligent_search and IntelligentSearchEngine:
                self.search_engine = IntelligentSearchEngine()
                self.context_manager = ConversationContextManager()
                self.query_resolver = ContextAwareQueryResolver(self.context_manager)
                self.intent_detector = ContextualIntentDetector()
                self.presenter = ConfidenceBasedPresenter()
                logger.info("Intelligent search components initialized")
            else:
                self.search_engine = None
                self.context_manager = None
                self.query_resolver = None
                self.intent_detector = None
                self.presenter = None
                logger.info("Intelligent search disabled or components not available")
        except Exception as e:
            logger.error(f"Intelligent search initialization error: {str(e)}")
            self.search_engine = None
            self.context_manager = None
            self.query_resolver = None
            self.intent_detector = None
            self.presenter = None
    
    async def process_message_with_functions(self, prompt: str, session_id: str, 
                                           isletme_id: str) -> Optional[Dict[str, Any]]:
        """Process message with SIMPLE intent detection"""
        try:
            # BASİT intent detector'ı kullan
            import asyncio
            from .simple_intent_system import simple_intent_system
            
            # Intent detection
            intent_result = await simple_intent_system.detect_intent(prompt)
            
            if not intent_result:
                return await self._fallback_processing(prompt, session_id, isletme_id)
            
            intent = intent_result.get("intent")
            method = intent_result.get("method")
            confidence = intent_result.get("confidence", 0.8)
            
            # BASİT INTENT HANDLING
            if intent in ["greeting", "thanks", "farewell", "acknowledgment", "negative", "clarification_needed"]:
                # Direct response
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": intent,
                    "final_response": intent_result.get("response", "Anlayamadım."),
                    "confidence": confidence,
                    "method": f"simple_{method}"
                }
            
            elif intent == "business_info":
                # Function call
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": intent,
                    "function_call": intent_result.get("function_call"),
                    "confidence": confidence,
                    "method": f"simple_{method}"
                }
            
            elif intent == "product_inquiry":
                # Enhanced semantic search - SADECE ürün sorguları için
                try:
                    enhanced_result = await self._process_with_enhanced_search(
                        prompt, session_id, isletme_id, intent_result
                    )
                    if enhanced_result:
                        enhanced_result["confidence"] = confidence
                        enhanced_result["intent"] = intent
                        enhanced_result["method"] = f"enhanced_semantic_search"
                        return enhanced_result
                except Exception as e:
                    logger.error(f"Enhanced search processing error: {str(e)}")
                
                # Fallback
                return await self._fallback_processing(prompt, session_id, isletme_id)
            
            elif intent == "needs_llm":
                # LLM'e gönder - SADECE karmaşık durumlar için
                try:
                    llm_result = await self._force_llm_analysis(prompt, session_id, isletme_id)
                    if llm_result:
                        return llm_result
                except Exception as e:
                    logger.error(f"LLM analysis error: {str(e)}")
                
                # Son çare fallback
                return await self._fallback_processing(prompt, session_id, isletme_id)
            
            else:
                # Bilinmeyen intent - fallback
                return await self._fallback_processing(prompt, session_id, isletme_id)
                
        except Exception as e:
            logger.error(f"Hybrid processing error: {str(e)}")
            return await self._fallback_processing(prompt, session_id, isletme_id)
    
    async def _force_llm_analysis(self, prompt: str, session_id: str, isletme_id: str) -> Dict[str, Any]:
        """ZORLA LLM analizi - son çare"""
        try:
            # Gerçek Gemini API çağrısı burada olacak
            # Şimdilik mock response
            
            return {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "product_inquiry",
                "final_response": f"'{prompt}' hakkında size yardımcı olmaya çalışıyorum. Lütfen biraz daha detay verebilir misiniz?",
                "confidence": 0.7,
                "method": "force_llm"
            }
            
        except Exception as e:
            logger.error(f"Force LLM analysis error: {str(e)}")
            return await self._fallback_processing(prompt, session_id, isletme_id)
    
    async def _process_with_enhanced_search(self, prompt: str, session_id: str, 
                                          isletme_id: str, intent_result: dict) -> Optional[Dict[str, Any]]:
        """Enhanced semantic search ile işle"""
        try:
            # Enhanced semantic search import
            from .enhanced_semantic_search import EnhancedSemanticSearch
            
            # Search engine oluştur
            search_engine = EnhancedSemanticSearch()
            
            # Test products - gerçek DB'den gelecek
            products = await self._get_products_for_search(isletme_id)
            
            if not products:
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_inquiry",
                    "final_response": "Şu anda ürün bilgilerimize erişemiyorum. Lütfen daha sonra tekrar deneyin.",
                    "confidence": 0.5,
                    "method": "no_products_available"
                }
            
            # Enhanced search yap
            matches = search_engine.search(prompt, products, limit=3, min_score=0.2)
            
            # DEBUG
            logger.info(f"Enhanced search for '{prompt}': found {len(matches)} matches")
            for match in matches:
                logger.info(f"  - {match.product['name']}: score={match.score:.3f}")
            
            if matches:
                # En iyi match'i al
                best_match = matches[0]
                
                # Context hint'e göre response oluştur
                context_hint = intent_result.get("context_hint", "")
                
                if "price" in context_hint:
                    response = f"🔍 Benzer özellikli ürünler buldum:\n\n"
                    response += f"**{best_match.product['name']}** - {best_match.product.get('price', 'Fiyat bilgisi yok')} TL\n"
                    response += f"*{best_match.match_type.title()} eşleşme ({best_match.confidence:.0%})*\n"
                    response += f"✨ Eşleşen özellikler: {', '.join(best_match.matched_features[:3])}\n\n"
                    
                    if len(matches) > 1:
                        response += "Diğer benzer ürünler:\n"
                        for match in matches[1:]:
                            response += f"• {match.product['name']} - {match.product.get('price', 'Fiyat bilgisi yok')} TL\n"
                else:
                    response = f"🔍 Aradığınız ürünle ilgili bilgiler:\n\n"
                    response += f"**{best_match.product['name']}**\n"
                    response += f"Fiyat: {best_match.product.get('price', 'Bilgi yok')} TL\n"
                    response += f"Renk: {best_match.product.get('color', 'Bilgi yok')}\n"
                    response += f"*{best_match.match_type.title()} eşleşme ({best_match.confidence:.0%})*\n\n"
                    
                    if len(matches) > 1:
                        response += "Benzer ürünler:\n"
                        for match in matches[1:]:
                            response += f"• {match.product['name']}\n"
                
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_inquiry",
                    "final_response": response,
                    "confidence": best_match.confidence,
                    "method": "enhanced_semantic_search",
                    "search_results": [match.product for match in matches]
                }
            else:
                # No matches found
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_inquiry",
                    "final_response": f"'{prompt}' ile eşleşen ürün bulamadım. Lütfen daha spesifik olabilir misiniz? Örneğin: 'siyah gecelik', 'hamile pijama' gibi.",
                    "confidence": 0.6,
                    "method": "no_search_results"
                }
                
        except Exception as e:
            logger.error(f"Enhanced search error: {str(e)}")
            return None
    
    async def _get_products_for_search(self, isletme_id: str) -> List[Dict[str, Any]]:
        """Arama için ürünleri getir - mock data"""
        # Gerçek sistemde DB'den gelecek
        return [
            {
                "id": 1,
                "name": "Çiçek ve Yaprak Desenli Dekolteli Gecelik",
                "color": "EKRU",
                "price": 1415.33
            },
            {
                "id": 2,
                "name": "Afrika Etnik Baskılı Dantelli \"Africa Style\" Gecelik",
                "color": "BEJ",
                "price": 1299.9
            },
            {
                "id": 3,
                "name": "Siyah Tüllü Askılı Gecelik",
                "color": "SİYAH",
                "price": 890.50
            },
            {
                "id": 4,
                "name": "Dantelli Önü Düğmeli Hamile Lohusa Gecelik",
                "color": "EKRU",
                "price": 1632.33
            },
            {
                "id": 5,
                "name": "Çiçek Desenli Tüllü Takım",
                "color": "PEMBE",
                "price": 1200.00
            },
            {
                "id": 6,
                "name": "Dantelli Önü Düğmeli Hamile Lohusa 3'lü Pijama Takımı",
                "color": "EKRU",
                "price": 3855.9
            },
            {
                "id": 7,
                "name": "Dantelli Önü Düğmeli Hamile Lohusa Sabahlık Takımı",
                "color": "BEJ",
                "price": 3621.9
            }
        ]
    
    async def _fallback_processing(self, prompt: str, session_id: str, isletme_id: str) -> Dict[str, Any]:
        """SON ÇARE fallback - asla unknown döndürme!"""
        
        # İnsan desteğine yönlendir
        return {
            "session_id": session_id,
            "isletme_id": isletme_id,
            "intent": "human_transfer",
            "final_response": "Bu konuda size daha iyi yardımcı olabilmek için WhatsApp üzerinden iletişime geçebilirsiniz: 0555 555 55 55",
            "confidence": 0.9,
            "method": "human_transfer_fallback"
        }
        if not self.enable_function_calling:
            return await self.process_message(prompt, session_id, isletme_id)
        
        try:
            # Gerçek Gemini function calling
            if not self.function_model:
                logger.warning("Function model not available, falling back to traditional processing")
                return await self.process_message(prompt, session_id, isletme_id)
            
            # Function definitions
            functions = [
                {
                    "name": "getProductInfo",
                    "description": "Ürün bilgilerini getir (fiyat, stok, detay, renk, beden)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_name": {
                                "type": "string",
                                "description": "Ürün adı (gecelik, pijama, elbise vb.)"
                            },
                            "query_type": {
                                "type": "string",
                                "description": "Sorgu türü",
                                "enum": ["fiyat", "stok", "detay", "renk", "beden"]
                            }
                        },
                        "required": ["product_name", "query_type"]
                    }
                },
                {
                    "name": "getGeneralInfo",
                    "description": "İşletme genel bilgilerini getir (telefon, iade, kargo, site)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "info_type": {
                                "type": "string",
                                "description": "Bilgi türü",
                                "enum": ["telefon", "iade", "kargo", "site"]
                            }
                        },
                        "required": ["info_type"]
                    }
                }
            ]
            
            # Gemini'ye function calling ile sorgu gönder
            system_prompt = """Sen bir Türk butik mağazasının müşteri hizmetleri asistanısın. 
            Müşteri sorularını analiz et ve uygun function'ı çağır.
            
            Ürün soruları için getProductInfo function'ını kullan.
            İşletme bilgileri için getGeneralInfo function'ını kullan.
            
            Türkçe ürün adlarındaki ekleri temizle (geceliği -> gecelik).
            """
            
            # Mock Gemini function calling response
            message = prompt.lower()
            
            # Önce ürün adını çıkar
            product_name = self._extract_product_name(message)
            
            # MVP: Context resolution for follow-up questions
            if not product_name:
                product_name = self._resolve_contextual_query(message, session_id)
            
            # Ürün sorguları - fiyat
            if any(word in message for word in ["fiyat", "kaç para", "ne kadar", "price"]):
                if product_name:
                    return {
                        "session_id": session_id,
                        "isletme_id": isletme_id,
                        "intent": "product_query",
                        "function_call": {
                            "name": "getProductInfo",
                            "args": {"product_name": product_name, "query_type": "fiyat"}
                        },
                        "confidence": 0.9,
                        "method": "function_calling"
                    }
            
            # Ürün sorguları - stok
            elif any(word in message for word in ["stok", "var mı", "mevcut", "stock"]):
                if product_name:
                    return {
                        "session_id": session_id,
                        "isletme_id": isletme_id,
                        "intent": "product_query",
                        "function_call": {
                            "name": "getProductInfo",
                            "args": {"product_name": product_name, "query_type": "stok"}
                        },
                        "confidence": 0.9,
                        "method": "function_calling"
                    }
            
            # Ürün sorguları - renk
            elif any(word in message for word in ["renk", "color", "renkler"]):
                if product_name:
                    return {
                        "session_id": session_id,
                        "isletme_id": isletme_id,
                        "intent": "product_query",
                        "function_call": {
                            "name": "getProductInfo",
                            "args": {"product_name": product_name, "query_type": "renk"}
                        },
                        "confidence": 0.9,
                        "method": "function_calling"
                    }
            
            # Ürün sorguları - beden
            elif any(word in message for word in ["beden", "size", "bedenleri"]):
                if product_name:
                    return {
                        "session_id": session_id,
                        "isletme_id": isletme_id,
                        "intent": "product_query",
                        "function_call": {
                            "name": "getProductInfo",
                            "args": {"product_name": product_name, "query_type": "beden"}
                        },
                        "confidence": 0.9,
                        "method": "function_calling"
                    }
            
            # Katalog sorguları
            elif product_name == "katalog":
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "catalog_query",
                    "function_call": {
                        "name": "getProductInfo",
                        "args": {"product_name": "katalog", "query_type": "katalog"}
                    },
                    "confidence": 0.9,
                    "method": "function_calling"
                }
            
            # Sadece ürün adı varsa - genel bilgi
            elif product_name:
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_query",
                    "function_call": {
                        "name": "getProductInfo",
                        "args": {"product_name": product_name, "query_type": "detay"}
                    },
                    "confidence": 0.8,
                    "method": "function_calling"
                }
            
            # İşletme bilgi sorguları - GELİŞTİRİLMİŞ PATTERN MATCHING
            elif any(word in message for word in ["telefon", "phone", "iletişim", "numar", "ara", "tel"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "meta_query",
                    "function_call": {
                        "name": "getGeneralInfo",
                        "args": {"info_type": "telefon"}
                    },
                    "confidence": 0.95,
                    "method": "function_calling"
                }
            
            # İADE SORULARI - ÇOK DAHA KAPSAMLI
            elif any(phrase in message for phrase in [
                "iade", "return", "geri", "iade var", "iade var mı", "iade yapabilir", 
                "iade edebilir", "geri verebilir", "değişim", "değiştir", "iade şart",
                "iade policy", "iade nasıl", "nasıl iade", "iade süresi", "kaç gün iade"
            ]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "meta_query",
                    "function_call": {
                        "name": "getGeneralInfo",
                        "args": {"info_type": "iade"}
                    },
                    "confidence": 0.95,
                    "method": "function_calling"
                }
            
            elif any(word in message for word in ["kargo", "teslimat", "shipping", "cargo"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "meta_query",
                    "function_call": {
                        "name": "getGeneralInfo",
                        "args": {"info_type": "kargo"}
                    },
                    "confidence": 0.95,
                    "method": "function_calling"
                }
            
            elif any(word in message for word in ["site", "web", "website"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "meta_query",
                    "function_call": {
                        "name": "getGeneralInfo",
                        "args": {"info_type": "site"}
                    },
                    "confidence": 0.95,
                    "method": "function_calling"
                }
            
            # Selamlama
            elif any(word in message for word in ["merhaba", "selam", "hello", "hi"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "greeting",
                    "final_response": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?",
                    "confidence": 0.95,
                    "method": "direct_response"
                }
            
            # Teşekkür ve onay
            elif any(word in message for word in ["teşekkür", "sağol", "thanks", "thank"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "thanks",
                    "final_response": "Rica ederim! Başka sorunuz var mı?",
                    "confidence": 0.95,
                    "method": "direct_response"
                }
            
            # Onay ve basit cevaplar
            elif any(word in message for word in ["tamam", "ok", "okay", "anladım", "peki", "iyi"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "acknowledgment",
                    "final_response": "Başka bir sorunuz var mı? Size nasıl yardımcı olabilirim?",
                    "confidence": 0.9,
                    "method": "direct_response"
                }
            
            # Vedalaşma - AKILLI CONTEXT AWARE
            elif any(phrase in message for phrase in ["iyi günler", "güle güle", "hoşça kal", "görüşürüz", "bay bay", "bye", "tamam iyi günler"]):
                # Context'e göre karar ver - gelişmiş heuristic
                if any(word in message for word in ["görüşürüz", "güle güle", "hoşça kal", "bay", "bye"]) or "tamam iyi günler" in message:
                    # Kesin veda
                    response = "Hoşça kalın! Tekrar bekleriz. 😊"
                elif len(message.split()) <= 2 and "iyi günler" in message:
                    # Sadece "iyi günler" - muhtemelen veda
                    response = "İyi günler dileriz! Tekrar bekleriz. 😊"
                else:
                    # Belirsiz - genel cevap
                    response = "İyi günler! Size nasıl yardımcı olabilirim?"
                
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "greeting_or_farewell",
                    "final_response": response,
                    "confidence": 0.85,
                    "method": "direct_response"
                }
            
            # ONAY VE KAPANIŞ - YENİ EKLEME
            elif any(phrase in message for phrase in ["yok", "yok teşekkürler", "başka soru yok", "o kadar", "bu kadar"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "conversation_end",
                    "final_response": "Teşekkür ederiz! İyi günler dileriz. 😊",
                    "confidence": 0.9,
                    "method": "direct_response"
                }
            
            # Fallback to traditional processing
            return await self.process_message(prompt, session_id, isletme_id)
            
        except Exception as e:
            logger.error(f"Function calling error: {str(e)}")
            return await self.process_message(prompt, session_id, isletme_id)
    
    def _extract_product_name(self, message: str) -> str:
        """Mesajdan ürün adını çıkar - MVP Güçlendirilmiş versiyon"""
        message_lower = message.lower()
        
        # 1. Genel katalog sorguları
        catalog_queries = [
            "hangi ürünler var", "hangi ürünleriniz var", "ürünleriniz neler",
            "stokta ne var", "stokta neler var", "mevcut ürünler",
            "katalog", "ürün listesi", "ne satıyorsunuz"
        ]
        
        for catalog_query in catalog_queries:
            if catalog_query in message_lower:
                return "katalog"  # Özel keyword
        
        # 2. Birleşik ürün adları - daha kapsamlı
        compound_products = [
            ("afrika gecelik", ["afrika", "gecelik"]),
            ("afrika geceliği", ["afrika", "gecelik"]),
            ("africa gecelik", ["africa", "gecelik"]),
            ("africa style", ["africa", "style"]),
            ("hamile gecelik", ["hamile", "gecelik"]),
            ("hamile geceliği", ["hamile", "gecelik"]),
            ("hamile pijama", ["hamile", "pijama"]),
            ("hamile pijamayı", ["hamile", "pijama"]),
            ("hamile takım", ["hamile", "takım"]),
            ("hamile takımı", ["hamile", "takım"]),
            ("hamile lohusa takım", ["hamile", "takım"]),  # Özel handling
            ("hamile lohusa takımı", ["hamile", "takım"]),
            ("lohusa takım", ["hamile", "takım"]),  # lohusa -> hamile mapping
            ("lohusa takımı", ["hamile", "takım"]),
            ("lohusa gecelik", ["lohusa", "gecelik"]),
            ("lohusa pijama", ["lohusa", "pijama"]),
            ("pijama takımı", ["pijama", "takım"]),
            ("pijama takimi", ["pijama", "takım"]),
            ("gecelik takımı", ["gecelik", "takım"]),
            ("sabahlık takımı", ["sabahlık", "takım"])
        ]
        
        for product_name, keywords in compound_products:
            if all(keyword in message_lower for keyword in keywords):
                return product_name.replace("geceliği", "gecelik").replace("pijamayı", "pijama")
        
        # 3. Renk + ürün kombinasyonları - genişletilmiş
        colors = [
            "siyah", "beyaz", "kırmızı", "mavi", "yeşil", "sarı", "pembe", "mor", 
            "lacivert", "bordo", "bej", "ekru", "gri", "krem", "turuncu"
        ]
        
        basic_products = {
            "gecelik": ["gecelik", "geceliği", "geceliğin", "gecelig", "geceliğe", "geceliğim"],
            "pijama": ["pijama", "pijamayı", "pijamanın", "pijamaya", "pijamalar", "pijamam"],
            "elbise": ["elbise", "elbiseyi", "elbisenin", "elbiseye", "elbiseler", "elbisem"],
            "sabahlık": ["sabahlık", "sabahlığı", "sabahlığın", "sabahlığa", "sabahlıklar"],
            "takım": ["takım", "takımı", "takımın", "takıma", "takimi", "takımlar"]
        }
        
        # Renk + ürün eşleştirmesi
        for color in colors:
            if color in message_lower:
                for product, variations in basic_products.items():
                    if any(var in message_lower for var in variations):
                        return f"{color} {product}"
        
        # 4. Temel ürün kategorileri
        for product, variations in basic_products.items():
            for variation in variations:
                if variation in message_lower:
                    return product
        
        # 5. Özel durumlar ve synonyms
        special_cases = {
            "hamile": "hamile gecelik",
            "lohusa": "lohusa gecelik", 
            "afrika": "afrika gecelik",
            "africa": "afrika gecelik",
            "etnik": "afrika gecelik",
            "dantelli": "dantelli gecelik",
            "dantel": "dantelli gecelik"
        }
        
        for keyword, product in special_cases.items():
            if keyword in message_lower and not any(p in message_lower for p in basic_products.keys()):
                return product
        
        # 6. Yazım hatası düzeltmeleri
        typo_corrections = {
            "gecelig": "gecelik",
            "afirca": "afrika",
            "afirka": "afrika", 
            "pyjama": "pijama",
            "pajama": "pijama"
        }
        
        for typo, correct in typo_corrections.items():
            if typo in message_lower:
                return correct
        
        return ""
    
    async def process_message(self, prompt: str, session_id: str, 
                            isletme_id: str) -> Optional[Dict[str, Any]]:
        """Traditional message processing"""
        try:
            # Mock traditional processing
            message = prompt.lower()
            
            if any(word in message for word in ["merhaba", "selam"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "greeting",
                    "entities": [],
                    "confidence": 0.95,
                    "method": "intent_detection"
                }
            
            elif any(word in message for word in ["fiyat", "kaç para"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_query",
                    "entities": [
                        {"type": "attribute", "value": "fiyat", "confidence": 0.9}
                    ],
                    "confidence": 0.8,
                    "method": "intent_detection"
                }
            
            else:
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "unknown",
                    "entities": [],
                    "confidence": 0.5,
                    "method": "intent_detection"
                }
                
        except Exception as e:
            logger.error(f"Traditional processing error: {str(e)}")
            return None
    
    async def health_check(self) -> bool:
        """Health check"""
        return True
    
    def _resolve_contextual_query(self, message: str, session_id: str) -> str:
        """MVP: Resolve contextual queries using simple context"""
        message_lower = message.lower().strip()
        
        # Check if this is a contextual query
        contextual_patterns = [
            # Fiyat soruları
            ["fiyat", "kaç para", "ne kadar", "price", "ücret"],
            # Stok soruları  
            ["stok", "var mı", "mevcut", "stock", "kaldı"],
            # Detay soruları
            ["detay", "bilgi", "özellik", "nasıl", "info"],
            # Renk soruları
            ["renk", "color", "renkler", "hangi renk"],
            # Beden soruları
            ["beden", "size", "bedenleri", "hangi beden"]
        ]
        
        is_contextual = False
        for patterns in contextual_patterns:
            if any(pattern in message_lower for pattern in patterns):
                is_contextual = True
                break
        
        if is_contextual:
            # Try to get context from semantic search service
            try:
                from .simple_semantic_search import semantic_search
                if semantic_search and hasattr(semantic_search, 'get_context'):
                    context_product = semantic_search.get_context(session_id)
                    if context_product:
                        return context_product
            except Exception as e:
                logger.error(f"Context resolution error: {str(e)}")
        
        return ""
    
    async def _process_with_intelligent_search(self, prompt: str, session_id: str, 
                                             isletme_id: str) -> Optional[Dict[str, Any]]:
        """Process message using intelligent search system"""
        try:
            # Get conversation context
            context = self.context_manager.get_context(session_id)
            
            # Detect intent with context
            detected_intent = self.intent_detector.detect_intent(prompt, context)
            
            # Resolve ambiguous queries
            resolved_query = self.query_resolver.resolve_ambiguous_query(prompt, session_id)
            
            # Use resolved query for search
            search_query = resolved_query.resolved_query
            
            # Get products from database service (mock for now)
            products = await self._get_products_for_search(isletme_id)
            
            if not products:
                logger.warning("No products available for search")
                return None
            
            # Perform intelligent search
            search_result = await self.search_engine.search(search_query, products, limit=5)
            
            # Add conversation turn to context
            self.context_manager.add_conversation_turn(
                session_id, prompt, "", detected_intent.intent.value
            )
            
            # Present results based on confidence
            if search_result.matches:
                # Convert search matches to fused results format
                from .result_fusion_engine import FusedResult
                from .intelligent_search_engine import SearchMethod
                
                fused_results = []
                for match in search_result.matches:
                    fused_result = FusedResult(
                        product=match.product,
                        final_score=match.score,
                        confidence=match.confidence,
                        method_scores={match.method: match.score},
                        method_ranks={match.method: 1},
                        fusion_explanation=match.explanation,
                        validation_score=0.8,
                        feature_matches=match.feature_matches or []
                    )
                    fused_results.append(fused_result)
                
                # Present results
                presentation = self.presenter.present_results(
                    fused_results, search_result.alternatives, 
                    search_result.overall_confidence, prompt
                )
                
                # Format for display
                formatted_response = self.presenter.format_for_display(presentation)
                
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": detected_intent.intent.value,
                    "intelligent_search_result": {
                        "query": search_query,
                        "original_query": prompt,
                        "matches_found": len(search_result.matches),
                        "overall_confidence": search_result.overall_confidence,
                        "search_time_ms": search_result.total_time_ms,
                        "presentation_mode": presentation.mode.value
                    },
                    "final_response": formatted_response,
                    "confidence": detected_intent.confidence,
                    "method": "intelligent_search"
                }
            
            else:
                # No matches found, provide helpful response
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": detected_intent.intent.value,
                    "intelligent_search_result": {
                        "query": search_query,
                        "original_query": prompt,
                        "matches_found": 0,
                        "overall_confidence": 0.0
                    },
                    "final_response": f"'{search_query}' için uygun ürün bulunamadı. Farklı arama terimleri deneyebilirsiniz.",
                    "confidence": detected_intent.confidence,
                    "method": "intelligent_search"
                }
                
        except Exception as e:
            logger.error(f"Intelligent search processing error: {str(e)}")
            return None
    
    async def _get_products_for_search(self, isletme_id: str) -> List[Dict[str, Any]]:
        """Get products for search from database service"""
        try:
            # Import database service
            from .database_service import DatabaseService
            
            db_service = DatabaseService()
            
            # Get business data
            if isletme_id in db_service.businesses:
                business_data = db_service.businesses[isletme_id]
                return business_data.get('products', [])
            else:
                # Fallback to default products
                return db_service.products
                
        except Exception as e:
            logger.error(f"Error getting products for search: {str(e)}")
            return []