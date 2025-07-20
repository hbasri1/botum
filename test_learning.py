import requests
import time
import json

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

# Öğrenme sistemini test et - başarısız sorgular yapalım
print("🧠 AKILLI ÖĞRENME SİSTEMİ TESTİ")
print("=" * 50)

# Başarısız sorgular (sistem bunları öğrenecek)
failed_tests = [
    "bye",           # Bilinmeyen
    "görüşürüz",     # Bilinmeyen  
    "hoşçakal",      # Bilinmeyen
    "naber",         # Greeting olmalı ama belki başarısız
    "nasılsın"       # Greeting olmalı ama belki başarısız
]

print("❌ BAŞARISIZ SORGULAR (Sistem öğrenecek):")
for question in failed_tests:
    print(f"SORU: {question}")
    answer = test_bot(question)
    print(f"CEVAP: {answer}")
    print("-" * 30)
    time.sleep(1)

print("\n⏰ 1 dakika bekleyin, sistem öğrenecek...")
print("📁 Dosyaları kontrol edin:")
print("   - learning_stats.json")
print("   - prompt_improvements.txt") 
print("   - chatbot_logs.log")

# 1 dakika bekle
time.sleep(65)

print("\n📊 ÖĞRENME İSTATİSTİKLERİ:")
try:
    with open("learning_stats.json", "r", encoding="utf-8") as f:
        stats = json.load(f)
    print(f"Toplam sorgu: {stats['total_queries']}")
    print(f"Başarı oranı: {stats['success_rate']:.1f}%")
    print(f"Güncelleme sıklığı: {stats['update_frequency']}")
    print(f"Son güncelleme: {stats['last_update']}")
except:
    print("İstatistik dosyası henüz oluşmadı.")