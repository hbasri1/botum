#!/usr/bin/env python3
"""
Enhanced Feature Extraction Test
"""

import sys
import os
sys.path.append('orchestrator/services')

from product_feature_extractor import ProductFeatureExtractor

def test_enhanced_extraction():
    """Enhanced feature extraction test"""
    
    extractor = ProductFeatureExtractor()
    
    print("🚀 Enhanced Product Feature Extraction Test:")
    print("=" * 50)
    
    # Test ürünleri
    test_products = [
        "Afrika Etnik Baskılı Dantelli 'Africa Style' Gecelik",
        "Dantelli Önü Düğmeli Hamile Lohusa Gecelik", 
        "Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı",
        "Siyah Tüllü Askılı Gecelik",
        "Beyaz Pamuklu Uzun Kollu Pijama Takımı",
        "Black Lace Nightgown",  # İngilizce test
        "Pregnant Maternity Pajama Set"  # İngilizce test
    ]
    
    for product_name in test_products:
        print(f"\n📦 Product: {product_name}")
        features = extractor.extract_features(product_name)
        
        if features:
            print(f"✅ Extracted {len(features)} features:")
            for feature in features:
                print(f"  • {feature.category.value}: {feature.value} "
                      f"(weight: {feature.weight:.2f}, confidence: {feature.confidence:.2f})")
                if feature.synonyms:
                    print(f"    Synonyms: {', '.join(feature.synonyms[:4])}")
        else:
            print("❌ No features extracted")
        
        # Enhanced product test
        product_dict = {"name": product_name, "id": 1}
        enhanced = extractor.enhance_product_with_features(product_dict)
        
        print(f"🔍 Enhanced search text: {enhanced['search_enhanced_text'][:100]}...")
    
    # İstatistikler
    stats = extractor.get_extraction_stats()
    print(f"\n📈 Enhanced Extraction Stats:")
    print(f"  • Total patterns: {stats['total_patterns']}")
    print(f"  • Categories: {stats['categories']}")
    print(f"  • Synonyms: {stats['synonyms_count']}")

if __name__ == "__main__":
    test_enhanced_extraction()