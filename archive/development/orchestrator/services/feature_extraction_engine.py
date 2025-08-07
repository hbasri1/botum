"""
Feature Extraction Engine - Turkish product query feature extraction
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FeatureCategory(Enum):
    """Özellik kategorileri"""
    GARMENT_TYPE = "garment_type"      # gecelik, pijama, elbise
    TARGET_GROUP = "target_group"      # hamile, lohusa, büyük beden
    STYLE = "style"                    # dantelli, düğmeli, dekolteli
    COLOR = "color"                    # siyah, beyaz, kırmızı
    BODY_PART = "body_part"           # kol, omuz, yaka, göğüs, sırt
    CLOSURE = "closure"                # düğmeli, fermuarlı, bağlamalı
    MATERIAL = "material"              # pamuk, ipek, dantel
    PATTERN = "pattern"                # çizgili, puantiyeli, desenli
    SIZE = "size"                      # büyük beden, küçük beden
    OCCASION = "occasion"              # günlük, özel, gece
    QUERY_TYPE = "query_type"          # fiyat, stok, renk, beden

@dataclass
class ProductFeature:
    """Ürün özelliği"""
    value: str
    category: FeatureCategory
    weight: float
    confidence: float
    synonyms: List[str]
    normalized_value: str
    start_pos: int = 0
    end_pos: int = 0

class FeatureExtractionEngine:
    """Turkish product query feature extraction engine"""
    
    def __init__(self):
        # Feature definitions with weights and synonyms
        self.feature_definitions = {
            # GARMENT TYPES - En yüksek ağırlık
            FeatureCategory.GARMENT_TYPE: {
                "gecelik": {
                    "weight": 2.0,
                    "synonyms": ["geceliği", "geceliğin", "geceliğe", "gecelig", "nightgown"],
                    "patterns": [r"\bgecelik\w*\b", r"\bnightgown\b"]
                },
                "pijama": {
                    "weight": 2.0,
                    "synonyms": ["pijamayı", "pijamanın", "pijamaya", "pijamalar", "pajama", "pyjama"],
                    "patterns": [r"\bpijama\w*\b", r"\bpajama\b", r"\bpyjama\b"]
                },
                "elbise": {
                    "weight": 2.0,
                    "synonyms": ["elbiseyi", "elbisenin", "elbiseye", "elbiseler", "dress"],
                    "patterns": [r"\belbise\w*\b", r"\bdress\b"]
                },
                "sabahlık": {
                    "weight": 2.0,
                    "synonyms": ["sabahlığı", "sabahlığın", "sabahlığa", "sabahlıklar", "robe"],
                    "patterns": [r"\bsabahlık\w*\b", r"\brobe\b"]
                },
                "takım": {
                    "weight": 1.8,
                    "synonyms": ["takımı", "takımın", "takıma", "takimi", "set"],
                    "patterns": [r"\btakım\w*\b", r"\bset\b"]
                }
            },
            
            # TARGET GROUPS - Yüksek ağırlık
            FeatureCategory.TARGET_GROUP: {
                "hamile": {
                    "weight": 1.8,
                    "synonyms": ["pregnant", "maternity", "anne adayı"],
                    "patterns": [r"\bhamile\b", r"\bpregnant\b", r"\bmaternity\b"]
                },
                "lohusa": {
                    "weight": 1.8,
                    "synonyms": ["emziren", "nursing", "anne"],
                    "patterns": [r"\blohusa\b", r"\bemziren\b", r"\bnursing\b"]
                },
                "büyük beden": {
                    "weight": 1.5,
                    "synonyms": ["plus size", "xl", "xxl", "geniş"],
                    "patterns": [r"\bbüyük\s+beden\b", r"\bplus\s+size\b", r"\bxxl\b"]
                }
            },
            
            # STYLE FEATURES - Orta-yüksek ağırlık
            FeatureCategory.STYLE: {
                "dantelli": {
                    "weight": 1.5,
                    "synonyms": ["dantel", "lace", "güpürlü"],
                    "patterns": [r"\bdantelli\b", r"\bdantel\b", r"\blace\b"]
                },
                "düğmeli": {
                    "weight": 1.4,
                    "synonyms": ["düğme", "button", "önü düğmeli"],
                    "patterns": [r"\bdüğmeli\b", r"\bdüğme\b", r"\bbutton\b"]
                },
                "dekolteli": {
                    "weight": 1.3,
                    "synonyms": ["dekolte", "v yaka", "açık yaka"],
                    "patterns": [r"\bdekolteli\b", r"\bdekolte\b", r"\bv\s+yaka\b"]
                },
                "askılı": {
                    "weight": 1.2,
                    "synonyms": ["askı", "strap", "ip askılı"],
                    "patterns": [r"\baskılı\b", r"\baskı\b", r"\bstrap\b"]
                }
            },
            
            # COLORS - Orta ağırlık
            FeatureCategory.COLOR: {
                "siyah": {
                    "weight": 1.2,
                    "synonyms": ["black", "kara"],
                    "patterns": [r"\bsiyah\b", r"\bblack\b"]
                },
                "beyaz": {
                    "weight": 1.2,
                    "synonyms": ["white", "ak"],
                    "patterns": [r"\bbeyaz\b", r"\bwhite\b"]
                },
                "kırmızı": {
                    "weight": 1.2,
                    "synonyms": ["red", "al"],
                    "patterns": [r"\bkırmızı\b", r"\bred\b"]
                },
                "mavi": {
                    "weight": 1.2,
                    "synonyms": ["blue", "gök"],
                    "patterns": [r"\bmavi\b", r"\bblue\b"]
                },
                "yeşil": {
                    "weight": 1.2,
                    "synonyms": ["green"],
                    "patterns": [r"\byeşil\b", r"\bgreen\b"]
                },
                "pembe": {
                    "weight": 1.2,
                    "synonyms": ["pink", "rozé"],
                    "patterns": [r"\bpembe\b", r"\bpink\b"]
                },
                "mor": {
                    "weight": 1.2,
                    "synonyms": ["purple", "menekşe"],
                    "patterns": [r"\bmor\b", r"\bpurple\b"]
                },
                "lacivert": {
                    "weight": 1.2,
                    "synonyms": ["navy", "koyu mavi"],
                    "patterns": [r"\blacivert\b", r"\bnavy\b"]
                },
                "bordo": {
                    "weight": 1.2,
                    "synonyms": ["burgundy", "koyu kırmızı"],
                    "patterns": [r"\bbordo\b", r"\bburgundy\b"]
                },
                "ekru": {
                    "weight": 1.2,
                    "synonyms": ["cream", "krem"],
                    "patterns": [r"\bekru\b", r"\bcream\b", r"\bkrem\b"]
                }
            },
            
            # BODY PARTS - Orta ağırlık
            FeatureCategory.BODY_PART: {
                "kol": {
                    "weight": 1.1,
                    "synonyms": ["sleeve", "arm", "kolu"],
                    "patterns": [r"\bkol\w*\b", r"\bsleeve\b"]
                },
                "omuz": {
                    "weight": 1.1,
                    "synonyms": ["shoulder", "omzu"],
                    "patterns": [r"\bomuz\w*\b", r"\bshoulder\b"]
                },
                "yaka": {
                    "weight": 1.1,
                    "synonyms": ["collar", "neck", "yakası"],
                    "patterns": [r"\byaka\w*\b", r"\bcollar\b", r"\bneck\b"]
                },
                "göğüs": {
                    "weight": 1.0,
                    "synonyms": ["chest", "breast", "göğsü"],
                    "patterns": [r"\bgöğüs\w*\b", r"\bchest\b", r"\bbreast\b"]
                },
                "sırt": {
                    "weight": 1.0,
                    "synonyms": ["back", "sırtı"],
                    "patterns": [r"\bsırt\w*\b", r"\bback\b"]
                }
            },
            
            # QUERY TYPES - Yüksek ağırlık (sorgu türü önemli)
            FeatureCategory.QUERY_TYPE: {
                "fiyat": {
                    "weight": 1.8,
                    "synonyms": ["price", "kaç para", "ne kadar", "ücret", "tutar"],
                    "patterns": [r"\bfiyat\w*\b", r"\bprice\b", r"\bkaç\s+para\b", r"\bne\s+kadar\b"]
                },
                "stok": {
                    "weight": 1.8,
                    "synonyms": ["stock", "var mı", "mevcut", "kaldı"],
                    "patterns": [r"\bstok\b", r"\bstock\b", r"\bvar\s+mı\b", r"\bmevcut\b"]
                },
                "renk": {
                    "weight": 1.6,
                    "synonyms": ["color", "renkler", "hangi renk"],
                    "patterns": [r"\brenk\w*\b", r"\bcolor\b"]
                },
                "beden": {
                    "weight": 1.6,
                    "synonyms": ["size", "bedenleri", "hangi beden"],
                    "patterns": [r"\bbeden\w*\b", r"\bsize\b"]
                },
                "detay": {
                    "weight": 1.4,
                    "synonyms": ["detail", "bilgi", "özellik", "info"],
                    "patterns": [r"\bdetay\w*\b", r"\bdetail\b", r"\bbilgi\b", r"\bözellik\b"]
                }
            }
        }
        
        # Turkish normalization rules
        self.turkish_char_map = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
        }
        
        # Common Turkish suffixes to remove
        self.turkish_suffixes = [
            'ı', 'i', 'u', 'ü',  # accusative
            'ın', 'in', 'un', 'ün',  # genitive
            'a', 'e',  # dative
            'da', 'de', 'ta', 'te',  # locative
            'dan', 'den', 'tan', 'ten',  # ablative
            'la', 'le',  # instrumental
            'lar', 'ler',  # plural
            'lık', 'lik', 'luk', 'lük',  # suffix
            'sı', 'si', 'su', 'sü'  # possessive
        ]
    
    def extract_features(self, text: str) -> List[ProductFeature]:
        """Ana feature extraction fonksiyonu"""
        if not text or not text.strip():
            return []
        
        text_lower = text.lower().strip()
        features = []
        
        # Her kategori için feature extraction
        for category, category_features in self.feature_definitions.items():
            category_matches = self._extract_category_features(text_lower, category, category_features)
            features.extend(category_matches)
        
        # Duplicate removal ve confidence calculation
        features = self._remove_duplicates_and_calculate_confidence(features, text_lower)
        
        # Sort by weight * confidence
        features.sort(key=lambda f: f.weight * f.confidence, reverse=True)
        
        return features
    
    def _extract_category_features(self, text: str, category: FeatureCategory, 
                                 category_features: Dict[str, Any]) -> List[ProductFeature]:
        """Belirli bir kategori için feature extraction"""
        features = []
        
        for feature_name, feature_config in category_features.items():
            # Pattern matching
            patterns = feature_config.get("patterns", [])
            found = False
            start_pos = 0
            end_pos = 0
            
            # Exact word match
            if feature_name in text:
                found = True
                start_pos = text.find(feature_name)
                end_pos = start_pos + len(feature_name)
            
            # Pattern matching
            if not found:
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        found = True
                        start_pos = match.start()
                        end_pos = match.end()
                        break
            
            # Synonym matching
            if not found:
                for synonym in feature_config.get("synonyms", []):
                    if synonym.lower() in text:
                        found = True
                        start_pos = text.find(synonym.lower())
                        end_pos = start_pos + len(synonym)
                        break
            
            if found:
                # Normalize value
                normalized_value = self.normalize_turkish_text(feature_name)
                
                feature = ProductFeature(
                    value=feature_name,
                    category=category,
                    weight=feature_config.get("weight", 1.0),
                    confidence=self._calculate_feature_confidence(feature_name, text),
                    synonyms=feature_config.get("synonyms", []),
                    normalized_value=normalized_value,
                    start_pos=start_pos,
                    end_pos=end_pos
                )
                features.append(feature)
        
        return features
    
    def _calculate_feature_confidence(self, feature_name: str, text: str) -> float:
        """Feature confidence hesaplama"""
        base_confidence = 0.8
        
        # Exact match bonus
        if feature_name in text:
            base_confidence += 0.1
        
        # Word boundary bonus
        if re.search(rf'\b{re.escape(feature_name)}\b', text):
            base_confidence += 0.05
        
        # Context bonus - yakındaki kelimeler
        words = text.split()
        if feature_name in words:
            word_index = words.index(feature_name)
            
            # Adjective-noun combinations
            if word_index > 0:
                prev_word = words[word_index - 1]
                if prev_word in ["siyah", "beyaz", "dantelli", "düğmeli"]:
                    base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _remove_duplicates_and_calculate_confidence(self, features: List[ProductFeature], 
                                                  text: str) -> List[ProductFeature]:
        """Duplicate removal ve confidence recalculation"""
        unique_features = {}
        
        for feature in features:
            key = f"{feature.category.value}_{feature.value}"
            
            if key not in unique_features:
                unique_features[key] = feature
            else:
                # Keep the one with higher confidence
                if feature.confidence > unique_features[key].confidence:
                    unique_features[key] = feature
        
        return list(unique_features.values())
    
    def normalize_turkish_text(self, text: str) -> str:
        """Turkish text normalization"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove Turkish characters
        for turkish_char, latin_char in self.turkish_char_map.items():
            normalized = normalized.replace(turkish_char.lower(), latin_char)
        
        # Remove common suffixes
        for suffix in sorted(self.turkish_suffixes, key=len, reverse=True):
            if normalized.endswith(suffix) and len(normalized) > len(suffix) + 2:
                normalized = normalized[:-len(suffix)]
                break
        
        return normalized.strip()
    
    def calculate_feature_similarity(self, features1: List[ProductFeature], 
                                   features2: List[ProductFeature]) -> float:
        """İki feature listesi arasında similarity hesapla"""
        if not features1 or not features2:
            return 0.0
        
        # Create feature sets by category
        features1_by_category = {}
        features2_by_category = {}
        
        for feature in features1:
            if feature.category not in features1_by_category:
                features1_by_category[feature.category] = []
            features1_by_category[feature.category].append(feature)
        
        for feature in features2:
            if feature.category not in features2_by_category:
                features2_by_category[feature.category] = []
            features2_by_category[feature.category].append(feature)
        
        # Calculate category-wise similarity
        total_similarity = 0.0
        total_weight = 0.0
        
        all_categories = set(features1_by_category.keys()) | set(features2_by_category.keys())
        
        for category in all_categories:
            cat_features1 = features1_by_category.get(category, [])
            cat_features2 = features2_by_category.get(category, [])
            
            if not cat_features1 or not cat_features2:
                continue
            
            # Find best matches in this category
            category_similarity = 0.0
            category_weight = 0.0
            
            for f1 in cat_features1:
                best_match_score = 0.0
                for f2 in cat_features2:
                    if f1.value == f2.value:
                        match_score = 1.0
                    elif f1.normalized_value == f2.normalized_value:
                        match_score = 0.9
                    elif f2.value in f1.synonyms or f1.value in f2.synonyms:
                        match_score = 0.8
                    else:
                        match_score = 0.0
                    
                    best_match_score = max(best_match_score, match_score)
                
                category_similarity += best_match_score * f1.weight
                category_weight += f1.weight
            
            if category_weight > 0:
                total_similarity += category_similarity
                total_weight += category_weight
        
        return total_similarity / total_weight if total_weight > 0 else 0.0
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Feature extraction istatistikleri"""
        stats = {
            "total_categories": len(self.feature_definitions),
            "categories": {}
        }
        
        for category, features in self.feature_definitions.items():
            stats["categories"][category.value] = {
                "feature_count": len(features),
                "features": list(features.keys())
            }
        
        return stats

# Test fonksiyonu
def test_feature_extraction():
    """Feature extraction test"""
    engine = FeatureExtractionEngine()
    
    test_queries = [
        "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik bu ne kadar",
        "siyah hamile pijama stok var mı",
        "dantelli sabahlık fiyatı",
        "afrika gecelik renkleri"
    ]
    
    print("🔧 Feature Extraction Engine Test:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        features = engine.extract_features(query)
        
        if features:
            print(f"✅ Found {len(features)} features:")
            for i, feature in enumerate(features, 1):
                print(f"  {i}. {feature.value} ({feature.category.value})")
                print(f"     Weight: {feature.weight:.2f}, Confidence: {feature.confidence:.2f}")
                if feature.synonyms:
                    print(f"     Synonyms: {', '.join(feature.synonyms[:3])}")
        else:
            print("❌ No features found")
    
    # Stats
    stats = engine.get_extraction_stats()
    print(f"\n📊 Feature Extraction Stats:")
    print(f"  Total categories: {stats['total_categories']}")
    for category, info in stats["categories"].items():
        print(f"  {category}: {info['feature_count']} features")

if __name__ == "__main__":
    test_feature_extraction()