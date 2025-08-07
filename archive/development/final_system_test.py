#!/usr/bin/env python3
"""
Final System Test - Basit sistem
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_final_system():
    """Final sistem testi"""
    print("🚀 FINAL SYSTEM TEST - Basit ve Etkili Sistem")
    print("=" * 60)
    
    test_cases = [
        # Problemli durumlar - artık düzgün çalışmalı
        {"question": "tamam", "expected": "acknowledgment", "description": "Basit onay"},
        {"question": "fiyat sorcaktım", "expected": "clarification_needed", "description": "Anlamsız sorgu"},
        {"question": "annen var mı", "expected": "clarification_needed", "description": "Saçma sorgu"},
        
        # Normal durumlar
        {"question": "merhaba", "expected": "greeting", "description": "Selamlama"},
        {"question": "teşekkürler", "expected": "thanks", "description": "Teşekkür"},
        {"question": "iade var mı", "expected": "business_info", "description": "İşletme bilgisi"},
        {"question": "afrika gecelik fiyatı", "expected": "product_inquiry", "description": "Ürün sorgusu"},
        
        # Edge cases
        {"question": "", "expected": "clarification_needed", "description": "Boş mesaj"},
        {"question": "asdfgh", "expected": "clarification_needed", "description": "Anlamsız"},
    ]
    
    print(f"\n🧪 {len(test_cases)} test çalıştırılıyor...\n")
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        question = test["question"]
        expected = test["expected"]
        description = test["description"]
        
        print(f"{i}. {description}")
        print(f"   Soru: '{question}'")
        
        try:
            response = requests.post(
                f"{BASE_URL}/ask",
                json={"question": question},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                intent = data.get("intent", "unknown")
                method = data.get("method", "unknown")
                confidence = data.get("confidence", 0)
                answer = data.get("answer", "")
                
                print(f"   📊 Intent: {intent}")
                print(f"   🔧 Method: {method}")
                print(f"   🎯 Confidence: {confidence:.2f}")
                print(f"   💬 Cevap: {answer[:60]}...")
                
                if intent == expected:
                    print(f"   ✅ BAŞARILI")
                    passed += 1
                else:
                    print(f"   ❌ BAŞARISIZ (Beklenen: {expected}, Gelen: {intent})")
                    failed += 1
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed += 1
        
        print()
    
    # Özet
    total = passed + failed
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print("=" * 60)
    print("📊 FINAL TEST SONUÇLARI")
    print("=" * 60)
    print(f"Toplam Test: {total}")
    print(f"Başarılı: {passed}")
    print(f"Başarısız: {failed}")
    print(f"Başarı Oranı: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"\n🎉 SİSTEM MÜKEMMEL! Production-ready.")
    elif success_rate >= 80:
        print(f"\n✅ Sistem iyi çalışıyor.")
    else:
        print(f"\n⚠️ Daha fazla iyileştirme gerekli.")
    
    # Maliyet analizi
    try:
        stats_response = requests.get(f"{BASE_URL}/admin/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            daily_stats = stats["daily_stats"]
            
            print(f"\n💰 MALİYET ANALİZİ:")
            print(f"Pattern Queries: {daily_stats['pattern_queries']} ({daily_stats['pattern_percentage']:.1f}%)")
            print(f"LLM Queries: {daily_stats['llm_queries']} ({daily_stats['llm_percentage']:.1f}%)")
            print(f"Günlük Maliyet: ${daily_stats['total_cost_usd']:.6f}")
            print(f"Efficiency Score: {daily_stats['efficiency_score']:.1f}%")
    except:
        pass

if __name__ == "__main__":
    test_final_system()