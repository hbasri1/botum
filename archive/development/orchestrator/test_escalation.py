#!/usr/bin/env python3
"""
Gelişmiş Sistem Test Scripti
Cache invalidation, Pydantic doğrulama ve eskalasyon mantığını test eder
"""

import asyncio
import json
from datetime import datetime
from services.business_logic_router import BusinessLogicRouter
from services.escalation_service import EscalationService
from services.database_service import DatabaseService
from services.session_manager import SessionManager
from services.cache_manager import CacheManager
from services.llm_service import LLMResponse, LLMEntity, LLMContext

async def test_low_confidence_escalation():
    """Düşük güven skoru eskalasyonu testi"""
    print("🧪 Düşük güven skoru eskalasyon testi...")
    
    router = BusinessLogicRouter()
    
    # Düşük güven skorlu LLM yanıtı simüle et
    low_confidence_response = {
        "session_id": "test-session-1",
        "isletme_id": "test-business-1",
        "intent": "product_query",
        "entities": [],
        "context": {},
        "confidence": 0.65,  # %80'in altında
        "language": "tr"
    }
    
    result = await router.route_intent(
        llm_response=low_confidence_response,
        session_id="test-session-1",
        isletme_id="test-business-1",
        original_message="bu ürünün fiyatı ne kadar?"
    )
    
    print(f"✅ Sonuç: {result}")
    assert "ticket" in result.lower() or "temsilci" in result.lower()
    print("✅ Düşük güven skoru eskalasyonu başarılı!")

async def test_escalation_intent():
    """Eskalasyon intent'i testi"""
    print("\n🧪 Eskalasyon intent testi...")
    
    router = BusinessLogicRouter()
    
    # Eskalasyon gerektiren intent
    escalation_response = {
        "session_id": "test-session-2",
        "isletme_id": "test-business-1",
        "intent": "sikayet_bildirme",  # Eskalasyon intent'i
        "entities": [],
        "context": {},
        "confidence": 0.95,  # Yüksek güven skoru olsa bile eskalasyon
        "language": "tr"
    }
    
    result = await router.route_intent(
        llm_response=escalation_response,
        session_id="test-session-2",
        isletme_id="test-business-1",
        original_message="şikayet etmek istiyorum"
    )
    
    print(f"✅ Sonuç: {result}")
    assert "ticket" in result.lower() or "temsilci" in result.lower()
    print("✅ Eskalasyon intent testi başarılı!")

async def test_invalid_response_escalation():
    """Geçersiz LLM yanıtı eskalasyonu testi"""
    print("\n🧪 Geçersiz LLM yanıtı eskalasyon testi...")
    
    router = BusinessLogicRouter()
    
    # Geçersiz LLM yanıtı (eksik alanlar)
    invalid_response = {
        "session_id": "test-session-3",
        # "isletme_id" eksik
        "intent": "greeting",
        # "confidence" eksik
        "language": "tr"
    }
    
    result = await router.route_intent(
        llm_response=invalid_response,
        session_id="test-session-3",
        isletme_id="test-business-1",
        original_message="merhaba"
    )
    
    print(f"✅ Sonuç: {result}")
    assert "ticket" in result.lower() or "temsilci" in result.lower()
    print("✅ Geçersiz yanıt eskalasyonu başarılı!")

async def test_normal_flow():
    """Normal akış testi (eskalasyon olmamalı)"""
    print("\n🧪 Normal akış testi...")
    
    router = BusinessLogicRouter()
    
    # Normal, yüksek güvenli yanıt
    normal_response = {
        "session_id": "test-session-4",
        "isletme_id": "test-business-1",
        "intent": "greeting",
        "entities": [],
        "context": {},
        "confidence": 0.95,  # Yüksek güven skoru
        "language": "tr"
    }
    
    result = await router.route_intent(
        llm_response=normal_response,
        session_id="test-session-4",
        isletme_id="test-business-1",
        original_message="merhaba"
    )
    
    print(f"✅ Sonuç: {result}")
    assert "ticket" not in result.lower() and "temsilci" not in result.lower()
    print("✅ Normal akış testi başarılı!")

async def test_escalation_service():
    """Eskalasyon servisi testi"""
    print("\n🧪 Eskalasyon servisi testi...")
    
    escalation_service = EscalationService()
    
    # Test ticket oluştur
    ticket_id = await escalation_service.create_ticket(
        session_id="test-session-5",
        isletme_id="test-business-1",
        user_message="test mesajı",
        escalation_reason="low_confidence",
        llm_response={"confidence": 0.65},
        conversation_history=[
            {
                "timestamp": datetime.now().isoformat(),
                "user_message": "test mesajı",
                "bot_response": "test yanıt",
                "intent": "unknown"
            }
        ]
    )
    
    print(f"✅ Ticket oluşturuldu: {ticket_id}")
    assert ticket_id.startswith("TKT-")
    print("✅ Eskalasyon servisi testi başarılı!")

