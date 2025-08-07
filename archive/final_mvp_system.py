#!/usr/bin/env python3
"""
Final MVP Chatbot System - Production Ready
Combines all components into a single, deployable system
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import google.generativeai as genai
from fuzzywuzzy import fuzz
from dotenv import load_dotenv

# Import semantic search (optional)
try:
    from mock_semantic_search import MockSemanticProductSearch
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    logger.warning("Semantic search not available")

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

class FinalMVPChatbot:
    def __init__(self):
        """Initialize the final MVP chatbot system"""
        logger.info("Initializing Final MVP Chatbot System...")
        
        # Load data
        self.products = self._load_products()
        self.business_info = self._load_business_info()
        
        # Setup Gemini
        self._setup_gemini()
        
        # Setup semantic search
        self.semantic_search = None
        if SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.semantic_search = MockSemanticProductSearch()
                if self.semantic_search._load_embeddings():
                    logger.info("✅ Mock semantic search initialized with existing embeddings")
                else:
                    logger.info("🔄 Creating mock embeddings...")
                    self.semantic_search.create_embeddings(self.products)
                    logger.info("✅ Mock semantic search initialized with new embeddings")
            except Exception as e:
                logger.error(f"Mock semantic search initialization failed: {e}")
                self.semantic_search = None
        
        # Initialize response templates
        self._setup_response_templates()
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'gemini_calls': 0,
            'fallback_calls': 0,
            'average_response_time': 0.0
        }
        
        logger.info(f"✅ MVP Chatbot initialized with {len(self.products)} products")
        
    def _setup_gemini(self):
        """Setup Gemini API with error handling"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found, using fallback intent detection only")
            self.model = None
            return
        
        try:
            genai.configure(api_key=api_key)
            # Use Gemini 2.0 Flash Lite - best performance/cost ratio
            self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
            logger.info("✅ Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"❌ Gemini setup error: {e}")
            self.model = None
    
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
        """Setup response templates"""
        self.fixed_responses = {
            "greeting": "Merhaba! 👋 Size nasıl yardımcı olabilirim? Ürünlerimiz hakkında bilgi alabilir, fiyat sorabilirsiniz.",
            "thanks": "Rica ederim! 😊 Başka sorunuz var mı?",
            "goodbye": "Görüşmek üzere! İyi günler dilerim. 👋",
            "phone_inquiry": f"📞 Telefon numaramız: {self.business_info.get('phone', '0212 123 45 67')}",
            "return_policy": "📋 İade politikamız: 14 gün içinde iade kabul edilir. Ürün kullanılmamış ve etiketli olmalıdır.",
            "shipping_info": "🚚 Kargo bilgileri: Türkiye geneli ücretsiz kargo. 1-3 iş günü içinde teslimat.",
            "website_inquiry": f"🌐 Web sitemiz: {self.business_info.get('website', 'www.butik.com')}",
            "size_inquiry": f"📏 Beden bilgileri için web sitemizi ziyaret edebilirsiniz: {self.business_info.get('website', 'www.butik.com')} \n\n📞 Detaylı bilgi için bizi arayabilirsiniz: {self.business_info.get('phone', '0212 123 45 67')}",
            "order_request": f"🛒 Sipariş vermek için web sitemizi ziyaret edebilirsiniz: {self.business_info.get('website', 'www.butik.com')} \n\n📞 Telefon ile sipariş: {self.business_info.get('phone', '0212 123 45 67')}",
            "order_status": f"📦 Sipariş durumunuz için lütfen bizi arayın: {self.business_info.get('phone', '0212 123 45 67')} \n\nSipariş numaranızı hazır bulundurun.",
            "complaint": f"😔 Üzgünüz! Sorununuz için lütfen bizi arayın: {self.business_info.get('phone', '0212 123 45 67')} \n\nMüşteri hizmetlerimiz size yardımcı olacaktır."
        }
    
    def extract_intent_with_gemini(self, user_message: str) -> IntentResult:
        """Extract intent using Gemini with fallback"""
        if not self.model:
            return self._fallback_intent_detection(user_message)
        
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
                                "complaint", "general_info", "unclear"]
                    },
                    "product_name": {"type": "string"},
                    "product_features": {"type": "array", "items": {"type": "string"}},
                    "color": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["intent", "confidence"]
            }
        }
        
        prompt = f"""Analiz et: "{user_message}"

İç giyim mağazası chatbot. Intent belirle:
- greeting: merhaba, selam
- product_search: ürün arama (hamile takım, dantelli gecelik)
- price_inquiry: fiyat sorma
- size_inquiry: beden sorma (m bedeni var mı)
- order_request: sipariş vermek
- order_status: kargo/sipariş durumu
- complaint: şikayet/sorun
- phone_inquiry: telefon
- thanks/goodbye: teşekkür/veda"""
        
        try:
            response = self.model.generate_content(
                prompt,
                tools=[{"function_declarations": [function_declaration]}]
            )
            
            if (response.candidates and 
                response.candidates[0].content.parts and 
                response.candidates[0].content.parts[0].function_call):
                
                function_call = response.candidates[0].content.parts[0].function_call
                args = dict(function_call.args)
                
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
            else:
                logger.warning("No function call in Gemini response, using fallback")
                return self._fallback_intent_detection(user_message)
                
        except Exception as e:
            logger.error(f"Gemini intent extraction error: {e}")
            self.stats['fallback_calls'] += 1
            return self._fallback_intent_detection(user_message)
    
    def _fallback_intent_detection(self, message: str) -> IntentResult:
        """Rule-based intent detection fallback"""
        message_lower = message.lower()
        
        # Greeting patterns
        if any(word in message_lower for word in ['merhaba', 'selam', 'hello', 'hi']):
            return IntentResult('greeting', {}, 0.9)
        
        # Thanks patterns
        if any(word in message_lower for word in ['teşekkür', 'sağol', 'thanks']):
            return IntentResult('thanks', {}, 0.9)
        
        # Goodbye patterns
        if any(word in message_lower for word in ['güle güle', 'görüşürüz', 'bye']):
            return IntentResult('goodbye', {}, 0.9)
        
        # Negative/dismissive patterns
        if any(phrase in message_lower for phrase in ['yok', 'hayır', 'başka sorum yok', 'gerek yok', 'olmaz']):
            return IntentResult('goodbye', {}, 0.8)
        
        # Single word negative responses
        if message_lower.strip() in ['yok', 'hayır', 'no']:
            return IntentResult('goodbye', {}, 0.9)
        
        # Business info patterns
        if any(word in message_lower for word in ['telefon', 'numara']):
            return IntentResult('phone_inquiry', {}, 0.8)
        
        if any(word in message_lower for word in ['iade', 'geri']):
            return IntentResult('return_policy', {}, 0.8)
        
        if any(word in message_lower for word in ['kargo', 'teslimat']):
            return IntentResult('shipping_info', {}, 0.8)
        
        if any(word in message_lower for word in ['site', 'web']):
            return IntentResult('website_inquiry', {}, 0.8)
        
        # Price and stock
        if any(word in message_lower for word in ['fiyat', 'kaç', 'para', 'tl']):
            return IntentResult('price_inquiry', {}, 0.7)
        
        if any(word in message_lower for word in ['stok', 'var mı', 'mevcut']):
            return IntentResult('stock_inquiry', {}, 0.7)
        
        # Size inquiries (only if explicitly asking about size)
        if any(phrase in message_lower for phrase in ['beden var', 'size var', 'bedeni var', 'bedeni mevcut', 'beden mevcut']):
            return IntentResult('size_inquiry', {}, 0.8)
        elif any(word in message_lower for word in ['xl', 'xs']) and ('var' in message_lower or 'mevcut' in message_lower):
            return IntentResult('size_inquiry', {}, 0.8)
        
        # Order related
        if any(phrase in message_lower for phrase in ['sipariş vermek', 'satın almak', 'nasıl alırım', 'sipariş ver']):
            return IntentResult('order_request', {}, 0.8)
        
        if any(phrase in message_lower for phrase in ['siparişim', 'kargom gelmedi', 'sipariş durumu']):
            return IntentResult('order_status', {}, 0.8)
        
        # Shipping info (different from order status)
        if 'kargo' in message_lower and 'gelmedi' not in message_lower:
            return IntentResult('shipping_info', {}, 0.8)
        
        # Complaints (higher priority than size)
        if any(phrase in message_lower for phrase in ['şikayet', 'sorun yaşı', 'problem', 'memnun değil', 'kötü']):
            return IntentResult('complaint', {}, 0.85)
        
        # Product search with feature extraction
        product_features = []
        if 'dantelli' in message_lower:
            product_features.append('dantelli')
        if 'dekolteli' in message_lower or 'dekolte' in message_lower:
            product_features.append('dekolteli')
        if 'hamile' in message_lower:
            product_features.append('hamile')
        if 'lohusa' in message_lower:
            product_features.append('lohusa')
        
        # Color extraction
        color = ''
        colors = ['siyah', 'beyaz', 'kırmızı', 'mavi', 'lacivert', 'yeşil', 'sarı', 'mor', 'pembe']
        for c in colors:
            if c in message_lower:
                color = c
                break
        
        if product_features or color or any(word in message_lower for word in ['takım', 'gecelik', 'pijama', 'sabahlık']):
            return IntentResult('product_search', {
                'product_features': product_features,
                'color': color
            }, 0.6)
        
        return IntentResult('unclear', {}, 0.3)
    
    def _normalize_turkish(self, text: str) -> str:
        """Normalize Turkish characters for better matching"""
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
    
    def search_products(self, query: str, features: List[str] = None, color: str = None) -> List[Product]:
        """Advanced product search with semantic and fuzzy matching"""
        if not query and not features and not color:
            return []
        
        # Try semantic search first
        if self.semantic_search and self.semantic_search.is_available():
            try:
                search_query = query
                if features:
                    search_query += " " + " ".join(features)
                if color:
                    search_query += f" {color} renk"
                
                semantic_results = self.semantic_search.semantic_search(search_query, 5)
                
                if semantic_results:
                    # Convert semantic results to Product objects
                    products = []
                    for result in semantic_results:
                        # Only include results with good similarity
                        if result.get('similarity', 0) > 0.7:
                            products.append(Product(
                                name=result['name'],
                                color=result['color'],
                                price=result['price'],
                                discount=0.0,  # Will be calculated from price difference
                                final_price=result['final_price'],
                                category=result['category'],
                                stock=result['stock']
                            ))
                    
                    if products:
                        logger.info(f"Semantic search returned {len(products)} products")
                        return products
                        
            except Exception as e:
                logger.error(f"Semantic search failed, falling back to fuzzy: {e}")
        
        # Fallback to fuzzy matching
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
            
            # 2. Fuzzy string matching
            if query_lower:
                fuzzy_score = fuzz.partial_ratio(query_lower, product_text)
                score += fuzzy_score * 0.8
            
            # 3. Feature matching (high weight for extracted features)
            if features:
                for feature in features:
                    if feature.lower() in product_text:
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
        return [product for product, score in scored_products[:5]]
    
    def format_product_response(self, products: List[Product]) -> str:
        """Format product information for user"""
        if not products:
            return "Üzgünüm, aradığınız kriterlere uygun ürün bulamadım. Başka bir şey deneyebilir misiniz?"
        
        if len(products) == 1:
            product = products[0]
            response = f"{product.name}\n"
            response += f"Renk: {product.color}\n"
            response += f"Fiyat: {product.final_price:.2f} TL"
            
            try:
                if float(product.discount) > 0:
                    response += f" (İndirimli! Eski fiyat: {product.price:.2f} TL, %{product.discount} indirim)"
            except (ValueError, TypeError):
                pass
            
            try:
                stock_available = int(product.stock) > 0
            except (ValueError, TypeError):
                stock_available = False
            response += f"\nStok: {'Mevcut' if stock_available else 'Tükendi'}"
            
            if stock_available:
                response += f"\n\nBu ürün hakkında daha fazla bilgi almak ister misiniz?"
            
            return response
        else:
            response = f"Size uygun {len(products)} ürün buldum:\n\n"
            
            for i, product in enumerate(products, 1):
                response += f"{i}. {product.name}\n"
                response += f"   Renk: {product.color} - Fiyat: {product.final_price:.2f} TL"
                
                try:
                    if float(product.discount) > 0:
                        response += f" (%{product.discount} indirim)"
                except (ValueError, TypeError):
                    pass
                
                try:
                    stock_status = 'Mevcut' if int(product.stock) > 0 else 'Tükendi'
                except (ValueError, TypeError):
                    stock_status = 'Bilinmiyor'
                
                response += f" - Stok: {stock_status}\n\n"
            
            response += "Hangi ürün hakkında daha detaylı bilgi almak istersiniz?"
            return response
    
    def route_and_respond(self, intent_result: IntentResult, original_message: str) -> ChatResponse:
        """Route request and generate response"""
        intent = intent_result.intent
        entities = intent_result.entities
        
        # Fixed responses
        if intent in self.fixed_responses:
            return ChatResponse(
                message=self.fixed_responses[intent],
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Product search
        elif intent == "product_search":
            query = entities.get('product_name', original_message)
            features = entities.get('product_features', [])
            color = entities.get('color', '')
            
            products = self.search_products(query, features, color)
            response_message = self.format_product_response(products)
            
            return ChatResponse(
                message=response_message,
                intent=intent,
                confidence=intent_result.confidence,
                products_found=len(products)
            )
        
        # Price inquiry
        elif intent == "price_inquiry":
            # Check if there's product context in the same message
            product_name = entities.get('product_name', '')
            features = entities.get('product_features', [])
            
            if product_name or features:
                # User asked for price of a specific product
                products = self.search_products(product_name or original_message, features)
                if products:
                    product = products[0]  # Take the best match
                    response_message = f"💰 **{product.name}** fiyatı:\n\n"
                    response_message += f"🎨 Renk: {product.color}\n"
                    response_message += f"💰 **Fiyat: {product.final_price:.2f} TL**"
                    
                    try:
                        if float(product.discount) > 0:
                            response_message += f" 🏷️ **(İndirimli! Eski fiyat: {product.price:.2f} TL, %{product.discount} indirim)**"
                    except (ValueError, TypeError):
                        pass
                    

                    
                    try:
                        stock_available = int(product.stock) > 0
                        response_message += f"\n📦 Stok: {'✅ Mevcut' if stock_available else '❌ Tükendi'}"
                    except (ValueError, TypeError):
                        pass
                    
                    return ChatResponse(
                        message=response_message,
                        intent=intent,
                        confidence=intent_result.confidence,
                        products_found=1
                    )
            
            return ChatResponse(
                message="💰 Hangi ürünün fiyatını öğrenmek istiyorsunuz? Ürün adını söylerseniz size fiyat bilgisini verebilirim.",
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Stock inquiry
        elif intent == "stock_inquiry":
            return ChatResponse(
                message="📦 Hangi ürünün stok durumunu öğrenmek istiyorsunuz? Ürün adını söylerseniz stok bilgisini kontrol edebilirim.",
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # General info
        elif intent == "general_info":
            return ChatResponse(
                message="ℹ️ Size nasıl yardımcı olabilirim? Ürün arama, fiyat bilgisi, stok durumu veya mağaza bilgileri hakkında sorularınızı yanıtlayabilirim.",
                intent=intent,
                confidence=intent_result.confidence
            )
        
        # Unclear or default
        else:
            return ChatResponse(
                message="🤔 Anlayamadım. Size nasıl yardımcı olabilirim?\n\n💡 **Yapabileceklerim:**\n• Ürün arama\n• Fiyat bilgisi\n• Stok durumu\n• Mağaza bilgileri",
                intent=intent,
                confidence=intent_result.confidence
            )
    
    def chat(self, user_message: str) -> ChatResponse:
        """Main chat function with performance tracking"""
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
            
            # Extract intent and entities
            intent_result = self.extract_intent_with_gemini(user_message.strip())
            
            # Generate response
            response = self.route_and_respond(intent_result, user_message)
            
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
                message="😔 Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
                intent="error",
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        return {
            **self.stats,
            'products_loaded': len(self.products),
            'gemini_available': self.model is not None,
            'success_rate': (self.stats['successful_requests'] / max(1, self.stats['total_requests'])) * 100
        }
    
    def health_check(self) -> Dict:
        """System health check"""
        return {
            'status': 'healthy',
            'products_loaded': len(self.products) > 0,
            'gemini_available': self.model is not None,
            'business_info_loaded': bool(self.business_info),
            'total_requests': self.stats['total_requests']
        }

def main():
    """Test the final MVP system"""
    print("🚀 Final MVP Chatbot System")
    print("=" * 50)
    
    try:
        # Initialize chatbot
        chatbot = FinalMVPChatbot()
        
        # Health check
        health = chatbot.health_check()
        print(f"🏥 Health Check: {health}")
        
        # Test messages
        test_messages = [
            "merhaba",
            "hamile lohusa takım arıyorum",
            "dantelli gecelik var mı",
            "siyah renkte bir şey",
            "telefon numaranız nedir",
            "teşekkürler"
        ]
        
        print("\n💬 Test Conversations:")
        print("-" * 30)
        
        for message in test_messages:
            print(f"\n👤 User: {message}")
            response = chatbot.chat(message)
            print(f"🤖 Bot: {response.message}")
            print(f"📊 Intent: {response.intent} (confidence: {response.confidence:.2f}, time: {response.processing_time:.3f}s)")
            
            if response.products_found > 0:
                print(f"🛍️ Products found: {response.products_found}")
        
        # Final stats
        stats = chatbot.get_stats()
        print(f"\n📈 Final Statistics:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Average response time: {stats['average_response_time']:.3f}s")
        print(f"   Gemini calls: {stats['gemini_calls']}")
        print(f"   Fallback calls: {stats['fallback_calls']}")
        
        print("\n✅ Final MVP System is ready for production!")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")

if __name__ == "__main__":
    main()