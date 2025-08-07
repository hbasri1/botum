#!/usr/bin/env python3
"""
Ürün Adı Düzeltme Sistemi - Türkçe Optimize
"""

import re
from typing import Dict, List, Tuple
from rapidfuzz import fuzz
import json

class TurkishProductNameCorrector:
    """Türkçe ürün adı düzeltme sistemi"""
    
    def __init__(self):
        # Türkçe ekleri ve çekimleri
        self.turkish_suffixes = {
            # Gecelik çekimleri
            'geceliği': 'gecelik', 'geceliğin': 'gecelik', 'geceliğe': 'gecelik',
            'gecelikler': 'gecelik', 'gecelig': 'gecelik', 'geceliğim': 'gecelik',
            
            # Pijama çekimleri
            'pijamayı': 'pijama', 'pijamanın': 'pijama', 'pijamaya': 'pijama',
            'pijamalar': 'pijama', 'pijamaları': 'pijama', 'pijamam': 'pijama',
            
            # Elbise çekimleri
            'elbiseyi': 'elbise', 'elbisenin': 'elbise', 'elbiseye': 'elbise',
            'elbiseler': 'elbise', 'elbiseleri': 'elbise', 'elbisem': 'elbise',
            
            # Sabahlık çekimleri
            'sabahlığı': 'sabahlık', 'sabahlığın': 'sabahlık', 'sabahlığa': 'sabahlık',
            'sabahlıklar': 'sabahlık', 'sabahlıkları': 'sabahlık',
            
            # Takım çekimleri
            'takımı': 'takım', 'takımın': 'takım', 'takıma': 'takım',
            'takımlar': 'takım', 'takımları': 'takım', 'takimi': 'takım'
        }
        
        # Yaygın yazım hataları
        self.typo_corrections = {
            'gecelig': 'gecelik',
            'pijama': 'pijama',  # Doğru yazım
            'pyjama': 'pijama',
            'pajama': 'pijama',
            'afirca': 'afrika',
            'afirka': 'afrika',
            'hamile': 'hamile',  # Doğru yazım
            'lohusa': 'lohusa',  # Doğru yazım
            'danteli': 'dantelli',
            'danteli': 'dantelli'
        }
        
        # Renk normalizasyonu
        self.color_mapping = {
            'siyah': ['siyah', 'black', 'kara'],
            'beyaz': ['beyaz', 'white', 'ak'],
            'kırmızı': ['kırmızı', 'red', 'al'],
            'mavi': ['mavi', 'blue', 'gök'],
            'yeşil': ['yeşil', 'green'],
            'sarı': ['sarı', 'yellow'],
            'pembe': ['pembe', 'pink', 'rozé'],
            'mor': ['mor', 'purple', 'menekşe'],
            'lacivert': ['lacivert', 'navy', 'koyu mavi'],
            'bordo': ['bordo', 'burgundy', 'koyu kırmızı'],
            'bej': ['bej', 'beige', 'krem'],
            'gri': ['gri', 'gray', 'grey', 'kül'],
            'ekru': ['ekru', 'cream', 'krem']
        }
        
        # Özel ürün kombinasyonları
        self.special_combinations = {
            ('afrika', 'gecelik'): 'afrika gecelik',
            ('africa', 'gecelik'): 'afrika gecelik',
            ('hamile', 'gecelik'): 'hamile gecelik',
            ('hamile', 'pijama'): 'hamile pijama',
            ('lohusa', 'gecelik'): 'lohusa gecelik',
            ('pijama', 'takım'): 'pijama takımı',
            ('pijama', 'takimi'): 'pijama takımı'
        }
    
    def correct_product_name(self, query: str) -> str:
        """Ana düzeltme fonksiyonu"""
        if not query:
            return ""
        
        # 1. Temel temizlik
        corrected = self._basic_cleanup(query)
        
        # 2. Yazım hatası düzeltme
        corrected = self._fix_typos(corrected)
        
        # 3. Türkçe ek düzeltme
        corrected = self._fix_turkish_suffixes(corrected)
        
        # 4. Renk normalizasyonu
        corrected = self._normalize_colors(corrected)
        
        # 5. Özel kombinasyonlar
        corrected = self._handle_special_combinations(corrected)
        
        # 6. Son temizlik
        corrected = self._final_cleanup(corrected)
        
        return corrected
    
    def _basic_cleanup(self, text: str) -> str:
        """Temel temizlik"""
        # Küçük harfe çevir
        text = text.lower().strip()
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text)
        
        # Özel karakterleri temizle (ama Türkçe karakterleri koru)
        text = re.sub(r'[^\w\sçğıöşüÇĞIİÖŞÜ]', ' ', text)
        
        return text.strip()
    
    def _fix_typos(self, text: str) -> str:
        """Yazım hatalarını düzelt"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Direkt eşleşme
            if word in self.typo_corrections:
                corrected_words.append(self.typo_corrections[word])
            else:
                # Fuzzy matching ile yakın kelime bul
                best_match = None
                best_score = 0
                
                for correct_word in self.typo_corrections.values():
                    score = fuzz.ratio(word, correct_word)
                    if score > 80 and score > best_score:
                        best_score = score
                        best_match = correct_word
                
                corrected_words.append(best_match or word)
        
        return ' '.join(corrected_words)
    
    def _fix_turkish_suffixes(self, text: str) -> str:
        """Türkçe ekleri düzelt"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Direkt eşleşme
            if word in self.turkish_suffixes:
                corrected_words.append(self.turkish_suffixes[word])
            else:
                # Kısmi eşleşme (kelime içinde ek var mı?)
                corrected = word
                for suffix, root in self.turkish_suffixes.items():
                    if suffix in word and word != suffix:
                        # Kelimenin başında root var mı kontrol et
                        if word.startswith(root) or root in word:
                            corrected = root
                            break
                
                corrected_words.append(corrected)
        
        return ' '.join(corrected_words)
    
    def _normalize_colors(self, text: str) -> str:
        """Renkleri normalize et"""
        words = text.split()
        normalized_words = []
        
        for word in words:
            color_found = False
            
            # Her renk için kontrol et
            for standard_color, variations in self.color_mapping.items():
                if word in variations:
                    normalized_words.append(standard_color)
                    color_found = True
                    break
            
            if not color_found:
                normalized_words.append(word)
        
        return ' '.join(normalized_words)
    
    def _handle_special_combinations(self, text: str) -> str:
        """Özel kombinasyonları handle et"""
        words = text.split()
        
        # İki kelimeli kombinasyonları kontrol et
        for i in range(len(words) - 1):
            combination = (words[i], words[i + 1])
            if combination in self.special_combinations:
                # Kombinasyonu değiştir
                result = self.special_combinations[combination]
                # Yeni listeyi oluştur
                new_words = words[:i] + result.split() + words[i + 2:]
                return ' '.join(new_words)
        
        # Üç kelimeli kombinasyonları da kontrol edebiliriz
        for i in range(len(words) - 2):
            # Örnek: "afrika style gecelik" → "afrika gecelik"
            if words[i] == 'afrika' and words[i + 2] == 'gecelik':
                new_words = words[:i] + ['afrika', 'gecelik'] + words[i + 3:]
                return ' '.join(new_words)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Son temizlik"""
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Boş string kontrolü
        if not text:
            return ""
        
        return text
    
    def get_correction_confidence(self, original: str, corrected: str) -> float:
        """Düzeltme güven skoru"""
        if original == corrected:
            return 1.0
        
        # Fuzzy similarity
        similarity = fuzz.ratio(original.lower(), corrected.lower()) / 100
        
        # Uzunluk farkı penaltısı
        length_diff = abs(len(original) - len(corrected)) / max(len(original), len(corrected))
        length_penalty = max(0, 1 - length_diff)
        
        return similarity * length_penalty

def test_correction_system():
    """Düzeltme sistemini test et"""
    corrector = TurkishProductNameCorrector()
    
    test_cases = [
        "afrika geceliği",
        "afirca gecelig",
        "hamile pijamaları",
        "siyah gecelik",
        "pijama takimi",
        "danteli gecelik",
        "lohusa sabahlığı",
        "AFRIKA GECELİK",
        "beyaz pyjama",
        "kırmızı elbiseyi"
    ]
    
    print("🔧 Ürün Adı Düzeltme Testi")
    print("=" * 50)
    
    for test_case in test_cases:
        corrected = corrector.correct_product_name(test_case)
        confidence = corrector.get_correction_confidence(test_case, corrected)
        
        print(f"'{test_case}' → '{corrected}' (Güven: {confidence:.2f})")

def integrate_with_current_system():
    """Mevcut sisteme entegrasyon örneği"""
    print("\n🔗 Mevcut Sisteme Entegrasyon")
    print("=" * 40)
    
    print("LLM Service'e eklenecek kod:")
    print("""
def _extract_product_name(self, message: str) -> str:
    # Önce düzeltme sistemi
    corrector = TurkishProductNameCorrector()
    corrected_message = corrector.correct_product_name(message)
    
    # Sonra mevcut extraction logic
    return self._extract_from_corrected_message(corrected_message)
""")
    
    print("\nDatabase Service'e eklenecek kod:")
    print("""
async def get_product_info(self, business_id: str, product_name: str):
    # Önce düzeltme
    corrector = TurkishProductNameCorrector()
    corrected_name = corrector.correct_product_name(product_name)
    
    # Sonra mevcut search logic
    return await self._search_with_corrected_name(corrected_name)
""")

if __name__ == "__main__":
    test_correction_system()
    integrate_with_current_system()