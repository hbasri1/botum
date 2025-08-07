#!/usr/bin/env python3
"""
Debug simple system
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.simple_intent_system import simple_intent_system

async def debug_simple():
    """Debug simple system"""
    
    test_cases = ["fiyat", "tamam", "afrika gecelik fiyatı", "fiyat soracaktım ama"]
    
    for test in test_cases:
        print(f"\n🧪 Test: '{test}'")
        
        result = await simple_intent_system.detect_intent(test)
        print(f"   Intent: {result.get('intent', 'None')}")
        print(f"   Method: {result.get('method', 'None')}")
        print(f"   Confidence: {result.get('confidence', 0)}")
        print(f"   Response: {result.get('response', 'None')}")
        print(f"   Use Search: {result.get('use_intelligent_search', False)}")

if __name__ == "__main__":
    asyncio.run(debug_simple())