"""
Fuzzy Matching Engine - Turkish-aware fuzzy string matching
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FuzzyMatch:
    """Fuzzy matching sonucu"""
    product: Dict[str, Any]
    similarity_score: float
    ratio_score: float
    token_sort_score: float
    token_set_score: float
    partial_score: float
    confidence: float
    matched_tokens: List[str]
    explanation: str

class TurkishNormalizer:
    """Turkish text normalization"""
    
    def __init__(self):
        # Turkish character mapping
        self.turkish_char_map = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
        }
        
        # Common Turkish suffixes
        self.turkish_suffixes = [
            'ları', 'leri', 'lar', 'ler',  # plural
            'ının', 'inin', 'unun', 'ünün',  # genitive
            'ını', 'ini', 'unu', 'ünü',  # accusative
            'ına', 'ine', 'una', 'üne',  # dative
            'ında', 'inde', 'unda', 'ünde',  # locative
            'ından', 'inden', 'undan', 'ünden',  # ablative
            'ıyla', 'iyle', 'uyla', 'üyle',  # instrumental
            'ı', 'i', 'u', 'ü',  # accusative short
            'ın', 'in', 'un', 'ün',  # genitive short
            'a', 'e',  # dative short
            'da', 'de', 'ta', 'te',  # locative short
            'dan', 'den', 'tan', 'ten',  # ablative short
            'la', 'le',  # instrumental short
            'sı', 'si', 'su', 'sü',  # possessive
            'lık', 'lik', 'luk', 'lük',  # suffix
            'cı', 'ci', 'cu', 'cü',  # agent
            'lı', 'li', 'lu', 'lü'  # adjective
        ]
        
        # Phonetic variations
        self.phonetic_variations = {
            'k': ['c', 'q'],
            'c': ['k', 'ç'],
            'ç': ['c', 'ch'],
            'ş': ['s', 'sh'],
            'ğ': ['g', ''],
            'ı': ['i'],
            'i': ['ı'],
            'ö': ['o'],
            'o': ['ö'],
            'ü': ['u'],
            'u': ['ü']
        }
    
    def normalize(self, text: str) -> str:
        """Turkish text normalization"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Replace Turkish characters
        for turkish_char, latin_char in self.turkish_char_map.items():
            normalized = normalized.replace(turkish_char.lower(), latin_char)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def remove_suffixes(self, word: str) -> str:
        """Remove Turkish suffixes from word"""
        if len(word) <= 3:
            return word
        
        # Try to remove suffixes (longest first)
        for suffix in sorted(self.turkish_suffixes, key=len, reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        
        return word
    
    def generate_phonetic_variations(self, word: str) -> Set[str]:
        """Generate phonetic variations of a word"""
        variations = {word}
        
        for char, alternatives in self.phonetic_variations.items():
            if char in word:
                for alt in alternatives:
                    variations.add(word.replace(char, alt))
        
        return variations

class FuzzyStringMatcher:
    """Basic fuzzy string matching without external dependencies"""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance"""
        if len(s1) < len(s2):
            return FuzzyStringMatcher.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def ratio(s1: str, s2: str) -> float:
        """Calculate similarity ratio (0-1)"""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        distance = FuzzyStringMatcher.levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        
        return 1.0 - (distance / max_len)
    
    @staticmethod
    def partial_ratio(s1: str, s2: str) -> float:
        """Calculate partial ratio for substring matching"""
        if not s1 or not s2:
            return 0.0
        
        shorter, longer = (s1, s2) if len(s1) <= len(s2) else (s2, s1)
        
        best_ratio = 0.0
        for i in range(len(longer) - len(shorter) + 1):
            substring = longer[i:i + len(shorter)]
            ratio = FuzzyStringMatcher.ratio(shorter, substring)
            best_ratio = max(best_ratio, ratio)
        
        return best_ratio
    
    @staticmethod
    def token_sort_ratio(s1: str, s2: str) -> float:
        """Calculate token sort ratio"""
        if not s1 or not s2:
            return 0.0
        
        tokens1 = sorted(s1.split())
        tokens2 = sorted(s2.split())
        
        sorted_s1 = ' '.join(tokens1)
        sorted_s2 = ' '.join(tokens2)
        
        return FuzzyStringMatcher.ratio(sorted_s1, sorted_s2)
    
    @staticmethod
    def token_set_ratio(s1: str, s2: str) -> float:
        """Calculate token set ratio"""
        if not s1 or not s2:
            return 0.0
        
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        if not union:
            return 1.0
        
        return len(intersection) / len(union)

class FuzzyMatchingEngine:
    """Turkish-aware fuzzy matching engine"""
    
    def __init__(self):
        self.normalizer = TurkishNormalizer()
        self.matcher = FuzzyStringMatcher()
        
        # Scoring weights
        self.score_weights = {
            'ratio': 0.3,
            'token_sort': 0.25,
            'token_set': 0.25,
            'partial': 0.2
        }
        
        # Turkish-specific boost patterns
        self.boost_patterns = [
            (r'\bgecelik\b', 1.1),
            (r'\bpijama\b', 1.1),
            (r'\belbise\b', 1.1),
            (r'\bsabahlık\b', 1.1),
            (r'\btakım\b', 1.1),
            (r'\bhamile\b', 1.2),
            (r'\blohusa\b', 1.2),
            (r'\bdantelli\b', 1.1),
            (r'\bdüğmeli\b', 1.1),
            (r'\bsiyah\b', 1.05),
            (r'\bbeyaz\b', 1.05)
        ]
    
    def match_products(self, query: str, products: List[Dict[str, Any]], 
                      threshold: float = 0.6) -> List[FuzzyMatch]:
        """Ürünleri query ile fuzzy matching yap"""
        
        if not query or not query.strip():
            return []
        
        # Normalize query
        normalized_query = self.normalizer.normalize(query)
        query_tokens = set(normalized_query.split())
        
        matches = []
        
        for product in products:
            product_name = product.get('name', '')
            if not product_name:
                continue
            
            # Calculate fuzzy match
            fuzzy_match = self._calculate_fuzzy_match(
                query, normalized_query, query_tokens, product, product_name
            )
            
            # Threshold kontrolü
            if fuzzy_match.similarity_score >= threshold:
                matches.append(fuzzy_match)
        
        # Score'a göre sırala
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches
    
    def _calculate_fuzzy_match(self, original_query: str, normalized_query: str,
                             query_tokens: Set[str], product: Dict[str, Any],
                             product_name: str) -> FuzzyMatch:
        """Tek bir ürün için fuzzy match hesapla"""
        
        # Normalize product name
        normalized_product = self.normalizer.normalize(product_name)
        product_tokens = set(normalized_product.split())
        
        # Calculate different similarity scores
        ratio_score = self.matcher.ratio(normalized_query, normalized_product)
        token_sort_score = self.matcher.token_sort_ratio(normalized_query, normalized_product)
        token_set_score = self.matcher.token_set_ratio(normalized_query, normalized_product)
        partial_score = self.matcher.partial_ratio(normalized_query, normalized_product)
        
        # Calculate weighted similarity
        similarity_score = (
            ratio_score * self.score_weights['ratio'] +
            token_sort_score * self.score_weights['token_sort'] +
            token_set_score * self.score_weights['token_set'] +
            partial_score * self.score_weights['partial']
        )
        
        # Apply Turkish-specific boosts
        similarity_score = self._apply_turkish_boosts(
            similarity_score, normalized_query, normalized_product
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            ratio_score, token_sort_score, token_set_score, partial_score
        )
        
        # Find matched tokens
        matched_tokens = list(query_tokens & product_tokens)
        
        # Generate explanation
        explanation = self._generate_explanation(
            ratio_score, token_sort_score, token_set_score, partial_score, matched_tokens
        )
        
        return FuzzyMatch(
            product=product,
            similarity_score=min(similarity_score, 1.0),
            ratio_score=ratio_score,
            token_sort_score=token_sort_score,
            token_set_score=token_set_score,
            partial_score=partial_score,
            confidence=confidence,
            matched_tokens=matched_tokens,
            explanation=explanation
        )
    
    def _apply_turkish_boosts(self, base_score: float, query: str, product: str) -> float:
        """Apply Turkish-specific scoring boosts"""
        boost_factor = 1.0
        
        for pattern, boost in self.boost_patterns:
            if re.search(pattern, query) and re.search(pattern, product):
                boost_factor *= boost
        
        # Suffix matching boost
        query_words = query.split()
        product_words = product.split()
        
        suffix_matches = 0
        for q_word in query_words:
            q_root = self.normalizer.remove_suffixes(q_word)
            for p_word in product_words:
                p_root = self.normalizer.remove_suffixes(p_word)
                if q_root == p_root and len(q_root) > 2:
                    suffix_matches += 1
                    break
        
        if suffix_matches > 0:
            boost_factor *= (1.0 + suffix_matches * 0.05)
        
        # Phonetic variation boost
        phonetic_matches = 0
        for q_word in query_words:
            q_variations = self.normalizer.generate_phonetic_variations(q_word)
            for p_word in product_words:
                if p_word in q_variations:
                    phonetic_matches += 1
                    break
        
        if phonetic_matches > 0:
            boost_factor *= (1.0 + phonetic_matches * 0.03)
        
        return base_score * boost_factor
    
    def _calculate_confidence(self, ratio: float, token_sort: float, 
                            token_set: float, partial: float) -> float:
        """Confidence score hesapla"""
        
        # Base confidence from average scores
        avg_score = (ratio + token_sort + token_set + partial) / 4
        
        # Consistency bonus - scores should be similar for high confidence
        scores = [ratio, token_sort, token_set, partial]
        max_score = max(scores)
        min_score = min(scores)
        consistency = 1.0 - (max_score - min_score)
        
        # High score bonus
        high_score_bonus = max(0, avg_score - 0.7) * 0.5
        
        # Final confidence
        confidence = avg_score * 0.7 + consistency * 0.2 + high_score_bonus
        
        return min(max(confidence, 0.0), 1.0)
    
    def _generate_explanation(self, ratio: float, token_sort: float, 
                            token_set: float, partial: float, 
                            matched_tokens: List[str]) -> str:
        """Match explanation oluştur"""
        
        explanation_parts = []
        
        # Best score type
        scores = {
            'exact': ratio,
            'sorted': token_sort,
            'token': token_set,
            'partial': partial
        }
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        if best_score > 0.8:
            explanation_parts.append(f"high {best_type} similarity")
        elif best_score > 0.6:
            explanation_parts.append(f"medium {best_type} similarity")
        else:
            explanation_parts.append(f"low {best_type} similarity")
        
        # Matched tokens
        if matched_tokens:
            if len(matched_tokens) == 1:
                explanation_parts.append(f"1 matched token")
            else:
                explanation_parts.append(f"{len(matched_tokens)} matched tokens")
        
        return f"Fuzzy match: {', '.join(explanation_parts)}"
    
    def explain_match(self, query: str, product: Dict[str, Any]) -> Dict[str, Any]:
        """Tek bir ürün için detaylı match explanation"""
        
        normalized_query = self.normalizer.normalize(query)
        query_tokens = set(normalized_query.split())
        product_name = product.get('name', '')
        
        fuzzy_match = self._calculate_fuzzy_match(
            query, normalized_query, query_tokens, product, product_name
        )
        
        return {
            "product_name": product_name,
            "normalized_query": normalized_query,
            "normalized_product": self.normalizer.normalize(product_name),
            "similarity_score": fuzzy_match.similarity_score,
            "confidence": fuzzy_match.confidence,
            "scores": {
                "ratio": fuzzy_match.ratio_score,
                "token_sort": fuzzy_match.token_sort_score,
                "token_set": fuzzy_match.token_set_score,
                "partial": fuzzy_match.partial_score
            },
            "matched_tokens": fuzzy_match.matched_tokens,
            "explanation": fuzzy_match.explanation
        }

# Test fonksiyonu
def test_fuzzy_matching_engine():
    """Fuzzy matching engine test"""
    
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
    
    engine = FuzzyMatchingEngine()
    
    print("🔀 Fuzzy Matching Engine Test:")
    print("=" * 50)
    
    # Test queries with typos and variations
    test_queries = [
        "Kolu Omzu ve Yakası Dantelli Önü Düğmeli Gecelik",  # Exact
        "kol omuz yaka dantelli dugmeli gecelik",  # No Turkish chars, different order
        "siyah gecelig",  # Typo
        "hamile lohusa geceliği",  # With suffix
        "danteli takım",  # Typo in dantelli
        "afrika gecelik",  # Partial match
        "göğüs dekolteli takım"  # Partial match
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        matches = engine.match_products(query, test_products, threshold=0.4)
        
        if matches:
            print(f"✅ Found {len(matches)} fuzzy matches:")
            for i, match in enumerate(matches, 1):
                print(f"\n  {i}. {match.product['name']}")
                print(f"     Similarity: {match.similarity_score:.3f}")
                print(f"     Confidence: {match.confidence:.3f}")
                print(f"     Scores: R:{match.ratio_score:.2f} TS:{match.token_sort_score:.2f} TSe:{match.token_set_score:.2f} P:{match.partial_score:.2f}")
                print(f"     Explanation: {match.explanation}")
                
                if match.matched_tokens:
                    print(f"     Matched tokens: {', '.join(match.matched_tokens)}")
        else:
            print("❌ No fuzzy matches found")
    
    # Detailed explanation for a specific case
    print(f"\n🔍 Detailed Match Explanation:")
    explanation = engine.explain_match("kol omuz dantelli gecelik", test_products[0])
    print(f"  Query: kol omuz dantelli gecelik")
    print(f"  Product: {explanation['product_name']}")
    print(f"  Normalized Query: {explanation['normalized_query']}")
    print(f"  Normalized Product: {explanation['normalized_product']}")
    print(f"  Similarity: {explanation['similarity_score']:.3f}")
    print(f"  Confidence: {explanation['confidence']:.3f}")
    print(f"  Matched Tokens: {', '.join(explanation['matched_tokens'])}")

if __name__ == "__main__":
    test_fuzzy_matching_engine()