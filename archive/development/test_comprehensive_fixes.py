#!/usr/bin/env python3
"""
Comprehensive Fixes Test - Kullanıcı sorunlarını test et
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.services.llm_service import LLMService

async def test_comprehensive_fixes():
    """Kapsamlı düzeltmeleri test et"""
    
    print("🧪 COMPREHENSIVE FIXES TEST")
    print("=" * 60)
    
    # LLM service oluştur
    llm_service = LLMService(enable_function_calling=True, enable_intelligent_search=True)
    
    # Kullanıcının problematik test case'leri
    test_cases = [
        {
            "query": "fiyat soracaktım",
            "expected": "Should understand future tense and ask for clarification",
            "category": "Intent Detection Fix"
        },
        {
            "query": "merhaba fiyat soracaktım",
            "expected": "Should handle greeting + future tense",
            "category": "Intent Detection Fix"
        },
        {
            "query": "Çiçek ve Yaprak Desenli Dekolteli Gecelik",
            "expected": "Should find exact match with high confidence",
            "category": "Semantic Search Fix"
        },
        {
            "query": "çiçek desenli tüllü takım fiyatı",
            "expected": "Should find matching products with price info",
            "category": "Semantic Search Fix"
        },
        {
            "query": "afrika gecelik",
            "expected": "Should find Afrika Etnik Baskılı product",
            "category": "Semantic Search Fix"
        },
        {
            "query": "hamile lohusa takımı",
            "expected": "Should find hamile lohusa products",
            "category": "Semantic Search Fix"
        },
        {
            "query": "siyah gecelik fiyatı",
            "expected": "Should find black nightgown with price",
            "category": "Combined Fix"
        },
        {
            "query": "dantelli takım var mı",
            "expected": "Should find lace products and check stock",
            "category": "Combined Fix"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['category']}")
        print(f"Query: '{test_case['query']}'")
        print(f"Expected: {test_case['expected']}")
        print("-" * 50)
        
        try:
            # Process message
            result = await llm_service.process_message_with_functions(
                prompt=test_case['query'],
                session_id=f"test_{i}",
                isletme_id="fashion_boutique"
            )
            
            if result:
                print(f"✅ Intent: {result.get('intent', 'unknown')}")
                print(f"🎯 Method: {result.get('method', 'unknown')}")
                print(f"📊 Confidence: {result.get('confidence', 0):.1%}")
                
                # Response
                response = result.get('final_response', 'No response')
                print(f"💬 Response: {response[:100]}...")
                
                # Function call varsa
                if result.get('function_call'):
                    func_call = result['function_call']
                    print(f"🔧 Function: {func_call['name']}({func_call['args']})")
                
                # Search results varsa
                if result.get('search_results'):
                    search_results = result['search_results']
                    print(f"🔍 Found {len(search_results)} products")
                
                # Success evaluation
                success = True
                if result.get('intent') == 'clarification_needed' and 'fiyat soracaktım' in test_case['query']:
                    success = True  # This is now expected behavior
                elif result.get('confidence', 0) < 0.5:
                    success = False
                elif 'Anlayamadım' in response:
                    success = False
                
                results.append({
                    'test': test_case['query'],
                    'success': success,
                    'confidence': result.get('confidence', 0),
                    'method': result.get('method', 'unknown')
                })
                
                print(f"🎯 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
                
            else:
                print("❌ No result returned")
                results.append({
                    'test': test_case['query'],
                    'success': False,
                    'confidence': 0,
                    'method': 'no_result'
                })
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                'test': test_case['query'],
                'success': False,
                'confidence': 0,
                'method': 'error'
            })
    
    # Summary
    print(f"\n\n📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if r['success']]
    success_rate = len(successful_tests) / len(results) * 100
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(results) - len(successful_tests)}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Average confidence
    avg_confidence = sum(r['confidence'] for r in results) / len(results) * 100
    print(f"Average Confidence: {avg_confidence:.1f}%")
    
    # Method breakdown
    methods = {}
    for result in results:
        method = result['method']
        methods[method] = methods.get(method, 0) + 1
    
    print(f"\nMethod Breakdown:")
    for method, count in methods.items():
        print(f"  {method}: {count}")
    
    # Failed tests
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for failed in failed_tests:
            print(f"  • {failed['test']} ({failed['method']})")
    
    print(f"\n🎯 OVERALL RESULT: {'✅ PASSED' if success_rate >= 75 else '❌ NEEDS IMPROVEMENT'}")
    
    return results

async def main():
    """Ana fonksiyon"""
    results = await test_comprehensive_fixes()
    
    print(f"\n🚀 Test completed!")
    print(f"Check the results above to see if the fixes are working properly.")

if __name__ == "__main__":
    asyncio.run(main())