
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
    """Gelişmiş ürün arama - önce tam eşleşme, sonra kısmi eşleşme"""
    if not product_name:
        return []
    
    product_name = product_name.lower().strip()
    exact_matches = []
    partial_matches = []
    
    name_words = product_name.split()
    
    # Tüm ürünlerde ara
    for product in PRODUCTS:
        product_full_name = product["name"].lower()
        match_score = 0
        exact_word_matches = 0
        
        # Kelime bazlı eşleşme sayısı
        for word in name_words:
            if len(word) > 2 and word in product_full_name:
                match_score += 1
                exact_word_matches += 1
        
        # Eğer tüm kelimeler eşleşiyorsa tam eşleşme
        if exact_word_matches == len(name_words) and len(name_words) > 1:
            exact_matches.append((product, match_score))
        elif match_score > 0:
            partial_matches.append((product, match_score))
        else:
            # Fuzzy matching sadece hiç eşleşme yoksa
            similarity = fuzz.partial_ratio(product_name, product_full_name)
            if similarity > 70:
                partial_matches.append((product, similarity / 100))
    
    # Önce tam eşleşmeleri döndür
    if exact_matches:
        exact_matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in exact_matches[:max_results]]
    
    # Tam eşleşme yoksa kısmi eşleşmeleri döndür
    partial_matches.sort(key=lambda x: x[1], reverse=True)
    return [match[0] for match in partial_matches[:max_results]]

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

# GERÇEK DİNAMİK SİSTEM - Her sektör için otomatik
def generate_dynamic_prompt(products_data=None, business_type="retail"):
    """Ürün verisinden otomatik prompt üret"""
    
    # Ürün verilerinden kategorileri çıkar
    categories = set()
    colors = set()
    
    if products_data:
        for product in products_data[:50]:  # İlk 50 ürünü analiz et
            name = product.get("name", "").lower()
            color = product.get("color", "")
            
            # Kategori tespiti
            if "gecelik" in name:
                categories.add("gecelik")
            elif "elbise" in name:
                categories.add("elbise")
            elif "pijama" in name:
                categories.add("pijama")
            elif "laptop" in name:
                categories.add("laptop")
            elif "telefon" in name:
                categories.add("telefon")
            elif "pizza" in name:
                categories.add("pizza")
            elif "burger" in name:
                categories.add("burger")
            
            # Renk tespiti
            if color:
                colors.add(color.lower())
    
    # Dinamik prompt oluştur
    categories_str = ", ".join(list(categories)[:10]) if categories else "çeşitli ürünler"
    colors_str = ", ".join(list(colors)[:10]) if colors else "çeşitli renkler"
    
    base_prompt = f"""Sen müşteri hizmetleri asistanısın. SADECE JSON döndür.

BU İŞLETMENİN ÜRÜNLERİ: {categories_str}
MEVCUT RENKLER: {colors_str}

GÖREVIN:
- Kullanıcının sorusunu analiz et
- Ürün adlarını düzelt (Türkçe ekleri temizle)
- Mevcut ürün/renklere uygun öneriler yap
- Doğru intent'i belirle

TEMEL KURALLAR:
- Selamlama → {{"intent":"greeting"}}
- Teşekkür → {{"intent":"thanks"}}
- İşletme bilgisi → {{"intent":"meta","attr":"telefon/iade/kargo"}}
- Belirsiz ürün → {{"intent":"clarify"}}
- Spesifik ürün → {{"intent":"product","product":"düzeltilmiş_ad","attr":"fiyat/stok/renk"}}

TÜRKÇE EK TEMİZLEME:
geceliği→gecelik, elbisenin→elbise, telefonun→telefon, laptopın→laptop

AKILLI RENK/ÜRÜN EŞLEŞTİRME:
- Olmayan renk sorulursa en yakın rengi öner
- Olmayan ürün sorulursa benzer ürünü öner

ÖRNEKLER:
"merhaba" → {{"intent":"greeting"}}
"sağol" → {{"intent":"thanks"}}
"telefon" → {{"intent":"meta","attr":"telefon"}}
"bu ürün ne kadar" → {{"intent":"clarify"}}

"{{question}}" → """
    
    return base_prompt

# Global prompt template - ürün verisiyle dinamik oluştur
LLM_PROMPT_TEMPLATE = generate_dynamic_prompt(PRODUCTS)

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

