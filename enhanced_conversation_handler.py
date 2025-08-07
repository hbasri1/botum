#!/usr/bin/env python3
"""
Enhanced Conversation Handler
Handles conversation context, ambiguous inputs, and edge cases
"""

import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from attribute_system import handle_attribute_query
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    GREETING = "greeting"
    PRODUCT_SEARCH = "product_search"
    PRODUCT_DETAILS = "product_details"
    CLARIFICATION = "clarification"
    GOODBYE = "goodbye"

@dataclass
class ConversationContext:
    """Stores conversation context"""
    state: ConversationState
    last_products: List[Dict] = None
    last_query: str = ""
    clarification_attempts: int = 0
    user_preferences: Dict = None
    conversation_history: List[Dict] = None
    
    def __post_init__(self):
        if self.last_products is None:
            self.last_products = []
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.conversation_history is None:
            self.conversation_history = []

class EnhancedConversationHandler:
    """Handles complex conversation scenarios"""
    
    def __init__(self):
        self.context = ConversationContext(ConversationState.GREETING)
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes
        
        # Ambiguous input patterns
        self.ambiguous_patterns = {
            "iyi günler": ["greeting", "goodbye"],
            "merhaba": ["greeting"],
            "güle güle": ["goodbye"],
            "teşekkürler": ["thanks", "goodbye"],
            "tamam": ["acknowledgment", "goodbye"],
            "hayır": ["negative", "goodbye"],
            "yok": ["negative", "goodbye"],
            "evet": ["positive", "continue"],
            "olur": ["positive", "continue"]
        }
        
        # Image/visual reference patterns
        self.image_reference_patterns = [
            "fiyatı nedir", "fiyatı ne", "fiyat nedir", "kaç para", "ne kadar",
            "bunun fiyatı", "şunun fiyatı", "onun fiyatı", "bu kaç", "şu kaç",
            "bunu istiyorum", "şunu istiyorum", "onu istiyorum",
            "var mı", "mevcut mu", "stokta mı", "bulunuyor mu"
        ]
        
        # Context-aware responses
        self.contextual_responses = {
            "greeting_after_search": "Başka bir ürün aramak ister misiniz?",
            "clarification_needed": "Hangi ürün türünü arıyorsunuz? (gecelik, pijama, sabahlık, takım)",
            "color_clarification": "Hangi renkte arıyorsunuz?",
            "size_clarification": "Hangi beden arıyorsunuz?",
            "multiple_meanings": "Ne demek istediğinizi açıklayabilir misiniz?"
        }
    
    def detect_ambiguity(self, message: str) -> Tuple[bool, List[str]]:
        """Detect if message has multiple possible meanings"""
        message_lower = message.lower().strip()
        
        # Check for ambiguous patterns
        for pattern, meanings in self.ambiguous_patterns.items():
            if pattern in message_lower:
                if len(meanings) > 1:
                    return True, meanings
        
        # Context-based ambiguity
        if message_lower in ["iyi günler"]:
            # Check conversation state to determine meaning
            if self.context.state == ConversationState.GREETING:
                return False, ["greeting"]
            elif len(self.context.conversation_history) > 2:
                return True, ["goodbye", "greeting"]
        
        return False, []
    
    def resolve_ambiguity(self, message: str, possible_meanings: List[str]) -> str:
        """Resolve ambiguous input based on context"""
        message_lower = message.lower().strip()
        
        # Time-based resolution for "iyi günler"
        current_hour = time.localtime().tm_hour
        if "iyi günler" in message_lower:
            if current_hour < 12:
                return "greeting"  # Morning greeting
            elif current_hour > 18 and len(self.context.conversation_history) > 2:
                return "goodbye"  # Evening goodbye
            elif len(self.context.conversation_history) == 0:
                return "greeting"  # First message
            else:
                return "goodbye"  # Likely goodbye in conversation
        
        # Context-based resolution
        if self.context.state == ConversationState.GREETING:
            if "greeting" in possible_meanings:
                return "greeting"
        elif self.context.state == ConversationState.PRODUCT_SEARCH:
            if "goodbye" in possible_meanings:
                return "goodbye"
        
        # Default to first meaning
        return possible_meanings[0] if possible_meanings else "unclear"
    
    def handle_incomplete_input(self, message: str) -> Tuple[bool, str]:
        """Handle incomplete or unclear inputs"""
        message_lower = message.lower().strip()
        
        # Single word inputs
        if len(message.split()) == 1:
            word = message_lower
            
            # Color only
            colors = ['siyah', 'beyaz', 'kırmızı', 'mavi', 'lacivert', 'yeşil', 'mor', 'pembe', 'ekru']
            if word in colors:
                if self.context.last_products:
                    return True, f"{word.title()} renkte ürünler arasından seçim yapıyorsunuz. Size uygun ürünleri göstereyim."
                else:
                    return True, f"{word.title()} renkte hangi ürün türünü arıyorsunuz? (gecelik, pijama, sabahlık, takım)"
            
            # Product type only
            product_types = ['gecelik', 'pijama', 'sabahlık', 'takım', 'elbise', 'şort']
            if word in product_types:
                return True, f"{word.title()} arıyorsunuz. Hangi renkte olsun?"
            
            # Size only
            sizes = ['xs', 's', 'm', 'l', 'xl', 'xxl']
            if word in sizes:
                return True, f"{word.upper()} beden için hangi ürün türünü arıyorsunuz?"
            
            # Vague responses
            vague_words = ['tamam', 'evet', 'olur', 'iyi', 'güzel']
            if word in vague_words:
                if self.context.last_products:
                    return True, "Hangi ürün hakkında daha fazla bilgi almak istersiniz?"
                else:
                    return True, "Size nasıl yardımcı olabilirim? Hangi ürünü arıyorsunuz?"
        
        # Very short inputs
        if len(message.strip()) < 3:
            return True, "Lütfen daha açık bir şekilde belirtir misiniz? Size nasıl yardımcı olabilirim?"
        
        return False, ""
    
    def get_cached_response(self, query: str) -> Optional[Dict]:
        """Get cached response if available"""
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                logger.info(f"Cache hit for: {query}")
                return cached_item['response']
            else:
                # Remove expired cache
                del self.cache[cache_key]
        return None
    
    def cache_response(self, query: str, response: Dict):
        """Cache response for future use"""
        cache_key = query.lower().strip()
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        
        # Simple cache cleanup (keep last 100 items)
        if len(self.cache) > 100:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
    
    def update_context(self, message: str, intent: str, products: List[Dict] = None):
        """Update conversation context"""
        # Add to history
        self.context.conversation_history.append({
            'message': message,
            'intent': intent,
            'timestamp': time.time(),
            'products_count': len(products) if products else 0
        })
        
        # Keep only last 10 messages
        if len(self.context.conversation_history) > 10:
            self.context.conversation_history = self.context.conversation_history[-10:]
        
        # Update state
        if intent == "greeting":
            self.context.state = ConversationState.GREETING
        elif intent == "product_search":
            self.context.state = ConversationState.PRODUCT_SEARCH
            if products:
                self.context.last_products = products
                self.context.last_query = message
        elif intent in ["goodbye", "thanks"]:
            self.context.state = ConversationState.GOODBYE
        elif intent == "unclear":
            self.context.clarification_attempts += 1
            if self.context.clarification_attempts > 2:
                self.context.state = ConversationState.CLARIFICATION
    
    def generate_contextual_response(self, intent: str, base_response: str) -> str:
        """Generate context-aware response"""
        
        # If user seems confused (multiple unclear attempts) - ONLY for unclear intent
        if intent == "unclear" and self.context.clarification_attempts > 2:
            return ("Anlaşılan biraz karışıklık var. Size şu konularda yardımcı olabilirim:\n\n"
                   "• Ürün arama (örnek: 'hamile pijama arıyorum')\n"
                   "• Fiyat bilgisi (örnek: 'bu ürünün fiyatı nedir?')\n"
                   "• Stok durumu\n"
                   "• Mağaza bilgileri\n\n"
                   "Hangi konuda yardım istiyorsunuz?")
        
        # If user just searched and now greeting again
        if (intent == "greeting" and 
            self.context.state == ConversationState.PRODUCT_SEARCH and 
            self.context.last_products):
            return "Merhaba! Daha önce gösterdiğim ürünler hakkında soru sormak ister misiniz? Yoksa başka bir ürün mü arıyorsunuz?"
        
        # If user says thanks after product search
        if (intent == "thanks" and 
            self.context.state == ConversationState.PRODUCT_SEARCH):
            return "Rica ederim! 😊 Gösterdiğim ürünlerden herhangi biri hakkında daha fazla bilgi almak ister misiniz?"
        
        return base_response
    
    def handle_follow_up_questions(self, message: str) -> Tuple[bool, str]:
        """Handle follow-up questions about previous products with better validation"""
        message_lower = message.lower().strip()
        
        # No previous products = no followup possible
        if not self.context.last_products:
            return False, ""
        
        # Validate that this is actually a followup question
        # Must have either number reference OR specific followup keywords
        import re
        
        # Strong followup patterns that indicate user is asking about previous results
        strong_followup_patterns = [
            r'\d+\s*(numaralı|nolu|no)\s*(ürün|ün)',  # "1 numaralı ürün"
            r'\d+\s*(fiyat|kaç|para)',                # "1 fiyatı"
            r'\d+\s*(stok|var|mevcut)',               # "1 stok"
            r'(bu|şu|o)\s*(ürün|ün)',                # "bu ürün"
            r'(ilk|birinci|ikinci)\s*(ürün|ün)',     # "ilk ürün"
        ]
        
        # Check if message matches strong followup patterns
        has_strong_followup = any(re.search(pattern, message_lower) for pattern in strong_followup_patterns)
        
        # Weak followup patterns (only valid if no product search keywords AND makes sense contextually)
        weak_followup_patterns = ['fiyat', 'stok', 'var mı', 'mevcut', 'kaç']
        has_weak_followup = any(word in message_lower for word in weak_followup_patterns)
        
        # Product search keywords that would override followup
        product_keywords = ['gecelik', 'pijama', 'sabahlık', 'takım', 'hamile', 'dantelli', 'afrika']
        has_product_keywords = any(word in message_lower for word in product_keywords)
        
        # Color-only queries that should NOT be followup (they're new searches)
        color_only_patterns = [
            r'^(siyah|beyaz|kırmızı|mavi|yeşil|mor|pembe|sarı|bordo|vizon|ekru|lacivert)\s*(var\s*mı|mevcut|stok)$',
            r'^(siyah|beyaz|kırmızı|mavi|yeşil|mor|pembe|sarı|bordo|vizon|ekru|lacivert)ı\s*(var\s*mı|mevcut|stok)$'
        ]
        
        # If it's a color-only query, it's NOT a followup
        for pattern in color_only_patterns:
            if re.search(pattern, message_lower.strip()):
                return False, ""
        
        # If has product keywords, it's NOT a followup (it's a new search)
        if has_product_keywords and not has_strong_followup:
            return False, ""
        
        # If no followup patterns at all, it's not a followup
        if not (has_strong_followup or has_weak_followup):
            return False, ""
        
        # Additional validation: Check if the followup makes sense contextually
        # Removed weak followup validation that was blocking color handling
        
        # Product selection by number with validation
        numbers = re.findall(r'\d+', message)
        if numbers and (has_strong_followup or 'numaralı' in message_lower):
            try:
                index = int(numbers[0]) - 1
                if 0 <= index < len(self.context.last_products):
                    product = self.context.last_products[index]
                    
                    # Determine what info user wants
                    if any(word in message_lower for word in ['fiyat', 'kaç', 'para']):
                        response = f"💰 **{product['name']}** fiyatı: **{product['final_price']:.2f} TL**"
                        if product.get('discount', 0) > 0:
                            response += f" 🏷️ **(İndirimli! Eski fiyat: {product['price']:.2f} TL, %{product['discount']} indirim)**"
                    elif any(word in message_lower for word in ['stok', 'var', 'mevcut']):
                        stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                        response = f"📦 **{product['name']}** stok durumu: {stock_status}"
                    else:
                        # Full details
                        response = f"✨ **{product['name']}**\n\n"
                        response += f"🎨 Renk: {product['color']}\n"
                        response += f"💰 Fiyat: **{product['final_price']:.2f} TL**"
                        
                        if product.get('discount', 0) > 0:
                            response += f" 🏷️ **(İndirimli! Eski fiyat: {product['price']:.2f} TL, %{product['discount']} indirim)**"
                        
                        stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                        response += f"\n📦 Stok: {stock_status}"
                    
                    response += f"\n\n🛒 Sipariş için: {self.get_business_info().get('phone', '0555 555 55 55')}"
                    response += f"\n🌐 Web: {self.get_business_info().get('website', 'www.butik.com')}"
                    
                    return True, response
            except (ValueError, IndexError):
                pass
        
        # General questions about all products (only if weak followup and no product keywords)
        if has_weak_followup and not has_product_keywords:
            if any(word in message_lower for word in ['fiyat', 'kaç', 'para']):
                if len(self.context.last_products) == 1:
                    product = self.context.last_products[0]
                    response = f"💰 **{product['name']}** fiyatı: **{product['final_price']:.2f} TL**"
                    if product.get('discount', 0) > 0:
                        response += f" 🏷️ **(İndirimli! %{product['discount']} indirim)**"
                    return True, response
                else:
                    response = "💰 **Fiyat bilgileri:**\n\n"
                    for i, product in enumerate(self.context.last_products[:5], 1):
                        response += f"**{i}.** {product['name'][:50]}{'...' if len(product['name']) > 50 else ''} - **{product['final_price']:.2f} TL**\n"
                    return True, response
            
            elif any(word in message_lower for word in ['stok', 'var mı', 'mevcut', 'beden', 'fiyat', 'ne kadar']):
                # Use unified attribute system (color, size, stock, price)
                if self.context.last_products:
                    is_attribute_query, attribute_response = handle_attribute_query(message, self.context.last_products)
                    if is_attribute_query:
                        return True, attribute_response
                else:
                    # General stock inquiry
                    if len(self.context.last_products) == 1:
                        product = self.context.last_products[0]
                        stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                        return True, f"📦 **{product['name']}** stok durumu: {stock_status}"
                    else:
                        response = "📦 **Stok durumları:**\n\n"
                        for i, product in enumerate(self.context.last_products[:5], 1):
                            stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                            response += f"**{i}.** {product['name'][:50]}{'...' if len(product['name']) > 50 else ''} - {stock_status}\n"
                        return True, response
        
        if any(word in message_lower for word in ['stok', 'var mı', 'mevcut']):
            if len(self.context.last_products) == 1:
                product = self.context.last_products[0]
                stock_status = 'Mevcut' if product.get('stock', 0) > 0 else 'Tükendi'
                return True, f"📦 {product['name']} stok durumu: {stock_status}"
            else:
                response = "📦 Stok durumları:\n\n"
                for i, product in enumerate(self.context.last_products[:5], 1):
                    stock_status = 'Mevcut' if product.get('stock', 0) > 0 else 'Tükendi'
                    response += f"{i}. {product['name'][:40]}... - {stock_status}\n"
                return True, response
        
        return False, ""
    
    def get_business_info(self) -> Dict:
        """Get business information"""
        try:
            with open('data/butik_meta.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'phone': '0212 123 45 67',
                'website': 'www.butik.com',
                'email': 'info@butik.com'
            }
    
    def reset_context(self):
        """Reset conversation context"""
        self.context = ConversationContext(ConversationState.GREETING)
        self.cache.clear()
    
    def get_conversation_stats(self) -> Dict:
        """Get conversation statistics"""
        try:
            state_value = self.context.state.value if hasattr(self.context.state, 'value') else str(self.context.state)
        except:
            state_value = 'unknown'
            
        return {
            'state': state_value,
            'history_length': len(self.context.conversation_history),
            'clarification_attempts': self.context.clarification_attempts,
            'last_products_count': len(self.context.last_products),
            'cache_size': len(self.cache)
        }

    def detect_image_reference(self, message: str) -> Tuple[bool, str]:
        """Detect if user is referring to an image/visual they shared"""
        message_lower = message.lower().strip()
        
        # Check for image reference patterns
        for pattern in self.image_reference_patterns:
            if pattern in message_lower:
                # Check if message is very short and vague (likely image reference)
                if len(message.split()) <= 3:
                    # Additional checks for image reference context
                    image_indicators = [
                        "bu", "şu", "o", "bunun", "şunun", "onun",
                        "yukarıdaki", "gönderdiğim", "attığım"
                    ]
                    
                    # If contains image indicators OR is very short price/stock query
                    if (any(indicator in message_lower for indicator in image_indicators) or
                        any(pattern in message_lower for pattern in ["fiyatı ne", "kaç para", "var mı"])):
                        return True, "image_reference"
        
        # Check for very vague queries that might be image references
        vague_image_queries = [
            "fiyatı nedir", "fiyatı ne", "kaç para", "ne kadar",
            "var mı", "mevcut mu", "stokta mı", "bulunuyor mu",
            "bunu istiyorum", "şunu istiyorum", "onu istiyorum"
        ]
        
        if message_lower in vague_image_queries:
            return True, "image_reference"
        
        return False, ""
    
    def handle_image_reference(self, message: str) -> str:
        """Handle image reference queries"""
        # Return helpful message for image references
        return ("📸 Gönderdiğiniz görselle ilgili yardım için:\n\n"
                "💡 **Lütfen ürünün adını yazın** veya görseldeki ürünü tarif edin\n"
                "📝 **Örnek:** 'Afrika gecelik fiyatı' veya 'siyah dantelli pijama'\n\n"
                "📞 **Hızlı yardım:** 0555 555 55 55\n"
                "💬 **WhatsApp:** wa.me/905555555555")

