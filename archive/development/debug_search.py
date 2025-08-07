import json
from rapidfuzz import fuzz

# Test the search issue
with open("data/products.json", "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

def search_products_by_name(product_name, max_results=5):
    """Gelişmiş ürün arama - tam eşleşme öncelikli"""
    if not product_name:
        return []
    
    product_name = product_name.lower().strip()
    exact_matches = []
    partial_matches = []
    
    name_words = product_name.split()
    
    print(f"🔍 ARAMA: '{product_name}'")
    print(f"📝 KELİMELER: {name_words}")
    
    # Tüm ürünlerde ara
    for product in PRODUCTS:
        product_full_name = product["name"].lower()
        match_score = 0
        exact_word_matches = 0
        
        # Afrika ürünlerini özel kontrol
        if "afrika" in product_full_name:
            print(f"🌍 Afrika ürünü bulundu: {product['name']}")
        
        # Kelime bazlı eşleşme sayısı
        for word in name_words:
            if len(word) > 2 and word in product_full_name:
                match_score += 1
                exact_word_matches += 1
                if "afrika" in product_full_name:
                    print(f"  ✅ Kelime eşleşmesi: '{word}' → score: {match_score}")
        
        # Eğer tüm kelimeler eşleşiyorsa tam eşleşme
        if exact_word_matches == len(name_words) and len(name_words) > 1:
            exact_matches.append((product, match_score))
            if "afrika" in product_full_name:
                print(f"  🎯 TAM EŞLEŞME: {product['name']}")
        elif match_score > 0:
            partial_matches.append((product, match_score))
            if "afrika" in product_full_name:
                print(f"  📍 KISMİ EŞLEŞME: {product['name']}")
        else:
            # Fuzzy matching
            similarity = fuzz.partial_ratio(product_name, product_full_name)
            if similarity > 70:
                partial_matches.append((product, similarity / 100))
    
    print(f"🎯 Tam eşleşme: {len(exact_matches)}")
    print(f"📍 Kısmi eşleşme: {len(partial_matches)}")
    
    # Önce tam eşleşmeleri döndür
    if exact_matches:
        exact_matches.sort(key=lambda x: x[1], reverse=True)
        results = [match[0] for match in exact_matches[:max_results]]
        print(f"✅ TAM EŞLEŞME SONUÇLARI:")
        for i, product in enumerate(results, 1):
            print(f"  {i}. {product['name']} - {product.get('final_price', 'N/A')} TL")
        return results
    
    # Tam eşleşme yoksa kısmi eşleşmeleri döndür
    partial_matches.sort(key=lambda x: x[1], reverse=True)
    results = [match[0] for match in partial_matches[:max_results]]
    print(f"📍 KISMİ EŞLEŞME SONUÇLARI:")
    for i, product in enumerate(results, 1):
        print(f"  {i}. {product['name']} - {product.get('final_price', 'N/A')} TL")
    return results

# Test
print("=" * 60)
results = search_products_by_name("afrika gecelik")
print("=" * 60)