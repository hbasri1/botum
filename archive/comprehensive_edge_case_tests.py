#!/usr/bin/env python3
"""
Comprehensive Edge Case Tests
Tests for all the problematic scenarios mentioned
"""

import json
import logging
import time
from typing import Dict, List
from final_mvp_system import FinalMVPChatbot
from enhanced_conversation_handler import EnhancedConversationHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EdgeCaseTestSuite:
    """Comprehensive test suite for edge cases"""
    
    def __init__(self):
        self.chatbot = FinalMVPChatbot()
        self.conversation_handler = EnhancedConversationHandler()
        self.test_results = []
    
    def run_test(self, test_name: str, message: str, expected_behavior: str) -> Dict:
        """Run a single test case"""
        print(f"\n🧪 Test: {test_name}")
        print(f"👤 Input: '{message}'")
        print(f"📋 Expected: {expected_behavior}")
        
        start_time = time.time()
        
        try:
            # Get response from chatbot
            response = self.chatbot.chat(message)
            
            # Update conversation context
            self.conversation_handler.update_context(
                message, response.intent, []
            )
            
            processing_time = time.time() - start_time
            
            result = {
                'test_name': test_name,
                'input': message,
                'expected': expected_behavior,
                'response': response.message,
                'intent': response.intent,
                'confidence': response.confidence,
                'processing_time': processing_time,
                'success': True
            }
            
            print(f"🤖 Response: {response.message}")
            print(f"🎯 Intent: {response.intent} (confidence: {response.confidence:.2f})")
            print(f"⏱️ Time: {processing_time:.3f}s")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            result = {
                'test_name': test_name,
                'input': message,
                'expected': expected_behavior,
                'error': str(e),
                'success': False
            }
            
            print(f"❌ Error: {e}")
            self.test_results.append(result)
            return result
    
    def test_ambiguous_greetings(self):
        """Test ambiguous greeting scenarios"""
        print("\n" + "="*60)
        print("🔄 AMBIGUOUS GREETINGS TEST")
        print("="*60)
        
        # Test "iyi günler" in different contexts
        self.run_test(
            "Morning greeting",
            "iyi günler",
            "Should be interpreted as greeting in morning/start of conversation"
        )
        
        # Simulate conversation flow
        self.run_test(
            "Product search after greeting",
            "hamile pijama arıyorum",
            "Should find hamile pijama products"
        )
        
        self.run_test(
            "Evening goodbye",
            "iyi günler",
            "Should be interpreted as goodbye after conversation"
        )
    
    def test_nonsense_inputs(self):
        """Test nonsense and unclear inputs"""
        print("\n" + "="*60)
        print("🤔 NONSENSE INPUTS TEST")
        print("="*60)
        
        nonsense_inputs = [
            ("tamamdırS", "Should handle typos and unclear text"),
            ("asdasdasd", "Should handle random characters"),
            ("123456", "Should handle numbers only"),
            ("!@#$%", "Should handle special characters"),
            ("", "Should handle empty input"),
            ("   ", "Should handle whitespace only"),
            ("a", "Should handle single character"),
            ("aaaaaaaaaaaaaaaaa", "Should handle repeated characters"),
            ("merhaba nasılsın iyi misin", "Should handle overly long greetings"),
            ("ürün ürün ürün", "Should handle repeated words")
        ]
        
        for message, expected in nonsense_inputs:
            self.run_test(f"Nonsense: {message[:20]}...", message, expected)
    
    def test_incomplete_queries(self):
        """Test incomplete product queries"""
        print("\n" + "="*60)
        print("📝 INCOMPLETE QUERIES TEST")
        print("="*60)
        
        incomplete_queries = [
            ("siyah", "Should ask for product type when only color given"),
            ("gecelik", "Should ask for color/size when only type given"),
            ("xl", "Should ask for product type when only size given"),
            ("dantelli", "Should ask for product type when only feature given"),
            ("hamile", "Should ask for specific product type"),
            ("takım", "Should ask for color or other details"),
            ("pahalı", "Should ask for specific product"),
            ("ucuz", "Should ask for specific product"),
            ("güzel", "Should ask for clarification"),
            ("var mı", "Should ask what product they're looking for")
        ]
        
        for message, expected in incomplete_queries:
            self.run_test(f"Incomplete: {message}", message, expected)
    
    def test_context_switching(self):
        """Test conversation context switching"""
        print("\n" + "="*60)
        print("🔄 CONTEXT SWITCHING TEST")
        print("="*60)
        
        # Start with product search
        self.run_test(
            "Initial product search",
            "dantelli hamile lohusa",
            "Should find dantelli hamile lohusa products"
        )
        
        # Switch to different product
        self.run_test(
            "Context switch to sabahlık",
            "sabahlık",
            "Should search for sabahlık products, not continue with previous search"
        )
        
        # Vague follow-up
        self.run_test(
            "Vague follow-up",
            "tamam",
            "Should ask for clarification about which product"
        )
        
        # Number selection
        self.run_test(
            "Number selection",
            "1",
            "Should select first product from last search results"
        )
    
    def test_cache_scenarios(self):
        """Test caching scenarios"""
        print("\n" + "="*60)
        print("💾 CACHE SCENARIOS TEST")
        print("="*60)
        
        # Same query multiple times
        query = "dantelli hamile gecelik"
        
        # First query (should be processed normally)
        result1 = self.run_test(
            "First query (no cache)",
            query,
            "Should process normally and cache result"
        )
        
        # Second query (should use cache)
        result2 = self.run_test(
            "Second query (cached)",
            query,
            "Should return cached result faster"
        )
        
        # Compare processing times
        if result1['success'] and result2['success']:
            time_diff = result1['processing_time'] - result2['processing_time']
            print(f"⚡ Cache performance: {time_diff:.3f}s faster")
    
    def test_turkish_character_handling(self):
        """Test Turkish character normalization"""
        print("\n" + "="*60)
        print("🇹🇷 TURKISH CHARACTERS TEST")
        print("="*60)
        
        turkish_tests = [
            ("dantelli gecelik", "Normal Turkish text"),
            ("DANTELLI GECELIK", "All uppercase"),
            ("Dantelli Gecelik", "Title case"),
            ("dantellı gecelık", "Typo with wrong i"),
            ("şık gecelik", "Turkish ş character"),
            ("güzel ürün", "Turkish ü character"),
            ("çok güzel", "Turkish ç character"),
            ("özel tasarım", "Turkish ö character"),
            ("geniş beden", "Turkish ş in middle"),
            ("büyük beden", "Turkish ü in middle")
        ]
        
        for message, description in turkish_tests:
            self.run_test(f"Turkish: {description}", message, "Should handle Turkish characters correctly")
    
    def test_conversation_flow_edge_cases(self):
        """Test complex conversation flows"""
        print("\n" + "="*60)
        print("💬 CONVERSATION FLOW EDGE CASES")
        print("="*60)
        
        # Rapid fire questions
        rapid_questions = [
            "merhaba",
            "hamile takım",
            "fiyatı",
            "stok var mı",
            "1 numara",
            "teşekkürler",
            "başka sorum yok",
            "iyi günler"
        ]
        
        for i, message in enumerate(rapid_questions):
            self.run_test(
                f"Rapid fire {i+1}",
                message,
                f"Should handle message {i+1} in sequence correctly"
            )
    
    def test_business_info_edge_cases(self):
        """Test business information queries"""
        print("\n" + "="*60)
        print("🏢 BUSINESS INFO EDGE CASES")
        print("="*60)
        
        business_queries = [
            ("telefon", "Should provide phone number"),
            ("numara", "Should provide phone number"),
            ("ara", "Should provide phone number"),
            ("iletişim", "Should provide contact info"),
            ("adres", "Should provide address or contact info"),
            ("site", "Should provide website"),
            ("web", "Should provide website"),
            ("mail", "Should provide email"),
            ("iade", "Should provide return policy"),
            ("kargo", "Should provide shipping info"),
            ("teslimat", "Should provide delivery info"),
            ("ödeme", "Should provide payment info"),
            ("kredi kartı", "Should provide payment info")
        ]
        
        for message, expected in business_queries:
            self.run_test(f"Business: {message}", message, expected)
    
    def test_error_recovery(self):
        """Test error recovery scenarios"""
        print("\n" + "="*60)
        print("🔧 ERROR RECOVERY TEST")
        print("="*60)
        
        # Test with potentially problematic inputs
        error_prone_inputs = [
            ("ürün" * 100, "Should handle very long repeated text"),
            ("çok çok çok çok pahalı ürün istiyorum ama ucuz olsun", "Should handle contradictory requests"),
            ("hamile değilim ama hamile ürünü istiyorum", "Should handle contradictory context"),
            ("erkek için kadın iç giyimi", "Should handle gender mismatch"),
            ("çocuk için yetişkin ürünü", "Should handle age mismatch")
        ]
        
        for message, expected in error_prone_inputs:
            self.run_test(f"Error prone: {message[:30]}...", message, expected)
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 COMPREHENSIVE EDGE CASE TEST SUITE")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_ambiguous_greetings()
        self.test_nonsense_inputs()
        self.test_incomplete_queries()
        self.test_context_switching()
        self.test_cache_scenarios()
        self.test_turkish_character_handling()
        self.test_conversation_flow_edge_cases()
        self.test_business_info_edge_cases()
        self.test_error_recovery()
        
        total_time = time.time() - start_time
        
        # Generate summary report
        self.generate_summary_report(total_time)
    
    def generate_summary_report(self, total_time: float):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - successful_tests
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"⏱️ Total Time: {total_time:.2f}s")
        print(f"⚡ Average Time per Test: {total_time/total_tests:.3f}s")
        
        # Intent distribution
        intents = {}
        for result in self.test_results:
            if result['success']:
                intent = result.get('intent', 'unknown')
                intents[intent] = intents.get(intent, 0) + 1
        
        print(f"\n🎯 Intent Distribution:")
        for intent, count in sorted(intents.items(), key=lambda x: x[1], reverse=True):
            print(f"   {intent}: {count}")
        
        # Performance analysis
        processing_times = [r.get('processing_time', 0) for r in self.test_results if r['success']]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)
            
            print(f"\n⚡ Performance Analysis:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Fastest: {min_time:.3f}s")
            print(f"   Slowest: {max_time:.3f}s")
        
        # Failed tests details
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result.get('error', 'Unknown error')}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if failed_tests > 0:
            print(f"   • Fix {failed_tests} failed test cases")
        
        unclear_count = intents.get('unclear', 0)
        if unclear_count > total_tests * 0.2:  # More than 20% unclear
            print(f"   • Improve intent detection (too many unclear: {unclear_count})")
        
        if avg_time > 1.0:  # Slower than 1 second
            print(f"   • Optimize performance (average {avg_time:.3f}s is slow)")
        
        print(f"   • Implement caching for repeated queries")
        print(f"   • Add more contextual responses")
        print(f"   • Improve Turkish character handling")
        
        # Save detailed report
        self.save_detailed_report()
    
    def save_detailed_report(self):
        """Save detailed test report to file"""
        report = {
            'timestamp': time.time(),
            'total_tests': len(self.test_results),
            'successful_tests': len([r for r in self.test_results if r['success']]),
            'test_results': self.test_results,
            'chatbot_stats': self.chatbot.get_stats(),
            'conversation_stats': self.conversation_handler.get_conversation_stats()
        }
        
        with open('edge_case_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detailed report saved to: edge_case_test_report.json")

def main():
    """Run the comprehensive test suite"""
    test_suite = EdgeCaseTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()