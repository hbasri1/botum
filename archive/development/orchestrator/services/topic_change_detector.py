#!/usr/bin/env python3
"""
Topic Change Detector - Advanced topic transition detection with graceful context handover
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

try:
    from .conversation_context_manager import ConversationContext, ContextType, EntityType, ContextEntity
    from .contextual_intent_detector import Intent, ContextualIntentDetector
    from .product_feature_extractor import ProductFeatureExtractor
    from .turkish_language_rules import TurkishLanguageRules
except ImportError:
    from conversation_context_manager import ConversationContext, ContextType, EntityType, ContextEntity
    from contextual_intent_detector import Intent, ContextualIntentDetector
    from product_feature_extractor import ProductFeatureExtractor
    from turkish_language_rules import TurkishLanguageRules

logger = logging.getLogger(__name__)

class TopicChangeType(Enum):
    """Topic değişim türleri"""
    HARD_SWITCH = "hard_switch"        # Tamamen farklı konu
    SOFT_TRANSITION = "soft_transition" # İlgili konuya geçiş
    REFINEMENT = "refinement"          # Aynı konuda detaylandırma
    RETURN = "return"                  # Önceki konuya dönüş
    EXPANSION = "expansion"            # Konu genişletme
    NO_CHANGE = "no_change"           # Değişim yok

class TopicTransitionStrategy(Enum):
    """Topic geçiş stratejileri"""
    PRESERVE_CONTEXT = "preserve_context"
    PARTIAL_RESET = "partial_reset"
    FULL_RESET = "full_reset"
    MERGE_CONTEXTS = "merge_contexts"
    STACK_CONTEXT = "stack_context"

@dataclass
class TopicChangeResult:
    """Topic değişim sonucu"""
    change_detected: bool
    change_type: TopicChangeType
    confidence: float
    old_topic: Optional[str]
    new_topic: Optional[str]
    transition_strategy: TopicTransitionStrategy
    context_preservation: Dict[str, Any]
    explanation: str
    related_entities: List[str]

@dataclass
class TopicContext:
    """Topic context bilgisi"""
    topic_name: str
    context_type: ContextType
    entities: List[ContextEntity]
    confidence: float
    first_mentioned: datetime
    last_mentioned: datetime
    mention_count: int

class TopicChangeDetector:
    """Advanced topic change detection and context management"""
    
    def __init__(self):
        self.feature_extractor = ProductFeatureExtractor()
        self.turkish_rules = TurkishLanguageRules()
        self.intent_detector = ContextualIntentDetector()
        
        # Topic change indicators
        self.hard_switch_indicators = [
            r'\b(şimdi|now|artık|bunun yerine|instead)\b',
            r'\b(başka|other|farklı|different|yeni|new)\b',
            r'\b(değiştir|change|geç|switch)\b',
            r'\b(bırak|leave|unut|forget)\b'
        ]
        
        self.soft_transition_indicators = [
            r'\b(ayrıca|also|additionally|ek olarak)\b',
            r'\b(benzer|similar|aynı|same|like)\b',
            r'\b(ilgili|related|about|hakkında)\b',
            r'\b(daha|more|plus|ve|and)\b'
        ]
        
        self.return_indicators = [
            r'\b(geri|back|tekrar|again|önce|before)\b',
            r'\b(ilk|first|başta|initially)\b',
            r'\b(o|that|önceki|previous)\b'
        ]
        
        # Topic similarity thresholds
        self.similarity_thresholds = {
            'hard_switch': 0.2,
            'soft_transition': 0.4,
            'refinement': 0.7,
            'no_change': 0.8
        }
        
        # Context preservation rules
        self.preservation_rules = {
            TopicChangeType.HARD_SWITCH: {
                'preserve_user_preferences': True,
                'preserve_session_info': True,
                'preserve_recent_products': False,
                'preserve_context_stack': False
            },
            TopicChangeType.SOFT_TRANSITION: {
                'preserve_user_preferences': True,
                'preserve_session_info': True,
                'preserve_recent_products': True,
                'preserve_context_stack': True
            },
            TopicChangeType.REFINEMENT: {
                'preserve_user_preferences': True,
                'preserve_session_info': True,
                'preserve_recent_products': True,
                'preserve_context_stack': True
            },
            TopicChangeType.RETURN: {
                'preserve_user_preferences': True,
                'preserve_session_info': True,
                'preserve_recent_products': True,
                'preserve_context_stack': True
            }
        }
    
    def detect_topic_change(self, query: str, context: ConversationContext) -> TopicChangeResult:
        """
        Topic değişimini tespit et
        
        Args:
            query: Kullanıcı sorgusu
            context: Mevcut conversation context
            
        Returns:
            TopicChangeResult: Tespit sonucu
        """
        try:
            # Extract current and new topics
            current_topic = self._extract_current_topic(context)
            new_topic = self._extract_topic_from_query(query)
            
            # Calculate topic similarity
            topic_similarity = self._calculate_topic_similarity(current_topic, new_topic)
            
            # Detect change type
            change_type = self._classify_change_type(query, topic_similarity, context)
            
            # Determine if change detected
            change_detected = change_type != TopicChangeType.NO_CHANGE
            
            # Calculate confidence
            confidence = self._calculate_change_confidence(query, change_type, topic_similarity, context)
            
            # Determine transition strategy
            transition_strategy = self._determine_transition_strategy(change_type, context)
            
            # Prepare context preservation
            context_preservation = self._prepare_context_preservation(change_type, context)
            
            # Find related entities
            related_entities = self._find_related_entities(current_topic, new_topic, context)
            
            # Generate explanation
            explanation = self._generate_change_explanation(
                change_type, current_topic, new_topic, confidence
            )
            
            result = TopicChangeResult(
                change_detected=change_detected,
                change_type=change_type,
                confidence=confidence,
                old_topic=current_topic,
                new_topic=new_topic,
                transition_strategy=transition_strategy,
                context_preservation=context_preservation,
                explanation=explanation,
                related_entities=related_entities
            )
            
            if change_detected:
                logger.info(f"Topic change detected: {current_topic} -> {new_topic} ({change_type.value})")
            
            return result
            
        except Exception as e:
            logger.error(f"Topic change detection error: {str(e)}")
            return self._create_fallback_result(query, context)
    
    def handle_topic_transition(self, change_result: TopicChangeResult, 
                              context: ConversationContext) -> ConversationContext:
        """
        Topic geçişini handle et ve context'i güncelle
        
        Args:
            change_result: Topic change result
            context: Mevcut context
            
        Returns:
            ConversationContext: Güncellenmiş context
        """
        try:
            if not change_result.change_detected:
                return context
            
            # Apply transition strategy
            if change_result.transition_strategy == TopicTransitionStrategy.PRESERVE_CONTEXT:
                return self._preserve_context_transition(change_result, context)
            
            elif change_result.transition_strategy == TopicTransitionStrategy.PARTIAL_RESET:
                return self._partial_reset_transition(change_result, context)
            
            elif change_result.transition_strategy == TopicTransitionStrategy.FULL_RESET:
                return self._full_reset_transition(change_result, context)
            
            elif change_result.transition_strategy == TopicTransitionStrategy.MERGE_CONTEXTS:
                return self._merge_contexts_transition(change_result, context)
            
            elif change_result.transition_strategy == TopicTransitionStrategy.STACK_CONTEXT:
                return self._stack_context_transition(change_result, context)
            
            else:
                return context
                
        except Exception as e:
            logger.error(f"Topic transition handling error: {str(e)}")
            return context
    
    def _extract_current_topic(self, context: ConversationContext) -> Optional[str]:
        """Mevcut topic'i çıkar"""
        if context.current_topic:
            return context.current_topic
        
        # From recent products
        if context.discussed_products:
            last_product = context.discussed_products[-1]
            if isinstance(last_product.value, dict):
                return last_product.value.get('name', '')
            return str(last_product.value)
        
        # From context stack
        if context.context_stack:
            return context.context_stack[-1].value
        
        return None
    
    def _extract_topic_from_query(self, query: str) -> Optional[str]:
        """Query'den topic çıkar"""
        # Extract features as potential topics
        features = self.feature_extractor.extract_features(query)
        
        # Prioritize garment types
        garment_features = [f for f in features if f.category.value == 'garment_type']
        if garment_features:
            return garment_features[0].value
        
        # Then other high-weight features
        high_weight_features = [f for f in features if f.weight > 0.7]
        if high_weight_features:
            return high_weight_features[0].value
        
        # Extract from common product categories
        categories = ['gecelik', 'pijama', 'sabahlık', 'takım', 'elbise', 'bluz']
        query_lower = query.lower()
        
        for category in categories:
            if category in query_lower:
                return category
        
        return None
    
    def _calculate_topic_similarity(self, topic1: Optional[str], topic2: Optional[str]) -> float:
        """İki topic arasında benzerlik hesapla"""
        if not topic1 or not topic2:
            return 0.0
        
        if topic1 == topic2:
            return 1.0
        
        # Use Turkish similarity
        similarity = self.turkish_rules.calculate_turkish_similarity(topic1, topic2)
        
        # Check for semantic similarity (same category)
        features1 = self.feature_extractor.extract_features(topic1)
        features2 = self.feature_extractor.extract_features(topic2)
        
        if features1 and features2:
            categories1 = {f.category for f in features1}
            categories2 = {f.category for f in features2}
            
            if categories1.intersection(categories2):
                similarity += 0.3  # Bonus for same category
        
        return min(similarity, 1.0)
    
    def _classify_change_type(self, query: str, similarity: float, 
                            context: ConversationContext) -> TopicChangeType:
        """Change type'ını sınıflandır"""
        query_lower = query.lower()
        
        # Check for explicit indicators
        import re
        
        # Hard switch indicators
        for indicator in self.hard_switch_indicators:
            if re.search(indicator, query_lower):
                return TopicChangeType.HARD_SWITCH
        
        # Return indicators
        for indicator in self.return_indicators:
            if re.search(indicator, query_lower):
                return TopicChangeType.RETURN
        
        # Soft transition indicators
        for indicator in self.soft_transition_indicators:
            if re.search(indicator, query_lower):
                return TopicChangeType.SOFT_TRANSITION
        
        # Based on similarity
        if similarity >= self.similarity_thresholds['no_change']:
            return TopicChangeType.NO_CHANGE
        elif similarity >= self.similarity_thresholds['refinement']:
            return TopicChangeType.REFINEMENT
        elif similarity >= self.similarity_thresholds['soft_transition']:
            return TopicChangeType.SOFT_TRANSITION
        else:
            return TopicChangeType.HARD_SWITCH
    
    def _calculate_change_confidence(self, query: str, change_type: TopicChangeType, 
                                   similarity: float, context: ConversationContext) -> float:
        """Change confidence hesapla"""
        base_confidence = 0.5
        
        # Explicit indicators boost confidence
        query_lower = query.lower()
        import re
        
        indicator_boost = 0.0
        all_indicators = (self.hard_switch_indicators + 
                         self.soft_transition_indicators + 
                         self.return_indicators)
        
        for indicator in all_indicators:
            if re.search(indicator, query_lower):
                indicator_boost += 0.2
                break
        
        # Similarity-based confidence
        if change_type == TopicChangeType.NO_CHANGE:
            similarity_confidence = similarity
        else:
            similarity_confidence = 1.0 - similarity
        
        # Context consistency
        context_consistency = 0.0
        if context.conversation_history:
            # Check if change is consistent with conversation flow
            recent_turns = context.conversation_history[-3:]
            topic_changes = 0
            
            for turn in recent_turns:
                if len(turn.extracted_entities) > 0:
                    topic_changes += 1
            
            if topic_changes > 0:
                context_consistency = min(topic_changes / 3, 1.0)
        
        final_confidence = (
            base_confidence * 0.4 +
            indicator_boost * 0.3 +
            similarity_confidence * 0.2 +
            context_consistency * 0.1
        )
        
        return min(max(final_confidence, 0.1), 1.0)
    
    def _determine_transition_strategy(self, change_type: TopicChangeType, 
                                     context: ConversationContext) -> TopicTransitionStrategy:
        """Transition strategy belirle"""
        if change_type == TopicChangeType.NO_CHANGE:
            return TopicTransitionStrategy.PRESERVE_CONTEXT
        
        elif change_type == TopicChangeType.REFINEMENT:
            return TopicTransitionStrategy.PRESERVE_CONTEXT
        
        elif change_type == TopicChangeType.SOFT_TRANSITION:
            return TopicTransitionStrategy.MERGE_CONTEXTS
        
        elif change_type == TopicChangeType.RETURN:
            return TopicTransitionStrategy.STACK_CONTEXT
        
        elif change_type == TopicChangeType.HARD_SWITCH:
            # Check conversation length to decide
            if len(context.conversation_history) > 5:
                return TopicTransitionStrategy.PARTIAL_RESET
            else:
                return TopicTransitionStrategy.FULL_RESET
        
        else:
            return TopicTransitionStrategy.PRESERVE_CONTEXT
    
    def _prepare_context_preservation(self, change_type: TopicChangeType, 
                                    context: ConversationContext) -> Dict[str, Any]:
        """Context preservation hazırla"""
        preservation = {}
        
        if change_type in self.preservation_rules:
            rules = self.preservation_rules[change_type]
            
            if rules.get('preserve_user_preferences', False):
                preservation['user_preferences'] = context.user_preferences.copy()
            
            if rules.get('preserve_session_info', False):
                preservation['session_id'] = context.session_id
                preservation['last_activity'] = context.last_activity
            
            if rules.get('preserve_recent_products', False):
                preservation['recent_products'] = context.discussed_products[-2:] if context.discussed_products else []
            
            if rules.get('preserve_context_stack', False):
                preservation['context_stack'] = context.context_stack.copy()
        
        return preservation
    
    def _find_related_entities(self, old_topic: Optional[str], new_topic: Optional[str], 
                             context: ConversationContext) -> List[str]:
        """İlgili entity'leri bul"""
        related = []
        
        # Find entities related to both topics
        if old_topic and new_topic:
            for entity in context.active_entities.values():
                entity_value = str(entity.value).lower()
                
                if (old_topic.lower() in entity_value or 
                    new_topic.lower() in entity_value):
                    related.append(entity.entity_id)
        
        return related
    
    def _generate_change_explanation(self, change_type: TopicChangeType, 
                                   old_topic: Optional[str], new_topic: Optional[str], 
                                   confidence: float) -> str:
        """Change açıklaması oluştur"""
        if change_type == TopicChangeType.NO_CHANGE:
            return f"No topic change detected (confidence: {confidence:.0%})"
        
        old_str = old_topic or "unknown"
        new_str = new_topic or "unknown"
        
        explanations = {
            TopicChangeType.HARD_SWITCH: f"Hard switch from '{old_str}' to '{new_str}'",
            TopicChangeType.SOFT_TRANSITION: f"Soft transition from '{old_str}' to '{new_str}'",
            TopicChangeType.REFINEMENT: f"Refinement of '{old_str}' topic",
            TopicChangeType.RETURN: f"Return to previous topic '{new_str}'",
            TopicChangeType.EXPANSION: f"Expansion of '{old_str}' topic"
        }
        
        base_explanation = explanations.get(change_type, f"Topic change: {change_type.value}")
        return f"{base_explanation} (confidence: {confidence:.0%})"
    
    def _preserve_context_transition(self, change_result: TopicChangeResult, 
                                   context: ConversationContext) -> ConversationContext:
        """Context'i preserve ederek transition"""
        # Update current topic
        if change_result.new_topic:
            context.current_topic = change_result.new_topic
        
        return context
    
    def _partial_reset_transition(self, change_result: TopicChangeResult, 
                                context: ConversationContext) -> ConversationContext:
        """Partial reset ile transition"""
        # Preserve important context elements
        preserved = change_result.context_preservation
        
        # Reset discussed products but keep recent ones
        if 'recent_products' in preserved:
            context.discussed_products = preserved['recent_products']
        else:
            context.discussed_products = []
        
        # Update topic
        if change_result.new_topic:
            context.current_topic = change_result.new_topic
        
        # Partial reset of active entities
        entities_to_keep = {}
        for entity_id, entity in context.active_entities.items():
            if entity_id in change_result.related_entities:
                entities_to_keep[entity_id] = entity
        
        context.active_entities = entities_to_keep
        
        return context
    
    def _full_reset_transition(self, change_result: TopicChangeResult, 
                             context: ConversationContext) -> ConversationContext:
        """Full reset ile transition"""
        # Keep only essential session info
        preserved = change_result.context_preservation
        
        context.discussed_products = []
        context.active_entities = {}
        context.context_stack = []
        
        if change_result.new_topic:
            context.current_topic = change_result.new_topic
        
        # Keep user preferences if preserved
        if 'user_preferences' not in preserved:
            context.user_preferences = {}
        
        return context
    
    def _merge_contexts_transition(self, change_result: TopicChangeResult, 
                                 context: ConversationContext) -> ConversationContext:
        """Context'leri merge ederek transition"""
        # Add new topic while keeping old context
        if change_result.new_topic:
            context.current_topic = change_result.new_topic
        
        # Keep all entities but mark related ones
        for entity_id in change_result.related_entities:
            if entity_id in context.active_entities:
                entity = context.active_entities[entity_id]
                entity.mentioned_at = datetime.now()  # Update timestamp
        
        return context
    
    def _stack_context_transition(self, change_result: TopicChangeResult, 
                                context: ConversationContext) -> ConversationContext:
        """Context'i stack'leyerek transition"""
        # This would implement a context stack for returning to previous topics
        # For now, similar to preserve context
        return self._preserve_context_transition(change_result, context)
    
    def _create_fallback_result(self, query: str, context: ConversationContext) -> TopicChangeResult:
        """Fallback result"""
        return TopicChangeResult(
            change_detected=False,
            change_type=TopicChangeType.NO_CHANGE,
            confidence=0.1,
            old_topic=self._extract_current_topic(context),
            new_topic=None,
            transition_strategy=TopicTransitionStrategy.PRESERVE_CONTEXT,
            context_preservation={},
            explanation="Fallback: no change detected due to error",
            related_entities=[]
        )
    
    def get_detector_stats(self) -> Dict[str, Any]:
        """Detector istatistikleri"""
        return {
            'change_types': [ct.value for ct in TopicChangeType],
            'transition_strategies': [ts.value for ts in TopicTransitionStrategy],
            'hard_switch_indicators': len(self.hard_switch_indicators),
            'soft_transition_indicators': len(self.soft_transition_indicators),
            'return_indicators': len(self.return_indicators),
            'similarity_thresholds': self.similarity_thresholds
        }

