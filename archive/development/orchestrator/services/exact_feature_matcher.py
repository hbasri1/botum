"""
Exact Feature Matcher - Precise feature-to-feature matching for products
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
try:
    from orchestrator.services.feature_extraction_engine import (
        FeatureExtractionEngine, ProductFeature, FeatureCategory
    )
except ImportError:
    from feature_extraction_engine import (
        FeatureExtractionEngine, ProductFeature, FeatureCategory
    )

logger = logging.getLogger(__name__)

@dataclass
class FeatureMatch:
    """Feature eşleşmesi"""
    query_feature: ProductFeature
    product_feature: ProductFeature
    match_type: str  # exact, synonym, normalized
    similarity_score: float
    explanation: str

@dataclass
class ExactMatchResult:
    """Exact matching sonucu"""
    product: Dict[str, Any]
    total_score: float
    confidence: float
    feature_matches: List[FeatureMatch]
    matched_feature_count: int
    total_query_features: int
    coverage_ratio: float
    explanation: str

class ExactFeatureMatcher:
    """Exact feature matching engine"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractionEngine()
        
        # Match type weights
        self.match_type_weights = {
            "exact": 1.0,
            "synonym": 0.9,
            "normalized": 0.8,
            "category_match": 0.6
        }
        
        # Category importance weights
        self.category_weights = {
            FeatureCategory.GARMENT_TYPE: 2.0,
            FeatureCategory.TARGET_GROUP: 1.8,
            FeatureCategory.QUERY_TYPE: 1.6,
            FeatureCategory.STYLE: 1.4,
            FeatureCategory.COLOR: 1.2,
            FeatureCategory.BODY_PART: 1.0,
            FeatureCategory.CLOSURE: 0.8,
            FeatureCategory.MATERIAL: 0.8,
            FeatureCategory.PATTERN: 0.6,
            FeatureCategory.SIZE: 0.6,
            FeatureCategory.OCCASION: 0.4
        }
    
    def match_products(self, query: str, products: List[Dict[str, Any]], 
                      threshold: float = 0.6) -> List[ExactMatchResult]:
        """Ürünleri query ile exact matching yap"""
        
        # Query'den feature'ları çıkar
        query_features = self.feature_extractor.extract_features(query)
        
        if not query_features:
            logger.warning(f"No features extracted from query: {query}")
            return []
        
        results = []
        
        for product in products:
            # Product'tan feature'ları çıkar
            product_name = product.get('name', '')
            product_features = self.feature_extractor.extract_features(product_name)
            
            if not product_features:
                continue
            
            # Feature matching yap
            match_result = self._match_features(query_features, product_features, product)
            
            # Threshold kontrolü
            if match_result.total_score >= threshold:
                results.append(match_result)
        
        # Score'a göre sırala
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        return results
    
    def _match_features(self, query_features: List[ProductFeature], 
                       product_features: List[ProductFeature], 
                       product: Dict[str, Any]) -> ExactMatchResult:
        """İki feature listesi arasında matching yap"""
        
        feature_matches = []
        total_score = 0.0
        matched_features = set()
        
        # Her query feature için en iyi product feature match'ini bul
        for query_feature in query_features:
            best_match = self._find_best_feature_match(query_feature, product_features)
            
            if best_match:
                feature_matches.append(best_match)
                total_score += best_match.similarity_score * query_feature.weight
                matched_features.add(query_feature.value)
        
        # Coverage ratio hesapla
        coverage_ratio = len(matched_features) / len(query_features) if query_features else 0.0
        
        # Confidence hesapla
        confidence = self._calculate_confidence(
            feature_matches, query_features, product_features, coverage_ratio
        )
        
        # Explanation oluştur
        explanation = self._generate_explanation(feature_matches, coverage_ratio)
        
        return ExactMatchResult(
            product=product,
            total_score=total_score,
            confidence=confidence,
            feature_matches=feature_matches,
            matched_feature_count=len(matched_features),
            total_query_features=len(query_features),
            coverage_ratio=coverage_ratio,
            explanation=explanation
        )
    
    def _find_best_feature_match(self, query_feature: ProductFeature, 
                                product_features: List[ProductFeature]) -> Optional[FeatureMatch]:
        """Query feature için en iyi product feature match'ini bul"""
        
        best_match = None
        best_score = 0.0
        
        for product_feature in product_features:
            match_score, match_type = self._calculate_feature_match_score(
                query_feature, product_feature
            )
            
            if match_score > best_score:
                best_score = match_score
                best_match = FeatureMatch(
                    query_feature=query_feature,
                    product_feature=product_feature,
                    match_type=match_type,
                    similarity_score=match_score,
                    explanation=f"{match_type} match: '{query_feature.value}' -> '{product_feature.value}'"
                )
        
        return best_match
    
    def _calculate_feature_match_score(self, query_feature: ProductFeature, 
                                     product_feature: ProductFeature) -> Tuple[float, str]:
        """İki feature arasında match score hesapla"""
        
        # Aynı kategori değilse düşük score
        if query_feature.category != product_feature.category:
            return 0.1, "category_mismatch"
        
        # Exact match
        if query_feature.value == product_feature.value:
            return 1.0 * self.match_type_weights["exact"], "exact"
        
        # Normalized match
        if query_feature.normalized_value == product_feature.normalized_value:
            return 0.95 * self.match_type_weights["normalized"], "normalized"
        
        # Synonym match
        if (product_feature.value in query_feature.synonyms or 
            query_feature.value in product_feature.synonyms):
            return 0.9 * self.match_type_weights["synonym"], "synonym"
        
        # Partial string match (for compound features)
        if (query_feature.value in product_feature.value or 
            product_feature.value in query_feature.value):
            return 0.7, "partial"
        
        # Category match but different values
        category_weight = self.category_weights.get(query_feature.category, 1.0)
        if category_weight > 1.0:  # Important categories
            return 0.3 * self.match_type_weights["category_match"], "category_match"
        
        return 0.0, "no_match"
    
    def _calculate_confidence(self, feature_matches: List[FeatureMatch], 
                            query_features: List[ProductFeature],
                            product_features: List[ProductFeature],
                            coverage_ratio: float) -> float:
        """Confidence score hesapla"""
        
        if not feature_matches:
            return 0.0
        
        # Base confidence from match quality
        match_quality_sum = sum(match.similarity_score for match in feature_matches)
        avg_match_quality = match_quality_sum / len(feature_matches)
        
        # Coverage bonus
        coverage_bonus = coverage_ratio * 0.2
        
        # Important feature bonus
        important_matches = 0
        for match in feature_matches:
            if match.query_feature.category in [FeatureCategory.GARMENT_TYPE, 
                                               FeatureCategory.TARGET_GROUP]:
                important_matches += 1
        
        important_bonus = min(important_matches * 0.1, 0.3)
        
        # Exact match bonus
        exact_matches = sum(1 for match in feature_matches if match.match_type == "exact")
        exact_bonus = min(exact_matches * 0.05, 0.2)
        
        # Final confidence
        confidence = avg_match_quality + coverage_bonus + important_bonus + exact_bonus
        
        return min(confidence, 1.0)
    
    def _generate_explanation(self, feature_matches: List[FeatureMatch], 
                            coverage_ratio: float) -> str:
        """Match explanation oluştur"""
        
        if not feature_matches:
            return "No feature matches found"
        
        # Match types summary
        match_types = {}
        for match in feature_matches:
            match_type = match.match_type
            if match_type not in match_types:
                match_types[match_type] = 0
            match_types[match_type] += 1
        
        # Create explanation
        explanation_parts = []
        
        if "exact" in match_types:
            explanation_parts.append(f"{match_types['exact']} exact matches")
        
        if "synonym" in match_types:
            explanation_parts.append(f"{match_types['synonym']} synonym matches")
        
        if "normalized" in match_types:
            explanation_parts.append(f"{match_types['normalized']} normalized matches")
        
        explanation = f"Found {len(feature_matches)} feature matches: " + ", ".join(explanation_parts)
        explanation += f" (coverage: {coverage_ratio:.1%})"
        
        return explanation
    
    def get_feature_importance_ranking(self, query: str) -> List[Tuple[str, float]]:
        """Query'deki feature'ların önem sıralaması"""
        
        query_features = self.feature_extractor.extract_features(query)
        
        # Weight * confidence ile sırala
        feature_importance = []
        for feature in query_features:
            importance_score = feature.weight * feature.confidence
            feature_importance.append((feature.value, importance_score))
        
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        return feature_importance
    
    def explain_match(self, query: str, product: Dict[str, Any]) -> Dict[str, Any]:
        """Tek bir ürün için detaylı match explanation"""
        
        query_features = self.feature_extractor.extract_features(query)
        product_features = self.feature_extractor.extract_features(product.get('name', ''))
        
        match_result = self._match_features(query_features, product_features, product)
        
        return {
            "product_name": product.get('name', ''),
            "total_score": match_result.total_score,
            "confidence": match_result.confidence,
            "coverage_ratio": match_result.coverage_ratio,
            "query_features": [
                {
                    "value": f.value,
                    "category": f.category.value,
                    "weight": f.weight,
                    "confidence": f.confidence
                } for f in query_features
            ],
            "product_features": [
                {
                    "value": f.value,
                    "category": f.category.value,
                    "weight": f.weight,
                    "confidence": f.confidence
                } for f in product_features
            ],
            "feature_matches": [
                {
                    "query_feature": match.query_feature.value,
                    "product_feature": match.product_feature.value,
                    "match_type": match.match_type,
                    "similarity_score": match.similarity_score,
                    "explanation": match.explanation
                } for match in match_result.feature_matches
            ],
            "explanation": match_result.explanation
        }

