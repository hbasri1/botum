#!/usr/bin/env python3
"""
Conversation Context Manager - Session-based context management with TTL
"""

import time
import logging
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

try:
    from .product_feature_extractor import ProductFeatureExtractor
    from .turkish_language_rules import TurkishLanguageRules
except ImportError:
    from product_feature_extractor import ProductFeatureExtractor
    from turkish_language_rules import TurkishLanguageRules

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """Context türleri"""
    PRODUCT_INQUIRY = "product_inquiry"
    PRODUCT_COMPARISON = "product_comparison"
    GENERAL_INFO = "general_info"
    SEARCH_REFINEMENT = "search_refinement"
    FOLLOW_UP = "follow_up"

class EntityType(Enum):
    """Entity türleri"""
    PRODUCT = "product"
    CATEGORY = "category"
    FEATURE = "feature"
    PRICE = "price"
    BRAND = "brand"
    USER_PREFERENCE = "user_preference"

@dataclass
class ContextEntity:
    """Context entity"""
    entity_id: str
    entity_type: EntityType
    value: Any
    confidence: float
    mentioned_at: datetime
    context_type: ContextType
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ConversationTurn:
    """Konuşma turu"""
    turn_id: str
    user_message: str
    bot_response: str
    timestamp: datetime
    context_type: ContextType
    extracted_entities: List[ContextEntity]
    intent: Optional[str] = None
    confidence: float = 1.0

@dataclass
class ConversationContext:
    """Konuşma context'i"""
    session_id: str
    current_topic: Optional[str]
    discussed_products: List[ContextEntity]
    user_preferences: Dict[str, Any]
    conversation_history: List[ConversationTurn]
    last_activity: datetime
    context_confidence: float
    active_entities: Dict[str, ContextEntity]
    context_stack: List[ContextType]
    
    def __post_init__(self):
        if not self.discussed_products:
            self.discussed_products = []
        if not self.user_preferences:
            self.user_preferences = {}
        if not self.conversation_history:
            self.conversation_history = []
        if not self.active_entities:
            self.active_entities = {}
        if not self.context_stack:
            self.context_stack = []

