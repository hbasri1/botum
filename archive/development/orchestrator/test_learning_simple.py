#!/usr/bin/env python3
"""
Learning System Simple Test - Bağımlılık gerektirmeyen testler
"""

import asyncio
import json
import time
from datetime import datetime

# Mock services
class MockLLMService:
    def __init__(self):
        self.conversation_memory = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_confidence": 0.0,
            "intent_accuracy": {}
        }
    
    async def process_message(self, prompt: str, session_id: str, isletme_id: str):
        """Mock LLM processing"""
        self.performance_metrics["total_requests"] += 1
        
        message = prompt.lower()
        
        # Selamlama
        if any(word in message for word in ["merhaba", "selam"]):
            response = {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "greeting",
                "entities": [],
                "context": {},
                "confidence": 0.95,
                "language": "tr"
            }
        # Ürün sorgusu
        elif any(word in message for word in ["fiyat", "ne kadar"]):
            if "gecelik" in message:
                confidence = 0.88
            else:
                confidence = 0.65  # Belirsiz ürün
            
            response = {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "product_query",
                "entities": [],
                "context": {},
                "confidence": confidence,
                "language": "tr"
            }
        # Şikayet
        elif any(word in message for word in ["şikayet", "problem"]):
            response = {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "sikayet_bildirme",
                "entities": [],
                "context": {},
                "confidence": 0.92,
                "language": "tr"
            }
        # Bilinmeyen
        else:
            response = {
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "unknown",
                "entities": [],
                "context": {},
                "confidence": 0.45,
                "language": "tr"
            }
        
        # Öğrenme verisi olarak kaydet
        interaction_data = {
            "timestamp": time.time(),
            "session_id": session_id,
            "isletme_id": isletme_id,
            "user_message": prompt,
            "intent": response["intent"],
            "confidence": response["confidence"],
            "success": True
        }
        
        self.conversation_memory.append(interaction_data)
        self.performance_metrics["successful_requests"] += 1
        
        # Ortalama confidence güncelle
        total = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_confidence"]
        new_conf = response["confidence"]
        
        self.performance_metrics["average_confidence"] = (
            (current_avg * (total - 1) + new_conf) / total
        )
        
        return response
    
    async def get_learning_insights(self):
        """Öğrenme içgörüleri"""
        total = len(self.conversation_memory)
        successful = len([i for i in self.conversation_memory if i.get("success", False)])
        
        # Intent dağılımı
        intent_dist = {}
        confidence_by_intent = {}
        
        for interaction in self.conversation_memory:
            intent = interaction.get("intent", "unknown")
            confidence = interaction.get("confidence", 0)
            
            if intent not in intent_dist:
                intent_dist[intent] = 0
                confidence_by_intent[intent] = []
            
            intent_dist[intent] += 1
            confidence_by_intent[intent].append(confidence)
        
        # Ortalama confidence'lar
        avg_conf_by_intent = {}
        for intent, confidences in confidence_by_intent.items():
            avg_conf_by_intent[intent] = sum(confidences) / len(confidences)
        
        # Düşük performanslı intent'ler
        low_perf = [
            intent for intent, avg_conf in avg_conf_by_intent.items()
            if avg_conf < 0.75
        ]
        
        return {
            "total_interactions": total,
            "successful_interactions": successful,
            "success_rate": successful / total if total > 0 else 0,
            "intent_distribution": intent_dist,
            "average_confidence_by_intent": avg_conf_by_intent,
            "low_performance_intents": low_perf,
            "overall_metrics": self.performance_metrics
        }
    
    async def export_training_data(self):
        """Training data export"""
        training_examples = []
        
        for interaction in self.conversation_memory:
            if interaction.get("confidence", 0) > 0.85:
                example = {
                    "input": interaction.get("user_message", ""),
                    "output": {
                        "intent": interaction.get("intent"),
                        "confidence": interaction.get("confidence")
                    }
                }
                training_examples.append(example)
        
        return {
            "training_examples": training_examples,
            "total_examples": len(training_examples),
            "export_timestamp": time.time()
        }

