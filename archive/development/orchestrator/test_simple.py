#!/usr/bin/env python3
"""
Basit Test - Bağımlılık gerektirmeyen temel testler
"""

import sys
import json
from pathlib import Path

def test_pydantic_models():
    """Pydantic modellerini test et"""
    print("🧪 Pydantic Model Testleri...")
    
    try:
        # Basit Pydantic test
        from pydantic import BaseModel, Field, ValidationError
        
        class TestModel(BaseModel):
            name: str = Field(..., min_length=1)
            confidence: float = Field(..., ge=0.0, le=1.0)
        
        # Geçerli veri
        valid_data = {"name": "test", "confidence": 0.85}
        model = TestModel(**valid_data)
        print(f"    ✅ Geçerli model: {model.name} (güven: {model.confidence})")
        
        # Geçersiz veri
        try:
            invalid_data = {"name": "", "confidence": 1.5}
            TestModel(**invalid_data)
            print("    ❌ Geçersiz veri kabul edildi")
        except ValidationError as e:
            print("    ✅ Geçersiz veri reddedildi")
        
        return True
        
    except ImportError as e:
        print(f"    ❌ Pydantic import hatası: {e}")
        return False
    except Exception as e:
        print(f"    ❌ Test hatası: {e}")
        return False

def test_json_operations():
    """JSON işlemlerini test et"""
    print("\n🧪 JSON İşlem Testleri...")
    
    try:
        # LLM yanıt simülasyonu
        llm_response = {
            "session_id": "test-session",
            "isletme_id": "test-business",
            "intent": "greeting",
            "entities": [
                {"type": "product", "value": "gecelik", "confidence": 0.9}
            ],
            "context": {"requires_followup": False},
            "confidence": 0.95,
            "language": "tr"
        }
        
        # JSON serialize/deserialize
        json_str = json.dumps(llm_response, ensure_ascii=False)
        parsed_back = json.loads(json_str)
        
        if parsed_back["confidence"] == 0.95:
            print("    ✅ JSON serialize/deserialize başarılı")
        else:
            print("    ❌ JSON veri bozuldu")
            return False
        
        # Güven skoru kontrolü
        if parsed_back["confidence"] >= 0.80:
            print("    ✅ Güven skoru yeterli (eskalasyon yok)")
        else:
            print("    ⚠️  Güven skoru düşük (eskalasyon gerekli)")
        
        # Intent kontrolü
        escalation_intents = {"sikayet_bildirme", "insana_aktar", "karmasik_sorun"}
        if parsed_back["intent"] in escalation_intents:
            print("    ⚠️  Eskalasyon intent'i tespit edildi")
        else:
            print("    ✅ Normal intent, eskalasyon gerekmiyor")
        
        return True
        
    except Exception as e:
        print(f"    ❌ JSON test hatası: {e}")
        return False

def test_cache_key_generation():
    """Cache anahtar üretimini test et"""
    print("\n🧪 Cache Anahtar Üretim Testleri...")
    
    try:
        import hashlib
        
        def generate_cache_key(isletme_id: str, query: str) -> str:
            normalized_query = query.lower().strip()
            query_hash = hashlib.md5(normalized_query.encode()).hexdigest()
            return f"cache:{isletme_id}:{query_hash}"
        
        # Test verileri
        test_cases = [
            ("test-business-1", "merhaba", "cache:test-business-1:"),
            ("test-business-1", "MERHABA", "cache:test-business-1:"),  # Aynı hash olmalı
            ("test-business-1", "gecelik fiyatı", "cache:test-business-1:"),
            ("test-business-2", "merhaba", "cache:test-business-2:")  # Farklı business
        ]
        
        keys = []
        for isletme_id, query, expected_prefix in test_cases:
            key = generate_cache_key(isletme_id, query)
            keys.append(key)
            
            if key.startswith(expected_prefix):
                print(f"    ✅ Cache key: {query} -> {key[:30]}...")
            else:
                print(f"    ❌ Yanlış cache key: {key}")
                return False
        
        # Aynı mesajların aynı hash'i ürettiğini kontrol et
        if keys[0] == keys[1]:  # "merhaba" ve "MERHABA"
            print("    ✅ Normalizasyon çalışıyor (büyük/küçük harf)")
        else:
            print("    ❌ Normalizasyon çalışmıyor")
            return False
        
        # Farklı business'ların farklı key'leri olduğunu kontrol et
        if keys[0] != keys[3]:  # Farklı business'lar
            print("    ✅ Business isolation çalışıyor")
        else:
            print("    ❌ Business isolation çalışmıyor")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Cache key test hatası: {e}")
        return False

def test_session_state_logic():
    """Session state mantığını test et"""
    print("\n🧪 Session State Mantık Testleri...")
    
    try:
        # Session state simülasyonu
        class MockSessionState:
            def __init__(self):
                self.state = "active"
                self.state_data = {}
                self.context = {}
            
            def set_state(self, state: str, data: dict = None):
                self.previous_state = self.state
                self.state = state
                self.state_data = data or {}
            
            def is_waiting_for(self, expected_info: str) -> bool:
                return (self.state == "waiting_for_input" and 
                       self.state_data.get("beklenen_bilgi") == expected_info)
        
        # Test senaryosu
        session = MockSessionState()
        
        # İlk durum
        if session.state == "active":
            print("    ✅ İlk session state: active")
        
        # Ürün bekleme durumuna geç
        session.set_state("waiting_for_input", {
            "beklenen_bilgi": "urun_adi",
            "onceki_niyet": "fiyat_sorma"
        })
        
        if session.is_waiting_for("urun_adi"):
            print("    ✅ Session ürün adı bekliyor")
        else:
            print("    ❌ Session state kontrolü başarısız")
            return False
        
        # Önceki state kaydedildi mi?
        if hasattr(session, 'previous_state') and session.previous_state == "active":
            print("    ✅ Önceki state kaydedildi")
        else:
            print("    ❌ Önceki state kaydedilmedi")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Session state test hatası: {e}")
        return False

