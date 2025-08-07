#!/usr/bin/env python3
"""
Result Fusion Engine - Multi-source result combination and ranking system
"""

import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

try:
    from .intelligent_search_engine import SearchMatch, SearchMethod
    from .product_feature_extractor import ProductFeatureExtractor
    from .feature_synonym_mapper import FeatureSynonymMapper
    from .turkish_language_rules import TurkishLanguageRules
except ImportError:
    from intelligent_search_engine import SearchMatch, SearchMethod
    from product_feature_extractor import ProductFeatureExtractor
    from feature_synonym_mapper import FeatureSynonymMapper
    from turkish_language_rules import TurkishLanguageRules

logger = logging.getLogger(__name__)

class FusionStrategy(Enum):
    """Result fusion stratejileri"""
    WEIGHTED_AVERAGE = "weighted_average"
    MAX_SCORE = "max_score"
    RANK_FUSION = "rank_fusion"
    BAYESIAN_FUSION = "bayesian_fusion"

@dataclass
class FusedResult:
    """Fused search result"""
    product: Dict[str, Any]
    final_score: float
    confidence: float
    method_scores: Dict[SearchMethod, float]
    method_ranks: Dict[SearchMethod, int]
    fusion_explanation: str
    validation_score: float
    feature_matches: List[str]
    alternative_reason: Optional[str] = None

@dataclass
class Alternative:
    """Alternative suggestion"""
    suggestion: str
    reason: str
    confidence: float
    original_query: str

