#!/usr/bin/env python3
"""
Debug Turkish normalization
"""

import sys
import os
sys.path.append('orchestrator/services')

from turkish_language_rules import TurkishLanguageRules

def debug_turkish_normalization():
    """Debug Turkish normalization"""
    
    turkish_rules = TurkishLanguageRules()
    
    test_texts = [
        "kısa kollu",
        "yakası dantelli kısa kollu",
        "yakası dantelli",
        "dantelli yaka"
    ]
    
    print("🐛 Debugging Turkish Normalization")
    print("=" * 40)
    
    for text in test_texts:
        normalized = turkish_rules.normalize_for_search(text)
        print(f"'{text}' -> '{normalized}'")

if __name__ == "__main__":
    debug_turkish_normalization()