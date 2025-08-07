"""
Multi-Stage Product Matcher - Combines exact, semantic, and fuzzy matching
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from orchestrator.services.exact_feature_matcher import ExactFeatureMatcher, ExactMatchResult
    from orchestrator.services.semantic_similarity_matcher import SemanticSimilarityMatcher, SemanticMatch
    from orchestrator.services.fuzzy_matching_engine import FuzzyMatchingEngine, FuzzyMatch
    from orchestrator.services.feature_extraction_engine import FeatureExtractionEngine
except ImportError:
    from exact_feature_matcher import ExactFeatureMatcher, ExactMatchResult
    from semantic_similarity_matcher import SemanticSimilarityMatcher, SemanticMatch
    from fuzzy_matching_engine import FuzzyMatchingEngine, FuzzyMatch
    from feature_extraction_engine import FeatureExtractionEngine

logger = logging.getLogger(__name__)

class MatchMethod(Enum):
    """Matching yöntemleri"""
    EXACT = "exact"
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"
    FUSED = "fused"

@dataclass
class UnifiedMatch:
    """Birleştirilmiş match sonucu"""
    product: Dict[str, Any]
    final_score: float
    confidence: float
    method_scores: Dict[str, float]
    method_confidences: Dict[str, float]
    dominant_method: MatchMethod
    explanation: str
    matched_features: List[str]
    method_count: int
    coverage_ratio: float

@dataclass
class SearchResult:
    """Arama sonucu"""
    matches: List[UnifiedMatch]
    query: str
    total_time_ms: int
    method_times: Dict[str, int]
    overall_confidence: float
    explanation: str
    alternatives: List[str]
    method_stats: Dict[str, Dict[str, Any]]

class MultiStageProductMatcher:
    """Multi-stage product matching with result fusion"""
    
    def __init__(self):
        # Initialize matchers
        self.exact_matcher = ExactFeatureMatcher()
        self.semantic_matcher = SemanticSimilarityMatcher()
        self.fuzzy_matcher = FuzzyMatchingEngine()
        self.feature_extractor = FeatureExtractionEngine()
        
        # Method weights for fusion
        self.method_weights = {
            MatchMethod.EXACT: 1.0,
            MatchMethod.SEMANTIC: 0.8,
            MatchMethod.FUZZY: 0.6
        }
        
        # Thresholds for each method
        self.method_thresholds = {
            MatchMethod.EXACT: 0.4,
            MatchMethod.SEMANTIC: 0.3,
            MatchMethod.FUZZY: 0.5
        }
        
        # Method priorities (higher = more important)
        self.method_priorities = {
            MatchMethod.EXACT: 3,
            MatchMethod.SEMANTIC: 2,
            MatchMethod.FUZZY: 1
        }
    
    async def search_products(self, query: str, products: List[Dict[str, Any]], 
                            limit: int = 10, methods: List[MatchMethod] = None) -> SearchResult:
        """Multi-stage product search with result fusion"""
        
        import time
        start_time = time.time()
        
        if not query or not query.strip():
            return self._empty_result(query)
        
        if methods is None:
            methods = [MatchMethod.EXACT, MatchMethod.SEMANTIC, MatchMethod.FUZZY]
        
        # Execute all matching methods
        method_results = {}
        method_times = {}
        
        for method in methods:
            method_start = time.time()
            try:
                results = await self._execute_method(method, query, products)
                method_results[method] = results
                method_times[method.value] = int((time.time() - method_start) * 1000)
            except Exception as e:
                logger.error(f"Method {method.value} failed: {str(e)}")
                method_results[method] = []
                method_times[method.value] = 0
        
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
        
        # Method statistics
        method_stats = self._calculate_method_stats(method_results)
        
        total_time = int((time.time() - start_time) * 1000)
        
        return SearchResult(
            matches=fused_matches[:limit],
            query=query,
            total_time_ms=total_time,
            method_times=method_times,
            overall_confidence=overall_confidence,
            explanation=explanation,
            alternatives=alternatives,
            method_stats=method_stats
        )
    
    async def _execute_method(self, method: MatchMethod, query: str, 
                            products: List[Dict[str, Any]]) -> List[Any]:
        """Tek bir matching method'u execute et"""
        
        threshold = self.method_thresholds[method]
        
        if method == MatchMethod.EXACT:
            return self.exact_matcher.match_products(query, products, threshold)
        elif method == MatchMethod.SEMANTIC:
            return self.semantic_matcher.match_products(query, products, threshold)
        elif method == MatchMethod.FUZZY:
            return self.fuzzy_matcher.match_products(query, products, threshold)
        else:
            return []
    
    def _fuse_results(self, method_results: Dict[MatchMethod, List[Any]], 
                     query: str) -> List[UnifiedMatch]:
        """Farklı method sonuçlarını birleştir ve rank et"""
        
        product_scores = {}  # product_id -> method_data
        
        # Her method'un sonuçlarını topla
        for method, results in method_results.items():
            weight = self.method_weights[method]
            
            for result in results:
                product = result.product if hasattr(result, 'product') else result.product
                product_id = str(product.get('id', hash(product.get('name', ''))))
                
                if product_id not in product_scores:
                    product_scores[product_id] = {
                        'product': product,
                        'method_scores': {},
                        'method_confidences': {},
                        'method_results': {},
                        'total_weighted_score': 0.0,
                        'method_count': 0
                    }
                
                # Extract score and confidence based on result type
                if isinstance(result, ExactMatchResult):
                    score = result.total_score / 10.0  # Normalize to 0-1
                    confidence = result.confidence
                    matched_features = [match.query_feature.value for match in result.feature_matches]
                elif isinstance(result, SemanticMatch):
                    score = result.similarity_score
                    confidence = result.confidence
                    matched_features = result.matched_features
                elif isinstance(result, FuzzyMatch):
                    score = result.similarity_score
                    confidence = result.confidence
                    matched_features = result.matched_tokens
                else:
                    score = 0.5
                    confidence = 0.5
                    matched_features = []
                
                # Store method data
                product_scores[product_id]['method_scores'][method.value] = score
                product_scores[product_id]['method_confidences'][method.value] = confidence
                product_scores[product_id]['method_results'][method.value] = {
                    'result': result,
                    'matched_features': matched_features
                }
                
                # Add weighted score
                weighted_score = score * weight
                product_scores[product_id]['total_weighted_score'] += weighted_score
                product_scores[product_id]['method_count'] += 1
        
        # Create unified matches
        unified_matches = []
        for product_id, data in product_scores.items():
            # Calculate final score with method diversity bonus
            method_count = data['method_count']
            base_score = data['total_weighted_score']
            
            # Bonus for multiple methods agreeing
            diversity_bonus = min((method_count - 1) * 0.1, 0.3)
            final_score = base_score + diversity_bonus
            
            # Calculate overall confidence
            confidences = list(data['method_confidences'].values())
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Bonus for high-priority methods
            priority_bonus = 0.0
            for method_str, confidence in data['method_confidences'].items():
                method_enum = MatchMethod(method_str)
                priority = self.method_priorities[method_enum]
                priority_bonus += (priority / 10.0) * confidence * 0.1
            
            overall_confidence = min(avg_confidence + priority_bonus + diversity_bonus, 1.0)
            
            # Determine dominant method
            dominant_method = self._get_dominant_method(data['method_scores'])
            
            # Collect all matched features
            all_matched_features = set()
            for method_data in data['method_results'].values():
                all_matched_features.update(method_data['matched_features'])
            
            # Calculate coverage ratio
            query_features = self.feature_extractor.extract_features(query)
            coverage_ratio = len(all_matched_features) / len(query_features) if query_features else 0.0
            
            # Generate explanation
            explanation = self._generate_match_explanation(
                data['method_scores'], dominant_method, method_count
            )
            
            unified_match = UnifiedMatch(
                product=data['product'],
                final_score=final_score,
                confidence=overall_confidence,
                method_scores=data['method_scores'],
                method_confidences=data['method_confidences'],
                dominant_method=dominant_method,
                explanation=explanation,
                matched_features=list(all_matched_features),
                method_count=method_count,
                coverage_ratio=coverage_ratio
            )
            
            unified_matches.append(unified_match)
        
        # Sort by final score
        unified_matches.sort(key=lambda x: x.final_score, reverse=True)
        
        return unified_matches
    
    def _get_dominant_method(self, method_scores: Dict[str, float]) -> MatchMethod:
        """En dominant method'u belirle"""
        if not method_scores:
            return MatchMethod.EXACT
        
        # Priority ve score'a göre weighted scoring
        weighted_scores = {}
        for method_str, score in method_scores.items():
            method_enum = MatchMethod(method_str)
            priority = self.method_priorities[method_enum]
            weighted_scores[method_enum] = score * priority
        
        return max(weighted_scores, key=weighted_scores.get)
    
    def _generate_match_explanation(self, method_scores: Dict[str, float], 
                                  dominant_method: MatchMethod, method_count: int) -> str:
        """Match explanation oluştur"""
        
        explanation_parts = []
        
        # Method count
        if method_count > 1:
            explanation_parts.append(f"{method_count} methods agree")
        else:
            explanation_parts.append("single method match")
        
        # Dominant method
        dominant_score = method_scores.get(dominant_method.value, 0.0)
        if dominant_score > 0.8:
            explanation_parts.append(f"strong {dominant_method.value} match")
        elif dominant_score > 0.6:
            explanation_parts.append(f"good {dominant_method.value} match")
        else:
            explanation_parts.append(f"weak {dominant_method.value} match")
        
        return f"Multi-stage match: {', '.join(explanation_parts)}"
    
    def _calculate_overall_confidence(self, matches: List[UnifiedMatch]) -> float:
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
    
    def _generate_explanation(self, method_results: Dict[MatchMethod, List[Any]], 
                            fused_matches: List[UnifiedMatch]) -> str:
        """Arama sonucu açıklaması oluştur"""
        
        total_results = sum(len(results) for results in method_results.values())
        active_methods = len([results for results in method_results.values() if results])
        
        if not fused_matches:
            return f"No matches found using {active_methods} search methods"
        
        best_match = fused_matches[0]
        explanation = f"Found {len(fused_matches)} matches using {active_methods} methods. "
        explanation += f"Best match: {best_match.explanation} (confidence: {best_match.confidence:.2f})"
        
        return explanation
    
    def _generate_alternatives(self, query: str, products: List[Dict[str, Any]]) -> List[str]:
        """Düşük confidence durumunda alternatif öneriler oluştur"""
        alternatives = []
        
        # Query'den feature'ları çıkar
        query_features = self.feature_extractor.extract_features(query)
        
        # Her feature için sinonimler öner
        for feature in query_features[:3]:  # İlk 3 feature
            synonyms = feature.synonyms[:2]  # İlk 2 sinonim
            for synonym in synonyms:
                alt_query = query.replace(feature.value, synonym)
                if alt_query != query and alt_query not in alternatives:
                    alternatives.append(alt_query)
        
        # Common variations
        common_variations = [
            query.replace("gecelik", "pijama"),
            query.replace("pijama", "gecelik"),
            query.replace("dantelli", "düğmeli"),
            query.replace("siyah", "beyaz")
        ]
        
        for variation in common_variations:
            if variation != query and variation not in alternatives:
                alternatives.append(variation)
        
        return alternatives[:5]  # Maksimum 5 alternatif
    
    def _calculate_method_stats(self, method_results: Dict[MatchMethod, List[Any]]) -> Dict[str, Dict[str, Any]]:
        """Method istatistikleri hesapla"""
        stats = {}
        
        for method, results in method_results.items():
            method_stats = {
                'result_count': len(results),
                'avg_score': 0.0,
                'avg_confidence': 0.0,
                'top_score': 0.0
            }
            
            if results:
                scores = []
                confidences = []
                
                for result in results:
                    if isinstance(result, ExactMatchResult):
                        scores.append(result.total_score / 10.0)
                        confidences.append(result.confidence)
                    elif isinstance(result, SemanticMatch):
                        scores.append(result.similarity_score)
                        confidences.append(result.confidence)
                    elif isinstance(result, FuzzyMatch):
                        scores.append(result.similarity_score)
                        confidences.append(result.confidence)
                
                if scores:
                    method_stats['avg_score'] = sum(scores) / len(scores)
                    method_stats['top_score'] = max(scores)
                
                if confidences:
                    method_stats['avg_confidence'] = sum(confidences) / len(confidences)
            
            stats[method.value] = method_stats
        
        return stats
    
    def _empty_result(self, query: str) -> SearchResult:
        """Boş sonuç döndür"""
        return SearchResult(
            matches=[],
            query=query,
            total_time_ms=0,
            method_times={},
            overall_confidence=0.0,
            explanation="Empty query provided",
            alternatives=[],
            method_stats={}
        )
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Search engine istatistikleri"""
        return {
            'available_methods': [method.value for method in MatchMethod],
            'method_weights': {method.value: weight for method, weight in self.method_weights.items()},
            'method_thresholds': {method.value: threshold for method, threshold in self.method_thresholds.items()},
            'method_priorities': {method.value: priority for method, priority in self.method_priorities.items()}
        }

# Test fonksiyonu
async def test_multi_stage_product_matcher():
    """Multi-stage product matcher test"""
    
    # Test products
    test_products = [
        {
            "id": 1,
            "name": "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik",
            "color": "EKRU",
            "price": 1415.33
        },
        {
            "id": 2,
            "name": "Afrika Etnik Baskılı Dantelli Gecelik",
            "color": "BEJ",
            "price": 565.44
        },
        {
            "id": 3,
            "name": "Siyah Tüllü Askılı Gecelik",
            "color": "SİYAH",
            "price": 890.50
        },
        {
            "id": 4,
            "name": "Dantelli Önü Düğmeli Hamile Lohusa Gecelik",
            "color": "EKRU",
            "price": 1632.33
        },
        {
            "id": 5,
            "name": "Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı",
            "color": "SİYAH",
            "price": 1821.33
        }
    ]
    
    matcher = MultiStageProductMatcher()
    
    print("🎯 Multi-Stage Product Matcher Test:")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik bu ne kadar",
        "siyah gecelik",
        "hamile lohusa geceliği",
        "dantelli takım",
        "kol omuz dantelli gecelig"  # With typo
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        result = await matcher.search_products(query, test_products, limit=3)
        
        print(f"⏱️  Total time: {result.total_time_ms}ms")
        print(f"🎯 Overall confidence: {result.overall_confidence:.3f}")
        print(f"📝 Explanation: {result.explanation}")
        
        if result.matches:
            print(f"✅ Found {len(result.matches)} unified matches:")
            for i, match in enumerate(result.matches, 1):
                print(f"\n  {i}. {match.product['name']}")
                print(f"     Final Score: {match.final_score:.3f}")
                print(f"     Confidence: {match.confidence:.3f}")
                print(f"     Dominant Method: {match.dominant_method.value}")
                print(f"     Methods Used: {match.method_count}")
                print(f"     Coverage: {match.coverage_ratio:.1%}")
                print(f"     Explanation: {match.explanation}")
                
                # Method scores
                method_scores = []
                for method, score in match.method_scores.items():
                    method_scores.append(f"{method}:{score:.2f}")
                print(f"     Method Scores: {', '.join(method_scores)}")
                
                if match.matched_features:
                    print(f"     Matched Features: {', '.join(match.matched_features[:5])}")
        else:
            print("❌ No matches found")
        
        if result.alternatives:
            print(f"💡 Alternatives: {', '.join(result.alternatives[:3])}")
        
        print(f"⚡ Method times: {result.method_times}")
        
        # Method stats
        print(f"📊 Method Stats:")
        for method, stats in result.method_stats.items():
            print(f"  {method}: {stats['result_count']} results, avg_score: {stats['avg_score']:.2f}")
    
    # Overall stats
    stats = matcher.get_search_stats()
    print(f"\n📊 Multi-Stage Matcher Stats:")
    print(f"  Available methods: {', '.join(stats['available_methods'])}")
    print(f"  Method weights: {stats['method_weights']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_multi_stage_product_matcher())