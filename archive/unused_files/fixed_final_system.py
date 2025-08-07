#!/usr/bin/env python3
"""
Fixed Final MVP Chatbot System
Simplified, robust, and accurate system
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
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
class ChatResponse:
    message: str
    intent: str
    confidence: float
    products_found: int = 0
    processing_time: float = 0.0

class FixedFinalChatbot:
    """Simplified, robust chatbot system"""
    
    def __init__(self):
        logger.info("Initializing Fixed Final Chatbot System...")
        
        # Load data
        self.products = self._load_products()
        self.business_info = self._load_business_info()
        
        # Simple conversation context
        self.last_products = []
        self.conversation_count = 0
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_response_time': 0.0
        }
        
        # Setup response templates
        self._setup_responses()
        
        logger.info(f"✅ Fixed Chatbot initialized with {len(self.products)} products")
    
    def _load_products(self) -> List[Product]:
        """Load products"""
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
            logger.error(f"Error loading products: {e}")
            return []
    
    def _load_business_info(self) -> Dict:
        """Load business information"""
        try:
            with open('data/butik_meta.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading business info: {e}")
            return {
                'phone': '0555 555 55 55',
                'website': 'www.butik.com',
                'email': 'info@butik.com'
            }
    
    def _setup_responses(self):
        """Setup response templates"""
        self.responses = {
            "greeting": "Merhaba! 👋 Size nasıl yardımcı olabilirim? Ürünlerimiz hakkında bilgi alabilir, fiyat sorabilirsiniz.",
            "thanks": "Rica ederim! 😊 Başka sorunuz var mı?",
            "goodbye": "Görüşmek üzere! İyi günler dilerim. 👋",
            "phone_inquiry": f"📞 Telefon numaramız: {self.business_info.get('phone', '0555 555 55 55')}",
            "return_policy": "📋 İade politikamız: 14 gün içinde iade kabul edilir. Ürün kullanılmamış ve etiketli olmalıdır.",
            "shipping_info": "🚚 Kargo bilgileri: Türkiye geneli ücretsiz kargo. 1-3 iş günü içinde teslimat.",
            "website_inquiry": f"🌐 Web sitemiz: {self.business_info.get('website', 'www.butik.com')}",
            "contact_info": f"📞 Telefon: {self.business_info.get('phone', '0555 555 55 55')}\n🌐 Web: {self.business_info.get('website', 'www.butik.com')}",
            "unclear": "🤔 Anlayamadım. Size nasıl yardımcı olabilirim?\n\n💡 **Yapabileceklerim:**\n• 🔍 Ürün arama\n• 💰 Fiyat bilgisi\n• 📦 Stok durumu\n• 🏢 Mağaza bilgileri"
        }
    
    def detect_intent(self, message: str) -> Tuple[str, float]:
        """Simple, reliable intent detection"""
        message_lower = message.lower().strip()
        
        # Empty or very short messages
        if not message_lower or len(message_lower) < 2:
            return "unclear", 0.3
        
        # Greeting patterns (HIGHEST PRIORITY)
        greeting_patterns = ['merhaba', 'selam', 'hello', 'hi', 'hey']
        if any(word in message_lower for word in greeting_patterns):
            return "greeting", 0.9
        
        # Special handling for "iyi günler" - context dependent
        if 'iyi günler' in message_lower:
            # If it's early in conversation, it's a greeting
            if self.conversation_count <= 2:
                return "greeting", 0.9
            else:
                return "goodbye", 0.9
        
        # Thanks patterns (HIGH PRIORITY)
        thanks_patterns = ['teşekkür', 'sağol', 'thanks', 'merci', 'eyvallah', 'sağ ol']
        if any(word in message_lower for word in thanks_patterns):
            return "thanks", 0.9
        
        # Goodbye patterns (HIGH PRIORITY)
        goodbye_patterns = ['güle güle', 'görüşürüz', 'bye', 'hoşça kal', 'iyi günler dilerim', 'hoşçakal']
        if any(phrase in message_lower for phrase in goodbye_patterns):
            return "goodbye", 0.9
        
        # Negative/dismissive patterns
        negative_patterns = ['yok', 'hayır', 'başka sorum yok', 'gerek yok', 'olmaz', 'istemiyorum']
        if any(phrase in message_lower for phrase in negative_patterns):
            return "goodbye", 0.8
        
        # Business info patterns (BEFORE product search)
        if any(word in message_lower for word in ['telefon', 'numara', 'ara']):
            return "phone_inquiry", 0.8
        
        # Enhanced return policy patterns
        if any(phrase in message_lower for phrase in ['iade var mı', 'iade nasıl', 'iade politika', 'iade']):
            return "return_policy", 0.8
        
        if any(word in message_lower for word in ['kargo', 'teslimat']):
            return "shipping_info", 0.8
        
        if any(word in message_lower for word in ['site', 'web']):
            return "website_inquiry", 0.8
        
        if any(word in message_lower for word in ['iletişim', 'adres']):
            return "contact_info", 0.8
        
        # Product search patterns
        product_indicators = [
            'afrika', 'hamile', 'lohusa', 'dantelli', 'gecelik', 'pijama', 
            'sabahlık', 'takım', 'elbise', 'şort', 'tulum',
            'siyah', 'beyaz', 'kırmızı', 'mavi', 'lacivert', 'yeşil'
        ]
        
        if any(indicator in message_lower for indicator in product_indicators):
            return "product_search", 0.8
        
        # Price inquiry
        if any(word in message_lower for word in ['fiyat', 'kaç', 'para', 'tl']):
            return "price_inquiry", 0.7
        
        # Stock inquiry
        if any(phrase in message_lower for phrase in ['stok', 'var mı', 'mevcut']):
            return "stock_inquiry", 0.7
        
        # If nothing matches, it's unclear
        return "unclear", 0.3
    
    def search_products(self, query: str) -> List[Product]:
        """Simple, effective product search"""
        if not query:
            return []
        
        query_lower = query.lower()
        scored_products = []
        
        # Special handling for specific product names
        specific_products = {
            'afrika gecelik': 1,  # Return only 1 result
            'afrika': 1,
            'etnik gecelik': 1
        }
        
        max_results = 5
        for specific_query, count in specific_products.items():
            if specific_query in query_lower:
                max_results = count
                break
        
        for product in self.products:
            score = 0
            product_text = f"{product.name} {product.color}".lower()
            
            # Exact word matches (highest score)
            query_words = query_lower.split()
            exact_matches = 0
            for word in query_words:
                if len(word) > 2 and word in product_text:
                    score += 50
                    exact_matches += 1
            
            # Bonus for matching all words
            if exact_matches == len([w for w in query_words if len(w) > 2]):
                score += 100
            
            # Fuzzy matching
            fuzzy_score = fuzz.partial_ratio(query_lower, product_text)
            score += fuzzy_score * 0.5
            
            # Stock bonus
            if product.stock > 0:
                score += 10
            
            if score > 30:
                scored_products.append((product, score))
        
        # Sort by score and return limited results
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return [product for product, score in scored_products[:max_results]]
    
    def format_products(self, products: List[Product]) -> str:
        """Format product list"""
        if not products:
            return "Üzgünüm, aradığınız kriterlere uygun ürün bulamadım. Başka bir şey deneyebilir misiniz?"
        
        if len(products) == 1:
            product = products[0]
            response = f"✨ **{product.name}**\n\n"
            response += f"🎨 Renk: {product.color}\n"
            response += f"💰 Fiyat: **{product.final_price:.2f} TL**"
            
            if product.discount > 0:
                response += f" 🏷️ **(İndirimli! %{product.discount} indirim)**"
            
            response += f"\n📦 Stok: {'✅ Mevcut' if product.stock > 0 else '❌ Tükendi'}"
            
            if product.stock > 0:
                response += f"\n\n🛒 Sipariş için: {self.business_info.get('phone', '0555 555 55 55')}"
            
            return response
        else:
            response = f"🛍️ Size uygun **{len(products)} ürün** buldum:\n\n"
            
            for i, product in enumerate(products, 1):
                response += f"**{i}.** {product.name}\n"
                response += f"   🎨 Renk: {product.color} - 💰 **{product.final_price:.2f} TL**"
                
                if product.discount > 0:
                    response += f" 🏷️ *(%{product.discount} indirim)*"
                
                response += f" - 📦 {'✅ Mevcut' if product.stock > 0 else '❌ Tükendi'}\n\n"
            
            response += "💡 **Hangi ürün hakkında daha detaylı bilgi almak istersiniz?**"
            return response
    
    def handle_follow_up(self, message: str) -> Optional[str]:
        """Handle follow-up questions about previous products"""
        if not self.last_products:
            return None
        
        message_lower = message.lower()
        
        # Number selection
        if message.strip().isdigit():
            try:
                index = int(message.strip()) - 1
                if 0 <= index < len(self.last_products):
                    product = self.last_products[index]
                    return self.format_products([product])
            except (ValueError, IndexError):
                pass
        
        # Price questions about previous products
        if any(word in message_lower for word in ['fiyat', 'kaç', 'para']):
            if len(self.last_products) == 1:
                product = self.last_products[0]
                return f"💰 **{product.name}** fiyatı: {product.final_price:.2f} TL"
            else:
                response = "💰 Fiyat bilgileri:\n\n"
                for i, product in enumerate(self.last_products[:3], 1):
                    response += f"{i}. {product.name[:40]}... - {product.final_price:.2f} TL\n"
                return response
        
        # Stock questions about previous products
        if any(phrase in message_lower for phrase in ['stok', 'var mı', 'mevcut']):
            if len(self.last_products) == 1:
                product = self.last_products[0]
                stock_status = 'Mevcut' if product.stock > 0 else 'Tükendi'
                return f"📦 **{product.name}** stok durumu: {stock_status}"
            else:
                response = "📦 Stok durumları:\n\n"
                for i, product in enumerate(self.last_products[:3], 1):
                    stock_status = 'Mevcut' if product.stock > 0 else 'Tükendi'
                    response += f"{i}. {product.name[:40]}... - {stock_status}\n"
                return response
        
        return None
    
    def chat(self, user_message: str) -> ChatResponse:
        """Main chat function"""
        start_time = time.time()
        
        try:
            self.stats['total_requests'] += 1
            self.conversation_count += 1
            
            # Validate input
            if not user_message or not user_message.strip():
                return ChatResponse(
                    message="📝 Lütfen bir mesaj yazın.",
                    intent="empty",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # Check for follow-up first
            follow_up_response = self.handle_follow_up(user_message)
            if follow_up_response:
                return ChatResponse(
                    message=follow_up_response,
                    intent="followup",
                    confidence=0.9,
                    processing_time=time.time() - start_time
                )
            
            # Detect intent
            intent, confidence = self.detect_intent(user_message)
            
            # Handle different intents
            if intent in self.responses:
                response_message = self.responses[intent]
                products_found = 0
            
            elif intent == "product_search":
                products = self.search_products(user_message)
                response_message = self.format_products(products)
                products_found = len(products)
                self.last_products = products  # Store for follow-up
            
            elif intent == "price_inquiry":
                if self.last_products:
                    response_message = self.handle_follow_up("fiyat") or "💰 Hangi ürünün fiyatını öğrenmek istiyorsunuz?"
                    products_found = 0
                else:
                    response_message = "💰 Hangi ürünün fiyatını öğrenmek istiyorsunuz? Ürün adını söylerseniz size fiyat bilgisini verebilirim."
                    products_found = 0
            
            elif intent == "stock_inquiry":
                if self.last_products:
                    response_message = self.handle_follow_up("stok") or "📦 Hangi ürünün stok durumunu öğrenmek istiyorsunuz?"
                    products_found = 0
                else:
                    response_message = "📦 Hangi ürünün stok durumunu öğrenmek istiyorsunuz? Ürün adını söylerseniz stok bilgisini kontrol edebilirim."
                    products_found = 0
            
            else:
                response_message = self.responses["unclear"]
                products_found = 0
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update stats
            self.stats['successful_requests'] += 1
            self.stats['average_response_time'] = (
                (self.stats['average_response_time'] * (self.stats['successful_requests'] - 1) + processing_time) 
                / self.stats['successful_requests']
            )
            
            logger.info(f"✅ Request processed: intent={intent}, confidence={confidence:.2f}, time={processing_time:.3f}s")
            
            return ChatResponse(
                message=response_message,
                intent=intent,
                confidence=confidence,
                products_found=products_found,
                processing_time=processing_time
            )
            
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
            'success_rate': (self.stats['successful_requests'] / max(1, self.stats['total_requests'])) * 100,
            'conversation_count': self.conversation_count
        }
    
    def health_check(self) -> Dict:
        """System health check"""
        return {
            'status': 'healthy',
            'products_loaded': len(self.products) > 0,
            'business_info_loaded': bool(self.business_info),
            'total_requests': self.stats['total_requests']
        }
    
    def reset_conversation(self):
        """Reset conversation context"""
        self.last_products = []
        self.conversation_count = 0

def main():
    """Test the fixed system"""
    print("🚀 Fixed Final Chatbot System")
    print("=" * 50)
    
    try:
        chatbot = FixedFinalChatbot()
        
        # Test messages
        test_messages = [
            "merhaba",
            "sağol",
            "afrika gecelik",
            "fiyatı nedir",
            "1",
            "teşekkürler",
            "iyi günler"
        ]
        
        print("\n💬 Test Conversations:")
        print("-" * 30)
        
        for message in test_messages:
            print(f"\n👤 User: {message}")
            response = chatbot.chat(message)
            print(f"🤖 Bot: {response.message[:100]}...")
            print(f"🎯 Intent: {response.intent} ({response.confidence:.2f})")
            print(f"⏱️ Time: {response.processing_time:.3f}s")
        
        print(f"\n📊 Final Stats: {chatbot.get_stats()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()