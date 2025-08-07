import requests
import json
import asyncio

# Chatbot API adresi
API_URL = "http://127.0.0.1:8000/ask"

# Test senaryoları
TEST_CASES = [
    # 1. Intent Detection Tests
    {"query": "merhaba", "expected_intent": "greeting"},
    {"query": "selam", "expected_intent": "greeting"},
    {"query": "teşekkürler", "expected_intent": "thanks"},
    {"query": "sağ ol", "expected_intent": "thanks"},
    {"query": "telefon numaranız nedir?", "expected_intent": "meta_query", "expected_attr": "telefon"},
    {"query": "iade politikanız", "expected_intent": "meta_query", "expected_attr": "iade"},
    {"query": "kargo ücreti ne kadar?", "expected_intent": "meta_query", "expected_attr": "kargo"},
    
    # 2. Türkçe NLP and Product Name Normalization Tests
    {"query": "geceliğin fiyatı", "expected_intent": "product_query", "expected_product": "gecelik", "expected_attr": "fiyat"},
    {"query": "pijamaların bedenleri", "expected_intent": "product_query", "expected_product": "pijama", "expected_attr": "beden"},
    {"query": "elbiseyi satın almak istiyorum", "expected_intent": "product_query", "expected_product": "elbise"},
    {"query": "hamileler için olan pijama takımı var mı?", "expected_intent": "product_query", "expected_product": "hamile pijama takımı", "expected_attr": "stok"},
    {"query": "sabahlığın rengi nedir?", "expected_intent": "product_query", "expected_product": "sabahlık", "expected_attr": "renk"},
    {"query": "Sırtı Dekolteli Tüllü ve Dantelli Pijama Takımının stok durumu", "expected_intent": "product_query", "expected_product": "Sırtı Dekolteli Tüllü ve Dantelli Pijama Takımı", "expected_attr": "stok"},

    # 3. Product Matching and Search Tests
    {"query": "siyah dekolteli gecelik", "expected_intent": "product_query", "expected_product_keywords": ["siyah", "dekolte", "gecelik"]},
    {"query": "dantelli pijama takımı ekru", "expected_intent": "product_query", "expected_product_keywords": ["dantelli", "pijama", "ekru"]},
    {"query": "3'lü hamile pijama takımı", "expected_intent": "product_query", "expected_product_keywords": ["3'lü", "hamile", "pijama"]},
    {"query": "büyük beden geceliklerinizden var mı?", "expected_intent": "product_query", "expected_product": "büyük beden gecelik"},

    # 4. Context and Clarification Tests
    {"query": "bu ne kadar?", "expected_intent": "clarify"},
    {"query": "fiyatı nedir?", "expected_intent": "clarify"},
    # Bu testler manuel olarak veya daha karmaşık bir test script'i ile context yönetimi kontrol edilerek yapılmalıdır.

    # 5. Edge Cases and Error Handling
    {"query": "alakasız bir soru", "expected_intent": "unknown"},
    {"query": "pizza sipariş etmek istiyorum", "expected_intent": "unknown"},
    {"query": "asdfghjkl", "expected_intent": "unknown"},
    {"query": "", "expected_intent": "unknown"}, # Boş sorgu
    {"query": "sadece bir kelime", "expected_intent": "product_query"}, # Genel bir sorgu

    # 6. More Complex Queries
    {"query": "hem siyah hem de dantelli olan bir gecelik arıyorum, fiyatı ne kadar?", "expected_intent": "product_query", "expected_product": "siyah dantelli gecelik", "expected_attr": "fiyat"},
    {"query": "merhaba, hamileler için olan pijamaların stok durumunu öğrenebilir miyim?", "expected_intent": "product_query", "expected_product": "hamile pijama", "expected_attr": "stok"},
    {"query": "kırmızı renkli bir sabahlık var mı ve iade şartlarınız nelerdir?", "expected_intent": "product_query"}, # Multiple intents, should prioritize product

    # 7. Additional Turkish variations
    {"query": "geceliklerin fiyatlarını göster", "expected_intent": "product_query", "expected_product": "gecelik", "expected_attr": "fiyat"},
    {"query": "pijama takımlarınızdan hangileri indirimde?", "expected_intent": "product_query", "expected_product": "pijama takımı", "expected_attr": "indirim"},
    {"query": "en ucuz elbiseniz hangisi?", "expected_intent": "product_query", "expected_product": "elbise", "expected_attr": "fiyat"},
    {"query": "lacivert renkli sabahlıkların kodunu alabilir miyim?", "expected_intent": "product_query", "expected_product": "lacivert sabahlık", "expected_attr": "kod"},

    # 8. More product specific queries
    {"query": "18K18154 kodlu ürünün rengi nedir?", "expected_intent": "product_query", "expected_product": "18K18154", "expected_attr": "renk"},
    {"query": "Yakası ve Omzu Dantelli Önü Boydan Düğmeli Pijama Takımı için stok var mı?", "expected_intent": "product_query", "expected_product": "Yakası ve Omzu Dantelli Önü Boydan Düğmeli Pijama Takımı", "expected_attr": "stok"},
    {"query": "vizon rengi gecelikler", "expected_intent": "product_query", "expected_product": "vizon gecelik"},
    {"query": "bordo pijamalar", "expected_intent": "product_query", "expected_product": "bordo pijama"},
]

