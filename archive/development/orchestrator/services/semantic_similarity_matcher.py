"""
Semantic Similarity Matcher - Feature-weighted semantic matching with embeddings
"""

import hashlib
import random
import math
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
class SemanticMatch:
    """Semantic matching sonucu"""
    product: Dict[str, Any]
    similarity_score: float
    feature_similarity: float
    text_similarity: float
    embedding_similarity: float
    confidence: float
    matched_features: List[str]
    feature_scores: Dict[str, float]
    explanation: str

@dataclass
class EnhancedEmbedding:
    """Feature-weighted embedding"""
    base_embedding: List[float]
    feature_embeddings: Dict[str, List[float]]
    feature_weights: Dict[str, float]
    combined_embedding: List[float]

class SemanticSimilarityMatcher:
    """Feature-weighted semantic similarity matcher"""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.feature_extractor = FeatureExtractionEngine()
        
        # Embedding cache
        self.embedding_cache = {}
        self.product_embeddings = {}
        
        # Feature category weights for embedding
        self.category_embedding_weights = {
            FeatureCategory.GARMENT_TYPE: 2.5,
            FeatureCategory.TARGET_GROUP: 2.0,
            FeatureCategory.QUERY_TYPE: 1.8,
            FeatureCategory.STYLE: 1.5,
            FeatureCategory.COLOR: 1.3,
            FeatureCategory.BODY_PART: 1.0,
            FeatureCategory.CLOSURE: 0.8,
            FeatureCategory.MATERIAL: 0.8,
            FeatureCategory.PATTERN: 0.6,
            FeatureCategory.SIZE: 0.6,
            FeatureCategory.OCCASION: 0.4
        }
        
        # Turkish normalization
        self.turkish_char_map = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
        }
    
    def match_products(self, query: str, products: List[Dict[str, Any]], 
                      threshold: float = 0.4) -> List[SemanticMatch]:
        """Ürünleri query ile semantic matching yap"""
        
        # Query için enhanced embedding oluştur
        query_embedding = self._create_enhanced_embedding(query)
        query_features = self.feature_extractor.extract_features(query)
        
        if not query_features:
            logger.warning(f"No features extracted from query: {query}")
            return []
        
        matches = []
        
        for product in products:
            # Product için enhanced embedding oluştur (cache'den al veya oluştur)
            product_id = str(product.get('id', hash(product.get('name', ''))))
            
            if product_id not in self.product_embeddings:
                product_name = product.get('name', '')
                self.product_embeddings[product_id] = self._create_enhanced_embedding(product_name)
            
            product_embedding = self.product_embeddings[product_id]
            product_features = self.feature_extractor.extract_features(product.get('name', ''))
            
            # Semantic match hesapla
            semantic_match = self._calculate_semantic_match(
                query, query_embedding, query_features,
                product, product_embedding, product_features
            )
            
            # Threshold kontrolü
            if semantic_match.similarity_score >= threshold:
                matches.append(semantic_match)
        
        # Score'a göre sırala
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches
    
    def _create_enhanced_embedding(self, text: str) -> EnhancedEmbedding:
        """Text için feature-weighted enhanced embedding oluştur"""
        
        # Base text embedding
        base_embedding = self._generate_deterministic_embedding(text)
        
        # Extract features
        features = self.feature_extractor.extract_features(text)
        
        # Feature embeddings
        feature_embeddings = {}
        feature_weights = {}
        
        for feature in features:
            feature_embedding = self._create_feature_embedding(feature)
            feature_embeddings[feature.value] = feature_embedding
            feature_weights[feature.value] = feature.weight * feature.confidence
        
        # Combine embeddings
        combined_embedding = self._combine_embeddings(
            base_embedding, feature_embeddings, feature_weights
        )
        
        return EnhancedEmbedding(
            base_embedding=base_embedding,
            feature_embeddings=feature_embeddings,
            feature_weights=feature_weights,
            combined_embedding=combined_embedding
        )
    
    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """Deterministic embedding generation (mock)"""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        # Normalize Turkish text
        normalized_text = self._normalize_turkish_text(text)
        
        # Deterministic seed from normalized text
        seed = int(hashlib.md5(normalized_text.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Generate embedding based on text characteristics
        embedding = []
        
        # Add character-based features
        for i in range(self.embedding_dim // 4):
            char_index = i % len(normalized_text) if normalized_text else 0
            char_value = ord(normalized_text[char_index]) if normalized_text else 65
            embedding.append((char_value / 128.0) - 1.0)
        
        # Add word-based features
        words = normalized_text.split()
        for i in range(self.embedding_dim // 4):
            if words:
                word_index = i % len(words)
                word_hash = hash(words[word_index]) % 1000
                embedding.append((word_hash / 500.0) - 1.0)
            else:
                embedding.append(random.uniform(-1, 1))
        
        # Add length-based features
        for i in range(self.embedding_dim // 4):
            length_feature = len(normalized_text) / 100.0 if normalized_text else 0.0
            embedding.append(length_feature + random.uniform(-0.1, 0.1))
        
        # Add random features for remaining dimensions
        while len(embedding) < self.embedding_dim:
            embedding.append(random.uniform(-1, 1))
        
        # Normalize
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        self.embedding_cache[text] = embedding
        return embedding
    
    def _create_feature_embedding(self, feature: ProductFeature) -> List[float]:
        """Özellik için embedding oluştur"""
        # Feature value + synonyms için embedding
        feature_text = f"{feature.value} {' '.join(feature.synonyms[:3])}"
        base_embedding = self._generate_deterministic_embedding(feature_text)
        
        # Category weight ile scale et
        category_weight = self.category_embedding_weights.get(feature.category, 1.0)
        weighted_embedding = [x * category_weight for x in base_embedding]
        
        return weighted_embedding
    
    def _combine_embeddings(self, base_embedding: List[float], 
                          feature_embeddings: Dict[str, List[float]], 
                          feature_weights: Dict[str, float]) -> List[float]:
        """Base ve feature embeddings'leri birleştir"""
        if not feature_embeddings:
            return base_embedding
        
        # Weighted average of feature embeddings
        weighted_feature_sum = [0.0] * self.embedding_dim
        total_weight = 0.0
        
        for feature_value, embedding in feature_embeddings.items():
            weight = feature_weights.get(feature_value, 1.0)
            for i in range(self.embedding_dim):
                weighted_feature_sum[i] += embedding[i] * weight
            total_weight += weight
        
        if total_weight > 0:
            avg_feature_embedding = [x / total_weight for x in weighted_feature_sum]
        else:
            avg_feature_embedding = [0.0] * self.embedding_dim
        
        # Combine base and feature embeddings (60% base, 40% features)
        combined = []
        for i in range(self.embedding_dim):
            combined_value = base_embedding[i] * 0.6 + avg_feature_embedding[i] * 0.4
            combined.append(combined_value)
        
        # Normalize
        norm = math.sqrt(sum(x * x for x in combined))
        if norm > 0:
            combined = [x / norm for x in combined]
        
        return combined
    
    def _calculate_semantic_match(self, query: str, query_embedding: EnhancedEmbedding,
                                query_features: List[ProductFeature],
                                product: Dict[str, Any], product_embedding: EnhancedEmbedding,
                                product_features: List[ProductFeature]) -> SemanticMatch:
        """Semantic match hesapla"""
        
        # Embedding similarity
        embedding_similarity = self._calculate_cosine_similarity(
            query_embedding.combined_embedding,
            product_embedding.combined_embedding
        )
        
        # Feature similarity
        feature_similarity, feature_scores = self._calculate_feature_similarity(
            query_features, product_features
        )
        
        # Text similarity (fallback)
        text_similarity = self._calculate_text_similarity(query, product.get('name', ''))
        
        # Combined similarity (weighted)
        combined_similarity = (
            embedding_similarity * 0.5 +
            feature_similarity * 0.4 +
            text_similarity * 0.1
        )
        
        # Confidence calculation
        confidence = self._calculate_confidence(
            embedding_similarity, feature_similarity, text_similarity, feature_scores
        )
        
        # Find matched features
        matched_features = [
            match_key.split('->')[1] for match_key in feature_scores.keys()
            if feature_scores[match_key] > 0.7
        ]
        
        # Explanation
        explanation = self._generate_explanation(
            embedding_similarity, feature_similarity, text_similarity, len(matched_features)
        )
        
        return SemanticMatch(
            product=product,
            similarity_score=combined_similarity,
            feature_similarity=feature_similarity,
            text_similarity=text_similarity,
            embedding_similarity=embedding_similarity,
            confidence=confidence,
            matched_features=matched_features,
            feature_scores=feature_scores,
            explanation=explanation
        )
    
    def _calculate_cosine_similarity(self, embedding1: List[float], 
                                   embedding2: List[float]) -> float:
        """Cosine similarity hesapla"""
        if len(embedding1) != len(embedding2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(x * x for x in embedding1))
        norm2 = math.sqrt(sum(x * x for x in embedding2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return max(0.0, dot_product / (norm1 * norm2))
    
    def _calculate_feature_similarity(self, query_features: List[ProductFeature], 
                                    product_features: List[ProductFeature]) -> Tuple[float, Dict[str, float]]:
        """Feature-based similarity hesapla"""
        if not query_features or not product_features:
            return 0.0, {}
        
        feature_scores = {}
        total_score = 0.0
        total_weight = 0.0
        
        for query_feature in query_features:
            best_match_score = 0.0
            best_match_feature = None
            
            # Direct match
            for product_feature in product_features:
                if query_feature.category == product_feature.category:
                    if query_feature.value == product_feature.value:
                        match_score = 1.0
                    elif query_feature.normalized_value == product_feature.normalized_value:
                        match_score = 0.95
                    elif (product_feature.value in query_feature.synonyms or 
                          query_feature.value in product_feature.synonyms):
                        match_score = 0.85
                    elif (query_feature.value in product_feature.value or 
                          product_feature.value in query_feature.value):
                        match_score = 0.7
                    else:
                        match_score = 0.0
                    
                    if match_score > best_match_score:
                        best_match_score = match_score
                        best_match_feature = product_feature.value
            
            if best_match_feature:
                feature_scores[f"{query_feature.value}->{best_match_feature}"] = best_match_score
                
                # Weight by feature importance
                weight = query_feature.weight * query_feature.confidence
                total_score += best_match_score * weight
                total_weight += weight
        
        overall_feature_similarity = total_score / total_weight if total_weight > 0 else 0.0
        return overall_feature_similarity, feature_scores
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Basic text similarity"""
        normalized1 = self._normalize_turkish_text(text1)
        normalized2 = self._normalize_turkish_text(text2)
        
        words1 = set(normalized1.split())
        words2 = set(normalized2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_confidence(self, embedding_sim: float, feature_sim: float, 
                            text_sim: float, feature_scores: Dict[str, float]) -> float:
        """Confidence score hesapla"""
        # Base confidence from similarities
        base_confidence = (embedding_sim * 0.4 + feature_sim * 0.4 + text_sim * 0.2)
        
        # Bonus for strong feature matches
        strong_feature_matches = sum(1 for score in feature_scores.values() if score > 0.8)
        feature_bonus = min(strong_feature_matches * 0.1, 0.3)
        
        # Penalty for low embedding similarity
        embedding_penalty = max(0, (0.4 - embedding_sim) * 0.2)
        
        # Bonus for high feature similarity
        feature_bonus_2 = min(feature_sim * 0.2, 0.2)
        
        final_confidence = base_confidence + feature_bonus + feature_bonus_2 - embedding_penalty
        return min(max(final_confidence, 0.0), 1.0)
    
    def _generate_explanation(self, embedding_sim: float, feature_sim: float, 
                            text_sim: float, matched_features_count: int) -> str:
        """Match explanation oluştur"""
        
        explanation_parts = []
        
        if embedding_sim > 0.7:
            explanation_parts.append("high embedding similarity")
        elif embedding_sim > 0.5:
            explanation_parts.append("medium embedding similarity")
        else:
            explanation_parts.append("low embedding similarity")
        
        if feature_sim > 0.7:
            explanation_parts.append("strong feature matches")
        elif feature_sim > 0.4:
            explanation_parts.append("moderate feature matches")
        else:
            explanation_parts.append("weak feature matches")
        
        if matched_features_count > 0:
            explanation_parts.append(f"{matched_features_count} matched features")
        
        return f"Semantic match: {', '.join(explanation_parts)}"
    
    def _normalize_turkish_text(self, text: str) -> str:
        """Turkish text normalization"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove Turkish characters
        for turkish_char, latin_char in self.turkish_char_map.items():
            normalized = normalized.replace(turkish_char.lower(), latin_char)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Embedding istatistikleri"""
        return {
            'embedding_dim': self.embedding_dim,
            'cached_embeddings': len(self.embedding_cache),
            'product_embeddings': len(self.product_embeddings),
            'category_weights': {cat.value: weight for cat, weight in self.category_embedding_weights.items()}
        }
    
    def clear_cache(self):
        """Cache'i temizle"""
        self.embedding_cache.clear()
        self.product_embeddings.clear()
        logger.info("Semantic similarity cache cleared")

# Test fonksiyonu
def test_semantic_similarity_matcher():
    """Semantic similarity matcher test"""
    
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
    
    matcher = SemanticSimilarityMatcher()
    
    print("🧠 Semantic Similarity Matcher Test:")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik bu ne kadar",
        "siyah gecelik",
        "hamile lohusa geceliği",
        "dantelli takım"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        matches = matcher.match_products(query, test_products, threshold=0.3)
        
        if matches:
            print(f"✅ Found {len(matches)} semantic matches:")
            for i, match in enumerate(matches, 1):
                print(f"\n  {i}. {match.product['name']}")
                print(f"     Similarity: {match.similarity_score:.3f}")
                print(f"     Embedding: {match.embedding_similarity:.3f}")
                print(f"     Feature: {match.feature_similarity:.3f}")
                print(f"     Text: {match.text_similarity:.3f}")
                print(f"     Confidence: {match.confidence:.3f}")
                print(f"     Explanation: {match.explanation}")
                
                if match.matched_features:
                    print(f"     Matched features: {', '.join(match.matched_features[:3])}")
        else:
            print("❌ No semantic matches found")
    
    # İstatistikler
    stats = matcher.get_embedding_stats()
    print(f"\n📊 Semantic Similarity Stats:")
    print(f"  Embedding dimension: {stats['embedding_dim']}")
    print(f"  Cached embeddings: {stats['cached_embeddings']}")
    print(f"  Product embeddings: {stats['product_embeddings']}")

if __name__ == "__main__":
    test_semantic_similarity_matcher()