#!/usr/bin/env python3
"""
Contextual Intent Detector - Context-aware intent detection with conversation history
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

try:
    from .conversation_context_manager import ConversationContext, ContextType, EntityType
    from .product_feature_extractor import ProductFeatureExtractor
    from .turkish_language_rules import TurkishLanguageRules
except ImportError:
    from conversation_context_manager import ConversationContext, ContextType, EntityType
    from product_feature_extractor import ProductFeatureExtractor
    from turkish_language_rules import TurkishLanguageRules

logger = logging.getLogger(__name__)

class Intent(Enum):
    """Intent türleri"""
    PRODUCT_SEARCH = "product_search"
    PRODUCT_INFO = "product_info"
    PRICE_INQUIRY = "price_inquiry"
    AVAILABILITY_CHECK = "availability_check"
    FEATURE_INQUIRY = "feature_inquiry"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    GENERAL_INFO = "general_info"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    CLARIFICATION = "clarification"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    UNKNOWN = "unknown"

class IntentConfidence(Enum):
    """Intent confidence seviyeleri"""
    VERY_HIGH = "very_high"  # 0.9+
    HIGH = "high"           # 0.7-0.89
    MEDIUM = "medium"       # 0.5-0.69
    LOW = "low"            # 0.3-0.49
    VERY_LOW = "very_low"  # <0.3

@dataclass
class DetectedIntent:
    """Tespit edilen intent"""
    intent: Intent
    confidence: float
    confidence_level: IntentConfidence
    context_used: bool
    supporting_patterns: List[str]
    entities_found: List[str]
    disambiguation_needed: bool
    alternative_intents: List[Tuple[Intent, float]]
    explanation: str

@dataclass
class ResolvedIntent:
    """Çözümlenmiş intent"""
    original_intent: DetectedIntent
    resolved_intent: Intent
    resolution_confidence: float
    context_factors: List[str]
    resolution_explanation: str

class ContextualIntentDetector:
    """Context-aware intent detection engine"""
    
    def __init__(self):
        self.feature_extractor = ProductFeatureExtractor()
        self.turkish_rules = TurkishLanguageRules()
        
        # Intent patterns with Turkish support
        self.intent_patterns = {
            Intent.PRODUCT_SEARCH: [
                r'\b(ara|arıyorum|bul|göster|show|search)\b',
                r'\b(istiyorum|want|need|lazım)\b',
                r'\b(var mı|mevcut|available)\b.*\b(ürün|product)\b',
                r'\b(hangi|which|ne|what).*\b(ürün|product|model)\b'
            ],
            Intent.PRODUCT_INFO: [
                r'\b(hakkında|about|bilgi|info|information)\b',
                r'\b(nasıl|how|ne|what).*\b(ürün|product)\b',
                r'\b(özellik|feature|specification|spec)\b',
                r'\b(detay|detail|açıklama|description)\b'
            ],
            Intent.PRICE_INQUIRY: [
                r'\b(fiyat|price|kaç para|ne kadar|cost)\b',
                r'\b(ücret|fee|tutar|amount)\b',
                r'\b(para|money|tl|lira|₺)\b',
                r'\b(ucuz|cheap|pahalı|expensive)\b'
            ],
            Intent.AVAILABILITY_CHECK: [
                r'\b(var mı|available|mevcut|stok|stock)\b',
                r'\b(bulabilir|can find|temin|supply)\b',
                r'\b(sipariş|order|satın|buy|purchase)\b'
            ],
            Intent.FEATURE_INQUIRY: [
                r'\b(özellik|feature|specification)\b',
                r'\b(malzeme|material|kumaş|fabric)\b',
                r'\b(renk|color|beden|size)\b',
                r'\b(nasıl|how).*\b(yapılmış|made)\b'
            ],
            Intent.COMPARISON: [
                r'\b(karşılaştır|compare|fark|difference)\b',
                r'\b(hangisi|which|better|daha iyi)\b',
                r'\b(arasında|between|versus|vs)\b',
                r'\b(benzer|similar|aynı|same)\b'
            ],
            Intent.RECOMMENDATION: [
                r'\b(öner|recommend|suggest|tavsiye)\b',
                r'\b(en iyi|best|ideal|perfect)\b',
                r'\b(uygun|suitable|appropriate)\b',
                r'\b(seçenek|option|alternatif|alternative)\b'
            ],
            Intent.GENERAL_INFO: [
                r'\b(kargo|shipping|teslimat|delivery)\b',
                r'\b(iade|return|değişim|exchange)\b',
                r'\b(telefon|phone|iletişim|contact)\b',
                r'\b(adres|address|konum|location)\b',
                r'\b(çalışma saati|working hour|açık|open)\b'
            ],
            Intent.GREETING: [
                r'\b(merhaba|hello|hi|selam|hey)\b',
                r'\b(iyi günler|good day|günaydın|good morning)\b',
                r'\b(nasılsın|how are you|naber)\b'
            ],
            Intent.GOODBYE: [
                r'\b(hoşça kal|goodbye|bye|görüşürüz)\b',
                r'\b(teşekkür|thank|thanks|sağol)\b',
                r'\b(iyi günler|good day|iyi akşamlar)\b'
            ],
            Intent.CLARIFICATION: [
                r'\b(anlamadım|don\'t understand|ne demek)\b',
                r'\b(tekrar|again|repeat|bir daha)\b',
                r'\b(açıkla|explain|nasıl yani)\b'
            ],
            Intent.COMPLAINT: [
                r'\b(şikayet|complaint|problem|sorun)\b',
                r'\b(memnun değil|not satisfied|kötü|bad)\b',
                r'\b(hata|error|yanlış|wrong)\b'
            ],
            Intent.COMPLIMENT: [
                r'\b(teşekkür|thank|thanks|sağol)\b',
                r'\b(mükemmel|perfect|harika|great)\b',
                r'\b(beğendim|like|güzel|nice)\b'
            ]
        }
        
        # Context-based intent modifiers
        self.context_modifiers = {
            ContextType.PRODUCT_INQUIRY: {
                Intent.PRODUCT_SEARCH: 1.2,
                Intent.PRODUCT_INFO: 1.1,
                Intent.PRICE_INQUIRY: 1.0,
                Intent.FEATURE_INQUIRY: 1.1
            },
            ContextType.PRODUCT_COMPARISON: {
                Intent.COMPARISON: 1.3,
                Intent.RECOMMENDATION: 1.1,
                Intent.PRODUCT_INFO: 1.0
            },
            ContextType.GENERAL_INFO: {
                Intent.GENERAL_INFO: 1.2,
                Intent.AVAILABILITY_CHECK: 1.0
            },
            ContextType.FOLLOW_UP: {
                Intent.PRICE_INQUIRY: 1.2,
                Intent.FEATURE_INQUIRY: 1.2,
                Intent.AVAILABILITY_CHECK: 1.1
            }
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            IntentConfidence.VERY_HIGH: 0.9,
            IntentConfidence.HIGH: 0.7,
            IntentConfidence.MEDIUM: 0.5,
            IntentConfidence.LOW: 0.3,
            IntentConfidence.VERY_LOW: 0.0
        }
    
    def detect_intent(self, query: str, context: ConversationContext) -> DetectedIntent:
        """
        Context-aware intent detection
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            DetectedIntent: Detected intent with confidence
        """
        try:
            # Normalize query
            normalized_query = self.turkish_rules.normalize_for_search(query)
            
            # Calculate base intent scores
            intent_scores = self._calculate_base_intent_scores(normalized_query)
            
            # Apply context modifiers
            context_modified_scores = self._apply_context_modifiers(intent_scores, context)
            
            # Find best intent
            if context_modified_scores:
                best_intent, best_score = max(context_modified_scores.items(), key=lambda x: x[1])
            else:
                best_intent, best_score = Intent.UNKNOWN, 0.1
            
            # Get alternative intents
            alternative_intents = sorted(
                [(intent, score) for intent, score in context_modified_scores.items() 
                 if intent != best_intent and score > 0.3],
                key=lambda x: x[1], reverse=True
            )[:3]
            
            # Check if disambiguation is needed
            disambiguation_needed = (
                len(alternative_intents) > 0 and 
                alternative_intents[0][1] > best_score * 0.8
            )
            
            # Extract supporting patterns and entities
            supporting_patterns = self._find_supporting_patterns(normalized_query, best_intent)
            entities_found = self._extract_intent_entities(query, best_intent)
            
            # Determine confidence level
            confidence_level = self._get_confidence_level(best_score)
            
            # Check if context was used
            context_used = self._was_context_used(intent_scores, context_modified_scores)
            
            # Generate explanation
            explanation = self._generate_intent_explanation(
                best_intent, best_score, context_used, supporting_patterns
            )
            
            return DetectedIntent(
                intent=best_intent,
                confidence=best_score,
                confidence_level=confidence_level,
                context_used=context_used,
                supporting_patterns=supporting_patterns,
                entities_found=entities_found,
                disambiguation_needed=disambiguation_needed,
                alternative_intents=alternative_intents,
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"Intent detection error: {str(e)}")
            return self._create_fallback_intent(query)
    
    def resolve_ambiguity(self, ambiguous_intent: DetectedIntent, 
                         context: ConversationContext) -> ResolvedIntent:
        """
        Belirsiz intent'i context kullanarak çöz
        
        Args:
            ambiguous_intent: Belirsiz intent
            context: Conversation context
            
        Returns:
            ResolvedIntent: Çözümlenmiş intent
        """
        try:
            context_factors = []
            
            # Use conversation history
            if context.conversation_history:
                recent_intents = self._extract_recent_intents(context)
                if recent_intents:
                    # Favor intents similar to recent ones
                    for intent, score in ambiguous_intent.alternative_intents:
                        if intent in recent_intents:
                            context_factors.append(f"Recent intent pattern: {intent.value}")
                            return ResolvedIntent(
                                original_intent=ambiguous_intent,
                                resolved_intent=intent,
                                resolution_confidence=min(score * 1.2, 1.0),
                                context_factors=context_factors,
                                resolution_explanation=f"Resolved using recent intent pattern"
                            )
            
            # Use current context type
            if context.context_stack:
                current_context_type = context.context_stack[-1]
                context_factors.append(f"Current context: {current_context_type.value}")
                
                # Find best intent for current context
                for intent, score in ambiguous_intent.alternative_intents:
                    if intent in self.context_modifiers.get(current_context_type, {}):
                        modifier = self.context_modifiers[current_context_type][intent]
                        if modifier > 1.0:  # Positive modifier
                            return ResolvedIntent(
                                original_intent=ambiguous_intent,
                                resolved_intent=intent,
                                resolution_confidence=min(score * modifier, 1.0),
                                context_factors=context_factors,
                                resolution_explanation=f"Resolved using context type {current_context_type.value}"
                            )
            
            # Use discussed products
            if context.discussed_products:
                context_factors.append("Product discussion context")
                # Favor product-related intents
                product_intents = [Intent.PRODUCT_INFO, Intent.PRICE_INQUIRY, Intent.FEATURE_INQUIRY]
                for intent, score in ambiguous_intent.alternative_intents:
                    if intent in product_intents:
                        return ResolvedIntent(
                            original_intent=ambiguous_intent,
                            resolved_intent=intent,
                            resolution_confidence=min(score * 1.1, 1.0),
                            context_factors=context_factors,
                            resolution_explanation="Resolved using product discussion context"
                        )
            
            # Fallback: return original intent
            return ResolvedIntent(
                original_intent=ambiguous_intent,
                resolved_intent=ambiguous_intent.intent,
                resolution_confidence=ambiguous_intent.confidence,
                context_factors=context_factors,
                resolution_explanation="Could not resolve ambiguity, using original intent"
            )
            
        except Exception as e:
            logger.error(f"Intent resolution error: {str(e)}")
            return ResolvedIntent(
                original_intent=ambiguous_intent,
                resolved_intent=ambiguous_intent.intent,
                resolution_confidence=ambiguous_intent.confidence,
                context_factors=[],
                resolution_explanation=f"Resolution failed: {str(e)}"
            )
    
    def detect_followup(self, query: str, context: ConversationContext) -> bool:
        """Follow-up soru tespiti"""
        try:
            # Short queries are often follow-ups
            if len(query.split()) <= 3 and context.conversation_history:
                return True
            
            # Check for follow-up patterns
            followup_patterns = [
                r'\b(fiyatı|price)\b',
                r'\b(özellikleri|features)\b',
                r'\b(var mı|available)\b',
                r'\b(nasıl|how)\b',
                r'\b(ne|what)\b'
            ]
            
            query_lower = query.lower()
            for pattern in followup_patterns:
                if re.search(pattern, query_lower):
                    return True
            
            # Check for implicit references
            implicit_patterns = [r'\b(bu|this|o|that|bunun|onun)\b']
            for pattern in implicit_patterns:
                if re.search(pattern, query_lower):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Follow-up detection error: {str(e)}")
            return False
    
    def _calculate_base_intent_scores(self, query: str) -> Dict[Intent, float]:
        """Base intent skorlarını hesapla"""
        scores = defaultdict(float)
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    # Score based on pattern strength and frequency
                    pattern_score = len(matches) * 0.3 + 0.7
                    scores[intent] = max(scores[intent], pattern_score)
        
        # Normalize scores
        max_score = max(scores.values()) if scores else 1.0
        if max_score > 1.0:
            scores = {intent: score / max_score for intent, score in scores.items()}
        
        return dict(scores)
    
    def _apply_context_modifiers(self, base_scores: Dict[Intent, float], 
                               context: ConversationContext) -> Dict[Intent, float]:
        """Context modifier'larını uygula"""
        modified_scores = base_scores.copy()
        
        # Apply context type modifiers
        if context.context_stack:
            current_context = context.context_stack[-1]
            if current_context in self.context_modifiers:
                modifiers = self.context_modifiers[current_context]
                for intent, modifier in modifiers.items():
                    if intent in modified_scores:
                        modified_scores[intent] *= modifier
        
        # Boost intents based on recent conversation
        if context.conversation_history:
            recent_entities = self._get_recent_entity_types(context)
            
            # If products were discussed, boost product-related intents
            if EntityType.PRODUCT in recent_entities:
                product_intents = [Intent.PRODUCT_INFO, Intent.PRICE_INQUIRY, Intent.FEATURE_INQUIRY]
                for intent in product_intents:
                    if intent in modified_scores:
                        modified_scores[intent] *= 1.1
            
            # If prices were mentioned, boost price-related intents
            if EntityType.PRICE in recent_entities:
                if Intent.PRICE_INQUIRY in modified_scores:
                    modified_scores[Intent.PRICE_INQUIRY] *= 1.2
        
        # Ensure scores don't exceed 1.0
        modified_scores = {intent: min(score, 1.0) for intent, score in modified_scores.items()}
        
        return modified_scores
    
    def _find_supporting_patterns(self, query: str, intent: Intent) -> List[str]:
        """Supporting pattern'leri bul"""
        supporting = []
        
        if intent in self.intent_patterns:
            for pattern in self.intent_patterns[intent]:
                if re.search(pattern, query.lower()):
                    supporting.append(pattern)
        
        return supporting
    
    def _extract_intent_entities(self, query: str, intent: Intent) -> List[str]:
        """Intent ile ilgili entity'leri çıkar"""
        entities = []
        
        # Extract features for product-related intents
        if intent in [Intent.PRODUCT_SEARCH, Intent.PRODUCT_INFO, Intent.FEATURE_INQUIRY]:
            features = self.feature_extractor.extract_features(query)
            entities.extend([f.value for f in features])
        
        # Extract price mentions for price intents
        if intent == Intent.PRICE_INQUIRY:
            price_patterns = [r'(\d+)\s*(tl|lira|₺)', r'(ucuz|pahalı|cheap|expensive)']
            for pattern in price_patterns:
                matches = re.findall(pattern, query.lower())
                entities.extend([match[0] if isinstance(match, tuple) else match for match in matches])
        
        return entities
    
    def _get_confidence_level(self, confidence: float) -> IntentConfidence:
        """Confidence level belirle"""
        if confidence >= self.confidence_thresholds[IntentConfidence.VERY_HIGH]:
            return IntentConfidence.VERY_HIGH
        elif confidence >= self.confidence_thresholds[IntentConfidence.HIGH]:
            return IntentConfidence.HIGH
        elif confidence >= self.confidence_thresholds[IntentConfidence.MEDIUM]:
            return IntentConfidence.MEDIUM
        elif confidence >= self.confidence_thresholds[IntentConfidence.LOW]:
            return IntentConfidence.LOW
        else:
            return IntentConfidence.VERY_LOW
    
    def _was_context_used(self, base_scores: Dict[Intent, float], 
                         modified_scores: Dict[Intent, float]) -> bool:
        """Context kullanıldı mı?"""
        for intent in base_scores:
            if intent in modified_scores:
                if abs(modified_scores[intent] - base_scores[intent]) > 0.05:
                    return True
        return False
    
    def _generate_intent_explanation(self, intent: Intent, confidence: float, 
                                   context_used: bool, patterns: List[str]) -> str:
        """Intent açıklaması oluştur"""
        explanation = f"Detected {intent.value} with {confidence:.0%} confidence"
        
        if patterns:
            explanation += f" based on patterns: {', '.join(patterns[:2])}"
        
        if context_used:
            explanation += " (context enhanced)"
        
        return explanation
    
    def _extract_recent_intents(self, context: ConversationContext) -> List[Intent]:
        """Son intent'leri çıkar"""
        # This would extract intents from conversation history
        # For now, return empty list as we don't store intents in history
        return []
    
    def _get_recent_entity_types(self, context: ConversationContext) -> Set[EntityType]:
        """Son entity türlerini getir"""
        entity_types = set()
        
        for entity in context.active_entities.values():
            entity_types.add(entity.entity_type)
        
        return entity_types
    
    def _create_fallback_intent(self, query: str) -> DetectedIntent:
        """Fallback intent"""
        return DetectedIntent(
            intent=Intent.UNKNOWN,
            confidence=0.1,
            confidence_level=IntentConfidence.VERY_LOW,
            context_used=False,
            supporting_patterns=[],
            entities_found=[],
            disambiguation_needed=False,
            alternative_intents=[],
            explanation="Fallback intent due to detection error"
        )
    
    def get_detector_stats(self) -> Dict[str, Any]:
        """Detector istatistikleri"""
        return {
            'supported_intents': [intent.value for intent in Intent],
            'total_patterns': sum(len(patterns) for patterns in self.intent_patterns.values()),
            'context_modifiers': len(self.context_modifiers),
            'confidence_levels': [level.value for level in IntentConfidence]
        }

