
from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
import requests
from dotenv import load_dotenv
from rapidfuzz import fuzz
import re
from web_interface import setup_web_routes

load_dotenv()

app = FastAPI()
setup_web_routes(app)

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
    """Gelişmiş ürün arama - V2 - rapidfuzz token_set_ratio ile"""
    if not product_name:
        return []
    
    product_name = product_name.lower().strip()
    
    # Arama terimlerindeki anlamsız kelimeleri çıkar
    stop_words = {"ve", "ile", "için", "bir"}
    query_words = [word for word in product_name.split() if word not in stop_words]
    clean_query = " ".join(query_words)

    scored_products = []
    
    for product in PRODUCTS:
        product_full_name = product["name"].lower()
        
        # Token Set Ratio, kelime sırasından bağımsız olarak eşleşmeyi ölçer.
        # Bu, "siyah gecelik" ile "gecelik siyah" sorgularının benzer skorlar almasını sağlar.
        score = fuzz.token_set_ratio(clean_query, product_full_name)
        
        # Bonus puanlar: Kelimelerin doğru sırada olması
        if all(word in product_full_name for word in query_words):
            score += 10 # Tüm kelimeler varsa bonus

        # Tam eşleşme için ekstra bonus
        if clean_query == product_full_name:
            score += 20

        # Yüksek skorlu ürünleri listeye ekle
        if score > 75: # Eşik değeri (ayarlanabilir)
            scored_products.append((product, score))

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
    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None

# OPTİMİZE EDİLMİŞ PROMPT TEMPLATE - V2
OPTIMIZED_PROMPT_TEMPLATE = """
Sen bir e-ticaret müşteri hizmetleri asistanısın. Görevin, kullanıcı sorularını analiz edip SADECE JSON formatında bir çıktı üretmektir.

# ANA KURALLAR
- Çıktın her zaman geçerli bir JSON nesnesi olmalıdır.
- Kullanıcının niyetini (intent) doğru bir şekilde belirle.
- Ürün isimlerinden ve sorulardan Türkçe ekleri temizle.
- Kullanıcıya asla doğrudan cevap verme, sadece JSON üret.

# INTENT'LER
1.  `greeting`: Kullanıcı selam verdiğinde.
2.  `thanks`: Kullanıcı teşekkür ettiğinde.
3.  `meta_query`: Kullanıcı işletme hakkında genel bir soru sorduğunda (telefon, iade, kargo, site vb.).
4.  `product_query`: Kullanıcı bir ürün hakkında spesifik bir soru sorduğunda (fiyat, stok, renk, beden vb.).
5.  `clarify`: Kullanıcının sorusu belirsiz olduğunda veya hangi üründen bahsettiği anlaşılmadığında.
6.  `unknown`: Soru yukarıdaki kategorilere uymadığında.

# JSON ÇIKTI FORMATI
{
  "intent": "<intent_adı>",
  "product": "<ürün_adı_normalize_edilmiş>" | null,
  "attribute": "<özellik_adı>" | null,
  "original_query": "<kullanıcının_orijinal_sorusu>"
}

# TÜRKÇE NORMALİZASYON KURALLARI
- İsimlerin sonundaki iyelik ve durum eklerini (-ı, -i, -u, -ü, -ın, -in, -a, -e, -da, -de, -dan, -den vb.) kaldır.
- Örnek: "geceliği" -> "gecelik", "pijamanın fiyatı" -> "pijama", "telefona bakıyorum" -> "telefon"

# ÖRNEKLER (FEW-SHOT LEARNING)

# Örnek 1: Basit selamlama
Soru: "selam"
Çıktı:
```json
{
  "intent": "greeting",
  "product": null,
  "attribute": null,
  "original_query": "selam"
}
```

# Örnek 2: Ürün ve fiyat sorgusu
Soru: "Sırtı Dekolteli Tüllü ve Dantelli Pijama Takımı ne kadar?"
Çıktı:
```json
{
  "intent": "product_query",
  "product": "Sırtı Dekolteli Tüllü ve Dantelli Pijama Takımı",
  "attribute": "fiyat",
  "original_query": "Sırtı Dekolteli Tüllü ve Dantelli Pijama Takımı ne kadar?"
}
```

# Örnek 3: Günlük dilde ürün sorgusu ve eklerin temizlenmesi
Soru: "elbiselerin rengi var mı"
Çıktı:
```json
{
  "intent": "product_query",
  "product": "elbise",
  "attribute": "renk",
  "original_query": "elbiselerin rengi var mı"
}
```

# Örnek 4: İşletme hakkında meta bilgi sorgusu
Soru: "kargo hakkında bilgi alabilir miyim"
Çıktı:
```json
{
  "intent": "meta_query",
  "product": null,
  "attribute": "kargo",
  "original_query": "kargo hakkında bilgi alabilir miyim"
}
```

# Örnek 5: Belirsiz ürün sorgusu
Soru: "bu ne kadar"
Çıktı:
```json
{
  "intent": "clarify",
  "product": null,
  "attribute": "fiyat",
  "original_query": "bu ne kadar"
}
```

# Örnek 6: Stok durumu sorgusu (dolaylı)
Soru: "siyah dekolteli gecelik var mı acaba"
Çıktı:
```json
{
  "intent": "product_query",
  "product": "siyah dekolteli gecelik",
  "attribute": "stok",
  "original_query": "siyah dekolteli gecelik var mı acaba"
}
```

# Örnek 7: Teşekkür
Soru: "çok teşekkürler"
Çıktı:
```json
{
  "intent": "thanks",
  "product": null,
  "attribute": null,
  "original_query": "çok teşekkürler"
}
```

# GERÇEK SORU
Soru: "{{question}}"
Çıktı:
"""