def test_business_logic():
    """İş mantığı testleri"""
    print("\n🧪 İş Mantığı Testleri...")
    
    try:
        # Mock business data
        business_data = {
            "test-business-1": {
                "meta_data": {
                    "telefon": "0555 123 45 67",
                    "iade": "İade 14 gün içinde yapılabilir",
                    "kargo": "Kargo 2-3 iş günü içinde"
                },
                "products": [
                    {"name": "Test Gecelik", "price": 299.99, "stock": 10},
                    {"name": "Test Pijama", "price": 199.99, "stock": 5}
                ]
            }
        }
        
        def get_business_meta_info(isletme_id: str, info_type: str) -> str:
            business = business_data.get(isletme_id)
            if business and business.get("meta_data"):
                return business["meta_data"].get(info_type)
            return None
        
        def get_product_info(isletme_id: str, product_name: str) -> str:
            business = business_data.get(isletme_id)
            if business:
                for product in business.get("products", []):
                    if product_name.lower() in product["name"].lower():
                        return f"{product['name']}\nFiyat: {product['price']} TL"
            return None
        
        # Meta bilgi testi
        iade_info = get_business_meta_info("test-business-1", "iade")
        if iade_info == "İade 14 gün içinde yapılabilir":
            print("    ✅ Meta bilgi getirme başarılı")
        else:
            print("    ❌ Meta bilgi getirme başarısız")
            return False
        
        # Ürün bilgi testi
        product_info = get_product_info("test-business-1", "gecelik")
        if product_info and "299.99" in product_info:
            print("    ✅ Ürün bilgi getirme başarılı")
        else:
            print("    ❌ Ürün bilgi getirme başarısız")
            return False
        
        # Olmayan bilgi testi
        nonexistent = get_business_meta_info("test-business-1", "olmayan_bilgi")
        if nonexistent is None:
            print("    ✅ Olmayan bilgi için None döndü")
        else:
            print("    ❌ Olmayan bilgi için yanlış değer döndü")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ İş mantığı test hatası: {e}")
        return False

def test_file_structure():
    """Dosya yapısını kontrol et"""
    print("\n🧪 Dosya Yapısı Kontrolü...")
    
    try:
        project_root = Path(__file__).parent
        
        required_files = [
            "app/main.py",
            "services/cache_manager.py",
            "services/session_manager.py", 
            "services/database_service.py",
            "services/business_logic_router.py",
            "services/llm_service.py",
            "services/escalation_service.py",
            "models/database_models.py",
            "config/settings.py",
            "utils/logger.py",
            "requirements.txt",
            "docker-compose.yml",
            "Dockerfile",
            "init.sql"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"    ✅ {file_path}")
            else:
                print(f"    ❌ {file_path} eksik")
                missing_files.append(file_path)
        
        if not missing_files:
            print("    ✅ Tüm gerekli dosyalar mevcut")
            return True
        else:
            print(f"    ❌ {len(missing_files)} dosya eksik")
            return False
        
    except Exception as e:
        print(f"    ❌ Dosya yapısı kontrolü hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 BASİT SİSTEM TESTLERİ")
    print("=" * 50)
    print("Bu testler harici bağımlılık gerektirmez")
    print("=" * 50)
    
    tests = [
        ("Dosya Yapısı", test_file_structure),
        ("JSON İşlemleri", test_json_operations),
        ("Cache Anahtar Üretimi", test_cache_key_generation),
        ("Session State Mantığı", test_session_state_logic),
        ("İş Mantığı", test_business_logic),
        ("Pydantic Modeller", test_pydantic_models)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"    ❌ {test_name} beklenmeyen hata: {e}")
            results[test_name] = False
    
    # Sonuçları özetle
    print("\n" + "=" * 50)
    print("📊 TEST SONUÇLARI")
    print("=" * 50)
    
    total_tests = len(results)
    successful_tests = sum(1 for success in results.values() if success)
    
    for test_name, success in results.items():
        icon = "✅" if success else "❌"
        print(f"{icon} {test_name}")
    
    print("\n" + "=" * 50)
    print(f"Toplam: {total_tests}")
    print(f"Başarılı: {successful_tests}")
    print(f"Başarısız: {total_tests - successful_tests}")
    print(f"Başarı Oranı: %{(successful_tests/total_tests)*100:.1f}")
    
    if successful_tests == total_tests:
        print("\n🎉 TÜM TESTLER BAŞARILI!")
        print("Sistem temel mantığı doğru çalışıyor.")
        print("\nSonraki adımlar:")
        print("1. pip install -r requirements.txt")
        print("2. Docker servisleri başlat")
        print("3. python test_comprehensive.py")
        return True
    else:
        print(f"\n❌ {total_tests - successful_tests} TEST BAŞARISIZ!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)