#!/usr/bin/env python3
"""
Test server API with hybrid system
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test API endpoints"""
    print("🌐 Server API Test - Hibrit Sistem")
    print("=" * 50)
    
    test_cases = [
        {"question": "merhaba", "description": "Selamlama"},
        {"question": "iade var mı acaba", "description": "İade sorgusu"},
        {"question": "afrika gecelik fiyatı", "description": "Ürün fiyat sorgusu"},
        {"question": "hamile pijama var mı", "description": "Hamile ürün sorgusu"},
        {"question": "çok memnun kaldım", "description": "Övgü (LLM gerekli)"},
        {"question": "tamam iyi günler", "description": "Vedalaşma"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Soru: '{test_case['question']}'")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/ask",
                json={"question": test_case["question"]},
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Cevap: {data['answer'][:100]}...")
                print(f"   📊 Method: {data.get('method', 'unknown')}")
                print(f"   🎯 Confidence: {data.get('confidence', 0):.2f}")
                print(f"   ⏱️ Response Time: {response_time:.0f}ms")
                print(f"   🔧 Server Time: {data.get('execution_time_ms', 0)}ms")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Server bağlantı hatası")
            break
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n🎉 API Test tamamlandı!")

if __name__ == "__main__":
    test_api()