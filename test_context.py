import requests
import json

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

print("🧠 CONTEXT MEMORY TESTİ")
print("=" * 50)

# Test senaryosu: Kullanıcı önce belirsiz soru soruyor, sonra ürün ismi veriyor
test_scenarios = [
    {
        "name": "İçerik Sorgusu",
        "questions": [
            "ürün içeriği öğrenebilir miyim",  # Clarify bekleniyor
            "afrika gecelik"                   # Context'e göre detay göstermeli
        ]
    },
    {
        "name": "Detay Sorgusu", 
        "questions": [
            "bu ürünün detayları nedir",      # Clarify bekleniyor
            "hamile gecelik"                  # Context'e göre detay göstermeli
        ]
    },
    {
        "name": "Normal Fiyat Sorgusu",
        "questions": [
            "bu ürünün fiyatı nedir",         # Clarify bekleniyor
            "afrika gecelik"                  # Normal fiyat göstermeli (context yok)
        ]
    }
]

for scenario in test_scenarios:
    print(f"\n📋 {scenario['name']}")
    print("-" * 30)
    
    for i, question in enumerate(scenario['questions'], 1):
        print(f"{i}. SORU: {question}")
        answer = test_bot(question)
        print(f"   CEVAP: {answer}")
        print()
    
    print("=" * 50)