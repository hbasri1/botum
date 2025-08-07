#!/usr/bin/env python3
"""
Gemini 2.0 Flash Lite Test - Anlama Kapasitesi
"""

import requests
import json

def test_understanding():
    """Bot'un anlama kapasitesini test et"""
    
    test_cases = [
        # Önceden başarısız olan case'ler
        ("afrika gecelik", "function_calling"),
        ("afrika geceliği", "function_calling"), 
        ("hamile gecelik", "function_calling"),
        ("hangi ürünler var", "function_calling"),
        ("stokta ne var", "function_calling"),
        
        # Yeni test case'ler
        ("kırmızı gecelik var mı", "function_calling"),
        ("siyah pijama takımı", "function_calling"),
        ("dantelli ürünler", "function_calling"),
        ("hamile için ne var", "function_calling"),
        ("en ucuz gecelik", "function_calling"),
        
        # Genel bilgi
        ("telefon numaranız", "function_calling"),
        ("iade nasıl yapılır", "function_calling"),
        ("merhaba", "direct_response")
    ]
    
    print("🧪 Gemini 2.0 Flash Lite Anlama Testi")
    print("=" * 50)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, (question, expected_method) in enumerate(test_cases, 1):
        try:
            response = requests.post(
                "http://localhost:8003/ask",
                json={"question": question, "business_id": "fashion_boutique"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                method = result.get("method", "unknown")
                answer = result.get("answer", "")
                confidence = result.get("confidence", 0)
                
                # Başarı kontrolü
                success = method == expected_method and "anlayamadım" not in answer.lower()
                
                if success:
                    success_count += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                print(f"{i:2d}. {status} | {question}")
                print(f"    Method: {method} (expected: {expected_method})")
                print(f"    Confidence: {confidence:.2f}")
                print(f"    Answer: {answer[:80]}...")
                print()
                
            else:
                print(f"{i:2d}. ❌ HTTP ERROR | {question} -> {response.status_code}")
                
        except Exception as e:
            print(f"{i:2d}. ❌ EXCEPTION | {question} -> {str(e)}")
    
    # Sonuçlar
    success_rate = (success_count / total_count) * 100
    print("📊 Test Sonuçları:")
    print(f"   • Toplam Test: {total_count}")
    print(f"   • Başarılı: {success_count}")
    print(f"   • Başarısız: {total_count - success_count}")
    print(f"   • Başarı Oranı: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 Mükemmel! Sistem %90+ accuracy'ye ulaştı!")
    elif success_rate >= 80:
        print("👍 İyi! Sistem %80+ accuracy'de, semantic search ile %90+'a çıkacak")
    else:
        print("⚠️ Daha fazla iyileştirme gerekli")

if __name__ == "__main__":
    test_understanding()