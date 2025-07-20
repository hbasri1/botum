#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from typing import List, Dict

class BotTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
    
    def ask_bot(self, question: str) -> str:
        """Bota soru sor ve cevabı al"""
        try:
            response = requests.post(
                f"{self.base_url}/ask",
                json={"question": question},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("answer", "Cevap alınamadı")
            else:
                return f"HTTP Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def run_test(self, test_name: str, question: str, expected_keywords: List[str] = None):
        """Tek bir test çalıştır"""
        print(f"\n🧪 TEST: {test_name}")
        print(f"❓ SORU: {question}")
        
        start_time = time.time()
        answer = self.ask_bot(question)
        response_time = time.time() - start_time
        
        print(f"💬 CEVAP: {answer}")
        print(f"⏱️ SÜRE: {response_time:.2f}s")
        
        # Anahtar kelime kontrolü
        success = True
        if expected_keywords:
            for keyword in expected_keywords:
                if keyword.lower() not in answer.lower():
                    success = False
                    print(f"❌ Eksik anahtar kelime: {keyword}")
        
        if success and expected_keywords:
            print("✅ Test başarılı!")
        elif not expected_keywords:
            print("ℹ️ Manuel kontrol gerekli")
        
        self.test_results.append({
            "test_name": test_name,
            "question": question,
            "answer": answer,
            "response_time": response_time,
            "success": success
        })
        
        return answer

def main():
    print("🤖 Butik Cemünay Bot Test Süreci Başlıyor...")
    print("=" * 60)
    
    tester = BotTester()
    
    # 1. ÜRÜN ARAMA TESTLERİ
    print("\n📦 ÜRÜN ARAMA TESTLERİ")
    print("-" * 30)
    
    # Tam ürün adı ile arama
    tester.run_test(
        "Tam Ürün Adı",
        "Kolu Omzu ve Yakası Dantelli Gecelik fiyatı ne kadar?",
        ["fiyat", "tl"]
    )
    
    # Kısaltılmış ürün adı
    tester.run_test(
        "Kısaltılmış Ürün Adı",
        "dantelli gecelik fiyatı",
        ["fiyat", "tl"]
    )
    
    # Yanlış yazım
    tester.run_test(
        "Yanlış Yazım",
        "dantel gecelik ne kadar",
        ["fiyat", "tl"]
    )
    
    # Genel kategori
    tester.run_test(
        "Genel Kategori",
        "gecelik fiyatları",
        ["fiyat", "tl"]
    )
    
    # Renk sorgusu
    tester.run_test(
        "Renk Sorgusu",
        "siyah gecelik var mı?",
        ["siyah", "renk"]
    )
    
    # Stok sorgusu
    tester.run_test(
        "Stok Sorgusu",
        "dantelli pijama stokta var mı?",
        ["stok"]
    )
    
    # 2. META BİLGİ TESTLERİ
    print("\n📋 META BİLGİ TESTLERİ")
    print("-" * 30)
    
    tester.run_test(
        "Telefon Bilgisi",
        "telefon numaranız nedir?",
        ["telefon", "555"]
    )
    
    tester.run_test(
        "Web Site",
        "siteniz nedir?",
        ["site", "butik"]
    )
    
    tester.run_test(
        "İade Politikası",
        "iade nasıl yapılır?",
        ["iade", "14 gün"]
    )
    
    tester.run_test(
        "Kargo Bilgisi",
        "kargo ne kadar sürer?",
        ["kargo", "gün"]
    )
    
    # 3. KARMAŞIK SORGULAR
    print("\n🔍 KARMAŞIK SORGULAR")
    print("-" * 30)
    
    tester.run_test(
        "Çoklu Bilgi",
        "bordo renkli gecelik var mı, fiyatı ne kadar?",
        ["bordo", "fiyat"]
    )
    
    tester.run_test(
        "Belirsiz Sorgu",
        "en ucuz ürününüz hangisi?",
        []
    )
    
    # 4. HATA DURUMLARI
    print("\n❌ HATA DURUMLARI")
    print("-" * 30)
    
    tester.run_test(
        "Olmayan Ürün",
        "erkek gömleği var mı?",
        ["bulunamadı"]
    )
    
    tester.run_test(
        "Anlamsız Sorgu",
        "asdasd qweqwe",
        []
    )
    
    tester.run_test(
        "Boş Sorgu",
        "",
        []
    )
    
    # 5. DOĞAL DİL TESTLERİ
    print("\n💬 DOĞAL DİL TESTLERİ")
    print("-" * 30)
    
    tester.run_test(
        "Günlük Konuşma",
        "merhaba, gecelik arıyorum, ne var?",
        ["gecelik"]
    )
    
    tester.run_test(
        "Kibarlık İfadesi",
        "lütfen bana dantelli pijama fiyatlarını söyler misiniz?",
        ["fiyat", "pijama"]
    )
    
    tester.run_test(
        "Kısa Sorgu",
        "afrika gecelik ne kadar",
        ["fiyat"]
    )
    
    # SONUÇLARI ÖZETLE
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI")
    print("=" * 60)
    
    total_tests = len(tester.test_results)
    successful_tests = sum(1 for result in tester.test_results if result["success"])
    avg_response_time = sum(result["response_time"] for result in tester.test_results) / total_tests
    
    print(f"Toplam Test: {total_tests}")
    print(f"Başarılı: {successful_tests}")
    print(f"Başarı Oranı: {(successful_tests/total_tests)*100:.1f}%")
    print(f"Ortalama Yanıt Süresi: {avg_response_time:.2f}s")
    
    # Başarısız testleri listele
    failed_tests = [result for result in tester.test_results if not result["success"]]
    if failed_tests:
        print(f"\n❌ BAŞARISIZ TESTLER ({len(failed_tests)} adet):")
        for test in failed_tests:
            print(f"- {test['test_name']}: {test['question']}")
    
    # JSON olarak kaydet
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(tester.test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detaylı sonuçlar 'test_results.json' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()