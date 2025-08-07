#!/usr/bin/env python3
"""
Debug search issue - "yakası dantelli kısa kollu" query problem
"""

import sys
import os
sys.path.append('orchestrator/services')

from database_service import DatabaseService
from product_feature_extractor import ProductFeatureExtractor
from simple_semantic_search import SimpleSemanticSearch

def debug_search_issue():
    """Debug the search issue"""
    
    print("🐛 Debugging Search Issue")
    print("=" * 50)
    
    # Initialize services
    db_service = DatabaseService()
    feature_extractor = ProductFeatureExtractor()
    semantic_search = SimpleSemanticSearch()
    
    # Test query
    query = "yakası dantelli kısa kollu"
    print(f"Query: '{query}'")
    
    # Extract features from query
    query_features = feature_extractor.extract_features(query)
    print(f"\nQuery features:")
    for feature in query_features:
        print(f"  - {feature.category.value}: {feature.value} (weight: {feature.weight:.2f})")
    
    # Get some products to test
    products = db_service.products[:10]  # First 10 products
    
    print(f"\nTesting against {len(products)} products:")
    
    # Test each product
    for i, product in enumerate(products, 1):
        product_name = product.get('name', '')
        print(f"\n{i}. {product_name}")
        
        # Extract features from product
        product_features = feature_extractor.extract_features(product_name)
        print(f"   Features: {[f.value for f in product_features]}")
        
        # Check feature overlap
        query_feature_values = {f.value for f in query_features}
        product_feature_values = {f.value for f in product_features}
        overlap = query_feature_values.intersection(product_feature_values)
        
        if overlap:
            print(f"   ✅ Feature overlap: {overlap}")
        else:
            print(f"   ❌ No feature overlap")
        
        # Check if this is the problematic match
        if "afrika" in product_name.lower() and "gecelik" in product_name.lower():
            print(f"   🚨 This is the problematic match!")
            
            # Detailed analysis
            print(f"   Query features: {query_feature_values}")
            print(f"   Product features: {product_feature_values}")
            
            # Check why it matches
            if "dantel" in product_feature_values or "dantelli" in product_name.lower():
                print(f"   🔍 Matches on 'dantel/dantelli'")
            
            # Check semantic similarity
            try:
                similarity = semantic_search._calculate_similarity(query, product_name)
                print(f"   📊 Semantic similarity: {similarity:.3f}")
            except:
                print(f"   📊 Could not calculate semantic similarity")

if __name__ == "__main__":
    debug_search_issue()