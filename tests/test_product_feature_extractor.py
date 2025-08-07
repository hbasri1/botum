#!/usr/bin/env python3
"""
Product Feature Extractor Unit Tests
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.services.product_feature_extractor import (
    ProductFeatureExtractor, 
    ProductFeature, 
    FeatureCategory
)

class TestProductFeatureExtractor(unittest.TestCase):
    """ProductFeatureExtractor test sınıfı"""
    
    def setUp(self):
        """Test setup"""
        self.extractor = ProductFeatureExtractor()
    
    def test_color_extraction(self):
        """Renk çıkarma testleri"""
        test_cases = [
            ("Siyah Gecelik", ["siyah"]),
            ("Beyaz Pamuklu Pijama", ["beyaz"]),
            ("Kırmızı Dantel Takım", ["kırmızı"]),
            ("Mavi ve Beyaz Çizgili", ["mavi", "beyaz"]),
            ("Leopar Desenli", ["leopar"])
        ]
        
        for product_name, expected_colors in test_cases:
            with self.subTest(product_name=product_name):
                features = self.extractor.extract_features(product_name)
                color_features = [f for f in features if f.category == FeatureCategory.COLOR]
                extracted_colors = [f.value for f in color_features]
                
                for expected_color in expected_colors:
                    self.assertIn(expected_color, extracted_colors, 
                                f"Expected color '{expected_color}' not found in {extracted_colors}")
    
    def test_material_extraction(self):
        """Malzeme çıkarma testleri"""
        test_cases = [
            ("Dantelli Gecelik", ["dantel"]),
            ("Pamuklu Pijama", ["pamuk"]),
            ("Tüllü Elbise", ["tül"]),
            ("Saten Sabahlık", ["saten"]),
            ("Dantelli ve Tüllü Takım", ["dantel", "tül"])
        ]
        
        for product_name, expected_materials in test_cases:
            with self.subTest(product_name=product_name):
                features = self.extractor.extract_features(product_name)
                material_features = [f for f in features if f.category == FeatureCategory.MATERIAL]
                extracted_materials = [f.value for f in material_features]
                
                for expected_material in expected_materials:
                    self.assertIn(expected_material, extracted_materials,
                                f"Expected material '{expected_material}' not found in {extracted_materials}")
    
    def test_garment_type_extraction(self):
        """Giysi türü çıkarma testleri"""
        test_cases = [
            ("Siyah Gecelik", ["gecelik"]),
            ("Pamuklu Pijama", ["pijama"]),
            ("Dantel Sabahlık", ["sabahlık"]),
            ("Şort Takımı", ["şort", "takım"]),
            ("Uzun Elbise", ["elbise"])
        ]
        
        for product_name, expected_types in test_cases:
            with self.subTest(product_name=product_name):
                features = self.extractor.extract_features(product_name)
                garment_features = [f for f in features if f.category == FeatureCategory.GARMENT_TYPE]
                extracted_types = [f.value for f in garment_features]
                
                for expected_type in expected_types:
                    self.assertIn(expected_type, extracted_types,
                                f"Expected garment type '{expected_type}' not found in {extracted_types}")
    
    def test_target_group_extraction(self):
        """Hedef grup çıkarma testleri"""
        test_cases = [
            ("Hamile Geceliği", ["hamile"]),
            ("Lohusa Sabahlığı", ["lohusa"]),
            ("Hamile Lohusa Takımı", ["hamile", "lohusa", "hamile_lohusa"]),
            ("Büyük Beden Elbise", ["büyük_beden"])
        ]
        
        for product_name, expected_groups in test_cases:
            with self.subTest(product_name=product_name):
                features = self.extractor.extract_features(product_name)
                target_features = [f for f in features if f.category == FeatureCategory.TARGET_GROUP]
                extracted_groups = [f.value for f in target_features]
                
                for expected_group in expected_groups:
                    self.assertIn(expected_group, extracted_groups,
                                f"Expected target group '{expected_group}' not found in {extracted_groups}")
    
    def test_style_extraction(self):
        """Stil çıkarma testleri"""
        test_cases = [
            ("Dekolteli Gecelik", ["dekolteli"]),
            ("Askılı Bluz", ["askılı"]),
            ("Uzun Kollu Pijama", ["uzun_kollu"]),
            ("Kısa Kollu Tişört", ["kısa_kollu"]),
            ("Kolsuz Elbise", ["kolsuz"])
        ]
        
        for product_name, expected_styles in test_cases:
            with self.subTest(product_name=product_name):
                features = self.extractor.extract_features(product_name)
                style_features = [f for f in features if f.category == FeatureCategory.STYLE]
                extracted_styles = [f.value for f in style_features]
                
                for expected_style in expected_styles:
                    self.assertIn(expected_style, extracted_styles,
                                f"Expected style '{expected_style}' not found in {extracted_styles}")
    
    def test_combination_features(self):
        """Kombinasyon özellik testleri"""
        # Hamile Lohusa kombinasyonu
        features = self.extractor.extract_features("Hamile Lohusa Geceliği")
        combination_features = [f for f in features if f.value == "hamile_lohusa"]
        self.assertTrue(len(combination_features) > 0, "Hamile lohusa combination not detected")
        
        # Göğüs ve sırt dekolteli kombinasyonu
        features = self.extractor.extract_features("Göğüs ve Sırt Dekolteli Takım")
        combination_features = [f for f in features if f.value == "göğüs_sırt_dekolteli"]
        self.assertTrue(len(combination_features) > 0, "Göğüs sırt dekolteli combination not detected")
    
    def test_feature_weights(self):
        """Özellik ağırlık testleri"""
        features = self.extractor.extract_features("Siyah Dantelli Hamile Geceliği")
        
        # Garment type en yüksek ağırlığa sahip olmalı
        garment_features = [f for f in features if f.category == FeatureCategory.GARMENT_TYPE]
        if garment_features:
            garment_weight = garment_features[0].weight
            
            # Diğer kategorilerin ağırlıkları garment type'dan düşük olmalı
            for feature in features:
                if feature.category != FeatureCategory.GARMENT_TYPE:
                    self.assertLessEqual(feature.weight, garment_weight,
                                       f"Feature {feature.value} has higher weight than garment type")
    
    def test_confidence_calculation(self):
        """Confidence hesaplama testleri"""
        features = self.extractor.extract_features("Siyah Siyah Gecelik")  # Tekrarlı kelime
        
        # Tüm feature'ların confidence'ı 0-1 arasında olmalı
        for feature in features:
            self.assertGreaterEqual(feature.confidence, 0.0, 
                                  f"Feature {feature.value} has negative confidence")
            self.assertLessEqual(feature.confidence, 1.0,
                               f"Feature {feature.value} has confidence > 1.0")
    
    def test_categorize_features(self):
        """Özellik kategorileme testleri"""
        features = self.extractor.extract_features("Siyah Dantelli Askılı Hamile Geceliği")
        categorized = self.extractor.categorize_features(features)
        
        # Kategoriler doğru şekilde gruplandırılmalı
        expected_categories = ["color", "material", "style", "target_group", "garment_type"]
        
        for category in expected_categories:
            if category in categorized:
                self.assertIsInstance(categorized[category], list,
                                    f"Category {category} should be a list")
                self.assertGreater(len(categorized[category]), 0,
                                 f"Category {category} should not be empty")
    
    def test_enhance_product_with_features(self):
        """Ürün zenginleştirme testleri"""
        product = {
            "id": 1,
            "name": "Siyah Dantelli Hamile Geceliği",
            "price": 100.0,
            "category": "İç Giyim"
        }
        
        enhanced = self.extractor.enhance_product_with_features(product)
        
        # Orijinal alanlar korunmalı
        self.assertEqual(enhanced["id"], 1)
        self.assertEqual(enhanced["name"], "Siyah Dantelli Hamile Geceliği")
        
        # Yeni alanlar eklenmiş olmalı
        self.assertIn("extracted_features", enhanced)
        self.assertIn("feature_categories", enhanced)
        self.assertIn("feature_weights", enhanced)
        self.assertIn("search_enhanced_text", enhanced)
        
        # Extracted features doğru formatta olmalı
        self.assertIsInstance(enhanced["extracted_features"], list)
        if enhanced["extracted_features"]:
            feature = enhanced["extracted_features"][0]
            required_keys = ["name", "category", "value", "weight", "confidence", "synonyms"]
            for key in required_keys:
                self.assertIn(key, feature, f"Feature missing key: {key}")
    
    def test_empty_input(self):
        """Boş input testleri"""
        # Boş string
        features = self.extractor.extract_features("")
        self.assertEqual(len(features), 0, "Empty string should return no features")
        
        # None input
        features = self.extractor.extract_features(None)
        self.assertEqual(len(features), 0, "None input should return no features")
    
    def test_turkish_characters(self):
        """Türkçe karakter testleri"""
        test_cases = [
            "Göğüs Dekolteli Gecelik",
            "Şık Sabahlık",
            "Çiçekli Pijama",
            "İpek Elbise",
            "Ürün Açıklaması"
        ]
        
        for product_name in test_cases:
            with self.subTest(product_name=product_name):
                # Türkçe karakterli ürün isimleri hata vermemeli
                try:
                    features = self.extractor.extract_features(product_name)
                    self.assertIsInstance(features, list)
                except Exception as e:
                    self.fail(f"Turkish characters caused error: {e}")
    
    def test_get_extraction_stats(self):
        """İstatistik testleri"""
        stats = self.extractor.get_extraction_stats()
        
        # Gerekli alanlar mevcut olmalı
        required_keys = ["total_patterns", "categories", "synonyms_count", "category_weights"]
        for key in required_keys:
            self.assertIn(key, stats, f"Stats missing key: {key}")
        
        # Değerler mantıklı olmalı
        self.assertGreater(stats["total_patterns"], 0, "Should have patterns")
        self.assertGreater(stats["categories"], 0, "Should have categories")
        self.assertGreaterEqual(stats["synonyms_count"], 0, "Synonyms count should be non-negative")

class TestProductFeature(unittest.TestCase):
    """ProductFeature model testleri"""
    
    def test_product_feature_creation(self):
        """ProductFeature oluşturma testi"""
        feature = ProductFeature(
            name="test_feature",
            category=FeatureCategory.COLOR,
            value="siyah",
            weight=0.8,
            synonyms=["black", "kara"],
            confidence=0.9
        )
        
        self.assertEqual(feature.name, "test_feature")
        self.assertEqual(feature.category, FeatureCategory.COLOR)
        self.assertEqual(feature.value, "siyah")
        self.assertEqual(feature.weight, 0.8)
        self.assertEqual(feature.synonyms, ["black", "kara"])
        self.assertEqual(feature.confidence, 0.9)

if __name__ == "__main__":
    # Test suite'i çalıştır
    unittest.main(verbosity=2)