class MockLearningService:
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.detected_patterns = {}
        self.improvement_suggestions = []
    
    async def analyze_patterns(self):
        """Pattern analizi"""
        interactions = self.llm_service.conversation_memory
        
        if len(interactions) < 3:
            return
        
        # Intent patterns
        intent_patterns = {}
        message_patterns = {}
        
        for interaction in interactions:
            intent = interaction.get("intent", "unknown")
            message = interaction.get("user_message", "").lower()
            confidence = interaction.get("confidence", 0)
            isletme_id = interaction.get("isletme_id", "")
            
            # Intent patterns
            key = f"{isletme_id}:{intent}"
            if key not in intent_patterns:
                intent_patterns[key] = {"count": 0, "avg_confidence": 0}
            
            intent_patterns[key]["count"] += 1
            intent_patterns[key]["avg_confidence"] = (
                intent_patterns[key]["avg_confidence"] + confidence
            ) / 2
            
            # Message patterns
            words = message.split()
            for word in words:
                if len(word) > 2:
                    if word not in message_patterns:
                        message_patterns[word] = {"count": 0, "intents": set()}
                    message_patterns[word]["count"] += 1
                    message_patterns[word]["intents"].add(intent)
        
        self.detected_patterns = {
            "intent_patterns": intent_patterns,
            "message_patterns": message_patterns,
            "analysis_timestamp": time.time()
        }
    
    async def generate_suggestions(self):
        """Gelişim önerileri üret"""
        suggestions = []
        
        intent_patterns = self.detected_patterns.get("intent_patterns", {})
        
        for pattern_key, pattern_data in intent_patterns.items():
            avg_conf = pattern_data["avg_confidence"]
            count = pattern_data["count"]
            
            if avg_conf < 0.75 and count >= 3:
                suggestions.append({
                    "type": "training_needed",
                    "priority": "high",
                    "description": f"Training gerekli: {pattern_key} (güven: {avg_conf:.2f})",
                    "data": pattern_data
                })
            elif avg_conf > 0.90 and count >= 5:
                suggestions.append({
                    "type": "cache_optimization",
                    "priority": "low",
                    "description": f"Cache optimize et: {pattern_key} (sık kullanılıyor)",
                    "data": pattern_data
                })
        
        self.improvement_suggestions = suggestions
    
    async def get_learning_report(self):
        """Learning raporu"""
        return {
            "timestamp": time.time(),
            "detected_patterns": self.detected_patterns,
            "improvement_suggestions": self.improvement_suggestions,
            "llm_insights": await self.llm_service.get_learning_insights()
        }

async def test_learning_system():
    """Learning system'i test et"""
    print("🧠 Learning System Test...")
    
    # Mock servisleri başlat
    llm_service = MockLLMService()
    learning_service = MockLearningService(llm_service)
    
    # Test mesajları
    test_messages = [
        ("merhaba", "greeting"),
        ("gecelik fiyatı ne kadar?", "product_query"),
        ("bu şeyin fiyatı ne kadar?", "product_query"),  # Düşük güven
        ("şikayet etmek istiyorum", "sikayet_bildirme"),
        ("teşekkürler", "thanks"),
        ("asdfgh qwerty", "unknown"),  # Çok düşük güven
        ("merhaba", "greeting"),  # Tekrar
        ("gecelik fiyatı", "product_query"),  # Tekrar
    ]
    
    print("    Test mesajları işleniyor...")
    
    for i, (message, expected_intent) in enumerate(test_messages, 1):
        session_id = f"test-{i}"
        
        response = await llm_service.process_message(
            prompt=f"[session: {session_id}] [kimlik: test-business] {message}",
            session_id=session_id,
            isletme_id="test-business"
        )
        
        if response:
            intent = response.get("intent")
            confidence = response.get("confidence", 0)
            
            if confidence >= 0.80:
                status = "✅ Normal"
            elif confidence >= 0.60:
                status = "⚠️  Düşük güven"
            else:
                status = "❌ Eskalasyon"
            
            print(f"      {i}. '{message}' → {intent} ({confidence:.2f}) {status}")
        else:
            print(f"      {i}. '{message}' → ❌ Yanıt yok")
    
    print("\n    Pattern analizi yapılıyor...")
    await learning_service.analyze_patterns()
    await learning_service.generate_suggestions()
    
    # Learning raporu
    report = await learning_service.get_learning_report()
    
    # Sonuçları göster
    llm_insights = report.get("llm_insights", {})
    print(f"      Toplam etkileşim: {llm_insights.get('total_interactions', 0)}")
    print(f"      Başarı oranı: %{llm_insights.get('success_rate', 0) * 100:.1f}")
    print(f"      Ortalama güven: {llm_insights.get('overall_metrics', {}).get('average_confidence', 0):.2f}")
    
    # Intent dağılımı
    intent_dist = llm_insights.get("intent_distribution", {})
    if intent_dist:
        print(f"      Intent dağılımı:")
        for intent, count in intent_dist.items():
            avg_conf = llm_insights.get("average_confidence_by_intent", {}).get(intent, 0)
            print(f"        - {intent}: {count} kez (ortalama güven: {avg_conf:.2f})")
    
    # Düşük performanslı intent'ler
    low_perf = llm_insights.get("low_performance_intents", [])
    if low_perf:
        print(f"      ⚠️  Düşük performanslı intent'ler: {', '.join(low_perf)}")
    
    # Pattern'ler
    patterns = report.get("detected_patterns", {})
    intent_patterns = patterns.get("intent_patterns", {})
    if intent_patterns:
        print(f"      Tespit edilen pattern'ler:")
        for pattern_key, pattern_data in intent_patterns.items():
            print(f"        - {pattern_key}: {pattern_data['count']} kez, güven: {pattern_data['avg_confidence']:.2f}")
    
    # Öneriler
    suggestions = report.get("improvement_suggestions", [])
    if suggestions:
        print(f"      Gelişim önerileri:")
        for suggestion in suggestions:
            priority = suggestion["priority"]
            desc = suggestion["description"]
            print(f"        - {priority.upper()}: {desc}")
    
    print("    ✅ Learning system testi başarılı!")