# AKILLI ÖĞRENME SİSTEMİ - Otomatik prompt iyileştirme
import datetime
import logging
import json
import os
import threading
import time
from collections import defaultdict

# Log dosyası ayarla
logging.basicConfig(
    filename='chatbot_logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Akıllı öğrenme sistemi
class SmartLearningSystem:
    def __init__(self):
        self.failed_queries = []
        self.successful_queries = []
        self.learning_stats = {
            "total_queries": 0,
            "success_rate": 0.0,
            "last_update": None,
            "update_frequency": "1_minute",  # Başlangıçta her dakika
            "learned_patterns": []
        }
        self.load_learning_stats()
        self.start_background_learning()
    
    def load_learning_stats(self):
        """Öğrenme istatistiklerini yükle"""
        try:
            if os.path.exists("learning_stats.json"):
                with open("learning_stats.json", "r", encoding="utf-8") as f:
                    self.learning_stats = json.load(f)
        except:
            pass
    
    def save_learning_stats(self):
        """Öğrenme istatistiklerini kaydet"""
        with open("learning_stats.json", "w", encoding="utf-8") as f:
            json.dump(self.learning_stats, f, ensure_ascii=False, indent=2)
    
    def log_query(self, question, intent, response, success=True):
        """Sorguları kaydet ve analiz et"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "intent": intent,
            "response": response[:100] + "..." if len(response) > 100 else response,
            "success": success
        }
        
        if success:
            self.successful_queries.append(entry)
            logging.info(f"SUCCESS: {entry}")
        else:
            self.failed_queries.append(entry)
            logging.error(f"FAILED: {entry}")
        
        self.learning_stats["total_queries"] += 1
        
        # Başarı oranını güncelle
        total_success = len(self.successful_queries)
        total_queries = len(self.successful_queries) + len(self.failed_queries)
        if total_queries > 0:
            self.learning_stats["success_rate"] = (total_success / total_queries) * 100
    
    def should_update_prompt(self):
        """Prompt güncellemesi gerekli mi?"""
        now = datetime.datetime.now()
        last_update = self.learning_stats.get("last_update")
        
        if not last_update:
            return True
        
        last_update_time = datetime.datetime.fromisoformat(last_update)
        frequency = self.learning_stats["update_frequency"]
        
        if frequency == "1_minute":
            return (now - last_update_time).total_seconds() >= 60
        elif frequency == "1_hour":
            return (now - last_update_time).total_seconds() >= 3600
        elif frequency == "1_day":
            return (now - last_update_time).days >= 1
        elif frequency == "1_month":
            return (now - last_update_time).days >= 30
        
        return False
    
    def analyze_and_improve(self):
        """Logları analiz et ve prompt'u iyileştir"""
        if not self.should_update_prompt():
            return
        
        print("🧠 AKILLI ÖĞRENME SİSTEMİ ÇALIŞIYOR...")
        
        # Başarısız sorguları analiz et
        if len(self.failed_queries) >= 5:  # En az 5 hata olmalı
            self.generate_prompt_improvements()
        
        # Başarı oranına göre güncelleme sıklığını ayarla
        success_rate = self.learning_stats["success_rate"]
        if success_rate >= 95:
            self.learning_stats["update_frequency"] = "1_month"  # Çok iyi, ayda 1
        elif success_rate >= 90:
            self.learning_stats["update_frequency"] = "1_day"    # İyi, günde 1
        elif success_rate >= 80:
            self.learning_stats["update_frequency"] = "1_hour"   # Orta, saatte 1
        else:
            self.learning_stats["update_frequency"] = "1_minute" # Kötü, dakikada 1
        
        self.learning_stats["last_update"] = datetime.datetime.now().isoformat()
        self.save_learning_stats()
        
        # Eski logları temizle (son 100 başarılı, 50 başarısız kalsın)
        self.successful_queries = self.successful_queries[-100:]
        self.failed_queries = self.failed_queries[-50:]
        
        print(f"✅ Öğrenme tamamlandı. Başarı oranı: {success_rate:.1f}%")
        print(f"📅 Sonraki güncelleme: {self.learning_stats['update_frequency']}")
    
    def generate_prompt_improvements(self):
        """Başarısız sorgulardan prompt iyileştirmeleri üret"""
        if not self.failed_queries:
            return
        
        # Hata türlerini analiz et
        error_patterns = defaultdict(list)
        for query in self.failed_queries[-20:]:  # Son 20 hatayı analiz et
            question = query["question"].lower()
            
            # Hata türlerini tespit et
            if any(word in question for word in ["hey", "selam", "merhaba"]) and "greeting" not in query.get("intent", ""):
                error_patterns["greeting_missed"].append(question)
            elif any(word in question for word in ["teşekkür", "sağol", "tamam"]) and "thanks" not in query.get("intent", ""):
                error_patterns["thanks_missed"].append(question)
            elif any(word in question for word in ["telefon", "iade", "kargo"]) and "meta" not in query.get("intent", ""):
                error_patterns["meta_missed"].append(question)
            else:
                error_patterns["unknown_pattern"].append(question)
        
        # Yeni örnekleri prompt'a ekle
        new_examples = []
        for error_type, questions in error_patterns.items():
            if len(questions) >= 2:  # En az 2 örnek varsa
                for question in questions[:3]:  # İlk 3'ünü al
                    if error_type == "greeting_missed":
                        new_examples.append(f'"{question}" → {{"intent":"greeting"}}')
                    elif error_type == "thanks_missed":
                        new_examples.append(f'"{question}" → {{"intent":"thanks"}}')
                    elif error_type == "meta_missed":
                        if "telefon" in question:
                            new_examples.append(f'"{question}" → {{"intent":"meta","attr":"telefon"}}')
                        elif "iade" in question:
                            new_examples.append(f'"{question}" → {{"intent":"meta","attr":"iade"}}')
                        elif "kargo" in question:
                            new_examples.append(f'"{question}" → {{"intent":"meta","attr":"kargo"}}')
        
        # Yeni örnekleri kaydet
        if new_examples:
            with open("prompt_improvements.txt", "w", encoding="utf-8") as f:
                f.write(f"YENİ PROMPT ÖRNEKLERİ - {datetime.datetime.now()}\n")
                f.write("="*50 + "\n\n")
                for example in new_examples:
                    f.write(example + "\n")
                f.write(f"\n📊 Analiz edilen hata sayısı: {len(self.failed_queries)}")
                f.write(f"\n🎯 Başarı oranı: {self.learning_stats['success_rate']:.1f}%")
            
            print(f"💡 {len(new_examples)} yeni örnek oluşturuldu: prompt_improvements.txt")
            self.learning_stats["learned_patterns"].extend(new_examples)
    
    def start_background_learning(self):
        """Arka planda sürekli öğrenme"""
        def learning_loop():
            while True:
                try:
                    time.sleep(60)  # Her dakika kontrol et
                    self.analyze_and_improve()
                except Exception as e:
                    print(f"Öğrenme hatası: {e}")
        
        # Arka plan thread'i başlat
        learning_thread = threading.Thread(target=learning_loop, daemon=True)
        learning_thread.start()

# Global öğrenme sistemi
smart_learning = SmartLearningSystem()

def log_failed_query(question, expected_intent, actual_response, error_type):
    """Başarısız sorguları kaydet"""
    smart_learning.log_query(question, expected_intent, actual_response, success=False)

def log_successful_query(question, intent, response):
    """Başarılı sorguları kaydet"""
    smart_learning.log_query(question, intent, response, success=True)

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

def rule_based_intent_detection(question):
    """Kural tabanlı intent tespiti - SADECE BASİT CÜMLELER İÇİN"""
    question_lower = question.lower().strip()
    words = question_lower.split()
    
    # KARMAŞIK CÜMLE KONTROLÜ - LLM'e bırak
    if len(words) > 3:
        return {"intent": "unknown"}  # LLM'e bırak
    
    # KARIŞIK CÜMLE KONTROLÜ - Birden fazla intent varsa LLM'e bırak
    intent_indicators = 0
    if any(greeting in question_lower for greeting in ["merhaba", "selam", "selamlar"]):
        intent_indicators += 1
    if any(word in question_lower for word in ["fiyat", "ne kadar", "ürün"]):
        intent_indicators += 1
    if any(word in question_lower for word in ["telefon", "iade", "kargo"]):
        intent_indicators += 1
    
    if intent_indicators > 1:
        return {"intent": "unknown"}  # LLM'e bırak
    
    # BASİT CÜMLELER İÇİN KURAL TABANLI
    
    # 1. SADECE SELAMLAMA
    if len(words) <= 2 and any(greeting in question_lower for greeting in ["merhaba", "selam", "selamlar"]):
        return {"intent": "greeting"}
    
    # 2. SADECE TEŞEKKÜR
    if len(words) <= 2 and any(thank in question_lower for thank in ["teşekkür", "sağol", "tamam"]):
        return {"intent": "thanks"}
    
    # 3. SADECE META BİLGİ
    if "telefon" in question_lower and "numara" in question_lower:
        return {"intent": "meta", "attr": "telefon"}
    if "iade" in question_lower:
        return {"intent": "meta", "attr": "iade"}
    if "kargo" in question_lower:
        return {"intent": "meta", "attr": "kargo"}
    
    # 4. BELİRSİZ SORGULAR
    vague_words = ["bu ürün", "şu ürün", "o ürün", "bunun", "şunun", "onun"]
    if any(vague in question_lower for vague in vague_words):
        return {"intent": "clarify"}
    
    # 5. DİĞER HER ŞEY LLM'E
    return {"intent": "unknown"}

def normalize_turkish_product_name(text):
    """Türkçe ürün adlarını normalize et - AKILLI ÇÖZÜM"""
    if not text:
        return text
    
    text = text.lower().strip()
    
    # ÖZEL DURUMLAR - Yaygın ürün adları için
    special_cases = {
        'geceliği': 'gecelik',
        'geceliğin': 'gecelik',
        'geceliğinin': 'gecelik',
        'pijamının': 'pijama',
        'pijamanın': 'pijama',
        'elbisenin': 'elbise',
        'elbisesinin': 'elbise',
        'sabahlığın': 'sabahlık',
        'sabahlığının': 'sabahlık'
    }
    
    # Kelime kelime kontrol et
    words = text.split()
    normalized_words = []
    
    for word in words:
        # Özel durumları kontrol et
        if word in special_cases:
            normalized_words.append(special_cases[word])
        else:
            # Genel Türkçe ek kaldırma
            original_word = word
            
            # Yaygın Türkçe ekleri (uzundan kısaya)
            turkish_suffixes = [
                'ının', 'inin', 'unun', 'ünün',  # -nın/-nin/-nun/-nün
                'nın', 'nin', 'nun', 'nün',      # -nın/-nin/-nun/-nün
                'ları', 'leri',                  # çoğul
                'lar', 'ler',                    # çoğul
                'dan', 'den', 'tan', 'ten',      # çıkma hali
                'ın', 'in', 'un', 'ün',          # -ın/-in/-un/-ün  
                'ya', 'ye',                      # yönelme hali
                'da', 'de', 'ta', 'te',          # bulunma hali
                'nı', 'ni', 'nu', 'nü',          # -nı/-ni/-nu/-nü
                'ı', 'i', 'u', 'ü'               # -ı/-i/-u/-ü (en son)
            ]
            
            # En uzun eklerden başlayarak kaldır
            for suffix in turkish_suffixes:
                if word.endswith(suffix):
                    # Ek kaldırıldıktan sonra en az 3 karakter kalmalı
                    if len(word) - len(suffix) >= 3:
                        word = word[:-len(suffix)]
                        break
            
            normalized_words.append(word)
    
    result = ' '.join(normalized_words)
    print(f"DEBUG NORMALIZE: '{text}' → '{result}'")
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
    try:
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
            prompt = LLM_PROMPT_TEMPLATE.format(question=question.question.strip())
            result = ask_gemini(prompt)
            print("LLM RESPONSE:", result)
            
            if not result:
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
            except json.JSONDecodeError:
                # Regex ile JSON çıkarmaya çalış
                json_match = re.search(r'\{.*\}', result_clean, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
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

    except Exception as e:
        print(f"Error: {e}")
        
        # HATA DURUMUNU LOGLA
        log_failed_query(
            question.question.strip(), 
            "error", 
            str(e), 
            "system_error"
        )
        
        return {"answer": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."}_response(product, attribute)
            
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

    except Exception as e:
        print(f"Error: {e}")
        
        # HATA DURUMUNU LOGLA
        log_failed_query(
            question.question.strip(), 
            "error", 
            str(e), 
            "system_error"
        )
        
        return {"answer": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."}
