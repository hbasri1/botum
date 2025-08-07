#!/usr/bin/env python3
"""
Context-Aware Query Resolver - Ambiguous query resolution using conversation history
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .conversation_context_manager import ConversationContextManager, ContextEntity, ContextType, EntityType
    from .product_feature_extractor import ProductFeatureExtractor
    from .turkish_language_rules import TurkishLanguageRules
    from .feature_synonym_mapper import FeatureSynonymMapper
except ImportError:
    from conversation_context_manager import ConversationContextManager, ContextEntity, ContextType, EntityType
    from product_feature_extractor import ProductFeatureExtractor
    from turkish_language_rules import TurkishLanguageRules
    from feature_synonym_mapper import FeatureSynonymMapper

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Query türleri"""
    EXPLICIT = "explicit"          # Açık, tam sorgu
    IMPLICIT_REFERENCE = "implicit_reference"  # Bu, o, onun gibi referanslar
    FOLLOW_UP = "follow_up"        # Takip sorusu
    CONTEXTUAL = "contextual"      # Context'e dayalı
    AMBIGUOUS = "ambiguous"        # Belirsiz

class ResolutionStrategy(Enum):
    """Çözümleme stratejileri"""
    ENTITY_SUBSTITUTION = "entity_substitution"
    CONTEXT_EXPANSION = "context_expansion"
    PREFERENCE_INJECTION = "preference_injection"
    HISTORY_BASED = "history_based"
    CLARIFICATION_REQUEST = "clarification_request"

@dataclass
class ResolvedQuery:
    """Çözümlenmiş sorgu"""
    original_query: str
    resolved_query: str
    query_type: QueryType
    resolution_strategy: ResolutionStrategy
    confidence: float
    used_entities: List[str]
    context_additions: List[str]
    explanation: str
    needs_clarification: bool = False
    clarification_options: List[str] = None
    
    def __post_init__(self):
        if self.clarification_options is None:
            self.clarification_options = []

