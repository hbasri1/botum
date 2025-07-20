import requests
import json

# Belirsiz sorgu testleri
clarify_tests = [
    "bu ürünün fiyatı nedir",
    "şunun fiyatı ne",
    "bunun rengi ne",
    "bu ne kadar",
    "şu ürün var mı",
    "onun stoğu var mı"
]

print("BELİRSİZ SORGU TESTLERİ")
print("="*50)

for query in clarify_tests:
    print(f"\nSorgu: '{query}'")
    
    response = requests.post("http://localhost:8000/ask", 
                           json={"question": query})
    
    if response.status_code == 200:
        result = response.json()
        print(f"Cevap: {result['answer']}")
    else:
        print(f"Hata: {response.status_code}")

print("\n\nKONTROL TESTLERİ (Normal sorgular)")
print("="*50)

normal_tests = [
    "afrika gecelik fiyat",
    "kırmızı elbise",
    "telefon numarası"
]

for query in normal_tests:
    print(f"\nSorgu: '{query}'")
    
    response = requests.post("http://localhost:8000/ask", 
                           json={"question": query})
    
    if response.status_code == 200:
        result = response.json()
        print(f"Cevap: {result['answer']}")
    else:
        print(f"Hata: {response.status_code}")