class ConversationContextManager:
    """Session-based conversation context manager"""
    
    def __init__(self, default_ttl_minutes: int = 30):
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.contexts: Dict[str, ConversationContext] = {}
        self.feature_extractor = ProductFeatureExtractor()
        self.turkish_rules = TurkishLanguageRules()
        
        # Context management parameters
        self.max_history_length = 20
        self.max_active_entities = 10
        self.entity_decay_factor = 0.9
        self.context_confidence_threshold = 0.3
        
        # Intent patterns for context type detection
        self.intent_patterns = {
            ContextType.PRODUCT_INQUIRY: [
                r'\b(fiyat|price|kaç para|ne kadar)\b',
                r'\b(özellik|feature|nasıl|hangi)\b',
                r'\b(stok|var mı|mevcut)\b'
            ],
            ContextType.PRODUCT_COMPARISON: [
                r'\b(karşılaştır|compare|fark|difference)\b',
                r'\b(hangisi|which|better|daha iyi)\b',
                r'\b(benzer|similar|alternatif)\b'
            ],
            ContextType.GENERAL_INFO: [
                r'\b(kargo|shipping|teslimat)\b',
                r'\b(iade|return|değişim)\b',
                r'\b(telefon|iletişim|contact)\b'
            ],
            ContextType.SEARCH_REFINEMENT: [
                r'\b(başka|other|farklı|different)\b',
                r'\b(daha|more|less|az)\b',
                r'\b(renk|color|beden|size)\b'
            ]
        }
    
    def store_context(self, session_id: str, entity: ContextEntity):
        """Context entity'sini sakla"""
        try:
            # Get or create context
            context = self.get_context(session_id)
            
            # Add to active entities
            context.active_entities[entity.entity_id] = entity
            
            # Add to appropriate list based on type
            if entity.entity_type == EntityType.PRODUCT:
                # Remove old product references to avoid clutter
                context.discussed_products = [
                    p for p in context.discussed_products 
                    if p.entity_id != entity.entity_id
                ]
                context.discussed_products.append(entity)
                
                # Keep only recent products
                if len(context.discussed_products) > 5:
                    context.discussed_products = context.discussed_products[-5:]
            
            # Update context stack
            if entity.context_type not in context.context_stack:
                context.context_stack.append(entity.context_type)
            
            # Update activity timestamp
            context.last_activity = datetime.now()
            
            # Cleanup old entities
            self._cleanup_old_entities(context)
            
            logger.info(f"Stored context entity {entity.entity_id} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error storing context: {str(e)}")
    
    def get_context(self, session_id: str) -> ConversationContext:
        """Session context'ini getir"""
        try:
            # Check if context exists and is not expired
            if session_id in self.contexts:
                context = self.contexts[session_id]
                if datetime.now() - context.last_activity < self.default_ttl:
                    return context
                else:
                    # Context expired, remove it
                    del self.contexts[session_id]
                    logger.info(f"Context expired for session {session_id}")
            
            # Create new context
            context = ConversationContext(
                session_id=session_id,
                current_topic=None,
                discussed_products=[],
                user_preferences={},
                conversation_history=[],
                last_activity=datetime.now(),
                context_confidence=1.0,
                active_entities={},
                context_stack=[]
            )
            
            self.contexts[session_id] = context
            logger.info(f"Created new context for session {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            # Return empty context on error
            return ConversationContext(
                session_id=session_id,
                current_topic=None,
                discussed_products=[],
                user_preferences={},
                conversation_history=[],
                last_activity=datetime.now(),
                context_confidence=0.0,
                active_entities={},
                context_stack=[]
            )
    
    def add_conversation_turn(self, session_id: str, user_message: str, 
                            bot_response: str, context_type: ContextType = None):
        """Konuşma turu ekle"""
        try:
            context = self.get_context(session_id)
            
            # Extract entities from user message
            extracted_entities = self._extract_entities_from_message(user_message, context_type)
            
            # Detect context type if not provided
            if context_type is None:
                context_type = self._detect_context_type(user_message, context)
            
            # Create conversation turn
            turn = ConversationTurn(
                turn_id=f"{session_id}_{len(context.conversation_history)}",
                user_message=user_message,
                bot_response=bot_response,
                timestamp=datetime.now(),
                context_type=context_type,
                extracted_entities=extracted_entities,
                intent=self._extract_intent(user_message),
                confidence=self._calculate_turn_confidence(user_message, extracted_entities)
            )
            
            # Add to history
            context.conversation_history.append(turn)
            
            # Keep history within limits
            if len(context.conversation_history) > self.max_history_length:
                context.conversation_history = context.conversation_history[-self.max_history_length:]
            
            # Store extracted entities
            for entity in extracted_entities:
                self.store_context(session_id, entity)
            
            # Update current topic
            self._update_current_topic(context, turn)
            
            # Update context confidence
            self._update_context_confidence(context)
            
            logger.info(f"Added conversation turn for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error adding conversation turn: {str(e)}")
    
    def resolve_ambiguous_query(self, query: str, session_id: str) -> str:
        """Belirsiz sorguyu context kullanarak çöz"""
        try:
            context = self.get_context(session_id)
            
            # Check for implicit references
            resolved_query = self._resolve_implicit_references(query, context)
            
            # Add context from recent products
            if self._is_follow_up_question(query):
                resolved_query = self._add_product_context(resolved_query, context)
            
            # Add user preferences
            resolved_query = self._add_preference_context(resolved_query, context)
            
            logger.info(f"Resolved query: '{query}' -> '{resolved_query}'")
            return resolved_query
            
        except Exception as e:
            logger.error(f"Error resolving ambiguous query: {str(e)}")
            return query  # Return original query on error
    
    def detect_context_switch(self, query: str, session_id: str) -> bool:
        """Context değişimini tespit et"""
        try:
            context = self.get_context(session_id)
            
            if not context.conversation_history:
                return False
            
            # Current context type
            current_context = context.context_stack[-1] if context.context_stack else None
            
            # Detect new context type
            new_context = self._detect_context_type(query, context)
            
            # Check for explicit topic change indicators
            topic_change_indicators = [
                'başka', 'farklı', 'other', 'different', 'yeni', 'new',
                'şimdi', 'now', 'bunun yerine', 'instead'
            ]
            
            query_lower = query.lower()
            has_topic_change_indicator = any(indicator in query_lower for indicator in topic_change_indicators)
            
            # Context switch if:
            # 1. Different context type detected
            # 2. Explicit topic change indicators
            # 3. No reference to current entities
            context_switch = (
                new_context != current_context or
                has_topic_change_indicator or
                not self._references_current_entities(query, context)
            )
            
            if context_switch:
                logger.info(f"Context switch detected: {current_context} -> {new_context}")
            
            return context_switch
            
        except Exception as e:
            logger.error(f"Error detecting context switch: {str(e)}")
            return False
    
    def _extract_entities_from_message(self, message: str, context_type: ContextType = None) -> List[ContextEntity]:
        """Mesajdan entity'leri çıkar"""
        entities = []
        
        try:
            # Extract product features
            features = self.feature_extractor.extract_features(message)
            for feature in features:
                entity = ContextEntity(
                    entity_id=f"feature_{feature.value}",
                    entity_type=EntityType.FEATURE,
                    value=feature.value,
                    confidence=feature.confidence,
                    mentioned_at=datetime.now(),
                    context_type=context_type or ContextType.PRODUCT_INQUIRY,
                    metadata={'category': feature.category.value, 'weight': feature.weight}
                )
                entities.append(entity)
            
            # Extract price mentions
            price_patterns = [
                r'(\d+)\s*(tl|lira|₺)',
                r'(fiyat|price|kaç para|ne kadar)',
                r'(ucuz|expensive|pahalı|cheap)'
            ]
            
            for pattern in price_patterns:
                import re
                matches = re.findall(pattern, message.lower())
                if matches:
                    entity = ContextEntity(
                        entity_id=f"price_mention_{len(entities)}",
                        entity_type=EntityType.PRICE,
                        value=matches[0] if isinstance(matches[0], str) else matches[0][0],
                        confidence=0.8,
                        mentioned_at=datetime.now(),
                        context_type=context_type or ContextType.PRODUCT_INQUIRY
                    )
                    entities.append(entity)
            
            # Extract category mentions
            categories = ['gecelik', 'pijama', 'sabahlık', 'takım', 'elbise', 'bluz']
            message_lower = message.lower()
            for category in categories:
                if category in message_lower:
                    entity = ContextEntity(
                        entity_id=f"category_{category}",
                        entity_type=EntityType.CATEGORY,
                        value=category,
                        confidence=0.9,
                        mentioned_at=datetime.now(),
                        context_type=context_type or ContextType.PRODUCT_INQUIRY
                    )
                    entities.append(entity)
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
        
        return entities
    
    def _detect_context_type(self, message: str, context: ConversationContext) -> ContextType:
        """Mesajdan context type'ını tespit et"""
        import re
        
        message_lower = message.lower()
        
        # Check patterns for each context type
        for context_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return context_type
        
        # Default based on conversation history
        if context.context_stack:
            return context.context_stack[-1]
        
        return ContextType.PRODUCT_INQUIRY
    
    def _extract_intent(self, message: str) -> Optional[str]:
        """Mesajdan intent çıkar"""
        import re
        
        intent_patterns = {
            'price_inquiry': r'\b(fiyat|price|kaç para|ne kadar)\b',
            'availability_check': r'\b(var mı|mevcut|stok)\b',
            'feature_inquiry': r'\b(özellik|nasıl|hangi)\b',
            'comparison': r'\b(karşılaştır|fark|hangisi)\b',
            'search': r'\b(ara|bul|göster|show)\b'
        }
        
        message_lower = message.lower()
        for intent, pattern in intent_patterns.items():
            if re.search(pattern, message_lower):
                return intent
        
        return None
    
    def _calculate_turn_confidence(self, message: str, entities: List[ContextEntity]) -> float:
        """Turn confidence hesapla"""
        base_confidence = 0.5
        
        # Entity count bonus
        entity_bonus = min(len(entities) * 0.1, 0.3)
        
        # Message length bonus (longer messages usually more informative)
        length_bonus = min(len(message.split()) * 0.02, 0.2)
        
        # High confidence entities bonus
        high_conf_entities = sum(1 for e in entities if e.confidence > 0.8)
        high_conf_bonus = min(high_conf_entities * 0.05, 0.15)
        
        return min(base_confidence + entity_bonus + length_bonus + high_conf_bonus, 1.0)
    
    def _update_current_topic(self, context: ConversationContext, turn: ConversationTurn):
        """Current topic'i güncelle"""
        # Extract potential topics from entities
        product_entities = [e for e in turn.extracted_entities if e.entity_type == EntityType.PRODUCT]
        category_entities = [e for e in turn.extracted_entities if e.entity_type == EntityType.CATEGORY]
        
        if product_entities:
            context.current_topic = product_entities[0].value
        elif category_entities:
            context.current_topic = category_entities[0].value
        elif turn.context_type != ContextType.FOLLOW_UP:
            # Reset topic if not a follow-up
            context.current_topic = None
    
    def _update_context_confidence(self, context: ConversationContext):
        """Context confidence'ını güncelle"""
        if not context.conversation_history:
            context.context_confidence = 1.0
            return
        
        # Calculate based on recent turns
        recent_turns = context.conversation_history[-5:]
        avg_confidence = sum(turn.confidence for turn in recent_turns) / len(recent_turns)
        
        # Decay factor for older context
        time_since_last = (datetime.now() - context.last_activity).total_seconds() / 60  # minutes
        time_decay = max(0.5, 1.0 - (time_since_last / 30))  # Decay over 30 minutes
        
        context.context_confidence = avg_confidence * time_decay
    
    def _resolve_implicit_references(self, query: str, context: ConversationContext) -> str:
        """Implicit referansları çöz"""
        # Pronouns and implicit references
        implicit_patterns = {
            r'\b(bu|this|o|that|onun|its)\b': lambda: self._get_last_product_name(context),
            r'\b(bunun|this one|onun)\b': lambda: self._get_last_product_name(context),
            r'\b(fiyatı|price of it)\b': lambda: f"{self._get_last_product_name(context)} fiyatı"
        }
        
        resolved_query = query
        import re
        
        for pattern, resolver in implicit_patterns.items():
            if re.search(pattern, query.lower()):
                replacement = resolver()
                if replacement:
                    resolved_query = re.sub(pattern, replacement, resolved_query, flags=re.IGNORECASE)
        
        return resolved_query
    
    def _get_last_product_name(self, context: ConversationContext) -> Optional[str]:
        """Son bahsedilen ürün adını getir"""
        if context.discussed_products:
            return context.discussed_products[-1].value.get('name', '') if isinstance(context.discussed_products[-1].value, dict) else str(context.discussed_products[-1].value)
        return None
    
    def _is_follow_up_question(self, query: str) -> bool:
        """Follow-up soru mu kontrol et"""
        follow_up_indicators = [
            'fiyatı', 'price', 'kaç para', 'ne kadar',
            'özellikleri', 'features', 'nasıl',
            'var mı', 'available', 'stok',
            'rengi', 'color', 'bedeni', 'size'
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in follow_up_indicators)
    
    def _add_product_context(self, query: str, context: ConversationContext) -> str:
        """Ürün context'ini ekle"""
        if context.discussed_products:
            last_product = context.discussed_products[-1]
            if isinstance(last_product.value, dict):
                product_name = last_product.value.get('name', '')
            else:
                product_name = str(last_product.value)
            
            if product_name and product_name.lower() not in query.lower():
                return f"{product_name} {query}"
        
        return query
    
    def _add_preference_context(self, query: str, context: ConversationContext) -> str:
        """Kullanıcı tercihlerini ekle"""
        # Add user preferences if relevant
        if context.user_preferences:
            for pref_key, pref_value in context.user_preferences.items():
                if pref_key not in query.lower() and isinstance(pref_value, str):
                    query += f" {pref_value}"
        
        return query
    
    def _references_current_entities(self, query: str, context: ConversationContext) -> bool:
        """Mevcut entity'lere referans var mı"""
        query_lower = query.lower()
        
        # Check active entities
        for entity in context.active_entities.values():
            if isinstance(entity.value, str) and entity.value.lower() in query_lower:
                return True
            elif isinstance(entity.value, dict):
                name = entity.value.get('name', '')
                if name and name.lower() in query_lower:
                    return True
        
        return False
    
    def _cleanup_old_entities(self, context: ConversationContext):
        """Eski entity'leri temizle"""
        current_time = datetime.now()
        
        # Remove entities older than TTL
        active_entities_to_remove = []
        for entity_id, entity in context.active_entities.items():
            if current_time - entity.mentioned_at > self.default_ttl:
                active_entities_to_remove.append(entity_id)
        
        for entity_id in active_entities_to_remove:
            del context.active_entities[entity_id]
        
        # Keep only recent discussed products
        context.discussed_products = [
            p for p in context.discussed_products
            if current_time - p.mentioned_at < self.default_ttl
        ]
        
        # Limit active entities count
        if len(context.active_entities) > self.max_active_entities:
            # Keep most recent entities
            sorted_entities = sorted(
                context.active_entities.items(),
                key=lambda x: x[1].mentioned_at,
                reverse=True
            )
            context.active_entities = dict(sorted_entities[:self.max_active_entities])
    
    def clear_context(self, session_id: str):
        """Context'i temizle"""
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"Cleared context for session {session_id}")
    
    def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Context özeti"""
        try:
            context = self.get_context(session_id)
            
            return {
                'session_id': session_id,
                'current_topic': context.current_topic,
                'discussed_products_count': len(context.discussed_products),
                'conversation_turns': len(context.conversation_history),
                'active_entities_count': len(context.active_entities),
                'context_confidence': context.context_confidence,
                'last_activity': context.last_activity.isoformat(),
                'context_stack': [ct.value for ct in context.context_stack],
                'user_preferences': context.user_preferences
            }
            
        except Exception as e:
            logger.error(f"Error getting context summary: {str(e)}")
            return {'error': str(e)}
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Manager istatistikleri"""
        active_sessions = len(self.contexts)
        total_turns = sum(len(ctx.conversation_history) for ctx in self.contexts.values())
        total_entities = sum(len(ctx.active_entities) for ctx in self.contexts.values())
        
        return {
            'active_sessions': active_sessions,
            'total_conversation_turns': total_turns,
            'total_active_entities': total_entities,
            'default_ttl_minutes': self.default_ttl.total_seconds() / 60,
            'max_history_length': self.max_history_length,
            'max_active_entities': self.max_active_entities
        }