class ContextAwareQueryResolver:
    """Context-aware query resolution engine"""
    
    def __init__(self, context_manager: ConversationContextManager):
        self.context_manager = context_manager
        self.feature_extractor = ProductFeatureExtractor()
        self.turkish_rules = TurkishLanguageRules()
        self.synonym_mapper = FeatureSynonymMapper()
        
        # Query patterns for different types
        self.query_patterns = {
            QueryType.IMPLICIT_REFERENCE: [
                r'\b(bu|this|o|that|şu)\b',
                r'\b(bunun|this one|onun|şunun)\b',
                r'\b(bunlar|these|onlar|those)\b'
            ],
            QueryType.FOLLOW_UP: [
                r'\b(fiyatı|price|kaç para|ne kadar)\b',
                r'\b(özellikleri|features|nasıl)\b',
                r'\b(var mı|available|stok|mevcut)\b',
                r'\b(rengi|color|bedeni|size)\b',
                r'\b(malzemesi|material|kumaşı)\b'
            ],
            QueryType.CONTEXTUAL: [
                r'\b(daha|more|başka|other|farklı)\b',
                r'\b(benzer|similar|aynı|same)\b',
                r'\b(alternatif|alternative|seçenek)\b'
            ]
        }
        
        # Resolution confidence thresholds
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    def resolve_ambiguous_query(self, query: str, session_id: str) -> ResolvedQuery:
        """
        Belirsiz sorguyu context kullanarak çöz
        
        Args:
            query: Orijinal sorgu
            session_id: Session ID
            
        Returns:
            ResolvedQuery: Çözümlenmiş sorgu
        """
        try:
            # Get conversation context
            context = self.context_manager.get_context(session_id)
            
            # Determine query type
            query_type = self._classify_query_type(query, context)
            
            # Apply appropriate resolution strategy
            if query_type == QueryType.EXPLICIT:
                return self._handle_explicit_query(query)
            elif query_type == QueryType.IMPLICIT_REFERENCE:
                return self._resolve_implicit_references(query, context)
            elif query_type == QueryType.FOLLOW_UP:
                return self._resolve_follow_up_query(query, context)
            elif query_type == QueryType.CONTEXTUAL:
                return self._resolve_contextual_query(query, context)
            else:  # AMBIGUOUS
                return self._resolve_ambiguous_query(query, context)
                
        except Exception as e:
            logger.error(f"Query resolution error: {str(e)}")
            return self._create_fallback_resolution(query)
    
    def detect_followup(self, query: str, session_id: str) -> bool:
        """Follow-up soru tespiti"""
        try:
            context = self.context_manager.get_context(session_id)
            
            # Check for follow-up patterns
            query_lower = query.lower()
            for pattern in self.query_patterns[QueryType.FOLLOW_UP]:
                if re.search(pattern, query_lower):
                    return True
            
            # Check if query is very short (likely follow-up)
            if len(query.split()) <= 3 and context.discussed_products:
                return True
            
            # Check for implicit references
            for pattern in self.query_patterns[QueryType.IMPLICIT_REFERENCE]:
                if re.search(pattern, query_lower):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Follow-up detection error: {str(e)}")
            return False
    
    def detect_topic_change(self, query: str, session_id: str) -> bool:
        """Topic değişimi tespiti"""
        return self.context_manager.detect_context_switch(query, session_id)
    
    def _classify_query_type(self, query: str, context) -> QueryType:
        """Query türünü sınıflandır"""
        query_lower = query.lower()
        
        # Check for implicit references
        for pattern in self.query_patterns[QueryType.IMPLICIT_REFERENCE]:
            if re.search(pattern, query_lower):
                return QueryType.IMPLICIT_REFERENCE
        
        # Check for follow-up patterns
        for pattern in self.query_patterns[QueryType.FOLLOW_UP]:
            if re.search(pattern, query_lower):
                return QueryType.FOLLOW_UP
        
        # Check for contextual patterns
        for pattern in self.query_patterns[QueryType.CONTEXTUAL]:
            if re.search(pattern, query_lower):
                return QueryType.CONTEXTUAL
        
        # Check if query is complete and specific
        if self._is_explicit_query(query):
            return QueryType.EXPLICIT
        
        return QueryType.AMBIGUOUS
    
    def _is_explicit_query(self, query: str) -> bool:
        """Sorgu açık ve tam mı?"""
        # Extract features to check completeness
        features = self.feature_extractor.extract_features(query)
        
        # Consider explicit if has multiple features or specific product terms
        if len(features) >= 2:
            return True
        
        # Check for specific product categories
        product_categories = ['gecelik', 'pijama', 'sabahlık', 'takım', 'elbise']
        query_lower = query.lower()
        
        has_category = any(cat in query_lower for cat in product_categories)
        has_descriptor = len(query.split()) >= 3
        
        return has_category and has_descriptor
    
    def _handle_explicit_query(self, query: str) -> ResolvedQuery:
        """Açık sorguyu işle"""
        return ResolvedQuery(
            original_query=query,
            resolved_query=query,
            query_type=QueryType.EXPLICIT,
            resolution_strategy=ResolutionStrategy.ENTITY_SUBSTITUTION,
            confidence=1.0,
            used_entities=[],
            context_additions=[],
            explanation="Query is explicit and complete"
        )
    
    def _resolve_implicit_references(self, query: str, context) -> ResolvedQuery:
        """Implicit referansları çöz"""
        resolved_query = query
        used_entities = []
        context_additions = []
        
        # Get the most recent product
        last_product = self._get_most_recent_product(context)
        
        if last_product:
            product_name = self._extract_product_name(last_product)
            
            # Replace implicit references
            implicit_patterns = {
                r'\b(bu|this)\b': product_name,
                r'\b(o|that)\b': product_name,
                r'\b(bunun|this one)\b': f"{product_name}",
                r'\b(onun|its)\b': f"{product_name}",
                r'\b(bunların|these)\b': product_name,
                r'\b(onların|those)\b': product_name
            }
            
            for pattern, replacement in implicit_patterns.items():
                if re.search(pattern, query.lower()):
                    resolved_query = re.sub(pattern, replacement, resolved_query, flags=re.IGNORECASE)
                    used_entities.append(last_product.entity_id)
                    context_additions.append(replacement)
                    break
        
        confidence = 0.9 if used_entities else 0.3
        
        return ResolvedQuery(
            original_query=query,
            resolved_query=resolved_query,
            query_type=QueryType.IMPLICIT_REFERENCE,
            resolution_strategy=ResolutionStrategy.ENTITY_SUBSTITUTION,
            confidence=confidence,
            used_entities=used_entities,
            context_additions=context_additions,
            explanation=f"Resolved implicit reference using {len(used_entities)} entities"
        )
    
    def _resolve_follow_up_query(self, query: str, context) -> ResolvedQuery:
        """Follow-up sorguyu çöz"""
        resolved_query = query
        used_entities = []
        context_additions = []
        
        # Get the most recent product for context
        last_product = self._get_most_recent_product(context)
        
        if last_product:
            product_name = self._extract_product_name(last_product)
            
            # Add product context to follow-up questions
            follow_up_expansions = {
                r'\b(fiyatı|price)\b': f"{product_name} fiyatı",
                r'\b(özellikleri|features)\b': f"{product_name} özellikleri",
                r'\b(var mı|available)\b': f"{product_name} var mı",
                r'\b(rengi|color)\b': f"{product_name} rengi",
                r'\b(bedeni|size)\b': f"{product_name} bedeni",
                r'\b(malzemesi|material)\b': f"{product_name} malzemesi"
            }
            
            for pattern, expansion in follow_up_expansions.items():
                if re.search(pattern, query.lower()):
                    resolved_query = expansion
                    used_entities.append(last_product.entity_id)
                    context_additions.append(product_name)
                    break
            
            # If no specific pattern matched, prepend product name
            if not used_entities and product_name not in resolved_query:
                resolved_query = f"{product_name} {query}"
                used_entities.append(last_product.entity_id)
                context_additions.append(product_name)
        
        confidence = 0.8 if used_entities else 0.4
        
        return ResolvedQuery(
            original_query=query,
            resolved_query=resolved_query,
            query_type=QueryType.FOLLOW_UP,
            resolution_strategy=ResolutionStrategy.CONTEXT_EXPANSION,
            confidence=confidence,
            used_entities=used_entities,
            context_additions=context_additions,
            explanation=f"Resolved follow-up query with product context"
        )
    
    def _resolve_contextual_query(self, query: str, context) -> ResolvedQuery:
        """Contextual sorguyu çöz"""
        resolved_query = query
        used_entities = []
        context_additions = []
        
        # Get recent entities for context
        recent_features = self._get_recent_features(context)
        recent_categories = self._get_recent_categories(context)
        
        # Add contextual information
        if "daha" in query.lower() or "başka" in query.lower():
            # User wants more/different options
            if recent_categories:
                category = recent_categories[0].value
                resolved_query = f"{category} {query}"
                used_entities.append(recent_categories[0].entity_id)
                context_additions.append(category)
        
        elif "benzer" in query.lower() or "aynı" in query.lower():
            # User wants similar items
            if recent_features:
                feature_values = [f.value for f in recent_features[:2]]
                feature_context = " ".join(feature_values)
                resolved_query = f"{feature_context} {query}"
                used_entities.extend([f.entity_id for f in recent_features[:2]])
                context_additions.extend(feature_values)
        
        # Add user preferences if available
        if context.user_preferences:
            for pref_key, pref_value in context.user_preferences.items():
                if isinstance(pref_value, str) and pref_value not in resolved_query.lower():
                    resolved_query += f" {pref_value}"
                    context_additions.append(pref_value)
        
        confidence = 0.7 if used_entities else 0.5
        
        return ResolvedQuery(
            original_query=query,
            resolved_query=resolved_query,
            query_type=QueryType.CONTEXTUAL,
            resolution_strategy=ResolutionStrategy.PREFERENCE_INJECTION,
            confidence=confidence,
            used_entities=used_entities,
            context_additions=context_additions,
            explanation=f"Added contextual information from {len(used_entities)} entities"
        )
    
    def _resolve_ambiguous_query(self, query: str, context) -> ResolvedQuery:
        """Belirsiz sorguyu çöz"""
        resolved_query = query
        used_entities = []
        context_additions = []
        clarification_options = []
        
        # Try to add context from conversation history
        if context.conversation_history:
            # Get recent topics
            recent_topics = self._extract_recent_topics(context)
            if recent_topics:
                resolved_query = f"{recent_topics[0]} {query}"
                context_additions.append(recent_topics[0])
        
        # Generate clarification options
        if context.discussed_products:
            for product in context.discussed_products[-3:]:  # Last 3 products
                product_name = self._extract_product_name(product)
                clarification_options.append(f"{product_name} hakkında mı?")
        
        if context.active_entities:
            categories = [e for e in context.active_entities.values() if e.entity_type == EntityType.CATEGORY]
            for category in categories[:2]:
                clarification_options.append(f"{category.value} kategorisinde mi?")
        
        needs_clarification = len(clarification_options) > 0
        confidence = 0.3 if not needs_clarification else 0.2
        
        return ResolvedQuery(
            original_query=query,
            resolved_query=resolved_query,
            query_type=QueryType.AMBIGUOUS,
            resolution_strategy=ResolutionStrategy.CLARIFICATION_REQUEST,
            confidence=confidence,
            used_entities=used_entities,
            context_additions=context_additions,
            explanation="Query is ambiguous, may need clarification",
            needs_clarification=needs_clarification,
            clarification_options=clarification_options
        )
    
    def _get_most_recent_product(self, context) -> Optional[ContextEntity]:
        """En son bahsedilen ürünü getir"""
        if context.discussed_products:
            return context.discussed_products[-1]
        return None
    
    def _extract_product_name(self, product_entity: ContextEntity) -> str:
        """Product entity'sinden ürün adını çıkar"""
        if isinstance(product_entity.value, dict):
            return product_entity.value.get('name', str(product_entity.value))
        return str(product_entity.value)
    
    def _get_recent_features(self, context) -> List[ContextEntity]:
        """Son bahsedilen özellikleri getir"""
        features = [e for e in context.active_entities.values() if e.entity_type == EntityType.FEATURE]
        return sorted(features, key=lambda x: x.mentioned_at, reverse=True)[:3]
    
    def _get_recent_categories(self, context) -> List[ContextEntity]:
        """Son bahsedilen kategorileri getir"""
        categories = [e for e in context.active_entities.values() if e.entity_type == EntityType.CATEGORY]
        return sorted(categories, key=lambda x: x.mentioned_at, reverse=True)[:2]
    
    def _extract_recent_topics(self, context) -> List[str]:
        """Son konuları çıkar"""
        topics = []
        
        # From current topic
        if context.current_topic:
            topics.append(context.current_topic)
        
        # From recent conversation turns
        for turn in context.conversation_history[-3:]:
            for entity in turn.extracted_entities:
                if entity.entity_type in [EntityType.PRODUCT, EntityType.CATEGORY]:
                    topic = self._extract_product_name(entity) if entity.entity_type == EntityType.PRODUCT else entity.value
                    if topic not in topics:
                        topics.append(topic)
        
        return topics[:2]  # Return top 2 topics
    
    def _create_fallback_resolution(self, query: str) -> ResolvedQuery:
        """Fallback resolution"""
        return ResolvedQuery(
            original_query=query,
            resolved_query=query,
            query_type=QueryType.AMBIGUOUS,
            resolution_strategy=ResolutionStrategy.CLARIFICATION_REQUEST,
            confidence=0.1,
            used_entities=[],
            context_additions=[],
            explanation="Fallback resolution due to error",
            needs_clarification=True,
            clarification_options=["Lütfen daha spesifik olabilir misiniz?"]
        )
    
    def get_resolver_stats(self) -> Dict[str, Any]:
        """Resolver istatistikleri"""
        return {
            'query_types': [qt.value for qt in QueryType],
            'resolution_strategies': [rs.value for rs in ResolutionStrategy],
            'confidence_thresholds': self.confidence_thresholds,
            'pattern_counts': {
                qt.value: len(patterns) for qt, patterns in self.query_patterns.items()
            }
        }

