#!/usr/bin/env python3
"""
Debug LLM service
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.llm_service import LLMService

async def debug_llm():
    """Debug LLM service"""
    
    llm_service = LLMService(enable_function_calling=True)
    
    test_cases = ["fiyat", "tamam", "afrika gecelik fiyatı"]
    
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
            print(f"   Final Response: {result.get('final_response', 'None')[:50]}...")
        else:
            print(f"   ❌ No result")

if __name__ == "__main__":
    asyncio.run(debug_llm())