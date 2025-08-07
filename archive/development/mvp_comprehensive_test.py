#!/usr/bin/env python3
"""
MVP Chatbot Comprehensive Test Suite
Tests all functionality with real product data
"""

import json
import logging
from mvp_gemini_chatbot import MVPGeminiChatbot
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MVPTestSuite:
    def __init__(self):
        """Initialize test suite"""
        self.chatbot = MVPGeminiChatbot()
        self.test_results = []
        
    def run_test(self, test_name: str, user_message: str, expected_intent: str = None) -> Dict:
        """Run a single test"""
        print(f"\n🧪 Test: {test_name}")
        print(f"👤 User: {user_message}")
        
        try:
            response = self.chatbot.chat(user_message)
            print(f"🤖 Bot: {response}")
            
            # Extract intent for validation
            intent_result = self.chatbot.extract_intent_with_gemini(user_message)
            actual_intent = intent_result.intent
            
            success = True
            if expected_intent and actual_intent != expected_intent:
                success = False
                print(f"❌ Intent mismatch: expected {expected_intent}, got {actual_intent}")
            else:
                print(f"✅ Intent: {actual_intent} (confidence: {intent_result.confidence})")
            
            result = {
                'test_name': test_name,
                'user_message': user_message,
                'response': response,
                'intent': actual_intent,
                'confidence': intent_result.confidence,
                'entities': intent_result.entities,
                'expected_intent': expected_intent,
                'success': success
            }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            result = {
                'test_name': test_name,
                'user_message': user_message,
                'error': str(e),
                'success': False
            }
            self.test_results.append(result)
            return result
    
    def run_greeting_tests(self):
        """Test greeting functionality"""
        print("\n" + "="*50)
        print("🤝 GREETING TESTS")
        print("="*50)
        
        greeting_tests = [
            ("Turkish greeting", "merhaba", "greeting"),
            ("Informal greeting", "selam", "greeting"),
            ("English greeting", "hello", "greeting"),
            ("Thanks", "teşekkürler", "thanks"),
            ("Goodbye", "görüşürüz", "goodbye")
        ]
        
        for test_name, message, expected in greeting_tests:
            self.run_test(test_name, message, expected)
    
    def run_business_info_tests(self):
        """Test business information queries"""
        print("\n" + "="*50)
        print("🏢 BUSINESS INFO TESTS")
        print("="*50)
        
        business_tests = [
            ("Phone inquiry", "telefon numaranız nedir", "phone_inquiry"),
            ("Return policy", "iade politikanız nedir", "return_policy"),
            ("Shipping info", "kargo bilgileriniz", "shipping_info"),
            ("Website inquiry", "web siteniz nedir", "website_inquiry")
        ]
        
        for test_name, message, expected in business_tests:
            self.run_test(test_name, message, expected)
    
    def run_product_search_tests(self):
        """Test product search functionality"""
        print("\n" + "="*50)
        print("🔍 PRODUCT SEARCH TESTS")
        print("="*50)
        
        product_tests = [
            ("Hamile lohusa search", "hamile lohusa takım arıyorum", "product_search"),
            ("Dantelli gecelik search", "dantelli gecelik var mı", "product_search"),
            ("Dekolteli takım search", "göğüs dekolteli takım", "product_search"),
            ("Color search", "siyah renkte bir şey var mı", "product_search"),
            ("Specific product", "Göğüs ve Sırt Dekolteli Dantelli Yırtmaçlı Gecelik", "product_search"),
            ("Typo handling", "afirka gecelik", "product_search"),
            ("Feature combination", "dantelli dekolteli hamile takım", "product_search")
        ]
        
        for test_name, message, expected in product_tests:
            self.run_test(test_name, message, expected)
    
    def run_price_stock_tests(self):
        """Test price and stock inquiries"""
        print("\n" + "="*50)
        print("💰 PRICE & STOCK TESTS")
        print("="*50)
        
        price_stock_tests = [
            ("Price inquiry", "fiyatı ne kadar", "price_inquiry"),
            ("Stock inquiry", "stok var mı", "stock_inquiry"),
            ("General price question", "kaç para", "price_inquiry"),
            ("Stock availability", "mevcut mu", "stock_inquiry")
        ]
        
        for test_name, message, expected in price_stock_tests:
            self.run_test(test_name, message, expected)
    
    def run_edge_case_tests(self):
        """Test edge cases and unclear inputs"""
        print("\n" + "="*50)
        print("🎯 EDGE CASE TESTS")
        print("="*50)
        
        edge_tests = [
            ("Empty-like message", "...", "unclear"),
            ("Random text", "asdfgh", "unclear"),
            ("Mixed language", "hello merhaba", "greeting"),
            ("Very long query", "çok uzun bir mesaj " * 10, "unclear"),
            ("Numbers only", "12345", "unclear")
        ]
        
        for test_name, message, expected in edge_tests:
            self.run_test(test_name, message, expected)
    
    def run_conversation_flow_tests(self):
        """Test conversation flow scenarios"""
        print("\n" + "="*50)
        print("💬 CONVERSATION FLOW TESTS")
        print("="*50)
        
        # Simulate a conversation
        conversation = [
            ("Greeting", "merhaba"),
            ("Product search", "hamile lohusa takım arıyorum"),
            ("Follow-up question", "bunların fiyatları ne kadar"),
            ("Thanks", "teşekkürler"),
            ("Goodbye", "görüşürüz")
        ]
        
        for test_name, message in conversation:
            self.run_test(f"Conversation: {test_name}", message)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.get('success', False)])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Intent accuracy
        intent_tests = [r for r in self.test_results if 'intent' in r and 'expected_intent' in r and r['expected_intent']]
        if intent_tests:
            correct_intents = len([r for r in intent_tests if r['intent'] == r['expected_intent']])
            intent_accuracy = (correct_intents / len(intent_tests)) * 100
            print(f"Intent Accuracy: {intent_accuracy:.1f}%")
        
        # Failed tests
        failed_tests = [r for r in self.test_results if not r.get('success', False)]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test.get('error', 'Intent mismatch')}")
        
        # High confidence tests
        high_confidence_tests = [r for r in self.test_results if r.get('confidence', 0) >= 0.8]
        print(f"\n🎯 High Confidence Tests (≥0.8): {len(high_confidence_tests)}/{total_tests}")
        
        # Save detailed results
        with open('mvp_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Detailed results saved to: mvp_test_results.json")
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'intent_accuracy': intent_accuracy if intent_tests else 0,
            'high_confidence_tests': len(high_confidence_tests)
        }

def main():
    """Run comprehensive MVP test suite"""
    print("🚀 MVP Chatbot Comprehensive Test Suite")
    print("Testing with real product data and Gemini integration")
    
    try:
        test_suite = MVPTestSuite()
        
        # Run all test categories
        test_suite.run_greeting_tests()
        test_suite.run_business_info_tests()
        test_suite.run_product_search_tests()
        test_suite.run_price_stock_tests()
        test_suite.run_edge_case_tests()
        test_suite.run_conversation_flow_tests()
        
        # Generate final report
        report = test_suite.generate_report()
        
        print(f"\n🎉 Test suite completed!")
        print(f"Overall success rate: {report['success_rate']:.1f}%")
        
        if report['success_rate'] >= 90:
            print("✅ MVP system is ready for production!")
        elif report['success_rate'] >= 80:
            print("⚠️ MVP system needs minor improvements")
        else:
            print("❌ MVP system needs significant improvements")
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()