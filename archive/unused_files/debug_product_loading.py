#!/usr/bin/env python3
"""
Debug Product Loading
"""

from final_mvp_system import FinalMVPChatbot
import json

def debug_product_loading():
    """Debug how products are loaded"""
    print("🔍 Product Loading Debug")
    print("=" * 40)
    
    chatbot = FinalMVPChatbot()
    
    # Check a few products
    print(f"Total products loaded: {len(chatbot.products)}")
    
    # Find black products
    black_products = [p for p in chatbot.products if 'siyah' in p.color.lower()]
    print(f"Black products found: {len(black_products)}")
    
    if black_products:
        print("\nFirst 5 black products:")
        for i, product in enumerate(black_products[:5], 1):
            print(f"{i}. {product.name} - Color: '{product.color}' - Code: {product.code}")
    
    # Find black nightgowns specifically
    black_nightgowns = [p for p in chatbot.products if 'siyah' in p.color.lower() and 'gecelik' in p.name.lower()]
    print(f"\nBlack nightgowns found: {len(black_nightgowns)}")
    
    if black_nightgowns:
        print("Black nightgowns:")
        for i, product in enumerate(black_nightgowns[:5], 1):
            print(f"{i}. {product.name} - Color: '{product.color}' - Code: {product.code}")
    
    # Test search algorithm directly
    print(f"\n🔍 Testing Search Algorithm")
    print("=" * 40)
    
    # Test the search function
    results = chatbot.search_products("siyah gecelik")
    print(f"Search results for 'siyah gecelik': {len(results)}")
    
    for i, product in enumerate(results, 1):
        print(f"{i}. {product.name}")
        print(f"   Color: '{product.color}'")
        print(f"   Code: {product.code}")
        
        # Test scoring manually
        query = "siyah gecelik"
        product_text = f"{product.name} {product.color}".lower()
        print(f"   Product text: '{product_text}'")
        print(f"   Query: '{query}'")
        
        # Check if color matches
        if 'siyah' in product.color.lower():
            print(f"   ✅ Color match found!")
        else:
            print(f"   ❌ No color match")
        
        print()

if __name__ == "__main__":
    debug_product_loading()