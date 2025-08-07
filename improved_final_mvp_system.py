#!/usr/bin/env python3
"""
Improved Final MVP Chatbot System
Addresses all edge cases and problematic scenarios
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import google.generativeai as genai
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
from aws_bedrock_integration import get_bedrock_client
from enhanced_conversation_handler import EnhancedConversationHandler
from smart_cache_system import SmartCacheSystem
from fixed_responses import get_fixed_responses
from color_grouping_system import group_products_by_base_name, format_grouped_products
from database_analyzer import DatabaseAnalyzer

# Import RAG search system
try:
    from rag_product_search import RAGProductSearch
    RAG_SEARCH_AVAILABLE = True
except ImportError:
    RAG_SEARCH_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Product:
    name: str
    color: str
    price: float
    discount: float
    final_price: float
    category: str
    stock: int

@dataclass
class IntentResult:
    intent: str
    entities: Dict[str, str]
    confidence: float

@dataclass
class ChatResponse:
    message: str
    intent: str
    confidence: float
    products_found: int = 0
    processing_time: float = 0.0

class ImprovedFinalMVPChatbot:
    def __init__(self):
        """Initialize the improved MVP chatbot system"""
        logger.info("Initializing Improved Final MVP Chatbot System...")
        
        # Load data
        self.products = self._load_products()
        self.business_info = self._load_business_info()
        
        # Setup AI models (Gemini + Bedrock)
        self._setup_gemini()
        self._setup_bedrock()
        
        # Setup RAG search system
        self.rag_search = None
        if RAG_SEARCH_AVAILABLE:
            try:
                self.rag_search = RAGProductSearch()
                if self.rag_search.is_available():
                    logger.info("✅ RAG search system initialized successfully")
                else:
                    logger.warning("⚠️ RAG search system not available")
            except Exception as e:
                logger.error(f"RAG search initialization failed: {e}")
                self.rag_search = None
        
        # Initialize enhanced conversation handler
        self.conversation_handler = EnhancedConversationHandler()
        
        # Initialize smart cache system
        self.smart_cache = SmartCacheSystem(default_ttl=1800, max_size=500)  # 30 minutes, 500 entries
        
        # Initialize database analyzer
        self.db_analyzer = DatabaseAnalyzer()
        
        # Initialize response templates
        self.fixed_responses = get_fixed_responses(self.business_info, self._get_whatsapp_support_text)
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'gemini_calls': 0,
            'fallback_calls': 0,
            'cache_hits': 0,
            'average_response_time': 0.0
        }
        
        # Intent cache for ultra-fast responses
        self.intent_cache = {}
        
        logger.info(f"✅ Improved MVP Chatbot initialized with {len(self.products)} products")
    
    def _check_intent_cache(self, message_lower: str) -> Optional[IntentResult]:
        """Check intent cache for exact matches"""
        if message_lower in self.intent_cache:
            self.stats['cache_hits'] += 1
            return self.intent_cache[message_lower]
        return None
    
    def _cache_intent_result(self, message_lower: str, result: IntentResult):
        """Cache intent result for future use"""
        # Keep cache size manageable (max 1000 entries)
        if len(self.intent_cache) > 1000:
            # Remove oldest 200 entries
            old_keys = list(self.intent_cache.keys())[:200]
            for key in old_keys:
                del self.intent_cache[key]
        
        self.intent_cache[message_lower] = result
    
    def _ultra_fast_rules(self, message_lower: str) -> Optional[IntentResult]:
        """Ultra-fast rules for 100% certain cases"""
        # Exact matches for common phrases
        exact_matches = {
            'merhaba': IntentResult('greeting', {}, 0.99),
            'selam': IntentResult('greeting', {}, 0.99),
            'hello': IntentResult('greeting', {}, 0.99),
            'hi': IntentResult('greeting', {}, 0.99),
            'teşekkürler': IntentResult('thanks', {}, 0.99),
            'teşekkür ederim': IntentResult('thanks', {}, 0.99),
            'sağol': IntentResult('thanks', {}, 0.99),
            'thanks': IntentResult('thanks', {}, 0.99),
            'tamam': IntentResult('thanks', {}, 0.99),
            'peki': IntentResult('thanks', {}, 0.99),
            'anladım': IntentResult('thanks', {}, 0.99),
            'güle güle': IntentResult('goodbye', {}, 0.99),
            'görüşürüz': IntentResult('goodbye', {}, 0.99),
            'bye': IntentResult('goodbye', {}, 0.99),
            'hoşça kal': IntentResult('goodbye', {}, 0.99),
            'telefon numaranız': IntentResult('phone_inquiry', {}, 0.99),
            'telefon numaranız nedir': IntentResult('phone_inquiry', {}, 0.99),
            'telefon': IntentResult('phone_inquiry', {}, 0.95),
        }
        
        if message_lower in exact_matches:
            return exact_matches[message_lower]
        
        # Pattern-based ultra-fast rules
        
        # SMART PRODUCT+COLOR QUERIES (Highest priority!)
        colors = ['siyah', 'beyaz', 'kırmızı', 'mavi', 'yeşil', 'mor', 'pembe', 'sarı', 'bordo', 'vizon', 'ekru', 'lacivert']
        products = ['afrika', 'hamile', 'dantelli', 'gecelik', 'pijama', 'sabahlık', 'takım']
        
        color_found = None
        product_found = None
        
        for color in colors:
            if color in message_lower:
                color_found = color
                break
                
        for product in products:
            if product in message_lower:
                product_found = product
                break
        
        # Smart parsing for size queries: "afrika geceliğin 42 si var mı"
        import re
        size_pattern = r'(\w+)\s*(\w+).*?(\d+)\s*(si|sı|beden|numara).*?(var mı|mevcut|stok)'
        size_match = re.search(size_pattern, message_lower)
        
        if size_match:
            product_name = size_match.group(1)
            size = size_match.group(3)
            return IntentResult('product_size_query', {
                'product_name': product_name,
                'size': size
            }, 0.95)
        
        # Smart parsing: "afrika geceliğin siyahı var mı" = specific product color query
        if color_found and product_found and any(phrase in message_lower for phrase in ['var mı', 'mevcut', 'stok']):
            # This is a specific product color query - should search for that exact product+color
            return IntentResult('product_color_query', {
                'product_name': product_found,
                'color': color_found
            }, 0.95)
        
        # SMART CONTEXT-AWARE COLOR QUERIES
        context_indicators = ['bunun', 'şunun', 'onun', 'bu ürünün', 'şu ürünün', 'o ürünün']
        conversation_flow_indicators = ['sağolasın', 'teşekkürler', 'tamam', 'anladım', 'peki']
        
        has_context_indicator = any(indicator in message_lower for indicator in context_indicators)
        has_conversation_flow = any(indicator in message_lower for indicator in conversation_flow_indicators)
        
        # If user says thanks/acknowledgment + color query = definitely followup about previous product
        if color_found and has_conversation_flow and any(phrase in message_lower for phrase in ['var mı', 'mevcut', 'stok']):
            if hasattr(self, 'conversation_handler') and self.conversation_handler.context.last_products:
                return IntentResult('followup', {'color': color_found}, 0.95)
        
        # Regular context-aware color queries
        if color_found and (any(phrase in message_lower for phrase in ['var mı', 'mevcut', 'stok']) or has_context_indicator):
            # Context-aware: If we have previous products OR context indicators, it's followup
            if (hasattr(self, 'conversation_handler') and self.conversation_handler.context.last_products) or has_context_indicator:
                return IntentResult('followup', {'color': color_found}, 0.95)
            else:
                # No context, treat as new product search
                return IntentResult('product_search', {'color': color_found}, 0.95)
        
        # Handle general category queries (need clarification) - HIGHEST PRIORITY
        general_category_patterns = [
            r'^gecelik$', r'^gecelik var mı$', r'^gecelik mevcut mu$',
            r'^pijama$', r'^pijama var mı$', r'^pijama mevcut mu$',
            r'^sabahlık$', r'^sabahlık var mı$', r'^sabahlık mevcut mu$',
            r'^takım$', r'^takım var mı$', r'^takım mevcut mu$'
        ]
        
        import re
        for pattern in general_category_patterns:
            if re.match(pattern, message_lower.strip()):
                # Extract category name
                category = message_lower.strip().split()[0].title()
                response = f"{category} arıyorsunuz. Hangi özellikte olsun?\n\n💡 **Örnekler:**\n• 'siyah {category.lower()}'\n• 'afrika {category.lower()}'\n• 'hamile {category.lower()}'\n• 'dantelli {category.lower()}'"
                return IntentResult('clarification_needed', {'response': response}, 0.95)
        
        # Handle vague price inquiries (HIGHER PRIORITY than context)
        price_patterns = ['fiyatı nedir', 'fiyatı ne', 'kaç para', 'ne kadar']
        if any(pattern in message_lower for pattern in price_patterns):
            # If it's EXACTLY these patterns, it's price inquiry regardless of context
            if message_lower.strip() in price_patterns:
                return IntentResult('price_inquiry', {}, 0.95)
        
        if message_lower.startswith('iade'):
            return IntentResult('return_policy', {}, 0.95)
        
        if 'telefon' in message_lower and ('numara' in message_lower or 'nedir' in message_lower):
            return IntentResult('phone_inquiry', {}, 0.95)
        
        return None
        
    def _setup_gemini(self):
        """Setup Gemini API with error handling"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found, using fallback intent detection only")
            self.model = None
            return
        
        try:
            genai.configure(api_key=api_key)
            # Use Gemini 1.5 Flash - best performance/cost ratio
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            logger.info("✅ Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"❌ Gemini setup error: {e}")
            self.model = None
    
    def _setup_bedrock(self):
        """Setup AWS Bedrock Mistral model"""
        try:
            self.bedrock_client = get_bedrock_client()
            if self.bedrock_client.bedrock_client:
                logger.info("✅ AWS Bedrock Mistral initialized successfully")
                self.use_bedrock = True
            else:
                logger.warning("⚠️ Bedrock not available, using Gemini fallback")
                self.use_bedrock = False
        except Exception as e:
            logger.error(f"❌ Bedrock setup error: {e}")
            self.use_bedrock = False
    
    def _bedrock_intent_detection(self, user_message: str, fallback_result: Optional[IntentResult]) -> Optional[IntentResult]:
        """Intent detection using AWS Bedrock Mistral"""
        try:
            intent_result = self.bedrock_client.intent_detection(user_message)
            
            if intent_result and intent_result.get('intent'):
                return IntentResult(
                    intent=intent_result['intent'],
                    entities=intent_result.get('entities', {}),
                    confidence=intent_result.get('confidence', 0.8)
                )
            
            return fallback_result
            
        except Exception as e:
            logger.error(f"❌ Bedrock intent detection error: {e}")
            return fallback_result
    
    def _load_products(self) -> List[Product]:
        """Load products with error handling"""
        try:
            with open('data/products.json', 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            products = []
            for item in products_data:
                products.append(Product(
                    name=item['name'],
                    color=item['color'],
                    price=item['price'],
                    discount=item['discount'],
                    final_price=item['final_price'],
                    category=item['category'],
                    stock=item['stock']
                ))
            
            return products
            
        except Exception as e:
            logger.error(f"❌ Error loading products: {e}")
            return []
    
    def _load_business_info(self) -> Dict:
        """Load business information with defaults"""
        try:
            with open('data/butik_meta.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading business info: {e}")
            return {
                'phone': '0212 123 45 67',
                'website': 'www.butik.com',
                'email': 'info@butik.com'
            }
    
    def _setup_response_templates(self):
        """Setup enhanced response templates with dynamic WhatsApp support"""
        # Get WhatsApp number for support
        whatsapp_support = self._get_whatsapp_support_text()
        
        self.fixed_responses = {
            "greeting": f"Merhaba! �e Size nasıl yardımcı olabilirim? Ürünlerimiz hakkında bilgi alabilir, fiyat sorabilirsiniz.\n\n{whatsapp_support}",
            "thanks": f"Rica ederim! 😊 Başka sorunuz var mı?\n\n{whatsapp_support}",
            "goodbye": f"Görüşmek üzere! İyi günler dilerim. 👋\n\n{whatsapp_support}",
            "phone_inquiry": f"📞 Telefon numaramız: {self.business_info.get('phone', '0212 123 45 67')}\n\n{whatsapp_support}",
            "return_policy": f"📋 İade politikamız: 14 gün içinde iade kabul edilir. Ürün kullanılmamış ve etiketli olmalıdır.\n\n{whatsapp_support}",
            "shipping_info": f"� Kargo şbilgileri: Türkiye geneli ücretsiz kargo. 1-3 iş günü içinde teslimat.\n\n{whatsapp_support}",
            "website_inquiry": f"🌐 Web sitemiz: {self.business_info.get('website', 'www.butik.com')}\n\n{whatsapp_support}",
            "size_inquiry": f"�g Beden bilgileri için web sitemizi ziyaret edebilirsiniz: {self.business_info.get('website', 'www.butik.com')} \n\n📞 Detaylı bilgi için bizi arayabilirsiniz: {self.business_info.get('phone', '0212 123 45 67')}\n\n{whatsapp_support}",
            "order_request": f"🛒 Sipariş vermek için web sitemizi ziyaret edebilirsiniz: {self.business_info.get('website', 'www.butik.com')} \n\n📞 Telefon ile sipariş: {self.business_info.get('phone', '0212 123 45 67')}\n\n{whatsapp_support}",
            "order_status": f"📦 Sipariş durumunuz için lütfen bizi arayın: {self.business_info.get('phone', '0212 123 45 67')} \n\nSipariş numaranızı hazır bulundurun.\n\n{whatsapp_support}",
            "complaint": f"� Üzgünlüz! Sorununuz için lütfen bizi arayın: {self.business_info.get('phone', '0212 123 45 67')} \n\nMüşteri hizmetlerimiz size yardımcı olacaktır.\n\n{whatsapp_support}",
            
            # Enhanced responses for edge cases
            "contact_info": f"📞 Telefon: {self.business_info.get('phone', '0212 123 45 67')}\n🌐 Web: {self.business_info.get('website', 'www.butik.com')}\n📧 Email: {self.business_info.get('email', 'info@butik.com')}\n\n{whatsapp_support}",
            "payment_info": f"💳 Ödeme seçenekleri için web sitemizi ziyaret edin: {self.business_info.get('website', 'www.butik.com')}\n📞 Detaylı bilgi: {self.business_info.get('phone', '0212 123 45 67')}\n\n{whatsapp_support}",
            "address_inquiry": f"📍 Adres bilgileri için lütfen bizi arayın: {self.business_info.get('phone', '0212 123 45 67')}\n\n{whatsapp_support}"
        }
    
    def _get_whatsapp_support_text(self, intent: str = None) -> str:
        """Get WhatsApp support text for specific intents only"""
        # Only show WhatsApp for these intents
        whatsapp_intents = [
            'product_search', 'return_policy', 'shipping_info', 
            'complaint', 'order_status', 'size_inquiry'
        ]
        
        if intent not in whatsapp_intents:
            return ""
        
        phone = self.business_info.get('phone', '0212 123 45 67')
        # Clean phone number for WhatsApp (remove spaces, dashes, etc.)
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if not present (assuming Turkey +90)
        if not clean_phone.startswith('90'):
            if clean_phone.startswith('0'):
                clean_phone = '90' + clean_phone[1:]
            else:
                clean_phone = '90' + clean_phone
        
        return f"\n\n💬 Size yardımcı olamadıysam WhatsApp'tan ulaşabilirsiniz: wa.me/{clean_phone}"
    
    def extract_intent_with_gemini(self, user_message: str) -> IntentResult:
        """Smart hybrid intent detection: Cache → Rules → LLM"""
        message_lower = user_message.lower().strip()
        

        
        # 1. EXACT CACHE CHECK (Instant, $0)
        cache_result = self._check_intent_cache(message_lower)
        if cache_result:
            return cache_result
        
        # 2. ULTRA-FAST RULES (1ms, $0) - Only for 100% certain cases
        fast_result = self._ultra_fast_rules(message_lower)
        if fast_result and fast_result.confidence >= 0.95:
            self._cache_intent_result(message_lower, fast_result)
            return fast_result
        
        # 3. LLM INTELLIGENCE (200ms, $0.001) - For everything else
        # Try Bedrock first, then Gemini fallback
        if self.use_bedrock and hasattr(self, 'bedrock_client'):
            llm_result = self._bedrock_intent_detection(user_message, fast_result)
            if llm_result and llm_result.confidence >= 0.7:
                self._cache_intent_result(message_lower, llm_result)
                return llm_result
        
        # Gemini fallback
        if self.model:
            llm_result = self._smart_llm_intent(user_message, fast_result)
            if llm_result.confidence >= 0.7:
                self._cache_intent_result(message_lower, llm_result)
                return llm_result
        
        # 4. FALLBACK (Only if LLM fails)
        fallback_result = self._enhanced_fallback_intent_detection(user_message)
        self._cache_intent_result(message_lower, fallback_result)
        return fallback_result
    
    def _smart_llm_intent(self, user_message: str, fallback_result: Optional[IntentResult]) -> IntentResult:
        
        """Try Gemini for unclear cases only"""
        function_declaration = {
            "name": "get_intent",
            "description": "Extract intent from user message",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": ["greeting", "thanks", "goodbye", "phone_inquiry", "return_policy", 
                                "shipping_info", "website_inquiry", "product_search", "price_inquiry", 
                                "stock_inquiry", "size_inquiry", "order_request", "order_status", 
                                "complaint", "general_info", "contact_info", "payment_info", 
                                "address_inquiry", "unclear"]
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Main product name or search query like 'afrika gecelik', 'hamile pijama'"
                    },
                    "product_features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Product features like hamile, dantelli, büyük_beden"
                    },
                    "color": {
                        "type": "string", 
                        "description": "Product color like siyah, beyaz, kırmızı"
                    },
                    "confidence": {"type": "number"}
                },
                "required": ["intent", "confidence"]
            }
        }
        
        prompt = f"""Türkçe e-ticaret mağazası chatbot asistanısın. Kullanıcı mesajını analiz et ve intent belirle.

MESAJ: "{user_message}"

İNTENT KATEGORİLERİ:
• greeting: merhaba, selam, iyi günler (konuşma başında), merhaba iyi günler
• goodbye: güle güle, görüşürüz, iyi günler (konuşma sonunda)
• product_search: ürün arama (giyim, aksesuar, ev eşyası vb.) + renk/özellik kombinasyonları
• return_policy: iade var mı, iade nasıl, geri verebilir miyim
• phone_inquiry: telefon numaranız, telefon, numara
• thanks: teşekkür, sağol, teşekkür ederim
• price_inquiry: fiyat, ne kadar, kaça
• stock_inquiry: stok, mevcut (sadece ürün özelliği olmadan)

ÖRNEKLERİ:
"merhaba iyi günler" → greeting (0.9)
"iade var mı" → return_policy (0.9)
"siyah dantelli gecelik var mı" → product_search (0.9)
"hamile pijama arıyorum" → product_search (0.9)
"afrika gecelik fiyat" → product_search (0.9) - ÜRÜN ADI + FİYAT = ÜRÜN ARAMA!
"dantelli gecelik ne kadar" → product_search (0.9) - ÜRÜN ADI + FİYAT = ÜRÜN ARAMA!
"telefon numaranız nedir" → phone_inquiry (0.9)

ÖNEMLİ KURAL: Ürün adı + fiyat sorusu = product_search (price_inquiry DEĞİL!)

ÇIKTI: Sadece function call kullan, metin yazma."""
        
        try:
            # Add timeout for performance
            start_time = time.time()
            response = self.model.generate_content(
                prompt,
                tools=[{"function_declarations": [function_declaration]}],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for faster, more consistent responses
                    max_output_tokens=50   # Very short output for cost optimization
                )
            )
            gemini_time = time.time() - start_time
            
            if gemini_time > 1.0:  # 1 second threshold
                logger.warning(f"Gemini API slow ({gemini_time:.3f}s), consider fallback")
            
            if (response.candidates and 
                response.candidates[0].content.parts):
                
                # Check for function call
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        
                        # Safely extract args
                        try:
                            args = {}
                            if hasattr(function_call, 'args') and function_call.args:
                                for key, value in function_call.args.items():
                                    args[key] = value
                            
                            self.stats['gemini_calls'] += 1
                            
                            return IntentResult(
                                intent=args.get('intent', 'unclear'),
                                entities={
                                    'product_name': args.get('product_name', ''),
                                    'product_features': args.get('product_features', []),
                                    'color': args.get('color', '')
                                },
                                confidence=args.get('confidence', 0.5)
                            )
                        except Exception as e:
                            logger.warning(f"Error parsing function call args: {e}")
                            continue
                
                # If no function call, try to parse text response
                if response.candidates[0].content.parts[0].text:
                    text_response = response.candidates[0].content.parts[0].text.lower()
                    self.stats['gemini_calls'] += 1
                    
                    # Simple text parsing for intent
                    if 'greeting' in text_response:
                        return IntentResult('greeting', {}, 0.8)
                    elif 'return_policy' in text_response:
                        return IntentResult('return_policy', {}, 0.8)
                    elif 'product_search' in text_response:
                        return IntentResult('product_search', {}, 0.8)
                    elif 'thanks' in text_response:
                        return IntentResult('thanks', {}, 0.8)
                
                logger.warning("No function call in Gemini response, using fallback")
                return fallback_result if fallback_result else self._enhanced_fallback_intent_detection(user_message)
            else:
                logger.warning("No valid Gemini response, using fallback")
                return fallback_result if fallback_result else self._enhanced_fallback_intent_detection(user_message)
                
        except Exception as e:
            logger.error(f"Gemini intent extraction error: {e}")
            self.stats['fallback_calls'] += 1
            return fallback_result if fallback_result else self._enhanced_fallback_intent_detection(user_message)
    
    def _enhanced_fallback_intent_detection(self, message: str) -> IntentResult:
        """Enhanced rule-based intent detection with better Turkish support"""
        message_lower = message.lower().strip()
        
        # Handle ambiguous inputs using conversation handler
        is_ambiguous, meanings = self.conversation_handler.detect_ambiguity(message)
        if is_ambiguous:
            resolved_intent = self.conversation_handler.resolve_ambiguity(message, meanings)
            return IntentResult(resolved_intent, {}, 0.8)
        
        # Handle general category queries (need clarification) - EXACT MATCH ONLY
        general_categories = ['gecelik', 'pijama', 'sabahlık', 'takım', 'elbise', 'şort']
        if message_lower.strip() in general_categories:
            category = message_lower.strip().title()
            response = f"{category} arıyorsunuz. Hangi renkte olsun?\n\n💡 **Örnek:** 'siyah {message_lower.strip()}', 'afrika {message_lower.strip()}'"
            return IntentResult('clarification_needed', {'response': response}, 0.95)
        
        # Handle incomplete inputs
        is_incomplete, response = self.conversation_handler.handle_incomplete_input(message)
        if is_incomplete:
            return IntentResult('clarification_needed', {'response': response}, 0.9)
        
        # Enhanced greeting patterns (check first - higher priority)
        greeting_patterns = ['merhaba', 'selam', 'hello', 'hi', 'hey']
        # Handle elongated greetings like "merhabaaaa", "iyi günleeee"
        normalized_message = ''.join(char if char not in 'aeiouüıöAEIOUÜIÖ' else char for i, char in enumerate(message_lower) if i == 0 or char != message_lower[i-1])
        
        # Check for mixed greetings first (merhaba iyi günler)
        has_greeting_word = any(word in normalized_message for word in greeting_patterns)
        has_iyi_gunler = 'iyi gün' in normalized_message or 'iyi gün' in message_lower
        
        if has_greeting_word and has_iyi_gunler:
            # Mixed greeting - prioritize greeting
            return IntentResult('greeting', {}, 0.9)
        elif has_greeting_word:
            return IntentResult('greeting', {}, 0.9)
        elif has_iyi_gunler:
            # Smart context analysis for "iyi günler"
            context_analysis = self._analyze_conversation_context(message_lower)
            if context_analysis == 'start':
                return IntentResult('greeting', {}, 0.9)
            elif context_analysis == 'end':
                return IntentResult('goodbye', {}, 0.9)
            else:
                # Default to greeting if uncertain
                return IntentResult('greeting', {}, 0.8)
        
        # This is now handled above in the mixed greeting section
        
        # Enhanced thanks patterns
        thanks_patterns = ['teşekkür', 'sağol', 'thanks', 'merci', 'eyvallah', 'tamam', 'ok', 'anladım', 'peki']
        if any(word in message_lower for word in thanks_patterns):
            return IntentResult('thanks', {}, 0.9)
        
        # Acknowledgment patterns (tamam, anladım, etc.)
        acknowledgment_patterns = ['tamam', 'anladım', 'anlıyorum', 'peki', 'ok', 'okay', 'evet anladım', 'tamamdır']
        if any(phrase in message_lower for phrase in acknowledgment_patterns):
            return IntentResult('thanks', {}, 0.9)
        
        # Enhanced goodbye patterns
        goodbye_patterns = ['güle güle', 'görüşürüz', 'bye', 'hoşça kal', 'iyi günler dilerim']
        if any(phrase in message_lower for phrase in goodbye_patterns):
            return IntentResult('goodbye', {}, 0.9)
        
        # Enhanced negative/dismissive patterns with context awareness
        negative_patterns = ['başka sorum yok', 'gerek yok', 'olmaz', 'istemiyorum', 'yeter', 'tamam']
        if any(phrase in message_lower for phrase in negative_patterns):
            return IntentResult('goodbye', {}, 0.8)
        
        # Single word negative responses - context aware
        single_negatives = ['yok', 'hayır', 'no', 'olmaz', 'yeter', 'tamam']
        if message_lower.strip() in single_negatives:
            # Check conversation context
            history_length = len(self.conversation_handler.context.conversation_history)
            if history_length > 1:  # If there's conversation history, it's likely goodbye
                return IntentResult('goodbye', {}, 0.9)
            else:  # If it's early in conversation, might be answering a question
                return IntentResult('negative_response', {}, 0.8)
        
        # Enhanced business info patterns (check BEFORE product search)
        phone_patterns = ['telefon', 'numara', 'ara', 'arayın']
        if any(word in message_lower for word in phone_patterns):
            return IntentResult('phone_inquiry', {}, 0.8)
        
        contact_patterns = ['iletişim', 'adres', 'nerede', 'konum']
        if any(word in message_lower for word in contact_patterns):
            return IntentResult('contact_info', {}, 0.8)
        
        payment_patterns = ['ödeme', 'kredi kartı', 'nakit', 'havale', 'eft']
        if any(phrase in message_lower for phrase in payment_patterns):
            return IntentResult('payment_info', {}, 0.8)
        
        # Enhanced return policy patterns (higher priority - check BEFORE product search)
        return_patterns = ['iade var mı', 'iade var mıydı', 'iade nasıl', 'iade politika', 'geri verebilir', 'iade şartları']
        if any(phrase in message_lower for phrase in return_patterns):
            return IntentResult('return_policy', {}, 0.9)
        
        # Single word "iade" check
        if message_lower.strip() == 'iade' or message_lower.startswith('iade '):
            return IntentResult('return_policy', {}, 0.9)
        
        if any(word in message_lower for word in ['kargo', 'teslimat']):
            return IntentResult('shipping_info', {}, 0.8)
        
        if any(word in message_lower for word in ['site', 'web']):
            return IntentResult('website_inquiry', {}, 0.8)
        
        # Enhanced product search with better feature extraction (check BEFORE stock/price)
        product_features = []
        if 'dantelli' in message_lower:
            product_features.append('dantelli')
        if 'dekolteli' in message_lower or 'dekolte' in message_lower:
            product_features.append('dekolteli')
        if 'hamile' in message_lower:
            product_features.append('hamile')
        if 'lohusa' in message_lower:
            product_features.append('lohusa')
        if 'düğmeli' in message_lower:
            product_features.append('düğmeli')
        if 'askılı' in message_lower:
            product_features.append('askılı')
        
        # Enhanced color extraction with Turkish variants
        color = ''
        color_mappings = {
            'siyah': ['siyah', 'siyahı', 'black'],
            'beyaz': ['beyaz', 'beyazı', 'white', 'ekru'],
            'kırmızı': ['kırmızı', 'kırmızısı', 'kirmizi', 'red'],
            'mavi': ['mavi', 'mavisi', 'blue'],
            'lacivert': ['lacivert', 'lacivertı', 'navy'],
            'yeşil': ['yeşil', 'yeşili', 'yesil', 'green'],
            'sarı': ['sarı', 'sarısı', 'sari', 'yellow'],
            'mor': ['mor', 'moru', 'purple', 'lila'],
            'pembe': ['pembe', 'pembesi', 'pink'],
            'vizon': ['vizon', 'vizonu', 'beige'],
            'bordo': ['bordo', 'bordosu', 'burgundy']
        }
        
        for turkish_color, variations in color_mappings.items():
            if any(var in message_lower for var in variations):
                color = turkish_color
                print(f"DEBUG: Found color '{color}' from message '{message_lower}'")
                break
        
        # Product type detection
        product_types = ['takım', 'gecelik', 'pijama', 'sabahlık', 'elbise', 'şort', 'tulum']
        has_product_type = any(ptype in message_lower for ptype in product_types)
        
        # Special handling for specific product names (like "afrika")
        specific_products = ['afrika', 'etnik']
        has_specific_product = any(prod in message_lower for prod in specific_products)
        
        if product_features or color or has_product_type or has_specific_product:
            return IntentResult('product_search', {
                'product_features': product_features,
                'color': color
            }, 0.8)  # Higher confidence for product search
        
        # FOLLOWUP DETECTION - Check BEFORE price patterns
        import re
        followup_patterns = [
            r'\d+\s*(numaralı|nolu|no)\s*(ürün|ün)',  # "1 numaralı ürün"
            r'\d+\s*(fiyat|kaç|para)',                # "1 fiyatı", "1 kaç para"
            r'\d+\s*(stok|var|mevcut)',               # "1 stok var mı"
        ]
        
        # If matches followup pattern, return followup intent
        if any(re.search(pattern, message_lower) for pattern in followup_patterns):
            return IntentResult('followup', {}, 0.95)
        
        # Color-only queries should NOT be followup - they're new searches
        color_only_patterns = [
            r'^(siyah|beyaz|kırmızı|mavi|yeşil|mor|pembe|sarı|bordo|vizon|ekru|lacivert)\s*(var\s*mı|mevcut|stok)$',
            r'^(siyah|beyaz|kırmızı|mavi|yeşil|mor|pembe|sarı|bordo|vizon|ekru|lacivert)ı?\s*(var\s*mı|mevcut|stok)$'
        ]
        
        # If it's a color-only query, treat as product search
        if any(re.search(pattern, message_lower.strip()) for pattern in color_only_patterns):
            return IntentResult('product_search', {'color': message_lower.split()[0]}, 0.8)
        
        # Vague followup patterns that should be treated as new searches
        vague_followup_patterns = [
            r'^(var\s*mı|mevcut|stok)$',  # Just "var mı"
            r'^(fiyat|kaç|para)$',        # Just "fiyat"
        ]
        
        # If it's a vague query, treat as unclear
        if any(re.search(pattern, message_lower.strip()) for pattern in vague_followup_patterns):
            return IntentResult('unclear', {}, 0.6)
        
        # Enhanced price and stock patterns (AFTER followup check)
        price_patterns = ['fiyat', 'kaç', 'para', 'tl', 'lira', 'ücret', 'maliyet', 'ne kadar']
        if any(word in message_lower for word in price_patterns):
            # If there's also a product type, it's a product search with price inquiry
            if has_product_type or product_features:
                return IntentResult('product_search', {
                    'product_features': product_features,
                    'color': color,
                    'price_inquiry': True
                }, 0.85)
            else:
                return IntentResult('price_inquiry', {}, 0.7)
        
        # Color-only queries: Check if we have context first
        if color and any(phrase in message_lower for phrase in ['var mı', 'mevcut', 'stok']):
            # If we have previous products in context, it's a followup
            if hasattr(self, 'conversation_handler') and self.conversation_handler.context.last_products:
                return IntentResult('followup', {'color': color}, 0.90)
            else:
                # No context, treat as new product search
                return IntentResult('product_search', {'color': color}, 0.85)
        
        # Stock patterns - only if no product context AND no product features
        stock_patterns = ['stok', 'var mı', 'mevcut', 'kaldı mı', 'bulunur mu']
        if any(phrase in message_lower for phrase in stock_patterns):
            # If there are product features/colors, it's product search, not stock inquiry
            if not (product_features or color or has_product_type or has_specific_product):
                return IntentResult('stock_inquiry', {}, 0.7)
        
        # Enhanced size inquiries
        size_patterns = ['beden var', 'size var', 'bedeni var', 'bedeni mevcut', 'beden mevcut']
        if any(phrase in message_lower for phrase in size_patterns):
            return IntentResult('size_inquiry', {}, 0.8)
        elif any(word in message_lower for word in ['xl', 'xs', 'xxl']) and ('var' in message_lower or 'mevcut' in message_lower):
            return IntentResult('size_inquiry', {}, 0.8)
        
        # Enhanced order related patterns
        order_patterns = ['sipariş vermek', 'satın almak', 'nasıl alırım', 'sipariş ver', 'almak istiyorum']
        if any(phrase in message_lower for phrase in order_patterns):
            return IntentResult('order_request', {}, 0.8)
        
        order_status_patterns = ['siparişim', 'kargom gelmedi', 'sipariş durumu', 'nerede kargom']
        if any(phrase in message_lower for phrase in order_status_patterns):
            return IntentResult('order_status', {}, 0.8)
        
        # Enhanced complaint patterns
        complaint_patterns = ['şikayet', 'sorun yaşı', 'problem', 'memnun değil', 'kötü', 'berbat']
        if any(phrase in message_lower for phrase in complaint_patterns):
            return IntentResult('complaint', {}, 0.85)
        
        # If nothing matches, it's unclear
        return IntentResult('unclear', {}, 0.3)
    
    def _normalize_turkish(self, text: str) -> str:
        """Enhanced Turkish character normalization"""
        if not text:
            return ""
        
        # Turkish character normalization
        replacements = {
            'İ': 'I', 'ı': 'i', 'Ğ': 'G', 'ğ': 'g',
            'Ü': 'U', 'ü': 'u', 'Ş': 'S', 'ş': 's',
            'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c'
        }
        
        normalized = text.lower()
        for turkish_char, latin_char in replacements.items():
            normalized = normalized.replace(turkish_char.lower(), latin_char.lower())
        
        return normalized
    
    def _enhance_query_with_llm(self, query: str) -> str:
        """Enhance query with LLM for typo correction and expansion"""
        if not self.model or len(query) > 50:
            return query
        
        try:
            prompt = f"""Türkçe iç giyim ürün arama sorgusunu düzelt ve iyileştir.

SORGU: "{query}"

GÖREVLER:
1. Yazım hatalarını düzelt (afirka → afrika, hamle → hamile, danteli → dantelli)
2. Kısaltmaları genişlet (geclik → gecelik, pjama → pijama)
3. Eksik kelimeleri tamamla
4. Sadece düzeltilmiş sorguyu döndür, açıklama yapma

ÜRÜN TİPLERİ: gecelik, pijama, sabahlık, takım, şort
ÖZELLİKLER: hamile, lohusa, dantelli, büyük beden, afrika, etnik

ÇIKTI: Sadece düzeltilmiş sorgu"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=20
                )
            )
            
            if response.candidates and response.candidates[0].content.parts:
                enhanced = response.candidates[0].content.parts[0].text.strip()
                # Basic validation
                if len(enhanced) > 0 and len(enhanced) < 100:
                    return enhanced
                    
        except Exception as e:
            logger.warning(f"Query enhancement failed: {e}")
        
        return query
    
    def _analyze_conversation_context(self, message: str) -> str:
        """Analyze conversation context to determine if greeting or goodbye"""
        history = self.conversation_handler.context.conversation_history
        
        # If no history, it's likely a greeting
        if len(history) == 0:
            return 'start'
        
        # If conversation has been going on, check for goodbye indicators
        if len(history) > 3:
            # Look for goodbye indicators in the message
            goodbye_indicators = ['görüşürüz', 'hoşça kal', 'teşekkür', 'yeter', 'tamam']
            if any(indicator in message for indicator in goodbye_indicators):
                return 'end'
        
        # Check last few messages for context
        recent_messages = history[-3:] if len(history) >= 3 else history
        
        # If recent messages show user is satisfied/leaving
        satisfaction_indicators = ['teşekkür', 'yeter', 'tamam', 'iyi', 'güzel']
        for msg in recent_messages:
            if any(indicator in msg.get('message', '').lower() for indicator in satisfaction_indicators):
                return 'end'
        
        # If user just started asking questions, it's likely greeting
        if len(history) <= 2:
            return 'start'
        
        # Default to uncertain
        return 'uncertain'
    
    def search_products(self, query: str, features: List[str] = None, color: str = None, session_id: str = None) -> List[Product]:
        """Enhanced product search with better Turkish handling"""
        if not query and not features and not color:
            return []
        
        # Check smart cache first (session-aware)
        cache_key = f"{query}_{features}_{color}"
        cached_result = self.smart_cache.get_session(
            query, session_id, features, color, 
            self.conversation_handler.context.conversation_history
        )
        if cached_result and len(cached_result) > 0:
            # Strict cache validation
            if self._validate_cache_result(query, cached_result):
                self.stats['cache_hits'] += 1
                return cached_result
            else:
                logger.info(f"Cache result not relevant for '{query}', searching again")
        
        # SMART EXACT MATCHING for specific product queries
        clean_query = query
        stop_words = ['var mı', 'arıyorum', 'istiyorum', 'lazım', 'gerek', 'bulunur mu', 'var mıydı', 'ne kadar', 'kaç para']
        for remove_word in stop_words:
            clean_query = clean_query.replace(remove_word, '').strip()
        
        # Detect if this is a VERY SPECIFIC product query
        specific_indicators = ['new york', 'africa style', 'calm down', 'never give up', 'stay strong']
        is_very_specific = any(indicator in clean_query.lower() for indicator in specific_indicators)
        
        if clean_query and (len(clean_query.split()) <= 5 or is_very_specific):
            exact_matches = []
            query_normalized = self._normalize_turkish(clean_query.lower())
            query_words = [word for word in query_normalized.split() if len(word) > 2]
            
            # ULTRA-STRICT matching for very specific queries
            for product in self.products:
                product_text = self._normalize_turkish(f"{product.name} {product.color}".lower())
                
                if is_very_specific:
                    # For very specific queries, require EXACT brand/style match
                    specific_match = False
                    for indicator in specific_indicators:
                        if indicator in clean_query.lower() and indicator in product_text:
                            specific_match = True
                            break
                    
                    if specific_match:
                        exact_matches.append(product)
                        # For very specific queries, return immediately with exact match
                        if len(exact_matches) >= 1:
                            # Cache the result
                            self.smart_cache.set(query, exact_matches[:1])
                            logger.info(f"Exact specific match found for '{query}': {exact_matches[0].name}")
                            return exact_matches[:1]
                else:
                    # Regular enhanced matching
                    word_matches = sum(1 for word in query_words if word in product_text)
                    match_ratio = word_matches / len(query_words) if query_words else 0
                    
                    # Stricter matching requirements
                    if len(query_words) <= 2:
                        required_ratio = 1.0  # 100% match for short queries
                    elif len(query_words) <= 4:
                        required_ratio = 0.9  # 90% match for medium queries
                    else:
                        required_ratio = 0.85  # 85% match for long queries
                    
                    if match_ratio >= required_ratio:
                        # Extra filtering for specific product types
                        if 'gecelik' in clean_query.lower() and 'gecelik' not in product.name.lower():
                            continue  # Skip non-gecelik products if user specifically asked for gecelik
                        if 'pijama' in clean_query.lower() and 'pijama' not in product.name.lower():
                            continue  # Skip non-pijama products if user specifically asked for pijama
                        if 'sabahlık' in clean_query.lower() and 'sabahlık' not in product.name.lower():
                            continue  # Skip non-sabahlık products if user specifically asked for sabahlık
                        
                        # Generic brand filtering system
                        brand_filtered = self._apply_brand_filtering(clean_query.lower(), product)
                        if not brand_filtered:
                            continue
                    
                    exact_matches.append(product)
            
            # If we found exact matches, prioritize them
            if exact_matches:
                # Smart result count based on specificity
                if len(query_words) >= 2:
                    # Multi-word specific search - be more restrictive
                    if any(specific in clean_query.lower() for specific in ['afrika', 'etnik']):
                        result_count = min(1, len(exact_matches))  # Only 1 for very specific
                    else:
                        result_count = min(2, len(exact_matches))  # Max 2 for specific
                else:
                    # Single word search - can show more
                    result_count = min(3, len(exact_matches))
                
                self.smart_cache.put_session(
                    query, exact_matches[:result_count], session_id, features, color,
                    self.conversation_handler.context.conversation_history
                )
                logger.info(f"Exact match search returned {len(exact_matches[:result_count])} products for '{clean_query}' (original: '{query}')")
                return exact_matches[:result_count]
        
        # Try RAG search first (with timeout for performance)
        if self.rag_search and self.rag_search.is_available():
            try:
                start_time = time.time()
                search_query = query
                if features:
                    search_query += " " + " ".join(features)
                if color:
                    search_query += f" {color} renk"
                
                rag_results = self.rag_search.search(search_query, 5)
                
                # If no results and query might have typos, try enhancement
                if not rag_results and len(query.split()) <= 3:
                    enhanced_query = self._enhance_query_with_llm(query)
                    if enhanced_query != query:
                        logger.info(f"Query enhanced: '{query}' → '{enhanced_query}'")
                        enhanced_search = enhanced_query
                        if features:
                            enhanced_search += " " + " ".join(features)
                        if color:
                            enhanced_search += f" {color} renk"
                        rag_results = self.rag_search.search(enhanced_search, 5)
                
                rag_time = time.time() - start_time
                
                # If RAG search takes too long, skip it next time
                if rag_time > 0.5:  # 500ms threshold
                    logger.warning(f"RAG search slow ({rag_time:.3f}s), consider optimization")
                
                if rag_results:
                    # Calculate overall search confidence
                    search_confidence = self._calculate_search_confidence(query, rag_results)
                    
                    # If confidence is low, use LLM validation
                    if search_confidence < 0.6 and self.model:
                        validated_results = self._validate_results_with_llm(query, rag_results)
                        if validated_results:
                            rag_results = validated_results
                    
                    # Convert RAG results to Product objects with color filtering
                    products = []
                    for result in rag_results:
                        # Dynamic similarity threshold based on search confidence
                        similarity_threshold = 0.15 if search_confidence > 0.7 else 0.25
                        
                        if result.get('similarity', 0) > similarity_threshold:
                            # CRITICAL: Color filtering for RAG results
                            if color:
                                product_color = result.get('color', '').lower()
                                if color.lower() not in product_color and not any(
                                    color_variant in product_color 
                                    for color_variant in [color.lower(), color.lower() + 'ı', color.lower() + 'i']
                                ):
                                    continue  # Skip products that don't match the requested color
                            # Calculate discount from price difference
                            discount = 0.0
                            if result['price'] > result['final_price']:
                                discount = ((result['price'] - result['final_price']) / result['price']) * 100
                            
                            products.append(Product(
                                name=result['name'],
                                color=result['color'],
                                price=result['price'],
                                discount=discount,
                                final_price=result['final_price'],
                                category=result['category'],
                                stock=result['stock']
                            ))
                    
                    if products:
                        # Cache the result
                        self.smart_cache.put_session(
                            query, products, session_id, features, color,
                            self.conversation_handler.context.conversation_history
                        )
                        logger.info(f"RAG search returned {len(products)} products in {rag_time:.3f}s")
                        return products
                        
            except Exception as e:
                logger.error(f"RAG search failed, falling back to fuzzy: {e}")
        
        # Enhanced fuzzy matching with better Turkish support
        scored_products = []
        
        for product in self.products:
            score = 0
            # Use normalized text for better Turkish matching
            product_text = self._normalize_turkish(f"{product.name} {product.color}")
            query_lower = self._normalize_turkish(query) if query else ""
            
            # 1. Exact name match (highest score)
            if query_lower and query_lower in product_text:
                score += 100
            
            # 1.5. Word-by-word exact matching (for multi-word queries)
            if query_lower:
                query_words = query_lower.split()
                word_matches = 0
                for word in query_words:
                    if len(word) > 2 and word in product_text:  # Skip very short words
                        word_matches += 1
                if word_matches > 0:
                    score += (word_matches / len(query_words)) * 120  # Higher than exact match for multi-word
            
            # 2. Enhanced fuzzy string matching
            if query_lower:
                fuzzy_score = fuzz.partial_ratio(query_lower, product_text)
                score += fuzzy_score * 0.8
            
            # 3. Feature matching (high weight for extracted features)
            if features:
                for feature in features:
                    feature_normalized = self._normalize_turkish(feature)
                    if feature_normalized in product_text:
                        score += 60
            
            # 4. Enhanced color matching with Turkish normalization
            if color:
                color_lower = self._normalize_turkish(color)
                product_color_lower = self._normalize_turkish(product.color)
                
                # Direct exact match (highest priority)
                if color_lower == product_color_lower:
                    score += 80
                elif color_lower in product_color_lower or product_color_lower in color_lower:
                    score += 60
                
                # Turkish color mappings with exact database values
                color_mappings = {
                    'siyah': ['siyah', 'black'],
                    'beyaz': ['beyaz', 'white', 'ekru'],
                    'kırmızı': ['kirmizi', 'red', 'kırmızı'],
                    'mavi': ['mavi', 'blue', 'lacivert'],
                    'yeşil': ['yesil', 'green', 'haki', 'açik yeşil', 'yeşil'],
                    'mor': ['mor', 'purple', 'lila'],
                    'vizon': ['vizon', 'beige'],
                    'bordo': ['bordo', 'burgundy']
                }
                
                for turkish_color, variations in color_mappings.items():
                    if color_lower == turkish_color or any(var == color_lower for var in variations):
                        for variation in variations:
                            if variation in product_color_lower:
                                score += 70
                                break
            
            # 5. Category and type bonuses
            if any(word in product_text for word in ['takım', 'gecelik', 'pijama', 'sabahlık']):
                score += 15
            
            # 6. Stock availability bonus
            try:
                if int(product.stock) > 0:
                    score += 10
            except (ValueError, TypeError):
                pass
            
            # 7. Discount bonus (popular items)
            try:
                if float(product.discount) > 0:
                    score += 5
            except (ValueError, TypeError):
                pass
            
            if score > 30:  # Minimum threshold
                scored_products.append((product, score))
        
        # Sort by score and return top results
        scored_products.sort(key=lambda x: x[1], reverse=True)
        products = [product for product, score in scored_products[:5]]
        
        # Cache the result
        self.smart_cache.put_session(
            query, products, session_id, features, color,
            self.conversation_handler.context.conversation_history
        )
        
        return products
    
    def format_product_response(self, products: List[Product]) -> str:
        """Enhanced product formatting with beautiful presentation"""
        if not products:
            return self.fixed_responses.get("no_products_found", 
                "Üzgünüm, aradığınız kriterlere uygun ürün bulamadım. 😔\n\n💡 **Öneriler:**\n• Ürünün tam adını yazın (örn: 'Afrika Etnik Baskılı Gecelik')\n• Farklı renk deneyin\n• Daha genel arama yapın\n\n📞 **Yardım için:** 0555 555 55 55")
        
        if len(products) == 1:
            product = products[0]
            response = f"✨ **{product.name}**\n\n"
            response += f"🎨 **Renk:** {product.color}\n"
            response += f"💰 **Fiyat:** {product.final_price:.2f} TL"
            
            try:
                if float(product.discount) > 0:
                    response += f"\n🏷️ **İndirim:** %{product.discount} (Eski fiyat: {product.price:.2f} TL)"
                    savings = product.price - product.final_price
                    response += f"\n💸 **Tasarruf:** {savings:.2f} TL"
            except (ValueError, TypeError):
                pass
            
            try:
                stock_available = int(product.stock) > 0
            except (ValueError, TypeError):
                stock_available = False
            
            response += f"\n📦 **Stok:** {'✅ Mevcut' if stock_available else '❌ Tükendi'}"
            
            if stock_available:
                response += f"\n\n🛒 **Sipariş için:** {self.business_info.get('phone', '0555 555 55 55')}"
                response += f"\n🌐 **Web:** {self.business_info.get('website', 'www.butik.com')}"
            
            return response
        else:
            # Multiple products - check if same product in different colors
            grouped_products = group_products_by_base_name(products)
            
            if len(grouped_products) == 1:
                # Same product, different colors
                base_name, group_data = next(iter(grouped_products.items()))
                colors = group_data['colors']
                
                response = f"✨ **{base_name}**\n\n"
                
                # Price range
                prices = [c['price'] for c in colors]
                min_price = min(prices)
                max_price = max(prices)
                
                if min_price == max_price:
                    response += f"💰 **Fiyat:** {min_price:.2f} TL\n"
                else:
                    response += f"💰 **Fiyat:** {min_price:.2f} - {max_price:.2f} TL\n"
                
                # Available colors
                response += f"🎨 **Mevcut Renkler:**\n"
                for i, color_info in enumerate(colors, 1):
                    stock_emoji = "✅" if color_info['stock'] > 0 else "❌"
                    price_diff = f" ({color_info['price']:.2f} TL)" if len(set(prices)) > 1 else ""
                    response += f"   {i}. {color_info['color']}{price_diff} {stock_emoji}\n"
                
                response += f"\n🛒 **Sipariş için:** {self.business_info.get('phone', '0555 555 55 55')}"
                response += f"\n🌐 **Web:** {self.business_info.get('website', 'www.butik.com')}"
                
                return response
            else:
                # Different products
                response = f"🛍️ Size uygun **{len(products)} ürün** buldum:\n\n"
                
                for i, product in enumerate(products[:5], 1):
                    response += f"**{i}.** {product.name}\n"
                    response += f"   🎨 **Renk:** {product.color}\n"
                    response += f"   💰 **Fiyat:** {product.final_price:.2f} TL"
                    
                    try:
                        if float(product.discount) > 0:
                            response += f" 🏷️ *(%{product.discount} indirim)*"
                    except (ValueError, TypeError):
                        pass
                    
                    try:
                        stock_available = int(product.stock) > 0
                        response += f"\n   📦 {'✅ Mevcut' if stock_available else '❌ Tükendi'}"
                    except (ValueError, TypeError):
                        response += f"\n   📦 ✅ Mevcut"
                    
                    response += "\n\n"
                
                response += f"🛒 **Sipariş için:** {self.business_info.get('phone', '0555 555 55 55')}"
                response += f"\n🌐 **Web:** {self.business_info.get('website', 'www.butik.com')}"
                response += self._get_whatsapp_support_text('product_search')
                
                return response
    
    def route_and_respond(self, intent_result: IntentResult, original_message: str, session_id: str = None) -> ChatResponse:
        """Enhanced routing with better context handling"""
        intent = intent_result.intent
        entities = intent_result.entities
        

        
        # Handle clarification needed
        if intent == "clarification_needed":
            return ChatResponse(
                message=entities.get('response', 'Lütfen daha açık belirtir misiniz?'),
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Smart context analysis - check if it's really a followup or new intent
        # Only check followup if intent is not already clearly determined
        if intent_result.intent in ['unclear', 'stock_inquiry', 'price_inquiry']:
            is_followup, followup_response = self.conversation_handler.handle_follow_up_questions(original_message)
            
            if is_followup:
                # Override followup if message contains clear intent keywords or product search patterns
                message_lower = original_message.lower()
                
                clear_intent_keywords = {
                    'iade': 'return_policy',
                    'kargo': 'shipping_info', 
                    'telefon': 'phone_inquiry'
                }
                
                # Product search patterns that should override followup
                product_search_patterns = ['gecelik', 'pijama', 'sabahlık', 'takım', 'dantelli', 'hamile']
                has_product_pattern = any(pattern in message_lower for pattern in product_search_patterns)
                
                # Strong followup patterns that should ALWAYS stay as followup
                strong_followup_patterns = ['numaralı.*fiyat', 'numaralı.*stok', 'numaralı.*detay', '\d+.*fiyat', '\d+.*stok']
                has_strong_followup = any(
                    __import__('re').search(pattern, message_lower) 
                    for pattern in strong_followup_patterns
                )
                
                # Check for clear intent keywords first
                for keyword, clear_intent in clear_intent_keywords.items():
                    if keyword in message_lower and not has_strong_followup:
                        is_followup = False  # Override followup detection
                        break
                
                # If has strong followup pattern, keep as followup regardless
                if has_strong_followup:
                    is_followup = True
                # If has product pattern but no strong followup pattern, it's product search
                elif has_product_pattern:
                    is_followup = False
        else:
            # If intent is already clearly determined (like followup from fallback), use it
            if intent_result.intent == 'followup':
                # For color queries, handle directly
                if 'color' in intent_result.entities and self.conversation_handler.context.last_products:
                    color = intent_result.entities['color']
                    products = self.conversation_handler.context.last_products
                    
                    # Check if any product has this color
                    matching_products = [p for p in products if p.get('color', '').lower() == color.lower()]
                    
                    if matching_products:
                        followup_response = f"✅ **{color.title()}** renkte ürün mevcut!\n\n"
                        for i, product in enumerate(matching_products[:3], 1):
                            followup_response += f"**{i}.** {product['name'][:50]}...\n"
                            followup_response += f"   💰 **{product.get('final_price', product.get('price', 'N/A'))} TL**\n\n"
                        followup_response += f"🛒 **Sipariş için:** {self.business_info.get('phone', '0555 555 55 55')}"
                    else:
                        # Show available colors
                        available_colors = list(set([p.get('color', '') for p in products if p.get('color')]))
                        followup_response = f"❌ **{color.title()}** renkte ürün bulunmuyor.\n\n🎨 **Mevcut renkler:**\n\n"
                        for i, avail_color in enumerate(available_colors[:5], 1):
                            price = next((p.get('final_price', p.get('price', 'N/A')) for p in products if p.get('color', '').lower() == avail_color.lower()), 'N/A')
                            followup_response += f"**{i}.** {avail_color.upper()} - **{price} TL** ✅\n\n"
                        followup_response += f"🛒 **Sipariş için:** {self.business_info.get('phone', '0555 555 55 55')}"
                    
                    is_followup = True
                else:
                    is_followup, followup_response = self.conversation_handler.handle_follow_up_questions(original_message)
            else:
                is_followup = False
        
        if is_followup:
            # Additional validation: Check if followup makes sense
            message_lower = original_message.lower().strip()
            
            # Color-only queries should NOT be followup even if context exists
            color_only_patterns = [
                r'^(siyah|beyaz|kırmızı|mavi|yeşil|mor|pembe|sarı|bordo|vizon|ekru|lacivert)\s*(var\s*mı|mevcut|stok)$',
                r'^(siyah|beyaz|kırmızı|mavi|yeşil|mor|pembe|sarı|bordo|vizon|ekru|lacivert)ı?\s*(var\s*mı|mevcut|stok)$'
            ]
            
            import re
            # Test the pattern
            test_match = re.search(r'^(siyah|beyaz|kırmızı|mavi|yeşil|mor|pembe|sarı|bordo|vizon|ekru|lacivert)ı?\s*(var\s*mı|mevcut|stok)$', message_lower)
            
            if test_match:
                # This is a color query in context - handle as followup with color filtering
                color = message_lower.split()[0].replace('ı', '')
                
                # Use attribute system to handle color query in context
                if hasattr(self, 'conversation_handler') and self.conversation_handler.context.last_products:
                    from attribute_system import handle_attribute_query
                    is_attr_query, response = handle_attribute_query(
                        original_message, 
                        self.conversation_handler.context.last_products
                    )
                    if not is_attr_query:
                        response = f"🔍 **{color.title()}** renkte hangi ürün türünü arıyorsunuz?\n\n💡 **Örnek:** '{color} gecelik', '{color} pijama'\n\n📞 **Yardım:** {self.business_info.get('phone', '0555 555 55 55')}"
                    return ChatResponse(
                        message=response,
                        intent="followup",
                        confidence=0.9,
                        products_found=0
                    )
                else:
                    # No context, treat as new search
                    return ChatResponse(
                        message=f"🔍 **{color.title()}** renkte hangi ürün türünü arıyorsunuz?\n\n💡 **Örnek:** '{color} gecelik', '{color} pijama'\n\n📞 **Yardım:** {self.business_info.get('phone', '0555 555 55 55')}",
                        intent="product_search",
                        confidence=0.9,
                        products_found=0
                    )
            
            return ChatResponse(
                message=followup_response,
                intent="followup",
                confidence=0.9
            )
        
        # Special handling for stock inquiry
        elif intent == "stock_inquiry":
            return ChatResponse(
                message="📦 Hangi ürünün stok durumunu öğrenmek istiyorsunuz?\n\n🔍 Ürün adını yazabilir veya arama yapabilirsiniz.",
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Special handling for size inquiry with dynamic response
        elif intent == "size_inquiry":
            dynamic_response = self.db_analyzer.generate_dynamic_response(original_message, self.business_info)
            return ChatResponse(
                message=dynamic_response,
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Fixed responses with context awareness
        elif intent in self.fixed_responses:
            try:
                base_response = self.fixed_responses[intent]
                contextual_response = self.conversation_handler.generate_contextual_response(intent, base_response)
                return ChatResponse(
                    message=contextual_response,
                    intent=intent,
                    confidence=intent_result.confidence
                )
            except Exception as e:
                logger.error(f"Error in contextual response generation: {e}")
                # Fallback to base response
                return ChatResponse(
                    message=self.fixed_responses.get(intent, "Üzgünüm, bir hata oluştu."),
                    intent=intent,
                    confidence=intent_result.confidence
                )
        
        # Smart product+color query
        elif intent == "product_color_query":
            product_name = entities.get('product_name', '')
            color = entities.get('color', '')
            
            # Search for the specific product first
            products = self.search_products(product_name, [], '', session_id)
            
            if products:
                # Check if any product has the requested color
                matching_products = [p for p in products if p.color.lower() == color.lower()]
                
                if matching_products:
                    # Found products in that color
                    response_message = f"✅ **{product_name.title()} {color}** renkte mevcut!\n\n"
                    for i, product in enumerate(matching_products[:3], 1):
                        response_message += f"**{i}.** {product.name}\n"
                        response_message += f"   💰 **{product.final_price:.2f} TL**"
                        if product.discount > 0:
                            response_message += f" 🏷️ *(%{product.discount} indirim)*"
                        response_message += f"\n   📦 ✅ Mevcut\n\n"
                    response_message += f"🛒 **Sipariş için:** {self.business_info.get('phone', '0555 555 55 55')}"
                else:
                    # Product exists but not in that color
                    available_colors = list(set([p.color for p in products if p.color]))
                    response_message = f"❌ **{product_name.title()}** ürünü **{color}** renkte bulunmuyor.\n\n"
                    response_message += f"🎨 **Mevcut renkler:**\n\n"
                    for i, avail_color in enumerate(available_colors[:5], 1):
                        price = next((p.final_price for p in products if p.color.lower() == avail_color.lower()), 0)
                        response_message += f"**{i}.** {avail_color.upper()} - **{price:.2f} TL** ✅\n"
                    response_message += f"\n🛒 **Sipariş için:** {self.business_info.get('phone', '0555 555 55 55')}"
            else:
                # Product not found at all
                response_message = f"❌ **{product_name.title()}** ürünü bulunamadı.\n\n💡 **Öneriler:**\n• Ürün adını kontrol edin\n• Farklı arama terimleri deneyin\n\n📞 **Yardım:** {self.business_info.get('phone', '0555 555 55 55')}"
            
            return ChatResponse(
                message=response_message,
                intent=intent,
                confidence=intent_result.confidence,
                products_found=len(matching_products) if 'matching_products' in locals() else 0
            )
        
        # Smart product+size query
        elif intent == "product_size_query":
            product_name = entities.get('product_name', '')
            size = entities.get('size', '')
            
            # Search for the specific product first
            products = self.search_products(product_name, [], '', session_id)
            
            if products:
                # For now, we don't have size data in our products, so give helpful response
                response_message = f"📏 **{product_name.title()}** ürünü için **{size}** beden bilgisi:\n\n"
                response_message += f"🔍 Beden bilgileri için lütfen bizi arayın:\n"
                response_message += f"📞 **Telefon:** {self.business_info.get('phone', '0555 555 55 55')}\n\n"
                response_message += f"💡 **Alternatif:** Web sitemizden beden tablosuna bakabilirsiniz:\n"
                response_message += f"🌐 **Web:** {self.business_info.get('website', 'www.butik.com')}\n\n"
                response_message += f"📦 **Mevcut ürünler:**\n"
                for i, product in enumerate(products[:2], 1):
                    response_message += f"**{i}.** {product.name} - **{product.final_price:.2f} TL**\n"
            else:
                response_message = f"❌ **{product_name.title()}** ürünü bulunamadı.\n\n💡 **Öneriler:**\n• Ürün adını kontrol edin\n• Farklı arama terimleri deneyin\n\n📞 **Yardım:** {self.business_info.get('phone', '0555 555 55 55')}"
            
            return ChatResponse(
                message=response_message,
                intent=intent,
                confidence=intent_result.confidence,
                products_found=len(products) if products else 0
            )
        
        # Product search
        elif intent == "product_search":
            query = entities.get('product_name', original_message)
            features = entities.get('product_features', [])
            color = entities.get('color', '')
            
            products = self.search_products(query, features, color, session_id)
            response_message = self.format_product_response(products)
            
            return ChatResponse(
                message=response_message,
                intent=intent,
                confidence=intent_result.confidence,
                products_found=len(products)
            )
        
        # Enhanced price inquiry
        elif intent == "price_inquiry":
            # Check if there's product context in the same message
            product_name = entities.get('product_name', '')
            features = entities.get('product_features', [])
            
            if product_name or features:
                # User asked for price of a specific product
                products = self.search_products(product_name or original_message, features, session_id=session_id)
                if products:
                    product = products[0]  # Take the best match
                    response_message = f"💰 **{product.name}** fiyat bilgisi:\n\n"
                    response_message += f"🎨 Renk: {product.color}\n"
                    response_message += f"💰 **Güncel Fiyat: {product.final_price:.2f} TL**"
                    
                    try:
                        if float(product.discount) > 0:
                            response_message += f"\n🏷️ **İndirim: %{product.discount}** (Eski fiyat: {product.price:.2f} TL)"
                            savings = product.price - product.final_price
                            response_message += f"\n💸 **Tasarruf: {savings:.2f} TL**"
                    except (ValueError, TypeError):
                        pass
                    
                    try:
                        stock_available = int(product.stock) > 0
                        response_message += f"\n📦 Stok: {'✅ Mevcut' if stock_available else '❌ Tükendi'}"
                    except (ValueError, TypeError):
                        pass
                    
                    if stock_available:
                        response_message += f"\n\n🛒 Sipariş için: {self.business_info.get('phone', '0212 123 45 67')}"
                    
                    return ChatResponse(
                        message=response_message,
                        intent=intent,
                        confidence=intent_result.confidence,
                        products_found=1
                    )
            
            # Check if user is asking about previous products
            if self.conversation_handler.context.last_products:
                response_message = "💰 **Son gösterdiğim ürünlerin fiyatları:**\n\n"
                for i, product in enumerate(self.conversation_handler.context.last_products[:3], 1):
                    # Handle both Product objects and dictionaries
                    if hasattr(product, 'name'):
                        name = product.name
                        final_price = product.final_price
                        discount = product.discount
                    else:
                        name = product.get('name', 'Bilinmeyen ürün')
                        final_price = product.get('final_price', 0)
                        discount = product.get('discount', 0)
                    
                    response_message += f"{i}. {name[:40]}...\n"
                    response_message += f"   💰 **{final_price:.2f} TL**"
                    if discount > 0:
                        response_message += f" (İndirimli!)"
                    response_message += "\n\n"
                
                response_message += "Hangi ürün hakkında detaylı fiyat bilgisi istersiniz?"
                return ChatResponse(
                    message=response_message,
                    intent=intent,
                    confidence=intent_result.confidence
                )
            
            return ChatResponse(
                message="💰 Hangi ürünün fiyatını öğrenmek istiyorsunuz?\n\nÖrnek: 'dantelli gecelik fiyatı' veya sadece ürün adını yazın.",
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Enhanced stock inquiry
        elif intent == "stock_inquiry":
            if self.conversation_handler.context.last_products:
                response_message = "📦 **Son gösterdiğim ürünlerin stok durumu:**\n\n"
                for i, product in enumerate(self.conversation_handler.context.last_products[:3], 1):
                    # Handle both Product objects and dictionaries
                    if hasattr(product, 'name'):
                        name = product.name
                        stock = product.stock
                    else:
                        name = product.get('name', 'Bilinmeyen ürün')
                        stock = product.get('stock', 0)
                    
                    stock_status = '✅ Mevcut' if stock > 0 else '❌ Tükendi'
                    response_message += f"{i}. {name[:40]}...\n"
                    response_message += f"   📦 **{stock_status}**\n\n"
                
                return ChatResponse(
                    message=response_message,
                    intent=intent,
                    confidence=intent_result.confidence
                )
            
            return ChatResponse(
                message="📦 Hangi ürünün stok durumunu öğrenmek istiyorsunuz?\n\nÖrnek: 'hamile pijama stok' veya ürün adını yazın.",
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # General info
        elif intent == "general_info":
            return ChatResponse(
                message="ℹ️ Size nasıl yardımcı olabilirim?\n\n💡 **Yapabileceklerim:**\n• 🔍 Ürün arama\n• 💰 Fiyat bilgisi\n• 📦 Stok durumu\n• 🏢 Mağaza bilgileri\n• 🚚 Kargo bilgileri\n• 📋 İade politikası",
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Unclear or default with enhanced help
        else:
            unclear_count = self.conversation_handler.context.clarification_attempts
            if unclear_count > 2:
                return ChatResponse(
                    message="🤔 Anlaşılan biraz karışıklık var. Size şu konularda yardımcı olabilirim:\n\n🛍️ **Ürün Arama Örnekleri:**\n• 'hamile pijama arıyorum'\n• 'dantelli gecelik'\n• 'siyah sabahlık'\n\n💡 **Diğer Sorular:**\n• 'telefon numaranız nedir?'\n• 'kargo ücreti ne kadar?'\n• 'iade nasıl yapılır?'\n\nHangi konuda yardım istiyorsunuz?",
                    intent=intent,
                    confidence=intent_result.confidence
                )
            else:
                return ChatResponse(
                    message="🤔 Anlayamadım. Size nasıl yardımcı olabilirim?\n\n💡 **Yapabileceklerim:**\n• 🔍 Ürün arama\n• 💰 Fiyat bilgisi\n• 📦 Stok durumu\n• 🏢 Mağaza bilgileri",
                    intent=intent,
                    confidence=intent_result.confidence
                )
    
    def chat(self, user_message: str, session_id: str = None) -> ChatResponse:
        """Enhanced main chat function with comprehensive error handling"""
        start_time = time.time()
        
        try:
            # Update stats
            self.stats['total_requests'] += 1
            
            # Validate input
            if not user_message or not user_message.strip():
                return ChatResponse(
                    message="📝 Lütfen bir mesaj yazın.",
                    intent="empty",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # Handle very long messages
            if len(user_message) > 500:
                user_message = user_message[:500] + "..."
                logger.warning("Message truncated due to length")
            

            
            # Extract intent and entities
            intent_result = self.extract_intent_with_gemini(user_message.strip())
            
            # Generate response
            response = self.route_and_respond(intent_result, user_message, session_id)
            
            # Update conversation context
            products = []
            if response.products_found > 0 and intent_result.intent == "product_search":
                # Get the products that were found
                query = intent_result.entities.get('product_name', user_message)
                features = intent_result.entities.get('product_features', [])
                color = intent_result.entities.get('color', '')
                found_products = self.search_products(query, features, color, session_id)
                
                # Convert Product objects to dictionaries for context storage
                products = []
                for product in found_products:
                    products.append({
                        'name': product.name,
                        'color': product.color,
                        'price': product.price,
                        'final_price': product.final_price,
                        'discount': product.discount,
                        'category': product.category,
                        'stock': product.stock
                    })
            
            self.conversation_handler.update_context(
                user_message, intent_result.intent, products
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            
            # Update stats
            self.stats['successful_requests'] += 1
            self.stats['average_response_time'] = (
                (self.stats['average_response_time'] * (self.stats['successful_requests'] - 1) + processing_time) 
                / self.stats['successful_requests']
            )
            
            logger.info(f"✅ Request processed: intent={response.intent}, confidence={response.confidence:.2f}, time={processing_time:.3f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Chat error: {e}")
            return ChatResponse(
                message="😔 Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.\n\nSorun devam ederse bizi arayabilirsiniz: " + self.business_info.get('phone', '0212 123 45 67'),
                intent="error",
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def get_stats(self) -> Dict:
        """Get enhanced system statistics"""
        return {
            **self.stats,
            'products_loaded': len(self.products),
            'gemini_available': self.model is not None,
            'success_rate': (self.stats['successful_requests'] / max(1, self.stats['total_requests'])) * 100,
            'cache_hit_rate': (self.stats['cache_hits'] / max(1, self.stats['total_requests'])) * 100,
            'conversation_stats': self.conversation_handler.get_conversation_stats(),
            'smart_cache_stats': self.smart_cache.get_stats()
        }
    
    def health_check(self) -> Dict:
        """Enhanced system health check"""
        return {
            'status': 'healthy',
            'products_loaded': len(self.products) > 0,
            'gemini_available': self.model is not None,
            'business_info_loaded': bool(self.business_info),
            'rag_search_available': self.rag_search is not None and self.rag_search.is_available(),
            'conversation_handler_ready': self.conversation_handler is not None,
            'total_requests': self.stats['total_requests'],
            'cache_size': len(self.smart_cache.cache) if self.smart_cache else 0
        }

    def _apply_brand_filtering(self, query_lower: str, product) -> bool:
        """Generic brand filtering system for all products"""
        product_name_lower = product.name.lower()
        
        # Define brand patterns (brand_name: [variations])
        brand_patterns = {
            'stay strong': ['stay strong', 'stay', 'strong'],
            'calm down': ['calm down', 'calm', 'down'],
            'africa style': ['africa style', 'afrika', 'etnik'],
            'basic': ['basic', 'temel'],
            'premium': ['premium', 'lüks'],
            'comfort': ['comfort', 'rahat'],
            'sport': ['sport', 'spor'],
            'classic': ['classic', 'klasik']
        }
        
        # Check if query contains any brand-specific terms
        for brand_name, variations in brand_patterns.items():
            # Check for exact brand match
            if brand_name in query_lower:
                return brand_name in product_name_lower
            
            # Check for multi-word brand components
            if len(variations) > 1:
                brand_words = brand_name.split()
                if len(brand_words) == 2:
                    word1, word2 = brand_words
                    if word1 in query_lower and word2 in query_lower:
                        return brand_name in product_name_lower
        
        # If no specific brand mentioned, allow all products
        return True

    def _calculate_search_confidence(self, query: str, results: List[Dict]) -> float:
        """Calculate confidence score for search results"""
        if not results:
            return 0.0
        
        query_words = set(query.lower().split())
        total_confidence = 0.0
        
        for result in results[:3]:  # Check top 3 results
            name_words = set(result['name'].lower().split())
            
            # Word overlap score
            overlap = len(query_words.intersection(name_words))
            overlap_score = overlap / len(query_words) if query_words else 0
            
            # Similarity score from RAG
            similarity_score = result.get('similarity', 0)
            
            # Combined confidence
            result_confidence = (overlap_score * 0.6) + (similarity_score * 0.4)
            total_confidence += result_confidence
        
        # Average confidence of top results
        avg_confidence = total_confidence / min(3, len(results))
        
        # Boost confidence for exact matches
        for result in results[:1]:
            if query.lower() in result['name'].lower():
                avg_confidence = min(1.0, avg_confidence + 0.3)
        
        return avg_confidence

    def _validate_results_with_llm(self, query: str, results: List[Dict]) -> List[Dict]:
        """Use LLM to validate search results when confidence is low"""
        if not self.model or not results:
            return results
        
        try:
            # Prepare results for LLM validation
            result_names = [r['name'] for r in results[:5]]
            
            prompt = f"""Türkçe iç giyim ürün arama sonuçlarını değerlendir.

