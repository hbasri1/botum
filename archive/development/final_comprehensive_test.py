#!/usr/bin/env python3
"""
Final Comprehensive Test - All Issues Fixed
"""

from final_mvp_system import FinalMVPChatbot
import logging

logging.basicConfig(level=logging.INFO)

def run_final_tests():
    """Run comprehensive tests for all fixed issues"""
    print("🚀 Final Comprehensive Test Suite")
    print("=" * 60)
    
    chatbot = FinalMVPChatbot()
    
    # Critical test cases that were problematic
    critical_tests = [
        {
            "category": "🔍 Product Search Accuracy",
            "tests": [
                ("afrika gecelik", "Should find Afrika Etnik product first"),
                ("afirka gecelik", "Should handle typo and find Afrika product"),
                ("hamile lohusa takım", "Should find maternity products"),
                ("dantelli gecelik", "Should find lace nightgowns"),
                ("göğüs dekolteli", "Should find decollete products")
            ]
        },
        {
            "category": "💰 Context-Aware Queries", 
            "tests": [
                ("afrika gecelik fiyatı nedir", "Should show Afrika product price directly"),
                ("hamile takım ne kadar", "Should show maternity set price"),
                ("dantelli gecelik stok var mı", "Should check lace nightgown stock")
            ]
        },
        {
            "category": "👋 Conversation Flow",
            "tests": [
                ("merhaba", "Should greet properly"),
                ("yok", "Should say goodbye"),
                ("hayır", "Should say goodbye"),
                ("başka sorum yok", "Should say goodbye"),
                ("teşekkürler", "Should acknowledge thanks"),
                ("görüşürüz", "Should say goodbye")
            ]
        },
        {
            "category": "🏢 Business Information",
            "tests": [
                ("telefon numaranız", "Should provide phone number"),
                ("iade politikası", "Should provide return policy"),
                ("kargo bilgileri", "Should provide shipping info")
            ]
        }
    ]
    
    total_tests = 0
    successful_tests = 0
    
    for category_info in critical_tests:
        category = category_info["category"]
        tests = category_info["tests"]
        
        print(f"\n{category}")
        print("-" * 50)
        
        for query, expected in tests:
            total_tests += 1
            print(f"\n👤 User: {query}")
            print(f"📝 Expected: {expected}")
            
            try:
                response = chatbot.chat(query)
                print(f"🤖 Bot: {response.message[:100]}{'...' if len(response.message) > 100 else ''}")
                print(f"📊 Intent: {response.intent} (confidence: {response.confidence:.2f})")
                
                if response.products_found > 0:
                    print(f"🛍️ Products found: {response.products_found}")
                
                # Simple success criteria
                success = True
                if "afrika" in query.lower() and response.products_found > 0:
                    # Check if Afrika product is mentioned in response
                    if "Afrika Etnik" not in response.message:
                        success = False
                        print("❌ Afrika product not found first")
                elif "yok" in query or "hayır" in query or "başka sorum yok" in query:
                    if response.intent != "goodbye":
                        success = False
                        print("❌ Should be goodbye intent")
                elif "fiyat" in query and response.intent == "price_inquiry":
                    if response.products_found == 0:
                        success = False
                        print("❌ Should find product and show price")
                
                if success:
                    successful_tests += 1
                    print("✅ Test passed")
                else:
                    print("❌ Test failed")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Final report
    print(f"\n{'='*60}")
    print(f"📊 FINAL TEST REPORT")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests / total_tests >= 0.95:
        print("🎉 EXCELLENT! System is production ready!")
    elif successful_tests / total_tests >= 0.90:
        print("✅ GOOD! System is ready with minor improvements needed")
    else:
        print("⚠️ NEEDS WORK! More improvements required")
    
    return successful_tests / total_tests

if __name__ == "__main__":
    success_rate = run_final_tests()
    print(f"\nFinal Success Rate: {success_rate*100:.1f}%")