# Test fonksiyonu
def test_contextual_intent_detector():
    """Contextual intent detector test"""
    
    # Setup
    from conversation_context_manager import ConversationContext, ContextEntity, ContextType, EntityType
    from datetime import datetime
    
    detector = ContextualIntentDetector()
    
    # Create test context
    context = ConversationContext(
        session_id="test_session_intent",
        current_topic="gecelik",
        discussed_products=[
            ContextEntity(
                entity_id="product_1",
                entity_type=EntityType.PRODUCT,
                value={"id": 1, "name": "Siyah Gecelik"},
                confidence=0.9,
                mentioned_at=datetime.now(),
                context_type=ContextType.PRODUCT_INQUIRY
            )
        ],
        user_preferences={},
        conversation_history=[],
        last_activity=datetime.now(),
        context_confidence=0.8,
        active_entities={},
        context_stack=[ContextType.PRODUCT_INQUIRY]
    )
    
    print("🎯 Contextual Intent Detector Test:")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Siyah gecelik arıyorum",           # PRODUCT_SEARCH
        "Fiyatı nedir?",                    # PRICE_INQUIRY (follow-up)
        "Bu ürün hakkında bilgi ver",       # PRODUCT_INFO
        "Hangi renklerde var?",             # FEATURE_INQUIRY
        "Kargo ücreti ne kadar?",           # GENERAL_INFO
        "Teşekkür ederim",                  # COMPLIMENT
        "Anlamadım",                        # CLARIFICATION
        "Belirsiz sorgu"                    # UNKNOWN
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        detected = detector.detect_intent(query, context)
        
        print(f"  🎯 Intent: {detected.intent.value}")
        print(f"  📊 Confidence: {detected.confidence:.2f} ({detected.confidence_level.value})")
        print(f"  🔄 Context used: {detected.context_used}")
        print(f"  📝 Explanation: {detected.explanation}")
        
        if detected.supporting_patterns:
            print(f"  🔍 Patterns: {', '.join(detected.supporting_patterns)}")
        
        if detected.entities_found:
            print(f"  🏷️ Entities: {', '.join(detected.entities_found)}")
        
        if detected.disambiguation_needed:
            print(f"  ❓ Disambiguation needed")
            for alt_intent, alt_score in detected.alternative_intents[:2]:
                print(f"    • {alt_intent.value}: {alt_score:.2f}")
        
        # Test follow-up detection
        is_followup = detector.detect_followup(query, context)
        print(f"  🔄 Is follow-up: {is_followup}")
        
        # Test ambiguity resolution if needed
        if detected.disambiguation_needed:
            resolved = detector.resolve_ambiguity(detected, context)
            print(f"  ✅ Resolved to: {resolved.resolved_intent.value} ({resolved.resolution_confidence:.2f})")
    
    # Stats
    stats = detector.get_detector_stats()
    print(f"\n📊 Detector Stats:")
    print(f"  Supported intents: {len(stats['supported_intents'])}")
    print(f"  Total patterns: {stats['total_patterns']}")
    print(f"  Context modifiers: {stats['context_modifiers']}")

if __name__ == "__main__":
    test_contextual_intent_detector()