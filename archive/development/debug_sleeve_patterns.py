#!/usr/bin/env python3
"""
Debug sleeve patterns
"""

import sys
import os
sys.path.append('orchestrator/services')

from product_feature_extractor import ProductFeatureExtractor
import re

def debug_sleeve_patterns():
    """Debug sleeve patterns"""
    
    extractor = ProductFeatureExtractor()
    
    print("🐛 Debugging Sleeve Patterns")
    print("=" * 40)
    
    # Check if sleeve_patterns exists
    if hasattr(extractor, 'sleeve_patterns'):
        print("✅ sleeve_patterns exists")
        print(f"Patterns: {extractor.sleeve_patterns}")
    else:
        print("❌ sleeve_patterns does not exist")
    
    # Test pattern directly
    test_text = "kısa kollu"
    pattern = r'\b(kısa kollu|kısa kol)\b'
    
    print(f"\nTesting pattern: {pattern}")
    print(f"Against text: '{test_text}'")
    
    matches = re.findall(pattern, test_text, re.IGNORECASE)
    print(f"Direct regex matches: {matches}")
    
    # Test with extractor
    features = extractor.extract_features(test_text)
    print(f"Extractor features: {[f.value for f in features]}")

if __name__ == "__main__":
    debug_sleeve_patterns()