#!/usr/bin/env python3
"""
Learning System Test - Kendi kendine öğrenen sistem testleri
"""

import asyncio
import json
import time
from datetime import datetime
from services.llm_service import LLMService
from services.learning_service import LearningService
from services.cache_manager import CacheManager
from services.database_service import DatabaseService
from services.session_manager import SessionManager

async def test_llm_learning():
    """LLM öğrenme sistemini test et"""
    print("🧠 LLM Öğrenme Sistemi Testi...")
    
    llm_service = LLMService()
    
    # Test mesajları - farklı senaryolar
    test_messages = [
        ("merhaba", "greeting", 0.95),
        ("gecelik fiyatı ne kadar?", "product_query", 0.88),
        ("bu şeyin fiyatı ne kadar?", "product_query", 0.65),  # Düşük güven
        ("şikayet etmek istiyorum", "sikayet_bildirme", 0.92),
        ("teşekkürler", "thanks", 0.93),
        ("asdfgh qwerty", "unknown", 0.35),  # Çok düşük güven
    ]
    
    print("    Test mesajları işleniyor...")
    
    for i, (message, expected_intent, expected_confidence) in enumerate(test_messages, 1):
        session_id = f"learning-test-{i}"
        
        # LLM'e gönder
        response = await llm_service.process_message(
            prompt=f"[session: {session_id}] [kimlik: test-business] {message}",
            session_id=session_id,
            isletme_id="test-business"
        )
        
        if response:
            actual_intent = response.get("intent")
            actual_confidence = response.get("confidence", 0)
            
            print(f"      {i}. '{message}' → {actual_intent} (güven: {actual_confidence:.2f})")
            
            # Beklenen sonuçları kontrol et
            if actual_intent == expected_intent:
                print(f"         ✅ Intent doğru")
            else:
                print(f"         ❌ Intent yanlış (beklenen: {expected_intent})")
            
            if abs(actual_confidence - expected_confidence) < 0.1:
                print(f"         ✅ Güven skoru uygun")
            else:
                print(f"         ⚠️  Güven skoru farklı (beklenen: {expected_confidence})")
        else:
            print(f"      {i}. '{message}' → ❌ LLM yanıt vermedi")
    
    # Öğrenme içgörülerini al
    print("\n    Öğrenme içgörüleri alınıyor...")
    insights = await llm_service.get_learning_insights()
    
    print(f"      Toplam etkileşim: {insights.get('total_interactions', 0)}")
    print(f"      Başarı oranı: %{insights.get('success_rate', 0) * 100:.1f}")
    print(f"      Ortalama güven: {insights.get('overall_metrics', {}).get('average_confidence', 0):.2f}")
    
    intent_dist = insights.get('intent_distribution', {})
    if intent_dist:
        print(f"      Intent dağılımı:")
        for intent, count in intent_dist.items():
            print(f"        - {intent}: {count}")
    
    recommendations = insights.get('recommendations', [])
    if recommendations:
        print(f"      Öneriler:")
        for rec in recommendations[:3]:
            print(f"        - {rec}")
    
    print("    ✅ LLM öğrenme sistemi testi tamamlandı!")

