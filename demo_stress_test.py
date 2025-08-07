#!/usr/bin/env python3
"""
Demo Stress Test - Müşteri senaryolarını test eder
Demoya gelen insanların bulabileceği tüm hataları ortaya çıkarır
"""

import time
import json
from improved_final_mvp_system import ImprovedFinalMVPChatbot

class DemoStressTest:
    def __init__(self):
        self.chatbot = ImprovedFinalMVPChatbot()
        self.failed_tests = []
        self.passed_tests = []
        
    def test_scenario(self, name, messages, expected_behaviors=None):
        """Test a complete customer scenario"""
        print(f"\n🎭 Testing Scenario: {name}")
        print("=" * 50)
        
        scenario_passed = True
        responses = []
        
        for i, message in enumerate(messages, 1):
            print(f"\n👤 Step {i}: {message}")
            
            try:
                start_time = time.time()
                response = self.chatbot.chat(message)
                processing_time = time.time() - start_time
                
                print(f"🤖 Intent: {response.intent} ({response.confidence:.0%})")
                print(f"⏱️  Time: {processing_time:.3f}s")
                print(f"📝 Response: {response.message[:100]}...")
                
                # Check for error responses
                if response.intent == "error" or "hata oluştu" in response.message.lower():
                    print("❌ ERROR DETECTED!")
                    scenario_passed = False
                
                # Check for very low confidence
                if response.confidence < 0.7:
                    print(f"⚠️  LOW CONFIDENCE: {response.confidence:.0%}")
                    scenario_passed = False
                
                # Check for very slow responses
                if processing_time > 2.0:
                    print(f"⚠️  SLOW RESPONSE: {processing_time:.3f}s")
                    scenario_passed = False
                
                responses.append({
                    'message': message,
                    'intent': response.intent,
                    'confidence': response.confidence,
                    'time': processing_time,
                    'response': response.message[:200]
                })
                
            except Exception as e:
                print(f"❌ EXCEPTION: {e}")
                scenario_passed = False
                responses.append({
                    'message': message,
                    'error': str(e)
                })
        
        if scenario_passed:
            print(f"\n✅ Scenario '{name}' PASSED")
            self.passed_tests.append(name)
        else:
            print(f"\n❌ Scenario '{name}' FAILED")
            self.failed_tests.append(name)
        
        return scenario_passed, responses
    
    def run_all_tests(self):
        """Run all demo stress tests"""
        print("🚀 DEMO STRESS TEST - Müşteri Senaryoları")
        print("=" * 60)
        
        # Scenario 1: Normal müşteri akışı
        self.test_scenario("Normal Müşteri Akışı", [
            "merhaba",
            "hamile için pijama arıyorum", 
            "1 numaralı ürünün fiyatı nedir",
            "stokta var mı",
            "nasıl sipariş veririm",
            "teşekkürler"
        ])
        
        # Scenario 2: Renk odaklı arama
        self.test_scenario("Renk Odaklı Arama", [
            "afrika gecelik var mı",
            "siyahı var mı",
            "beyazı var mı", 
            "hangi renkler mevcut",
            "en ucuz hangisi"
        ])
        
        # Scenario 3: Kararsız müşteri
        self.test_scenario("Kararsız Müşteri", [
            "gecelik arıyorum",
            "pijama da var mı",
            "sabahlık nasıl",
            "hangisi daha güzel",
            "fiyatları nasıl",
            "düşüneyim"
        ])
        
        # Scenario 4: Acele müşteri
        self.test_scenario("Acele Müşteri", [
            "hızlı",
            "gecelik",
            "fiyat",
            "stok",
            "sipariş",
            "telefon"
        ])
        
        # Scenario 5: Detaycı müşteri
        self.test_scenario("Detaycı Müşteri", [
            "afrika etnik baskılı dantelli gecelik hakkında detaylı bilgi istiyorum",
            "bu ürünün kumaşı nedir",
            "beden tablosu var mı",
            "iade koşulları nelerdir",
            "kargo ücreti ne kadar",
            "ne zaman gelir"
        ])
        
        # Scenario 6: Sorunlu girişler
        self.test_scenario("Sorunlu Girişler", [
            "",  # Boş mesaj
            "asdasdasd",  # Anlamsız
            "gecelik!!!!",  # Aşırı noktalama
            "çok çok çok uzun bir mesaj bu gerçekten çok uzun gecelik arıyorum",
            "BÜYÜK HARFLERLE YAZIYORUM",
            "123456789"
        ])
        
        # Scenario 7: Çok hızlı sorular
        self.test_scenario("Hızlı Sorular", [
            "merhaba",
            "gecelik",
            "fiyat", 
            "stok",
            "renk",
            "beden",
            "sipariş",
            "kargo",
            "iade",
            "telefon"
        ])
        
        # Scenario 8: Karışık dil kullanımı
        self.test_scenario("Karışık Dil", [
            "hello merhaba",
            "gecelik nightgown",
            "price fiyat ne kadar",
            "thanks teşekkürler",
            "bye güle güle"
        ])
        
        # Scenario 9: Yazım hataları
        self.test_scenario("Yazım Hataları", [
            "afirka gecelik",
            "hamle pijama", 
            "danteli sabahlık",
            "geceli arıyorum",
            "fiyatı nedr"
        ])
        
        # Scenario 10: Bağlam kaybı
        self.test_scenario("Bağlam Kaybı", [
            "afrika geceliği",
            "merhaba",  # Yeni selamlama
            "siyahı var mı",  # Bağlam kayboldu mu?
            "1 numaralı ürün",  # Hangi ürün?
            "teşekkürler"
        ])
        
        # Final report
        self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📊 DEMO STRESS TEST RAPORU")
        print("=" * 60)
        
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        success_rate = len(self.passed_tests) / total_tests * 100 if total_tests > 0 else 0
        
        print(f"📈 Genel Sonuçlar:")
        print(f"   Toplam Test: {total_tests}")
        print(f"   Başarılı: {len(self.passed_tests)} ({success_rate:.1f}%)")
        print(f"   Başarısız: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ Başarısız Testler:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        if self.passed_tests:
            print(f"\n✅ Başarılı Testler:")
            for test in self.passed_tests:
                print(f"   - {test}")
        
        # Demo readiness assessment
        if success_rate >= 90:
            print(f"\n🎉 DEMO HAZIR! Sistem %{success_rate:.1f} başarı oranıyla çalışıyor.")
        elif success_rate >= 80:
            print(f"\n⚠️  DEMO RİSKLİ! %{success_rate:.1f} başarı oranı. Kritik hataları düzeltin.")
        else:
            print(f"\n❌ DEMO HAZIR DEĞİL! %{success_rate:.1f} başarı oranı çok düşük.")
        
        # System stats
        stats = self.chatbot.get_stats()
        print(f"\n📊 Sistem İstatistikleri:")
        print(f"   Toplam İstek: {stats['total_requests']}")
        print(f"   Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
        print(f"   Ortalama Yanıt Süresi: {stats['average_response_time']:.3f}s")
        print(f"   Gemini Çağrıları: {stats.get('gemini_calls', 0)}")
        print(f"   Fallback Çağrıları: {stats.get('fallback_calls', 0)}")

if __name__ == "__main__":
    tester = DemoStressTest()
    tester.run_all_tests()