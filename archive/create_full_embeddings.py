#!/usr/bin/env python3
"""
Tüm ürünler için embeddings oluştur
"""

import json
import os
from semantic_product_search import SemanticProductSearch

def main():
    # API key'i ayarla
    os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key-here'
    
    # Temizlenmiş ürünleri yükle
    with open('data/products.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"🚀 {len(products)} ürün için embeddings oluşturuluyor...")
    
    # Semantic search engine'i başlat
    search_engine = SemanticProductSearch()
    
    # Embeddings oluştur
    success = search_engine.create_embeddings(products)
    
    if success:
        print("✅ Tüm embeddings başarıyla oluşturuldu!")
        
        # Test araması yap
        test_queries = [
            "hamile için rahat pijama",
            "siyah dantelli gecelik", 
            "ekonomik takım",
            "premium sabahlık"
        ]
        
        print("\n🔍 Test Aramaları:")
        for query in test_queries:
            print(f"\n👤 '{query}' araması:")
            results = search_engine.semantic_search(query, 3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['name'][:60]}...")
                    print(f"     {result['color']} - {result['final_price']} TL - Benzerlik: {result['similarity']:.3f}")
            else:
                print("     Sonuç bulunamadı")
    else:
        print("❌ Embeddings oluşturulamadı!")

if __name__ == "__main__":
    main()