# Test fonksiyonu
def test_topic_change_detector():
    """Topic change detector test"""
    
    # Setup
    from conversation_context_manager import ConversationContext, ContextEntity, ContextType, EntityType
    from datetime import datetime
    
    detector = TopicChangeDetector()
    
    # Create test context
    context = ConversationContext(
        session_id="test_session_topic",
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
        user_preferences={"color": "siyah"},
        conversation_history=[],
        last_activity=datetime.now(),
        context_confidence=0.8,
        active_entities={},
        context_stack=[ContextType.PRODUCT_INQUIRY]
    )
    
    print("🔄 Topic Change Detector Test:")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Bu geceliğin fiyatı nedir?",        # NO_CHANGE
        "Siyah pijama da var mı?",           # SOFT_TRANSITION
        "Şimdi hamile kıyafetlerine bakalım", # HARD_SWITCH
        "Benzer gecelikler göster",          # REFINEMENT
        "Geri o geceliğe dönelim",          # RETURN
        "Başka bir şey arıyorum"            # HARD_SWITCH
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        result = detector.detect_topic_change(query, context)
        
        print(f"  🔄 Change detected: {result.change_detected}")
        print(f"  📊 Change type: {result.change_type.value}")
        print(f"  📈 Confidence: {result.confidence:.2f}")
        print(f"  🏷️ Old topic: {result.old_topic}")
        print(f"  🆕 New topic: {result.new_topic}")
        print(f"  🔧 Strategy: {result.transition_strategy.value}")
        print(f"  📝 Explanation: {result.explanation}")
        
        if result.related_entities:
            print(f"  🔗 Related entities: {len(result.related_entities)}")
        
        if result.context_preservation:
            print(f"  💾 Context preservation: {list(result.context_preservation.keys())}")
        
        # Test transition handling
        if result.change_detected:
            updated_context = detector.handle_topic_transition(result, context)
            print(f"  ✅ Context updated - New topic: {updated_context.current_topic}")
    
    # Stats
    stats = detector.get_detector_stats()
    print(f"\n📊 Detector Stats:")
    print(f"  Change types: {len(stats['change_types'])}")
    print(f"  Transition strategies: {len(stats['transition_strategies'])}")
    print(f"  Indicators: {stats['hard_switch_indicators']} + {stats['soft_transition_indicators']} + {stats['return_indicators']}")

if __name__ == "__main__":
    test_topic_change_detector()