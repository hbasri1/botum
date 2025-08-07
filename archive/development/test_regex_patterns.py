#!/usr/bin/env python3
"""
Test regex patterns
"""

import re

def test_patterns():
    """Test regex patterns"""
    
    patterns = [
        r'\b(kısa kollu|kısa kol)\b',
        r'\b(yakası|yaka|collar|neck)\b',
        r'\b(kollu|sleeve)\b'
    ]
    
    test_text = "yakası dantelli kısa kollu"
    
    print(f"Testing text: '{test_text}'")
    print("=" * 40)
    
    for pattern in patterns:
        matches = re.findall(pattern, test_text, re.IGNORECASE)
        print(f"Pattern: {pattern}")
        print(f"Matches: {matches}")
        print()

if __name__ == "__main__":
    test_patterns()