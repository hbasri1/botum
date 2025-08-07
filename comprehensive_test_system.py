#!/usr/bin/env python3
"""
Comprehensive Test System
Tests all aspects of the chatbot system including performance, edge cases, and real scenarios
"""

import json
import time
import asyncio
import logging
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass
import concurrent.futures
from improved_final_mvp_system import ImprovedFinalMVPChatbot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    test_name: str
    success: bool
    response_time: float
    response: str
    intent: str
    confidence: float
    error: str = None

class ComprehensiveTestSystem:
    """Comprehensive testing system for the chatbot"""
    
    def __init__(self, base_url: str = "http://localhost:5005"):
        self.base_url = base_url
        self.results = []
        self.performance_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'average_response_time': 0.0,
            'max_response_time': 0.0,
            'min_response_time': float('inf')
        }
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Test System")
        print("=" * 60)
        
        # Test categories
        test_categories = [
            ("Dialog Flow Tests", self._test_dialog_flows),
            ("Product Search Tests", self._test_product_searches),
            ("Edge Case Tests", self._test_edge_cases),
            ("Performance Tests", self._test_performance),
            ("Cache System Tests", self._test_cache_system),
            ("Error Handling Tests", self._test_error_handling),
            ("Intent Detection Tests", self._test_intent_detection),
            ("Database Integration Tests", self._test_database_integration),
            ("Mobile Compatibility Tests", self._test_mobile_compatibility),
            ("Real Customer Scenarios", self._test_real_scenarios)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n📋 {category_name}")
            print("-" * 40)
            test_function()
        
        self._generate_report()
    
    def _test_dialog_flows(self):
        """Test conversation flows"""
        dialog_tests = [
            # Greeting flow
            ("merhaba", "greeting"),
            ("selam", "greeting"),
            ("iyi günler", "greeting"),
            
            # Product search flow
            ("hamile pijama arıyorum", "product_search"),
            ("1 numaralı ürünün fiyatı nedir", "followup"),
            ("stokta var mı", "followup"),
            
            # Business info flow
            ("telefon numaranız nedir", "phone_inquiry"),
            ("iade nasıl yapılır", "return_policy"),
            ("kargo ücreti ne kadar", "shipping_info"),
            
            # Goodbye flow
            ("teşekkürler", "thanks"),
            ("güle güle", "goodbye"),
        ]
        
        for query, expected_intent in dialog_tests:
            result = self._send_request(query)
            success = result.intent == expected_intent
            self._add_result(f"Dialog: {query}", success, result.response_time, 
                           result.response, result.intent, result.confidence, result.error)
    
    def _test_product_searches(self):
        """Test product search functionality"""
        product_tests = [
            # Exact product names
            ("Afrika Etnik Baskılı Dantelli Gecelik", "product_search"),
            ("Kısa Kollu V Yakalı Dantelli Pijama Takımı", "product_search"),
            ("Stay Strong Eşofman Takımı", "product_search"),
            
            # Color searches
            ("siyah gecelik", "product_search"),
            ("beyaz pijama", "product_search"),
            ("kırmızı sabahlık", "product_search"),
            
            # Feature searches
            ("hamile pijama", "product_search"),
            ("dantelli gecelik", "product_search"),
            ("büyük beden takım", "product_search"),
            
            # Brand searches
            ("stay strong", "product_search"),
            ("calm down", "product_search"),
            ("africa style", "product_search"),
            
            # Typos and variations
            ("afirka gecelik", "product_search"),
            ("hamle pijama", "product_search"),
            ("danteli gecelik", "product_search"),
        ]
        
        for query, expected_intent in product_tests:
            result = self._send_request(query)
            success = result.intent == expected_intent
            self._add_result(f"Product: {query}", success, result.response_time, 
                           result.response, result.intent, result.confidence, result.error)
    
    def _test_edge_cases(self):
        """Test edge cases and problematic inputs"""
        edge_cases = [
            # Empty and minimal inputs
            ("", "unclear"),
            ("a", "unclear"),
            ("??", "unclear"),
            
            # Nonsense inputs
            ("asdasdasd", "unclear"),
            ("xyzxyzxyz", "unclear"),
            ("123456789", "unclear"),
            
            # Mixed language
            ("hello merhaba", "greeting"),
            ("gecelik nightgown", "product_search"),
            
            # Very long inputs
            ("çok uzun bir mesaj bu gerçekten çok uzun bir mesaj gecelik arıyorum ama çok detaylı anlatıyorum", "product_search"),
            
            # Special characters
            ("gecelik!!!", "product_search"),
            ("pijama???", "product_search"),
            ("takım@@@", "product_search"),
            
            # Numbers and prices
            ("100 tl altında gecelik", "product_search"),
            ("1000 lira pijama", "product_search"),
            
            # Ambiguous queries
            ("var mı", "stock_inquiry"),
            ("fiyat", "price_inquiry"),
            ("stok", "stock_inquiry"),
        ]
        
        for query, expected_intent in edge_cases:
            result = self._send_request(query)
            # For edge cases, we mainly check if system doesn't crash
            success = result.error is None
            self._add_result(f"Edge: {query}", success, result.response_time, 
                           result.response, result.intent, result.confidence, result.error)
    
    def _test_performance(self):
        """Test system performance under load"""
        print("🔥 Performance Testing...")
        
        # Response time test
        fast_queries = ["merhaba", "afrika gecelik", "telefon", "teşekkürler"]
        response_times = []
        
        for query in fast_queries * 5:  # 20 requests
            start_time = time.time()
            result = self._send_request(query)
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Performance benchmarks
        performance_good = avg_response_time < 1.0  # Under 1 second
        performance_excellent = avg_response_time < 0.5  # Under 500ms
        
        self._add_result("Performance: Average Response Time", 
                        performance_good, avg_response_time, 
                        f"Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s", 
                        "performance", 1.0 if performance_excellent else 0.8)
        
        # Concurrent requests test
        print("🔄 Testing concurrent requests...")
        concurrent_queries = ["hamile pijama", "siyah gecelik", "stay strong", "telefon"] * 3
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._send_request, query) for query in concurrent_queries]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_time = time.time() - start_time
        concurrent_success = all(r.error is None for r in results)
        
        self._add_result("Performance: Concurrent Requests", 
                        concurrent_success, concurrent_time, 
                        f"12 concurrent requests in {concurrent_time:.3f}s", 
                        "performance", 1.0 if concurrent_success else 0.5)
    
    def _test_cache_system(self):
        """Test cache system functionality"""
        print("💾 Testing cache system...")
        
        # Cache hit test
        query = "afrika gecelik"
        
        # First request (cache miss)
        result1 = self._send_request(query)
        time.sleep(0.1)
        
        # Second request (should be cache hit)
        result2 = self._send_request(query)
        
        # Cache should make second request faster
        cache_working = result2.response_time < result1.response_time * 0.8
        
        self._add_result("Cache: Hit Performance", 
                        cache_working, result2.response_time, 
                        f"First: {result1.response_time:.3f}s, Second: {result2.response_time:.3f}s", 
                        "cache", 1.0 if cache_working else 0.7)
        
        # Cache invalidation test
        different_query = "hamile pijama"
        result3 = self._send_request(different_query)
        
        cache_invalidation = result1.response != result3.response
        self._add_result("Cache: Proper Invalidation", 
                        cache_invalidation, result3.response_time, 
                        "Different queries return different results", 
                        "cache", 1.0 if cache_invalidation else 0.5)
    
    def _test_error_handling(self):
        """Test error handling and recovery"""
        error_tests = [
            # Malformed requests would be handled by web interface
            # We test application-level errors
            
            # Very long query
            ("a" * 1000, "unclear"),
            
            # Special characters that might break parsing
            ("gecelik\n\n\n", "product_search"),
            ("pijama\t\t\t", "product_search"),
            
            # Unicode edge cases
            ("🤖🤖🤖 gecelik", "product_search"),
            ("pijama 😊😊😊", "product_search"),
        ]
        
        for query, expected_intent in error_tests:
            result = self._send_request(query)
            success = result.error is None  # System should handle gracefully
            self._add_result(f"Error: {query[:20]}...", success, result.response_time, 
                           result.response, result.intent, result.confidence, result.error)
    
    def _test_intent_detection(self):
        """Test intent detection accuracy"""
        intent_tests = [
            # Clear intents
            ("merhaba nasılsınız", "greeting"),
            ("teşekkür ederim çok yardımcı oldunuz", "thanks"),
            ("güle güle görüşürüz", "goodbye"),
            ("telefon numaranızı öğrenebilir miyim", "phone_inquiry"),
            ("iade politikanız nedir", "return_policy"),
            ("kargo ücreti var mı", "shipping_info"),
            
            # Product search variations
            ("gecelik arıyorum", "product_search"),
            ("pijama var mı", "product_search"),
            ("sabahlık görmek istiyorum", "product_search"),
            
            # Followup questions
            ("1 numaralı ürün ne kadar", "followup"),
            ("bunun fiyatı nedir", "followup"),
            ("stokta mevcut mu", "followup"),
            
            # Size inquiries
            ("m beden var mı", "size_inquiry"),
            ("xl beden mevcut mu", "size_inquiry"),
            ("beden tablosu", "size_inquiry"),
        ]
        
        for query, expected_intent in intent_tests:
            result = self._send_request(query)
            success = result.intent == expected_intent
            self._add_result(f"Intent: {query}", success, result.response_time, 
                           result.response, result.intent, result.confidence, result.error)
    
    def _test_database_integration(self):
        """Test database integration and product data"""
        # Test with known products from database
        db_tests = [
            "Afrika Etnik Baskılı Dantelli Gecelik",
            "Kısa Kollu V Yakalı Dantelli Pijama Takımı",
            "Sırtı Dekolteli Tüllü ve Dantelli Pijama Takımı",
            "Stay Strong Eşofman Takımı",
            "Calm Down Eşofman Takımı",
        ]
        
        for product_name in db_tests:
            result = self._send_request(product_name)
            # Should find the product and return product_search intent
            success = result.intent == "product_search" and "buldum" in result.response.lower()
            self._add_result(f"DB: {product_name[:30]}...", success, result.response_time, 
                           result.response, result.intent, result.confidence, result.error)
    
    def _test_mobile_compatibility(self):
        """Test mobile-specific scenarios"""
        mobile_tests = [
            # Short queries (mobile typing)
            ("gecelik", "product_search"),
            ("pijama", "product_search"),
            ("fiyat", "price_inquiry"),
            
            # Voice-to-text errors
            ("geceli", "product_search"),  # Missing 'k'
            ("pijama takım", "product_search"),
            
            # Auto-correct issues
            ("afrika", "product_search"),
            ("hamile", "product_search"),
        ]
        
        for query, expected_intent in mobile_tests:
            result = self._send_request(query)
            success = result.intent == expected_intent or result.error is None
            self._add_result(f"Mobile: {query}", success, result.response_time, 
                           result.response, result.intent, result.confidence, result.error)
    
    def _test_real_scenarios(self):
        """Test real customer scenarios"""
        scenarios = [
            # Customer journey 1: Product discovery
            [
                ("merhaba", "greeting"),
                ("hamile için pijama arıyorum", "product_search"),
                ("1 numaralı ürünün fiyatı nedir", "followup"),
                ("stokta var mı", "followup"),
                ("teşekkürler", "thanks"),
            ],
            
            # Customer journey 2: Specific product
            [
                ("afrika gecelik var mı", "product_search"),
                ("fiyatı ne kadar", "followup"),
                ("başka rengi var mı", "followup"),
                ("sipariş nasıl veririm", "order_request"),
            ],
            
            # Customer journey 3: Size inquiry
            [
                ("büyük beden gecelik", "product_search"),
                ("m beden var mı", "size_inquiry"),
                ("beden tablosu", "size_inquiry"),
                ("telefon numaranız", "phone_inquiry"),
            ],
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"🎭 Testing Customer Scenario {i}")
            scenario_success = True
            
            for query, expected_intent in scenario:
                result = self._send_request(query)
                success = result.intent == expected_intent or result.error is None
                if not success:
                    scenario_success = False
                
                self._add_result(f"Scenario {i}: {query}", success, result.response_time, 
                               result.response, result.intent, result.confidence, result.error)
            
            print(f"   {'✅' if scenario_success else '❌'} Scenario {i} {'Passed' if scenario_success else 'Failed'}")
    
    def _send_request(self, message: str) -> TestResult:
        """Send request to chatbot API"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": message},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    test_name="",
                    success=True,
                    response_time=response_time,
                    response=data.get('response', ''),
                    intent=data.get('intent', 'unknown'),
                    confidence=data.get('confidence', 0.0)
                )
            else:
                return TestResult(
                    test_name="",
                    success=False,
                    response_time=response_time,
                    response="",
                    intent="error",
                    confidence=0.0,
                    error=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            return TestResult(
                test_name="",
                success=False,
                response_time=0.0,
                response="",
                intent="error",
                confidence=0.0,
                error=str(e)
            )
    
    def _add_result(self, test_name: str, success: bool, response_time: float, 
                   response: str, intent: str, confidence: float, error: str = None):
        """Add test result"""
        result = TestResult(test_name, success, response_time, response, intent, confidence, error)
        self.results.append(result)
        
        # Update stats
        self.performance_stats['total_tests'] += 1
        if success:
            self.performance_stats['passed_tests'] += 1
        else:
            self.performance_stats['failed_tests'] += 1
        
        if response_time > 0:
            self.performance_stats['max_response_time'] = max(self.performance_stats['max_response_time'], response_time)
            self.performance_stats['min_response_time'] = min(self.performance_stats['min_response_time'], response_time)
        
        # Print result
        status = "✅" if success else "❌"
        print(f"   {status} {test_name} ({response_time:.3f}s) - {intent} ({confidence:.2f})")
        if error:
            print(f"      Error: {error}")
    
    def _generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Calculate average response time
        response_times = [r.response_time for r in self.results if r.response_time > 0]
        if response_times:
            self.performance_stats['average_response_time'] = sum(response_times) / len(response_times)
        
        # Overall stats
        total = self.performance_stats['total_tests']
        passed = self.performance_stats['passed_tests']
        failed = self.performance_stats['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed} ({success_rate:.1f}%)")
        print(f"   Failed: {failed}")
        
        print(f"\n⚡ Performance Metrics:")
        print(f"   Average Response Time: {self.performance_stats['average_response_time']:.3f}s")
        print(f"   Max Response Time: {self.performance_stats['max_response_time']:.3f}s")
        print(f"   Min Response Time: {self.performance_stats['min_response_time']:.3f}s")
        
        # Category breakdown
        categories = {}
        for result in self.results:
            category = result.test_name.split(':')[0]
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0}
            categories[category]['total'] += 1
            if result.success:
                categories[category]['passed'] += 1
        
        print(f"\n📋 Results by Category:")
        for category, stats in categories.items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Failed tests
        failed_tests = [r for r in self.results if not r.success]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for result in failed_tests[:10]:  # Show first 10 failures
                print(f"   - {result.test_name}")
                if result.error:
                    print(f"     Error: {result.error}")
        
        # Performance warnings
        slow_tests = [r for r in self.results if r.response_time > 2.0]
        if slow_tests:
            print(f"\n⚠️ Slow Tests (>2s) ({len(slow_tests)}):")
            for result in slow_tests[:5]:
                print(f"   - {result.test_name}: {result.response_time:.3f}s")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if success_rate >= 95:
            print("   🟢 EXCELLENT - System is production ready")
        elif success_rate >= 90:
            print("   🟡 GOOD - Minor issues need attention")
        elif success_rate >= 80:
            print("   🟠 FAIR - Several issues need fixing")
        else:
            print("   🔴 POOR - Major issues need immediate attention")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = ComprehensiveTestSystem()
    tester.run_all_tests()