class ResultFusionEngine:
    """Multi-source result fusion and ranking engine"""
    
    def __init__(self, fusion_strategy: FusionStrategy = FusionStrategy.WEIGHTED_AVERAGE):
        self.fusion_strategy = fusion_strategy
        self.feature_extractor = ProductFeatureExtractor()
        self.synonym_mapper = FeatureSynonymMapper()
        self.turkish_rules = TurkishLanguageRules()
        
        # Method reliability weights (learned from historical performance)
        self.method_reliability = {
            SearchMethod.SEMANTIC: 0.9,
            SearchMethod.FEATURE_BASED: 0.85,
            SearchMethod.FUZZY: 0.8,
            SearchMethod.KEYWORD: 0.6
        }
        
        # Fusion parameters
        self.fusion_params = {
            'min_methods_for_boost': 2,
            'multi_method_boost': 0.15,
            'consistency_threshold': 0.7,
            'consistency_boost': 0.1,
            'validation_weight': 0.2
        }
    
    def fuse_results(self, method_results: Dict[SearchMethod, List[SearchMatch]], 
                    query: str) -> List[FusedResult]:
        """
        Farklı method sonuçlarını birleştir ve rank'le
        
        Args:
            method_results: Method -> SearchMatch listesi mapping
            query: Orijinal sorgu
            
        Returns:
            List[FusedResult]: Fused ve ranked sonuçlar
        """
        try:
            # Product-based grouping
            product_groups = self._group_by_product(method_results)
            
            # Fuse each product group
            fused_results = []
            for product_id, method_matches in product_groups.items():
                fused_result = self._fuse_product_results(method_matches, query)
                if fused_result:
                    fused_results.append(fused_result)
            
            # Sort by final score
            fused_results.sort(key=lambda x: x.final_score, reverse=True)
            
            logger.info(f"Fused {len(fused_results)} results from {len(method_results)} methods")
            return fused_results
            
        except Exception as e:
            logger.error(f"Result fusion error: {str(e)}")
            return []
    
    def _group_by_product(self, method_results: Dict[SearchMethod, List[SearchMatch]]) -> Dict[str, Dict[SearchMethod, SearchMatch]]:
        """Sonuçları ürüne göre grupla"""
        product_groups = defaultdict(dict)
        
        for method, matches in method_results.items():
            for match in matches:
                product_id = self._get_product_id(match.product)
                product_groups[product_id][method] = match
        
        return dict(product_groups)
    
    def _get_product_id(self, product: Dict[str, Any]) -> str:
        """Ürün için unique ID oluştur"""
        return str(product.get('id', hash(product.get('name', ''))))
    
    def _fuse_product_results(self, method_matches: Dict[SearchMethod, SearchMatch], 
                            query: str) -> Optional[FusedResult]:
        """Tek bir ürün için method sonuçlarını fuse et"""
        if not method_matches:
            return None
        
        # Get product (all matches should have same product)
        product = next(iter(method_matches.values())).product
        
        # Extract scores and ranks
        method_scores = {method: match.score for method, match in method_matches.items()}
        method_ranks = self._calculate_method_ranks(method_matches)
        
        # Apply fusion strategy
        if self.fusion_strategy == FusionStrategy.WEIGHTED_AVERAGE:
            final_score = self._weighted_average_fusion(method_scores)
        elif self.fusion_strategy == FusionStrategy.MAX_SCORE:
            final_score = self._max_score_fusion(method_scores)
        elif self.fusion_strategy == FusionStrategy.RANK_FUSION:
            final_score = self._rank_fusion(method_ranks)
        elif self.fusion_strategy == FusionStrategy.BAYESIAN_FUSION:
            final_score = self._bayesian_fusion(method_scores, method_matches)
        else:
            final_score = self._weighted_average_fusion(method_scores)
        
        # Apply bonuses and penalties
        final_score = self._apply_fusion_bonuses(final_score, method_matches, query)
        
        # Calculate confidence
        confidence = self._calculate_fusion_confidence(method_matches, final_score)
        
        # Validate result
        validation_score = self._validate_result(product, query)
        
        # Combine feature matches
        all_feature_matches = []
        for match in method_matches.values():
            if hasattr(match, 'feature_matches') and match.feature_matches:
                all_feature_matches.extend(match.feature_matches)
        
        # Generate explanation
        explanation = self._generate_fusion_explanation(method_matches, final_score)
        
        return FusedResult(
            product=product,
            final_score=final_score,
            confidence=confidence,
            method_scores=method_scores,
            method_ranks=method_ranks,
            fusion_explanation=explanation,
            validation_score=validation_score,
            feature_matches=list(set(all_feature_matches))
        )
    
    def _calculate_method_ranks(self, method_matches: Dict[SearchMethod, SearchMatch]) -> Dict[SearchMethod, int]:
        """Her method için rank hesapla (1 = best)"""
        # Sort by score descending
        sorted_methods = sorted(method_matches.items(), key=lambda x: x[1].score, reverse=True)
        
        ranks = {}
        for rank, (method, _) in enumerate(sorted_methods, 1):
            ranks[method] = rank
        
        return ranks
    
    def _weighted_average_fusion(self, method_scores: Dict[SearchMethod, float]) -> float:
        """Weighted average fusion"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for method, score in method_scores.items():
            weight = self.method_reliability.get(method, 0.5)
            total_weighted_score += score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _max_score_fusion(self, method_scores: Dict[SearchMethod, float]) -> float:
        """Max score fusion"""
        return max(method_scores.values()) if method_scores else 0.0
    
    def _rank_fusion(self, method_ranks: Dict[SearchMethod, int]) -> float:
        """Rank-based fusion (lower rank = higher score)"""
        if not method_ranks:
            return 0.0
        
        # Convert ranks to scores (1/rank)
        rank_scores = []
        for method, rank in method_ranks.items():
            weight = self.method_reliability.get(method, 0.5)
            rank_score = weight / rank  # Lower rank = higher score
            rank_scores.append(rank_score)
        
        return sum(rank_scores) / len(rank_scores)
    
    def _bayesian_fusion(self, method_scores: Dict[SearchMethod, float], 
                        method_matches: Dict[SearchMethod, SearchMatch]) -> float:
        """Bayesian fusion with confidence weighting"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for method, score in method_scores.items():
            match = method_matches[method]
            
            # Base weight from reliability
            base_weight = self.method_reliability.get(method, 0.5)
            
            # Confidence weight
            confidence_weight = match.confidence if hasattr(match, 'confidence') else 1.0
            
            # Combined weight
            combined_weight = base_weight * confidence_weight
            
            total_weighted_score += score * combined_weight
            total_weight += combined_weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _apply_fusion_bonuses(self, base_score: float, 
                            method_matches: Dict[SearchMethod, SearchMatch], 
                            query: str) -> float:
        """Fusion bonusları ve penaltileri uygula"""
        final_score = base_score
        
        # Multi-method bonus
        if len(method_matches) >= self.fusion_params['min_methods_for_boost']:
            final_score += self.fusion_params['multi_method_boost']
        
        # Consistency bonus
        scores = [match.score for match in method_matches.values()]
        if len(scores) > 1:
            score_std = statistics.stdev(scores)
            if score_std < (1.0 - self.fusion_params['consistency_threshold']):
                final_score += self.fusion_params['consistency_boost']
        
        # High-confidence method bonus
        high_conf_methods = sum(1 for match in method_matches.values() 
                               if hasattr(match, 'confidence') and match.confidence > 0.8)
        if high_conf_methods >= 2:
            final_score += 0.05
        
        return min(final_score, 2.0)  # Cap at 2.0
    
    def _calculate_fusion_confidence(self, method_matches: Dict[SearchMethod, SearchMatch], 
                                   final_score: float) -> float:
        """Fusion confidence hesapla"""
        # Base confidence from final score
        base_confidence = min(final_score / 1.5, 1.0)
        
        # Method agreement bonus
        scores = [match.score for match in method_matches.values()]
        if len(scores) > 1:
            score_range = max(scores) - min(scores)
            agreement_bonus = max(0, (0.5 - score_range) * 0.4)
            base_confidence += agreement_bonus
        
        # Method count bonus
        method_count_bonus = min(len(method_matches) * 0.05, 0.2)
        base_confidence += method_count_bonus
        
        # Individual method confidence
        if method_matches:
            avg_method_confidence = sum(
                getattr(match, 'confidence', 0.5) for match in method_matches.values()
            ) / len(method_matches)
            base_confidence = (base_confidence + avg_method_confidence) / 2
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _validate_result(self, product: Dict[str, Any], query: str) -> float:
        """Sonucu query'ye karşı validate et"""
        try:
            product_name = product.get('name', '')
            
            # Feature-based validation
            query_features = self.feature_extractor.extract_features(query)
            product_features = self.feature_extractor.extract_features(product_name)
            
            if query_features and product_features:
                query_feature_values = {f.value for f in query_features}
                product_feature_values = {f.value for f in product_features}
                
                # Direct feature overlap
                overlap = len(query_feature_values.intersection(product_feature_values))
                feature_validation = overlap / len(query_feature_values) if query_feature_values else 0.0
            else:
                feature_validation = 0.5  # Neutral if no features
            
            # Text-based validation
            text_validation = self.turkish_rules.calculate_turkish_similarity(query, product_name)
            
            # Combined validation
            return feature_validation * 0.6 + text_validation * 0.4
            
        except Exception as e:
            logger.error(f"Result validation error: {str(e)}")
            return 0.5  # Neutral validation on error
    
    def _generate_fusion_explanation(self, method_matches: Dict[SearchMethod, SearchMatch], 
                                   final_score: float) -> str:
        """Fusion açıklaması oluştur"""
        method_count = len(method_matches)
        best_method = max(method_matches.keys(), key=lambda m: method_matches[m].score)
        best_score = method_matches[best_method].score
        
        explanation = f"Fused from {method_count} methods"
        explanation += f", best: {best_method.value} ({best_score:.2f})"
        explanation += f", final: {final_score:.2f}"
        
        # Add method breakdown
        method_scores = [f"{m.value}:{s.score:.2f}" for m, s in method_matches.items()]
        explanation += f" [{', '.join(method_scores)}]"
        
        return explanation
    
    def calculate_overall_confidence(self, fused_results: List[FusedResult]) -> float:
        """Overall confidence hesapla"""
        if not fused_results:
            return 0.0
        
        # Top 3 result'ın weighted confidence'ı
        top_results = fused_results[:3]
        weights = [1.0, 0.7, 0.4]
        
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for i, result in enumerate(top_results):
            if i < len(weights):
                weight = weights[i]
                total_weighted_confidence += result.confidence * weight
                total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def validate_results(self, fused_results: List[FusedResult], 
                        query: str) -> List[FusedResult]:
        """Sonuçları validate et ve filter'le"""
        validated_results = []
        
        for result in fused_results:
            # Validation score'u final score'a dahil et
            validation_weight = self.fusion_params['validation_weight']
            adjusted_score = (
                result.final_score * (1 - validation_weight) +
                result.validation_score * validation_weight
            )
            
            # Update result
            result.final_score = adjusted_score
            
            # Filter low-quality results
            if result.confidence > 0.3 and result.validation_score > 0.2:
                validated_results.append(result)
        
        # Re-sort after validation adjustment
        validated_results.sort(key=lambda x: x.final_score, reverse=True)
        return validated_results
    
    def generate_alternatives(self, query: str, fused_results: List[FusedResult], 
                            original_method_results: Dict[SearchMethod, List[SearchMatch]]) -> List[Alternative]:
        """Düşük confidence durumunda alternatif öneriler oluştur"""
        alternatives = []
        
        try:
            # Query feature analysis
            query_features = self.feature_extractor.extract_features(query)
            
            # Synonym-based alternatives
            for feature in query_features[:3]:
                synonyms = feature.synonyms[:2]
                for synonym in synonyms:
                    alt_query = query.replace(feature.value, synonym)
                    if alt_query != query:
                        alternatives.append(Alternative(
                            suggestion=alt_query,
                            reason=f"Try synonym '{synonym}' for '{feature.value}'",
                            confidence=0.7,
                            original_query=query
                        ))
            
            # Turkish language alternatives
            turkish_alternatives = self.turkish_rules.expand_query_with_synonyms(query)
            for alt in turkish_alternatives[1:3]:  # Skip original, take next 2
                if alt != query:
                    alternatives.append(Alternative(
                        suggestion=alt,
                        reason="Turkish language variation",
                        confidence=0.6,
                        original_query=query
                    ))
            
            # Feature-based suggestions from partial matches
            if fused_results:
                top_result = fused_results[0]
                if top_result.confidence < 0.6:
                    product_features = self.feature_extractor.extract_features(
                        top_result.product.get('name', '')
                    )
                    
                    for feature in product_features[:2]:
                        if feature.value not in query.lower():
                            alt_query = f"{query} {feature.value}"
                            alternatives.append(Alternative(
                                suggestion=alt_query,
                                reason=f"Add '{feature.value}' to be more specific",
                                confidence=0.5,
                                original_query=query
                            ))
            
            # Remove duplicates and sort by confidence
            seen = set()
            unique_alternatives = []
            for alt in alternatives:
                if alt.suggestion not in seen:
                    seen.add(alt.suggestion)
                    unique_alternatives.append(alt)
            
            unique_alternatives.sort(key=lambda x: x.confidence, reverse=True)
            return unique_alternatives[:5]  # Top 5 alternatives
            
        except Exception as e:
            logger.error(f"Alternative generation error: {str(e)}")
            return []
    
    def get_fusion_stats(self) -> Dict[str, Any]:
        """Fusion engine istatistikleri"""
        return {
            'fusion_strategy': self.fusion_strategy.value,
            'method_reliability': self.method_reliability,
            'fusion_params': self.fusion_params,
            'supported_methods': list(SearchMethod)
        }

