import requests

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

# SORUNLU DURUMLAR TESTİ
problem_tests = [
    "afrika gecelik var mı",     # 2 ürün gösteriyor → "Evet var" demeli
    "hmm sağol",                 # Bulunamadı → Teşekkür olmalı
    "sağol",                     # Teşekkür testi
    "afrika geceliği",           # Normal ürün testi
]

print("🔧 SORUN ÇÖZME TESTİ")
print("=" * 40)

for question in problem_tests:
    print(f"\nSORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    print("-" * 30)