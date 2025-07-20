import requests
import json

# Doğal dil testleri
natural_tests = [
    "tamam",
    "tamamdır", 
    "teşekkürler",
    "sağol",
    "bu ürünün fiyatı nedir",
    "afrika gecelik ne kadar",
    "telefon numarası nedir"
]

print("DOĞAL DİL TESTLERİ")
print("="*50)

for query in natural_tests:
    print(f"\nSorgu: '{query}'")
    
    response = requests.post("http://localhost:8000/ask", 
                           json={"question": query})
    
    if response.status_code == 200:
        result = response.json()
        print(f"Cevap: {result['answer']}")
    else:
        print(f"Hata: {response.status_code}")
        print(response.text)