# 100+ test senaryosuna tamamlamak için eklemeler
ADDITIONAL_TEST_CASES = [
    {"query": "merhabalar", "expected_intent": "greeting"},
    {"query": "selamlar", "expected_intent": "greeting"},
    {"query": "çok sağolun", "expected_intent": "thanks"},
    {"query": "teşekkür ederim", "expected_intent": "thanks"},
    {"query": "websiteniz nedir?", "expected_intent": "meta_query", "expected_attr": "site"},
    {"query": "kargo bilgisi alabilir miyim?", "expected_intent": "meta_query", "expected_attr": "kargo"},
    {"query": "geceliklerin bedenleri nelerdir?", "expected_intent": "product_query", "expected_product": "gecelik", "expected_attr": "beden"},
    {"query": "pijama takımlarının renk seçenekleri", "expected_intent": "product_query", "expected_product": "pijama takımı", "expected_attr": "renk"},
    {"query": "lohusa sabahlık takımı var mı?", "expected_intent": "product_query", "expected_product": "lohusa sabahlık takımı", "expected_attr": "stok"},
    {"query": "dantelli geceliklerin fiyat aralığı nedir?", "expected_intent": "product_query", "expected_product": "dantelli gecelik", "expected_attr": "fiyat"},
    {"query": "ekru renkli pijama", "expected_intent": "product_query", "expected_product_keywords": ["ekru", "pijama"]},
    {"query": "büyük beden hamile geceliği", "expected_intent": "product_query", "expected_product_keywords": ["büyük beden", "hamile", "gecelik"]},
    {"query": "ne kadar bu?", "expected_intent": "clarify"},
    {"query": "özellikleri neler?", "expected_intent": "clarify"},
    {"query": "alakasız bir konu hakkında konuşalım", "expected_intent": "unknown"},
    {"query": "hava durumu nasıl?", "expected_intent": "unknown"},
    {"query": "siyah ve dantelli gecelik fiyatları", "expected_intent": "product_query", "expected_product": "siyah dantelli gecelik", "expected_attr": "fiyat"},
    {"query": "hamile pijamalarının stok durumu ve iade koşulları", "expected_intent": "product_query", "expected_product": "hamile pijama", "expected_attr": "stok"},
    {"query": "en pahalı gecelik hangisi?", "expected_intent": "product_query", "expected_product": "gecelik", "expected_attr": "fiyat"},
    {"query": "18K18202 kodlu ürünün adı nedir?", "expected_intent": "product_query", "expected_product": "18K18202", "expected_attr": "ad"},
    {"query": "vizon rengi sabahlıklar", "expected_intent": "product_query", "expected_product": "vizon sabahlık"},
    {"query": "bordo gecelikler", "expected_intent": "product_query", "expected_product": "bordo gecelik"},
    {"query": "indirimli ürünleriniz var mı?", "expected_intent": "product_query", "expected_product": "indirimli ürünler", "expected_attr": "indirim"},
    {"query": "siyah renkli elbiseler", "expected_intent": "product_query", "expected_product": "siyah elbise", "expected_attr": "renk"},
    {"query": "bornoz var mı?", "expected_intent": "unknown"},
    {"query": "çocuk pijaması", "expected_intent": "unknown"},
    {"query": "erkek pijama", "expected_intent": "unknown"},
    {"query": "sadece gecelik", "expected_intent": "product_query", "expected_product": "gecelik"},
    {"query": "fiyat", "expected_intent": "clarify"},
    {"query": "renk", "expected_intent": "clarify"},
    {"query": "beden", "expected_intent": "clarify"},
    {"query": "stok", "expected_intent": "clarify"},
    {"query": "Merhaba, siyah dekolteli tüllü bir pijama takımı arıyorum, acaba elinizde var mı?", "expected_intent": "product_query", "expected_product": "siyah dekolteli tüllü pijama takımı", "expected_attr": "stok"},
    {"query": "İade politikanız hakkında detaylı bilgi verebilir misiniz acaba?", "expected_intent": "meta_query", "expected_attr": "iade"},
    {"query": "Sitenizden alışveriş yapmak güvenli mi?", "expected_intent": "meta_query", "expected_attr": "güvenlik"}, # `güvenlik` meta'da yok, `unknown` da olabilir.
    {"query": "Ürünleriniz hangi malzemeden yapılıyor?", "expected_intent": "clarify"}, # Hangi ürün?
    {"query": "Kargo kaç günde gelir?", "expected_intent": "meta_query", "expected_attr": "kargo"},
    {"query": "Önü düğmeli hamile lohusa geceliklerinin fiyatı nedir?", "expected_intent": "product_query", "expected_product": "önü düğmeli hamile lohusa gecelik", "expected_attr": "fiyat"},
    {"query": "Büyük beden pijama takımlarının renkleri nelerdir?", "expected_intent": "product_query", "expected_product": "büyük beden pijama takımı", "expected_attr": "renk"},
    {"query": "En çok satan ürününüz hangisi?", "expected_intent": "unknown"},
    {"query": "Bu ürünün başka rengi var mı?", "expected_intent": "clarify"},
    {"query": "Siyah ve ekru renklerinde pijama takımı arıyorum.", "expected_intent": "product_query", "expected_product": "siyah ekru pijama takımı"},
    {"query": "Dantelli ve yırtmaçlı gecelikler ne kadar?", "expected_intent": "product_query", "expected_product": "dantelli yırtmaçlı gecelik", "expected_attr": "fiyat"},
    {"query": "Sadece sabahlık satıyor musunuz?", "expected_intent": "product_query", "expected_product": "sabahlık"},
    {"query": "Kapıda ödeme var mı?", "expected_intent": "meta_query", "expected_attr": "ödeme"}, # `ödeme` meta'da yok, `unknown` da olabilir.
    {"query": "Hangi kargo firması ile çalışıyorsunuz?", "expected_intent": "meta_query", "expected_attr": "kargo"},
    {"query": "Ürünlerinizi nereden alabilirim?", "expected_intent": "meta_query", "expected_attr": "site"},
    {"query": "Bu pijamanın aynısının farklı bir rengi var mı?", "expected_intent": "clarify"},
    {"query": "3'lü pijama takımları ne kadar?", "expected_intent": "product_query", "expected_product": "3'lü pijama takımı", "expected_attr": "fiyat"},
    {"query": "Stokta olmayan ürünler ne zaman gelir?", "expected_intent": "unknown"},
    {"query": "Müşteri hizmetlerine nasıl ulaşabilirim?", "expected_intent": "meta_query", "expected_attr": "telefon"},
    {"query": "Siyah dekolteli tüllü pijamanın başka bedeni var mı?", "expected_intent": "product_query", "expected_product": "siyah dekolteli tüllü pijama", "expected_attr": "beden"},
    {"query": "Bu geceliğin kumaşı nedir?", "expected_intent": "clarify"},
    {"query": "Siparişimi nasıl takip edebilirim?", "expected_intent": "unknown"},
    {"query": "Hediye paketi yapıyor musunuz?", "expected_intent": "unknown"},
    {"query": "Toplu alımda indirim var mı?", "expected_intent": "unknown"},
    {"query": "Siyah, dantelli, dekolteli, tüllü pijama takımı", "expected_intent": "product_query", "expected_product": "siyah dantelli dekolteli tüllü pijama takımı"},
    {"query": "En yeni ürünleriniz hangileri?", "expected_intent": "product_query", "expected_product": "yeni ürünler"},
    {"query": "Geçen hafta baktığım bir ürün vardı, bulamıyorum.", "expected_intent": "clarify"},
    {"query": "Bu sabahlığın bornozu var mı?", "expected_intent": "product_query", "expected_product": "sabahlık bornoz"},
    {"query": "Sadece üst pijama satıyor musunuz?", "expected_intent": "unknown"},
    {"query": "Siyah renkli, büyük beden, dantelli, hamile geceliği var mı?", "expected_intent": "product_query", "expected_product": "siyah büyük beden dantelli hamile geceliği", "expected_attr": "stok"},
]

