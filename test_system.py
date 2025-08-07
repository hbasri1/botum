#!/usr/bin/env python3
"""
Sistem Test Scripti
RAG tabanlı ürün arama sistemini test eder
"""

import json
import time
from improved_final_mvp_system import ImprovedFinalMVPChatbot

def test_chatbot_system():
    """Chatbot sistemini kapsamlı test et"""
    print("🚀 RAG Tabanlı Ürün Arama Sistemi Test")
    print("=" * 60)
    
    # Initialize chatbot
    try:
        bot = ImprovedFinalMVPChatbot()
        print("✅ Sistem başarıyla başlatıldı")
        
        # Health check
        health = bot.health_check()
        print(f"🏥 Health Status: {health['status']}")
        print(f"📦 Ürün sayısı: {len(bot.products)}")
        print(f"🔍 RAG arama: {'✅' if health['rag_search_available'] else '❌'}")
        print(f"🤖 Gemini: {'✅' if health['gemini_available'] else '❌'}")
        
    except Exception as e:
        print(f"❌ Sistem başlatılamadı: {e}")
        return
    
    # Test queries
    test_queries = [
        {
            "query": "hamile pijama arıyorum",
            "expected_intent": "product_search",
            "description": "Hamile ürün arama"
        },
        {
            "query": "siyah dantelli gecelik var mı",
            "expected_intent": "product_search",
            "description": "Renk ve özellik bazlı arama"
        },
        {
            "query": "büyük beden gecelik",
            "expected_intent": "product_search", 
            "description": "Beden bazlı arama"
        },
        {
            "query": "1 numaralı ürünün fiyatı nedir",
            "expected_intent": "followup",
            "description": "Takip sorusu"
        },
        {
            "query": "telefon numaranız nedir",
            "expected_intent": "phone_inquiry",
            "description": "İletişim bilgisi"
        },
        {
            "query": "merhaba",
            "expected_intent": "greeting",
            "description": "Selamlama"
        },
        {
            "query": "teşekkürler",
            "expected_intent": "thanks",
            "description": "Teşekkür"
        }
    ]
    
    print(f"\n🧪 {len(test_queries)} Test Senaryosu Çalıştırılıyor...")
    print("-" * 60)
    
    results = []
    total_time = 0
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. {test['description']}")
        print(f"👤 Soru: {test['query']}")
        
        start_time = time.time()
        response = bot.chat(test['query'])
        end_time = time.time()
        
        response_time = end_time - start_time
        total_time += response_time
        
        # Check intent
        intent_correct = response.intent == test['expected_intent']
        intent_status = "✅" if intent_correct else "❌"
        
        print(f"🤖 Cevap: {response.message[:100]}...")
        print(f"📊 Intent: {response.intent} {intent_status} (Beklenen: {test['expected_intent']})")
        print(f"🎯 Confidence: {response.confidence:.2f}")
        print(f"📦 Ürün sayısı: {response.products_found}")
        print(f"⏱️ Süre: {response_time:.3f}s")
        
        results.append({
            'query': test['query'],
            'intent_correct': intent_correct,
            'confidence': response.confidence,
            'products_found': response.products_found,
            'response_time': response_time,
            'response_length': len(response.message)
        })
    
    # Summary
    print(f"\n📊 TEST SONUÇLARI")
    print("=" * 60)
    
    correct_intents = sum(1 for r in results if r['intent_correct'])
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_response_time = total_time / len(results)
    total_products = sum(r['products_found'] for r in results)
    
    print(f"✅ Doğru Intent: {correct_intents}/{len(results)} ({correct_intents/len(results)*100:.1f}%)")
    print(f"🎯 Ortalama Confidence: {avg_confidence:.2f}")
    print(f"⏱️ Ortalama Yanıt Süresi: {avg_response_time:.3f}s")
    print(f"📦 Toplam Bulunan Ürün: {total_products}")
    
    # System stats
    stats = bot.get_stats()
    print(f"\n🔧 SİSTEM İSTATİSTİKLERİ")
    print("-" * 30)
    print(f"Toplam İstek: {stats['total_requests']}")
    print(f"Başarı Oranı: {stats['success_rate']:.1f}%")
    print(f"Cache Hit Rate: {stats['smart_cache_stats']['hit_rate']:.1f}%")
    print(f"Gemini Çağrı: {stats['gemini_calls']}")
    print(f"Fallback Çağrı: {stats['fallback_calls']}")
    
    # Performance evaluation
    print(f"\n⚡ PERFORMANS DEĞERLENDİRMESİ")
    print("-" * 40)
    
    if avg_response_time < 0.5:
        print("🟢 Yanıt Süresi: Mükemmel (< 0.5s)")
    elif avg_response_time < 1.0:
        print("🟡 Yanıt Süresi: İyi (< 1.0s)")
    else:
        print("🔴 Yanıt Süresi: Yavaş (> 1.0s)")
    
    if correct_intents/len(results) >= 0.9:
        print("🟢 Intent Doğruluğu: Mükemmel (≥ 90%)")
    elif correct_intents/len(results) >= 0.8:
        print("🟡 Intent Doğruluğu: İyi (≥ 80%)")
    else:
        print("🔴 Intent Doğruluğu: Geliştirilmeli (< 80%)")
    
    if avg_confidence >= 0.8:
        print("🟢 Confidence: Yüksek (≥ 0.8)")
    elif avg_confidence >= 0.6:
        print("🟡 Confidence: Orta (≥ 0.6)")
    else:
        print("🔴 Confidence: Düşük (< 0.6)")
    
    print(f"\n🎉 Test tamamlandı! Sistem {'✅ HAZIR' if correct_intents/len(results) >= 0.8 else '⚠️ GELİŞTİRİLMELİ'}")

if __name__ == "__main__":
    test_chatbot_system()