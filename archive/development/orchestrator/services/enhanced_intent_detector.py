"""
Enhanced Intent Detector - Multi-stage pattern matching with context awareness
"""

import logging
import re
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Intent türleri"""
    GREETING = "greeting"
    THANKS = "thanks"
    FAREWELL = "farewell"
    ACKNOWLEDGMENT = "acknowledgment"
    NEGATIVE = "negative"
    CLARIFICATION_NEEDED = "clarification_needed"
    BUSINESS_INFO = "business_info"
    PRODUCT_INQUIRY = "product_inquiry"
    NEEDS_LLM = "needs_llm"
    HUMAN_TRANSFER = "human_transfer"

class ConfidenceLevel(Enum):
    """Güven seviyeleri"""
    VERY_HIGH = 0.95
    HIGH = 0.85
    MEDIUM = 0.70
    LOW = 0.55
    VERY_LOW = 0.40

@dataclass
class Entity:
    """Extracted entity"""
    type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int

@dataclass
class IntentResult:
    """Intent detection sonucu"""
    intent: IntentType
    confidence: float
    entities: List[Entity]
    context: Dict[str, Any]
    requires_llm: bool
    function_call: Optional[Dict[str, Any]]
    response: Optional[str]
    method: str
    explanation: str

class EnhancedIntentDetector:
    """Gelişmiş intent detection sistemi"""
    
    def __init__(self):
        self.context_memory = {}  # session_id -> context
        
        # EXACT PATTERNS - En yüksek öncelik
        self.exact_patterns = {
            # Selamlama
            "merhaba": (IntentType.GREETING, "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"),
            "selam": (IntentType.GREETING, "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"),
            "hello": (IntentType.GREETING, "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"),
            "hi": (IntentType.GREETING, "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"),
            
            # Teşekkür
            "teşekkürler": (IntentType.THANKS, "Rica ederim! Başka sorunuz var mı?"),
            "teşekkür": (IntentType.THANKS, "Rica ederim! Başka sorunuz var mı?"),
            "sağol": (IntentType.THANKS, "Rica ederim! Başka sorunuz var mı?"),
            "thanks": (IntentType.THANKS, "Rica ederim! Başka sorunuz var mı?"),
            
            # Vedalaşma
            "hoşça kal": (IntentType.FAREWELL, "Hoşça kalın! Tekrar bekleriz. 😊"),
            "güle güle": (IntentType.FAREWELL, "Hoşça kalın! Tekrar bekleriz. 😊"),
            "görüşürüz": (IntentType.FAREWELL, "Hoşça kalın! Tekrar bekleriz. 😊"),
            "bye": (IntentType.FAREWELL, "Hoşça kalın! Tekrar bekleriz. 😊"),
            
            # Onay/Anlama
            "tamam": (IntentType.ACKNOWLEDGMENT, "Başka bir sorunuz var mı?"),
            "ok": (IntentType.ACKNOWLEDGMENT, "Başka bir sorunuz var mı?"),
            "peki": (IntentType.ACKNOWLEDGMENT, "Başka bir sorunuz var mı?"),
            "anladım": (IntentType.ACKNOWLEDGMENT, "Başka bir sorunuz var mı?"),
            "evet": (IntentType.ACKNOWLEDGMENT, "Başka bir sorunuz var mı?"),
            
            # Red/Olumsuz
            "yok": (IntentType.NEGATIVE, "Teşekkür ederiz! İyi günler dileriz. 😊"),
            "hayır": (IntentType.NEGATIVE, "Başka bir konuda yardımcı olabilirim."),
            "istemiyorum": (IntentType.NEGATIVE, "Başka bir konuda yardımcı olabilirim."),
        }
        
        # BUSINESS INFO PATTERNS
        self.business_patterns = {
            "telefon": {
                "keywords": ["telefon", "phone", "iletişim", "numar", "ara", "tel"],
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "telefon"}}
            },
            "iade": {
                "keywords": ["iade", "return", "geri", "değişim", "değiştir", "iade var", 
                           "iade var mı", "iade yapabilir", "iade edebilir", "geri verebilir",
                           "iade şart", "iade policy", "iade nasıl", "nasıl iade", 
                           "iade süresi", "kaç gün iade"],
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "iade"}}
            },
            "kargo": {
                "keywords": ["kargo", "teslimat", "shipping", "cargo"],
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "kargo"}}
            },
            "site": {
                "keywords": ["site", "web", "website"],
                "function_call": {"name": "getGeneralInfo", "args": {"info_type": "site"}}
            }
        }
        
        # PRODUCT QUERY PATTERNS
        self.product_query_patterns = [
            "fiyat", "kaç para", "ne kadar", "price", "ücret",
            "stok", "var mı", "mevcut", "stock", "kaldı",
            "renk", "color", "renkler", "hangi renk",
            "beden", "size", "bedenleri", "hangi beden",
            "detay", "bilgi", "özellik", "nasıl", "info"
        ]
        
        # PRODUCT NAME PATTERNS
        self.product_names = [
            "gecelik", "geceliği", "geceliğin", "geceliğe",
            "pijama", "pijamayı", "pijamanın", "pijamaya", 
            "elbise", "elbiseyi", "elbisenin", "elbiseye",
            "sabahlık", "sabahlığı", "sabahlığın", "sabahlığa",
            "takım", "takımı", "takımın", "takıma",
            "hamile", "lohusa", "afrika", "dantelli", "siyah", "beyaz",
            "kol", "omuz", "yaka", "düğmeli", "dekolteli", "askılı"
        ]
        
        # NONSENSE PATTERNS - Anlamsız sorgular
        self.nonsense_patterns = [
            "fiyat sorcaktım", "fiyat sroacaktım", "soracaktım", "diyecektim",
            "annen", "baban", "kardeşin", "ablan", "ağabeyin",
            "asdfgh", "qwerty", "123456", "test", "deneme"
        ]
        
        # CONTEXT PATTERNS - Takip soruları
        self.context_patterns = [
            "bunun", "onun", "şunun", "bu ürünün", "o ürünün",
            "daha", "başka", "diğer", "farklı"
        ]
    
    async def detect_intent(self, message: str, session_id: str = None, 
                          context: Dict[str, Any] = None) -> IntentResult:
        """Ana intent detection fonksiyonu"""
        
        if not message or not message.strip():
            return IntentResult(
                intent=IntentType.CLARIFICATION_NEEDED,
                confidence=ConfidenceLevel.VERY_HIGH.value,
                entities=[],
                context={},
                requires_llm=False,
                function_call=None,
                response="Merhaba! Size nasıl yardımcı olabilirim?",
                method="empty_message",
                explanation="Empty or whitespace-only message"
            )
        
        message_clean = message.lower().strip()
        
        # 1. NONSENSE DETECTION - En önce kontrol et
        nonsense_result = self._detect_nonsense(message_clean)
        if nonsense_result:
            return nonsense_result
        
        # 2. EXACT PATTERN MATCHING - Kesin eşleşmeler
        exact_result = self._detect_exact_patterns(message_clean)
        if exact_result:
            return exact_result
        
        # 3. BUSINESS INFO DETECTION
        business_result = self._detect_business_info(message_clean)
        if business_result:
            return business_result
        
        # 4. PRODUCT QUERY DETECTION - En karmaşık kısım
        product_result = await self._detect_product_query(message_clean, session_id, context)
        if product_result:
            return product_result
        
        # 5. CONTEXT-AWARE DETECTION - Takip soruları
        if session_id:
            context_result = self._detect_contextual_query(message_clean, session_id)
            if context_result:
                return context_result
        
        # 6. SHORT MESSAGE HANDLING
        short_result = self._handle_short_messages(message_clean)
        if short_result:
            return short_result
        
        # 7. COMPLEX QUERY - LLM'e gönder
        return IntentResult(
            intent=IntentType.NEEDS_LLM,
            confidence=ConfidenceLevel.MEDIUM.value,
            entities=self._extract_basic_entities(message_clean),
            context=context or {},
            requires_llm=True,
            function_call=None,
            response=None,
            method="needs_llm",
            explanation="Complex query requiring LLM analysis"
        )
    
    def _detect_nonsense(self, message: str) -> Optional[IntentResult]:
        """Anlamsız sorguları tespit et"""
        for nonsense in self.nonsense_patterns:
            if nonsense in message:
                return IntentResult(
                    intent=IntentType.CLARIFICATION_NEEDED,
                    confidence=ConfidenceLevel.VERY_HIGH.value,
                    entities=[],
                    context={},
                    requires_llm=False,
                    function_call=None,
                    response="Anlayamadım. Ürün, fiyat, iade veya iletişim hakkında sorabilirsiniz.",
                    method="nonsense_detection",
                    explanation=f"Detected nonsense pattern: {nonsense}"
                )
        return None
    
    def _detect_exact_patterns(self, message: str) -> Optional[IntentResult]:
        """Kesin pattern eşleşmelerini tespit et"""
        if message in self.exact_patterns:
            intent_type, response = self.exact_patterns[message]
            return IntentResult(
                intent=intent_type,
                confidence=ConfidenceLevel.VERY_HIGH.value,
                entities=[],
                context={},
                requires_llm=False,
                function_call=None,
                response=response,
                method="exact_pattern",
                explanation=f"Exact pattern match: {message}"
            )
        return None
    
    def _detect_business_info(self, message: str) -> Optional[IntentResult]:
        """İşletme bilgi sorgularını tespit et"""
        for info_type, config in self.business_patterns.items():
            # Keyword matching
            if any(keyword in message for keyword in config["keywords"]):
                # Ürün adı da varsa ürün sorgusu olabilir - kontrol et
                has_product = any(product in message for product in self.product_names)
                if not has_product:
                    return IntentResult(
                        intent=IntentType.BUSINESS_INFO,
                        confidence=ConfidenceLevel.HIGH.value,
                        entities=[Entity("info_type", info_type, 0.9, 0, len(message))],
                        context={"info_type": info_type},
                        requires_llm=False,
                        function_call=config["function_call"],
                        response=None,
                        method="business_pattern",
                        explanation=f"Business info query detected: {info_type}"
                    )
        return None
    
    async def _detect_product_query(self, message: str, session_id: str = None, 
                                  context: Dict[str, Any] = None) -> Optional[IntentResult]:
        """Ürün sorgularını tespit et - En karmaşık kısım"""
        
        has_product_query = any(pattern in message for pattern in self.product_query_patterns)
        has_product_name = any(product in message for product in self.product_names)
        
        # Extract entities
        entities = self._extract_product_entities(message)
        
        # Sadece ürün sorgu kelimesi varsa ve ürün adı yoksa belirsiz
        if has_product_query and not has_product_name:
            words = message.split()
            if len(words) <= 1:
                query_word = words[0] if words else "bilgi"
                return IntentResult(
                    intent=IntentType.CLARIFICATION_NEEDED,
                    confidence=ConfidenceLevel.HIGH.value,
                    entities=entities,
                    context={"incomplete_query": True, "query_type": query_word},
                    requires_llm=False,
                    function_call=None,
                    response=f"Hangi ürünün {query_word} bilgisini öğrenmek istiyorsunuz?",
                    method="incomplete_query",
                    explanation=f"Incomplete product query: {query_word}"
                )
        
        # Hem ürün sorgusu hem ürün adı varsa ürün sorgusu
        if has_product_query and has_product_name:
            return IntentResult(
                intent=IntentType.PRODUCT_INQUIRY,
                confidence=ConfidenceLevel.HIGH.value,
                entities=entities,
                context={"has_product_query": True, "has_product_name": True},
                requires_llm=False,
                function_call=None,
                response=None,
                method="product_pattern",
                explanation="Product query with both query type and product name"
            )
        
        # Sadece ürün adı varsa da ürün sorgusu
        if has_product_name:
            return IntentResult(
                intent=IntentType.PRODUCT_INQUIRY,
                confidence=ConfidenceLevel.MEDIUM.value,
                entities=entities,
                context={"has_product_name": True},
                requires_llm=False,
                function_call=None,
                response=None,
                method="product_name_only",
                explanation="Product query with product name only"
            )
        
        return None
    
    def _detect_contextual_query(self, message: str, session_id: str) -> Optional[IntentResult]:
        """Context-aware sorgu tespiti"""
        has_context_pattern = any(pattern in message for pattern in self.context_patterns)
        has_product_query = any(pattern in message for pattern in self.product_query_patterns)
        
        if has_context_pattern or has_product_query:
            # Session context'ini kontrol et
            session_context = self.context_memory.get(session_id, {})
            last_product = session_context.get("last_product")
            
            if last_product:
                return IntentResult(
                    intent=IntentType.PRODUCT_INQUIRY,
                    confidence=ConfidenceLevel.MEDIUM.value,
                    entities=[Entity("product", last_product, 0.8, 0, len(message))],
                    context={"contextual_query": True, "referenced_product": last_product},
                    requires_llm=False,
                    function_call=None,
                    response=None,
                    method="contextual_query",
                    explanation=f"Contextual query referencing: {last_product}"
                )
        
        return None
    
    def _handle_short_messages(self, message: str) -> Optional[IntentResult]:
        """Kısa mesajları işle"""
        words = message.split()
        if len(words) <= 2:
            # Tek kelime ürün sorguları
            if len(words) == 1 and words[0] in self.product_query_patterns:
                return IntentResult(
                    intent=IntentType.CLARIFICATION_NEEDED,
                    confidence=ConfidenceLevel.HIGH.value,
                    entities=[Entity("query_type", words[0], 0.9, 0, len(words[0]))],
                    context={"incomplete_query": True, "query_type": words[0]},
                    requires_llm=False,
                    function_call=None,
                    response=f"Hangi ürünün {words[0]} bilgisini öğrenmek istiyorsunuz?",
                    method="incomplete_query",
                    explanation=f"Single word query: {words[0]}"
                )
            
            # Diğer kısa mesajlar
            return IntentResult(
                intent=IntentType.CLARIFICATION_NEEDED,
                confidence=ConfidenceLevel.MEDIUM.value,
                entities=[],
                context={"short_message": True},
                requires_llm=False,
                function_call=None,
                response="Tam olarak ne hakkında bilgi almak istiyorsunuz? Ürün, fiyat, iade veya iletişim konularında yardımcı olabilirim.",
                method="short_message",
                explanation=f"Short message with {len(words)} words"
            )
        
        return None
    
    def _extract_basic_entities(self, message: str) -> List[Entity]:
        """Temel entity extraction"""
        entities = []
        
        # Product names
        for product in self.product_names:
            if product in message:
                start_pos = message.find(product)
                entities.append(Entity(
                    type="product",
                    value=product,
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=start_pos + len(product)
                ))
        
        # Query types
        for query_type in self.product_query_patterns:
            if query_type in message:
                start_pos = message.find(query_type)
                entities.append(Entity(
                    type="query_type",
                    value=query_type,
                    confidence=0.9,
                    start_pos=start_pos,
                    end_pos=start_pos + len(query_type)
                ))
        
        return entities
    
    def _extract_product_entities(self, message: str) -> List[Entity]:
        """Ürün-specific entity extraction"""
        entities = []
        
        # Product names (garment types)
        garment_types = ["gecelik", "geceliği", "pijama", "pijamayı", "elbise", "elbiseyi", 
                        "sabahlık", "sabahlığı", "takım", "takımı"]
        
        for garment in garment_types:
            if garment in message:
                start_pos = message.find(garment)
                entities.append(Entity(
                    type="product",
                    value=garment,
                    confidence=0.9,
                    start_pos=start_pos,
                    end_pos=start_pos + len(garment)
                ))
        
        # Target groups
        target_groups = ["hamile", "lohusa", "büyük beden"]
        
        for target in target_groups:
            if target in message:
                start_pos = message.find(target)
                entities.append(Entity(
                    type="target_group",
                    value=target,
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=start_pos + len(target)
                ))
        
        # Colors
        colors = ["siyah", "beyaz", "kırmızı", "mavi", "yeşil", "sarı", "pembe", "mor", 
                 "lacivert", "bordo", "bej", "ekru", "gri", "krem", "turuncu"]
        
        for color in colors:
            if color in message:
                start_pos = message.find(color)
                entities.append(Entity(
                    type="color",
                    value=color,
                    confidence=0.9,
                    start_pos=start_pos,
                    end_pos=start_pos + len(color)
                ))
        
        # Product features
        features = ["dantelli", "düğmeli", "dekolteli", "askılı", "kol", "omuz", "yaka"]
        
        for feature in features:
            if feature in message:
                start_pos = message.find(feature)
                entities.append(Entity(
                    type="feature",
                    value=feature,
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=start_pos + len(feature)
                ))
        
        # Query types
        for query_type in self.product_query_patterns:
            if query_type in message:
                start_pos = message.find(query_type)
                entities.append(Entity(
                    type="query_type",
                    value=query_type,
                    confidence=0.9,
                    start_pos=start_pos,
                    end_pos=start_pos + len(query_type)
                ))
        
        return entities
    
    def update_context(self, session_id: str, context_data: Dict[str, Any]):
        """Session context'ini güncelle"""
        if session_id not in self.context_memory:
            self.context_memory[session_id] = {}
        
        self.context_memory[session_id].update(context_data)
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Session context'ini al"""
        return self.context_memory.get(session_id, {})
    
    def clear_context(self, session_id: str):
        """Session context'ini temizle"""
        if session_id in self.context_memory:
            del self.context_memory[session_id]
    
    def calculate_confidence(self, matches: List[Tuple[str, float]]) -> float:
        """Confidence hesaplama"""
        if not matches:
            return 0.0
        
        # Weighted average of matches
        total_weight = sum(weight for _, weight in matches)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(score * weight for score, weight in matches)
        return min(weighted_sum / total_weight, 1.0)

# Global instance
enhanced_intent_detector = EnhancedIntentDetector()