# Test fonksiyonu
def test_result_fusion_engine():
    """Result fusion engine test"""
    
    # Mock search matches
    from intelligent_search_engine import SearchMatch, SearchMethod
    
    test_product1 = {'id': 1, 'name': 'Siyah Tüllü Askılı Gecelik'}
    test_product2 = {'id': 2, 'name': 'Dantelli Hamile Gecelik'}
    
    # Mock method results
    method_results = {
        SearchMethod.SEMANTIC: [
            SearchMatch(test_product1, 0.9, SearchMethod.SEMANTIC, 0.85, "Semantic match", ['siyah', 'gecelik']),
            SearchMatch(test_product2, 0.7, SearchMethod.SEMANTIC, 0.75, "Semantic match", ['gecelik'])
        ],
        SearchMethod.FUZZY: [
            SearchMatch(test_product1, 0.95, SearchMethod.FUZZY, 0.9, "Fuzzy match", []),
            SearchMatch(test_product2, 0.6, SearchMethod.FUZZY, 0.65, "Fuzzy match", [])
        ],
        SearchMethod.FEATURE_BASED: [
            SearchMatch(test_product1, 0.8, SearchMethod.FEATURE_BASED, 0.8, "Feature match", ['siyah', 'gecelik'])
        ]
    }
    
    fusion_engine = ResultFusionEngine()
    
    print("🔀 Result Fusion Engine Test:")
    print("=" * 50)
    
    # Test fusion
    query = "siyah gecelik"
    fused_results = fusion_engine.fuse_results(method_results, query)
    
    print(f"\n🔍 Query: '{query}'")
    print(f"✅ Fused {len(fused_results)} results:")
    
    for i, result in enumerate(fused_results, 1):
        print(f"\n  {i}. {result.product['name']}")
        print(f"     Final score: {result.final_score:.3f}")
        print(f"     Confidence: {result.confidence:.3f}")
        print(f"     Validation: {result.validation_score:.3f}")
        print(f"     Method scores: {result.method_scores}")
        print(f"     Explanation: {result.fusion_explanation}")
        
        if result.feature_matches:
            print(f"     Feature matches: {', '.join(result.feature_matches)}")
    
    # Test validation
    validated_results = fusion_engine.validate_results(fused_results, query)
    print(f"\n✅ Validated {len(validated_results)} results")
    
    # Test overall confidence
    overall_confidence = fusion_engine.calculate_overall_confidence(validated_results)
    print(f"🎯 Overall confidence: {overall_confidence:.3f}")
    
    # Test alternatives
    alternatives = fusion_engine.generate_alternatives(query, validated_results, method_results)
    if alternatives:
        print(f"\n💡 Generated {len(alternatives)} alternatives:")
        for alt in alternatives:
            print(f"  • '{alt.suggestion}' - {alt.reason} (conf: {alt.confidence:.2f})")
    
    # Stats
    stats = fusion_engine.get_fusion_stats()
    print(f"\n📊 Fusion Stats:")
    print(f"  Strategy: {stats['fusion_strategy']}")
    print(f"  Method reliability: {stats['method_reliability']}")

if __name__ == "__main__":
    test_result_fusion_engine()