TEST_CASES.extend(ADDITIONAL_TEST_CASES)


async def run_test(test_case):
    """Tek bir test senaryosunu çalıştırır ve sonucu döndürür."""
    query = test_case["query"]
    payload = {"question": query}

    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json().get("answer", "")
        
        # Bu test script'i LLM'in JSON çıktısını değil, son kullanıcıya giden cevabı test eder.
        # Daha detaylı test için, /ask endpoint'inin direkt LLM'in JSON çıktısını döndürmesi gerekir.
        # Şimdilik, dönen cevabın beklenen anahtar kelimeleri içerip içermediğini kontrol edebiliriz.
        
        # Basit bir pass/fail mantığı (şimdilik)
        # Bu kısım, beklenen yanıta göre daha karmaşık hale getirilebilir.
        # Örneğin, beklenen intent'e göre farklı kontroller yapılabilir.
        
        # Cevabın genel bir hata mesajı olup olmadığını kontrol et
        if "üzgünüm" in result.lower() or "hata" in result.lower():
            print(f"FAIL: '{query}' -> Bot returned an error: '{result[:100]}...'")
            return {"query": query, "status": "FAIL", "error": "Bot returned an error", "response": result}

        # Şimdilik basit bir PASS durumu
        print(f"PASS: '{query}' -> '{result[:100]}...'")
        return {"query": query, "status": "PASS", "response": result}
        
    except requests.exceptions.RequestException as e:
        print(f"FAIL: '{query}' -> Error: {e}")
        return {"query": query, "status": "FAIL", "error": str(e)}
    except json.JSONDecodeError:
        print(f"FAIL: '{query}' -> Invalid JSON response")
        return {"query": query, "status": "FAIL", "error": "Invalid JSON response"}


