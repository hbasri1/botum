#!/usr/bin/env python3
"""
Debug Simple Intent System
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.services.simple_intent_system import simple_intent_system

async def debug_simple_intent():
    """Debug simple intent system"""
    
    test_cases = [
        "fiyat soracaktım",
        "merhaba fiyat soracaktım", 
        "çiçek desenli takım",
        "amk"
    ]
    
    for test in test_cases:
        print(f"\n🔍 Test: '{test}'")
        result = await simple_intent_system.detect_intent(test)
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(debug_simple_intent())