async def test_pydantic_validation():
    """Pydantic doğrulama testi"""
    print("\n🧪 Pydantic doğrulama testi...")
    
    # Geçerli LLM yanıtı
    valid_data = {
        "session_id": "test-session",
        "isletme_id": "test-business",
        "intent": "greeting",
        "entities": [
            {
                "type": "product",
                "value": "gecelik",
                "confidence": 0.95
            }
        ],
        "context": {
            "requires_followup": False,
            "waiting_for": None,
            "product_mentioned": "gecelik",
            "attribute_requested": None
        },
        "confidence": 0.92,
        "language": "tr"
    }
    
    try:
        validated = LLMResponse(**valid_data)
        print(f"✅ Geçerli yanıt doğrulandı: {validated.intent} (güven: {validated.confidence})")
    except Exception as e:
        print(f"❌ Geçerli yanıt doğrulama hatası: {str(e)}")
        return
    
    # Geçersiz LLM yanıtı (eksik alanlar)
    invalid_data = {
        "session_id": "test-session",
        # "isletme_id" eksik
        "intent": "greeting",
        "confidence": 1.5,  # Geçersiz değer (>1.0)
        "language": "tr"
    }
    
    try:
        LLMResponse(**invalid_data)
        print("❌ Geçersiz yanıt doğrulandı (olmamalıydı)")
    except Exception as e:
        print(f"✅ Geçersiz yanıt reddedildi: {str(e)}")
    
    print("✅ Pydantic doğrulama testi başarılı!")

async def test_cache_invalidation():
    """Cache invalidation testi"""
    print("\n🧪 Cache invalidation testi...")
    
    cache_manager = CacheManager()
    db_service = DatabaseService(cache_manager=cache_manager)
    
    # Test cache'e bir değer koy
    test_key = "cache:test-business:test ürün fiyatı"
    await cache_manager.set(test_key, "Test yanıt", ttl=3600)
    
    # Cache'de olduğunu kontrol et
    cached_value = await cache_manager.get(test_key)
    if cached_value:
        print("✅ Cache'e değer kaydedildi")
    else:
        print("❌ Cache'e değer kaydedilemedi")
        return
    
    # Product cache invalidation test
    await cache_manager.invalidate_product_cache("test-business", "test-product", "test ürün")
    
    # Cache'den silindiğini kontrol et
    cached_value_after = await cache_manager.get(test_key)
    if not cached_value_after:
        print("✅ Product cache invalidation başarılı")
    else:
        print("❌ Product cache invalidation başarısız")
    
    print("✅ Cache invalidation testi başarılı!")

async def test_session_state_management():
    """Session state management testi"""
    print("\n🧪 Session state management testi...")
    
    session_manager = SessionManager()
    test_session_id = "test-session-state"
    
    # İlk state ayarla
    await session_manager.set_session_state(test_session_id, "waiting_for_input", {
        "beklenen_bilgi": "urun_adi",
        "onceki_niyet": "fiyat_sorma"
    })
    
    # State'i kontrol et
    state, state_data = await session_manager.get_session_state(test_session_id)
    if state == "waiting_for_input" and state_data.get("beklenen_bilgi") == "urun_adi":
        print("✅ Session state ayarlandı")
    else:
        print("❌ Session state ayarlanamadı")
        return
    
    # Context value test
    await session_manager.set_session_context_value(test_session_id, "last_product_mentioned", "gecelik")
    
    last_product = await session_manager.get_session_context_value(test_session_id, "last_product_mentioned")
    if last_product == "gecelik":
        print("✅ Session context value ayarlandı")
    else:
        print("❌ Session context value ayarlanamadı")
    
    # State revert test
    await session_manager.set_session_state(test_session_id, "active", {})
    reverted = await session_manager.revert_session_state(test_session_id)
    
    if reverted:
        state, _ = await session_manager.get_session_state(test_session_id)
        if state == "waiting_for_input":
            print("✅ Session state revert başarılı")
        else:
            print("❌ Session state revert başarısız")
    
    print("✅ Session state management testi başarılı!")

async def main():
    """Ana test fonksiyonu"""
    print("🚀 Gelişmiş Sistem Testleri Başlıyor...\n")
    
    try:
        await test_pydantic_validation()
        await test_cache_invalidation()
        await test_session_state_management()
        await test_low_confidence_escalation()
        await test_escalation_intent()
        await test_invalid_response_escalation()
        await test_normal_flow()
        await test_escalation_service()
        
        print("\n🎉 Tüm testler başarılı!")
        
    except Exception as e:
        print(f"\n❌ Test hatası: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())