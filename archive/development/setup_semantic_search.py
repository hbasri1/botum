#!/usr/bin/env python3
"""
Semantic Search Setup - pgvector + Google Embedding
"""

import asyncio
import json
import asyncpg
from orchestrator.services.semantic_search_engine import SemanticSearchEngine, create_rich_embedding_text

async def setup_semantic_search():
    """Semantic search sistemini kur"""
    
    print("🚀 Semantic Search Setup Başlıyor...")
    
    # 1. Ürünleri yükle
    print("\n📦 Ürünler yükleniyor...")
    with open("data/products.json", "r", encoding="utf-8") as f:
        products = json.load(f)
    
    print(f"✅ {len(products)} ürün yüklendi")
    
    # 2. Rich text örnekleri göster
    print("\n🧪 Rich Text Örnekleri:")
    for i, product in enumerate(products[:3]):
        rich_text = create_rich_embedding_text(product)
        print(f"\n{i+1}. {product['name'][:40]}...")
        print(f"   Rich Text: {rich_text[:100]}...")
    
    # 3. PostgreSQL bağlantısı (mock)
    print(f"\n🗄️ PostgreSQL + pgvector Setup:")
    print("   • pgvector extension kurulacak")
    print("   • product_embeddings tablosu oluşturulacak")
    print("   • Vector index'ler kurulacak")
    
    # 4. Embedding generation (mock)
    print(f"\n🧠 Embedding Generation:")
    engine = SemanticSearchEngine()
    
    sample_texts = [
        "afrika gecelik",
        "hamile pijama", 
        "siyah dantelli gecelik"
    ]
    
    for text in sample_texts:
        embedding = await engine.generate_embedding(text)
        print(f"   • '{text}' → {len(embedding)} dimensions")
    
    # 5. Semantic search testi (mock)
    print(f"\n🔍 Semantic Search Test:")
    test_queries = [
        "afrika tarzı gecelik",
        "hamile için uygun pijama",
        "siyah renkte dantelli ürün"
    ]
    
    for query in test_queries:
        print(f"   • '{query}' → Mock semantic search ready")
    
    print(f"\n✅ Semantic Search Setup Tamamlandı!")
    print(f"\n📋 Sonraki Adımlar:")
    print("   1. PostgreSQL'e pgvector extension kur")
    print("   2. Google Embedding API setup")
    print("   3. Batch embedding generation çalıştır")
    print("   4. Mevcut sisteme entegre et")
    print("   5. Hybrid search (fuzzy + semantic) aktifleştir")

if __name__ == "__main__":
    asyncio.run(setup_semantic_search())