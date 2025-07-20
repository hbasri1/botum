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

# TÜRKÇE GÜNLÜK DİL TESTİ
turkish_tests = [
    "sağolasın",        # Günlük teşekkür
    "eyvallah",         # Günlük teşekkür
    "tamamdır",         # Günlük onay
    "olur",             # Günlük onay
    "iyi",              # Günlük onay
    "neyse",            # Günlük
    "peki",             # Günlük onay
    "tamam işte",       # Günlük onay
    "sağol canım",      # Günlük teşekkür
]

print("🇹🇷 TÜRKÇE GÜNLÜK DİL TESTİ")
print("=" * 40)

for question in turkish_tests:
    print(f"\nSORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    print("-" * 25)