#!/usr/bin/env python3
"""
Feature Synonym Mapper - Özellik sinonim mapping sistemi
"""

import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SynonymGroup:
    """Sinonim grubu"""
    canonical: str  # Standart terim
    synonyms: List[str]  # Sinonimler
    category: str  # Kategori
    weight: float = 1.0  # Ağırlık

class FeatureSynonymMapper:
    """Özellik sinonim mapping sistemi"""
    
    def __init__(self):
        self._initialize_synonym_groups()
        self._build_synonym_index()
    
    def _initialize_synonym_groups(self):
        """Sinonim gruplarını initialize et"""
        
        self.synonym_groups = [
            # Renk sinonimları
            SynonymGroup("siyah", ["black", "kara", "koyu", "dark"], "color", 1.0),
            SynonymGroup("beyaz", ["white", "ak", "ekru", "krem", "bej", "açık"], "color", 1.0),
            SynonymGroup("kırmızı", ["red", "al", "bordo", "crimson", "kızıl"], "color", 1.0),
            SynonymGroup("mavi", ["blue", "lacivert", "navy", "gök", "gökyüzü"], "color", 1.0),
            SynonymGroup("yeşil", ["green", "yemyeşil", "çimen", "mint"], "color", 1.0),
            SynonymGroup("sarı", ["yellow", "altın", "gold", "golden", "limon"], "color", 1.0),
            SynonymGroup("pembe", ["pink", "fuşya", "rose", "gül", "pudra"], "color", 1.0),
            SynonymGroup("mor", ["purple", "lila", "violet", "menekşe", "eflatun"], "color", 1.0),
            SynonymGroup("gri", ["gray", "grey", "ash", "kül", "antrasit"], "color", 1.0),
            SynonymGroup("kahverengi", ["brown", "bej", "beige", "camel", "kahve"], "color", 1.0),
            SynonymGroup("turuncu", ["orange", "portakal", "amber"], "color", 1.0),
            
            # Malzeme sinonimları
            SynonymGroup("dantel", ["lace", "güpür", "dantela", "dantelli"], "material", 1.0),
            SynonymGroup("tül", ["tulle", "mesh", "file", "tüllü"], "material", 1.0),
            SynonymGroup("pamuk", ["cotton", "pamuklu", "cotton blend", "100% pamuk"], "material", 1.0),
            SynonymGroup("ipek", ["silk", "satin", "ipeksi", "silky"], "material", 1.0),
            SynonymGroup("saten", ["satin", "silk", "parlak", "shiny"], "material", 1.0),
            SynonymGroup("kadife", ["velvet", "kadifeli", "soft"], "material", 1.0),
            SynonymGroup("deri", ["leather", "derili", "faux leather"], "material", 1.0),
            SynonymGroup("jean", ["denim", "kot", "jeans"], "material", 1.0),
            SynonymGroup("örme", ["knit", "knitted", "örgü"], "material", 1.0),
            SynonymGroup("polyester", ["poly", "synthetic"], "material", 0.8),
            SynonymGroup("viskoz", ["viscose", "rayon"], "material", 0.8),
            SynonymGroup("elastan", ["spandex", "lycra", "stretch"], "material", 0.8),
            SynonymGroup("modal", ["modal fiber", "soft modal"], "material", 0.8),
            SynonymGroup("bambu", ["bamboo", "bamboo fiber"], "material", 0.9),
            
            # Giysi türü sinonimları
            SynonymGroup("gecelik", ["nightgown", "nightdress", "gece elbisesi", "uyku elbisesi"], "garment_type", 1.0),
            SynonymGroup("pijama", ["pajama", "pyjama", "ev kıyafeti", "uyku kıyafeti"], "garment_type", 1.0),
            SynonymGroup("sabahlık", ["robe", "bathrobe", "morning gown", "bornoz"], "garment_type", 1.0),
            SynonymGroup("takım", ["set", "suit", "kombin", "ensemble"], "garment_type", 1.0),
            SynonymGroup("elbise", ["dress", "frock", "gown"], "garment_type", 1.0),
            SynonymGroup("bluz", ["blouse", "top", "shirt"], "garment_type", 1.0),
            SynonymGroup("tişört", ["t-shirt", "tshirt", "tee"], "garment_type", 1.0),
            SynonymGroup("şort", ["shorts", "short", "kısa pantolon"], "garment_type", 1.0),
            SynonymGroup("pantolon", ["pants", "trousers", "jean"], "garment_type", 1.0),
            SynonymGroup("etek", ["skirt", "mini", "maxi"], "garment_type", 1.0),
            SynonymGroup("ceket", ["jacket", "blazer", "coat"], "garment_type", 1.0),
            SynonymGroup("hırka", ["cardigan", "sweater"], "garment_type", 1.0),
            SynonymGroup("sütyeni", ["bra", "brassiere"], "garment_type", 1.0),
            SynonymGroup("külot", ["panty", "underwear", "brief"], "garment_type", 1.0),
            
            # Stil sinonimları
            SynonymGroup("dekolteli", ["decollete", "açık yakalı", "göğüs açık", "low cut"], "style", 1.0),
            SynonymGroup("askılı", ["strappy", "strap", "ip askılı", "spaghetti"], "style", 1.0),
            SynonymGroup("kolsuz", ["sleeveless", "tank", "without sleeves"], "style", 1.0),
            SynonymGroup("uzun_kollu", ["long sleeve", "uzun kol", "full sleeve"], "style", 1.0),
            SynonymGroup("kısa_kollu", ["short sleeve", "kısa kol", "half sleeve"], "style", 1.0),
            SynonymGroup("bol_kesim", ["loose", "oversize", "baggy", "relaxed"], "style", 1.0),
            SynonymGroup("dar_kesim", ["tight", "slim", "fit", "fitted"], "style", 1.0),
            SynonymGroup("crop", ["kısa", "cropped", "short"], "style", 1.0),
            SynonymGroup("uzun", ["long", "maxi", "full length"], "style", 1.0),
            SynonymGroup("kısa", ["short", "mini", "brief"], "style", 1.0),
            SynonymGroup("orta_boy", ["midi", "medium", "mid length"], "style", 1.0),
            
            # Kapama sinonimları
            SynonymGroup("düğmeli", ["buttoned", "button", "düğme", "button up"], "closure", 1.0),
            SynonymGroup("fermuarlı", ["zipped", "zipper", "fermuar", "zip up"], "closure", 1.0),
            SynonymGroup("bağlamalı", ["tie", "tied", "lace up", "string"], "closure", 1.0),
            SynonymGroup("çıtçıtlı", ["snap", "press stud", "popper"], "closure", 0.8),
            SynonymGroup("lastikli", ["elastic", "elasticated", "stretch"], "closure", 0.8),
            
            # Yaka sinonimları
            SynonymGroup("v_yaka", ["v neck", "v-neck", "v neckline"], "neckline", 1.0),
            SynonymGroup("yuvarlak_yaka", ["round neck", "crew neck", "round neckline"], "neckline", 1.0),
            SynonymGroup("halter", ["halter neck", "balık sırtı", "halter top"], "neckline", 1.0),
            SynonymGroup("straplez", ["strapless", "bandeau", "tube"], "neckline", 1.0),
            SynonymGroup("göğüs_dekolteli", ["chest decollete", "front decollete"], "neckline", 1.0),
            SynonymGroup("sırt_dekolteli", ["back decollete", "backless", "open back"], "neckline", 1.0),
            SynonymGroup("omuz_dekolteli", ["off shoulder", "shoulder decollete"], "neckline", 1.0),
            
            # Hedef grup sinonimları
            SynonymGroup("hamile", ["pregnant", "maternity", "anne adayı", "gebe", "expectant"], "target_group", 1.0),
            SynonymGroup("lohusa", ["nursing", "emziren", "anne", "postpartum", "breastfeeding"], "target_group", 1.0),
            SynonymGroup("büyük_beden", ["plus size", "large size", "xl", "xxl"], "target_group", 1.0),
            SynonymGroup("genç", ["teen", "teenager", "young", "junior"], "target_group", 0.8),
            SynonymGroup("çocuk", ["kids", "child", "children"], "target_group", 1.0),
            SynonymGroup("bebek", ["baby", "infant", "newborn"], "target_group", 1.0),
            
            # Desen sinonimları
            SynonymGroup("çizgili", ["stripe", "striped", "lines"], "pattern", 1.0),
            SynonymGroup("puantiyeli", ["polka dot", "dotted", "spots"], "pattern", 1.0),
            SynonymGroup("çiçekli", ["floral", "flower", "flowery"], "pattern", 1.0),
            SynonymGroup("geometrik", ["geometric", "geo", "abstract"], "pattern", 1.0),
            SynonymGroup("etnik", ["ethnic", "tribal", "afrika", "african"], "pattern", 1.0),
            SynonymGroup("baskılı", ["print", "printed", "graphic"], "pattern", 1.0),
            SynonymGroup("düz", ["plain", "solid", "solid color"], "pattern", 1.0),
            SynonymGroup("kareli", ["check", "checkered", "plaid"], "pattern", 1.0),
            SynonymGroup("leopar_desen", ["leopard", "animal print"], "pattern", 1.0),
            SynonymGroup("zebra_desen", ["zebra", "zebra print"], "pattern", 1.0),
            
            # Beden sinonimları
            SynonymGroup("XS", ["extra small", "xs", "çok küçük"], "size", 1.0),
            SynonymGroup("S", ["small", "s", "küçük"], "size", 1.0),
            SynonymGroup("M", ["medium", "m", "orta"], "size", 1.0),
            SynonymGroup("L", ["large", "l", "büyük"], "size", 1.0),
            SynonymGroup("XL", ["extra large", "xl", "çok büyük"], "size", 1.0),
            SynonymGroup("XXL", ["2xl", "xxl", "double xl"], "size", 1.0),
            SynonymGroup("XXXL", ["3xl", "xxxl", "triple xl"], "size", 1.0),
        ]
    
    def _build_synonym_index(self):
        """Sinonim indeksini oluştur"""
        self.synonym_index = {}  # synonym -> canonical mapping
        self.canonical_index = {}  # canonical -> SynonymGroup mapping
        
        for group in self.synonym_groups:
            # Canonical term'i kendisine map et
            self.synonym_index[group.canonical] = group.canonical
            self.canonical_index[group.canonical] = group
            
            # Her sinonimi canonical term'e map et
            for synonym in group.synonyms:
                self.synonym_index[synonym.lower()] = group.canonical
    
    def get_canonical_term(self, term: str) -> Optional[str]:
        """
        Terim için canonical (standart) karşılığını getir
        
        Args:
            term: Aranacak terim
            
        Returns:
            str: Canonical terim veya None
        """
        return self.synonym_index.get(term.lower())
    
    def get_synonyms(self, term: str) -> List[str]:
        """
        Terim için tüm sinonimları getir
        
        Args:
            term: Aranacak terim
            
        Returns:
            List[str]: Sinonimler listesi
        """
        canonical = self.get_canonical_term(term)
        if canonical and canonical in self.canonical_index:
            group = self.canonical_index[canonical]
            return group.synonyms.copy()
        return []
    
    def get_synonym_group(self, term: str) -> Optional[SynonymGroup]:
        """
        Terim için sinonim grubunu getir
        
        Args:
            term: Aranacak terim
            
        Returns:
            SynonymGroup: Sinonim grubu veya None
        """
        canonical = self.get_canonical_term(term)
        if canonical:
            return self.canonical_index.get(canonical)
        return None
    
    def expand_terms(self, terms: List[str]) -> Dict[str, List[str]]:
        """
        Terim listesini sinonimlerle genişlet
        
        Args:
            terms: Genişletilecek terimler
            
        Returns:
            Dict: term -> [synonyms] mapping
        """
        expanded = {}
        
        for term in terms:
            synonyms = self.get_synonyms(term)
            canonical = self.get_canonical_term(term)
            
            # Canonical term + synonyms
            all_terms = [canonical] if canonical else []
            all_terms.extend(synonyms)
            all_terms = list(set(all_terms))  # Duplicate'leri temizle
            
            expanded[term] = all_terms
        
        return expanded
    
    def normalize_feature_value(self, value: str) -> str:
        """
        Özellik değerini normalize et (canonical term'e çevir)
        
        Args:
            value: Normalize edilecek değer
            
        Returns:
            str: Normalize edilmiş değer
        """
        canonical = self.get_canonical_term(value)
        return canonical if canonical else value
    
    def calculate_synonym_similarity(self, term1: str, term2: str) -> float:
        """
        İki terim arasında sinonim benzerliği hesapla
        
        Args:
            term1: İlk terim
            term2: İkinci terim
            
        Returns:
            float: Benzerlik skoru (0-1)
        """
        canonical1 = self.get_canonical_term(term1)
        canonical2 = self.get_canonical_term(term2)
        
        # Aynı canonical term'e sahipse
        if canonical1 and canonical2 and canonical1 == canonical2:
            return 1.0
        
        # Birbirinin sinonimi mi kontrol et
        if canonical1:
            synonyms1 = self.get_synonyms(canonical1)
            if term2.lower() in [s.lower() for s in synonyms1]:
                return 0.9
        
        if canonical2:
            synonyms2 = self.get_synonyms(canonical2)
            if term1.lower() in [s.lower() for s in synonyms2]:
                return 0.9
        
        return 0.0
    
    def get_category_terms(self, category: str) -> Dict[str, List[str]]:
        """
        Belirli kategori için tüm terimleri getir
        
        Args:
            category: Kategori adı
            
        Returns:
            Dict: canonical -> synonyms mapping
        """
        category_terms = {}
        
        for group in self.synonym_groups:
            if group.category == category:
                category_terms[group.canonical] = group.synonyms
        
        return category_terms
    
    def get_all_categories(self) -> List[str]:
        """Tüm kategorileri getir"""
        categories = set()
        for group in self.synonym_groups:
            categories.add(group.category)
        return list(categories)
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """Mapping istatistikleri"""
        stats = {
            'total_groups': len(self.synonym_groups),
            'total_synonyms': len(self.synonym_index),
            'categories': len(self.get_all_categories()),
            'category_breakdown': {}
        }
        
        # Kategori bazında breakdown
        for category in self.get_all_categories():
            category_groups = [g for g in self.synonym_groups if g.category == category]
            total_synonyms = sum(len(g.synonyms) for g in category_groups)
            
            stats['category_breakdown'][category] = {
                'groups': len(category_groups),
                'synonyms': total_synonyms
            }
        
        return stats

