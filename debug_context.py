import requests
import json

def test_step_by_step():
    print("1. İlk soru: 'bu ürünün detayları nedir'")
    
    response1 = requests.post("http://localhost:8000/ask", 
                             json={"question": "bu ürünün detayları nedir"})
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   Cevap: {result1['answer']}")
    
    print("\n2. İkinci soru: 'afrika gecelik'")
    
    response2 = requests.post("http://localhost:8000/ask", 
                             json={"question": "afrika gecelik"})
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   Cevap: {result2['answer']}")

test_step_by_step()