#!/usr/bin/env python3
"""
Debug strategy
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.hybrid_intent_detector import HybridIntentDetector

async def debug_strategy():
    """Debug strategy"""
    detector = HybridIntentDetector()
    
    test = "tamam"
    print(f"🧪 Test: '{test}'")
    
    # Intent detection
    intent_result = await detector.detect_intent(test)
    print(f"Intent Result: {intent_result}")
    
    # Strategy
    strategy = await detector.get_response_strategy(intent_result)
    print(f"Strategy: {strategy}")

if __name__ == "__main__":
    asyncio.run(debug_strategy())