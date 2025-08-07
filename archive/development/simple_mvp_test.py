#!/usr/bin/env python3
"""
Basit MVP Test - Gemini olmadan önce temel yapıyı test edelim
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from fuzzywuzzy import fuzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Product:
    code: str
    name: str
    color: str
    price: float
    discount: float
    final_price: float
    category: str
    stock: int

class SimpleMVPChatbot:
    def __init__(self):
        """Initialize simple MVP chatbot"""
        self.products = self._load_products()
        self.business_info = self._load_business_info()
        
        # Sabit cevaplar
        self.fixed_responses = {
            "greeting": "Merhaba! Size nasıl yardımcı olabilirim? Ürünlerimiz hakkında bilgi alabilir, fiyat sorabilirsiniz.",
            "thanks": "Rica ederim! Başka sorunuz var mı?",
            "goodbye": "Görüşmek üzere! İyi günler dilerim.",
            "phone": "Telefon numaramız: 0212 123 45 67",
            "return_policy": "İade politikamız: 14 gün içinde iade kabul edilir. Ürün kullanılmamış olmalıdır.",
            "shipping": "Kargo bilgileri: Türkiye geneli ücretsiz kargo. 1-3 iş günü içinde teslimat.",
            "website": "Web sitemiz: www.butik.com"
        }
        
    def _load_products(self) -> List[Product]:
        """Load products from JSON file"""
        try:
            with open('data/products.json', 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            products = []
            for item in products_data:
                products.append(Product(
                    code=item['code'],
                    name=item['name'],
                    color=item['color'],
                    price=item['price'],
                    discount=item['discount'],
                    final_price=item['final_price'],
                    category=item['category'],
                    stock=item['stock']
                ))
            
            logger.info(f"Loaded {len(products)} products")
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
            return {}
    
    def simple_intent_detection(self, message: str) -> str:
        """Basit intent detection"""
        message_lower = message.lower()
        
        # Greeting patterns
        if any(word in message_lower for word in ['merhaba', 'selam', 'hello', 'hi']):
            return 'greeting'
        
        # Thanks patterns
        if any(word in message_lower for word in ['teşekkür', 'sağol', 'thanks']):
            return 'thanks'
        
        # Goodbye patterns
        if any(word in message_lower for word in ['güle güle', 'görüşürüz', 'bye']):
            return 'goodbye'
        
        # Business info patterns
        if any(word in message_lower for word in ['telefon', 'numara']):
            return 'phone'
        
        if any(word in message_lower for word in ['iade', 'geri']):
            return 'return_policy'
        
        if any(word in message_lower for word in ['kargo', 'teslimat']):
            return 'shipping'
        
        if any(word in message_lower for word in ['site', 'web']):
            return 'website'
        
        # Product search (default for other messages)
        if any(word in message_lower for word in ['takım', 'gecelik', 'pijama', 'sabahlık', 'dantelli', 'dekolteli', 'hamile', 'lohusa']):
            return 'product_search'
        
        return 'unclear'
    
    def search_products(self, query: str) -> List[Product]:
        """Basit ürün arama"""
        if not query:
            return []
        
        scored_products = []
        query_lower = query.lower()
        
        for product in self.products:
            score = 0
            product_text = f"{product.name} {product.color}".lower()
            
            # Exact match
            if query_lower in product_text:
                score += 100
            
            # Fuzzy matching
            fuzzy_score = fuzz.partial_ratio(query_lower, product_text)
            score += fuzzy_score * 0.8
            
            # Feature matching
            if 'dantelli' in query_lower and 'dantelli' in product_text:
                score += 50
            if 'dekolteli' in query_lower and 'dekolteli' in product_text:
                score += 50
            if 'hamile' in query_lower and 'hamile' in product_text:
                score += 50
            if 'lohusa' in query_lower and 'lohusa' in product_text:
                score += 50
            
            if score > 30:  # Minimum threshold
                scored_products.append((product, score))
        
        # Sort by score and return top 3
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return [product for product, score in scored_products[:3]]
    
    def format_product_response(self, products: List[Product]) -> str:
        """Ürün bilgilerini formatla"""
        if not products:
            return "Üzgünüm, aradığınız kriterlere uygun ürün bulamadım. Başka bir şey deneyebilir misiniz?"
        
        if len(products) == 1:
            product = products[0]
            response = f"✨ {product.name}\n"
            response += f"🎨 Renk: {product.color}\n"
            response += f"💰 Fiyat: {product.final_price:.2f} TL"
            if product.discount > 0:
                response += f" (İndirimli! %{product.discount} indirim)"
            response += f"\n📦 Stok: {'Mevcut' if product.stock > 0 else 'Tükendi'}"
            response += f"\n🏷️ Ürün Kodu: {product.code}"
            return response
        else:
            response = f"Size uygun {len(products)} ürün buldum:\n\n"
            for i, product in enumerate(products, 1):
                response += f"{i}. {product.name}\n"
                response += f"   🎨 {product.color} - 💰 {product.final_price:.2f} TL"
                if product.discount > 0:
                    response += f" (%{product.discount} indirim)"
                response += f" - 🏷️ {product.code}\n\n"
            return response
    
    def chat(self, user_message: str) -> str:
        """Ana chat fonksiyonu"""
        try:
            # 1. Intent detection
            intent = self.simple_intent_detection(user_message)
            logger.info(f"Intent: {intent}")
            
            # 2. Route and respond
            if intent in self.fixed_responses:
                return self.fixed_responses[intent]
            elif intent == "product_search":
                products = self.search_products(user_message)
                return self.format_product_response(products)
            else:
                return "Anlayamadım. Size nasıl yardımcı olabilirim? Ürün arayabilir, fiyat sorabilir veya mağaza bilgilerini öğrenebilirsiniz."
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

def main():
    """Test the simple MVP chatbot"""
    print("🤖 Basit MVP Chatbot başlatılıyor...")
    
    try:
        chatbot = SimpleMVPChatbot()
        print("✅ Chatbot hazır!")
        print("💡 Test mesajları:")
        
        test_messages = [
            "merhaba",
            "hamile lohusa takım arıyorum",
            "dantelli gecelik var mı",
            "göğüs dekolteli takım",
            "telefon numaranız nedir",
            "teşekkürler"
        ]
        
        for message in test_messages:
            print(f"\n👤 User: {message}")
            response = chatbot.chat(message)
            print(f"🤖 Bot: {response}")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()