# Test fonksiyonu
def test_exact_feature_matcher():
    """Exact feature matcher test"""
    
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
        }
    ]
    
    matcher = ExactFeatureMatcher()
    
    print("🎯 Exact Feature Matcher Test:")
    print("=" * 50)
    
    # Test query - problematic case
    query = "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik bu ne kadar"
    
    print(f"\n🔍 Query: '{query}'")
    
    results = matcher.match_products(query, test_products, threshold=0.3)
    
    if results:
        print(f"✅ Found {len(results)} matches:")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result.product['name']}")
            print(f"     Score: {result.total_score:.3f}")
            print(f"     Confidence: {result.confidence:.3f}")
            print(f"     Coverage: {result.coverage_ratio:.1%}")
            print(f"     Matches: {result.matched_feature_count}/{result.total_query_features}")
            print(f"     Explanation: {result.explanation}")
            
            # Top feature matches
            if result.feature_matches:
                print(f"     Top matches:")
                for match in result.feature_matches[:3]:
                    print(f"       • {match.explanation} (score: {match.similarity_score:.2f})")
    else:
        print("❌ No matches found")
    
    # Feature importance
    print(f"\n📊 Feature Importance for Query:")
    importance = matcher.get_feature_importance_ranking(query)
    for feature, score in importance[:5]:
        print(f"  • {feature}: {score:.2f}")
    
    # Detailed explanation for best match
    if results:
        print(f"\n🔍 Detailed Match Explanation for Best Result:")
        explanation = matcher.explain_match(query, results[0].product)
        print(f"  Product: {explanation['product_name']}")
        print(f"  Total Score: {explanation['total_score']:.3f}")
        print(f"  Confidence: {explanation['confidence']:.3f}")
        print(f"  Feature Matches:")
        for match in explanation['feature_matches'][:5]:
            print(f"    • {match['explanation']} (score: {match['similarity_score']:.2f})")

if __name__ == "__main__":
    test_exact_feature_matcher()