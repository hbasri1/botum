#!/usr/bin/env python3
"""
Test hybrid intent detection system
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.hybrid_intent_detector import HybridIntentDetector

async def test_hybrid_system():
    """Test hybrid intent detection"""
    print("🚀 Hibrit Intent Detection Sistemi Testi")
    print("=" * 60)
    
    detector = HybridIntentDetector()
    
    test_cases = [
        # Kesin pattern'ler - LLM'e gerek yok
        {
            "category": "🎯 Kesin Pattern'ler (LLM'siz)",
            "tests": [
                {"message": "merhaba", "expected_method": "certain_pattern"},
                {"message": "teşekkürler", "expected_method": "certain_pattern"},
                {"message": "hoşça kal", "expected_method": "certain_pattern"},
                {"message": "iade var mı", "expected_method": "business_pattern"},
                {"message": "telefon numaranız", "expected_method": "business_pattern"},
            ]
        },
        
        # Ürün sorguları - Intelligent search
        {
            "category": "🔍 Ürün Sorguları (Intelligent Search)",
            "tests": [
                {"message": "afrika gecelik fiyatı", "expected_method": "pattern_detection"},
                {"message": "hamile pijama var mı", "expected_method": "pattern_detection"},
                {"message": "gecelik", "expected_method": "pattern_detection"},
                {"message": "dantelli", "expected_method": "pattern_detection"},
            ]
        },
        
        # Karmaşık durumlar - LLM gerekli
        {
            "category": "🧠 Karmaşık Durumlar (LLM)",
            "tests": [
                {"message": "çok memnun kaldım harika", "expected_method": "llm_heuristic"},
                {"message": "sorun var berbat", "expected_method": "llm_heuristic"},
                {"message": "anlamadım karışık", "expected_method": "llm_heuristic"},
                {"message": "nasıl sipariş vereceğim", "expected_method": "llm_heuristic"},
            ]
        }
    ]
    
    total_tests = 0
    pattern_tests = 0
    llm_tests = 0
    
    for category_data in test_cases:
        print(f"\n{category_data['category']}")
        print("-" * 50)
        
        for i, test in enumerate(category_data['tests'], 1):
            total_tests += 1
            message = test['message']
            expected_method = test['expected_method']
            
            print(f"\n{i}. Test: '{message}'")
            
            try:
                # Intent detection
                result = await detector.detect_intent(message)
                
                if result:
                    intent = result.get('intent', 'unknown')
                    confidence = result.get('confidence', 0)
                    method = result.get('method', 'unknown')
                    
                    print(f"   📊 Intent: {intent}")
                    print(f"   🎯 Confidence: {confidence:.2f}")
                    print(f"   🔧 Method: {method}")
                    
                    # LLM kullanım kontrolü
                    should_use_llm = detector.should_use_llm(message)
                    print(f"   🧠 LLM Gerekli: {'Evet' if should_use_llm else 'Hayır'}")
                    
                    # Response strategy
                    strategy = await detector.get_response_strategy(result)
                    strategy_type = "direct" if strategy["use_direct_response"] else \
                                  "function" if strategy["use_function_call"] else \
                                  "search" if strategy["use_intelligent_search"] else \
                                  "human" if strategy["use_human_transfer"] else "unknown"
                    print(f"   📋 Strategy: {strategy_type}")
                    
                    # Method tracking
                    if method in ["certain_pattern", "business_pattern", "pattern_detection"]:
                        pattern_tests += 1
                        print(f"   ✅ Pattern-based (Hızlı)")
                    else:
                        llm_tests += 1
                        print(f"   🧠 LLM-based (Akıllı)")
                    
                else:
                    print(f"   ❌ No result")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 HİBRİT SİSTEM ANALİZİ")
    print("=" * 60)
    print(f"Toplam Test: {total_tests}")
    print(f"Pattern-based (Hızlı): {pattern_tests} ({(pattern_tests/total_tests)*100:.1f}%)")
    print(f"LLM-based (Akıllı): {llm_tests} ({(llm_tests/total_tests)*100:.1f}%)")
    
    print(f"\n🎯 AVANTAJLAR:")
    print(f"• %{(pattern_tests/total_tests)*100:.0f} sorgu hızlı pattern matching ile çözülüyor")
    print(f"• %{(llm_tests/total_tests)*100:.0f} karmaşık sorgu LLM zekası ile çözülüyor")
    print(f"• Maliyet optimizasyonu: LLM sadece gerektiğinde kullanılıyor")
    print(f"• Esneklik: Yeni durumlar LLM ile handle ediliyor")

if __name__ == "__main__":
    asyncio.run(test_hybrid_system())