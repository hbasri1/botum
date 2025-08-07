import requests
import json

# Kapsamlı test sorguları
test_queries = [
    # Afrika gecelik testleri
    "afrika gecelik ne kadar",
    "afrika gecelik",
    "afrika gecelik fiyat",
    
    # Diğer spesifik ürün testleri
    "kırmızı elbise",
    "hamile gecelik",
    "dantelli gecelik",
    
    # Genel sorgular
    "gecelik var mı",
    "pijama var mı",
    
    # Meta bilgi testleri
    "telefon numarası",
    "iade şartları",
    "kargo bilgisi",
    
    # Genel sohbet
    "merhaba",
    "teşekkürler"
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Sorgu: '{query}'")
    print('='*60)
    
    response = requests.post("http://localhost:8000/ask", 
                           json={"question": query})
    
    if response.status_code == 200:
        result = response.json()
        print(result["answer"])
    else:
        print(f"Hata: {response.status_code}")
        print(response.text)