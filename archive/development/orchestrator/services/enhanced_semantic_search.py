#!/usr/bin/env python3
"""
Enhanced Semantic Search - Basit ama güçlü
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

@dataclass
class SearchMatch:
    """Arama sonucu"""
    product: Dict[str, Any]
    score: float
    confidence: float
    matched_features: List[str]
    match_type: str
    explanation: str

class EnhancedSemanticSearch:
    """Gelişmiş semantic search - basit ama etkili"""
    
    def __init__(self):
        # Türkçe karakter normalizasyonu
        self.turkish_map = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
        }
        
        # Ürün kategorileri ve synonyms
        self.product_categories = {
            "gecelik": ["gecelik", "geceliği", "geceliğin", "nightgown", "nightdress"],
            "pijama": ["pijama", "pijamayı", "pijamanın", "pajama", "pyjama"],
            "takım": ["takım", "takımı", "takımın", "set", "suit"],
            "elbise": ["elbise", "elbiseyi", "elbisenin", "dress"],
            "sabahlık": ["sabahlık", "sabahlığı", "robe"]
        }
        
        # Özellik kategorileri
        self.feature_categories = {
            "colors": {
                "siyah": ["siyah", "black", "kara"],
                "beyaz": ["beyaz", "white", "ak"],
                "kırmızı": ["kırmızı", "red", "al"],
                "mavi": ["mavi", "blue", "gök"],
                "yeşil": ["yeşil", "green"],
                "pembe": ["pembe", "pink", "rozé"],
                "ekru": ["ekru", "cream", "krem"],
                "bej": ["bej", "beige"]
            },
            "patterns": {
                "dantelli": ["dantelli", "dantel", "lace", "lacy"],
                "çiçekli": ["çiçek", "çiçekli", "floral", "flower"],
                "desenli": ["desen", "desenli", "pattern", "patterned"],
                "yaprak": ["yaprak", "leaf", "leaves"],
                "etnik": ["etnik", "ethnic", "afrika", "africa"]
            },
            "styles": {
                "dekolteli": ["dekolte", "dekolteli", "low-cut", "v-neck"],
                "askılı": ["askı", "askılı", "strap", "strappy"],
                "düğmeli": ["düğme", "düğmeli", "button", "buttoned"],
                "uzun": ["uzun", "long"],
                "kısa": ["kısa", "short"]
            },
            "target_groups": {
                "hamile": ["hamile", "pregnancy", "pregnant", "maternity"],
                "lohusa": ["lohusa", "nursing", "breastfeeding", "postpartum"]
            }
        }
        
        # Stopwords - arama için önemsiz kelimeler
        self.stopwords = {
            "ve", "ile", "için", "bu", "şu", "o", "bir", "the", "and", "or", "of", "in", "on", "at"
        }
    
    def search(self, query: str, products: List[Dict[str, Any]], 
               limit: int = 5, min_score: float = 0.3) -> List[SearchMatch]:
        """Ana arama fonksiyonu"""
        
        if not query or not products:
            return []
        
        # Query'yi normalize et ve analiz et
        normalized_query = self._normalize_text(query)
        query_features = self._extract_query_features(normalized_query)
        
        logger.info(f"Search query: '{query}' -> normalized: '{normalized_query}'")
        logger.info(f"Extracted features: {query_features}")
        
        matches = []
        
        for product in products:
            product_name = product.get('name', '')
            if not product_name:
                continue
            
            # Multi-stage matching
            match = self._calculate_multi_stage_match(
                query, normalized_query, query_features, product, product_name
            )
            
            if match and match.score >= min_score:
                matches.append(match)
        
        # Score'a göre sırala
        matches.sort(key=lambda x: x.score, reverse=True)
        
        return matches[:limit]
    
    def _normalize_text(self, text: str) -> str:
        """Metni normalize et"""
        if not text:
            return ""
        
        # Küçük harfe çevir
        normalized = text.lower().strip()
        
        # Türkçe karakterleri değiştir
        for tr_char, en_char in self.turkish_map.items():
            normalized = normalized.replace(tr_char.lower(), en_char)
        
        # Özel karakterleri temizle
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Çoklu boşlukları tek boşluğa çevir
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_query_features(self, query: str) -> Dict[str, List[str]]:
        """Query'den özellikleri çıkar"""
        features = {
            "products": [],
            "colors": [],
            "patterns": [],
            "styles": [],
            "target_groups": [],
            "keywords": []
        }
        
        query_words = query.split()
        
        # Ürün kategorilerini bul
        for category, synonyms in self.product_categories.items():
            if any(synonym in query for synonym in synonyms):
                features["products"].append(category)
        
        # Renkleri bul
        for color, synonyms in self.feature_categories["colors"].items():
            if any(synonym in query for synonym in synonyms):
                features["colors"].append(color)
        
        # Desenleri bul
        for pattern, synonyms in self.feature_categories["patterns"].items():
            if any(synonym in query for synonym in synonyms):
                features["patterns"].append(pattern)
        
        # Stilleri bul
        for style, synonyms in self.feature_categories["styles"].items():
            if any(synonym in query for synonym in synonyms):
                features["styles"].append(style)
        
        # Hedef grupları bul
        for group, synonyms in self.feature_categories["target_groups"].items():
            if any(synonym in query for synonym in synonyms):
                features["target_groups"].append(group)
        
        # Diğer önemli kelimeleri bul
        for word in query_words:
            if len(word) > 2 and word not in self.stopwords:
                features["keywords"].append(word)
        
        return features
    
    def _calculate_multi_stage_match(self, original_query: str, normalized_query: str, 
                                   query_features: Dict[str, List[str]], 
                                   product: Dict[str, Any], product_name: str) -> Optional[SearchMatch]:
        """Multi-stage matching algoritması"""
        
        normalized_product = self._normalize_text(product_name)
        product_features = self._extract_query_features(normalized_product)
        
        # Stage 1: Exact match
        exact_score = self._calculate_exact_match(normalized_query, normalized_product)
        
        # Stage 2: Feature-based match
        feature_score, matched_features = self._calculate_feature_match(query_features, product_features)
        
        # Stage 3: Fuzzy string similarity
        fuzzy_score = self._calculate_fuzzy_similarity(normalized_query, normalized_product)
        
        # Stage 4: Keyword overlap
        keyword_score = self._calculate_keyword_overlap(query_features["keywords"], 
                                                       product_features["keywords"])
        
        # Weighted final score
        final_score = (
            exact_score * 0.4 +
            feature_score * 0.3 +
            fuzzy_score * 0.2 +
            keyword_score * 0.1
        )
        
        # Confidence calculation
        confidence = self._calculate_confidence(exact_score, feature_score, fuzzy_score, 
                                              len(matched_features))
        
        # Match type
        if exact_score > 0.8:
            match_type = "exact"
        elif feature_score > 0.7:
            match_type = "feature"
        elif fuzzy_score > 0.6:
            match_type = "fuzzy"
        else:
            match_type = "keyword"
        
        # Explanation
        explanation = self._generate_explanation(exact_score, feature_score, fuzzy_score, 
                                               matched_features)
        
        return SearchMatch(
            product=product,
            score=final_score,
            confidence=confidence,
            matched_features=matched_features,
            match_type=match_type,
            explanation=explanation
        )
    
    def _calculate_exact_match(self, query: str, product_name: str) -> float:
        """Exact match score"""
        if query == product_name:
            return 1.0
        elif query in product_name:
            return 0.8
        elif product_name in query:
            return 0.6
        else:
            return 0.0
    
    def _calculate_feature_match(self, query_features: Dict[str, List[str]], 
                               product_features: Dict[str, List[str]]) -> Tuple[float, List[str]]:
        """Feature-based matching"""
        matched_features = []
        total_score = 0.0
        total_weight = 0.0
        
        # Feature weights
        feature_weights = {
            "products": 3.0,
            "colors": 2.0,
            "patterns": 2.0,
            "styles": 1.5,
            "target_groups": 2.5,
            "keywords": 1.0
        }
        
        for feature_type, weight in feature_weights.items():
            query_vals = query_features.get(feature_type, [])
            product_vals = product_features.get(feature_type, [])
            
            if query_vals and product_vals:
                # Intersection over union
                intersection = set(query_vals) & set(product_vals)
                union = set(query_vals) | set(product_vals)
                
                if union:
                    feature_score = len(intersection) / len(union)
                    total_score += feature_score * weight
                    total_weight += weight
                    
                    # Add matched features
                    matched_features.extend(list(intersection))
        
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        return overall_score, matched_features
    
    def _calculate_fuzzy_similarity(self, query: str, product_name: str) -> float:
        """Fuzzy string similarity"""
        if not query or not product_name:
            return 0.0
        
        # SequenceMatcher kullan
        similarity = SequenceMatcher(None, query, product_name).ratio()
        
        # Bonus for common substrings
        query_words = set(query.split())
        product_words = set(product_name.split())
        
        if query_words and product_words:
            word_overlap = len(query_words & product_words) / len(query_words | product_words)
            similarity = max(similarity, word_overlap * 0.8)
        
        return similarity
    
    def _calculate_keyword_overlap(self, query_keywords: List[str], 
                                 product_keywords: List[str]) -> float:
        """Keyword overlap score"""
        if not query_keywords or not product_keywords:
            return 0.0
        
        query_set = set(query_keywords)
        product_set = set(product_keywords)
        
        intersection = query_set & product_set
        union = query_set | product_set
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_confidence(self, exact_score: float, feature_score: float, 
                            fuzzy_score: float, matched_features_count: int) -> float:
        """Confidence score hesapla"""
        base_confidence = (exact_score * 0.4 + feature_score * 0.4 + fuzzy_score * 0.2)
        
        # Bonus for multiple matched features
        feature_bonus = min(matched_features_count * 0.1, 0.3)
        
        # Penalty for very low scores
        penalty = 0.0
        if exact_score < 0.2 and feature_score < 0.3:
            penalty = 0.2
        
        final_confidence = base_confidence + feature_bonus - penalty
        return max(0.0, min(1.0, final_confidence))
    
    def _generate_explanation(self, exact_score: float, feature_score: float, 
                            fuzzy_score: float, matched_features: List[str]) -> str:
        """Match explanation oluştur"""
        explanations = []
        
        if exact_score > 0.5:
            explanations.append("exact match")
        if feature_score > 0.5:
            explanations.append("feature match")
        if fuzzy_score > 0.5:
            explanations.append("fuzzy similarity")
        
        if matched_features:
            explanations.append(f"{len(matched_features)} matched features")
        
        return ", ".join(explanations) if explanations else "low similarity"

