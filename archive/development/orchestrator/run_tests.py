#!/usr/bin/env python3
"""
Test Runner - Tüm testleri sırayla çalıştırır
"""

import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
    
    def run_command(self, command: str, description: str, timeout: int = 30) -> bool:
        """Komut çalıştır ve sonucu kaydet"""
        print(f"\n🔄 {description}...")
        print(f"Komut: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                print(f"✅ {description} başarılı")
                if result.stdout.strip():
                    print("Çıktı:")
                    print(result.stdout)
                self.test_results[description] = "BAŞARILI"
                return True
            else:
                print(f"❌ {description} başarısız (exit code: {result.returncode})")
                if result.stderr.strip():
                    print("Hata:")
                    print(result.stderr)
                if result.stdout.strip():
                    print("Çıktı:")
                    print(result.stdout)
                self.test_results[description] = "BAŞARISIZ"
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} zaman aşımı ({timeout}s)")
            self.test_results[description] = "ZAMAN AŞIMI"
            return False
        except Exception as e:
            print(f"❌ {description} hatası: {str(e)}")
            self.test_results[description] = f"HATA: {str(e)}"
            return False
    
    async def run_async_test(self, test_file: str, description: str) -> bool:
        """Async test dosyasını çalıştır"""
        print(f"\n🔄 {description}...")
        
        try:
            # Test dosyasını import et ve çalıştır
            if test_file == "test_comprehensive.py":
                from test_comprehensive import main as test_main
            elif test_file == "test_escalation.py":
                from test_escalation import main as test_main
            else:
                print(f"❌ Bilinmeyen test dosyası: {test_file}")
                return False
            
            await test_main()
            print(f"✅ {description} başarılı")
            self.test_results[description] = "BAŞARILI"
            return True
            
        except Exception as e:
            print(f"❌ {description} hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            self.test_results[description] = f"HATA: {str(e)}"
            return False
    
    def check_dependencies(self) -> bool:
        """Gerekli bağımlılıkları kontrol et"""
        print("🔍 Bağımlılık Kontrolü...")
        
        # Python paketlerini kontrol et
        required_packages = [
            "fastapi", "uvicorn", "redis", "asyncpg", 
            "pydantic", "aiohttp", "python-json-logger"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package} eksik")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\nEksik paketleri yüklemek için:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def check_services(self) -> bool:
        """Gerekli servisleri kontrol et"""
        print("\n🔍 Servis Kontrolü...")
        
        # Redis kontrolü
        redis_ok = self.run_command(
            "docker ps | grep redis || echo 'Redis container bulunamadı'",
            "Redis Container Kontrolü",
            timeout=10
        )
        
        # PostgreSQL kontrolü
        postgres_ok = self.run_command(
            "docker ps | grep postgres || echo 'PostgreSQL container bulunamadı'",
            "PostgreSQL Container Kontrolü", 
            timeout=10
        )
        
        if not redis_ok or not postgres_ok:
            print("\nServisleri başlatmak için:")
            print("docker-compose up -d")
            return False
        
        return True
    
    def print_summary(self):
        """Test sonuçlarını özetle"""
        print("\n" + "=" * 60)
        print("📊 TEST SONUÇLARI ÖZETİ")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result == "BAŞARILI")
        
        for test_name, result in self.test_results.items():
            if result == "BAŞARILI":
                icon = "✅"
            elif result == "ZAMAN AŞIMI":
                icon = "⏰"
            else:
                icon = "❌"
            
            print(f"{icon} {test_name}: {result}")
        
        print("\n" + "=" * 60)
        print(f"Toplam Test: {total_tests}")
        print(f"Başarılı: {successful_tests}")
        print(f"Başarısız: {total_tests - successful_tests}")
        print(f"Başarı Oranı: %{(successful_tests/total_tests)*100:.1f}")
        print("=" * 60)
        
        return successful_tests == total_tests

async def main():
    """Ana test runner fonksiyonu"""
    print("🚀 KAPSAMLI TEST RUNNER")
    print("=" * 60)
    
    runner = TestRunner()
    
    # 1. Bağımlılık kontrolü
    if not runner.check_dependencies():
        print("\n❌ Bağımlılık kontrolü başarısız!")
        return False
    
    # 2. Servis kontrolü
    if not runner.check_services():
        print("\n⚠️  Servisler çalışmıyor, yine de testlere devam ediliyor...")
    
    # 3. Unit testler
    print("\n" + "=" * 60)
    print("🧪 UNIT TESTLER")
    print("=" * 60)
    
    await runner.run_async_test("test_escalation.py", "Eskalasyon Sistemi Testleri")
    await runner.run_async_test("test_comprehensive.py", "Kapsamlı Entegrasyon Testleri")
    
    # 4. Linting ve kod kalitesi
    print("\n" + "=" * 60)
    print("🔍 KOD KALİTESİ KONTROLLERI")
    print("=" * 60)
    
    # Python syntax kontrolü
    runner.run_command(
        "python -m py_compile app/main.py services/*.py",
        "Python Syntax Kontrolü"
    )
    
    # Import kontrolü
    runner.run_command(
        "python -c 'from app.main import app; print(\"✅ Import başarılı\")'",
        "Import Kontrolü"
    )
    
    # 5. Docker build testi
    print("\n" + "=" * 60)
    print("🐳 DOCKER TESTLER")
    print("=" * 60)
    
    runner.run_command(
        "docker-compose config",
        "Docker Compose Konfigürasyon Kontrolü"
    )
    
    # 6. API testleri (eğer sunucu çalışıyorsa)
    print("\n" + "=" * 60)
    print("🌐 API TESTLER")
    print("=" * 60)
    
    # Sunucu kontrolü
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print("✅ API sunucusu çalışıyor, API testleri başlatılıyor...")
                    
                    # API testlerini çalıştır
                    runner.run_command(
                        "python test_api_endpoints.py",
                        "API Endpoint Testleri",
                        timeout=60
                    )
                else:
                    print("⚠️  API sunucusu yanıt veriyor ama sağlıklı değil")
    except:
        print("⚠️  API sunucusu çalışmıyor, API testleri atlanıyor")
        print("   Sunucuyu başlatmak için: python -m app.main")
    
    # 7. Sonuçları özetle
    success = runner.print_summary()
    
    if success:
        print("\n🎉 TÜM TESTLER BAŞARILI!")
        return True
    else:
        print("\n❌ BAZI TESTLER BAŞARISIZ!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)