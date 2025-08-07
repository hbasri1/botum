#!/usr/bin/env python3
"""
Enhanced Query Processor - Sistemik query işleme sistemi
"""

import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProductFeature:
    """Ürün özelliği modeli"""
    name: str
    category: str
    weight: float
    synonyms: List[str]

@dataclass
class ProcessedQuery:
    """İşlenmiş query modeli"""
    original: str
    normalized: str
    features: List[ProductFeature]
    expanded_terms: List[str]
    query_type: str

class QueryProcessor:
    """Sistemik query işleme sistemi"""
    
    def __init__(self):
        self.feature_patterns = self._load_feature_patterns()
        self.turkish_normalizations = self._load_turkish_normalizations()
        self.synonym_mappings = self._load_synonym_mappings()
        self.query_type_patterns = self._load_query_type_patterns()
    
    def _load_feature_patterns(self) -> Dict[str, List[str]]:
        """Ürün özellik pattern'lerini yükle"""
        return {
            'dekolte_types': [
                'göğüs dekolteli', 'sırt dekolteli', 'göğüs ve sırt dekolteli',
                'v yaka', 'açık yaka', 'derin yaka', 'dekolteli', 'dekolte'
            ],
            'product_types': [
                'takım', 'set', 'pijama', 'gecelik', 'sabahlık', 'şort',
                'elbise', 'bluz', 'pantolon', 'tişört', 'kazak'
            ],
            'materials': [
                'dantelli', 'dantel', 'brode', 'brodeli', 'saten', 'pamuk',
                'viskon', 'modal', 'polyester', 'elastan', 'ipek'
            ],
            'styles': [
                'etnik', 'afrika', 'desenli', 'düz', 'çizgili', 'puantiyeli',
                'çiçekli', 'geometrik', 'vintage', 'modern', 'klasik'
            ],
            'colors': [
                'siyah', 'beyaz', 'kırmızı', 'mavi', 'yeşil', 'sarı', 'pembe',
                'mor', 'lacivert', 'bordo', 'bej', 'ekru', 'gri', 'krem'
            ],
            'sizes': [
                'xs', 's', 'm', 'l', 'xl', 'xxl', 'küçük', 'orta', 'büyük'
            ],
            'occasions': [
                'hamile', 'lohusa', 'anne', 'gebelik', 'emzirme', 'doğum',
                'günlük', 'özel', 'gece', 'gündüz', 'spor', 'rahat'
            ]
        }
    
    def _load_turkish_normalizations(self) -> Dict[str, str]:
        """Türkçe normalizasyon kuralları"""
        return {
            # Hal ekleri
            'geceliği': 'gecelik', 'geceliğin': 'gecelik', 'geceliğe': 'gecelik',
            'pijamayı': 'pijama', 'pijamanın': 'pijama', 'pijamaya': 'pijama',
            'elbiseyi': 'elbise', 'elbisenin': 'elbise', 'elbiseye': 'elbise',
            'sabahlığı': 'sabahlık', 'sabahlığın': 'sabahlık', 'sabahlığa': 'sabahlık',
            'takımı': 'takım', 'takımın': 'takım', 'takıma': 'takım', 'takimi': 'takım',
            'şortu': 'şort', 'şortun': 'şort', 'şorta': 'şort',
            
            # Çoğul ekleri
            'gecelikler': 'gecelik', 'pijamalar': 'pijama', 'elbiseler': 'elbise',
            'takımlar': 'takım', 'şortlar': 'şort',
            
            # Yaygın yazım hataları
            'afirka': 'afrika', 'afrik': 'afrika', 'africa': 'afrika',
            'danteli': 'dantelli', 'dantel': 'dantelli',
            'hamil': 'hamile', 'lohsa': 'lohusa',
            'dekolte': 'dekolteli', 'dekolte': 'dekolteli',
            'pijma': 'pijama', 'geclik': 'gecelik'
        }
    
    def _load_synonym_mappings(self) -> Dict[str, List[str]]:
        """Synonym mapping'leri yükle"""
        return {
            'takım': ['set', 'komple', 'alt üst', 'eşofman'],
            'gecelik': ['nightgown', 'gece elbisesi', 'uyku elbisesi'],
            'pijama': ['pajama', 'uyku kıyafeti', 'ev kıyafeti'],
            'sabahlık': ['robe', 'bornoz', 'ev mantolu'],
            'dekolteli': ['açık', 'derin yaka', 'v yaka'],
            'dantelli': ['güpürlü', 'işlemeli', 'süslü'],
            'afrika': ['etnik', 'tribal', 'desenli'],
            'hamile': ['gebelik', 'anne adayı', 'pregnant'],
            'lohusa': ['emziren', 'yeni anne', 'doğum sonrası']
        }
    
    def _load_query_type_patterns(self) -> Dict[str, List[str]]:
        """Query type pattern'lerini yükle"""
        return {
            'price': ['fiyat', 'kaç para', 'ne kadar', 'price', 'ücret', 'tutar'],
            'stock': ['stok', 'var mı', 'mevcut', 'stock', 'kaldı', 'bulunur'],
            'detail': ['detay', 'bilgi', 'özellik', 'nasıl', 'info', 'hakkında'],
            'color': ['renk', 'color', 'renkler', 'hangi renk', 'ne renk'],
            'size': ['beden', 'size', 'bedenleri', 'hangi beden', 'boyut'],
            'search': ['ara', 'bul', 'göster', 'search', 'find', 'show']
        }
    
    def normalize_turkish(self, text: str) -> str:
        """Türkçe metni normalize et"""
        if not text:
            return ""
        
        text = text.lower().strip()
        
        # Türkçe normalizasyonları uygula
        for old, new in self.turkish_normalizations.items():
            text = text.replace(old, new)
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_features(self, query: str) -> List[ProductFeature]:
        """Query'den ürün özelliklerini çıkar"""
        features = []
        normalized_query = self.normalize_turkish(query)
        
        for category, patterns in self.feature_patterns.items():
            for pattern in patterns:
                if pattern in normalized_query:
                    # Özellik ağırlığını hesapla
                    weight = self._calculate_feature_weight(pattern, category, normalized_query)
                    
                    # Synonym'leri al
                    synonyms = self.synonym_mappings.get(pattern, [])
                    
                    feature = ProductFeature(
                        name=pattern,
                        category=category,
                        weight=weight,
                        synonyms=synonyms
                    )
                    features.append(feature)
        
        return features
    
    def _calculate_feature_weight(self, pattern: str, category: str, query: str) -> float:
        """Özellik ağırlığını hesapla"""
        base_weight = 1.0
        
        # Kategori bazlı ağırlık
        category_weights = {
            'dekolte_types': 1.5,  # Çok spesifik özellik
            'product_types': 1.3,  # Önemli kategori
            'materials': 1.2,      # Orta önemli
            'styles': 1.1,         # Az önemli
            'colors': 1.0,         # Temel özellik
            'sizes': 0.9,          # Daha az önemli
            'occasions': 1.4       # Özel durumlar (hamile vs.)
        }
        
        weight = base_weight * category_weights.get(category, 1.0)
        
        # Query'deki pozisyona göre ağırlık
        words = query.split()
        if pattern in words[:3]:  # İlk 3 kelimede
            weight *= 1.2
        
        # Tam kelime eşleşmesi bonusu
        if f" {pattern} " in f" {query} ":
            weight *= 1.1
        
        return weight
    
    def expand_query(self, query: str) -> str:
        """Query'yi synonym'lerle genişlet"""
        expanded_terms = []
        normalized_query = self.normalize_turkish(query)
        words = normalized_query.split()
        
        for word in words:
            expanded_terms.append(word)
            
            # Synonym'leri ekle
            if word in self.synonym_mappings:
                expanded_terms.extend(self.synonym_mappings[word])
        
        return " ".join(expanded_terms)
    
    def detect_query_type(self, query: str) -> str:
        """Query tipini tespit et"""
        normalized_query = self.normalize_turkish(query)
        
        for query_type, patterns in self.query_type_patterns.items():
            if any(pattern in normalized_query for pattern in patterns):
                return query_type
        
        # Default olarak search
        return 'search'
    
    def process_query(self, query: str, context: Optional[Dict] = None) -> ProcessedQuery:
        """Query'yi tam olarak işle"""
        try:
            # Normalize et
            normalized = self.normalize_turkish(query)
            
            # Context ile entegre et
            if context and context.get('last_product'):
                # Context varsa ve query belirsizse, context'i ekle
                if len(normalized.split()) <= 2:  # Kısa query
                    normalized = f"{context['last_product']} {normalized}"
            
            # Özellikleri çıkar
            features = self.extract_features(normalized)
            
            # Query'yi genişlet
            expanded = self.expand_query(normalized)
            
            # Query tipini tespit et
            query_type = self.detect_query_type(normalized)
            
            return ProcessedQuery(
                original=query,
                normalized=normalized,
                features=features,
                expanded_terms=expanded.split(),
                query_type=query_type
            )
            
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            # Fallback
            return ProcessedQuery(
                original=query,
                normalized=self.normalize_turkish(query),
                features=[],
                expanded_terms=query.split(),
                query_type='search'
            )
    
    def get_feature_summary(self, features: List[ProductFeature]) -> Dict[str, List[str]]:
        """Özelliklerin özetini al"""
        summary = {}
        for feature in features:
            if feature.category not in summary:
                summary[feature.category] = []
            summary[feature.category].append(feature.name)
        return summary

# Test fonksiyonu
def test_query_processor():
    """Query processor'ı test et"""
    
    print("🔧 Query Processor Test")
    print("=" * 40)
    
    processor = QueryProcessor()
    
    test_queries = [
        "göğüs ve sırt dekolteli takım",
        "hamile lohusa pijamayı",
        "afrika geceliği fiyatı",
        "dantelli şort takimi var mı",
        "brode sabahlığın stok durumu"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        processed = processor.process_query(query)
        
        print(f"   Normalized: {processed.normalized}")
        print(f"   Type: {processed.query_type}")
        print(f"   Features: {len(processed.features)}")
        
        feature_summary = processor.get_feature_summary(processed.features)
        for category, features in feature_summary.items():
            print(f"     {category}: {', '.join(features)}")

if __name__ == "__main__":
    test_query_processor()