#!/usr/bin/env python3
"""
Direct test without server
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.llm_service import LLMService
from orchestrator.services.database_service import DatabaseService
from orchestrator.services.function_execution_coordinator import FunctionExecutionCoordinator
from orchestrator.services.function_cache_manager import FunctionCacheManager

async def test_system():
    """Test the system directly"""
    print("🚀 Direct System Test...")
    print("=" * 50)
    
    # Initialize services
    llm_service = LLMService(enable_function_calling=True)
    db_service = DatabaseService()
    cache_manager = FunctionCacheManager()
    function_coordinator = FunctionExecutionCoordinator(db_service, cache_manager)
    
    test_cases = [
        {
            "question": "iade var mı acaba",
            "description": "İade sorgusu - basit"
        },
        {
            "question": "afrika gecelik fiyatı",
            "description": "Ürün fiyat sorgusu"
        },
        {
            "question": "hamile pijama var mı",
            "description": "Hamile ürün stok sorgusu"
        },
        {
            "question": "merhaba",
            "description": "Selamlama"
        },
        {
            "question": "tamam iyi günler",
            "description": "Konuşma bitirme"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Soru: '{test_case['question']}'")
        
        try:
            # Process message
            result = await llm_service.process_message_with_functions(
                prompt=test_case["question"],
                session_id="test_user",
                isletme_id="fashion_boutique"
            )
            
            if result:
                print(f"   ✅ Intent: {result.get('intent', 'unknown')}")
                print(f"   📊 Method: {result.get('method', 'unknown')}")
                print(f"   🎯 Confidence: {result.get('confidence', 0)}")
                
                # Execute function if needed
                if result.get("function_call"):
                    function_call = result["function_call"]
                    execution_result = await function_coordinator.execute_function_call(
                        function_name=function_call["name"],
                        arguments=function_call["args"],
                        session_id="test_user",
                        business_id="fashion_boutique"
                    )
                    
                    if execution_result and execution_result.get("success"):
                        response = execution_result.get("response", "İşlem tamamlandı.")
                        print(f"   💬 Response: {response[:100]}...")
                    else:
                        print(f"   ❌ Function execution failed")
                elif result.get("final_response"):
                    print(f"   💬 Response: {result['final_response']}")
                
            else:
                print(f"   ❌ No result from LLM service")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_system())