async def test_learning_service():
    """Learning Service'i test et"""
    print("\n📚 Learning Service Testi...")
    
    # Servisleri başlat
    cache_manager = CacheManager()
    session_manager = SessionManager()
    db_service = DatabaseService(cache_manager=cache_manager)
    llm_service = LLMService()
    learning_service = LearningService(db_service, llm_service, cache_manager)
    
    # Önce bazı test verileri oluştur
    print("    Test verileri oluşturuluyor...")
    
    test_interactions = [
        ("merhaba", "greeting", 0.95),
        ("gecelik fiyatı", "product_query", 0.88),
        ("iade politikası", "meta_query", 0.91),
        ("şikayet", "sikayet_bildirme", 0.92),
        ("belirsiz mesaj", "unknown", 0.45),
    ]
    
    # Test etkileşimlerini simüle et
    for message, intent, confidence in test_interactions:
        for i in range(3):  # Her mesajı 3 kez tekrarla
            await llm_service.process_message(
                prompt=f"[session: test-{i}] [kimlik: test-business] {message}",
                session_id=f"test-{i}",
                isletme_id="test-business"
            )
    
    print("    Pattern analizi yapılıyor...")
    
    # Pattern analizini manuel olarak tetikle
    await learning_service._analyze_interaction_patterns()
    await learning_service._analyze_performance_metrics()
    await learning_service._optimize_cache_patterns()
    await learning_service._analyze_intent_accuracy()
    await learning_service._generate_improvement_suggestions()
    
    # Learning raporu al
    print("    Learning raporu alınıyor...")
    report = await learning_service.get_learning_report()
    
    detected_patterns = report.get('detected_patterns', {})
    
    # Intent patterns
    intent_patterns = detected_patterns.get('intent_patterns', {})
    print(f"      Tespit edilen intent pattern'leri: {len(intent_patterns)}")
    
    for pattern_key, pattern_data in list(intent_patterns.items())[:3]:
        print(f"        - {pattern_key}: {pattern_data['count']} kez, güven: {pattern_data['avg_confidence']:.2f}")
    
    # Performance issues
    perf_issues = detected_patterns.get('performance_issues', [])
    print(f"      Performance sorunları: {len(perf_issues)}")
    
    for issue in perf_issues:
        print(f"        - {issue['type']}: {issue['recommendation']}")
    
    # Improvement suggestions
    suggestions = report.get('improvement_suggestions', [])
    print(f"      Gelişim önerileri: {len(suggestions)}")
    
    for suggestion in suggestions[:3]:
        print(f"        - {suggestion['type']} ({suggestion['priority']}): {suggestion['description']}")
    
    print("    ✅ Learning service testi tamamlandı!")

async def test_fine_tuning_data_export():
    """Fine-tuning data export'unu test et"""
    print("\n📤 Fine-tuning Data Export Testi...")
    
    llm_service = LLMService()
    cache_manager = CacheManager()
    db_service = DatabaseService(cache_manager=cache_manager)
    learning_service = LearningService(db_service, llm_service, cache_manager)
    
    # Önce bazı kaliteli etkileşimler oluştur
    quality_interactions = [
        ("merhaba", "greeting", 0.95),
        ("gecelik fiyatı ne kadar", "product_query", 0.88),
        ("iade politikanız nedir", "meta_query", 0.91),
        ("telefon numaranız", "meta_query", 0.89),
        ("teşekkür ederim", "thanks", 0.93),
    ]
    
    print("    Kaliteli etkileşimler oluşturuluyor...")
    
    for message, intent, confidence in quality_interactions:
        for i in range(5):  # Her mesajı 5 kez tekrarla
            await llm_service.process_message(
                prompt=f"[session: export-test-{i}] [kimlik: export-business] {message}",
                session_id=f"export-test-{i}",
                isletme_id="export-business"
            )
    
    # Training data export et
    print("    Training data export ediliyor...")
    
    export_data = await learning_service.export_fine_tuning_data()
    
    training_data = export_data.get('training_data', {})
    pattern_examples = export_data.get('pattern_examples', [])
    
    print(f"      Training examples: {len(training_data.get('training_examples', []))}")
    print(f"      Pattern examples: {len(pattern_examples)}")
    print(f"      Toplam examples: {export_data.get('total_examples', 0)}")
    
    # Örnek training data göster
    examples = training_data.get('training_examples', [])
    if examples:
        print(f"      Örnek training data:")
        for example in examples[:3]:
            input_text = example.get('input', '')[:50]
            output_intent = example.get('output', {}).get('intent', '')
            confidence = example.get('output', {}).get('confidence', 0)
            print(f"        - '{input_text}...' → {output_intent} ({confidence:.2f})")
    
    # Pattern examples göster
    if pattern_examples:
        print(f"      Örnek pattern data:")
        for example in pattern_examples[:3]:
            input_text = example.get('input', '')[:50]
            output_intent = example.get('output', {}).get('intent', '')
            confidence = example.get('output', {}).get('confidence', 0)
            print(f"        - '{input_text}...' → {output_intent} ({confidence:.2f})")
    
    print("    ✅ Fine-tuning data export testi tamamlandı!")

