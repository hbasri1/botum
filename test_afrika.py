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

# Afrika gecelik testleri
tests = [
    "afrika geceliği",
    "afrika geceliğin fiyatı",
    "afrika gecelik ne kadar"
]

print("🧪 AFRİKA GECELİK TESTLERİ")
print("=" * 40)

for question in tests:
    print(f"\nSORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    print("-" * 30)