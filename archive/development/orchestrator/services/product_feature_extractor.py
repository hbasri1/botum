#!/usr/bin/env python3
"""
Product Feature Extractor - Ürün isimlerinden otomatik özellik çıkarma sistemi
"""

import re
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
try:
    from .turkish_language_rules import TurkishLanguageRules
    from .feature_synonym_mapper import FeatureSynonymMapper
except ImportError:
    from turkish_language_rules import TurkishLanguageRules
    from feature_synonym_mapper import FeatureSynonymMapper

logger = logging.getLogger(__name__)

class FeatureCategory(Enum):
    """Özellik kategorileri"""
    COLOR = "color"
    STYLE = "style"
    MATERIAL = "material"
    SIZE = "size"
    PATTERN = "pattern"
    CLOSURE = "closure"
    NECKLINE = "neckline"
    SLEEVE = "sleeve"
    TARGET_GROUP = "target_group"
    OCCASION = "occasion"
    GARMENT_TYPE = "garment_type"

@dataclass
class ProductFeature:
    """Ürün özelliği modeli"""
    name: str
    category: FeatureCategory
    value: str
    weight: float
    synonyms: List[str]
    confidence: float = 1.0

class ProductFeatureExtractor:
    """Ürün isimlerinden otomatik özellik çıkarma sistemi"""
    
    def __init__(self):
        self.turkish_rules = TurkishLanguageRules()
        self.synonym_mapper = FeatureSynonymMapper()
        self._initialize_feature_patterns()
        self._initialize_synonyms()
        self._initialize_weights()
    
    def _initialize_feature_patterns(self):
        """Özellik çıkarma pattern'lerini initialize et"""
        
        # Renk pattern'leri
        self.color_patterns = {
            r'\b(siyah|black)\b': 'siyah',
            r'\b(beyaz|white|ekru)\b': 'beyaz',
            r'\b(kırmızı|red|bordo)\b': 'kırmızı',
            r'\b(mavi|blue|lacivert|navy)\b': 'mavi',
            r'\b(yeşil|green)\b': 'yeşil',
            r'\b(sarı|yellow|altın|gold)\b': 'sarı',
            r'\b(pembe|pink|fuşya)\b': 'pembe',
            r'\b(mor|purple|lila)\b': 'mor',
            r'\b(gri|gray|grey)\b': 'gri',
            r'\b(kahverengi|brown|bej|beige)\b': 'kahverengi',
            r'\b(turuncu|orange)\b': 'turuncu',
            r'\b(leopar|leopard)\b': 'leopar',
            r'\b(zebra)\b': 'zebra'
        }
        
        # Stil pattern'leri
        self.style_patterns = {
            r'\b(dekolteli|dekolte)\b': 'dekolteli',
            r'\b(askılı|askı)\b': 'askılı',
            r'\b(bol|oversize)\b': 'bol_kesim',
            r'\b(dar|slim|fit)\b': 'dar_kesim',
            r'\b(crop)\b': 'crop',  # Removed "kısa" to avoid conflict
            r'\b(maxi)\b': 'uzun',  # Removed "uzun" to avoid conflict
            r'\b(mini)\b': 'kısa',  # Removed "kısa" to avoid conflict
            r'\b(midi|orta)\b': 'orta_boy',
            r'\b(yüksek bel|yüksek belli)\b': 'yüksek_bel',
            r'\b(düşük bel|düşük belli)\b': 'düşük_bel'
        }
        
        # Malzeme pattern'leri
        self.material_patterns = {
            r'\b(pamuk|cotton|pamuklu)\b': 'pamuk',
            r'\b(ipek|silk)\b': 'ipek',
            r'\b(saten|satin)\b': 'saten',
            r'\b(dantel|dantelli|lace)\b': 'dantel',
            r'\b(tül|tüllü|tulle)\b': 'tül',
            r'\b(kadife|velvet)\b': 'kadife',
            r'\b(deri|leather)\b': 'deri',
            r'\b(jean|denim)\b': 'denim',
            r'\b(örme|knit)\b': 'örme',
            r'\b(polyester)\b': 'polyester',
            r'\b(viskoz|viscose)\b': 'viskoz',
            r'\b(elastan|spandex)\b': 'elastan',
            r'\b(modal)\b': 'modal',
            r'\b(bambu|bamboo)\b': 'bambu'
        }
        
        # Desen pattern'leri
        self.pattern_patterns = {
            r'\b(çizgili|stripe|striped)\b': 'çizgili',
            r'\b(puantiyeli|polka dot|noktalı)\b': 'puantiyeli',
            r'\b(çiçekli|floral|flower)\b': 'çiçekli',
            r'\b(geometrik|geometric)\b': 'geometrik',
            r'\b(etnik|ethnic|afrika|african)\b': 'etnik',
            r'\b(baskılı|print|printed)\b': 'baskılı',
            r'\b(düz|plain|solid)\b': 'düz',
            r'\b(kareli|check|checkered)\b': 'kareli',
            r'\b(leopar|leopard)\b': 'leopar_desen',
            r'\b(zebra)\b': 'zebra_desen'
        }
        
        # Kapama pattern'leri
        self.closure_patterns = {
            r'\b(düğmeli|button|buttoned)\b': 'düğmeli',
            r'\b(fermuarlı|zip|zipper)\b': 'fermuarlı',
            r'\b(bağlamalı|tie|tied)\b': 'bağlamalı',
            r'\b(çıtçıtlı|snap)\b': 'çıtçıtlı',
            r'\b(lastikli|elastic)\b': 'lastikli'
        }
        
        # Yaka pattern'leri - normalized text için
        self.neckline_patterns = {
            r'\b(v yak|v neck)\b': 'v_yaka',              # "yaka" -> "yak"
            r'\b(yuvarlak yak|round neck)\b': 'yuvarlak_yaka',
            r'\b(balık sırt|halter)\b': 'halter',         # "sırtı" -> "sırt"
            r'\b(straplez|strapless)\b': 'straplez',
            r'\b(göğüs dekolte|chest decollete)\b': 'göğüs_dekolteli',  # "dekolteli" -> "dekolte"
            r'\b(sırt dekolte|back decollete)\b': 'sırt_dekolteli',
            r'\b(omuz dekolte|shoulder decollete)\b': 'omuz_dekolteli',
            r'\b(yakas|yak|collar|neck)\b': 'yaka',       # "yakası" -> "yakas"
            r'\b(yakas dantel|dantel yak)\b': 'dantelli_yaka'  # normalized versions
        }
        
        # Hedef grup pattern'leri
        self.target_group_patterns = {
            r'\b(hamile|pregnant|maternity)\b': 'hamile',
            r'\b(lohusa|nursing|breastfeeding)\b': 'lohusa',
            r'\b(büyük beden|plus size)\b': 'büyük_beden',
            r'\b(genç|teen|teenager)\b': 'genç',
            r'\b(çocuk|kids|child)\b': 'çocuk',
            r'\b(bebek|baby)\b': 'bebek'
        }
        
        # Giysi türü pattern'leri
        self.garment_type_patterns = {
            r'\b(gecelik|nightgown|nightdress)\b': 'gecelik',
            r'\b(pijama|pajama|pyjama)\b': 'pijama',
            r'\b(sabahlık|robe|bathrobe)\b': 'sabahlık',
            r'\b(takım|takımı|set|suit)\b': 'takım',
            r'\b(elbise|dress)\b': 'elbise',
            r'\b(bluz|blouse|top)\b': 'bluz',
            r'\b(tişört|t-shirt|tshirt)\b': 'tişört',
            r'\b(şort|short|shorts)\b': 'şort',
            r'\b(pantolon|pants|trousers)\b': 'pantolon',
            r'\b(etek|skirt)\b': 'etek',
            r'\b(ceket|jacket)\b': 'ceket',
            r'\b(hırka|cardigan)\b': 'hırka',
            r'\b(sütyeni|bra)\b': 'sütyeni',
            r'\b(külot|panty|underwear)\b': 'külot'
        }
        
        # Kol pattern'leri (ayrı kategori) - normalized text için
        self.sleeve_patterns = {
            r'\b(kolsuz)\b': 'kolsuz',
            r'\b(uzun koll|uzun kol)\b': 'uzun_kollu',  # "kollu" -> "koll"
            r'\b(kıs koll|kısa kol)\b': 'kısa_kollu',   # "kısa kollu" -> "kıs koll"
            r'\b(koll|sleeve)\b': 'kollu'               # "kollu" -> "koll"
        }
        
        # Beden pattern'leri
        self.size_patterns = {
            r'\b(xs|extra small)\b': 'XS',
            r'\b(s|small)\b': 'S',
            r'\b(m|medium)\b': 'M',
            r'\b(l|large)\b': 'L',
            r'\b(xl|extra large)\b': 'XL',
            r'\b(xxl|2xl)\b': 'XXL',
            r'\b(xxxl|3xl)\b': 'XXXL',
            r'\b(\d{2,3})\b': 'numeric_size'  # 36, 38, 40 gibi
        }
    
    def _initialize_synonyms(self):
        """Sinonim mapping'lerini initialize et"""
        self.synonyms = {
            # Renk sinonimları
            'siyah': ['black', 'kara'],
            'beyaz': ['white', 'ak', 'ekru', 'krem'],
            'kırmızı': ['red', 'al', 'bordo', 'crimson'],
            'mavi': ['blue', 'lacivert', 'navy', 'gök'],
            'yeşil': ['green', 'yemyeşil'],
            'sarı': ['yellow', 'altın', 'gold', 'golden'],
            'pembe': ['pink', 'fuşya', 'rose'],
            'mor': ['purple', 'lila', 'violet'],
            'gri': ['gray', 'grey', 'ash'],
            'kahverengi': ['brown', 'bej', 'beige', 'camel'],
            
            # Stil sinonimları
            'dekolteli': ['dekolte', 'açık yakalı'],
            'askılı': ['askı', 'strap', 'strappy'],
            'kolsuz': ['sleeveless', 'tank'],
            'uzun_kollu': ['long sleeve', 'uzun kol'],
            'kısa_kollu': ['short sleeve', 'kısa kol'],
            
            # Malzeme sinonimları
            'dantel': ['dantelli', 'lace', 'güpür'],
            'tül': ['tüllü', 'tulle', 'mesh'],
            'pamuk': ['cotton', '100% pamuk'],
            'ipek': ['silk', 'satin'],
            
            # Hedef grup sinonimları
            'hamile': ['pregnant', 'maternity', 'anne adayı'],
            'lohusa': ['nursing', 'emziren', 'anne'],
            
            # Giysi türü sinonimları
            'gecelik': ['nightgown', 'nightdress', 'gece elbisesi'],
            'pijama': ['pajama', 'pyjama', 'ev kıyafeti'],
            'sabahlık': ['robe', 'bathrobe', 'morning gown'],
            'takım': ['set', 'suit', 'kombin']
        }
    
    def _initialize_weights(self):
        """Özellik ağırlıklarını initialize et"""
        self.category_weights = {
            FeatureCategory.GARMENT_TYPE: 1.0,  # En önemli
            FeatureCategory.TARGET_GROUP: 0.9,
            FeatureCategory.STYLE: 0.8,
            FeatureCategory.MATERIAL: 0.7,
            FeatureCategory.COLOR: 0.6,
            FeatureCategory.PATTERN: 0.5,
            FeatureCategory.NECKLINE: 0.4,
            FeatureCategory.SLEEVE: 0.4,  # Kol önemli
            FeatureCategory.CLOSURE: 0.3,
            FeatureCategory.SIZE: 0.2,
            FeatureCategory.OCCASION: 0.1
        }
    
    def extract_features(self, product_text: str) -> List[ProductFeature]:
        """
        Ürün metninden özellikleri çıkar
        
        Args:
            product_text: Ürün adı veya açıklaması
            
        Returns:
            List[ProductFeature]: Çıkarılan özellikler
        """
        if not product_text:
            return []
        
        features = []
        # Türkçe normalizasyon uygula
        normalized_text = self.turkish_rules.normalize_for_search(product_text)
        text_lower = normalized_text.lower()
        
        # Her kategori için pattern matching yap
        pattern_mappings = [
            (self.color_patterns, FeatureCategory.COLOR),
            (self.style_patterns, FeatureCategory.STYLE),
            (self.material_patterns, FeatureCategory.MATERIAL),
            (self.pattern_patterns, FeatureCategory.PATTERN),
            (self.closure_patterns, FeatureCategory.CLOSURE),
            (self.neckline_patterns, FeatureCategory.NECKLINE),
            (self.sleeve_patterns, FeatureCategory.SLEEVE),
            (self.target_group_patterns, FeatureCategory.TARGET_GROUP),
            (self.garment_type_patterns, FeatureCategory.GARMENT_TYPE),
            (self.size_patterns, FeatureCategory.SIZE)
        ]
        
        for patterns, category in pattern_mappings:
            for pattern, feature_value in patterns.items():
                if re.search(pattern, text_lower, re.IGNORECASE):
                    # Confidence hesapla (pattern match kalitesine göre)
                    confidence = self._calculate_confidence(pattern, text_lower)
                    
                    # Weight al
                    weight = self.category_weights.get(category, 0.5)
                    
                    # Sinonimları al (kendi sinonimler + Türkçe kurallar + synonym mapper)
                    synonyms = self.synonyms.get(feature_value, [])
                    turkish_synonyms = self.turkish_rules.get_synonyms(feature_value)
                    mapper_synonyms = self.synonym_mapper.get_synonyms(feature_value)
                    
                    synonyms.extend(turkish_synonyms)
                    synonyms.extend(mapper_synonyms)
                    synonyms = list(set(synonyms))  # Duplicate'leri temizle
                    
                    # Feature value'yu normalize et
                    normalized_value = self.synonym_mapper.normalize_feature_value(feature_value)
                    
                    feature = ProductFeature(
                        name=normalized_value,
                        category=category,
                        value=normalized_value,
                        weight=weight,
                        synonyms=synonyms,
                        confidence=confidence
                    )
                    
                    features.append(feature)
        
        # Özel kombinasyon kuralları
        features.extend(self._extract_combination_features(text_lower))
        
        # Duplicate'leri temizle
        features = self._deduplicate_features(features)
        
        logger.info(f"Extracted {len(features)} features from: {product_text[:50]}...")
        return features
    
    def _calculate_confidence(self, pattern: str, text: str) -> float:
        """Pattern match confidence'ını hesapla"""
        matches = re.findall(pattern, text, re.IGNORECASE)
        if not matches:
            return 0.0
        
        # Basit confidence hesaplama
        # Daha fazla match = daha yüksek confidence
        base_confidence = min(len(matches) * 0.3 + 0.7, 1.0)
        
        # Pattern karmaşıklığına göre bonus
        if len(pattern) > 20:  # Karmaşık pattern
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _extract_combination_features(self, text: str) -> List[ProductFeature]:
        """Özel kombinasyon özelliklerini çıkar"""
        features = []
        
        # "hamile lohusa" kombinasyonu
        if re.search(r'\b(hamile.*lohusa|lohusa.*hamile)\b', text):
            feature = ProductFeature(
                name='hamile_lohusa',
                category=FeatureCategory.TARGET_GROUP,
                value='hamile_lohusa',
                weight=0.95,
                synonyms=['maternity', 'anne', 'pregnancy'],
                confidence=0.9
            )
            features.append(feature)
        
        # "göğüs ve sırt dekolteli" kombinasyonu
        if re.search(r'\b(göğüs.*sırt.*dekolteli|sırt.*göğüs.*dekolteli)\b', text):
            feature = ProductFeature(
                name='göğüs_sırt_dekolteli',
                category=FeatureCategory.NECKLINE,
                value='göğüs_sırt_dekolteli',
                weight=0.8,
                synonyms=['front_back_decollete', 'açık yakalı'],
                confidence=0.9
            )
            features.append(feature)
        
        # "dantelli ve tüllü" kombinasyonu
        if re.search(r'\b(dantelli.*tüllü|tüllü.*dantelli)\b', text):
            feature = ProductFeature(
                name='dantelli_tüllü',
                category=FeatureCategory.MATERIAL,
                value='dantelli_tüllü',
                weight=0.7,
                synonyms=['lace_tulle', 'süslü'],
                confidence=0.8
            )
            features.append(feature)
        
        return features
    
    def _deduplicate_features(self, features: List[ProductFeature]) -> List[ProductFeature]:
        """Duplicate özellikleri temizle"""
        seen = set()
        unique_features = []
        
        for feature in features:
            # Aynı kategori ve değer kombinasyonu
            key = (feature.category, feature.value)
            if key not in seen:
                seen.add(key)
                unique_features.append(feature)
        
        return unique_features
    
    def categorize_features(self, features: List[ProductFeature]) -> Dict[str, List[ProductFeature]]:
        """Özellikleri kategorilere göre grupla"""
        categorized = {}
        
        for feature in features:
            category_name = feature.category.value
            if category_name not in categorized:
                categorized[category_name] = []
            categorized[category_name].append(feature)
        
        return categorized
    
    def create_feature_embeddings(self, features: List[ProductFeature]) -> Dict[str, List[float]]:
        """Özellikler için embeddings oluştur (mock implementation)"""
        embeddings = {}
        
        for feature in features:
            # Mock embedding generation
            import hashlib
            import random
            
            # Deterministic embedding
            seed = int(hashlib.md5(feature.value.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            embedding = [random.uniform(-1, 1) for _ in range(384)]  # Smaller dimension
            
            embeddings[feature.value] = embedding
        
        return embeddings
    
    def weight_features(self, features: List[ProductFeature]) -> Dict[str, float]:
        """Özelliklerin ağırlıklarını hesapla"""
        weights = {}
        
        for feature in features:
            # Base weight + confidence bonus
            final_weight = feature.weight * feature.confidence
            weights[feature.value] = final_weight
        
        return weights
    
    def get_feature_synonyms(self, feature_value: str) -> List[str]:
        """Özellik için sinonimları getir"""
        return self.synonyms.get(feature_value, [])
    
    def enhance_product_with_features(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Ürünü çıkarılan özelliklerle zenginleştir"""
        enhanced_product = product.copy()
        
        # Ürün adından özellikleri çıkar
        product_name = product.get('name', '')
        features = self.extract_features(product_name)
        
        # Özellikleri ürüne ekle
        enhanced_product['extracted_features'] = [
            {
                'name': f.name,
                'category': f.category.value,
                'value': f.value,
                'weight': f.weight,
                'confidence': f.confidence,
                'synonyms': f.synonyms
            }
            for f in features
        ]
        
        # Kategorize edilmiş özellikleri ekle
        categorized = self.categorize_features(features)
        enhanced_product['feature_categories'] = {
            category: [f.value for f in features_list]
            for category, features_list in categorized.items()
        }
        
        # Ağırlıkları ekle
        weights = self.weight_features(features)
        enhanced_product['feature_weights'] = weights
        
        # Arama için zenginleştirilmiş metin oluştur
        enhanced_product['search_enhanced_text'] = self._create_search_text(product, features)
        
        return enhanced_product
    
    def _create_search_text(self, product: Dict[str, Any], features: List[ProductFeature]) -> str:
        """Arama için zenginleştirilmiş metin oluştur"""
        text_parts = []
        
        # Orijinal ürün adı
        if name := product.get('name'):
            text_parts.append(name)
        
        # Çıkarılan özellikler
        for feature in features:
            text_parts.append(feature.value)
            text_parts.extend(feature.synonyms)
        
        # Mevcut ürün bilgileri
        for field in ['category', 'color', 'material', 'description']:
            if value := product.get(field):
                text_parts.append(str(value))
        
        return ' '.join(text_parts)
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Feature extraction istatistikleri"""
        return {
            'total_patterns': sum([
                len(self.color_patterns),
                len(self.style_patterns),
                len(self.material_patterns),
                len(self.pattern_patterns),
                len(self.closure_patterns),
                len(self.neckline_patterns),
                len(self.target_group_patterns),
                len(self.garment_type_patterns),
                len(self.size_patterns)
            ]),
            'categories': len(FeatureCategory),
            'synonyms_count': sum(len(syns) for syns in self.synonyms.values()),
            'category_weights': {cat.value: weight for cat, weight in self.category_weights.items()}
        }

# Test fonksiyonu
def test_feature_extraction():
    """Feature extraction sistemini test et"""
    
    extractor = ProductFeatureExtractor()
    
    # Test ürünleri
    test_products = [
        "Afrika Etnik Baskılı Dantelli 'Africa Style' Gecelik",
        "Dantelli Önü Düğmeli Hamile Lohusa Gecelik",
        "Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı",
        "Siyah Tüllü Askılı Gecelik",
        "Beyaz Pamuklu Uzun Kollu Pijama Takımı"
    ]
    
    print("🧪 Product Feature Extraction Test:")
    print("=" * 50)
    
    for product_name in test_products:
        print(f"\n📦 Product: {product_name}")
        features = extractor.extract_features(product_name)
        
        if features:
            print(f"✅ Extracted {len(features)} features:")
            for feature in features:
                print(f"  • {feature.category.value}: {feature.value} "
                      f"(weight: {feature.weight:.2f}, confidence: {feature.confidence:.2f})")
                if feature.synonyms:
                    print(f"    Synonyms: {', '.join(feature.synonyms[:3])}")
        else:
            print("❌ No features extracted")
        
        # Kategorize edilmiş özellikleri göster
        categorized = extractor.categorize_features(features)
        if categorized:
            print("📊 Categorized features:")
            for category, cat_features in categorized.items():
                values = [f.value for f in cat_features]
                print(f"  • {category}: {', '.join(values)}")
    
    # İstatistikleri göster
    stats = extractor.get_extraction_stats()
    print(f"\n📈 Extraction Stats:")
    print(f"  • Total patterns: {stats['total_patterns']}")
    print(f"  • Categories: {stats['categories']}")
    print(f"  • Synonyms: {stats['synonyms_count']}")

if __name__ == "__main__":
    # Test için relative import'ları düzelt
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from turkish_language_rules import TurkishLanguageRules
    from feature_synonym_mapper import FeatureSynonymMapper
    
    # Test'i çalıştır
    test_feature_extraction()