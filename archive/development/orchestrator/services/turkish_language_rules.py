#!/usr/bin/env python3
"""
Turkish Language Rules - Türkçe dil kuralları ve normalizasyon
"""

import re
from typing import Dict, List, Set

class TurkishLanguageRules:
    """Türkçe dil kuralları ve normalizasyon sistemi"""
    
    def __init__(self):
        self._initialize_turkish_rules()
    
    def _initialize_turkish_rules(self):
        """Türkçe dil kurallarını initialize et"""
        
        # Türkçe ek normalizasyonu
        self.suffix_normalizations = {
            # Genitif ekleri
            r'\b(\w+)(nin|nın|nun|nün)\b': r'\1',
            r'\b(\w+)(in|ın|un|ün)\b': r'\1',
            
            # Accusative ekleri
            r'\b(\w+)(yi|yı|yu|yü)\b': r'\1',
            r'\b(\w+)(i|ı|u|ü)\b': r'\1',
            
            # Dative ekleri
            r'\b(\w+)(ye|ya)\b': r'\1',
            r'\b(\w+)(e|a)\b': r'\1',
            
            # Locative ekleri
            r'\b(\w+)(de|da)\b': r'\1',
            r'\b(\w+)(te|ta)\b': r'\1',
            
            # Ablative ekleri
            r'\b(\w+)(den|dan)\b': r'\1',
            r'\b(\w+)(ten|tan)\b': r'\1',
            
            # Plural ekleri
            r'\b(\w+)(ler|lar)\b': r'\1',
            
            # Possessive ekleri
            r'\b(\w+)(si|sı|su|sü)\b': r'\1',
            r'\b(\w+)(i|ı|u|ü)\b': r'\1'
        }
        
        # Özel kelime normalizasyonları
        self.word_normalizations = {
            'geceliği': 'gecelik',
            'geceliğin': 'gecelik',
            'geceliğe': 'gecelik',
            'gecelikler': 'gecelik',
            'gecelikleri': 'gecelik',
            
            'pijamayı': 'pijama',
            'pijamanın': 'pijama',
            'pijamaya': 'pijama',
            'pijamalar': 'pijama',
            'pijamaları': 'pijama',
            
            'sabahlığı': 'sabahlık',
            'sabahlığın': 'sabahlık',
            'sabahlığa': 'sabahlık',
            'sabahlıklar': 'sabahlık',
            'sabahlıkları': 'sabahlık',
            
            'takımı': 'takım',
            'takımın': 'takım',
            'takıma': 'takım',
            'takımlar': 'takım',
            'takımları': 'takım',
            
            'elbiseyi': 'elbise',
            'elbisenin': 'elbise',
            'elbiseye': 'elbise',
            'elbiseler': 'elbise',
            'elbiseleri': 'elbise',
            
            'dantelli': 'dantel',
            'dantelleri': 'dantel',
            'dantellerin': 'dantel',
            
            'tüllü': 'tül',
            'tülleri': 'tül',
            'tüllerin': 'tül',
            
            'pamuklu': 'pamuk',
            'pamukları': 'pamuk',
            'pamuklarin': 'pamuk',
            
            'askılı': 'askı',
            'askıları': 'askı',
            'askıların': 'askı',
            
            'düğmeli': 'düğme',
            'düğmeleri': 'düğme',
            'düğmelerin': 'düğme',
            
            'dekolteli': 'dekolte',
            'dekolteleri': 'dekolte',
            'dekoltelerin': 'dekolte'
        }
        
        # Türkçe karakter normalizasyonu
        self.character_normalizations = {
            'ç': 'c', 'Ç': 'C',
            'ğ': 'g', 'Ğ': 'G',
            'ı': 'i', 'I': 'I',
            'İ': 'I', 'i': 'i',
            'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S',
            'ü': 'u', 'Ü': 'U'
        }
        
        # Türkçe sinonimler
        self.turkish_synonyms = {
            'gecelik': ['nightgown', 'nightdress', 'gece elbisesi', 'uyku elbisesi'],
            'pijama': ['pajama', 'pyjama', 'ev kıyafeti', 'uyku kıyafeti'],
            'sabahlık': ['robe', 'bathrobe', 'morning gown', 'bornoz'],
            'takım': ['set', 'suit', 'kombin', 'eşofman'],
            'elbise': ['dress', 'frock', 'gown'],
            'bluz': ['blouse', 'top', 'shirt'],
            'şort': ['shorts', 'short', 'kısa pantolon'],
            'pantolon': ['pants', 'trousers', 'jean'],
            
            'dantel': ['lace', 'güpür', 'dantela'],
            'tül': ['tulle', 'mesh', 'file'],
            'pamuk': ['cotton', '100% pamuk', 'cotton blend'],
            'ipek': ['silk', 'satin', 'ipeksi'],
            'saten': ['satin', 'silk', 'parlak'],
            
            'siyah': ['black', 'kara', 'koyu'],
            'beyaz': ['white', 'ak', 'ekru', 'krem', 'bej'],
            'kırmızı': ['red', 'al', 'bordo', 'crimson'],
            'mavi': ['blue', 'lacivert', 'navy', 'gök'],
            'yeşil': ['green', 'yemyeşil', 'çimen'],
            'sarı': ['yellow', 'altın', 'gold', 'golden'],
            'pembe': ['pink', 'fuşya', 'rose', 'gül'],
            'mor': ['purple', 'lila', 'violet', 'menekşe'],
            
            'hamile': ['pregnant', 'maternity', 'anne adayı', 'gebe'],
            'lohusa': ['nursing', 'emziren', 'anne', 'postpartum'],
            
            'dekolteli': ['decollete', 'açık yakalı', 'göğüs açık'],
            'askılı': ['strappy', 'strap', 'ip askılı'],
            'düğmeli': ['buttoned', 'button', 'düğme'],
            'fermuarlı': ['zipped', 'zipper', 'fermuar']
        }
        
        # Türkçe stopwords (arama için önemsiz kelimeler)
        self.stopwords = {
            've', 'ile', 'için', 'olan', 'olarak', 'bu', 'şu', 'o',
            'bir', 'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz', 'on',
            'çok', 'az', 'biraz', 'oldukça', 'son', 'yeni', 'eski',
            'büyük', 'küçük', 'orta', 'normal', 'standart',
            'model', 'tip', 'tür', 'çeşit', 'stil', 'style'
        }
    
    def normalize_text(self, text: str) -> str:
        """
        Türkçe metni normalize et
        
        Args:
            text: Normalize edilecek metin
            
        Returns:
            str: Normalize edilmiş metin
        """
        if not text:
            return ""
        
        # Küçük harfe çevir
        normalized = text.lower().strip()
        
        # Özel kelime normalizasyonları
        words = normalized.split()
        normalized_words = []
        
        for word in words:
            # Stopwords'leri atla
            if word in self.stopwords:
                continue
            
            # Özel kelime normalizasyonu
            if word in self.word_normalizations:
                normalized_words.append(self.word_normalizations[word])
            else:
                # Ek normalizasyonu
                normalized_word = self._normalize_suffixes(word)
                normalized_words.append(normalized_word)
        
        return ' '.join(normalized_words)
    
    def _normalize_suffixes(self, word: str) -> str:
        """Türkçe ekleri normalize et"""
        for pattern, replacement in self.suffix_normalizations.items():
            word = re.sub(pattern, replacement, word)
        return word
    
    def normalize_for_search(self, text: str) -> str:
        """Arama için özel normalizasyon"""
        normalized = self.normalize_text(text)
        
        # Türkçe karakterleri ASCII'ye çevir (opsiyonel)
        # for turkish_char, ascii_char in self.character_normalizations.items():
        #     normalized = normalized.replace(turkish_char, ascii_char)
        
        return normalized
    
    def get_synonyms(self, word: str) -> List[str]:
        """Kelime için sinonimları getir"""
        normalized_word = self.normalize_text(word).strip()
        return self.turkish_synonyms.get(normalized_word, [])
    
    def expand_query_with_synonyms(self, query: str) -> List[str]:
        """Sorguyu sinonimlerle genişlet"""
        expanded_queries = [query]
        words = query.lower().split()
        
        for word in words:
            synonyms = self.get_synonyms(word)
            if synonyms:
                # Her sinonim için yeni sorgu oluştur
                for synonym in synonyms[:3]:  # İlk 3 sinonim
                    expanded_query = query.replace(word, synonym)
                    if expanded_query not in expanded_queries:
                        expanded_queries.append(expanded_query)
        
        return expanded_queries
    
    def extract_root_words(self, text: str) -> Set[str]:
        """Metinden kök kelimeleri çıkar"""
        normalized = self.normalize_text(text)
        words = normalized.split()
        
        root_words = set()
        for word in words:
            if len(word) > 2:  # Çok kısa kelimeleri atla
                root_words.add(word)
        
        return root_words
    
    def calculate_turkish_similarity(self, text1: str, text2: str) -> float:
        """Türkçe metinler arası benzerlik hesapla"""
        # Normalize et
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        # Kök kelimeleri çıkar
        roots1 = self.extract_root_words(norm1)
        roots2 = self.extract_root_words(norm2)
        
        if not roots1 or not roots2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(roots1.intersection(roots2))
        union = len(roots1.union(roots2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def enhance_search_terms(self, search_term: str) -> Dict[str, List[str]]:
        """Arama terimini zenginleştir"""
        normalized = self.normalize_text(search_term)
        
        enhancement = {
            'original': search_term,
            'normalized': normalized,
            'root_words': list(self.extract_root_words(normalized)),
            'synonyms': [],
            'expanded_queries': self.expand_query_with_synonyms(search_term)
        }
        
        # Her kelime için sinonimları topla
        for word in normalized.split():
            synonyms = self.get_synonyms(word)
            enhancement['synonyms'].extend(synonyms)
        
        # Duplicate'leri temizle
        enhancement['synonyms'] = list(set(enhancement['synonyms']))
        
        return enhancement

# Test fonksiyonu
def test_turkish_rules():
    """Turkish language rules test"""
    
    rules = TurkishLanguageRules()
    
    print("🇹🇷 Turkish Language Rules Test:")
    print("=" * 40)
    
    # Normalizasyon testleri
    test_texts = [
        "Hamile Lohusa Geceliği",
        "Dantelli Pijamalar",
        "Siyah Tüllü Sabahlıklar",
        "Göğüs ve Sırt Dekolteli Takımı",
        "Pamuklu Askılı Gecelikler"
    ]
    
    print("\n📝 Text Normalization:")
    for text in test_texts:
        normalized = rules.normalize_text(text)
        print(f"  '{text}' -> '{normalized}'")
    
    # Sinonim testleri
    print("\n🔄 Synonym Expansion:")
    test_words = ['gecelik', 'pijama', 'dantel', 'siyah', 'hamile']
    for word in test_words:
        synonyms = rules.get_synonyms(word)
        print(f"  '{word}': {synonyms[:3]}")  # İlk 3 sinonim
    
    # Sorgu genişletme testleri
    print("\n🔍 Query Expansion:")
    test_queries = [
        "siyah gecelik",
        "hamile pijama",
        "dantelli takım"
    ]
    
    for query in test_queries:
        expanded = rules.expand_query_with_synonyms(query)
        print(f"  '{query}':")
        for exp in expanded[:3]:  # İlk 3 genişletilmiş sorgu
            print(f"    -> '{exp}'")
    
    # Benzerlik testleri
    print("\n📊 Similarity Calculation:")
    similarity_tests = [
        ("hamile geceliği", "hamile gecelik"),
        ("siyah dantelli", "black lace"),
        ("pijama takımı", "pajama set")
    ]
    
    for text1, text2 in similarity_tests:
        similarity = rules.calculate_turkish_similarity(text1, text2)
        print(f"  '{text1}' <-> '{text2}': {similarity:.3f}")

if __name__ == "__main__":
    test_turkish_rules()