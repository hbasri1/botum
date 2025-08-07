#!/usr/bin/env python3
"""
Debug pattern mappings
"""

import sys
import os
sys.path.append('orchestrator/services')

from product_feature_extractor import ProductFeatureExtractor, FeatureCategory
import re

def debug_pattern_mappings():
    """Debug pattern mappings"""
    
    extractor = ProductFeatureExtractor()
    
    print("🐛 Debugging Pattern Mappings")
    print("=" * 40)
    
    # Simulate extract_features logic
    text = "kısa kollu"
    text_lower = text.lower()
    
    print(f"Testing text: '{text}'")
    print(f"Normalized: '{text_lower}'")
    
    # Check pattern mappings
    pattern_mappings = [
        (extractor.color_patterns, FeatureCategory.COLOR),
        (extractor.style_patterns, FeatureCategory.STYLE),
        (extractor.material_patterns, FeatureCategory.MATERIAL),
        (extractor.pattern_patterns, FeatureCategory.PATTERN),
        (extractor.closure_patterns, FeatureCategory.CLOSURE),
        (extractor.neckline_patterns, FeatureCategory.NECKLINE),
        (extractor.sleeve_patterns, FeatureCategory.SLEEVE),
        (extractor.target_group_patterns, FeatureCategory.TARGET_GROUP),
        (extractor.garment_type_patterns, FeatureCategory.GARMENT_TYPE),
        (extractor.size_patterns, FeatureCategory.SIZE)
    ]
    
    print(f"\nTesting {len(pattern_mappings)} pattern categories:")
    
    for patterns, category in pattern_mappings:
        print(f"\n{category.value}:")
        for pattern, feature_value in patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                print(f"  ✅ MATCH: {pattern} -> {feature_value}")
            else:
                # Only show non-matches for sleeve category
                if category == FeatureCategory.SLEEVE:
                    print(f"  ❌ NO MATCH: {pattern} -> {feature_value}")

if __name__ == "__main__":
    debug_pattern_mappings()