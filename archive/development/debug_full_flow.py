#!/usr/bin/env python3
"""
Debug full flow
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.llm_service import LLMService

async def debug_full_flow():
    """Debug full flow"""
    llm_service = LLMService(enable_function_calling=True)
    
    test_cases = ["merhaba", "tamam", "iade var mı", "afrika gecelik"]
    
    for test in test_cases:
        print(f"\n🧪 Test: '{test}'")
        
        result = await llm_service.process_message_with_functions(
            prompt=test,
            session_id="test",
            isletme_id="test"
        )
        
        if result:
            print(f"   Intent: {result.get('intent', 'None')}")
            print(f"   Method: {result.get('method', 'None')}")
            print(f"   Confidence: {result.get('confidence', 0)}")
            print(f"   Response: {result.get('final_response', 'None')[:50]}...")
        else:
            print(f"   ❌ No result")

if __name__ == "__main__":
    asyncio.run(debug_full_flow())