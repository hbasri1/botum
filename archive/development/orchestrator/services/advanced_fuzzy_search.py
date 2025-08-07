#!/usr/bin/env python3
"""
Advanced Fuzzy Search - Feature-aware fuzzy matching with Turkish language support
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher

try:
    from .product_feature_extractor import ProductFeatureExtractor, ProductFeature
    from .feature_synonym_mapper import FeatureSynonymMapper
    from .turkish_language_rules import TurkishLanguageRules
except ImportError:
    from product_feature_extractor import ProductFeatureExtractor, ProductFeature
    from feature_synonym_mapper import FeatureSynonymMapper
    from turkish_language_rules import TurkishLanguageRules

logger = logging.getLogger(__name__)

@dataclass
class FuzzyMatch:
    """Fuzzy match result"""
    product: Dict[str, Any]
    overall_score: float
    text_score: float
    feature_score: float
    phonetic_score: float
    confidence: float
    matched_terms: List[str]
    match_explanation: str

class TurkishPhoneticMatcher:
    """Türkçe fonetik benzerlik matcher'ı"""
    
    def __init__(self):
        # Türkçe fonetik benzerlikler
        self.phonetic_groups = [
            ['c', 'ç'],
            ['g', 'ğ'],
            ['i', 'ı', 'İ', 'I'],
            ['o', 'ö'],
            ['s', 'ş'],
            ['u', 'ü'],
            ['k', 'g'],  # Yumuşama
            ['p', 'b'],  # Yumuşama
            ['t', 'd'],  # Yumuşama
            ['f', 'v'],  # Benzer sesler
        ]
        
        # Phonetic mapping oluştur
        self.phonetic_map = {}
        for group in self.phonetic_groups:
            canonical = group[0]
            for char in group:
                self.phonetic_map[char.lower()] = canonical
    
    def phonetic_normalize(self, text: str) -> str:
        """Metni fonetik olarak normalize et"""
        normalized = ""
        for char in text.lower():
            normalized += self.phonetic_map.get(char, char)
        return normalized
    
    def phonetic_similarity(self, text1: str, text2: str) -> float:
        """İki metin arasında fonetik benzerlik hesapla"""
        norm1 = self.phonetic_normalize(text1)
        norm2 = self.phonetic_normalize(text2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()

class AdvancedFuzzySearch:
    """Advanced fuzzy search with feature awareness"""
    
    def __init__(self):
        self.feature_extractor = ProductFeatureExtractor()
        self.synonym_mapper = FeatureSynonymMapper()
        self.turkish_rules = TurkishLanguageRules()
        self.phonetic_matcher = TurkishPhoneticMatcher()
        
        # Fuzzy matching weights
        self.scoring_weights = {
            'exact_match': 1.0,
            'feature_match': 0.9,
            'fuzzy_ratio': 0.8,
            'token_sort': 0.7,
            'token_set': 0.6,
            'phonetic': 0.5,
            'partial': 0.4,
            'substring': 0.3
        }
        
        # Turkish-specific bonuses
        self.turkish_bonuses = {
            'suffix_match': 0.15,
            'root_match': 0.20,
            'synonym_match': 0.25,
            'category_match': 0.10
        }
    
    def _try_import_rapidfuzz(self):
        """rapidfuzz import'unu dene"""
        try:
            from rapidfuzz import fuzz, process
            return fuzz, process
        except ImportError:
            logger.warning("rapidfuzz not available, using fallback fuzzy matching")
            return None, None
    
    async def search(self, query: str, products: List[Dict[str, Any]], 
                    limit: int = 10) -> List[FuzzyMatch]:
        """Advanced fuzzy search"""
        try:
            fuzz, process = self._try_import_rapidfuzz()
            
            if fuzz:
                return await self._rapidfuzz_search(query, products, limit, fuzz)
            else:
                return await self._fallback_fuzzy_search(query, products, limit)
                
        except Exception as e:
            logger.error(f"Advanced fuzzy search error: {str(e)}")
            return []
    
    async def _rapidfuzz_search(self, query: str, products: List[Dict[str, Any]], 
                               limit: int, fuzz) -> List[FuzzyMatch]:
        """RapidFuzz ile gelişmiş fuzzy search"""
        # Query'yi normalize et ve özellikleri çıkar
        normalized_query = self.turkish_rules.normalize_for_search(query)
        query_features = self.feature_extractor.extract_features(query)
        
        matches = []
        
        for product in products:
            product_name = product.get('name', '')
            normalized_product = self.turkish_rules.normalize_for_search(product_name)
            product_features = self.feature_extractor.extract_features(product_name)
            
            # Multiple fuzzy scoring methods
            scores = self._calculate_fuzzy_scores(
                normalized_query, normalized_product, query, product_name, fuzz
            )
            
            # Feature-based scoring
            feature_score = self._calculate_feature_fuzzy_score(query_features, product_features)
            
            # Phonetic scoring
            phonetic_score = self.phonetic_matcher.phonetic_similarity(query, product_name)
            
            # Turkish-specific bonuses
            turkish_bonus = self._calculate_turkish_bonus(
                query, product_name, normalized_query, normalized_product
            )
            
            # Combined scoring
            text_score = max(scores.values())
            overall_score = (
                text_score * 0.5 +
                feature_score * 0.3 +
                phonetic_score * 0.2 +
                turkish_bonus
            )
            
            if overall_score > 0.4:  # Threshold
                confidence = self._calculate_fuzzy_confidence(
                    overall_score, text_score, feature_score, scores
                )
                
                matched_terms = self._find_matched_terms(
                    query, product_name, query_features, product_features
                )
                
                explanation = self._generate_match_explanation(
                    scores, feature_score, phonetic_score, turkish_bonus
                )
                
                match = FuzzyMatch(
                    product=product,
                    overall_score=overall_score,
                    text_score=text_score,
                    feature_score=feature_score,
                    phonetic_score=phonetic_score,
                    confidence=confidence,
                    matched_terms=matched_terms,
                    match_explanation=explanation
                )
                matches.append(match)
        
        # Sort by overall score
        matches.sort(key=lambda x: x.overall_score, reverse=True)
        return matches[:limit]
    
    def _calculate_fuzzy_scores(self, norm_query: str, norm_product: str, 
                               orig_query: str, orig_product: str, fuzz) -> Dict[str, float]:
        """Farklı fuzzy scoring yöntemlerini hesapla"""
        scores = {}
        
        try:
            # Basic ratios
            scores['ratio'] = fuzz.ratio(norm_query, norm_product) / 100.0
            scores['partial_ratio'] = fuzz.partial_ratio(norm_query, norm_product) / 100.0
            
            # Token-based ratios
            scores['token_sort_ratio'] = fuzz.token_sort_ratio(norm_query, norm_product) / 100.0
            scores['token_set_ratio'] = fuzz.token_set_ratio(norm_query, norm_product) / 100.0
            
            # WRatio (weighted ratio)
            scores['wratio'] = fuzz.WRatio(norm_query, norm_product) / 100.0
            
            # QRatio (quick ratio)
            scores['qratio'] = fuzz.QRatio(norm_query, norm_product) / 100.0
            
        except Exception as e:
            logger.error(f"RapidFuzz scoring error: {str(e)}")
            # Fallback to basic scoring
            scores['ratio'] = self._basic_similarity(norm_query, norm_product)
        
        return scores
    
    def _calculate_feature_fuzzy_score(self, query_features: List[ProductFeature], 
                                     product_features: List[ProductFeature]) -> float:
        """Feature-based fuzzy scoring"""
        if not query_features or not product_features:
            return 0.0
        
        query_values = {f.value for f in query_features}
        product_values = {f.value for f in product_features}
        
        # Direct feature matches
        direct_matches = query_values.intersection(product_values)
        direct_score = len(direct_matches) / len(query_values) if query_values else 0.0
        
        # Fuzzy feature matches
        fuzzy_matches = 0
        for query_feature in query_features:
            best_fuzzy_score = 0.0
            
            for product_feature in product_features:
                # Synonym similarity
                synonym_sim = self.synonym_mapper.calculate_synonym_similarity(
                    query_feature.value, product_feature.value
                )
                
                # Text similarity between feature values
                text_sim = self._basic_similarity(query_feature.value, product_feature.value)
                
                fuzzy_score = max(synonym_sim, text_sim)
                if fuzzy_score > best_fuzzy_score:
                    best_fuzzy_score = fuzzy_score
            
            if best_fuzzy_score > 0.6:
                fuzzy_matches += best_fuzzy_score
        
        fuzzy_score = fuzzy_matches / len(query_features) if query_features else 0.0
        
        # Combine direct and fuzzy scores
        return direct_score * 0.7 + fuzzy_score * 0.3
    
    def _calculate_turkish_bonus(self, query: str, product_name: str, 
                               norm_query: str, norm_product: str) -> float:
        """Türkçe-specific bonus hesapla"""
        bonus = 0.0
        
        # Root word matching bonus
        query_roots = self.turkish_rules.extract_root_words(query)
        product_roots = self.turkish_rules.extract_root_words(product_name)
        
        if query_roots and product_roots:
            root_overlap = len(query_roots.intersection(product_roots))
            if root_overlap > 0:
                bonus += self.turkish_bonuses['root_match'] * (root_overlap / len(query_roots))
        
        # Suffix handling bonus
        if self._has_similar_suffixes(norm_query, norm_product):
            bonus += self.turkish_bonuses['suffix_match']
        
        # Synonym expansion bonus
        expanded_queries = self.turkish_rules.expand_query_with_synonyms(query)
        for expanded in expanded_queries[1:]:  # Skip original query
            if self._basic_similarity(expanded.lower(), product_name.lower()) > 0.7:
                bonus += self.turkish_bonuses['synonym_match']
                break
        
        return min(bonus, 0.5)  # Cap bonus at 0.5
    
    def _has_similar_suffixes(self, text1: str, text2: str) -> bool:
        """Benzer Türkçe ekleri kontrol et"""
        # Common Turkish suffixes
        suffixes = ['ler', 'lar', 'leri', 'ları', 'nin', 'nın', 'nun', 'nün']
        
        for suffix in suffixes:
            if text1.endswith(suffix) and text2.endswith(suffix):
                return True
            
            # Check if removing suffix makes them more similar
            if text1.endswith(suffix):
                root1 = text1[:-len(suffix)]
                if self._basic_similarity(root1, text2) > 0.8:
                    return True
            
            if text2.endswith(suffix):
                root2 = text2[:-len(suffix)]
                if self._basic_similarity(text1, root2) > 0.8:
                    return True
        
        return False
    
    def _calculate_fuzzy_confidence(self, overall_score: float, text_score: float, 
                                  feature_score: float, scores: Dict[str, float]) -> float:
        """Fuzzy match confidence hesapla"""
        # Base confidence from overall score
        base_confidence = overall_score
        
        # Bonus for consistent scores across methods
        score_values = list(scores.values())
        if score_values:
            score_std = self._calculate_std(score_values)
            consistency_bonus = max(0, (0.2 - score_std) * 2)  # Lower std = higher bonus
            base_confidence += consistency_bonus
        
        # Bonus for strong feature matches
        if feature_score > 0.8:
            base_confidence += 0.1
        
        # Penalty for very low text scores
        if text_score < 0.3:
            base_confidence -= 0.2
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _calculate_std(self, values: List[float]) -> float:
        """Standard deviation hesapla"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _find_matched_terms(self, query: str, product_name: str, 
                          query_features: List[ProductFeature], 
                          product_features: List[ProductFeature]) -> List[str]:
        """Matched terms'leri bul"""
        matched = []
        
        # Direct word matches
        query_words = set(query.lower().split())
        product_words = set(product_name.lower().split())
        direct_matches = query_words.intersection(product_words)
        matched.extend(direct_matches)
        
        # Feature matches
        query_feature_values = {f.value for f in query_features}
        product_feature_values = {f.value for f in product_features}
        feature_matches = query_feature_values.intersection(product_feature_values)
        matched.extend(feature_matches)
        
        # Remove duplicates and return
        return list(set(matched))
    
    def _generate_match_explanation(self, scores: Dict[str, float], 
                                  feature_score: float, phonetic_score: float, 
                                  turkish_bonus: float) -> str:
        """Match açıklaması oluştur"""
        best_method = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_method]
        
        explanation = f"Fuzzy match via {best_method} ({best_score:.2f})"
        
        if feature_score > 0.5:
            explanation += f", features ({feature_score:.2f})"
        
        if phonetic_score > 0.6:
            explanation += f", phonetic ({phonetic_score:.2f})"
        
        if turkish_bonus > 0.1:
            explanation += f", Turkish bonus ({turkish_bonus:.2f})"
        
        return explanation
    
    async def _fallback_fuzzy_search(self, query: str, products: List[Dict[str, Any]], 
                                   limit: int) -> List[FuzzyMatch]:
        """Fallback fuzzy search (rapidfuzz olmadan)"""
        normalized_query = self.turkish_rules.normalize_for_search(query)
        query_features = self.feature_extractor.extract_features(query)
        
        matches = []
        
        for product in products:
            product_name = product.get('name', '')
            normalized_product = self.turkish_rules.normalize_for_search(product_name)
            product_features = self.feature_extractor.extract_features(product_name)
            
            # Basic similarity scores
            text_score = self._basic_similarity(normalized_query, normalized_product)
            feature_score = self._calculate_feature_fuzzy_score(query_features, product_features)
            phonetic_score = self.phonetic_matcher.phonetic_similarity(query, product_name)
            
            # Turkish bonus
            turkish_bonus = self._calculate_turkish_bonus(
                query, product_name, normalized_query, normalized_product
            )
            
            overall_score = (
                text_score * 0.5 +
                feature_score * 0.3 +
                phonetic_score * 0.2 +
                turkish_bonus
            )
            
            if overall_score > 0.4:
                confidence = min(overall_score * 1.1, 1.0)
                matched_terms = self._find_matched_terms(
                    query, product_name, query_features, product_features
                )
                
                match = FuzzyMatch(
                    product=product,
                    overall_score=overall_score,
                    text_score=text_score,
                    feature_score=feature_score,
                    phonetic_score=phonetic_score,
                    confidence=confidence,
                    matched_terms=matched_terms,
                    match_explanation=f"Fallback fuzzy match (text: {text_score:.2f})"
                )
                matches.append(match)
        
        matches.sort(key=lambda x: x.overall_score, reverse=True)
        return matches[:limit]
    
    def _basic_similarity(self, text1: str, text2: str) -> float:
        """Basic text similarity"""
        if not text1 or not text2:
            return 0.0
        
        # Jaccard similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_fuzzy_stats(self) -> Dict[str, Any]:
        """Fuzzy search istatistikleri"""
        fuzz, _ = self._try_import_rapidfuzz()
        
        return {
            'rapidfuzz_available': fuzz is not None,
            'scoring_weights': self.scoring_weights,
            'turkish_bonuses': self.turkish_bonuses,
            'phonetic_groups': len(self.phonetic_matcher.phonetic_groups)
        }