async def main():
    """Tüm testleri asenkron olarak çalıştırır ve sonuçları raporlar."""
    print(f"🚀 {len(TEST_CASES)} adet test senaryosu çalıştırılıyor...")
    
    tasks = [run_test(case) for case in TEST_CASES]
    results = await asyncio.gather(*tasks)
    
    # Sonuçları analiz et
    passed = [r for r in results if r["status"] == "PASS"]
    failed = [r for r in results if r["status"] == "FAIL"]
    
    success_rate = (len(passed) / len(TEST_CASES)) * 100
    
    print("\n" + "="*50)
    print("📊 TEST SONUÇLARI")
    print("="*50)
    print(f"✅ Başarılı Testler: {len(passed)}")
    print(f"❌ Başarısız Testler: {len(failed)}")
    print(f"🎯 Başarı Oranı: {success_rate:.2f}%")
    
    if failed:
        print("\n--- BAŞARISIZ TESTLER ---")
        for f in failed:
            print(f"- Sorgu: '{f['query']}' -> Hata: {f['error']}")

    # Sonuçları JSON dosyasına yaz
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_tests": len(TEST_CASES),
            "passed": len(passed),
            "failed": len(failed),
            "success_rate": success_rate,
            "failed_cases": failed
        }, f, ensure_ascii=False, indent=2)

    print("\n💾 Test sonuçları 'test_results.json' dosyasına kaydedildi.")


if __name__ == "__main__":
    # FastAPI sunucusunun çalıştığından emin olun.
    # Terminalde: uvicorn main:app --reload
    asyncio.run(main())
