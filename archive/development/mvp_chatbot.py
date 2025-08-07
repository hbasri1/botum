#!/usr/bin/env python3
"""
MVP Chatbot System - Basit ve Etkili
Akış: User → LLM (Intent+Entity) → Route → Response
"""

import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import google.generativeai as genai
from fuzzywuzzy import fuzz
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
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

@dataclass
class IntentResult:
    intent: str
    entities: Dict[str, str]
    confidence: float

class MVPChatbot:
    def __init__(self):
        """Initialize MVP Chatbot with simple configuration"""
        self.products = self._load_products()
        self.business_info = self._load_business_info()
        self._setup_gemini()
        
        # Sabit cevaplar
        self.fixed_responses = {
            "greeting": "Merhaba! Size nasıl yardımcı olabilirim? Ürünlerimiz hakkında bilgi alabilir, fiyat sorabilirsiniz.",
            "thanks": "Rica ederim! Başka sorunuz var mı?",
            "goodbye": "Görüşmek üzere! İyi günler dilerim.",
            "phone": f"Telefon numaramız: {self.business_info.get('phone', 'Bilgi mevcut değil')}",
            "return_policy": "İade politikamız: 14 gün içinde iade kabul edilir. Ürün kullanılmamış olmalıdır.",
            "shipping": "Kargo bilgileri: Türkiye geneli ücretsiz kargo. 1-3 iş günü içinde teslimat.",
            "website": f"Web sitemiz: {self.business_info.get('website', 'Bilgi mevcut değil')}"
        }
        
    def _setup_gemini(self):
        """Setup Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
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
    
    def extract_intent_and_entities(self, user_message: str) -> IntentResult:
        """
        LLM ile intent ve entity çıkarma (Function Calling)
        """
        function_declaration = {
            "name": "analyze_user_intent",
            "description": "Kullanıcının mesajından intent ve entity'leri çıkar",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": [
                            "greeting",           # selam, merhaba
                            "thanks",            # teşekkür
                            "goodbye",           # güle güle
                            "phone_inquiry",     # telefon numarası
                            "return_policy",     # iade politikası
                            "shipping_info",     # kargo bilgisi
                            "website_inquiry",   # web sitesi
                            "product_search",    # ürün arama
                            "price_inquiry",     # fiyat sorma
                            "stock_inquiry",     # stok sorma
                            "general_info",      # genel bilgi
                            "unclear"            # belirsiz
                        ],
                        "description": "Kullanıcının niyeti"
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Aranan ürün adı (varsa)"
                    },
                    "product_features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ürün özellikleri (dantelli, dekolteli, hamile, vs.)"
                    },
                    "color": {
                        "type": "string",
                        "description": "Aranan renk (varsa)"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Intent güven skoru (0-1)"
                    }
                },
                "required": ["intent", "confidence"]
            }
        }
        
        prompt = f"""
        Türkçe e-ticaret chatbot için kullanıcı mesajını analiz et:
        
        Mesaj: "{user_message}"
        
        Bu bir iç giyim (pijama, gecelik, sabahlık) mağazası için chatbot.
        
        Örnekler:
        - "merhaba" → intent: greeting
        - "hamile lohusa takım arıyorum" → intent: product_search, product_features: ["hamile", "lohusa", "takım"]
        - "dantelli gecelik var mı" → intent: product_search, product_features: ["dantelli", "gecelik"]
        - "fiyatı ne kadar" → intent: price_inquiry
        - "stok var mı" → intent: stock_inquiry
        - "telefon numaranız" → intent: phone_inquiry
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                tools=[{"function_declarations": [function_declaration]}]
            )
            
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                args = dict(function_call.args)
                
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
                # Fallback: basit kural tabanlı
                return self._fallback_intent_detection(user_message)
                
        except Exception as e:
            logger.error(f"Intent extraction error: {e}")
            return self._fallback_intent_detection(user_message)
    
    def _fallback_intent_detection(self, message: str) -> IntentResult:
        """Basit kural tabanlı intent detection (fallback)"""
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
        
        # Business info patterns
        if any(word in message_lower for word in ['telefon', 'numara']):
            return IntentResult('phone_inquiry', {}, 0.8)
        
        if any(word in message_lower for word in ['iade', 'geri']):
            return IntentResult('return_policy', {}, 0.8)
        
        if any(word in message_lower for word in ['kargo', 'teslimat']):
            return IntentResult('shipping_info', {}, 0.8)
        
        if any(word in message_lower for word in ['site', 'web']):
            return IntentResult('website_inquiry', {}, 0.8)
        
        # Price inquiry
        if any(word in message_lower for word in ['fiyat', 'kaç', 'para', 'tl']):
            return IntentResult('price_inquiry', {}, 0.7)
        
        # Stock inquiry
        if any(word in message_lower for word in ['stok', 'var mı', 'mevcut']):
            return IntentResult('stock_inquiry', {}, 0.7)
        
        # Product search (default for other messages)
        product_features = []
        if 'dantelli' in message_lower:
            product_features.append('dantelli')
        if 'dekolteli' in message_lower or 'dekolte' in message_lower:
            product_features.append('dekolteli')
        if 'hamile' in message_lower:
            product_features.append('hamile')
        if 'lohusa' in message_lower:
            product_features.append('lohusa')
        
        if product_features or any(word in message_lower for word in ['takım', 'gecelik', 'pijama', 'sabahlık']):
            return IntentResult('product_search', {'product_features': product_features}, 0.6)
        
        return IntentResult('unclear', {}, 0.3)  
  def search_products(self, query: str, features: List[str] = None, color: str = None) -> List[Product]:
        """
        Basit ama etkili ürün arama (Semantic Search benzeri)
        """
        if not query and not features:
            return []
        
        scored_products = []
        
        for product in self.products:
            score = 0
            product_text = f"{product.name} {product.color}".lower()
            query_lower = query.lower() if query else ""
            
            # 1. Exact name match (en yüksek skor)
            if query_lower and query_lower in product_text:
                score += 100
            
            # 2. Fuzzy string matching
            if query_lower:
                fuzzy_score = fuzz.partial_ratio(query_lower, product_text)
                score += fuzzy_score * 0.8
            
            # 3. Feature matching
            if features:
                for feature in features:
                    if feature.lower() in product_text:
                        score += 50
            
            # 4. Color matching
            if color and color.lower() in product.color.lower():
                score += 30
            
            # 5. Category bonus
            if any(word in product_text for word in ['takım', 'gecelik', 'pijama', 'sabahlık']):
                score += 10
            
            if score > 20:  # Minimum threshold
                scored_products.append((product, score))
        
        # Sort by score and return top results
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return [product for product, score in scored_products[:5]]
    
    def format_product_response(self, products: List[Product]) -> str:
        """Ürün bilgilerini formatla"""
        if not products:
            return "Üzgünüm, aradığınız kriterlere uygun ürün bulamadım. Başka bir şey deneyebilir misiniz?"
        
        if len(products) == 1:
            product = products[0]
            response = f"✨ **{product.name}**\n"
            response += f"🎨 Renk: {product.color}\n"
            response += f"💰 Fiyat: {product.final_price:.2f} TL"
            if product.discount > 0:
                response += f" (İndirimli! Eski fiyat: {product.price:.2f} TL, %{product.discount} indirim)"
            response += f"\n📦 Stok: {'Mevcut' if product.stock > 0 else 'Tükendi'}"
            response += f"\n🏷️ Ürün Kodu: {product.code}"
            return response
        else:
            response = f"Size uygun {len(products)} ürün buldum:\n\n"
            for i, product in enumerate(products, 1):
                response += f"{i}. **{product.name}**\n"
                response += f"   🎨 {product.color} - 💰 {product.final_price:.2f} TL"
                if product.discount > 0:
                    response += f" (%{product.discount} indirim)"
                response += f" - 🏷️ {product.code}\n\n"
            response += "Hangi ürün hakkında daha detaylı bilgi almak istersiniz?"
            return response
    
    def route_and_respond(self, intent_result: IntentResult, original_message: str) -> str:
        """
        Intent'e göre route et ve cevap üret
        """
        intent = intent_result.intent
        entities = intent_result.entities
        
        # Sabit cevaplar
        if intent in self.fixed_responses:
            return self.fixed_responses[intent]
        
        # Ürün arama
        elif intent == "product_search":
            query = entities.get('product_name', original_message)
            features = entities.get('product_features', [])
            color = entities.get('color', '')
            
            products = self.search_products(query, features, color)
            return self.format_product_response(products)
        
        # Fiyat sorgusu (context'e ihtiyaç var, şimdilik basit)
        elif intent == "price_inquiry":
            return "Hangi ürünün fiyatını öğrenmek istiyorsunuz? Ürün adını söylerseniz size fiyat bilgisini verebilirim."
        
        # Stok sorgusu
        elif intent == "stock_inquiry":
            return "Hangi ürünün stok durumunu öğrenmek istiyorsunuz? Ürün adını söylerseniz stok bilgisini kontrol edebilirim."
        
        # Genel bilgi
        elif intent == "general_info":
            return "Size nasıl yardımcı olabilirim? Ürün arama, fiyat bilgisi, stok durumu veya mağaza bilgileri hakkında sorularınızı yanıtlayabilirim."
        
        # Belirsiz
        else:
            return "Anlayamadım. Size nasıl yardımcı olabilirim? Ürün arayabilir, fiyat sorabilir veya mağaza bilgilerini öğrenebilirsiniz."
    
    def chat(self, user_message: str) -> str:
        """
        Ana chat fonksiyonu - MVP akışı
        """
        try:
            # 1. LLM ile intent ve entity çıkar
            intent_result = self.extract_intent_and_entities(user_message)
            logger.info(f"Intent: {intent_result.intent}, Confidence: {intent_result.confidence}")
            
            # 2. Route et ve cevap üret
            response = self.route_and_respond(intent_result, user_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

def main():
    """Test the MVP chatbot"""
    print("🤖 MVP Chatbot başlatılıyor...")
    
    try:
        chatbot = MVPChatbot()
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