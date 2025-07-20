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

# SÜPER AKILLI SİSTEM TESTİ
tests = [
    "selamlar fiyat soracaktım",      # Ana sorun
    "afrika geceliği ne kadar",       # Türkçe ek
    "telefon numarası",               # Meta bilgi
    "merhaba",                        # Selamlama
    "bu ürünün fiyatı nedir",         # Belirsiz
    "teşekkürler"                     # Teşekkür
]

print("🚀 SÜPER AKILLI SİSTEM TESTİ")
print("=" * 50)

for i, question in enumerate(tests, 1):
    print(f"\n{i}. SORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    print("-" * 30)