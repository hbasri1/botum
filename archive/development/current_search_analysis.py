#!/usr/bin/env python3
"""
Mevcut Ürün Arama Sistemi Analizi
"""

import json
from rapidfuzz import fuzz

def analyze_current_search():
    """Mevcut arama sistemini analiz et"""
    
    print("🔍 Mevcut Ürün Arama Sistemi Analizi")
    print("=" * 50)
    
    # Ürünleri yükle
    with open("data/products.json", "r", encoding="utf-8") as f:
        products = json.load(f)
    
    print(f"📦 Toplam Ürün Sayısı: {len(products)}")
    
    # İlk 5 ürünü göster
    print("\n📋 Örnek Ürünler:")
    for i, product in enumerate(products[:5]):
        print(f"   {i+1}. {product['name']}")
        print(f"      Fiyat: {product.get('final_price', 'N/A')} TL")
        print(f"      Kategori: {product.get('category', 'N/A')}")
        print(f"      Renk: {product.get('color', 'N/A')}")
        print()
    
    # Arama algoritması testi
    print("🧪 Arama Algoritması Testi:")
    test_queries = [
        "afrika gecelik",
        "afrika geceliği", 
        "hamile pijama",
        "siyah gecelik",
        "dantelli gecelik"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Sorgu: '{query}'")
        
        # Normalize et
        normalized_query = normalize_turkish_text(query)
        print(f"   Normalize: '{normalized_query}'")
        
        # En iyi eşleşmeleri bul
        matches = []
        for product in products:
            product_name_normalized = normalize_turkish_text(product["name"])
            score = fuzz.token_set_ratio(normalized_query, product_name_normalized)
            
            if score > 75:
                matches.append((product, score))
        
        # Sırala
        matches.sort(key=lambda x: x[1], reverse=True)
        
        print(f"   Sonuç: {len(matches)} eşleşme")
        for i, (product, score) in enumerate(matches[:3]):
            print(f"      {i+1}. {product['name']} (Skor: {score})")

def normalize_turkish_text(text):
    """Basit Türkçe normalizasyon"""
    if not text:
        return ""
    
    text = text.lower().strip()
    
    # Türkçe ekleri temizle
    replacements = {
        'geceliği': 'gecelik', 'geceliğin': 'gecelik',
        'pijamayı': 'pijama', 'pijamanın': 'pijama',
        'elbiseyi': 'elbise', 'elbisenin': 'elbise',
        'sabahlığı': 'sabahlık', 'sabahlığın': 'sabahlık'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def show_search_flow():
    """Arama akışını göster"""
    print("\n🔄 Mevcut Arama Akışı:")
    print("1. Kullanıcı sorgusu: 'afrika geceliği'")
    print("2. LLM Service: _extract_product_name() → 'afrika gecelik'")
    print("3. Database Service: get_product_info() çağrılır")
    print("4. Normalizasyon: 'afrika geceliği' → 'afrika gecelik'")
    print("5. Fuzzy Matching: Tüm ürünlerle karşılaştır")
    print("6. En yüksek skor (>75): Ürünü döndür")
    print("7. Product Handler: Response formatla")
    print("8. Kullanıcıya cevap")
    
    print("\n⚠️ Mevcut Sorunlar:")
    print("• Sadece fuzzy matching (semantic yok)")
    print("• Türkçe normalizasyon eksik")
    print("• Context awareness yok")
    print("• Personalization yok")
    print("• Synonym handling yok")

if __name__ == "__main__":
    analyze_current_search()
    show_search_flow()