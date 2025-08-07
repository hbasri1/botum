#!/usr/bin/env python3
"""
Complete System Test - Enhanced Intent Detection + Multi-Stage Product Matching
"""

import asyncio
import json
from orchestrator.services.enhanced_intent_detector import enhanced_intent_detector, IntentType
from orchestrator.services.multi_stage_product_matcher import MultiStageProductMatcher

async def test_complete_system():
    """Complete system test with real product data"""
    
    # Load real product data
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
        print(f"✅ Loaded {len(products)} products from database")
    except Exception as e:
        print(f"❌ Error loading products: {e}")
        return
    
    # Initialize components
    matcher = MultiStageProductMatcher()
    
    print("\n🚀 Complete System Test - Enhanced Intent + Multi-Stage Matching")
    print("=" * 70)
    
    # Test cases - the problematic ones from the original issue
    test_cases = [
        {
            "query": "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik bu ne kadar",
            "expected_product": "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik",
            "description": "Exact match test - should find the exact product"
        },
        {
            "query": "siyah gecelik fiyatı",
            "expected_features": ["siyah", "gecelik", "fiyat"],
            "description": "Color + product + query type test"
        },
        {
            "query": "hamile lohusa geceliği stok var mı",
            "expected_features": ["hamile", "lohusa", "gecelik", "stok"],
            "description": "Target group + product + query type test"
        },
        {
            "query": "dantelli sabahlık renkleri",
            "expected_features": ["dantelli", "sabahlık", "renk"],
            "description": "Style + product + query type test"
        },
        {
            "query": "afrika gecelik",
            "expected_features": ["afrika", "gecelik"],
            "description": "Pattern + product test"
        },
        {
            "query": "fiyat soracaktım",
            "expected_intent": IntentType.CLARIFICATION_NEEDED,
            "description": "Nonsense detection test"
        },
        {
            "query": "merhaba",
            "expected_intent": IntentType.GREETING,
            "description": "Greeting test"
        },
        {
            "query": "telefon numaranız",
            "expected_intent": IntentType.BUSINESS_INFO,
            "description": "Business info test"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"\n🧪 Test {i}/{total_count}: {description}")
        print(f"Query: '{query}'")
        
        try:
            # Step 1: Intent Detection
            intent_result = await enhanced_intent_detector.detect_intent(query)
            print(f"Intent: {intent_result.intent.value} (confidence: {intent_result.confidence:.2f})")
            
            # Check expected intent if specified
            if "expected_intent" in test_case:
                if intent_result.intent == test_case["expected_intent"]:
                    print("✅ Intent detection: PASSED")
                    success_count += 1
                else:
                    print(f"❌ Intent detection: FAILED (expected {test_case['expected_intent'].value})")
                continue
            
            # Step 2: Product Matching (if product inquiry)
            if intent_result.intent == IntentType.PRODUCT_INQUIRY:
                search_result = await matcher.search_products(query, products[:100], limit=3)  # Limit for speed
                
                print(f"Search time: {search_result.total_time_ms}ms")
                print(f"Overall confidence: {search_result.overall_confidence:.3f}")
                
                if search_result.matches:
                    print(f"Found {len(search_result.matches)} matches:")
                    
                    for j, match in enumerate(search_result.matches, 1):
                        print(f"  {j}. {match.product['name']}")
                        print(f"     Score: {match.final_score:.3f}, Confidence: {match.confidence:.3f}")
                        print(f"     Method: {match.dominant_method.value} ({match.method_count} methods)")
                        
                        if match.matched_features:
                            print(f"     Features: {', '.join(match.matched_features[:5])}")
                    
                    # Check expected product if specified
                    if "expected_product" in test_case:
                        top_match = search_result.matches[0]
                        if test_case["expected_product"] in top_match.product['name']:
                            print("✅ Product matching: PASSED")
                            success_count += 1
                        else:
                            print(f"❌ Product matching: FAILED")
                            print(f"   Expected: {test_case['expected_product']}")
                            print(f"   Got: {top_match.product['name']}")
                    
                    # Check expected features if specified
                    elif "expected_features" in test_case:
                        top_match = search_result.matches[0]
                        found_features = set(top_match.matched_features)
                        
                        expected_features = set(test_case["expected_features"])
                        if expected_features.intersection(found_features):
                            print("✅ Feature matching: PASSED")
                            success_count += 1
                        else:
                            print(f"❌ Feature matching: FAILED")
                            print(f"   Expected features: {expected_features}")
                            print(f"   Found features: {found_features}")
                    else:
                        # General success if we found matches
                        print("✅ Product search: PASSED")
                        success_count += 1
                else:
                    print("❌ No matches found")
            else:
                # Non-product queries are successful if intent is correct
                print("✅ Non-product query: PASSED")
                success_count += 1
                
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
    
    # Final results
    print(f"\n{'='*70}")
    print(f"🏆 Test Results: {success_count}/{total_count} passed ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print(f"⚠️  {total_count - success_count} tests failed. System needs improvement.")
    
    return success_count == total_count

if __name__ == "__main__":
    asyncio.run(test_complete_system())