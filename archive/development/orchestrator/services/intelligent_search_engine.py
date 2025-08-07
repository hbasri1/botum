#!/usr/bin/env python3
"""
Intelligent Search Engine - Multi-modal search engine with parallel execution
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import concurrent.futures

try:
    from .product_feature_extractor import ProductFeatureExtractor
    from .turkish_language_rules import TurkishLanguageRules
    from .feature_synonym_mapper import FeatureSynonymMapper
except ImportError:
    from product_feature_extractor import ProductFeatureExtractor
    from turkish_language_rules import TurkishLanguageRules
    from feature_synonym_mapper import FeatureSynonymMapper

logger = logging.getLogger(__name__)

class SearchMethod(Enum):
    """Arama yöntemleri"""
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"
    KEYWORD = "keyword"
    FEATURE_BASED = "feature_based"

@dataclass
class SearchMatch:
    """Arama sonucu match'i"""
    product: Dict[str, Any]
    score: float
    method: SearchMethod
    confidence: float
    explanation: str
    feature_matches: List[str] = None
    
    def __post_init__(self):
        if self.feature_matches is None:
            self.feature_matches = []

@dataclass
class SearchResult:
    """Arama sonucu"""
    matches: List[SearchMatch]
    query: str
    total_time_ms: int
    method_times: Dict[SearchMethod, int]
    overall_confidence: float
    explanation: str
    alternatives: List[str] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []

class BaseSearchMethod(ABC):
    """Base search method interface"""
    
    @abstractmethod
    async def search(self, query: str, products: List[Dict], limit: int = 10) -> List[SearchMatch]:
        """Arama yap"""
        pass
    
    @abstractmethod
    def get_method_name(self) -> SearchMethod:
        """Method adını döndür"""
        pass

