#!/usr/bin/env python3
"""
Comprehensive Intelligent Search System Test
"""

import asyncio
import sys
import os
sys.path.append('orchestrator/services')

from intelligent_search_engine import IntelligentSearchEngine
from conversation_context_manager import ConversationContextManager
from context_aware_query_resolver import ContextAwareQueryResolver
from contextual_intent_detector import ContextualIntentDetector
from confidence_based_presenter import ConfidenceBasedPresenter
from result_fusion_engine import ResultFusionEngine
from llm_service import LLMService

async def test_complete_intelligent_search_system():
    """Complete intelligent search system test"""
    
    print("🚀 Comprehensive Intelligent Search System Test")
    print("=" * 60)
    
    # Test data
    test_products = [
        {
            'id': 1,
            'name': 'Afrika Etnik Baskılı Dantelli Gecelik',
            'category': 'İç Giyim',
            'color': 'BEJ',
            'price': 565.44,
            'description': 'Özel etnik desenli dantelli gecelik'
        },
        {
            'id': 2,
            'name': 'Dantelli Önü Düğmeli Hamile Lohusa Gecelik',
            'category': 'İç Giyim',
            'color': 'EKRU',
            'price': 1632.33,
            'description': 'Hamile ve lohusa anneler için özel tasarım'
        },
        {
            'id': 3,
            'name': 'Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı',
            'category': 'İç Giyim',
            'color': 'SİYAH',
            'price': 1821.33,
            'description': 'Şık dekolteli takım'
        },
        {
            'id': 4,
            'name': 'Siyah Tüllü Askılı Gecelik',
            'category': 'İç Giyim',
            'color': 'SİYAH',
            'price': 890.50,
            'description': 'Zarif tüllü gecelik'
        }
    ]
    
    # Initialize components
    search_engine = IntelligentSearchEngine()
    context_manager = ConversationContextManager()
    query_resolver = ContextAwareQueryResolver(context_manager)
    intent_detector = ContextualIntentDetector()
    presenter = ConfidenceBasedPresenter()
    fusion_engine = ResultFusionEngine()
    
    session_id = "test_session_comprehensive"
    
    print("\n🔍 Test Scenario 1: Initial Product Search")
    print("-" * 40)
    
    # Test 1: Initial search
    query1 = "siyah gecelik arıyorum"
    print(f"Query: '{query1}'")
    
    # Detect intent
    context = context_manager.get_context(session_id)
    intent = intent_detector.detect_intent(query1, context)
    print(f"Intent: {intent.intent.value} (confidence: {intent.confidence:.2f})")
    
    # Resolve query
    resolved = query_resolver.resolve_ambiguous_query(query1, session_id)
    print(f"Resolved query: '{resolved.resolved_query}'")
    
    # Search
    search_result = await search_engine.search(resolved.resolved_query, test_products, limit=3)
    print(f"Found {len(search_result.matches)} matches in {search_result.total_time_ms}ms")
    
    # Add to context
    context_manager.add_conversation_turn(session_id, query1, "Siyah gecelikler buldum", intent.intent.value)
    
    # Present results
    if search_result.matches:
        from result_fusion_engine import FusedResult
        fused_results = []
        for match in search_result.matches:
            fused_result = FusedResult(
                product=match.product,
                final_score=match.score,
                confidence=match.confidence,
                method_scores={match.method: match.score},
                method_ranks={match.method: 1},
                fusion_explanation=match.explanation,
                validation_score=0.8,
                feature_matches=match.feature_matches or []
            )
            fused_results.append(fused_result)
        
        presentation = presenter.present_results(fused_results, search_result.alternatives, 
                                               search_result.overall_confidence, query1)
        formatted = presenter.format_for_display(presentation)
        print(f"Presentation:\n{formatted}")
    
    print("\n🔄 Test Scenario 2: Follow-up Question")
    print("-" * 40)
    
    # Test 2: Follow-up question
    query2 = "fiyatı nedir?"
    print(f"Query: '{query2}'")
    
    # Detect intent with context
    context = context_manager.get_context(session_id)
    intent2 = intent_detector.detect_intent(query2, context)
    print(f"Intent: {intent2.intent.value} (confidence: {intent2.confidence:.2f})")
    
    # Check if follow-up
    is_followup = query_resolver.detect_followup(query2, session_id)
    print(f"Is follow-up: {is_followup}")
    
    # Resolve with context
    resolved2 = query_resolver.resolve_ambiguous_query(query2, session_id)
    print(f"Resolved query: '{resolved2.resolved_query}'")
    
    print("\n🔄 Test Scenario 3: Topic Change")
    print("-" * 40)
    
    # Test 3: Topic change
    query3 = "Hamile pijamalarına bakalım"
    print(f"Query: '{query3}'")
    
    # Detect topic change
    topic_change = query_resolver.detect_topic_change(query3, session_id)
    print(f"Topic change detected: {topic_change}")
    
    # Search with new topic
    search_result3 = await search_engine.search(query3, test_products, limit=3)
    print(f"Found {len(search_result3.matches)} matches")
    
    for i, match in enumerate(search_result3.matches, 1):
        print(f"  {i}. {match.product['name']} (score: {match.score:.3f})")
    
    print("\n🧠 Test Scenario 4: LLM Service Integration")
    print("-" * 40)
    
    # Test 4: Full LLM service integration
    llm_service = LLMService(enable_intelligent_search=True)
    
    test_queries = [
        "siyah gecelik",
        "fiyatı ne kadar?",
        "daha farklı modeller var mı?"
    ]
    
    for query in test_queries:
        print(f"\nLLM Query: '{query}'")
        try:
            result = await llm_service.process_message_with_functions(query, session_id, "fashion_boutique")
            if result:
                print(f"Method: {result.get('method', 'unknown')}")
                print(f"Intent: {result.get('intent', 'unknown')}")
                if 'intelligent_search_result' in result:
                    search_info = result['intelligent_search_result']
                    print(f"Matches: {search_info.get('matches_found', 0)}")
                    print(f"Confidence: {search_info.get('overall_confidence', 0):.2f}")
                if 'final_response' in result:
                    print(f"Response: {result['final_response'][:100]}...")
            else:
                print("No result returned")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\n📊 System Performance Summary")
    print("-" * 40)
    
    # Get stats from all components
    search_stats = search_engine.get_search_stats()
    context_stats = context_manager.get_manager_stats()
    resolver_stats = query_resolver.get_resolver_stats()
    intent_stats = intent_detector.get_detector_stats()
    presenter_stats = presenter.get_presenter_stats()
    
    print(f"Search Engine:")
    print(f"  Available methods: {len(search_stats['available_methods'])}")
    print(f"  Method weights: {len(search_stats['method_weights'])}")
    
    print(f"Context Manager:")
    print(f"  Active sessions: {context_stats['active_sessions']}")
    print(f"  Total turns: {context_stats['total_conversation_turns']}")
    print(f"  Active entities: {context_stats['total_active_entities']}")
    
    print(f"Query Resolver:")
    print(f"  Query types: {len(resolver_stats['query_types'])}")
    print(f"  Resolution strategies: {len(resolver_stats['resolution_strategies'])}")
    
    print(f"Intent Detector:")
    print(f"  Supported intents: {len(intent_stats['supported_intents'])}")
    print(f"  Total patterns: {intent_stats['total_patterns']}")
    
    print(f"Presenter:")
    print(f"  Confidence levels: {len(presenter_stats['confidence_levels'])}")
    print(f"  Presentation modes: {len(presenter_stats['presentation_modes'])}")
    
    print("\n✅ Comprehensive test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_complete_intelligent_search_system())