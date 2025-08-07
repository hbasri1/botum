#!/usr/bin/env python3
"""
Debug hybrid intent detector
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.hybrid_intent_detector import HybridIntentDetector

async def debug_hybrid():
    """Debug hybrid intent detector"""
    detector = HybridIntentDetector()
    
    test_cases = [
        "merhaba",
        "tamam", 
        "teşekkürler",
        "iade var mı",
        "afrika gecelik",
        "fiyat sorcaktım"
    ]
    
    for test in test_cases:
        print(f"\n🧪 Test: '{test}'")
        
        # _is_product_related test
        is_product = detector._is_product_related(test)
        print(f"   Is Product Related: {is_product}")
        
        # Full detection
        result = await detector.detect_intent(test)
        print(f"   Intent: {result.get('intent', 'None')}")
        print(f"   Method: {result.get('method', 'None')}")
        print(f"   Confidence: {result.get('confidence', 0)}")

if __name__ == "__main__":
    asyncio.run(debug_hybrid())