# Sabit cevaplar - LLM'e gerek yok
STATIC_RESPONSES = {
    "greeting": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?",
    "thanks": "Rica ederim! Başka sorunuz var mı?",
    "decline": "Bu konuda yardımcı olamam. Ürünlerimiz hakkında sorabilirsiniz.",
    "unknown": "Anlayamadım. Ürün, fiyat, iade veya iletişim hakkında sorabilirsiniz."
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
    """Türkçe ürün adlarını normalize et - V2 - Daha Kapsamlı"""
    if not text:
        return text
    
    text = text.lower().strip()
    
    # Gelişmiş özel durumlar ve sık yapılan yazım hataları
    special_cases = {
        'geceliği': 'gecelik', 'geceliğin': 'gecelik', 'gecelig': 'gecelik',
        'pijamayı': 'pijama', 'pijamanın': 'pijama', 'pijama takimi': 'pijama takımı',
        'elbiseyi': 'elbise', 'elbisenin': 'elbise',
        'sabahlığı': 'sabahlık', 'sabahlığın': 'sabahlık',
        'takım': 'takımı',
        'lohusa': 'lohusa', 'hamile': 'hamile',
        'fiyatı ne kadar': '', 'fiyatı': '', 'fiyat': '', 'ne kadar': '',
        'kaç para': '', 'kac para': '',
        'bedeni': 'beden', 'bedenleri': 'beden',
        'rengi': 'renk', 'renkleri': 'renk',
        'stogu': 'stok', 'stokta': 'stok',
        'varmi': 'var mı'
    }
    
    # Önce tam ifade eşleşmelerini yap
    for case, replacement in special_cases.items():
        if case in text:
            text = text.replace(case, replacement)

    # Kök bulma için daha genel bir yaklaşım
    words = text.split()
    normalized_words = []
    
    for word in words:
        original_word = word

        # Yaygın Türkçe ekleri (en uzundan en kısaya doğru sıralı)
        # Bu sıralama, "elbiselerin" -> "elbise" gibi durumları doğru handle etmek için önemli.
        suffixes = [
            'lerini', 'larını', 'lerinin', 'larının',
            'lerim', 'larım', 'lerimiz', 'larımız',
            'sınız', 'siniz', 'sunuz', 'sünüz',
            'ler', 'lar',
            'dan', 'den', 'tan', 'ten',
            'daki', 'deki',
            'nın', 'nin', 'nun', 'nün',
            'ına', 'ine', 'una', 'üne',
            'dan', 'den', 'tan', 'ten',
            'da', 'de', 'ta', 'te',
            'ın', 'in', 'un', 'ün',
            'ım', 'im', 'um', 'üm',
            'a', 'e', 'ı', 'i', 'u', 'ü'
        ]

        # Kelime kökünü bulmaya çalış
        for suffix in suffixes:
            if word.endswith(suffix):
                potential_root = word[:-len(suffix)]
                # Kökün anlamlı bir uzunlukta olduğundan emin ol
                if len(potential_root) > 2:
                    word = potential_root
                    break # İlk eşleşen en uzun ek yeterli

        normalized_words.append(word)

    result = ' '.join(filter(None, normalized_words)) # Boş elemanları filtrele
    print(f"DEBUG NORMALIZE V2: '{text}' → '{result}'")
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
    """Kısa çoklu ürün listesi"""
    if not products:
        return "Ürün bulunamadı."
    
    if len(products) == 1:
        return format_product_response(products[0], attribute)
    
    # Kısa liste
    response = f"{query} için {len(products)} ürün:\n\n"
    
    for i, product in enumerate(products, 1):
        attr_key = PRODUCT_ATTRIBUTE_MAP.get(attribute.lower(), attribute.lower())
        value = product.get(attr_key, "-")
        
        response += f"{i}. {product['name']}\n"
        
        if attribute.lower() in ["fiyat", "price", "final_price"]:
            response += f"Fiyat: {product.get('final_price', '-')} TL\n"
        elif attribute.lower() in ["renk", "color"]:
            response += f"Renk: {product.get('color', '-')}\n"
        elif attribute.lower() in ["stok", "stock"]:
            response += f"Stok: {product.get('stock', '-')} adet\n"
        else:
            response += f"Fiyat: {product.get('final_price', '-')} TL\n"
        
        response += f"Kod: {product.get('code', '-')}\n\n"
    
    response += "Detay için kod belirtin. Tel: 0555 555 55 55"
    return response

def get_product_attribute_value(product, attribute):
    """Ürün attribute değerini getir - yoksa None döndür"""
    attr_key = PRODUCT_ATTRIBUTE_MAP.get(attribute.lower(), attribute.lower())
    return product.get(attr_key)



@app.post("/ask")
async def ask(question: Question):
    query = question.question.strip().lower()
    user_id = "default"  # Şimdilik tek kullanıcı

    # Cache kontrolü - benzer sorular için
    if query in response_cache:
        print("CACHE HIT:", query)
        return {"answer": response_cache[query]}

    # SADECE LLM SİSTEMİ - Temiz ve güçlü

    # Context kontrolü - önceki soru clarify ise
    context = get_user_context(user_id)
    if context.get("last_intent") == "clarify":
        # Kullanıcı ürün ismi verdi, önceki soruya göre işle
        original_question = context.get("last_question", "")
        
        # Eğer önceki soruda "içerik", "detay" gibi kelimeler varsa
        if any(word in original_question.lower() for word in ["içerik", "detay", "açıklama", "bilgi"]):
            # Ürün detaylarını göster
            products = search_products_by_name(query)
            if products:
                product = products[0]
                # Şimdilik basit detay göster
                answer = f"{product['name']}\n\nFiyat: {product.get('final_price', '-')} TL\nRenk: {product.get('color', '-')}\nStok: {product.get('stock', '-')} adet\nKod: {product.get('code', '-')}"

                # Context'i temizle
                save_user_context(user_id, query, "product", {"product": query})
                return {"answer": answer}
        
        # Normal ürün sorgusu olarak işle - fiyat default
        data = {"intent": "product", "product": query, "attr": "fiyat"}
    else:
        # SADECE LLM - Her şeyi LLM yapsın
        prompt = OPTIMIZED_PROMPT_TEMPLATE.format(question=question.question.strip())
        result = ask_gemini(prompt)
        print("LLM RESPONSE:", result)
        
        if not result:
            log_failed_query(query, "llm_error", "No response from LLM", "llm_no_response")
            return {"answer": "Üzgünüm, şu anda yanıt veremiyorum. Lütfen tekrar deneyin."}

        # JSON'u temizle ve parse et
        result_clean = result.strip()
        if result_clean.startswith('```json'):
            result_clean = result_clean[7:]
        if result_clean.endswith('```'):
            result_clean = result_clean[:-3]
        result_clean = result_clean.strip()

        try:
            data = json.loads(result_clean)
            # Orijinal sorguyu da ekleyelim
            if "original_query" not in data:
                data["original_query"] = query
        except json.JSONDecodeError:
            log_failed_query(query, "json_error", result, "json_decode_error")
            # Regex ile JSON çıkarmaya çalış
            json_match = re.search(r'\{.*\}', result_clean, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    if "original_query" not in data:
                        data["original_query"] = query
                except json.JSONDecodeError:
                    log_failed_query(query, "json_error", json_match.group(), "json_regex_decode_error")
                    return {"answer": "Üzgünüm, sorunuzu işlerken bir sorun oluştu."}
            else:
                log_failed_query(query, "json_error", result, "no_json_found")
                return {"answer": "Üzgünüm, sorunuzu anlayamadım. Lütfen daha açık bir şekilde sorar mısınız?"}

    intent = data.get("intent", "unknown")

    # Sabit cevapları kullan - LLM'e gerek yok
    if intent in STATIC_RESPONSES:
        return {"answer": STATIC_RESPONSES[intent]}

    elif intent == "clarify":
        # Context'e kaydet - kullanıcı clarify bekliyor
        save_user_context(user_id, question.question.strip(), "clarify", data)
        return {"answer": "Hangi ürün?"}

    elif intent == "meta" or intent == "meta_query":
        attribute = data.get("attr", data.get("attribute", ""))
        value = get_meta_info(attribute)
        if value:
            # Kısa ve net cevaplar
            if attribute.lower() in ["telefon", "phone"]:
                return {"answer": f"Telefon: {value}"}
            elif attribute.lower() in ["iade", "iade_policy"]:
                return {"answer": f"İade: {value}"}
            elif attribute.lower() in ["kargo", "shipping_info", "teslimat"]:
                return {"answer": f"Kargo: {value}"}
            elif attribute.lower() in ["site", "web"]:
                return {"answer": f"Site: {value}"}
            else:
                return {"answer": value}
        else:
            return {"answer": "Bu bilgi bulunamadı."}

    elif intent == "product" or intent == "product_query":
        product_name = data.get("product", "")
        attribute = data.get("attr", data.get("attribute", "fiyat"))

        # BOŞSA DEFAULT FIYAT YAP
        if not attribute or attribute.strip() == "":
            attribute = "fiyat"
            
        original_query = question.question.strip()

        if not product_name:
            return {"answer": "Hangi ürün?"}

        # GENEL ÇÖZÜM: Türkçe normalizasyon uygula
        normalized_product_name = normalize_turkish_product_name(product_name)
        print(f"DEBUG: '{product_name}' → '{normalized_product_name}'")

        # "VAR MI" SORGUSU ÖZEL KONTROLÜ
        if attribute.lower() == "stok" or "var" in original_query.lower():
            products = search_products_by_name(normalized_product_name)
            if products:
                # Ürün varsa kısa bilgi ver
                if len(products) == 1:
                    product = products[0]
                    answer = f"Evet, {product['name']} mevcut.\nFiyat: {product.get('final_price', '-')} TL\nStok: {product.get('stock', '-')} adet"
                else:
                    answer = f"Evet, {normalized_product_name} ürünlerimiz mevcut. {len(products)} farklı model var.\nDetay için ürün kodunu belirtin. Tel: 0555 555 55 55"
            else:
                answer = f"Üzgünüm, {normalized_product_name} ürünümüz şu anda mevcut değil."
            
            # Cache'e ekle
            response_cache[query] = answer
            return {"answer": answer}
        
        # Genel kategori sorgusu kontrolü
        if normalized_product_name.lower() in ["gecelik", "pijama", "sabahlık"] and "var" in original_query.lower():
            categories = get_available_categories()
            if normalized_product_name.lower() in categories:
                answer = f"Evet, {normalized_product_name} ürünlerimiz var. Hangi renk/model?"
            else:
                answer = f"{normalized_product_name} ürünümüz yok."
            
            # Cache'e ekle
            response_cache[query] = answer
            return {"answer": answer}

        # Ürün arama - normalize edilmiş isimle ara
        products = search_products_by_name(normalized_product_name)

        if not products:
            answer = f"'{product_name}' bulunamadı."
            response_cache[query] = answer
            return {"answer": answer}

        # Cevap üret ve cache'e ekle
        if len(products) > 1:
            answer = format_multiple_products_response(products, attribute, product_name)
        else:
            product = products[0]
            attr_value = get_product_attribute_value(product, attribute)

            if attr_value is None:
                answer = f"{product['name']} - {attribute} bilgisi yok."
            else:
                answer = format_product_response(product, attribute)

        # Cache'e ekle
        response_cache[query] = answer
        
        # BAŞARILI SORGUYU LOGLA
        log_successful_query(question.question.strip(), intent, answer)

        return {"answer": answer}

    else:
        # BİLİNMEYEN INTENT - BAŞARISIZ SORGU LOGLA
        log_failed_query(
            question.question.strip(), 
            "unknown",
            STATIC_RESPONSES["unknown"],
            "unknown_intent"
        )
        return {"answer": STATIC_RESPONSES["unknown"]}
