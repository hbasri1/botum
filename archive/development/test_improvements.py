#!/usr/bin/env python3
"""
Test the improvements made to the MVP system
"""

from final_mvp_system import FinalMVPChatbot
import logging

logging.basicConfig(level=logging.INFO)

def test_improvements():
    """Test the specific improvements"""
    print("🧪 Testing MVP System Improvements")
    print("=" * 50)
    
    chatbot = FinalMVPChatbot()
    
    # Test cases for the reported issues
    test_cases = [
        {
            "name": "Afrika Gecelik Search",
            "query": "afrika gecelik",
            "expected": "Should find Afrika Etnik Baskılı product first"
        },
        {
            "name": "Negative Response",
            "query": "yok",
            "expected": "Should recognize as goodbye intent"
        },
        {
            "name": "Context-Aware Price Query",
            "query": "afrika gecelik fiyatı nedir",
            "expected": "Should find product and show price directly"
        },
        {
            "name": "Another Negative",
            "query": "başka sorum yok",
            "expected": "Should say goodbye"
        },
        {
            "name": "Typo Tolerance",
            "query": "afirka gecelik",
            "expected": "Should still find Afrika product"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"👤 User: {test_case['query']}")
        print(f"📝 Expected: {test_case['expected']}")
        
        response = chatbot.chat(test_case['query'])
        print(f"🤖 Bot: {response.message}")
        print(f"📊 Intent: {response.intent} (confidence: {response.confidence:.2f})")
        
        if response.products_found > 0:
            print(f"🛍️ Products found: {response.products_found}")
        
        print("-" * 50)
    
    # Test the specific Afrika product search
    print(f"\n🔍 Detailed Afrika Gecelik Search Test:")
    products = chatbot.search_products("afrika gecelik")
    print(f"Found {len(products)} products:")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product.name} - {product.code}")

if __name__ == "__main__":
    test_improvements()