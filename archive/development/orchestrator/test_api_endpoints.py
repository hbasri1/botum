#!/usr/bin/env python3
"""
API Endpoint Test Scripti
Gerçek HTTP istekleri ile tüm endpoint'leri test eder
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_endpoint(self):
        """Health endpoint testi"""
        print("🧪 Health Endpoint Testi...")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"    ✅ Health check başarılı")
                    print(f"    Status: {data.get('status')}")
                    
                    services = data.get('services', {})
                    for service, status in services.items():
                        status_icon = "✅" if status else "❌"
                        print(f"    {status_icon} {service}: {status}")
                else:
                    print(f"    ❌ Health check başarısız: {response.status}")
        
        except Exception as e:
            print(f"    ❌ Health endpoint hatası: {str(e)}")
    
    async def test_webhook_endpoint(self):
        """Webhook endpoint testi"""
        print("\n🧪 Webhook Endpoint Testi...")
        
        test_cases = [
            {
                "name": "Selamlama",
                "payload": {
                    "mesaj_metni": "merhaba",
                    "kullanici_id": "test-user-1",
                    "isletme_id": "test-business-1",
                    "platform": "test"
                },
                "expected_success": True
            },
            {
                "name": "Ürün Sorgusu",
                "payload": {
                    "mesaj_metni": "gecelik fiyatı ne kadar?",
                    "kullanici_id": "test-user-2", 
                    "isletme_id": "test-business-1",
                    "platform": "whatsapp"
                },
                "expected_success": True
            },
            {
                "name": "Eksik Alan",
                "payload": {
                    "mesaj_metni": "test",
                    # kullanici_id eksik
                    "isletme_id": "test-business-1"
                },
                "expected_success": False
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {test_case['name']}")
            
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/webhook",
                    json=test_case['payload'],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('success') == test_case['expected_success']:
                            print(f"    ✅ Beklenen sonuç alındı")
                            print(f"    Yanıt süresi: {response_time:.1f}ms")
                            print(f"    Session ID: {data.get('session_id', 'N/A')}")
                            print(f"    Mesaj: {data.get('message', '')[:100]}...")
                        else:
                            print(f"    ❌ Beklenmeyen sonuç: {data.get('success')}")
                    
                    elif response.status == 422 and not test_case['expected_success']:
                        print(f"    ✅ Validation hatası beklenen şekilde alındı")
                    
                    else:
                        print(f"    ❌ Beklenmeyen HTTP status: {response.status}")
                        error_text = await response.text()
                        print(f"    Hata: {error_text[:200]}...")
            
            except Exception as e:
                print(f"    ❌ İstek hatası: {str(e)}")
    
    async def test_admin_endpoints(self):
        """Admin endpoint'lerini test et"""
        print("\n🧪 Admin Endpoint Testleri...")
        
        # Cache invalidation test
        print("\n  Cache Invalidation Testi:")
        try:
            async with self.session.post(
                f"{self.base_url}/admin/cache/invalidate/test-business-1"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"    ✅ Cache invalidation: {data.get('message')}")
                else:
                    print(f"    ❌ Cache invalidation başarısız: {response.status}")
        except Exception as e:
            print(f"    ❌ Cache invalidation hatası: {str(e)}")
        
        # Product cache invalidation test
        print("\n  Product Cache Invalidation Testi:")
        try:
            async with self.session.post(
                f"{self.base_url}/admin/cache/invalidate-product/test-business-1/product-1"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"    ✅ Product cache invalidation: {data.get('message')}")
                else:
                    print(f"    ❌ Product cache invalidation başarısız: {response.status}")
        except Exception as e:
            print(f"    ❌ Product cache invalidation hatası: {str(e)}")
        
        # Cache stats test
        print("\n  Cache Stats Testi:")
        try:
            async with self.session.get(
                f"{self.base_url}/admin/cache/stats/test-business-1"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"    ✅ Cache stats alındı")
                    print(f"    Cached queries: {data.get('total_cached_queries', 0)}")
                    print(f"    Memory usage: {data.get('memory_usage_mb', 0)} MB")
                else:
                    print(f"    ❌ Cache stats başarısız: {response.status}")
        except Exception as e:
            print(f"    ❌ Cache stats hatası: {str(e)}")
        
        # Product update test
        print("\n  Product Update Testi:")
        try:
            update_payload = {
                "price": 399.99,
                "stock_quantity": 15
            }
            
            async with self.session.put(
                f"{self.base_url}/admin/products/test-business-1/product-1",
                json=update_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"    ✅ Product update: {data.get('message')}")
                else:
                    print(f"    ❌ Product update başarısız: {response.status}")
                    error_text = await response.text()
                    print(f"    Hata: {error_text}")
        except Exception as e:
            print(f"    ❌ Product update hatası: {str(e)}")
        
        # Business meta update test
        print("\n  Business Meta Update Testi:")
        try:
            meta_payload = {
                "info_type": "iade",
                "new_value": "İade 30 gün içinde yapılabilir"
            }
            
            async with self.session.put(
                f"{self.base_url}/admin/business/test-business-1/meta",
                json=meta_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"    ✅ Business meta update: {data.get('message')}")
                else:
                    print(f"    ❌ Business meta update başarısız: {response.status}")
                    error_text = await response.text()
                    print(f"    Hata: {error_text}")
        except Exception as e:
            print(f"    ❌ Business meta update hatası: {str(e)}")
    
    async def test_stats_endpoint(self):
        """Stats endpoint testi"""
        print("\n🧪 Stats Endpoint Testi...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/stats/test-business-1"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"    ✅ Stats alındı")
                    print(f"    30 günlük etkileşim: {data.get('total_interactions_30d', 0)}")
                    
                    intent_dist = data.get('intent_distribution', [])
                    if intent_dist:
                        print(f"    Intent dağılımı:")
                        for intent_data in intent_dist[:3]:  # İlk 3'ü göster
                            print(f"      - {intent_data.get('intent')}: {intent_data.get('count')}")
                else:
                    print(f"    ❌ Stats başarısız: {response.status}")
        except Exception as e:
            print(f"    ❌ Stats hatası: {str(e)}")
    
    async def test_performance(self):
        """Performans testi"""
        print("\n🧪 Performans Testi...")
        
        # Aynı mesajı birden fazla kez gönder (cache test)
        test_payload = {
            "mesaj_metni": "merhaba",
            "kullanici_id": "perf-test-user",
            "isletme_id": "test-business-1",
            "platform": "test"
        }
        
        response_times = []
        
        for i in range(5):
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/webhook",
                    json=test_payload
                ) as response:
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status == 200:
                        data = await response.json()
                        server_time = data.get('response_time_ms', 0)
                        print(f"    İstek {i+1}: {response_time:.1f}ms (server: {server_time}ms)")
                    else:
                        print(f"    İstek {i+1}: Hata {response.status}")
                        
            except Exception as e:
                print(f"    İstek {i+1}: Exception {str(e)}")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"\n    Performans Özeti:")
            print(f"    Ortalama: {avg_time:.1f}ms")
            print(f"    En hızlı: {min_time:.1f}ms")
            print(f"    En yavaş: {max_time:.1f}ms")
            
            # Cache etkisini kontrol et
            if len(response_times) >= 2 and response_times[1] < response_times[0]:
                print(f"    ✅ Cache etkisi gözlemlendi (2. istek daha hızlı)")
            else:
                print(f"    ⚠️  Cache etkisi net değil")

async def main():
    """Ana test fonksiyonu"""
    print("🚀 API ENDPOINT TESTLERİ")
    print("=" * 50)
    print(f"Test URL: {BASE_URL}")
    print("=" * 50)
    
    # Sunucunun çalıştığını kontrol et
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print("✅ Sunucu çalışıyor")
                else:
                    print(f"⚠️  Sunucu yanıt veriyor ama status: {response.status}")
    except Exception as e:
        print(f"❌ Sunucu çalışmıyor: {str(e)}")
        print("\nSunucuyu başlatmak için:")
        print("  cd orchestrator")
        print("  docker-compose up -d")
        print("  python -m app.main")
        return
    
    print("\n" + "=" * 50)
    
    # Testleri çalıştır
    async with APITester() as tester:
        await tester.test_health_endpoint()
        await tester.test_webhook_endpoint()
        await tester.test_admin_endpoints()
        await tester.test_stats_endpoint()
        await tester.test_performance()
    
    print("\n" + "=" * 50)
    print("🎉 API ENDPOINT TESTLERİ TAMAMLANDI!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())