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

# GERÇEK ÜRÜN VERİLERİ TESTİ
real_product_tests = [
    # Ana sorunlar
    "afrika gecelik",           # Afrika Etnik Gecelik bulmalı
    "kırmızı elbise",          # Bordo elbise önerisi vermeli
    "mavi elbise",             # Lacivert elbise önerisi vermeli
    
    # Diğer testler
    "hamile geceliği",         # Hamile gecelik bulmalı
    "afrika gecelik var mı",   # Var, mevcut demeli
    "bordo elbise",            # Bordo elbise bulmalı
    "lacivert elbise",         # Lacivert elbise bulmalı
]

print("🎯 GERÇEK ÜRÜN VERİLERİ TESTİ")
print("=" * 50)

for question in real_product_tests:
    print(f"\nSORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    print("-" * 40)