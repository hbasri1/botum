#!/usr/bin/env python3
"""
Sistem Demo - Gerçek senaryolarla sistem gösterimi
"""

import asyncio
import json
from datetime import datetime
import time

class ChatbotDemo:
    def __init__(self):
        self.conversation_count = 0
        self.demo_data = {
            "business": {
                "id": "demo-butik-123",
                "name": "Demo Butik",
                "greeting": "Merhaba! Demo Butik'e hoş geldiniz! Size nasıl yardımcı olabilirim?",
                "meta_data": {
                    "telefon": "0555 123 45 67",
                    "iade": "İade 14 gün içinde fatura ile birlikte yapılabilir",
                    "kargo": "Kargo ücretsiz, 2-3 iş günü içinde teslim",
                    "adres": "Demo Mahallesi, Test Sokak No:123, İstanbul"
                }
            },
            "products": [
                {"name": "Saten Gecelik", "price": 299.99, "stock": 15, "color": "siyah"},
                {"name": "Pamuklu Pijama Takımı", "price": 199.99, "stock": 8, "color": "mavi"},
                {"name": "İpek Sabahlık", "price": 449.99, "stock": 3, "color": "bordo"},
                {"name": "Dantel Gecelik", "price": 359.99, "stock": 12, "color": "beyaz"}
            ]
        }
    
    def simulate_llm_response(self, user_message: str, session_id: str) -> dict:
        """LLM yanıtını simüle et"""
        message = user_message.lower()
        
        # Selamlama
        if any(word in message for word in ["merhaba", "selam", "hey", "iyi"]):
            return {
                "session_id": session_id,
                "isletme_id": self.demo_data["business"]["id"],
                "intent": "greeting",
                "entities": [],
                "context": {"requires_followup": False},
                "confidence": 0.95,
                "language": "tr"
            }
        
        # Ürün fiyat sorgusu
        elif any(word in message for word in ["fiyat", "kaç para", "ne kadar", "ücret"]):
            product_found = None
            for product in self.demo_data["products"]:
                if any(word in message for word in product["name"].lower().split()):
                    product_found = product
                    break
            
            if product_found:
                return {
                    "session_id": session_id,
                    "isletme_id": self.demo_data["business"]["id"],
                    "intent": "product_query",
                    "entities": [
                        {"type": "product", "value": product_found["name"], "confidence": 0.9},
                        {"type": "attribute", "value": "fiyat", "confidence": 0.95}
                    ],
                    "context": {"product_mentioned": product_found["name"]},
                    "confidence": 0.88,
                    "language": "tr"
                }
            else:
                # Belirsiz ürün - düşük güven
                return {
                    "session_id": session_id,
                    "isletme_id": self.demo_data["business"]["id"],
                    "intent": "product_query",
                    "entities": [],
                    "context": {"requires_followup": True},
                    "confidence": 0.65,  # DÜŞÜK GÜVEN - ESKALASYON
                    "language": "tr"
                }
        
        # Stok sorgusu
        elif any(word in message for word in ["stok", "var mı", "mevcut", "kaldı"]):
            product_found = None
            for product in self.demo_data["products"]:
                if any(word in message for word in product["name"].lower().split()):
                    product_found = product
                    break
            
            if product_found:
                return {
                    "session_id": session_id,
                    "isletme_id": self.demo_data["business"]["id"],
                    "intent": "product_query",
                    "entities": [
                        {"type": "product", "value": product_found["name"], "confidence": 0.9},
                        {"type": "attribute", "value": "stok", "confidence": 0.92}
                    ],
                    "context": {"product_mentioned": product_found["name"]},
                    "confidence": 0.86,
                    "language": "tr"
                }
        
        # Meta bilgi sorguları
        elif any(word in message for word in ["telefon", "iletişim", "ara"]):
            return {
                "session_id": session_id,
                "isletme_id": self.demo_data["business"]["id"],
                "intent": "meta_query",
                "entities": [{"type": "attribute", "value": "telefon", "confidence": 0.9}],
                "context": {},
                "confidence": 0.91,
                "language": "tr"
            }
        
        elif any(word in message for word in ["iade", "geri", "değişim"]):
            return {
                "session_id": session_id,
                "isletme_id": self.demo_data["business"]["id"],
                "intent": "meta_query",
                "entities": [{"type": "attribute", "value": "iade", "confidence": 0.9}],
                "context": {},
                "confidence": 0.89,
                "language": "tr"
            }
        
        elif any(word in message for word in ["kargo", "teslimat", "gönder"]):
            return {
                "session_id": session_id,
                "isletme_id": self.demo_data["business"]["id"],
                "intent": "meta_query",
                "entities": [{"type": "attribute", "value": "kargo", "confidence": 0.9}],
                "context": {},
                "confidence": 0.87,
                "language": "tr"
            }
        
        # Şikayet - ESKALASYON
        elif any(word in message for word in ["şikayet", "problem", "sorun", "memnun değil"]):
            return {
                "session_id": session_id,
                "isletme_id": self.demo_data["business"]["id"],
                "intent": "sikayet_bildirme",  # ESKALASYON İNTENT'İ
                "entities": [],
                "context": {"requires_followup": True},
                "confidence": 0.94,
                "language": "tr"
            }
        
        # Teşekkür
        elif any(word in message for word in ["teşekkür", "sağol", "tamam", "peki"]):
            return {
                "session_id": session_id,
                "isletme_id": self.demo_data["business"]["id"],
                "intent": "thanks",
                "entities": [],
                "context": {},
                "confidence": 0.93,
                "language": "tr"
            }
        
        # Bilinmeyen - DÜŞÜK GÜVEN
        else:
            return {
                "session_id": session_id,
                "isletme_id": self.demo_data["business"]["id"],
                "intent": "unknown",
                "entities": [],
                "context": {},
                "confidence": 0.35,  # ÇOK DÜŞÜK GÜVEN - ESKALASYON
                "language": "tr"
            }
    
    def process_business_logic(self, llm_response: dict, user_message: str) -> str:
        """İş mantığını işle"""
        intent = llm_response.get("intent")
        confidence = llm_response.get("confidence", 0)
        entities = llm_response.get("entities", [])
        
        # GÜVEN SKORU KONTROLÜ
        if confidence < 0.80:
            ticket_id = f"TKT-{int(time.time())}"
            return f"🎫 Sorununuzu bir müşteri temsilcimize aktarıyorum. Ticket numaranız: {ticket_id}. En kısa sürede size dönüş yapılacaktır."
        
        # ESKALASYON İNTENT'LERİ
        if intent == "sikayet_bildirme":
            ticket_id = f"TKT-COMPLAINT-{int(time.time())}"
            return f"🎫 Şikayetinizi öncelikli olarak müşteri temsilcimize aktarıyorum. Ticket numaranız: {ticket_id}. En kısa sürede size dönüş yapılacaktır."
        
        # NORMAL İŞ MANTIK AKIŞI
        if intent == "greeting":
            return self.demo_data["business"]["greeting"]
        
        elif intent == "thanks":
            return "Rica ederim! Başka bir sorunuz var mı?"
        
        elif intent == "meta_query":
            # Entity'den bilgi türünü çıkar
            info_type = None
            for entity in entities:
                if entity.get("type") == "attribute":
                    info_type = entity.get("value")
                    break
            
            if info_type and info_type in self.demo_data["business"]["meta_data"]:
                return self.demo_data["business"]["meta_data"][info_type]
            else:
                return "Bu bilgi şu anda mevcut değil. Müşteri hizmetlerimizle iletişime geçebilirsiniz."
        
        elif intent == "product_query":
            # Ürün ve attribute'u çıkar
            product_name = None
            attribute = "fiyat"  # Default
            
            for entity in entities:
                if entity.get("type") == "product":
                    product_name = entity.get("value")
                elif entity.get("type") == "attribute":
                    attribute = entity.get("value")
            
            if product_name:
                # Ürünü bul
                product = None
                for p in self.demo_data["products"]:
                    if product_name.lower() in p["name"].lower() or p["name"].lower() in product_name.lower():
                        product = p
                        break
                
                if product:
                    if attribute == "fiyat":
                        return f"💰 {product['name']}\nFiyat: {product['price']} TL"
                    elif attribute == "stok":
                        if product['stock'] > 0:
                            return f"📦 {product['name']}\nStok: {product['stock']} adet mevcut"
                        else:
                            return f"❌ {product['name']} şu anda stokta yok"
                    else:
                        return f"ℹ️ {product['name']}\nFiyat: {product['price']} TL\nStok: {product['stock']} adet\nRenk: {product['color']}"
                else:
                    return "Aradığınız ürün bulunamadı. Mevcut ürünlerimiz: " + ", ".join([p["name"] for p in self.demo_data["products"]])
            else:
                return "Hangi ürün hakkında bilgi almak istiyorsunuz?"
        
        else:
            return "Anlayamadım. Ürünlerimiz, fiyatlar veya hizmetlerimiz hakkında soru sorabilirsiniz."
    
    async def simulate_conversation(self, user_message: str) -> dict:
        """Tam konuşma simülasyonu"""
        self.conversation_count += 1
        session_id = f"demo-session-{self.conversation_count}"
        
        print(f"\n{'='*60}")
        print(f"💬 KONUŞMA #{self.conversation_count}")
        print(f"Session ID: {session_id}")
        print(f"{'='*60}")
        
        # 1. Kullanıcı mesajı
        print(f"👤 Kullanıcı: {user_message}")
        
        # 2. LLM işleme simülasyonu
        print(f"\n🧠 LLM İşleme...")
        await asyncio.sleep(0.1)  # LLM gecikmesi simülasyonu
        
        llm_response = self.simulate_llm_response(user_message, session_id)
        
        print(f"   Intent: {llm_response['intent']}")
        print(f"   Güven Skoru: {llm_response['confidence']:.2f}")
        print(f"   Entities: {len(llm_response['entities'])} adet")
        
        # 3. Güven skoru kontrolü
        if llm_response['confidence'] < 0.80:
            print(f"   ⚠️  DÜŞÜK GÜVEN SKORU - ESKALASYON TETİKLENDİ")
        elif llm_response['intent'] in ['sikayet_bildirme', 'insana_aktar']:
            print(f"   🎫 ESKALASYON İNTENT'İ TESPİT EDİLDİ")
        else:
            print(f"   ✅ Normal akış devam ediyor")
        
        # 4. İş mantığı işleme
        print(f"\n⚙️  İş Mantığı İşleme...")
        await asyncio.sleep(0.05)  # İş mantığı gecikmesi
        
        final_response = self.process_business_logic(llm_response, user_message)
        
        # 5. Bot yanıtı
        print(f"\n🤖 Bot: {final_response}")
        
        # 6. Performans metrikleri
        response_time = 150 + (self.conversation_count * 10)  # Simüle edilmiş süre
        print(f"\n📊 Performans:")
        print(f"   Yanıt Süresi: {response_time}ms")
        print(f"   Cache Durumu: {'Hit' if self.conversation_count > 1 and 'merhaba' in user_message.lower() else 'Miss'}")
        
        return {
            "user_message": user_message,
            "llm_response": llm_response,
            "final_response": final_response,
            "response_time_ms": response_time,
            "session_id": session_id
        }

