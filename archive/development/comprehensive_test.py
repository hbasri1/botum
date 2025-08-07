#!/usr/bin/env python3
"""
Kapsamlı Test Sistemi - Yüksek Hacim ve Edge Case Testleri
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import statistics

class ComprehensiveTestSuite:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.results = []
        self.failed_tests = []
        self.performance_stats = []
    
    async def run_single_test(self, session: aiohttp.ClientSession, question: str, 
                            expected_method: str = None, expected_keywords: List[str] = None) -> Dict[str, Any]:
        """Tek test çalıştır"""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/ask",
                json={"question": question, "business_id": "fashion_boutique"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Test sonucunu değerlendir
                    test_result = {
                        "question": question,
                        "answer": result.get("answer", ""),
                        "method": result.get("method", "unknown"),
                        "confidence": result.get("confidence", 0.0),
                        "execution_time_ms": execution_time,
                        "server_time_ms": result.get("execution_time_ms", 0),
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Beklenen method kontrolü
                    if expected_method and result.get("method") != expected_method:
                        test_result["method_mismatch"] = True
                        test_result["expected_method"] = expected_method
                    
                    # Beklenen keyword kontrolü
                    if expected_keywords:
                        answer_lower = result.get("answer", "").lower()
                        missing_keywords = [kw for kw in expected_keywords if kw.lower() not in answer_lower]
                        if missing_keywords:
                            test_result["missing_keywords"] = missing_keywords
                    
                    return test_result
                else:
                    return {
                        "question": question,
                        "error": f"HTTP {response.status}",
                        "success": False,
                        "execution_time_ms": (time.time() - start_time) * 1000,
                        "timestamp": datetime.now().isoformat()
                    }
        
        except Exception as e:
            return {
                "question": question,
                "error": str(e),
                "success": False,
                "execution_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_product_tests(self, session: aiohttp.ClientSession):
        """Ürün testleri"""
        print("🛍️ Ürün Testleri Başlıyor...")
        
        product_tests = [
            # Temel ürün sorguları
            ("afrika gecelik", "function_calling", ["afrika", "gecelik"]),
            ("afrika geceliği", "function_calling", ["afrika", "gecelik"]),
            ("afrika gecelik fiyatı", "function_calling", ["565.44", "TL"]),
            ("afrika gecelik var mı", "function_calling", ["stokta", "mevcut"]),
            
            # Hamile ürünleri
            ("hamile gecelik", "function_calling", ["hamile", "gecelik"]),
            ("hamile geceliği", "function_calling", ["hamile", "gecelik"]),
            ("hamile pijama", "function_calling", ["hamile", "pijama"]),
            
            # Pijama testleri
            ("pijama", "function_calling", ["pijama"]),
            ("pijama fiyatı", "function_calling", ["pijama", "TL"]),
            ("pijama takımı", "function_calling", ["pijama", "takım"]),
            
            # Edge cases
            ("gecelik", "function_calling", ["gecelik"]),
            ("gecelig", "function_calling", ["gecelik"]),  # Yazım hatası
            ("AFRIKA GECELİK", "function_calling", ["afrika", "gecelik"]),  # Büyük harf
            
            # Renk sorguları
            ("siyah gecelik", "function_calling", ["gecelik"]),
            ("beyaz pijama", "function_calling", ["pijama"]),
            ("kırmızı elbise", "function_calling", ["elbise"]),
            
            # Beden sorguları
            ("gecelik bedenleri", "function_calling", ["gecelik", "beden"]),
            ("pijama bedenleri", "function_calling", ["pijama", "beden"]),
            
            # Stok sorguları
            ("hangi ürünler var", "function_calling", []),
            ("stokta ne var", "function_calling", []),
        ]
        
        for question, expected_method, expected_keywords in product_tests:
            result = await self.run_single_test(session, question, expected_method, expected_keywords)
            self.results.append(result)
            
            if not result.get("success") or result.get("method_mismatch") or result.get("missing_keywords"):
                self.failed_tests.append(result)
                print(f"❌ FAIL: {question} -> {result.get('answer', 'ERROR')}")
            else:
                print(f"✅ PASS: {question}")
    
    async def run_business_info_tests(self, session: aiohttp.ClientSession):
        """İşletme bilgi testleri"""
        print("\n📞 İşletme Bilgi Testleri Başlıyor...")
        
        business_tests = [
            ("telefon", "function_calling", ["0555 555 55 55"]),
            ("telefon numaranız", "function_calling", ["0555 555 55 55"]),
            ("iletişim", "function_calling", ["0555 555 55 55"]),
            ("iade", "function_calling", ["iade", "14 gün"]),
            ("iade nasıl yapılır", "function_calling", ["iade", "14 gün"]),
            ("kargo", "function_calling", ["kargo"]),
            ("teslimat", "function_calling", ["kargo"]),
            ("site", "function_calling", ["site"]),
            ("web sitesi", "function_calling", ["site"]),
        ]
        
        for question, expected_method, expected_keywords in business_tests:
            result = await self.run_single_test(session, question, expected_method, expected_keywords)
            self.results.append(result)
            
            if not result.get("success") or result.get("method_mismatch") or result.get("missing_keywords"):
                self.failed_tests.append(result)
                print(f"❌ FAIL: {question} -> {result.get('answer', 'ERROR')}")
            else:
                print(f"✅ PASS: {question}")
    
    async def run_greeting_tests(self, session: aiohttp.ClientSession):
        """Selamlama testleri"""
        print("\n👋 Selamlama Testleri Başlıyor...")
        
        greeting_tests = [
            ("merhaba", "direct_response", ["merhaba", "hoş geldiniz"]),
            ("selam", "direct_response", ["merhaba", "hoş geldiniz"]),
            ("hello", "direct_response", ["merhaba", "hoş geldiniz"]),
            ("hi", "direct_response", ["merhaba", "hoş geldiniz"]),
            ("teşekkürler", "direct_response", ["rica ederim"]),
            ("sağol", "direct_response", ["rica ederim"]),
        ]
        
        for question, expected_method, expected_keywords in greeting_tests:
            result = await self.run_single_test(session, question, expected_method, expected_keywords)
            self.results.append(result)
            
            if not result.get("success") or result.get("method_mismatch") or result.get("missing_keywords"):
                self.failed_tests.append(result)
                print(f"❌ FAIL: {question} -> {result.get('answer', 'ERROR')}")
            else:
                print(f"✅ PASS: {question}")
    
    async def run_edge_case_tests(self, session: aiohttp.ClientSession):
        """Edge case testleri"""
        print("\n🔍 Edge Case Testleri Başlıyor...")
        
        edge_cases = [
            ("", None, []),  # Boş string
            ("asdfgh", None, []),  # Anlamsız string
            ("123456", None, []),  # Sadece rakam
            ("!@#$%", None, []),  # Sadece sembol
            ("a" * 1000, None, []),  # Çok uzun string
            ("afrika gecelik fiyatı ne kadar stok durumu nasıl", None, []),  # Karmaşık soru
        ]
        
        for question, expected_method, expected_keywords in edge_cases:
            result = await self.run_single_test(session, question, expected_method, expected_keywords)
            self.results.append(result)
            print(f"📝 EDGE: {question[:50]}... -> {result.get('method', 'ERROR')}")
    
    async def run_performance_test(self, session: aiohttp.ClientSession, concurrent_requests: int = 10):
        """Performance testi"""
        print(f"\n⚡ Performance Testi Başlıyor... ({concurrent_requests} eşzamanlı istek)")
        
        test_questions = [
            "afrika gecelik",
            "telefon numaranız",
            "hamile gecelik var mı",
            "pijama fiyatı",
            "merhaba"
        ]
        
        # Eşzamanlı istekler
        tasks = []
        for i in range(concurrent_requests):
            question = test_questions[i % len(test_questions)]
            task = self.run_single_test(session, f"{question} {i}")
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        if successful_results:
            response_times = [r["execution_time_ms"] for r in successful_results]
            
            perf_stats = {
                "total_requests": concurrent_requests,
                "successful_requests": len(successful_results),
                "failed_requests": concurrent_requests - len(successful_results),
                "total_time_seconds": total_time,
                "requests_per_second": concurrent_requests / total_time,
                "avg_response_time_ms": statistics.mean(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "median_response_time_ms": statistics.median(response_times)
            }
            
            self.performance_stats.append(perf_stats)
            
            print(f"📊 Performance Sonuçları:")
            print(f"   • Toplam İstek: {perf_stats['total_requests']}")
            print(f"   • Başarılı: {perf_stats['successful_requests']}")
            print(f"   • Başarısız: {perf_stats['failed_requests']}")
            print(f"   • RPS: {perf_stats['requests_per_second']:.2f}")
            print(f"   • Ortalama Yanıt: {perf_stats['avg_response_time_ms']:.2f}ms")
            print(f"   • Min/Max: {perf_stats['min_response_time_ms']:.2f}/{perf_stats['max_response_time_ms']:.2f}ms")
    
    async def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🚀 Kapsamlı Test Süreci Başlıyor...\n")
        
        async with aiohttp.ClientSession() as session:
            # Temel testler
            await self.run_product_tests(session)
            await self.run_business_info_tests(session)
            await self.run_greeting_tests(session)
            await self.run_edge_case_tests(session)
            
            # Performance testleri
            await self.run_performance_test(session, 5)
            await self.run_performance_test(session, 20)
            await self.run_performance_test(session, 50)
        
        # Sonuçları analiz et
        self.analyze_results()
    
    def analyze_results(self):
        """Test sonuçlarını analiz et"""
        print("\n📈 Test Sonuçları Analizi:")
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.get("success")])
        failed_tests = len(self.failed_tests)
        
        print(f"   • Toplam Test: {total_tests}")
        print(f"   • Başarılı: {successful_tests}")
        print(f"   • Başarısız: {failed_tests}")
        print(f"   • Başarı Oranı: {(successful_tests/total_tests)*100:.1f}%")
        
        # Method dağılımı
        methods = {}
        for result in self.results:
            if result.get("success"):
                method = result.get("method", "unknown")
                methods[method] = methods.get(method, 0) + 1
        
        print(f"\n📊 Method Dağılımı:")
        for method, count in methods.items():
            print(f"   • {method}: {count}")
        
        # Başarısız testleri detaylandır
        if self.failed_tests:
            print(f"\n❌ Başarısız Testler ({len(self.failed_tests)}):")
            for test in self.failed_tests[:10]:  # İlk 10 tanesini göster
                print(f"   • '{test['question']}' -> {test.get('answer', test.get('error', 'UNKNOWN'))}")
        
        # Performance özeti
        if self.performance_stats:
            print(f"\n⚡ Performance Özeti:")
            for i, stats in enumerate(self.performance_stats):
                print(f"   • Test {i+1}: {stats['requests_per_second']:.1f} RPS, {stats['avg_response_time_ms']:.1f}ms avg")
    
    def save_results(self, filename: str = "test_results.json"):
        """Sonuçları kaydet"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": len([r for r in self.results if r.get("success")]),
                "failed_tests": len(self.failed_tests)
            },
            "results": self.results,
            "failed_tests": self.failed_tests,
            "performance_stats": self.performance_stats
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Sonuçlar kaydedildi: {filename}")

async def main():
    test_suite = ComprehensiveTestSuite()
    await test_suite.run_all_tests()
    test_suite.save_results()

if __name__ == "__main__":
    asyncio.run(main())