#!/usr/bin/env python3
"""
Test feature extraction fix
"""

import sys
import os
sys.path.append('orchestrator/services')

from product_feature_extractor import ProductFeatureExtractor

def test_feature_extraction():
    """Test feature extraction for problematic query"""
    
    extractor = ProductFeatureExtractor()
    
    test_queries = [
        "yakası dantelli kısa kollu",
        "yakası dantelli",
        "kısa kollu",
        "dantelli yaka",
        "kollu bluz"
    ]
    
    print("🧪 Testing Feature Extraction Fix")
    print("=" * 40)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        features = extractor.extract_features(query)
        
        if features:
            print(f"✅ Extracted {len(features)} features:")
            for feature in features:
                print(f"  • {feature.category.value}: {feature.value} (weight: {feature.weight:.2f})")
        else:
            print("❌ No features extracted")

if __name__ == "__main__":
    test_feature_extraction()