# Test fonksiyonu
def test_context_aware_query_resolver():
    """Context-aware query resolver test"""
    
    # Setup
    context_manager = ConversationContextManager()
    resolver = ContextAwareQueryResolver(context_manager)
    session_id = "test_session_456"
    
    print("🔍 Context-Aware Query Resolver Test:")
    print("=" * 50)
    
    # Setup context with some conversation history
    context_manager.add_conversation_turn(
        session_id,
        "Siyah dantelli gecelik arıyorum",
        "Size uygun siyah dantelli gecelikler buldum"
    )
    
    # Test queries
    test_queries = [
        "fiyatı nedir",           # Follow-up
        "bunun özellikleri",      # Implicit reference
        "daha farklı modeller",   # Contextual
        "siyah tüllü gecelik",    # Explicit
        "nasıl",                  # Ambiguous
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        
        resolved = resolver.resolve_ambiguous_query(query, session_id)
        
        print(f"  ✅ Resolved: '{resolved.resolved_query}'")
        print(f"  📊 Type: {resolved.query_type.value}")
        print(f"  🎯 Strategy: {resolved.resolution_strategy.value}")
        print(f"  📈 Confidence: {resolved.confidence:.2f}")
        print(f"  📝 Explanation: {resolved.explanation}")
        
        if resolved.used_entities:
            print(f"  🔗 Used entities: {len(resolved.used_entities)}")
        
        if resolved.context_additions:
            print(f"  ➕ Context additions: {', '.join(resolved.context_additions)}")
        
        if resolved.needs_clarification:
            print(f"  ❓ Needs clarification: {resolved.clarification_options[:2]}")
        
        # Test follow-up detection
        is_followup = resolver.detect_followup(query, session_id)
        print(f"  🔄 Is follow-up: {is_followup}")
    
    # Test topic change detection
    print(f"\n🔄 Topic change tests:")
    topic_change_queries = [
        "Hamile pijamalarına bakalım",
        "Bu ürünün fiyatı nedir"
    ]
    
    for query in topic_change_queries:
        topic_change = resolver.detect_topic_change(query, session_id)
        print(f"  '{query}' -> Topic change: {topic_change}")
    
    # Stats
    stats = resolver.get_resolver_stats()
    print(f"\n📊 Resolver Stats:")
    print(f"  Query types: {len(stats['query_types'])}")
    print(f"  Resolution strategies: {len(stats['resolution_strategies'])}")
    print(f"  Pattern counts: {stats['pattern_counts']}")

if __name__ == "__main__":
    test_context_aware_query_resolver()