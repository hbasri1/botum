#!/usr/bin/env python3
"""
Test fixed search system
"""

import asyncio
import sys
import os
sys.path.append('orchestrator/services')

from intelligent_search_engine import IntelligentSearchEngine

async def test_fixed_search():
    """Test the fixed search system"""
    
    # Test products
    test_products = [
        {
            'id': 1,
            'name': 'Afrika Etnik Baskılı Dantelli Gecelik',
            'category': 'İç Giyim',
            'color': 'BEJ',
            'price': 565.44
        },
        {
            'id': 2,
            'name': 'Dantelli Önü Düğmeli Hamile Lohusa Gecelik',
            'category': 'İç Giyim',
            'color': 'EKRU',
            'price': 1632.33
        },
        {
            'id': 3,
            'name': 'Dantelli Önü Düğmeli Hamile Lohusa Sabahlık Takımı',
            'category': 'İç Giyim',
            'color': 'EKRU',
            'price': 1786.00
        },
        {
            'id': 4,
            'name': 'Siyah Tüllü Askılı Gecelik',
            'category': 'İç Giyim',
            'color': 'SİYAH',
            'price': 890.50
        }
    ]
    
    search_engine = IntelligentSearchEngine()
    
    print("🔍 Testing Fixed Search System")
    print("=" * 50)
    
    # Test problematic queries
    test_queries = [
        "dantelli hamile lohusa",      # Should find hamile lohusa products
        "yakası dantelli kısa kollu",  # Should NOT find Afrika gecelik
        "siyah gecelik",               # Should find siyah gecelik
        "afrika gecelik"               # Should find afrika gecelik
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        
        result = await search_engine.search(query, test_products, limit=3)
        
        print(f"⏱️  Search time: {result.total_time_ms}ms")
        print(f"🎯 Overall confidence: {result.overall_confidence:.3f}")
        
        if result.matches:
            print(f"✅ Found {len(result.matches)} matches:")
            for i, match in enumerate(result.matches, 1):
                print(f"  {i}. {match.product['name']}")
                print(f"     Score: {match.score:.3f}, Confidence: {match.confidence:.3f}")
                print(f"     Method: {match.method.value}")
                if match.feature_matches:
                    print(f"     Features: {', '.join(match.feature_matches[:3])}")
        else:
            print("❌ No matches found")
        
        print(f"📊 Method times: {result.method_times}")

if __name__ == "__main__":
    asyncio.run(test_fixed_search())