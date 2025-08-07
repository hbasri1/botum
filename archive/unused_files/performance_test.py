#!/usr/bin/env python3
"""
Comprehensive Performance Test Suite
Tests both accuracy and performance metrics
"""

import json
import time
import statistics
import requests
from typing import List, Dict
import concurrent.futures
import threading

class PerformanceTestSuite:
    """Comprehensive performance and accuracy testing"""
    
    def __init__(self, base_url: str = "http://localhost:5004"):
        self.base_url = base_url
        self.results = []
        self.lock = threading.Lock()
    
    def single_request(self, message: str, expected_intent: str = None) -> Dict:
        """Single request with timing"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=5.0  # 5 second timeout
            )
            
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    'message': message,
                    'success': data.get('success', False),
                    'intent': data.get('intent', 'unknown'),
                    'confidence': data.get('confidence', 0),
                    'products_found': data.get('products_found', 0),
                    'processing_time': data.get('processing_time', 0),
                    'total_time': total_time,
                    'expected_intent': expected_intent,
                    'intent_correct': data.get('intent') == expected_intent if expected_intent else None,
                    'response_length': len(data.get('response', '')),
                    'timestamp': time.time()
                }
                
                return result
            else:
                return {
                    'message': message,
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'total_time': total_time,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            return {
                'message': message,
                'success': False,
                'error': str(e),
                'total_time': time.time() - start_time,
                'timestamp': time.time()
            }
    
    def test_accuracy(self) -> Dict:
        """Test accuracy with known inputs"""
        print("🎯 ACCURACY TESTS")
        print("=" * 50)
        
        test_cases = [
            # Basic intents
            ("merhaba", "greeting"),
            ("teşekkürler", "thanks"),
            ("güle güle", "goodbye"),
            ("iyi günler", "greeting"),  # Context dependent
            
            # Business info
            ("telefon numaranız", "phone_inquiry"),
            ("iade var mı", "return_policy"),
            ("kargo bilgisi", "shipping_info"),
            ("web siteniz", "website_inquiry"),
            
            # Product searches
            ("afrika gecelik", "product_search"),
            ("hamile pijama", "product_search"),
            ("dantelli gecelik", "product_search"),
            ("siyah takım", "product_search"),
            
            # Edge cases
            ("tamamdırS", "unclear"),
            ("asdasd", "unclear"),
            ("", "unclear"),
            
            # Price/stock inquiries
            ("fiyatı nedir", "price_inquiry"),
            ("stok var mı", "stock_inquiry"),
        ]
        
        accuracy_results = []
        
        for message, expected_intent in test_cases:
            print(f"Testing: '{message}' -> Expected: {expected_intent}")
            result = self.single_request(message, expected_intent)
            accuracy_results.append(result)
            
            if result['success']:
                status = "✅" if result['intent_correct'] else "❌"
                print(f"  {status} Got: {result['intent']} ({result['confidence']:.2f}) in {result['total_time']:.3f}s")
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown')}")
            
            time.sleep(0.1)  # Small delay between requests
        
        # Calculate accuracy metrics
        successful_tests = [r for r in accuracy_results if r['success']]
        correct_intents = [r for r in successful_tests if r['intent_correct']]
        
        accuracy_stats = {
            'total_tests': len(test_cases),
            'successful_tests': len(successful_tests),
            'correct_intents': len(correct_intents),
            'accuracy_rate': len(correct_intents) / len(successful_tests) * 100 if successful_tests else 0,
            'success_rate': len(successful_tests) / len(test_cases) * 100,
            'average_response_time': statistics.mean([r['total_time'] for r in successful_tests]) if successful_tests else 0,
            'average_confidence': statistics.mean([r['confidence'] for r in successful_tests]) if successful_tests else 0
        }
        
        print(f"\n📊 ACCURACY RESULTS:")
        print(f"  Total Tests: {accuracy_stats['total_tests']}")
        print(f"  Success Rate: {accuracy_stats['success_rate']:.1f}%")
        print(f"  Intent Accuracy: {accuracy_stats['accuracy_rate']:.1f}%")
        print(f"  Avg Response Time: {accuracy_stats['average_response_time']:.3f}s")
        print(f"  Avg Confidence: {accuracy_stats['average_confidence']:.2f}")
        
        return accuracy_stats
    
    def test_performance(self) -> Dict:
        """Test performance under load"""
        print("\n⚡ PERFORMANCE TESTS")
        print("=" * 50)
        
        # Test different message types
        test_messages = [
            "merhaba",
            "afrika gecelik",
            "hamile pijama arıyorum",
            "telefon numaranız nedir",
            "iade var mı",
            "teşekkürler"
        ]
        
        performance_results = []
        
        # Sequential tests
        print("🔄 Sequential Performance Test...")
        for i in range(10):
            for message in test_messages:
                result = self.single_request(message)
                performance_results.append(result)
                print(f"  Request {len(performance_results)}: {result['total_time']:.3f}s")
        
        # Concurrent tests
        print("\n🚀 Concurrent Performance Test...")
        concurrent_results = []
        
        def concurrent_request(message):
            result = self.single_request(f"{message} {time.time()}")  # Make unique
            with self.lock:
                concurrent_results.append(result)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(20):
                message = test_messages[i % len(test_messages)]
                futures.append(executor.submit(concurrent_request, message))
            
            concurrent.futures.wait(futures)
        
        # Calculate performance metrics
        all_results = performance_results + concurrent_results
        successful_results = [r for r in all_results if r['success']]
        
        if successful_results:
            response_times = [r['total_time'] for r in successful_results]
            processing_times = [r.get('processing_time', 0) for r in successful_results]
            
            performance_stats = {
                'total_requests': len(all_results),
                'successful_requests': len(successful_results),
                'failed_requests': len(all_results) - len(successful_results),
                'success_rate': len(successful_results) / len(all_results) * 100,
                'avg_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)],
                'avg_processing_time': statistics.mean(processing_times),
                'requests_per_second': len(successful_results) / sum(response_times) if sum(response_times) > 0 else 0
            }
        else:
            performance_stats = {
                'total_requests': len(all_results),
                'successful_requests': 0,
                'failed_requests': len(all_results),
                'success_rate': 0,
                'error': 'All requests failed'
            }
        
        print(f"\n📈 PERFORMANCE RESULTS:")
        print(f"  Total Requests: {performance_stats['total_requests']}")
        print(f"  Success Rate: {performance_stats.get('success_rate', 0):.1f}%")
        if 'avg_response_time' in performance_stats:
            print(f"  Avg Response Time: {performance_stats['avg_response_time']:.3f}s")
            print(f"  Median Response Time: {performance_stats['median_response_time']:.3f}s")
            print(f"  95th Percentile: {performance_stats['p95_response_time']:.3f}s")
            print(f"  Min/Max: {performance_stats['min_response_time']:.3f}s / {performance_stats['max_response_time']:.3f}s")
            print(f"  Requests/Second: {performance_stats['requests_per_second']:.2f}")
        
        return performance_stats
    
    def test_edge_cases(self) -> Dict:
        """Test edge cases and error handling"""
        print("\n🔥 EDGE CASE TESTS")
        print("=" * 50)
        
        edge_cases = [
            # Problematic inputs
            ("tamamdırS", "Should handle typos"),
            ("", "Should handle empty input"),
            ("a" * 1000, "Should handle very long input"),
            ("!@#$%^&*()", "Should handle special characters"),
            ("123456789", "Should handle numbers only"),
            
            # Ambiguous inputs
            ("iyi günler", "Context-dependent greeting/goodbye"),
            ("tamam", "Vague acknowledgment"),
            ("evet", "Simple yes"),
            ("hayır", "Simple no"),
            
            # Turkish character issues
            ("dantellı gecelık", "Wrong Turkish characters"),
            ("şık gecelik", "Turkish ş character"),
            ("güzel ürün", "Turkish ü character"),
            
            # Complex queries
            ("afrika gecelik var mı", "Complex product query"),
            ("hamile için rahat pijama arıyorum", "Long descriptive query"),
            ("siyah renkte dantelli gecelik fiyatı nedir", "Multi-intent query"),
        ]
        
        edge_results = []
        
        for message, description in edge_cases:
            print(f"Testing: '{message[:50]}...' - {description}")
            result = self.single_request(message)
            edge_results.append(result)
            
            if result['success']:
                print(f"  ✅ Intent: {result['intent']} ({result['confidence']:.2f}) in {result['total_time']:.3f}s")
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown')}")
        
        # Calculate edge case metrics
        successful_edge = [r for r in edge_results if r['success']]
        
        edge_stats = {
            'total_edge_cases': len(edge_cases),
            'successful_edge_cases': len(successful_edge),
            'edge_success_rate': len(successful_edge) / len(edge_cases) * 100,
            'avg_edge_response_time': statistics.mean([r['total_time'] for r in successful_edge]) if successful_edge else 0,
            'unclear_rate': len([r for r in successful_edge if r['intent'] == 'unclear']) / len(successful_edge) * 100 if successful_edge else 0
        }
        
        print(f"\n🔥 EDGE CASE RESULTS:")
        print(f"  Total Edge Cases: {edge_stats['total_edge_cases']}")
        print(f"  Success Rate: {edge_stats['edge_success_rate']:.1f}%")
        print(f"  Avg Response Time: {edge_stats['avg_edge_response_time']:.3f}s")
        print(f"  Unclear Rate: {edge_stats['unclear_rate']:.1f}%")
        
        return edge_stats
    
    def run_comprehensive_test(self) -> Dict:
        """Run all tests and generate comprehensive report"""
        print("🚀 COMPREHENSIVE PERFORMANCE & ACCURACY TEST SUITE")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test suites
        accuracy_stats = self.test_accuracy()
        performance_stats = self.test_performance()
        edge_stats = self.test_edge_cases()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        comprehensive_report = {
            'test_timestamp': time.time(),
            'total_test_time': total_time,
            'accuracy_stats': accuracy_stats,
            'performance_stats': performance_stats,
            'edge_case_stats': edge_stats,
            'overall_grade': self._calculate_overall_grade(accuracy_stats, performance_stats, edge_stats)
        }
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        print(f"🎯 Accuracy: {accuracy_stats.get('accuracy_rate', 0):.1f}%")
        print(f"⚡ Avg Response Time: {performance_stats.get('avg_response_time', 0):.3f}s")
        print(f"🔥 Edge Case Success: {edge_stats.get('edge_success_rate', 0):.1f}%")
        print(f"📈 Overall Grade: {comprehensive_report['overall_grade']}")
        print(f"⏱️ Total Test Time: {total_time:.2f}s")
        
        # Save detailed report
        with open('comprehensive_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detailed report saved to: comprehensive_test_report.json")
        
        return comprehensive_report
    
    def _calculate_overall_grade(self, accuracy_stats: Dict, performance_stats: Dict, edge_stats: Dict) -> str:
        """Calculate overall system grade"""
        accuracy_score = accuracy_stats.get('accuracy_rate', 0)
        performance_score = 100 - min(performance_stats.get('avg_response_time', 0) * 100, 100)  # Penalty for slow responses
        edge_score = edge_stats.get('edge_success_rate', 0)
        
        overall_score = (accuracy_score * 0.4 + performance_score * 0.3 + edge_score * 0.3)
        
        if overall_score >= 90:
            return "A+ (Excellent)"
        elif overall_score >= 80:
            return "A (Very Good)"
        elif overall_score >= 70:
            return "B (Good)"
        elif overall_score >= 60:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"

def main():
    """Run comprehensive test suite"""
    # Test both local and public endpoints
    endpoints = [
        ("Local", "http://localhost:5004"),
        # ("Public", "https://25a17a363c2c.ngrok-free.app")  # Uncomment to test public endpoint
    ]
    
    for name, url in endpoints:
        print(f"\n🌐 Testing {name} Endpoint: {url}")
        print("=" * 80)
        
        try:
            test_suite = PerformanceTestSuite(url)
            report = test_suite.run_comprehensive_test()
            
            print(f"\n✅ {name} endpoint test completed successfully!")
            
        except Exception as e:
            print(f"\n❌ {name} endpoint test failed: {e}")

if __name__ == "__main__":
    main()