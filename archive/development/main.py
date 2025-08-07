
from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
import requests
from dotenv import load_dotenv
from rapidfuzz import fuzz
import re
import sys
import asyncio
from datetime import datetime

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

from orchestrator.services.llm_service import LLMService
from orchestrator.services.function_execution_coordinator import FunctionExecutionCoordinator

load_dotenv()

app = FastAPI()

# Initialize function calling system
llm_service = LLMService(enable_function_calling=True)

# Initialize services for function coordinator
from orchestrator.services.database_service import DatabaseService
from orchestrator.services.function_cache_manager import FunctionCacheManager

db_service = DatabaseService()
cache_manager = FunctionCacheManager()
function_coordinator = FunctionExecutionCoordinator(db_service, cache_manager)

# Ürün ve meta veriyi yükle
with open("data/products.json", "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

with open("data/butik_meta.json", "r", encoding="utf-8") as f:
    BUTIK_META = json.load(f)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class Question(BaseModel):
    question: str

META_KEYS = {
    "telefon": "phone",
    "telefon_numarası": "phone",
    "phone": "phone",
    "site": "site",
    "web": "site",
    "website": "site",
    "iade": "iade_policy",
    "iade_policy": "iade_policy",
    "iade_şartları": "iade_policy",
    "kargo": "shipping_info",
    "shipping_info": "shipping_info",
    "teslimat": "shipping_info",
    "cargo": "shipping_info",
    "kargo_bilgisi": "shipping_info"
}

PRODUCT_ATTRIBUTE_MAP = {
    "fiyat": "final_price",
    "price": "final_price", 
    "final_price": "final_price",
    "renk": "color",
    "color": "color",
    "beden": "size",
    "size": "size",
    "stok": "stock",
    "stock": "stock",
    "kategori": "category",
    "category": "category",
    "kod": "code",
    "code": "code",
    "indirim": "discount",
    "discount": "discount",
    "orijinal_fiyat": "price",
    "original_price": "price"
}

def get_meta_info(attribute):
    """Meta bilgi getir"""
    # Önce direkt anahtar kontrolü
    if attribute in BUTIK_META:
        return BUTIK_META[attribute]
    
    # Sonra mapping kontrolü
    key = META_KEYS.get(attribute.lower())
    if key and key in BUTIK_META:
        return BUTIK_META[key]
    
    print(f"DEBUG: Meta info bulunamadı - attribute: {attribute}, key: {key}")
    return None

def search_products_by_name(product_name, max_results=5):
    """SÜPER GELİŞMİŞ ürün arama - V3 - Çoklu algoritma + fuzzy matching"""
    if not product_name:
        return []
    
    product_name = product_name.lower().strip()
    
    # Arama terimlerindeki anlamsız kelimeleri çıkar
    stop_words = {"ve", "ile", "için", "bir", "bu", "şu", "o"}
    query_words = [word for word in product_name.split() if word not in stop_words and len(word) > 1]
    clean_query = " ".join(query_words)

    scored_products = []
    
    for product in PRODUCTS:
        product_full_name = product["name"].lower()
        
        # 1. Token Set Ratio (kelime sırası bağımsız)
        token_score = fuzz.token_set_ratio(clean_query, product_full_name)
        
        # 2. Partial Ratio (kısmi eşleşme)
        partial_score = fuzz.partial_ratio(clean_query, product_full_name)
        
        # 3. WRatio (weighted ratio - en iyi genel skor)
        wratio_score = fuzz.WRatio(clean_query, product_full_name)
        
        # 4. Kelime bazlı eşleşme skoru
        word_match_score = 0
        matched_words = 0
        for word in query_words:
            if word in product_full_name:
                matched_words += 1
                # Tam kelime eşleşmesi
                if f" {word} " in f" {product_full_name} " or product_full_name.startswith(word) or product_full_name.endswith(word):
                    word_match_score += 25
                else:
                    word_match_score += 15
        
        # Tüm kelimeler eşleşiyorsa bonus
        if matched_words == len(query_words) and len(query_words) > 0:
            word_match_score += 20
        
        # 5. Yazım hatası toleransı - her kelime için
        typo_score = 0
        for word in query_words:
            best_word_score = 0
            for product_word in product_full_name.split():
                word_similarity = fuzz.ratio(word, product_word)
                if word_similarity > best_word_score:
                    best_word_score = word_similarity
            
            # Yüksek benzerlik varsa puan ekle
            if best_word_score > 80:
                typo_score += best_word_score / len(query_words)
        
        # 6. Kategori ve özel durumlar
        category_bonus = 0
        if "hamile" in clean_query or "lohusa" in clean_query:
            if "hamile" in product_full_name or "lohusa" in product_full_name:
                category_bonus = 15
        
        if "afrika" in clean_query or "africa" in clean_query:
            if "afrika" in product_full_name or "africa" in product_full_name:
                category_bonus = 15
        
        if "dantelli" in clean_query or "dantel" in clean_query:
            if "dantelli" in product_full_name or "dantel" in product_full_name:
                category_bonus = 15
        
        # FINAL SCORE HESAPLAMA - Ağırlıklı ortalama
        final_score = (
            token_score * 0.3 +      # Token set ratio
            partial_score * 0.2 +    # Partial ratio  
            wratio_score * 0.25 +    # Weighted ratio
            word_match_score * 0.15 + # Kelime eşleşme
            typo_score * 0.1         # Yazım hatası toleransı
        ) + category_bonus
        
        # Tam eşleşme için ekstra bonus
        if clean_query == product_full_name:
            final_score += 25
        
        # Çok düşük skorları filtrele - DAHA TOLERANSLI
        if final_score > 60:  # 75'ten 60'a düşürdük
            scored_products.append((product, final_score))
            
            # Debug için
            print(f"DEBUG SEARCH: '{clean_query}' -> '{product['name']}' = {final_score:.1f}")

    # Ürünleri skora göre büyükten küçüğe sırala
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    # En iyi sonuçları döndür
    return [product for product, score in scored_products[:max_results]]

def get_available_categories():
    """Mevcut kategorileri döndür"""
    categories = set()
    for product in PRODUCTS:
        name = product["name"].lower()
        if "gecelik" in name:
            categories.add("gecelik")
        if "pijama" in name:
            categories.add("pijama")
        if "sabahlık" in name:
            categories.add("sabahlık")
        if "hamile" in name or "lohusa" in name:
            categories.add("hamile/lohusa")
    return list(categories)

def ask_gemini(prompt: str):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
    headers = { "Content-Type": "application/json" }
    payload = {
        "contents": [{
            "parts": [{ "text": prompt }]
        }],
        "generationConfig": {
            "temperature": 0.3
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

def generate_optimized_prompt(question: str) -> str:
    """Yeni nesil akıllı prompt - %95+ başarı + LLM zekasını kısıtlamadan"""
    
    base_prompt = """Sen profesyonel bir Türk müşteri hizmetleri asistanısın. Müşterinin mesajını analiz et ve ne istediğini anla.

🎯 GÖREV: Müşteri mesajını incele ve hangi hizmeti istediğini belirle. SADECE GEÇERLİ JSON döndür.

📋 HİZMET TİPLERİ:
• greeting: Selamlama, sohbet başlatma
• thanks: Teşekkür, veda, onay ifadeleri  
• meta_query: İşletme bilgileri (telefon, iade, kargo, adres, ödeme)
• product_query: Ürün sorguları (fiyat, stok, özellik, renk, beden)
• clarify: Belirsiz sorular (hangi ürün, daha detay gerekli)
• contact: Anlaşılamayan, karmaşık durumlar

🧠 AKILLI ANALİZ:
- Türkçe günlük konuşma dilini anla
- Ürün adlarındaki Türkçe ekleri NAZIKÇE temizle (geceliği→gecelik, pijamanın→pijama)
- Müşterinin gerçek niyetini yakala
- Belirsizse clarify, çok karmaşıksa contact

📝 JSON FORMAT (ZORUNLU):
{
  "intent": "intent_adı",
  "product": "ürün_adı" | null,
  "attribute": "özellik" | null,
  "original_query": "orijinal_soru"
}

💡 ÖRNEKLER:
"merhaba" → {"intent":"greeting","product":null,"attribute":null,"original_query":"merhaba"}
"çok teşekkürler" → {"intent":"thanks","product":null,"attribute":null,"original_query":"çok teşekkürler"}
"telefon numaranız" → {"intent":"meta_query","product":null,"attribute":"telefon","original_query":"telefon numaranız"}
"iade nasıl yapılır" → {"intent":"meta_query","product":null,"attribute":"iade","original_query":"iade nasıl yapılır"}
"afrika geceliği ne kadar" → {"intent":"product_query","product":"afrika gecelik","attribute":"fiyat","original_query":"afrika geceliği ne kadar"}
"hamile pijama var mı" → {"intent":"product_query","product":"hamile pijama","attribute":"stok","original_query":"hamile pijama var mı"}
"bu ürün ne kadar" → {"intent":"clarify","product":null,"attribute":"fiyat","original_query":"bu ürün ne kadar"}
"pijamaların bedenleri" → {"intent":"product_query","product":"pijama","attribute":"beden","original_query":"pijamaların bedenleri"}
"indirimli ürünleriniz var mı" → {"intent":"product_query","product":"indirimli ürün","attribute":"stok","original_query":"indirimli ürünleriniz var mı"}
"toplu alımda indirim + iade şartları nedir" → {"intent":"contact","product":null,"attribute":"çoklu_sorgu","original_query":"toplu alımda indirim + iade şartları nedir"}

🚨 ÖNEMLİ KURALLAR:
1. Ürün adlarını çok fazla kısaltma (pijama→pijam YANLIŞ!)
2. Eğer soru çok karmaşık veya birden fazla konu içeriyorsa: "intent":"contact"
3. Müşteri "var mı" diyorsa attribute:"stok"
4. Müşteri "ne kadar" diyorsa attribute:"fiyat"
5. Belirsiz ürün sorularında "intent":"clarify"

MÜŞTERI MESAJI: "{question}"
ANALİZ SONUCU:"""
    
    return base_prompt.replace("{question}", question)

# Sabit cevaplar - LLM'e gerek yok
STATIC_RESPONSES = {
    "greeting": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?",
    "thanks": "Rica ederim! Başka sorunuz var mı?",
    "decline": "Bu konuda yardımcı olamam. Ürünlerimiz hakkında sorabilirsiniz.",
    "unknown": "Anlayamadım. Ürün, fiyat, iade veya iletişim hakkında sorabilirsiniz.",
    "contact": "Sorularınız için WhatsApp üzerinden iletişime geçebilirsiniz: 0555 555 55 55\nSorularınız anında cevaplanacaktır! 📱"
}

# Cache sistemi
response_cache = {}

# Context memory - kullanıcının önceki sorularını hatırla
user_context = {}

import logging

def log_failed_query(question, expected_intent, actual_response, error_type):
    """Basit hata loglama"""
    logging.error(f"FAILED_QUERY: question='{question}', expected='{expected_intent}', actual='{actual_response}', error='{error_type}'")

def log_successful_query(question, intent, response):
    """Basit başarılı sorgu loglama"""
    logging.info(f"SUCCESS_QUERY: question='{question}', intent='{intent}', response='{response}'")

def save_user_context(user_id, question, intent, data):
    """Kullanıcının context'ini kaydet"""
    user_context[user_id] = {
        "last_question": question,
        "last_intent": intent,
        "last_data": data,
        "waiting_for": None
    }

def get_user_context(user_id):
    """Kullanıcının context'ini getir"""
    return user_context.get(user_id, {})

# MULTI-SEKTÖR MİMARİSİ - Temel yapı
SECTOR_CONFIGS = {
    "fashion": {
        "name": "Giyim Sektörü",
        "product_attributes": ["name", "price", "color", "size", "stock", "category"],
        "meta_info": ["phone", "iade_policy", "shipping_info", "site"],
        "categories": ["gecelik", "pijama", "elbise", "sabahlık"],
        "greeting": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"
    }
    # Diğer sektörler buraya eklenecek
}


def normalize_turkish_product_name(text):
    """Türkçe ürün adlarını normalize et - V3 - SÜPER AKILLI"""
    if not text:
        return text
    
    text = text.lower().strip()
    
    # 1. Önce yaygın yazım hatalarını düzelt
    typo_corrections = {
        'gecelig': 'gecelik', 'geceliğ': 'gecelik', 'gecelik': 'gecelik',
        'pijam': 'pijama', 'pyjama': 'pijama', 'pajama': 'pijama',
        'afirca': 'afrika', 'afirka': 'afrika', 'africa': 'afrika',
        'danteli': 'dantelli', 'dantel': 'dantelli',
        'hamil': 'hamile', 'lohus': 'lohusa',
        'sabahlk': 'sabahlık', 'sabahlik': 'sabahlık'
    }
    
    for typo, correct in typo_corrections.items():
        text = text.replace(typo, correct)
    
    # 2. Gelişmiş özel durumlar - TAM İFADE EŞLEŞMELERİ
    special_phrases = {
        # Ürün adı + ek kombinasyonları
        'geceliği': 'gecelik', 'geceliğin': 'gecelik', 'geceliğe': 'gecelik',
        'pijamayı': 'pijama', 'pijamanın': 'pijama', 'pijamaya': 'pijama',
        'elbiseyi': 'elbise', 'elbisenin': 'elbise', 'elbiseye': 'elbise',
        'sabahlığı': 'sabahlık', 'sabahlığın': 'sabahlık', 'sabahlığa': 'sabahlık',
        'takımı': 'takım', 'takımın': 'takım', 'takıma': 'takım',
        
        # Fiyat sorgu temizleme
        'fiyatı ne kadar': '', 'fiyatı nedir': '', 'fiyatı': '', 'fiyat': '',
        'ne kadar': '', 'kaç para': '', 'kac para': '', 'kaça': '',
        
        # Stok sorgu temizleme  
        'var mı': '', 'var mi': '', 'varmı': '', 'varmi': '',
        'mevcut mu': '', 'stokta var': '', 'stokta': '',
        
        # Özellik sorgu temizleme
        'bedeni': 'beden', 'bedenleri': 'beden', 'hangi beden': 'beden',
        'rengi': 'renk', 'renkleri': 'renk', 'hangi renk': 'renk',
        
        # Takım ifadeleri
        'pijama takimi': 'pijama takım', 'pijama takımı': 'pijama takım',
        'gecelik takımı': 'gecelik takım', 'sabahlık takımı': 'sabahlık takım'
    }
    
    # Tam ifade eşleşmelerini uygula
    for phrase, replacement in special_phrases.items():
        if phrase in text:
            text = text.replace(phrase, replacement)
    
    # 3. Gereksiz kelimeleri temizle
    noise_words = [
        'lütfen', 'acaba', 'bir', 'bu', 'şu', 'o', 'hangi', 'nasıl',
        'için', 'ile', 've', 'da', 'de', 'ta', 'te', 'ki', 'mi', 'mı'
    ]
    
    words = text.split()
    cleaned_words = []
    
    for word in words:
        # Noise word'leri atla ama çok kısa kalmasın
        if word not in noise_words or len(cleaned_words) == 0:
            cleaned_words.append(word)
    
    # 4. Türkçe ek temizleme - DAHA AKILLI
    final_words = []
    
    for word in cleaned_words:
        original_word = word
        
        # Sadece uzun kelimeler için ek temizleme yap
        if len(word) > 4:
            # En yaygın ekleri temizle (konservatif)
            common_suffixes = [
                'lerini', 'larını', 'lerinin', 'larının',  # Çokluk + iyelik
                'lerim', 'larım', 'lerimiz', 'larımız',    # Çokluk + iyelik
                'ler', 'lar',                              # Çokluk
                'nın', 'nin', 'nun', 'nün',               # İyelik
                'ını', 'ini', 'unu', 'ünü',               # Belirtme
                'ına', 'ine', 'una', 'üne'                # Yönelme
            ]
            
            for suffix in common_suffixes:
                if word.endswith(suffix):
                    potential_root = word[:-len(suffix)]
                    # Kök çok kısa kalmasın
                    if len(potential_root) >= 4:
                        word = potential_root
                        break
        
        final_words.append(word)
    
    # 5. Sonucu temizle ve döndür
    result = ' '.join(filter(None, final_words)).strip()
    
    # Boş sonuç kontrolü
    if not result:
        result = text.strip()
    
    print(f"DEBUG NORMALIZE V3: '{text}' → '{result}'")
    return result

def format_product_response(product, attribute):
    """Kısa ürün bilgisi döndür"""
    attr_key = PRODUCT_ATTRIBUTE_MAP.get(attribute.lower(), attribute.lower())
    value = product.get(attr_key)
    
    if not value:
        return f"{product['name']} - {attribute} bilgisi yok."
    
    if attr_key == "final_price":
        return f"{product['name']}\nFiyat: {value} TL"
    elif attr_key == "color":
        return f"{product['name']}\nRenk: {value}"
    elif attr_key == "stock":
        return f"{product['name']}\nStok: {value} adet"
    else:
        return f"{product['name']}\n{attribute.capitalize()}: {value}"

def format_multiple_products_response(products, attribute, query):
    """SÜPER AKILLI çoklu ürün listesi - müşteri dostu"""
    if not products:
        return f"'{query}' için uygun ürün bulunamadı. Farklı arama terimleri deneyebilirsiniz."
    
    if len(products) == 1:
        return format_product_response(products[0], attribute)
    
    # Başlık - daha samimi
    response = f"'{query}' için {len(products)} ürün buldum:\n\n"
    
    for i, product in enumerate(products, 1):
        response += f"{i}. {product['name']}\n"
        
        # Fiyat her zaman göster
        price = product.get('final_price', 'Fiyat bilgisi yok')
        if price != 'Fiyat bilgisi yok':
            response += f"💰 Fiyat: {price} TL\n"
        else:
            response += f"💰 {price}\n"
        
        # İstenen attribute'a göre ek bilgi
        if attribute.lower() in ["renk", "color"]:
            color = product.get('color', 'Renk bilgisi yok')
            response += f"🎨 Renk: {color}\n"
        elif attribute.lower() in ["stok", "stock"]:
            stock = product.get('stock', 'Stok bilgisi yok')
            if stock != 'Stok bilgisi yok':
                response += f"📦 Stok: {stock} adet\n"
            else:
                response += f"📦 {stock}\n"
        elif attribute.lower() in ["beden", "size"]:
            size = product.get('size', 'Beden bilgisi yok')
            response += f"📏 Beden: {size}\n"
        
        # Kod her zaman göster
        code = product.get('code', 'Kod yok')
        response += f"🏷️ Kod: {code}\n\n"
    
    # Kapanış - daha yardımcı
    if len(products) > 3:
        response += "Hangi ürün hakkında detay istiyorsunuz? Kod numarasını söyleyebilirsiniz.\n"
    
    response += "📞 Detaylı bilgi: 0555 555 55 55"
    return response

def get_product_attribute_value(product, attribute):
    """Ürün attribute değerini getir - yoksa None döndür"""
    attr_key = PRODUCT_ATTRIBUTE_MAP.get(attribute.lower(), attribute.lower())
    return product.get(attr_key)



@app.post("/ask")
async def ask(question: Question):
    start_time = datetime.now()
    query = question.question.strip()
    user_id = "default"
    business_id = "fashion_boutique"

    try:
        # Function calling sistemi ile işle
        result = await llm_service.process_message_with_functions(
            prompt=query,
            session_id=user_id,
            isletme_id=business_id
        )
        
        # Maliyet takibi
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))
            from orchestrator.services.cost_optimizer import cost_optimizer
            
            method = result.get("method", "unknown") if result else "error"
            cost_optimizer.track_query(method)
        except Exception as e:
            logger.error(f"Cost tracking error: {str(e)}")
        
        if not result:
            log_failed_query(query, "function_calling_error", "No result from function calling", "no_result")
            return {"answer": "Üzgünüm, şu anda yanıt veremiyorum. Lütfen tekrar deneyin."}
        
        # Function call varsa execute et
        if result.get("function_call"):
            function_call = result["function_call"]
            execution_result = await function_coordinator.execute_function_call(
                function_name=function_call["name"],
                arguments=function_call["args"],
                session_id=user_id,
                business_id=business_id
            )
            
            if execution_result and execution_result.get("success"):
                answer = execution_result.get("response", "İşlem tamamlandı.")
                method = "function_calling"
            else:
                # Function call başarısızsa fallback
                answer = await handle_fallback_response(query, result)
                method = "fallback"
        else:
            # Direct response varsa kullan
            answer = result.get("final_response", "Anlayamadım, tekrar sorabilir misiniz?")
            method = result.get("method", "intent_detection")
            
            # Answer None ise fallback
            if answer is None:
                answer = "Anlayamadım, tekrar sorabilir misiniz?"
        
        # Execution time hesapla
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log successful query
        log_successful_query(query, result.get("intent", "unknown"), answer)
        
        return {
            "answer": answer,
            "intent": result.get("intent", "unknown"),  # Intent bilgisini ekle
            "method": method,
            "confidence": result.get("confidence", 0.8),
            "execution_time_ms": int(execution_time)
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        error_msg = f"System error: {str(e)}"
        log_failed_query(query, "system_error", error_msg, "exception")
        
        return {
            "answer": "Üzgünüm, teknik bir sorun oluştu. Lütfen tekrar deneyin.",
            "method": "error",
            "confidence": 0.0,
            "execution_time_ms": int(execution_time)
        }

@app.get("/admin/stats")
async def get_admin_stats():
    """Admin istatistikleri"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))
        from orchestrator.services.cost_optimizer import cost_optimizer
        
        daily_stats = cost_optimizer.get_daily_stats()
        projection = cost_optimizer.get_cost_projection(33333)  # 1M/month target
        
        return {
            "daily_stats": daily_stats,
            "monthly_projection": projection,
            "system_health": "healthy",
            "target_efficiency": "70% pattern matching, 30% LLM"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))
        from orchestrator.services.cost_optimizer import cost_optimizer
        
        stats = cost_optimizer.get_daily_stats()
        
        return {
            "status": "healthy",
            "queries_today": stats["total_queries"],
            "cost_today": f"${stats['total_cost_usd']:.4f}",
            "efficiency": f"{stats['efficiency_score']:.1f}%",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def handle_fallback_response(query: str, llm_result: dict) -> str:
    """Function call başarısızsa fallback response"""
    intent = llm_result.get("intent", "unknown")
    
    if intent == "greeting":
        return "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"
    elif intent == "thanks":
        return "Rica ederim! Başka sorunuz var mı?"
    elif intent == "product_query":
        return "Ürün bilgisi için lütfen daha spesifik olabilir misiniz?"
    elif intent == "meta_query":
        return "İşletme bilgileri için WhatsApp: 0555 555 55 55"
    else:
        return "Anlayamadım. Ürün, fiyat veya iletişim hakkında sorabilirsiniz."
