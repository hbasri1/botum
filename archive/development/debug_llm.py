import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def ask_gemini(prompt: str):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
    headers = { "Content-Type": "application/json" }
    payload = {
        "contents": [{
            "parts": [{ "text": prompt }]
        }],
        "generationConfig": {
            "temperature": 0.3
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None

# Mevcut prompt
LLM_PROMPT_TEMPLATE = """Sen Türk müşteri hizmetleri asistanısın. Türkçe günlük konuşma dilini mükemmel anlarsın.

Kullanıcının sorusunu analiz et ve JSON formatında cevap ver:

İNTENT TİPLERİ:
- greeting: Selamlama, sohbet
- thanks: Teşekkür, onay, veda (sağol, eyvallah, tamam, tamamdır, olur, peki vs.)
- meta: İşletme bilgisi (telefon, iade, kargo)
- clarify: Belirsiz ürün sorgusu
- product: Spesifik ürün sorgusu

ÜRÜN SORGUSU İÇİN:
- Türkçe ekleri temizle (geceliği→gecelik)
- Attribute belirle (fiyat, stok, renk)

"{question}" → """

# Test
test_queries = [
    "afrika gecelik",
    "afrika geceliği", 
    "afrika gecelik ne kadar"
]

print("🧪 LLM PARSE TESTİ")
print("=" * 40)

for query in test_queries:
    print(f"\nSORU: '{query}'")
    prompt = LLM_PROMPT_TEMPLATE.format(question=query)
    result = ask_gemini(prompt)
    print(f"LLM CEVABI: {result}")
    
    # JSON parse et
    try:
        result_clean = result.strip()
        if result_clean.startswith('```json'):
            result_clean = result_clean[7:]
        if result_clean.endswith('```'):
            result_clean = result_clean[:-3]
        result_clean = result_clean.strip()
        
        data = json.loads(result_clean)
        print(f"PARSE EDİLMİŞ: {data}")
        
        product = data.get("product", "")
        print(f"ÜRÜN ADI: '{product}'")
        
    except Exception as e:
        print(f"PARSE HATASI: {e}")
    
    print("-" * 30)