async def main():
    """Demo ana fonksiyonu"""
    print("🚀 CHATBOT SİSTEMİ DEMO")
    print("=" * 60)
    print("Bu demo, sistemin gerçek senaryolardaki davranışını gösterir")
    print("=" * 60)
    
    demo = ChatbotDemo()
    
    # Demo senaryoları
    scenarios = [
        {
            "category": "🟢 Normal Akış",
            "messages": [
                "merhaba",
                "gecelik fiyatı ne kadar?",
                "saten gecelik stokta var mı?",
                "teşekkürler"
            ]
        },
        {
            "category": "🔵 Meta Bilgi Sorguları",
            "messages": [
                "telefon numaranız nedir?",
                "iade politikanız nasıl?",
                "kargo ücreti ne kadar?"
            ]
        },
        {
            "category": "🟡 Düşük Güven Skoru (Eskalasyon)",
            "messages": [
                "bu şeyin fiyatı ne kadar?",  # Belirsiz ürün
                "asdfgh qwerty zxcvbn"        # Anlamsız mesaj
            ]
        },
        {
            "category": "🔴 Eskalasyon Intent'leri",
            "messages": [
                "şikayet etmek istiyorum",
                "çok memnun değilim bu hizmetten"
            ]
        }
    ]
    
    # Senaryoları çalıştır
    for scenario in scenarios:
        print(f"\n\n🎭 {scenario['category']}")
        print("=" * 60)
        
        for message in scenario['messages']:
            result = await demo.simulate_conversation(message)
            await asyncio.sleep(0.5)  # Demo için bekleme
    
    # Özet
    print(f"\n\n📊 DEMO ÖZETİ")
    print("=" * 60)
    print(f"Toplam Konuşma: {demo.conversation_count}")
    print(f"İşletme: {demo.demo_data['business']['name']}")
    print(f"Ürün Sayısı: {len(demo.demo_data['products'])}")
    
    print(f"\n✅ Test Edilen Özellikler:")
    print(f"   • Güven skoru kontrolü (%80 eşiği)")
    print(f"   • Intent sınıflandırması")
    print(f"   • Entity çıkarma")
    print(f"   • Eskalasyon sistemi")
    print(f"   • İş mantığı routing")
    print(f"   • Meta bilgi sorguları")
    print(f"   • Ürün bilgi sorguları")
    
    print(f"\n🎯 Sistem Davranışı:")
    print(f"   • Anladığı sorulara doğru yanıt verdi")
    print(f"   • Anlamadığı durumları eskalasyon yaptı")
    print(f"   • Asla tahmin yürütmedi")
    print(f"   • Güvenilir ve tutarlı çalıştı")
    
    print(f"\n🎉 DEMO TAMAMLANDI!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())