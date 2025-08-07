#!/usr/bin/env python3
"""
Final Comprehensive Test Suite
Tests the fixed system thoroughly
"""

import requests
import time
import json

def test_fixed_system():
    """Test the fixed system comprehensively"""
    base_url = "http://localhost:5004"
    
    print("🚀 FINAL COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Test cases with expected results
    test_cases = [
        # Basic intents
        ("merhaba", "greeting", "Should greet properly"),
        ("sağol", "thanks", "Should thank properly"),
        ("teşekkürler", "thanks", "Should thank properly"),
        ("güle güle", "goodbye", "Should say goodbye"),
        ("iyi günler", "greeting", "Should greet (context dependent)"),
        
        # Business info
        ("telefon numaranız", "phone_inquiry", "Should provide phone"),
        ("iade var mı", "return_policy", "Should provide return policy"),
        ("kargo bilgisi", "shipping_info", "Should provide shipping info"),
        ("web siteniz", "website_inquiry", "Should provide website"),
        
        # Product searches
        ("afrika gecelik", "product_search", "Should find 1 Afrika gecelik"),
        ("hamile pijama", "product_search", "Should find hamile pijama products"),
        ("dantelli gecelik", "product_search", "Should find dantelli gecelik products"),
        ("siyah takım", "product_search", "Should find siyah takım products"),
        
        # Edge cases
        ("tamamdırS", "unclear", "Should handle typos"),
        ("asdasd", "unclear", "Should handle nonsense"),
        ("", "empty", "Should handle empty input"),
        
        # Follow-up scenarios
        ("afrika gecelik", "product_search", "Initial search"),
        ("1", "followup", "Should select first product"),
        ("fiyatı", "followup", "Should show price"),
    ]
    
    results = []
    total_time = 0
    
    for i, (message, expected_intent, description) in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {description}")
        print(f"👤 Input: '{message}'")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/chat",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=5.0
            )
            
            test_time = time.time() - start_time
            total_time += test_time
            
            if response.status_code == 200:
                data = response.json()
                
                intent = data.get('intent', 'unknown')
                confidence = data.get('confidence', 0)
                products_found = data.get('products_found', 0)
                response_text = data.get('response', '')
                
                # Check if intent matches expected
                intent_correct = intent == expected_intent
                status = "✅" if intent_correct else "❌"
                
                print(f"  {status} Got: {intent} (expected: {expected_intent})")
                print(f"  📊 Confidence: {confidence:.2f}")
                print(f"  🛍️ Products: {products_found}")
                print(f"  ⏱️ Time: {test_time:.3f}s")
                print(f"  📝 Response: {response_text[:80]}...")
                
                # Special checks
                if message == "afrika gecelik" and products_found != 1:
                    print(f"  ⚠️ WARNING: Expected 1 product, got {products_found}")
                
                if message == "sağol" and "karışıklık" in response_text:
                    print(f"  ❌ CRITICAL: Still showing confusion message!")
                
                results.append({
                    'message': message,
                    'expected_intent': expected_intent,
                    'actual_intent': intent,
                    'correct': intent_correct,
                    'confidence': confidence,
                    'products_found': products_found,
                    'time': test_time,
                    'response_length': len(response_text)
                })
                
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                results.append({
                    'message': message,
                    'error': f"HTTP {response.status_code}",
                    'correct': False,
                    'time': test_time
                })
                
        except Exception as e:
            test_time = time.time() - start_time
            total_time += test_time
            print(f"  ❌ Exception: {e}")
            results.append({
                'message': message,
                'error': str(e),
                'correct': False,
                'time': test_time
            })
        
        # Small delay between tests
        time.sleep(0.1)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = len([r for r in results if r.get('correct', False)])
    failed_tests = total_tests - successful_tests
    
    print(f"📈 Total Tests: {total_tests}")
    print(f"✅ Successful: {successful_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    print(f"⏱️ Total Time: {total_time:.2f}s")
    print(f"⚡ Average Time: {total_time/total_tests:.3f}s")
    
    # Performance analysis
    successful_results = [r for r in results if r.get('correct', False)]
    if successful_results:
        times = [r['time'] for r in successful_results]
        confidences = [r.get('confidence', 0) for r in successful_results]
        
        print(f"\n⚡ Performance Analysis:")
        print(f"   Fastest: {min(times):.3f}s")
        print(f"   Slowest: {max(times):.3f}s")
        print(f"   Average Confidence: {sum(confidences)/len(confidences):.2f}")
    
    # Failed tests details
    failed_results = [r for r in results if not r.get('correct', False)]
    if failed_results:
        print(f"\n❌ Failed Tests:")
        for result in failed_results:
            expected = result.get('expected_intent', 'unknown')
            actual = result.get('actual_intent', 'error')
            print(f"   • '{result['message']}': expected {expected}, got {actual}")
    
    # Critical issues check
    critical_issues = []
    
    # Check for "sağol" confusion issue
    sagol_results = [r for r in results if r['message'] == 'sağol']
    if sagol_results and not sagol_results[0].get('correct', False):
        critical_issues.append("'sağol' still not working correctly")
    
    # Check for Afrika gecelik issue
    afrika_results = [r for r in results if r['message'] == 'afrika gecelik']
    if afrika_results and afrika_results[0].get('products_found', 0) != 1:
        critical_issues.append("'afrika gecelik' not returning single product")
    
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"   • {issue}")
    else:
        print(f"\n🎉 NO CRITICAL ISSUES FOUND!")
    
    # Overall grade
    if successful_tests / total_tests >= 0.95:
        grade = "A+ (Excellent)"
    elif successful_tests / total_tests >= 0.90:
        grade = "A (Very Good)"
    elif successful_tests / total_tests >= 0.80:
        grade = "B (Good)"
    elif successful_tests / total_tests >= 0.70:
        grade = "C (Fair)"
    else:
        grade = "D (Needs Improvement)"
    
    print(f"\n🏆 Overall Grade: {grade}")
    
    # Save detailed results
    with open('final_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.time(),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': (successful_tests/total_tests)*100,
            'total_time': total_time,
            'average_time': total_time/total_tests,
            'grade': grade,
            'critical_issues': critical_issues,
            'detailed_results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed results saved to: final_test_results.json")
    
    return successful_tests / total_tests >= 0.90

if __name__ == "__main__":
    success = test_fixed_system()
    if success:
        print("\n🎉 SYSTEM READY FOR PRODUCTION!")
    else:
        print("\n⚠️ SYSTEM NEEDS MORE WORK!")