class SemanticSearchMethod(BaseSearchMethod):
    """Semantic search implementation"""
    
    def __init__(self):
        self.feature_extractor = ProductFeatureExtractor()
    
    async def search(self, query: str, products: List[Dict], limit: int = 10) -> List[SearchMatch]:
        """Semantic search yap"""
        try:
            # Query'den özellikleri çıkar
            query_features = self.feature_extractor.extract_features(query)
            query_feature_values = [f.value for f in query_features]
            
            matches = []
            
            for product in products:
                # Ürün özelliklerini çıkar
                product_features = self.feature_extractor.extract_features(product.get('name', ''))
                product_feature_values = [f.value for f in product_features]
                
                # Feature overlap hesapla
                common_features = set(query_feature_values).intersection(set(product_feature_values))
                
                # Improved scoring algorithm
                if query_feature_values:
                    # Base overlap ratio
                    overlap_ratio = len(common_features) / len(query_feature_values)
                    
                    # Penalty for low match count when query has many features
                    if len(query_feature_values) >= 3 and len(common_features) <= 1:
                        overlap_ratio *= 0.3  # Heavy penalty for single feature match on complex query
                    elif len(query_feature_values) >= 2 and len(common_features) <= 1:
                        overlap_ratio *= 0.5  # Moderate penalty
                    
                    # Bonus for high match count
                    if len(common_features) >= 2:
                        overlap_ratio *= 1.2  # Bonus for multiple feature matches
                else:
                    overlap_ratio = 0.0
                
                # Text similarity
                text_similarity = self._calculate_text_similarity(query, product.get('name', ''))
                
                # Combined semantic score with better weighting
                semantic_score = overlap_ratio * 0.7 + text_similarity * 0.3
                
                if semantic_score > 0.2:  # Lowered threshold
                    confidence = min(semantic_score * 1.2, 1.0)
                    
                    match = SearchMatch(
                        product=product,
                        score=semantic_score,
                        method=SearchMethod.SEMANTIC,
                        confidence=confidence,
                        explanation=f"Semantic match with {len(common_features)} common features",
                        feature_matches=list(common_features)
                    )
                    matches.append(match)
            
            # Score'a göre sırala
            matches.sort(key=lambda x: x.score, reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Basit text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_method_name(self) -> SearchMethod:
        return SearchMethod.SEMANTIC

class FuzzySearchMethod(BaseSearchMethod):
    """Fuzzy search implementation"""
    
    def __init__(self):
        self.turkish_rules = TurkishLanguageRules()
    
    async def search(self, query: str, products: List[Dict], limit: int = 10) -> List[SearchMatch]:
        """Fuzzy search yap"""
        try:
            from rapidfuzz import fuzz
            
            normalized_query = self.turkish_rules.normalize_for_search(query)
            matches = []
            
            for product in products:
                product_name = product.get('name', '')
                normalized_product = self.turkish_rules.normalize_for_search(product_name)
                
                # Farklı fuzzy matching yöntemleri
                ratio_score = fuzz.ratio(normalized_query, normalized_product) / 100.0
                token_sort_score = fuzz.token_sort_ratio(normalized_query, normalized_product) / 100.0
                token_set_score = fuzz.token_set_ratio(normalized_query, normalized_product) / 100.0
                
                # En yüksek skoru al
                fuzzy_score = max(ratio_score, token_sort_score, token_set_score)
                
                if fuzzy_score > 0.6:  # Threshold
                    confidence = fuzzy_score * 0.9  # Fuzzy biraz daha düşük confidence
                    
                    match = SearchMatch(
                        product=product,
                        score=fuzzy_score,
                        method=SearchMethod.FUZZY,
                        confidence=confidence,
                        explanation=f"Fuzzy match (ratio: {ratio_score:.2f}, token_set: {token_set_score:.2f})"
                    )
                    matches.append(match)
            
            matches.sort(key=lambda x: x.score, reverse=True)
            return matches[:limit]
            
        except ImportError:
            logger.warning("rapidfuzz not available, using basic fuzzy matching")
            return await self._basic_fuzzy_search(query, products, limit)
        except Exception as e:
            logger.error(f"Fuzzy search error: {str(e)}")
            return []
    
    async def _basic_fuzzy_search(self, query: str, products: List[Dict], limit: int) -> List[SearchMatch]:
        """Basic fuzzy search fallback"""
        normalized_query = self.turkish_rules.normalize_for_search(query)
        query_words = set(normalized_query.split())
        matches = []
        
        for product in products:
            product_name = product.get('name', '')
            normalized_product = self.turkish_rules.normalize_for_search(product_name)
            product_words = set(normalized_product.split())
            
            # Jaccard similarity
            if query_words and product_words:
                intersection = len(query_words.intersection(product_words))
                union = len(query_words.union(product_words))
                similarity = intersection / union if union > 0 else 0.0
                
                if similarity > 0.3:
                    match = SearchMatch(
                        product=product,
                        score=similarity,
                        method=SearchMethod.FUZZY,
                        confidence=similarity * 0.8,
                        explanation=f"Basic fuzzy match ({intersection}/{union} words)"
                    )
                    matches.append(match)
        
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:limit]
    
    def get_method_name(self) -> SearchMethod:
        return SearchMethod.FUZZY