# Test function
def test_conversation_handler():
    """Test the enhanced conversation handler"""
    handler = EnhancedConversationHandler()
    
    test_scenarios = [
        # Ambiguous inputs
        ("iyi günler", "Should detect greeting vs goodbye ambiguity"),
        ("tamam", "Should handle vague acknowledgment"),
        ("siyah", "Should ask for product type"),
        ("gecelik", "Should ask for color"),
        
        # Follow-up questions
        ("1", "Should select first product from previous search"),
        ("fiyatı nedir", "Should give price info for previous products"),
        ("stok var mı", "Should give stock info"),
        
        # Edge cases
        ("", "Should handle empty input"),
        ("a", "Should handle very short input"),
        ("asdasdasd", "Should handle nonsense input")
    ]
    
    print("🧪 Enhanced Conversation Handler Test")
    print("=" * 50)
    
    for message, description in test_scenarios:
        print(f"\n📝 Test: {description}")
        print(f"👤 Input: '{message}'")
        
        # Test ambiguity detection
        is_ambiguous, meanings = handler.detect_ambiguity(message)
        if is_ambiguous:
            resolved = handler.resolve_ambiguity(message, meanings)
            print(f"🔍 Ambiguous: {meanings} → Resolved: {resolved}")
        
        # Test incomplete input handling
        is_incomplete, response = handler.handle_incomplete_input(message)
        if is_incomplete:
            print(f"⚠️ Incomplete: {response}")
        
        # Test follow-up handling
        is_followup, followup_response = handler.handle_follow_up_questions(message)
        if is_followup:
            print(f"🔄 Follow-up: {followup_response}")

if __name__ == "__main__":
    test_conversation_handler()