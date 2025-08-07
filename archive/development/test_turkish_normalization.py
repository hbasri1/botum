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

# GENEL ÇÖZÜM TESTLERİ - Türkçe ekleri
turkish_tests = [
    # Türkçe ek testleri
    "afrika geceliği",           # geceliği → gecelik
    "afrika geceliğin fiyatı",   # geceliğin → gecelik  
    "hamile geceliğinin rengi",  # geceliğinin → gecelik
    "kırmızı elbisenin fiyatı",  # elbisenin → elbise
    "pijamının stoğu",           # pijamının → pijama
    "dantelli gecelikler",       # gecelikler → gecelik
    
    # Mevcut çalışan sistemler (bozulmamalı)
    "afrika gecelik ne kadar",   # Zaten çalışıyor
    "bu ürünün fiyatı nedir",    # Clarify olmalı
    "telefon numarası",          # Meta bilgi
    "merhaba",                   # Greeting
]

print("🧠 GENEL ÇÖZÜM TESTLERİ - Türkçe Normalizasyon")
print("=" * 60)

for i, question in enumerate(turkish_tests, 1):
    print(f"\n{i}. SORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    
    # Kısa cevap için truncate
    if len(answer) > 200:
        print(f"[Kısaltıldı - Toplam {len(answer)} karakter]")
    
    print("-" * 60)