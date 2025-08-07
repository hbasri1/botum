#!/usr/bin/env python3
import requests
import json

def test_query(question):
    response = requests.post("http://localhost:8003/ask", 
                           json={"question": question, "business_id": "fashion_boutique"})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {question} -> {result['method']} | {result['answer'][:100]}...")
    else:
        print(f"❌ {question} -> ERROR")

# Önceden başarısız olan testler
failing_tests = [
    "afrika gecelik",
    "afrika geceliği", 
    "hamile gecelik",
    "hamile geceliği",
    "hamile pijama",
    "pijama",
    "pijama takımı",
    "gecelik",
    "siyah gecelik",
    "beyaz pijama"
]

print("🧪 Hızlı Test - Önceden Başarısız Olan Sorgular:")
for test in failing_tests:
    test_query(test)