ARAMA SORGUSU: "{query}"

BULUNAN ÜRÜNLER:
{chr(10).join(f"{i+1}. {name}" for i, name in enumerate(result_names))}

GÖREV: Hangi ürünler arama sorgusuna uygun? Sadece uygun olanların numaralarını ver.

KURALLAR:
- Ürün tipi eşleşmeli (gecelik, pijama, sabahlık, takım)
- Özellikler eşleşmeli (dantelli, hamile, büyük beden)
- Renk belirtilmişse eşleşmeli
- Marka belirtilmişse eşleşmeli

ÇIKTI: Sadece uygun ürün numaraları (örnek: 1,3,5)"""

            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 50
                }
            )
            
            if response.text:
                # Parse LLM response
                valid_indices = []
                for char in response.text:
                    if char.isdigit():
                        idx = int(char) - 1
                        if 0 <= idx < len(results):
                            valid_indices.append(idx)
                
                if valid_indices:
                    validated_results = [results[i] for i in valid_indices]
                    logger.info(f"LLM validation: {len(results)} → {len(validated_results)} results")
                    return validated_results
        
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
        
        return results

    def _validate_cache_result(self, query: str, cached_result: List[Product]) -> bool:
        """Validate if cached result is relevant to the query"""
        if not query or not cached_result:
            return False
        
        query_lower = query.lower().strip()
        
        # Skip validation for attribute queries (color, size, stock)
        attribute_indicators = ['var mı', 'mevcut', 'stok', 'beden', 'fiyat']
        if any(indicator in query_lower for indicator in attribute_indicators):
            return True  # Always use cache for attribute queries
        
        # Skip validation for very short queries
        if len(query_lower) < 3:
            return True
        
        # Extract meaningful words from query
        query_words = [word for word in query_lower.split() if len(word) > 2]
        if not query_words:
            return True
        
        # Check first few products for relevance
        relevant_products = 0
        for product in cached_result[:3]:
            product_text = f"{product.name} {product.color}".lower()
            
            # Count matching words
            matches = sum(1 for word in query_words if word in product_text)
            match_ratio = matches / len(query_words)
            
            # Product is relevant if at least 60% of query words match
            if match_ratio >= 0.6:
                relevant_products += 1
        
        # Cache is valid if at least 50% of products are relevant
        return relevant_products / min(3, len(cached_result)) >= 0.5

def main():
    """Test the improved MVP system"""
    print("🚀 Improved Final MVP Chatbot System")
    print("=" * 50)
    
    try:
        # Initialize chatbot
        chatbot = ImprovedFinalMVPChatbot()
        
        # Health check
        health = chatbot.health_check()
        print(f"🏥 Health Check: {health}")
        
        # Test queries
        test_queries = [
            "merhaba",
            "hamile pijama arıyorum",
            "afrika gecelik",
            "telefon numaranız nedir"
        ]
        
        for query in test_queries:
            print(f"\n👤 Test: {query}")
            response = chatbot.chat(query)
            print(f"🤖 Response: {response.message[:100]}...")
            print(f"📊 Intent: {response.intent} ({response.confidence:.2f})")
    
    except Exception as e:
        print(f"❌ Error: {e}")

    def _update_business_responses(self, chatbot_config: Dict):
        """Update chatbot responses for specific business"""
        business_info = chatbot_config.get("business_info", {})
        
        # Update business info
        self.business_info.update(business_info)
        
        # Update fixed responses with business-specific info
        from fixed_responses import get_fixed_responses
        self.fixed_responses = get_fixed_responses(self.business_info, self._get_whatsapp_support_text)
        
        # Update greeting message if customized
        welcome_message = chatbot_config.get("welcome_message")
        if welcome_message:
            self.fixed_responses["greeting"] = welcome_message

if __name__ == "__main__":
    main()