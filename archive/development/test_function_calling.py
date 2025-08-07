#!/usr/bin/env python3
"""
Function Calling Test Script
Gemini Function Calling entegrasyonunu test eder
"""

import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.append('orchestrator')

from orchestrator.services.llm_service import LLMService
from orchestrator.services.function_cache_manager import FunctionCacheManager
from orchestrator.services.database_service import DatabaseService
from orchestrator.services.function_execution_coordinator import FunctionExecutionCoordinator
from orchestrator.services.input_validation_service import InputValidationService
from orchestrator.services.access_control_service import AccessControlService

async def test_basic_function_calling():
    """Temel function calling testi"""
    print("🚀 Testing Basic Function Calling...")
    
    try:
        # LLM Service'i başlat
        llm_service = LLMService(enable_function_calling=True)
        
        # Test mesajları
        test_messages = [
            "gecelik fiyatı ne kadar?",
            "pijama stok durumu nedir?",
            "telefon numaranız nedir?",
            "iade koşulları nelerdir?"
        ]
        
        for message in test_messages:
            print(f"\n📝 Test Message: {message}")
            
            try:
                result = await llm_service.process_message_with_functions(
                    prompt=message,
                    session_id="test_session",
                    isletme_id="test_business"
                )
                
                if result:
                    print(f"✅ Success: {json.dumps(result, indent=2, ensure_ascii=False)}")
                else:
                    print("❌ No result returned")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n✅ Basic Function Calling Test Completed")
        
    except Exception as e:
        print(f"❌ Basic Function Calling Test Failed: {str(e)}")

async def test_cache_functionality():
    """Cache functionality testi"""
    print("\n🗄️ Testing Cache Functionality...")
    
    try:
        # Cache manager'ı başlat
        cache_manager = FunctionCacheManager()
        
        # Test cache operations
        function_name = "getProductInfo"
        arguments = {"product_name": "gecelik", "query_type": "fiyat"}
        business_id = "test_business"
        test_result = {"success": True, "result": "Gecelik fiyatı 150 TL"}
        
        # Test set
        print("📝 Testing cache set...")
        success = await cache_manager.set(function_name, arguments, business_id, test_result)
        print(f"Cache set result: {success}")
        
        # Test get
        print("📝 Testing cache get...")
        cached_result = await cache_manager.get(function_name, arguments, business_id)
        print(f"Cache get result: {cached_result}")
        
        # Test invalidation
        print("📝 Testing cache invalidation...")
        deleted_count = await cache_manager.invalidate(business_id=business_id)
        print(f"Cache invalidation result: {deleted_count} entries deleted")
        
        print("✅ Cache Functionality Test Completed")
        
    except Exception as e:
        print(f"❌ Cache Functionality Test Failed: {str(e)}")

async def test_input_validation():
    """Input validation testi"""
    print("\n🔒 Testing Input Validation...")
    
    try:
        validation_service = InputValidationService()
        
        # Valid input test
        print("📝 Testing valid input...")
        result = await validation_service.validate_function_call(
            "getProductInfo",
            {"product_name": "gecelik", "query_type": "fiyat"},
            "test_session",
            "test_business"
        )
        print(f"Valid input result: {result['valid']}")
        
        # Invalid function test
        print("📝 Testing invalid function...")
        result = await validation_service.validate_function_call(
            "invalidFunction",
            {"test": "value"},
            "test_session",
            "test_business"
        )
        print(f"Invalid function result: {result['valid']}")
        
        # SQL injection test
        print("📝 Testing SQL injection prevention...")
        result = await validation_service.validate_function_call(
            "getProductInfo",
            {"product_name": "test'; DROP TABLE products; --", "query_type": "fiyat"},
            "test_session",
            "test_business"
        )
        print(f"SQL injection prevention result: {result['valid']}")
        
        print("✅ Input Validation Test Completed")
        
    except Exception as e:
        print(f"❌ Input Validation Test Failed: {str(e)}")

async def test_access_control():
    """Access control testi"""
    print("\n🛡️ Testing Access Control...")
    
    try:
        access_control = AccessControlService()
        
        # Basic access test
        print("📝 Testing basic access...")
        result = await access_control.check_access(
            "test_business", "test_session", "getProductInfo"
        )
        print(f"Basic access result: {result['allowed']}")
        
        # Rate limiting test
        print("📝 Testing rate limiting...")
        for i in range(35):  # Exceed basic limit
            await access_control.check_access(
                "test_business", "test_session", "getProductInfo"
            )
        
        result = await access_control.check_access(
            "test_business", "test_session", "getProductInfo"
        )
        print(f"Rate limiting result: {result['allowed']} (should be False)")
        
        print("✅ Access Control Test Completed")
        
    except Exception as e:
        print(f"❌ Access Control Test Failed: {str(e)}")

async def test_fallback_mechanism():
    """Fallback mechanism testi"""
    print("\n🔄 Testing Fallback Mechanism...")
    
    try:
        llm_service = LLMService(enable_function_calling=True)
        
        # Force fallback by disabling function calling
        llm_service.enable_function_calling = False
        
        result = await llm_service.process_message_with_functions(
            prompt="gecelik fiyatı ne kadar?",
            session_id="test_session",
            isletme_id="test_business"
        )
        
        if result:
            print(f"✅ Fallback successful: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("❌ Fallback failed")
        
        print("✅ Fallback Mechanism Test Completed")
        
    except Exception as e:
        print(f"❌ Fallback Mechanism Test Failed: {str(e)}")

async def main():
    """Ana test fonksiyonu"""
    print("🧪 Gemini Function Calling Integration Tests")
    print("=" * 50)
    
    # Run all tests
    await test_basic_function_calling()
    await test_cache_functionality()
    await test_input_validation()
    await test_access_control()
    await test_fallback_mechanism()
    
    print("\n" + "=" * 50)
    print("🎉 All Tests Completed!")
    print("\n📋 Next Steps:")
    print("1. Set up Redis for caching")
    print("2. Set up PostgreSQL database")
    print("3. Configure Gemini API key")
    print("4. Run database migrations")
    print("5. Start the application with: python orchestrator/app/main.py")

if __name__ == "__main__":
    asyncio.run(main())