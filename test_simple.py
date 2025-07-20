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

# Basit kelime testleri
tests = [
    "hey",
    "teşekkürler", 
    "sağol",
    "tamam"
]

print("🧪 BASİT KELİME TESTLERİ")
print("=" * 30)

for question in tests:
    print(f"\nSORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    print("-" * 20)