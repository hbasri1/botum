#!/usr/bin/env python3
"""
Debug Turkish Character Issues
"""

import json

def debug_turkish_chars():
    """Debug Turkish character handling"""
    print("🔍 Turkish Character Debug")
    print("=" * 40)
    
    # Load products directly
    with open('data/products.json', 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    # Find black products in raw data
    black_products = [p for p in products_data if 'SİYAH' in p['color']]
    print(f"Black products in raw data: {len(black_products)}")
    
    if black_products:
        print("\nFirst 5 black products from raw data:")
        for i, product in enumerate(black_products[:5], 1):
            print(f"{i}. {product['name']} - Color: '{product['color']}' - Code: {product['code']}")
    
    # Test character encoding
    test_color = "SİYAH"
    print(f"\nTesting color: '{test_color}'")
    print(f"Bytes: {test_color.encode('utf-8')}")
    print(f"Lower: '{test_color.lower()}'")
    
    # Test search in raw data
    matching_products = []
    for product in products_data:
        product_text = f"{product['name']} {product['color']}".lower()
        if 'siyah' in product_text and 'gecelik' in product_text:
            matching_products.append(product)
    
    print(f"\nMatching products in raw data: {len(matching_products)}")
    for product in matching_products[:3]:
        print(f"- {product['name']} - {product['color']}")

if __name__ == "__main__":
    debug_turkish_chars()