# Test fonksiyonu
async def test_advanced_fuzzy_search():
    """Advanced fuzzy search test"""
    
    # Test ürünleri
    test_products = [
        {
            'id': 1,
            'name': 'Afrika Etnik Baskılı Dantelli Gecelik',
            'category': 'İç Giyim'
        },
        {
            'id': 2,
            'name': 'Dantelli Önü Düğmeli Hamile Lohusa Gecelik',
            'category': 'İç Giyim'
        },
        {
            'id': 3,
            'name': 'Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı',
            'category': 'İç Giyim'
        },
        {
            'id': 4,
            'name': 'Siyah Tüllü Askılı Gecelik',
            'category': 'İç Giyim'
        },
        {
            'id': 5,
            'name': 'Beyaz Pamuklu Uzun Kollu Pijama Takımı',
            'category': 'İç Giyim'
        }
    ]
    
    fuzzy_search = AdvancedFuzzySearch()
    
    print("🔍 Advanced Fuzzy Search Test:")
    print("=" * 50)
    
    # Test sorguları (typos ve variations ile)
    test_queries = [
        "siyah gecelik",
        "siyah gecelig",  # typo
        "hamile lohusa geceliği",
        "hamile lohusa geceligi",  # typo
        "danteli takım",  # missing 'l'
        "göğüs dekolteli",
        "gogus dekolteli",  # missing ğ
        "afrika etnik",
        "pamuklu pijama",
        "pamuklu pyjama"  # variant spelling
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        
        matches = await fuzzy_search.search(query, test_products, limit=3)
        
        if matches:
            print(f"✅ Found {len(matches)} fuzzy matches:")
            for i, match in enumerate(matches, 1):
                print(f"  {i}. {match.product['name']}")
                print(f"     Overall: {match.overall_score:.3f}")
                print(f"     Text: {match.text_score:.3f}, Feature: {match.feature_score:.3f}")
                print(f"     Phonetic: {match.phonetic_score:.3f}, Confidence: {match.confidence:.3f}")
                print(f"     Explanation: {match.match_explanation}")
                
                if match.matched_terms:
                    print(f"     Matched terms: {', '.join(match.matched_terms)}")
        else:
            print("❌ No fuzzy matches found")
    
    # İstatistikler
    stats = fuzzy_search.get_fuzzy_stats()
    print(f"\n📊 Advanced Fuzzy Search Stats:")
    print(f"  RapidFuzz available: {stats['rapidfuzz_available']}")
    print(f"  Scoring methods: {len(stats['scoring_weights'])}")
    print(f"  Turkish bonuses: {len(stats['turkish_bonuses'])}")
    print(f"  Phonetic groups: {stats['phonetic_groups']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_advanced_fuzzy_search())