#!/usr/bin/env python3
"""
Ürün dosyasını sadeleştir - code alanını kaldır
"""

import json

def main():
    # Mevcut ürün dosyasını oku
    with open('data/products.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📊 {len(products)} ürün bulundu")
    
    # Code alanını kaldır
    simplified_products = []
    for product in products:
        simplified_product = {
            "name": product['name'],
            "color": product['color'],
            "price": product['price'],
            "discount": product['discount'],
            "final_price": product['final_price'],
            "category": product['category'],
            "stock": product['stock']
        }
        simplified_products.append(simplified_product)
    
    # Dosyayı güncelle
    with open('data/products.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_products, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(simplified_products)} ürün güncellendi (code alanı kaldırıldı)")
    
    # İlk 3 ürünü göster
    print("\n📝 İlk 3 ürün:")
    for i, product in enumerate(simplified_products[:3]):
        print(f"{i+1}. {product['name']} - {product['color']} - {product['final_price']} TL")

if __name__ == "__main__":
    main()