def test_enhanced_semantic_search():
    """Test enhanced semantic search"""
    
    # Test products
    test_products = [
        {
            "id": 1,
            "name": "Çiçek ve Yaprak Desenli Dekolteli Gecelik",
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
            "name": "Çiçek Desenli Tüllü Takım",
            "color": "PEMBE",
            "price": 1200.00
        }
    ]
    
    search_engine = EnhancedSemanticSearch()
    
    print("🔍 ENHANCED SEMANTIC SEARCH TEST")
    print("=" * 50)
    
    # Test queries - problematic ones from user
    test_queries = [
        "Çiçek ve Yaprak Desenli Dekolteli Gecelik",
        "çiçek desenli tüllü takım fiyatı",
        "afrika gecelik",
        "hamile lohusa gecelik",
        "siyah gecelik",
        "dantelli takım"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        matches = search_engine.search(query, test_products, limit=3, min_score=0.2)
        
        if matches:
            print(f"✅ Found {len(matches)} matches:")
            for i, match in enumerate(matches, 1):
                print(f"\n  {i}. {match.product['name']}")
                print(f"     Score: {match.score:.3f}")
                print(f"     Confidence: {match.confidence:.3f}")
                print(f"     Type: {match.match_type}")
                print(f"     Features: {', '.join(match.matched_features[:3])}")
                print(f"     Explanation: {match.explanation}")
        else:
            print("❌ No matches found")
    
    print(f"\n🎯 Test completed!")

if __name__ == "__main__":
    test_enhanced_semantic_search()