# Test fonksiyonu
def test_conversation_context_manager():
    """Conversation context manager test"""
    
    manager = ConversationContextManager(default_ttl_minutes=5)
    session_id = "test_session_123"
    
    print("💬 Conversation Context Manager Test:")
    print("=" * 50)
    
    # Test 1: Basic context creation
    context = manager.get_context(session_id)
    print(f"✅ Created context for session: {context.session_id}")
    
    # Test 2: Add conversation turns
    manager.add_conversation_turn(
        session_id, 
        "Siyah gecelik arıyorum", 
        "Size uygun siyah gecelikler buldum"
    )
    
    manager.add_conversation_turn(
        session_id,
        "Fiyatı nedir?",
        "Bu ürünün fiyatı 890 TL"
    )
    
    print(f"✅ Added conversation turns")
    
    # Test 3: Context resolution
    resolved_query = manager.resolve_ambiguous_query("fiyatı nedir", session_id)
    print(f"🔍 Resolved query: 'fiyatı nedir' -> '{resolved_query}'")
    
    # Test 4: Context switch detection
    context_switch = manager.detect_context_switch("Hamile pijamalarına bakalım", session_id)
    print(f"🔄 Context switch detected: {context_switch}")
    
    # Test 5: Context summary
    summary = manager.get_context_summary(session_id)
    print(f"📊 Context summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test 6: Manager stats
    stats = manager.get_manager_stats()
    print(f"\n📈 Manager stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_conversation_context_manager()