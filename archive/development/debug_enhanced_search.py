#!/usr/bin/env python3
"""
Debug Enhanced Search
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.services.enhanced_semantic_search import EnhancedSemanticSearch

def debug_enhanced_search():
    """Debug enhanced search"""
    
    # Test products
    products = [
        {
            "id": 1,
            "name": "Çiçek ve Yaprak Desenli Dekolteli Gecelik",
            "color": "EKRU",
            "price": 1415.33
        },
        {
            "id": 2,
            "name": "Afrika Etnik Baskılı Dantelli \"Africa Style\" Gecelik",
            "color": "BEJ",
            "price": 1299.9
        },
        {
            "id": 5,
            "name": "Çiçek Desenli Tüllü Takım",
            "color": "PEMBE",
            "price": 1200.00
        }
    ]
    
    search_engine = EnhancedSemanticSearch()
    
    test_queries = [
        "Çiçek ve Yaprak Desenli Dekolteli Gecelik",
        "çiçek desenli tüllü takım fiyatı"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        matches = search_engine.search(query, products, limit=3, min_score=0.1)
        
        if matches:
            print(f"✅ Found {len(matches)} matches:")
            for i, match in enumerate(matches, 1):
                print(f"\n  {i}. {match.product['name']}")
                print(f"     Score: {match.score:.3f}")
                print(f"     Confidence: {match.confidence:.3f}")
                print(f"     Type: {match.match_type}")
                print(f"     Features: {', '.join(match.matched_features[:3])}")
        else:
            print("❌ No matches found")

if __name__ == "__main__":
    debug_enhanced_search()