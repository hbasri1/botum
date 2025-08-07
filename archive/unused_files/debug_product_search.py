#!/usr/bin/env python3
"""
Debug Product Search Issues
"""

from final_mvp_system import FinalMVPChatbot
import json

def test_critical_searches():
    """Test critical product searches that should work"""
    print("🔍 Critical Product Search Debug")
    print("=" * 50)
    
    chatbot = FinalMVPChatbot()
    
    # Critical test cases that MUST work
    critical_tests = [
        ("afrika gecelik", "Should find Afrika Etnik Baskılı product"),
        ("hamile lohusa takım", "Should find maternity products"),
        ("dantelli gecelik", "Should find lace nightgowns"),
        ("dekolteli takım", "Should find decollete sets"),
        ("siyah gecelik", "Should find black nightgowns"),
        ("pijama takımı", "Should find pajama sets"),
        ("sabahlık", "Should find robes"),
        ("büyük beden", "Should find plus size items")
    ]
    
    for query, expected in critical_tests:
        print(f"\n🧪 Testing: '{query}'")
        print(f"Expected: {expected}")
        
        try:
            # Test the chat function
            response = chatbot.chat(query)
            print(f"Intent: {response.intent}")
            print(f"Products found: {response.products_found}")
            
            if response.products_found > 0:
                print("✅ Found products")
                # Show first few characters of response
                print(f"Response preview: {response.message[:100]}...")
            else:
                print("❌ No products found")
                print(f"Full response: {response.message}")
            
            # Also test direct search
            if response.intent == "product_search":
                direct_products = chatbot.search_products(query)
                print(f"Direct search found: {len(direct_products)} products")
                if direct_products:
                    print(f"First product: {direct_products[0].name}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

def test_specific_products():
    """Test with specific product names from our database"""
    print("\n🎯 Specific Product Name Tests")
    print("=" * 50)
    
    chatbot = FinalMVPChatbot()
    
    # Load some actual product names
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # Test with actual product names
        test_products = [
            "Afrika Etnik Baskılı Dantelli \"Africa Style\" Gecelik",
            "Dantelli Önü Düğmeli Hamile Lohusa Sabahlık Takımı",
            "Göğüs ve Sırt Dekolteli Dantelli Yırtmaçlı Askılı Gecelik",
            "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik"
        ]
        
        for product_name in test_products:
            print(f"\n🧪 Testing exact name: '{product_name[:50]}...'")
            
            # Test with exact name
            response = chatbot.chat(product_name)
            print(f"Intent: {response.intent}")
            print(f"Products found: {response.products_found}")
            
            if response.products_found > 0:
                print("✅ Found with exact name")
            else:
                print("❌ Not found with exact name")
            
            # Test with simplified version
            simplified = product_name.lower().replace('"', '').replace('\\', '')
            words = simplified.split()[:3]  # First 3 words
            simple_query = ' '.join(words)
            
            print(f"Testing simplified: '{simple_query}'")
            response2 = chatbot.chat(simple_query)
            print(f"Simplified result: {response2.products_found} products")
            
    except Exception as e:
        print(f"Error loading products: {e}")

if __name__ == "__main__":
    test_critical_searches()
    test_specific_products()