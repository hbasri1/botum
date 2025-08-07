#!/usr/bin/env python3
"""
Real Embeddings Setup - Gerçek Google Embedding API ile embeddings oluştur
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.services.simple_semantic_search import SimpleSemanticSearch

async def setup_real_embeddings():
    """Gerçek API key ile embeddings oluştur"""
    
    print("🚀 Real Embeddings Setup")
    print("=" * 40)
    
    # Environment variables yükle
    load_dotenv()
    
    # API key kontrol et
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'YOUR_REAL_GEMINI_API_KEY_HERE':
        print("❌ GEMINI_API_KEY not set!")
        print("💡 Çözüm:")
        print("   1. Google AI Studio'ya git: https://aistudio.google.com/")
        print("   2. API key oluştur")
        print("   3. .env dosyasında GEMINI_API_KEY=your_real_key_here set et")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Semantic search initialize et
    print("\n🧠 Initializing Semantic Search...")
    semantic_search = SimpleSemanticSearch()
    
    # Stats
    stats = semantic_search.get_stats()
    print(f"📊 Products loaded: {stats['total_products']}")
    
    if stats['total_products'] == 0:
        print("❌ No products found!")
        return False
    
    # Test embedding generation
    print("\n🧪 Testing embedding generation...")
    
    test_texts = [
        "Hamile lohusa takım ürünü",
        "Afrika desenli gecelik",
        "Dantelli pijama takımı"
    ]
    
    for text in test_texts:
        try:
            embedding = await semantic_search._get_embedding(text)
            if embedding:
                print(f"✅ '{text}': Embedding generated ({len(embedding)} dimensions)")
            else:
                print(f"❌ '{text}': Failed to generate embedding")
        except Exception as e:
            print(f"❌ '{text}': Error - {str(e)}")
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    
    test_queries = [
        "hamile lohusa takım",
        "afrika gecelik",
        "3lü pijama takım"
    ]
    
    for query in test_queries:
        try:
            results = await semantic_search.search(query, limit=2)
            if results:
                print(f"✅ '{query}': {len(results)} results found")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['name'][:50]}... (similarity: {result['similarity']:.3f})")
            else:
                print(f"❌ '{query}': No results found")
        except Exception as e:
            print(f"❌ '{query}': Error - {str(e)}")
    
    # Cache stats
    final_stats = semantic_search.get_stats()
    print(f"\n📈 Final Stats:")
    print(f"   • Products: {final_stats['total_products']}")
    print(f"   • Cached embeddings: {final_stats['cached_embeddings']}")
    print(f"   • Cached queries: {final_stats['cached_queries']}")
    
    print("\n🎉 Real embeddings setup complete!")
    return True

async def test_with_web_bot():
    """Web bot ile test et"""
    
    print("\n🌐 Testing with Web Bot...")
    
    import requests
    
    test_queries = [
        "hamile lohusa takım ne kadar",
        "afrika gecelik var mı",
        "3lü pijama takım fiyatı"
    ]
    
    for query in test_queries:
        try:
            response = requests.post(
                "http://localhost:8003/ask",
                json={"question": query, "business_id": "fashion_boutique"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ '{query}': {data.get('answer', 'No answer')[:100]}...")
            else:
                print(f"❌ '{query}': HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ '{query}': Error - {str(e)}")

if __name__ == "__main__":
    asyncio.run(setup_real_embeddings())
    
    # Web bot test
    try:
        asyncio.run(test_with_web_bot())
    except Exception as e:
        print(f"Web bot test skipped: {str(e)}")