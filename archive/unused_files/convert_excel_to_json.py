#!/usr/bin/env python3
"""
Excel dosyasını JSON formatına çevir
"""

import pandas as pd
import json
import re

def clean_price(price_str):
    """Fiyat stringini temizle ve float'a çevir"""
    if pd.isna(price_str):
        return 0.0
    
    # String'e çevir
    price_str = str(price_str)
    
    # Virgülü noktaya çevir
    price_str = price_str.replace(',', '.')
    
    # Sadece sayıları ve noktayı tut
    price_str = re.sub(r'[^\d.]', '', price_str)
    
    try:
        return float(price_str)
    except:
        return 0.0

def main():
    # Excel dosyasını oku
    df = pd.read_excel('Ürün Bilgisi Raporu (3).xlsx')
    
    print(f"📊 Excel dosyasında {len(df)} ürün bulundu")
    
    # JSON formatına çevir
    products = []
    
    for _, row in df.iterrows():
        # Fiyatları temizle
        original_price = clean_price(row['Monamise Satış Fiyatı'])
        discount_rate = float(row['İndirim Oranı (%)']) if pd.notna(row['İndirim Oranı (%)']) else 0.0
        final_price = clean_price(row['Monamise İndirimli Net Satış Fiyatı'])
        
        product = {
            "code": str(row['Ürün Kodu']).strip(),
            "name": str(row['Ürün Adı']).strip(),
            "color": str(row['Renk']).strip(),
            "price": original_price,
            "discount": discount_rate,
            "final_price": final_price,
            "category": "İç Giyim",
            "stock": 10  # Varsayılan stok
        }
        
        products.append(product)
    
    # JSON dosyasına kaydet
    with open('data/products_new.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(products)} ürün data/products_new.json dosyasına kaydedildi")
    
    # İlk 3 ürünü göster
    print("\n📝 İlk 3 ürün:")
    for i, product in enumerate(products[:3]):
        print(f"{i+1}. {product['name']} - {product['color']} - {product['final_price']} TL")
    
    # Eski dosyayı yedekle
    import shutil
    shutil.copy('data/products.json', 'data/products_backup.json')
    print("📦 Eski ürün dosyası products_backup.json olarak yedeklendi")
    
    # Yeni dosyayı ana dosya yap
    shutil.copy('data/products_new.json', 'data/products.json')
    print("🔄 Yeni ürün dosyası products.json olarak güncellendi")

if __name__ == "__main__":
    main()