class KeywordSearchMethod(BaseSearchMethod):
    """Keyword search implementation"""
    
    def __init__(self):
        self.synonym_mapper = FeatureSynonymMapper()
        self.turkish_rules = TurkishLanguageRules()
    
    async def search(self, query: str, products: List[Dict], limit: int = 10) -> List[SearchMatch]:
        """Keyword search yap"""
        try:
            # Query'yi normalize et ve genişlet
            normalized_query = self.turkish_rules.normalize_for_search(query)
            expanded_queries = self.turkish_rules.expand_query_with_synonyms(normalized_query)
            
            matches = []
            
            for product in products:
                product_name = product.get('name', '')
                product_desc = product.get('description', '')
                product_text = f"{product_name} {product_desc}".lower()
                
                max_score = 0.0
                best_explanation = ""
                
                # Her genişletilmiş query için test et
                for expanded_query in expanded_queries:
                    query_words = expanded_query.lower().split()
                    matched_words = 0
                    
                    for word in query_words:
                        if word in product_text:
                            matched_words += 1
                    
                    if query_words:
                        score = matched_words / len(query_words)
                        if score > max_score:
                            max_score = score
                            best_explanation = f"Keyword match: {matched_words}/{len(query_words)} words"
                
                if max_score > 0.5:  # Threshold
                    confidence = max_score * 0.7  # Keyword search düşük confidence
                    
                    match = SearchMatch(
                        product=product,
                        score=max_score,
                        method=SearchMethod.KEYWORD,
                        confidence=confidence,
                        explanation=best_explanation
                    )
                    matches.append(match)
            
            matches.sort(key=lambda x: x.score, reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Keyword search error: {str(e)}")
            return []
    
    def get_method_name(self) -> SearchMethod:
        return SearchMethod.KEYWORD

class FeatureBasedSearchMethod(BaseSearchMethod):
    """Feature-based search implementation"""
    
    def __init__(self):
        self.feature_extractor = ProductFeatureExtractor()
        self.synonym_mapper = FeatureSynonymMapper()
    
    async def search(self, query: str, products: List[Dict], limit: int = 10) -> List[SearchMatch]:
        """Feature-based search yap"""
        try:
            # Query'den özellikleri çıkar
            query_features = self.feature_extractor.extract_features(query)
            
            if not query_features:
                return []
            
            matches = []
            
            for product in products:
                # Ürün özelliklerini çıkar
                product_features = self.feature_extractor.extract_features(product.get('name', ''))
                
                # Feature matching score hesapla
                feature_score = self._calculate_feature_score(query_features, product_features)
                
                if feature_score > 0.4:  # Threshold
                    confidence = min(feature_score * 1.1, 1.0)
                    
                    # Matched features'ları bul
                    matched_features = self._find_matched_features(query_features, product_features)
                    
                    match = SearchMatch(
                        product=product,
                        score=feature_score,
                        method=SearchMethod.FEATURE_BASED,
                        confidence=confidence,
                        explanation=f"Feature-based match with {len(matched_features)} features",
                        feature_matches=matched_features
                    )
                    matches.append(match)
            
            matches.sort(key=lambda x: x.score, reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Feature-based search error: {str(e)}")
            return []
    
    def _calculate_feature_score(self, query_features, product_features) -> float:
        """Feature matching score hesapla"""
        if not query_features or not product_features:
            return 0.0
        
        query_values = {f.value for f in query_features}
        product_values = {f.value for f in product_features}
        
        # Direct matches
        direct_matches = query_values.intersection(product_values)
        direct_score = len(direct_matches) / len(query_values) if query_values else 0.0
        
        # Synonym matches
        synonym_matches = 0
        for query_feature in query_features:
            for product_feature in product_features:
                similarity = self.synonym_mapper.calculate_synonym_similarity(
                    query_feature.value, product_feature.value
                )
                if similarity > 0.8:
                    synonym_matches += 1
                    break
        
        synonym_score = synonym_matches / len(query_features) if query_features else 0.0
        
        # Weighted combination
        return direct_score * 0.7 + synonym_score * 0.3
    
    def _find_matched_features(self, query_features, product_features) -> List[str]:
        """Matched features'ları bul"""
        matched = []
        
        query_values = {f.value for f in query_features}
        product_values = {f.value for f in product_features}
        
        # Direct matches
        direct_matches = query_values.intersection(product_values)
        matched.extend(direct_matches)
        
        # Synonym matches
        for query_feature in query_features:
            for product_feature in product_features:
                similarity = self.synonym_mapper.calculate_synonym_similarity(
                    query_feature.value, product_feature.value
                )
                if similarity > 0.8 and query_feature.value not in matched:
                    matched.append(f"{query_feature.value}~{product_feature.value}")
        
        return matched
    
    def get_method_name(self) -> SearchMethod:
        return SearchMethod.FEATURE_BASED

class IntelligentSearchEngine:
    """Multi-modal intelligent search engine"""
    
    def __init__(self):
        self.search_methods = {
            SearchMethod.SEMANTIC: SemanticSearchMethod(),
            SearchMethod.FUZZY: FuzzySearchMethod(),
            SearchMethod.KEYWORD: KeywordSearchMethod(),
            SearchMethod.FEATURE_BASED: FeatureBasedSearchMethod()
        }
        
        self.method_weights = {
            SearchMethod.SEMANTIC: 1.0,
            SearchMethod.FEATURE_BASED: 0.9,
            SearchMethod.FUZZY: 0.8,
            SearchMethod.KEYWORD: 0.6
        }
        
        self.feature_extractor = ProductFeatureExtractor()
        self.turkish_rules = TurkishLanguageRules()
    
    async def search(self, query: str, products: List[Dict], 
                    methods: List[SearchMethod] = None, 
                    limit: int = 10) -> SearchResult:
        """
        Multi-modal search yap
        
        Args:
            query: Arama sorgusu
            products: Ürün listesi
            methods: Kullanılacak arama yöntemleri (None = hepsi)
            limit: Maksimum sonuç sayısı
            
        Returns:
            SearchResult: Arama sonucu
        """
        start_time = time.time()
        
        if methods is None:
            methods = list(self.search_methods.keys())
        
        # Parallel search execution
        method_results = {}
        method_times = {}
        
        tasks = []
        for method in methods:
            if method in self.search_methods:
                task = self._execute_search_method(method, query, products, limit * 2)
                tasks.append((method, task))
        
        # Execute all methods in parallel
        for method, task in tasks:
            method_start = time.time()
            try:
                results = await task
                method_results[method] = results
                method_times[method] = int((time.time() - method_start) * 1000)
            except Exception as e:
                logger.error(f"Search method {method} failed: {str(e)}")
                method_results[method] = []
                method_times[method] = 0
        
        # Fuse results
        fused_matches = self._fuse_results(method_results, query)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(fused_matches)
        
        # Generate explanation
        explanation = self._generate_explanation(method_results, fused_matches)
        
        # Generate alternatives if confidence is low
        alternatives = []
        if overall_confidence < 0.6:
            alternatives = self._generate_alternatives(query, products)
        
        total_time = int((time.time() - start_time) * 1000)
        
        return SearchResult(
            matches=fused_matches[:limit],
            query=query,
            total_time_ms=total_time,
            method_times=method_times,
            overall_confidence=overall_confidence,
            explanation=explanation,
            alternatives=alternatives
        )
    
    async def _execute_search_method(self, method: SearchMethod, query: str, 
                                   products: List[Dict], limit: int) -> List[SearchMatch]:
        """Tek bir search method'u execute et"""
        search_method = self.search_methods[method]
        return await search_method.search(query, products, limit)
    
    def _fuse_results(self, method_results: Dict[SearchMethod, List[SearchMatch]], 
                     query: str) -> List[SearchMatch]:
        """Farklı method sonuçlarını birleştir"""
        product_scores = {}  # product_id -> {method: match}
        
        # Her method'un sonuçlarını topla
        for method, matches in method_results.items():
            weight = self.method_weights.get(method, 1.0)
            
            for match in matches:
                product_id = match.product.get('id', str(hash(match.product.get('name', ''))))
                
                if product_id not in product_scores:
                    product_scores[product_id] = {
                        'product': match.product,
                        'method_matches': {},
                        'total_score': 0.0,
                        'total_confidence': 0.0,
                        'method_count': 0
                    }
                
                # Weighted score ekle
                weighted_score = match.score * weight
                product_scores[product_id]['method_matches'][method] = match
                product_scores[product_id]['total_score'] += weighted_score
                product_scores[product_id]['total_confidence'] += match.confidence
                product_scores[product_id]['method_count'] += 1
        
        # Fused matches oluştur
        fused_matches = []
        for product_id, data in product_scores.items():
            # Average confidence
            avg_confidence = data['total_confidence'] / data['method_count']
            
            # Bonus for multiple methods
            method_bonus = min(data['method_count'] * 0.1, 0.3)
            final_score = data['total_score'] + method_bonus
            final_confidence = min(avg_confidence + method_bonus, 1.0)
            
            # Best method explanation
            best_method = max(data['method_matches'].keys(), 
                            key=lambda m: data['method_matches'][m].score)
            best_match = data['method_matches'][best_method]
            
            # Combine feature matches
            all_feature_matches = []
            for match in data['method_matches'].values():
                if match.feature_matches:
                    all_feature_matches.extend(match.feature_matches)
            
            fused_match = SearchMatch(
                product=data['product'],
                score=final_score,
                method=best_method,  # Dominant method
                confidence=final_confidence,
                explanation=f"Multi-method match ({data['method_count']} methods): {best_match.explanation}",
                feature_matches=list(set(all_feature_matches))
            )
            
            fused_matches.append(fused_match)
        
        # Score'a göre sırala
        fused_matches.sort(key=lambda x: x.score, reverse=True)
        return fused_matches
    
    def _calculate_overall_confidence(self, matches: List[SearchMatch]) -> float:
        """Overall confidence hesapla"""
        if not matches:
            return 0.0
        
        # Top 3 match'in confidence'ının weighted average'ı
        top_matches = matches[:3]
        weights = [1.0, 0.7, 0.4]
        
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for i, match in enumerate(top_matches):
            if i < len(weights):
                weight = weights[i]
                total_weighted_confidence += match.confidence * weight
                total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _generate_explanation(self, method_results: Dict[SearchMethod, List[SearchMatch]], 
                            fused_matches: List[SearchMatch]) -> str:
        """Arama sonucu açıklaması oluştur"""
        total_results = sum(len(matches) for matches in method_results.values())
        active_methods = len([m for m in method_results.values() if m])
        
        if not fused_matches:
            return f"No matches found using {active_methods} search methods"
        
        best_match = fused_matches[0]
        explanation = f"Found {len(fused_matches)} matches using {active_methods} methods. "
        explanation += f"Best match: {best_match.explanation} (confidence: {best_match.confidence:.2f})"
        
        return explanation
    
    def _generate_alternatives(self, query: str, products: List[Dict]) -> List[str]:
        """Düşük confidence durumunda alternatif öneriler oluştur"""
        alternatives = []
        
        # Query'den özellikleri çıkar
        query_features = self.feature_extractor.extract_features(query)
        
        # Her feature için sinonimler öner
        for feature in query_features[:3]:  # İlk 3 feature
            synonyms = feature.synonyms[:2]  # İlk 2 sinonim
            for synonym in synonyms:
                alt_query = query.replace(feature.value, synonym)
                if alt_query != query and alt_query not in alternatives:
                    alternatives.append(alt_query)
        
        # Türkçe kurallardan alternatifler
        turkish_alternatives = self.turkish_rules.expand_query_with_synonyms(query)
        for alt in turkish_alternatives[:2]:
            if alt != query and alt not in alternatives:
                alternatives.append(alt)
        
        return alternatives[:5]  # Maksimum 5 alternatif
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Search engine istatistikleri"""
        return {
            'available_methods': list(self.search_methods.keys()),
            'method_weights': self.method_weights,
            'feature_extractor_stats': self.feature_extractor.get_extraction_stats()
        }

# Test fonksiyonu
async def test_intelligent_search():
    """Intelligent search engine test"""
    
    # Test ürünleri
    test_products = [
        {
            'id': 1,
            'name': 'Afrika Etnik Baskılı Dantelli Gecelik',
            'category': 'İç Giyim',
            'color': 'BEJ',
            'price': 565.44
        },
        {
            'id': 2,
            'name': 'Dantelli Önü Düğmeli Hamile Lohusa Gecelik',
            'category': 'İç Giyim',
            'color': 'EKRU',
            'price': 1632.33
        },
        {
            'id': 3,
            'name': 'Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı',
            'category': 'İç Giyim',
            'color': 'SİYAH',
            'price': 1821.33
        },
        {
            'id': 4,
            'name': 'Siyah Tüllü Askılı Gecelik',
            'category': 'İç Giyim',
            'color': 'SİYAH',
            'price': 890.50
        }
    ]
    
    engine = IntelligentSearchEngine()
    
    print("🔍 Intelligent Search Engine Test:")
    print("=" * 50)
    
    # Test sorguları
    test_queries = [
        "siyah gecelik",
        "hamile lohusa",
        "dantelli takım",
        "black nightgown",
        "göğüs dekolteli"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        
        result = await engine.search(query, test_products, limit=3)
        
        print(f"⏱️  Total time: {result.total_time_ms}ms")
        print(f"🎯 Overall confidence: {result.overall_confidence:.3f}")
        print(f"📝 Explanation: {result.explanation}")
        
        if result.matches:
            print(f"✅ Found {len(result.matches)} matches:")
            for i, match in enumerate(result.matches, 1):
                print(f"  {i}. {match.product['name']}")
                print(f"     Score: {match.score:.3f}, Confidence: {match.confidence:.3f}")
                print(f"     Method: {match.method.value}")
                if match.feature_matches:
                    print(f"     Features: {', '.join(match.feature_matches[:3])}")
        else:
            print("❌ No matches found")
        
        if result.alternatives:
            print(f"💡 Alternatives: {', '.join(result.alternatives[:3])}")
        
        print(f"⚡ Method times: {result.method_times}")

if __name__ == "__main__":
    asyncio.run(test_intelligent_search())