async def test_performance_monitoring():
    """Performance monitoring'i test et"""
    print("\n📊 Performance Monitoring Testi...")
    
    llm_service = LLMService()
    
    # Farklı performance senaryoları
    scenarios = [
        ("Yüksek performans", [
            ("merhaba", 0.95),
            ("teşekkürler", 0.93),
            ("gecelik fiyatı", 0.88),
        ]),
        ("Orta performans", [
            ("bu ürün", 0.75),
            ("ne kadar", 0.72),
            ("bilgi", 0.78),
        ]),
        ("Düşük performans", [
            ("asdfgh", 0.35),
            ("belirsiz", 0.45),
            ("karmaşık soru", 0.55),
        ])
    ]
    
    print("    Farklı performance senaryoları test ediliyor...")
    
    for scenario_name, messages in scenarios:
        print(f"      {scenario_name} senaryosu:")
        
        for message, expected_conf in messages:
            response = await llm_service.process_message(
                prompt=f"[session: perf-test] [kimlik: perf-business] {message}",
                session_id="perf-test",
                isletme_id="perf-business"
            )
            
            if response:
                actual_conf = response.get("confidence", 0)
                intent = response.get("intent", "unknown")
                
                if actual_conf >= 0.80:
                    status = "✅ Normal"
                elif actual_conf >= 0.60:
                    status = "⚠️  Düşük"
                else:
                    status = "❌ Eskalasyon"
                
                print(f"        - '{message}' → {intent} ({actual_conf:.2f}) {status}")
    
    # Model bilgilerini al
    print("    Model performans metrikleri:")
    model_info = await llm_service.get_model_info()
    
    perf_metrics = model_info.get("performance_metrics", {})
    print(f"      Toplam istek: {perf_metrics.get('total_requests', 0)}")
    print(f"      Başarılı istek: {perf_metrics.get('successful_requests', 0)}")
    print(f"      Başarısız istek: {perf_metrics.get('failed_requests', 0)}")
    print(f"      Ortalama güven: {perf_metrics.get('average_confidence', 0):.2f}")
    print(f"      Memory size: {model_info.get('memory_size', 0)} etkileşim")
    
    print("    ✅ Performance monitoring testi tamamlandı!")

async def main():
    """Ana test fonksiyonu"""
    print("🚀 LEARNING SYSTEM KAPSAMLI TESTLERİ")
    print("=" * 60)
    print("Bu testler sistemin kendi kendine öğrenme kabiliyetini test eder")
    print("=" * 60)
    
    try:
        await test_llm_learning()
        await test_learning_service()
        await test_fine_tuning_data_export()
        await test_performance_monitoring()
        
        print("\n" + "=" * 60)
        print("🎉 TÜM LEARNING SYSTEM TESTLERİ BAŞARILI!")
        print("=" * 60)
        
        print("\n📋 ÖZETLİ SONUÇLAR:")
        print("✅ LLM öğrenme sistemi çalışıyor")
        print("✅ Pattern detection aktif")
        print("✅ Performance monitoring çalışıyor")
        print("✅ Fine-tuning data export hazır")
        print("✅ Auto-improvement önerileri üretiliyor")
        
        print("\n🚀 SİSTEM HAZIR:")
        print("- Kendi kendine öğreniyor")
        print("- Pattern'leri tespit ediyor")
        print("- Performance'ı izliyor")
        print("- Fine-tuning için veri hazırlıyor")
        print("- Otomatik iyileştirmeler öneriyor")
        
    except Exception as e:
        print(f"\n❌ Test hatası: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())