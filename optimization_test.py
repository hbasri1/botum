#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_bot(question):
    try:
        response = requests.post(
            "http://localhost:8000/ask",
            json={"question": question},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("answer", "Cevap alınamadı")
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def test_dialog(dialog_name, questions, expected_behaviors):
    """Diyalog testi - sıralı sorular"""
    print(f"\n🎭 {dialog_name}")
    print("=" * 60)
    
    results = []
    for i, (question, expected) in enumerate(zip(questions, expected_behaviors), 1):
        print(f"\n{i}. SORU: {question}")
        print(f"   BEKLENTİ: {expected}")
        
        answer = test_bot(question)
        print(f"   CEVAP: {answer[:100]}..." if len(answer) > 100 else f"   CEVAP: {answer}")
        
        # Basit beklenti kontrolü
        success = False
        if "fiyat" in expected.lower() and ("TL" in answer or "fiyat" in answer.lower()):
            success = True
        elif "hangi ürün" in expected.lower() and "hangi ürün" in answer.lower():
            success = True
        elif "telefon" in expected.lower() and "0555" in answer:
            success = True
        elif "merhaba" in expected.lower() and ("merhaba" in answer.lower() or "hoş geldin" in answer.lower()):
            success = True
        elif "ürün" in expected.lower() and "ürün" in answer.lower():
            success = True
        
        status = "✅ BAŞARILI" if success else "❌ BAŞARISIZ"
        print(f"   DURUM: {status}")
        
        results.append({
            "question": question,
            "expected": expected,
            "answer": answer,
            "success": success
        })
        
        time.sleep(0.5)  # Rate limiting
    
    # Özet
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    print(f"\n📊 ÖZET: {success_count}/{total_count} başarılı ({success_count/total_count*100:.1f}%)")
    
    return results

# TEST SENARYOLARI
test_scenarios = [
    {
        "name": "TÜRKÇE EK TEMİZLEME",
        "questions": [
            "afrika geceliği",
            "afrika geceliğin fiyatı", 
            "hamile geceliğinin rengi",
            "pijamının stoğu"
        ],
        "expected": [
            "Afrika gecelik fiyat göster",
            "Afrika gecelik fiyat göster",
            "Hamile gecelik renk göster", 
            "Pijama stok göster"
        ]
    },
    
    {
        "name": "CONTEXT MEMORY",
        "questions": [
            "ürün içeriği öğrenebilir miyim",
            "afrika gecelik"
        ],
        "expected": [
            "Hangi ürün sorusu",
            "Afrika gecelik detay göster"
        ]
    },
    
    {
        "name": "BELİRSİZ SORGU YÖNETİMİ", 
        "questions": [
            "bu ürünün fiyatı nedir",
            "şunun rengi ne",
            "bunun stoğu var mı"
        ],
        "expected": [
            "Hangi ürün sorusu",
            "Hangi ürün sorusu", 
            "Hangi ürün sorusu"
        ]
    },
    
    {
        "name": "META BİLGİ SİSTEMİ",
        "questions": [
            "telefon numarası",
            "iade şartları",
            "kargo bilgisi"
        ],
        "expected": [
            "Telefon numarası göster",
            "İade bilgisi göster",
            "Kargo bilgisi göster"
        ]
    },
    
    {
        "name": "ÜRÜN ARAMA SİSTEMİ",
        "questions": [
            "afrika gecelik ne kadar",
            "kırmızı elbise",
            "hamile gecelik var mı"
        ],
        "expected": [
            "Afrika gecelik fiyat göster",
            "Kırmızı elbise ürün listesi",
            "Hamile gecelik ürün listesi"
        ]
    },
    
    {
        "name": "GENEL SOHBET",
        "questions": [
            "merhaba",
            "teşekkürler", 
            "tamam"
        ],
        "expected": [
            "Merhaba karşılığı",
            "Rica ederim karşılığı",
            "Rica ederim karşılığı"
        ]
    }
]

print("🔬 KAPSAMLI SİSTEM TESTİ")
print("=" * 80)

all_results = []
for scenario in test_scenarios:
    results = test_dialog(
        scenario["name"], 
        scenario["questions"], 
        scenario["expected"]
    )
    all_results.extend(results)

# GENEL ÖZET
print("\n" + "="*80)
print("📈 GENEL ÖZET")
print("="*80)

total_success = sum(1 for r in all_results if r["success"])
total_tests = len(all_results)
success_rate = total_success/total_tests*100

print(f"Toplam Test: {total_tests}")
print(f"Başarılı: {total_success}")
print(f"Başarısız: {total_tests - total_success}")
print(f"Başarı Oranı: {success_rate:.1f}%")

# BAŞARISIZ TESTLER
failed_tests = [r for r in all_results if not r["success"]]
if failed_tests:
    print(f"\n❌ BAŞARISIZ TESTLER ({len(failed_tests)} adet):")
    print("-" * 50)
    for i, test in enumerate(failed_tests, 1):
        print(f"{i}. SORU: {test['question']}")
        print(f"   BEKLENTİ: {test['expected']}")
        print(f"   CEVAP: {test['answer'][:80]}...")
        print()

print("\n🎯 TEST TAMAMLANDI!")