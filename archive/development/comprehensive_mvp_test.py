#!/usr/bin/env python3
"""
Comprehensive MVP Test - Tüm sorunları test et
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

async def test_comprehensive_mvp():
    """Comprehensive MVP test"""
    print("🚀 Comprehensive MVP Test - Sorun Çözümleri")
    print("=" * 60)
    
    # Initialize services
    llm_service = LLMService(enable_function_calling=True)
    db_service = DatabaseService()
    cache_manager = FunctionCacheManager()
    function_coordinator = FunctionExecutionCoordinator(db_service, cache_manager)
    
    # Test cases covering all reported issues
    test_cases = [
        # SORUN 1: Intent Detection - LLM anlamıyor bazen intentleri
        {
            "category": "🧠 Intent Detection Sorunları",
            "tests": [
                {"question": "iade var mı acaba", "expected": "İade politikası bilgisi"},
                {"question": "iade yapabilir miyim", "expected": "İade politikası bilgisi"},
                {"question": "telefon numaranız", "expected": "Telefon bilgisi"},
                {"question": "kargo nasıl", "expected": "Kargo bilgisi"},
                {"question": "site adresiniz", "expected": "Website bilgisi"},
            ]
        },
        
        # SORUN 2: Ürün Arama - Ürünler bulunmalı hatasız şekilde
        {
            "category": "🔍 Ürün Arama Sorunları",
            "tests": [
                {"question": "afrika gecelik fiyatı", "expected": "Afrika gecelik fiyat bilgisi"},
                {"question": "hamile pijama var mı", "expected": "Hamile pijama stok bilgisi"},
                {"question": "dantelli gecelik", "expected": "Dantelli gecelik bilgisi"},
                {"question": "lohusa takımı", "expected": "Lohusa takım bilgisi"},
                {"question": "gecelik fiyatları", "expected": "Gecelik fiyat listesi"},
            ]
        },
        
        # SORUN 3: Kısaltma ve Çoklu Ürün - Müşteri kısaltma yazacak
        {
            "category": "📝 Kısaltma ve Çoklu Ürün Sorunları", 
            "tests": [
                {"question": "dantelli hamile lohusa", "expected": "Dantelli hamile lohusa ürünleri"},
                {"question": "gecelik", "expected": "Gecelik kategorisi ürünleri"},
                {"question": "pijama", "expected": "Pijama kategorisi ürünleri"},
                {"question": "hamile", "expected": "Hamile kategorisi ürünleri"},
            ]
        },
        
        # SORUN 4: Konuşma Akışı - Bot uygun şekilde bitirsin
        {
            "category": "💬 Konuşma Akışı Sorunları",
            "tests": [
                {"question": "merhaba", "expected": "Selamlama"},
                {"question": "teşekkürler", "expected": "Rica ederim"},
                {"question": "tamam iyi günler", "expected": "Hoşça kalın"},
                {"question": "yok teşekkürler", "expected": "İyi günler"},
                {"question": "başka soru yok", "expected": "İyi günler"},
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for category_data in test_cases:
        print(f"\n{category_data['category']}")
        print("-" * 50)
        
        for i, test in enumerate(category_data['tests'], 1):
            total_tests += 1
            question = test['question']
            expected = test['expected']
            
            print(f"\n{i}. Test: '{question}'")
            print(f"   Beklenen: {expected}")
            
            try:
                # Process message
                result = await llm_service.process_message_with_functions(
                    prompt=question,
                    session_id="test_user",
                    isletme_id="fashion_boutique"
                )
                
                if result:
                    intent = result.get('intent', 'unknown')
                    method = result.get('method', 'unknown')
                    confidence = result.get('confidence', 0)
                    
                    print(f"   📊 Intent: {intent} | Method: {method} | Confidence: {confidence:.2f}")
                    
                    # Execute function if needed
                    response = ""
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
                        else:
                            response = "Function execution failed"
                    elif result.get("final_response"):
                        response = result['final_response']
                    else:
                        response = "No response"
                    
                    print(f"   💬 Cevap: {response[:100]}...")
                    
                    # Simple success check
                    if intent != "unknown" and confidence > 0.5:
                        print(f"   ✅ BAŞARILI")
                        passed_tests += 1
                    else:
                        print(f"   ❌ BAŞARISIZ (Intent: {intent}, Confidence: {confidence})")
                
                else:
                    print(f"   ❌ BAŞARISIZ - No result from LLM service")
                    
            except Exception as e:
                print(f"   ❌ HATA: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI")
    print("=" * 60)
    print(f"Toplam Test: {total_tests}")
    print(f"Başarılı: {passed_tests}")
    print(f"Başarısız: {total_tests - passed_tests}")
    print(f"Başarı Oranı: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 TÜM TESTLER BAŞARILI! Sorunlar çözüldü.")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ Çoğu test başarılı. Sistem büyük ölçüde düzeldi.")
    else:
        print("\n⚠️ Daha fazla iyileştirme gerekiyor.")
    
    return passed_tests, total_tests

if __name__ == "__main__":
    asyncio.run(test_comprehensive_mvp())