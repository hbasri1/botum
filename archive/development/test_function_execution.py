#!/usr/bin/env python3
"""
Test function execution directly
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.database_service import DatabaseService
from orchestrator.services.function_execution_coordinator import FunctionExecutionCoordinator
from orchestrator.services.function_cache_manager import FunctionCacheManager

async def test_functions():
    """Test function execution directly"""
    print("🔧 Testing Function Execution...")
    print("=" * 50)
    
    # Initialize services
    db_service = DatabaseService()
    cache_manager = FunctionCacheManager()
    function_coordinator = FunctionExecutionCoordinator(db_service, cache_manager)
    
    test_cases = [
        {
            "function_name": "getGeneralInfo",
            "args": {"info_type": "iade"},
            "description": "İade bilgisi"
        },
        {
            "function_name": "getGeneralInfo", 
            "args": {"info_type": "telefon"},
            "description": "Telefon bilgisi"
        },
        {
            "function_name": "getProductInfo",
            "args": {"product_name": "afrika gecelik", "query_type": "fiyat"},
            "description": "Ürün fiyat sorgusu"
        },
        {
            "function_name": "getProductInfo",
            "args": {"product_name": "hamile pijama", "query_type": "stok"},
            "description": "Hamile ürün stok sorgusu"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Function: {test_case['function_name']}")
        print(f"   Args: {test_case['args']}")
        
        try:
            result = await function_coordinator.execute_function_call(
                function_name=test_case["function_name"],
                arguments=test_case["args"],
                session_id="test_user",
                business_id="fashion_boutique"
            )
            
            if result and result.get("success"):
                print(f"   ✅ Success: {result.get('success')}")
                print(f"   💬 Response: {result.get('response', 'No response')}")
                print(f"   ⏱️ Time: {result.get('execution_time_ms', 0)}ms")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error') if result else 'No result'}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_functions())