# Test fonksiyonu
def test_synonym_mapper():
    """Synonym mapper test"""
    
    mapper = FeatureSynonymMapper()
    
    print("🔄 Feature Synonym Mapper Test:")
    print("=" * 40)
    
    # Canonical term testleri
    print("\n📝 Canonical Term Mapping:")
    test_terms = ['black', 'lace', 'nightgown', 'pregnant', 'striped']
    for term in test_terms:
        canonical = mapper.get_canonical_term(term)
        print(f"  '{term}' -> '{canonical}'")
    
    # Sinonim genişletme testleri
    print("\n🔍 Synonym Expansion:")
    test_expand = ['siyah', 'dantel', 'gecelik']
    for term in test_expand:
        synonyms = mapper.get_synonyms(term)
        print(f"  '{term}': {synonyms[:4]}")  # İlk 4 sinonim
    
    # Benzerlik testleri
    print("\n📊 Synonym Similarity:")
    similarity_tests = [
        ('siyah', 'black'),
        ('dantel', 'lace'),
        ('gecelik', 'nightgown'),
        ('hamile', 'pregnant'),
        ('siyah', 'beyaz')  # Farklı terimler
    ]
    
    for term1, term2 in similarity_tests:
        similarity = mapper.calculate_synonym_similarity(term1, term2)
        print(f"  '{term1}' <-> '{term2}': {similarity:.2f}")
    
    # İstatistikler
    print("\n📈 Mapping Statistics:")
    stats = mapper.get_mapping_stats()
    print(f"  Total groups: {stats['total_groups']}")
    print(f"  Total synonyms: {stats['total_synonyms']}")
    print(f"  Categories: {stats['categories']}")
    
    print("\n📊 Category Breakdown:")
    for category, info in stats['category_breakdown'].items():
        print(f"  {category}: {info['groups']} groups, {info['synonyms']} synonyms")

if __name__ == "__main__":
    test_synonym_mapper()