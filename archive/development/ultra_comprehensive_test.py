#!/usr/bin/env python3
"""
Ultra Comprehensive Test - Gerçek müşteri senaryoları
"""

import requests
import json
import time
import random

BASE_URL = "http://localhost:8000"

class UltraComprehensiveTest:
    """Ultra kapsamlı test sistemi"""
    
    def __init__(self):
        # Gerçek ürün isimleri (products.json'dan)
        self.real_products = [
            "Afrika Etnik Baskılı Dantelli \"Africa Style\" Gecelik",
            "Dantelli Önü Düğmeli Hamile Lohusa 3'lü Pijama Takımı",
            "Siyah Dantel Detaylı Gecelik",
            "Beyaz Pamuklu Pijama Takımı",
            "Kırmızı Saten Gecelik"
        ]
        
        # Kısaltılmış versiyonlar
        self.product_shortcuts = [
            "afrika gecelik", "africa gecelik", "etnik gecelik",
            "hamile pijama", "lohusa pijama", "hamile takım",
            "siyah gecelik", "dantel gecelik", "siyah dantel",
            "beyaz pijama", "pamuk pijama", "beyaz takım",
            "kırmızı gecelik", "saten gecelik", "kırmızı saten"
        ]
        
        # Yazım hataları
        self.typos = [
            "afirka gecelik", "afirca gecelik", "afrika gecelig",
            "hamil pijama", "lohus pijama", "hamile pijam",
            "siyh gecelik", "syah gecelik", "siyah gecelig"
        ]
        
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "categories": {}
        }
    
    def make_request(self, question: str) -> dict:
        """API'ye request gönder"""
        try:
            response = requests.post(
                f"{BASE_URL}/ask",
                json={"question": question},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def test_category(self, category_name: str, test_cases: list):
        """Test kategorisi çalıştır"""
        print(f"\n🧪 {category_name}")
        print("-" * 60)
        
        category_results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        for i, test_case in enumerate(test_cases, 1):
            self.test_results["total_tests"] += 1
            category_results["total"] += 1
            
            question = test_case["question"]
            expected = test_case.get("expected", {})
            description = test_case.get("description", "")
            
            print(f"\n{i}. {description}")
            print(f"   Soru: '{question}'")
            
            # Request gönder
            result = self.make_request(question)
            
            if "error" in result:
                print(f"   ❌ ERROR: {result['error']}")
                category_results["failed"] += 1
                self.test_results["failed"] += 1
                continue
            
            # Sonuçları analiz et - API response formatı
            intent = result.get("intent", "unknown")  # API'de intent yok, sadece answer var
            method = result.get("method", "unknown")
            confidence = result.get("confidence", 0)
            answer = result.get("answer", "")
            
            # Intent bilgisi API response'ta yok, method'dan çıkaralım
            if method == "hybrid_direct":
                if "merhaba" in answer.lower():
                    intent = "greeting"
                elif "rica ederim" in answer.lower():
                    intent = "thanks"
                elif "hoşça" in answer.lower():
                    intent = "farewell"
                elif "tam olarak ne" in answer.lower():
                    intent = "clarification_needed"
            elif method == "function_calling":
                intent = "business_info"
            elif method == "hybrid_intelligent_search":
                intent = "product_inquiry"
            
            print(f"   📊 Intent: {intent}")
            print(f"   🔧 Method: {method}")
            print(f"   🎯 Confidence: {confidence:.2f}")
            print(f"   💬 Cevap: {answer[:100]}...")
            
            # Başarı kontrolü
            success = self._evaluate_response(test_case, result)
            
            if success:
                print(f"   ✅ BAŞARILI")
                category_results["passed"] += 1
                self.test_results["passed"] += 1
            else:
                print(f"   ❌ BAŞARISIZ")
                category_results["failed"] += 1
                self.test_results["failed"] += 1
            
            # Detayları kaydet
            category_results["details"].append({
                "question": question,
                "expected": expected,
                "actual": result,
                "success": success
            })
        
        self.test_results["categories"][category_name] = category_results
        
        # Kategori özeti
        success_rate = (category_results["passed"] / category_results["total"]) * 100
        print(f"\n📊 {category_name} Özeti:")
        print(f"   Toplam: {category_results['total']}")
        print(f"   Başarılı: {category_results['passed']}")
        print(f"   Başarısız: {category_results['failed']}")
        print(f"   Başarı Oranı: {success_rate:.1f}%")
    
    def _evaluate_response(self, test_case: dict, result: dict) -> bool:
        """Response'u değerlendir"""
        expected = test_case.get("expected", {})
        
        # Intent kontrolü
        if "intent" in expected:
            if result.get("intent") != expected["intent"]:
                return False
        
        # Method kontrolü
        if "method_type" in expected:
            method = result.get("method", "")
            expected_type = expected["method_type"]
            
            if expected_type == "pattern" and not any(x in method for x in ["hybrid_direct", "certain_pattern"]):
                return False
            elif expected_type == "function" and not any(x in method for x in ["function_calling", "hybrid_function"]):
                return False
            elif expected_type == "search" and not any(x in method for x in ["intelligent_search", "hybrid_intelligent_search"]):
                return False
        
        # Confidence kontrolü
        if "min_confidence" in expected:
            if result.get("confidence", 0) < expected["min_confidence"]:
                return False
        
        # Cevap içerik kontrolü
        if "should_contain" in expected:
            answer = result.get("answer", "").lower()
            for keyword in expected["should_contain"]:
                if keyword.lower() not in answer:
                    return False
        
        # Cevap içermemesi gereken
        if "should_not_contain" in expected:
            answer = result.get("answer", "").lower()
            for keyword in expected["should_not_contain"]:
                if keyword.lower() in answer:
                    return False
        
        return True
    
    def run_dialog_tests(self):
        """Diyalog testleri - gerçek konuşma akışı"""
        print(f"\n💬 DIYALOG TESTLERİ")
        print("=" * 60)
        
        dialogs = [
            {
                "name": "Ürün Fiyat Sorgusu Diyalogu",
                "steps": [
                    {"user": "merhaba", "expect_greeting": True},
                    {"user": "afrika gecelik fiyatı ne kadar", "expect_product_info": True},
                    {"user": "teşekkürler", "expect_thanks": True},
                    {"user": "iyi günler", "expect_farewell": True}
                ]
            },
            {
                "name": "Belirsiz Sorgu Diyalogu",
                "steps": [
                    {"user": "selam", "expect_greeting": True},
                    {"user": "gecelik", "expect_product_search": True},
                    {"user": "siyah olanı", "expect_clarification": True},
                    {"user": "tamam teşekkürler", "expect_thanks": True}
                ]
            },
            {
                "name": "İade Sorgusu Diyalogu",
                "steps": [
                    {"user": "merhaba", "expect_greeting": True},
                    {"user": "iade var mı", "expect_business_info": True},
                    {"user": "kaç gün içinde", "expect_clarification": True},
                    {"user": "anladım sağol", "expect_thanks": True}
                ]
            }
        ]
        
        for dialog in dialogs:
            print(f"\n🎭 {dialog['name']}")
            print("-" * 40)
            
            for step_num, step in enumerate(dialog["steps"], 1):
                user_message = step["user"]
                print(f"\n{step_num}. Kullanıcı: '{user_message}'")
                
                result = self.make_request(user_message)
                
                if "error" not in result:
                    print(f"   🤖 Bot: {result.get('answer', '')[:80]}...")
                    print(f"   📊 Intent: {result.get('intent', 'unknown')}")
                else:
                    print(f"   ❌ Error: {result['error']}")
                
                time.sleep(0.5)  # Gerçek konuşma hızı
    
    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🚀 ULTRA COMPREHENSIVE TEST BAŞLIYOR")
        print("=" * 80)
        
        # 1. Temel Intent Testleri
        basic_intent_tests = [
            {"question": "merhaba", "description": "Basit selamlama", "expected": {"intent": "greeting", "method_type": "pattern"}},
            {"question": "selam nasılsın", "description": "Uzun selamlama", "expected": {"intent": "greeting"}},
            {"question": "teşekkürler", "description": "Teşekkür", "expected": {"intent": "thanks", "method_type": "pattern"}},
            {"question": "çok sağol", "description": "Uzun teşekkür", "expected": {"intent": "thanks"}},
            {"question": "hoşça kal", "description": "Vedalaşma", "expected": {"intent": "farewell", "method_type": "pattern"}},
            {"question": "tamam iyi günler", "description": "Konuşma bitirme", "expected": {"intent": "farewell"}},
            {"question": "yok teşekkürler", "description": "Red + teşekkür", "expected": {"should_not_contain": ["ürün bulunamadı"]}},
            {"question": "tamam", "description": "Basit onay", "expected": {"should_not_contain": ["ürün bulunamadı"]}},
        ]
        self.test_category("Temel Intent Testleri", basic_intent_tests)
        
        # 2. İşletme Bilgi Testleri
        business_info_tests = [
            {"question": "telefon numaranız", "description": "Telefon sorgusu", "expected": {"method_type": "function", "should_contain": ["telefon"]}},
            {"question": "iade var mı", "description": "İade sorgusu", "expected": {"method_type": "function", "should_contain": ["iade"]}},
            {"question": "kargo nasıl", "description": "Kargo sorgusu", "expected": {"method_type": "function", "should_contain": ["kargo"]}},
            {"question": "siteniz var mı", "description": "Website sorgusu", "expected": {"method_type": "function", "should_contain": ["site"]}},
        ]
        self.test_category("İşletme Bilgi Testleri", business_info_tests)
        
        # 3. Ürün Arama Testleri - Gerçek Ürünler
        product_search_tests = []
        
        # Tam ürün isimleri
        for product in self.real_products[:3]:  # İlk 3 ürün
            product_search_tests.append({
                "question": product,
                "description": f"Tam ürün ismi: {product[:30]}...",
                "expected": {"method_type": "search", "should_contain": [product.split()[0].lower()]}
            })
        
        # Kısaltılmış versiyonlar
        for shortcut in self.product_shortcuts[:5]:
            product_search_tests.append({
                "question": shortcut,
                "description": f"Kısaltılmış: {shortcut}",
                "expected": {"method_type": "search"}
            })
        
        # Yazım hataları
        for typo in self.typos[:3]:
            product_search_tests.append({
                "question": typo,
                "description": f"Yazım hatası: {typo}",
                "expected": {"method_type": "search"}
            })
        
        self.test_category("Ürün Arama Testleri", product_search_tests)
        
        # 4. Fiyat Sorguları
        price_query_tests = [
            {"question": "afrika gecelik fiyatı", "description": "Direkt fiyat sorgusu", "expected": {"method_type": "search", "should_contain": ["fiyat", "tl"]}},
            {"question": "hamile pijama ne kadar", "description": "Ne kadar sorgusu", "expected": {"method_type": "search"}},
            {"question": "siyah gecelik kaç para", "description": "Kaç para sorgusu", "expected": {"method_type": "search"}},
            {"question": "fiyatları nedir", "description": "Genel fiyat sorgusu", "expected": {"method_type": "search"}},
        ]
        self.test_category("Fiyat Sorguları", price_query_tests)
        
        # 5. Stok Sorguları
        stock_query_tests = [
            {"question": "hamile pijama var mı", "description": "Var mı sorgusu", "expected": {"method_type": "search"}},
            {"question": "afrika gecelik stokta", "description": "Stok sorgusu", "expected": {"method_type": "search"}},
            {"question": "beyaz pijama mevcut mu", "description": "Mevcut sorgusu", "expected": {"method_type": "search"}},
        ]
        self.test_category("Stok Sorguları", stock_query_tests)
        
        # 6. Problemli Durumlar - Bunlar düzeltilmeli
        problematic_tests = [
            {"question": "fiyat sorcaktım", "description": "Yanlış ürün algılama", "expected": {"should_not_contain": ["ürün bulunamadı"]}},
            {"question": "tamam", "description": "Basit onay", "expected": {"should_not_contain": ["ürün bulunamadı"]}},
            {"question": "ok", "description": "İngilizce onay", "expected": {"should_not_contain": ["ürün bulunamadı"]}},
            {"question": "anladım", "description": "Anlama ifadesi", "expected": {"should_not_contain": ["ürün bulunamadı"]}},
            {"question": "peki", "description": "Onay kelimesi", "expected": {"should_not_contain": ["ürün bulunamadı"]}},
        ]
        self.test_category("Problemli Durumlar (Düzeltilmeli)", problematic_tests)
        
        # 7. Edge Cases
        edge_case_tests = [
            {"question": "", "description": "Boş string", "expected": {}},
            {"question": "asdfghjkl", "description": "Anlamsız kelime", "expected": {}},
            {"question": "123456", "description": "Sadece rakam", "expected": {}},
            {"question": "çok uzun bir mesaj bu gerçekten çok uzun bir mesaj ve anlamsız", "description": "Çok uzun mesaj", "expected": {}},
        ]
        self.test_category("Edge Cases", edge_case_tests)
        
        # 8. Diyalog Testleri
        self.run_dialog_tests()
        
        # 9. Final Rapor
        self.generate_final_report()
    
    def generate_final_report(self):
        """Final rapor oluştur"""
        print(f"\n" + "=" * 80)
        print("📊 ULTRA COMPREHENSIVE TEST RAPORU")
        print("=" * 80)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n🎯 GENEL SONUÇLAR:")
        print(f"   Toplam Test: {total}")
        print(f"   Başarılı: {passed}")
        print(f"   Başarısız: {failed}")
        print(f"   Başarı Oranı: {success_rate:.1f}%")
        
        print(f"\n📋 KATEGORİ DETAYLARI:")
        for category, results in self.test_results["categories"].items():
            cat_success_rate = (results["passed"] / results["total"]) * 100
            status = "✅" if cat_success_rate >= 80 else "⚠️" if cat_success_rate >= 60 else "❌"
            print(f"   {status} {category}: {cat_success_rate:.1f}% ({results['passed']}/{results['total']})")
        
        # Kritik hatalar
        print(f"\n🚨 KRİTİK HATALAR:")
        critical_issues = []
        
        for category, results in self.test_results["categories"].items():
            for detail in results["details"]:
                if not detail["success"] and "should_not_contain" in detail["expected"]:
                    critical_issues.append({
                        "category": category,
                        "question": detail["question"],
                        "issue": "Yanlış ürün algılama"
                    })
        
        if critical_issues:
            for issue in critical_issues[:5]:  # İlk 5 kritik hata
                print(f"   ❌ {issue['category']}: '{issue['question']}' - {issue['issue']}")
        else:
            print(f"   ✅ Kritik hata bulunamadı!")
        
        # Öneriler
        print(f"\n💡 ÖNERİLER:")
        if success_rate >= 90:
            print(f"   🎉 Sistem mükemmel çalışıyor!")
        elif success_rate >= 80:
            print(f"   ✅ Sistem iyi çalışıyor, küçük iyileştirmeler yapılabilir")
        elif success_rate >= 70:
            print(f"   ⚠️ Sistem orta seviyede, önemli iyileştirmeler gerekli")
        else:
            print(f"   ❌ Sistem ciddi sorunlar içeriyor, büyük düzeltmeler gerekli")
        
        print(f"\n🎯 SONRAKI ADIMLAR:")
        print(f"   1. Kritik hataları düzelt")
        print(f"   2. Pattern matching'i güçlendir")
        print(f"   3. Ürün detection algoritmasını iyileştir")
        print(f"   4. LLM fallback'lerini optimize et")

if __name__ == "__main__":
    test = UltraComprehensiveTest()
    test.run_all_tests()