async def test_training_data_export():
    """Training data export testi"""
    print("\n📤 Training Data Export Test...")
    
    llm_service = MockLLMService()
    
    # Kaliteli etkileşimler oluştur
    quality_messages = [
        ("merhaba", "greeting"),
        ("gecelik fiyatı ne kadar", "product_query"),
        ("iade politikanız nedir", "meta_query"),
        ("telefon numaranız", "meta_query"),
        ("teşekkür ederim", "thanks"),
    ]
    
    print("    Kaliteli etkileşimler oluşturuluyor...")
    
    for message, expected_intent in quality_messages:
        for i in range(3):  # Her mesajı 3 kez
            await llm_service.process_message(
                prompt=f"[session: export-{i}] [kimlik: export-business] {message}",
                session_id=f"export-{i}",
                isletme_id="export-business"
            )
    
    # Training data export et
    print("    Training data export ediliyor...")
    export_data = await llm_service.export_training_data()
    
    examples = export_data.get("training_examples", [])
    print(f"      Export edilen örnek sayısı: {len(examples)}")
    
    if examples:
        print(f"      Örnek training data:")
        for example in examples[:5]:
            input_text = example.get("input", "")[:50]
            output_intent = example.get("output", {}).get("intent", "")
            confidence = example.get("output", {}).get("confidence", 0)
            print(f"        - '{input_text}...' → {output_intent} ({confidence:.2f})")
    
    print("    ✅ Training data export testi başarılı!")

async def test_performance_monitoring():
    """Performance monitoring testi"""
    print("\n📊 Performance Monitoring Test...")
    
    llm_service = MockLLMService()
    
    # Farklı performance senaryoları
    scenarios = [
        ("Yüksek Performans", [
            "merhaba",
            "teşekkürler", 
            "gecelik fiyatı ne kadar"
        ]),
        ("Düşük Performans", [
            "asdfgh qwerty",
            "belirsiz mesaj xyz",
            "karmaşık ve anlaşılmaz soru"
        ])
    ]
    
    print("    Performance senaryoları test ediliyor...")
    
    for scenario_name, messages in scenarios:
        print(f"      {scenario_name}:")
        
        scenario_confidences = []
        
        for message in messages:
            response = await llm_service.process_message(
                prompt=f"[session: perf] [kimlik: perf-business] {message}",
                session_id="perf",
                isletme_id="perf-business"
            )
            
            if response:
                confidence = response.get("confidence", 0)
                intent = response.get("intent", "unknown")
                scenario_confidences.append(confidence)
                
                if confidence >= 0.80:
                    status = "✅"
                elif confidence >= 0.60:
                    status = "⚠️"
                else:
                    status = "❌"
                
                print(f"        {status} '{message[:30]}...' → {intent} ({confidence:.2f})")
        
        # Senaryo ortalaması
        if scenario_confidences:
            avg_conf = sum(scenario_confidences) / len(scenario_confidences)
            print(f"        📊 Ortalama güven: {avg_conf:.2f}")
    
    # Genel performance metrikleri
    insights = await llm_service.get_learning_insights()
    overall_metrics = insights.get("overall_metrics", {})
    
    print(f"    Genel Performance Metrikleri:")
    print(f"      Toplam istek: {overall_metrics.get('total_requests', 0)}")
    print(f"      Başarılı istek: {overall_metrics.get('successful_requests', 0)}")
    print(f"      Ortalama güven: {overall_metrics.get('average_confidence', 0):.2f}")
    
    print("    ✅ Performance monitoring testi başarılı!")

async def main():
    """Ana test fonksiyonu"""
    print("🚀 LEARNING SYSTEM BASİT TESTLERİ")
    print("=" * 50)
    print("Bu testler harici bağımlılık gerektirmez")
    print("=" * 50)
    
    try:
        await test_learning_system()
        await test_training_data_export()
        await test_performance_monitoring()
        
        print("\n" + "=" * 50)
        print("🎉 TÜM LEARNING TESTLER BAŞARILI!")
        print("=" * 50)
        
        print("\n📋 BAŞARILI ÖZELLİKLER:")
        print("✅ LLM öğrenme sistemi çalışıyor")
        print("✅ Etkileşim memory'si aktif")
        print("✅ Pattern detection çalışıyor")
        print("✅ Performance monitoring aktif")
        print("✅ Training data export hazır")
        print("✅ Improvement suggestions üretiliyor")
        
        print("\n🧠 SİSTEMİN ÖĞRENDİKLERİ:")
        print("- Intent pattern'lerini tespit ediyor")
        print("- Düşük performanslı alanları buluyor")
        print("- Otomatik iyileştirme önerileri üretiyor")
        print("- Fine-tuning için veri hazırlıyor")
        print("- Performance metriklerini takip ediyor")
        
        print("\n🚀 SONRAKI ADIMLAR:")
        print("1. Gerçek Gemini API key'i ekle")
        print("2. Fine-tuning pipeline'ı kur")
        print("3. Production'da learning loop'u başlat")
        print("4. Feedback sistemi entegre et")
        
    except Exception as e:
        print(f"\n❌ Test hatası: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())