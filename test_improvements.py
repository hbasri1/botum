import requests
import json

# Meta bilgi testleri
meta_tests = [
    "telefon numarası",
    "telefon",
    "iade şartları", 
    "iade",
    "kargo bilgisi",
    "kargo"
]

print("META BİLGİ TESTLERİ")
print("="*50)

for query in meta_tests:
    print(f"\nSorgu: '{query}'")
    
    response = requests.post("http://localhost:8000/ask", 
                           json={"question": query})
    
    if response.status_code == 200:
        result = response.json()
        print(f"Cevap: {result['answer']}")
    else:
        print(f"Hata: {response.status_code}")

print("\n\nAFRIKA GECELİK TESTLERİ")
print("="*50)

afrika_tests = [
    "afrika gecelik",
    "afrika gecelik ne kadar",
    "afrika gecelik fiyat",
    "afrika gecelik var mı"
]

for query in afrika_tests:
    print(f"\nSorgu: '{query}'")
    
    response = requests.post("http://localhost:8000/ask", 
                           json={"question": query})
    
    if response.status_code == 200:
        result = response.json()
        print(f"Cevap: {result['answer']}")
    else:
        print(f"Hata: {response.status_code}")