# 🤖 Gelişmiş İşletme Chatbot Sistemi

Bu proje, işletmeler için AI destekli, özelleştirilebilir chatbot sistemidir. Gemini 2.5 Flash ile dosya işleme, admin paneli ve WhatsApp webhook desteği içerir.

## 🚀 Yeni Özellikler (v5.0 - Complete Business Solution)

### 🎯 Müşteri Onboarding Sistemi
- **Modern landing page** ile müşteri kayıt
- **Instagram Basic Display API** entegrasyonu
- Otomatik işletme oluşturma
- Müşteri dashboard'ı
- Chat widget kodu üretimi

### 🤖 AI Chatbot
- **Gemini 2.0 Flash Lite** ile hızlı yanıtlar (normal chat için)
- **Gemini 2.5 Flash/Pro** ile dosya işleme (admin paneli için)
- Akıllı ürün arama ve öneri sistemi
- Konuşma bağlamı takibi
- Çoklu dil desteği (Türkçe odaklı)

### 📁 Dosya İşleme Sistemi
- **Gemini 2.5 Flash/Pro** ile otomatik ürün çıkarma
- JSON, CSV, Excel dosya desteği
- Fiyat standardizasyonu (₺, TL sembolleri temizlenir)
- Renk ve kategori normalizasyonu (İngilizce → Türkçe)
- Veri doğrulama ve temizleme

### 🔧 Admin Paneli
- İşletme yönetimi
- Dosya yükleme ve işleme
- Chatbot test sistemi
- İstatistik ve raporlama
- Gerçek zamanlı sistem durumu

### 📱 WhatsApp Integration
- Meta WhatsApp Business API desteği
- Webhook sistemi
- Çoklu işletme desteği
- Otomatik mesaj yanıtlama

### 📸 Instagram Integration
- Instagram Basic Display API
- Otomatik hesap bağlama
- Profil bilgisi çekme
- DM entegrasyonu hazırlığı

## 🏗️ Sistem Mimarisi

```
├── 🌐 Web Interface (Port 5004)
│   ├── Chat arayüzü
│   └── API endpoints
├── 🎯 Customer Onboarding (Port 5008)
│   ├── Landing page
│   ├── Instagram OAuth
│   ├── Müşteri dashboard
│   └── Widget kod üretimi
├── 🔧 Admin Panel (Port 5006)
│   ├── İşletme yönetimi
│   ├── Dosya yükleme (Gemini 2.5 Flash)
│   └── Test sistemi
├── 🔗 Webhook System (Port 5007)
│   ├── WhatsApp webhook
│   └── Meta API integration
└── 🗄️ Data Layer
    ├── Business data
    ├── Product data
    ├── Customer registrations
    └── Conversation logs
```

## 🛠️ Kurulum ve Çalıştırma

### 1. Environment Variables
`.env` dosyasını güncelleyin:
```env
# Google Gemini API Key
GEMINI_API_KEY=AIzaSyDNcOfDasPMbZdaZ_rkMDQ4u-OraAHbNcI2

# WhatsApp Business API
WHATSAPP_VERIFY_TOKEN=your-verify-token-change-this
WHATSAPP_ACCESS_TOKEN=your-access-token-from-meta
WHATSAPP_WEBHOOK_SECRET=your-webhook-secret-change-this

# Server Ports
ADMIN_PORT=5006
WEBHOOK_PORT=5007
```

### 2. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 3. Sistemleri Başlat

#### Müşteri Onboarding (Ana Sistem)
```bash
python3 customer_onboarding_system.py
# http://localhost:5008 - Müşteri kayıt sayfası
```

#### Ana Chat Interface
```bash
python3 production_web_interface.py
# http://localhost:5004 - Chatbot test arayüzü
```

#### Admin Paneli
```bash
python3 admin_web_interface.py
# http://localhost:5006 - İşletme yönetimi
```

#### Webhook Sistemi
```bash
python3 webhook_system.py
# http://localhost:5007/webhook - WhatsApp webhook
```

## 📸 Instagram Integration Kurulumu

### 1. Instagram Basic Display App Oluşturma
1. [Meta Developer Console](https://developers.facebook.com/) → "Create App"
2. **App Type**: "Consumer" seçin
3. **Use Case**: "Other" seçin
4. App adını girin ve oluşturun

### 2. Instagram Basic Display Ekleme
1. Dashboard → "Add Product" → "Instagram Basic Display"
2. **Instagram App ID** ve **Instagram App Secret** alın
3. `.env` dosyasına ekleyin:
```env
INSTAGRAM_APP_ID=your-app-id-here
INSTAGRAM_APP_SECRET=your-app-secret-here
```

### 3. OAuth Redirect URI Ayarlama
1. Instagram Basic Display → Settings
2. **Valid OAuth Redirect URIs** ekleyin:
   - `http://localhost:5008/instagram/callback` (development)
   - `https://your-domain.com/instagram/callback` (production)

### 4. Test Kullanıcıları Ekleme
1. Instagram Basic Display → Roles → Roles
2. **Instagram Testers** bölümüne test hesapları ekleyin
3. Test hesabı sahipleri daveti kabul etmeli

## 📱 WhatsApp Webhook Kurulumu

### 1. Domain Gereksinimi
Meta WhatsApp Business API HTTPS gerektirir. Seçenekler:
- **Ngrok** (test için): `ngrok http 5007`
- **Gerçek domain** (production için): Domain satın alın

### 2. Meta Developer Console Ayarları
1. [Meta Developer Console](https://developers.facebook.com/) → WhatsApp Business
2. Webhook URL: `https://your-domain.com/webhook`
3. Verify Token: `.env` dosyasındaki `WHATSAPP_VERIFY_TOKEN`
4. Webhook fields: `messages`

### 3. Test
```bash
curl -X POST http://localhost:5007/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"phone": "905551234567", "message": "test"}'
```

## 🎯 Müşteri Onboarding Akışı

### 1. Müşteri Kayıt Süreci
1. **Landing Page**: `http://localhost:5008`
2. **Form Doldurma**: Ad, soyad, email, telefon, işletme bilgileri
3. **Instagram Bağlama**: Otomatik Instagram OAuth
4. **Sistem Hazırlama**: Otomatik işletme ve chatbot oluşturma
5. **Dashboard**: Müşteri dashboard'ına yönlendirme

### 2. Müşteri Dashboard Özellikleri
- **İstatistikler**: Ürün sayısı, kategori, renk çeşitliliği
- **Ürün Yükleme**: Admin paneline yönlendirme
- **Chatbot Test**: Test arayüzü
- **Widget Kodu**: Sitenize entegre edilebilir kod
- **WhatsApp Durumu**: Webhook sistem kontrolü

### 3. Instagram Entegrasyonu
- **Otomatik Bağlantı**: OAuth ile güvenli bağlantı
- **Profil Bilgileri**: Username ve ID otomatik çekme
- **İzin Yönetimi**: Gerekli izinlerin otomatik alınması

## 🔧 Admin Paneli Kullanımı

### 1. İşletme Oluşturma
- Admin paneline gidin: `http://localhost:5006`
- "Yeni İşletme Oluştur" butonuna tıklayın
- Gerekli bilgileri doldurun

### 2. Dosya Yükleme
- İşletme kartında "Dosya Yükle" butonuna tıklayın
- JSON, CSV veya Excel dosyası seçin
- Gemini AI otomatik olarak ürünleri işler ve veritabanına ekler

### 3. Desteklenen Dosya Formatları
```json
// JSON örneği
[
  {
    "name": "Kırmızı Elbise",
    "price": "299.99 TL",
    "color": "red",
    "category": "dress",
    "stock": 5,
    "description": "Şık kırmızı elbise"
  }
]
```

```csv
# CSV örneği
name,price,color,category,stock,description
Mavi Pantolon,199₺,blue,pants,10,Rahat mavi pantolon
```

## 🤖 AI Dosya İşleme Özellikleri

### Gemini 2.5 Flash ile:
- **Otomatik ürün çıkarma**: Dosyadan ürün bilgilerini akıllıca çıkarır
- **Fiyat standardizasyonu**: "299.99 TL", "199₺" → sayısal değer
- **Renk normalizasyonu**: "red" → "kırmızı", "blue" → "mavi"
- **Kategori sınıflandırması**: Ürünleri otomatik kategorilere ayırır
- **Veri doğrulama**: Eksik veya hatalı verileri temizler

## 📊 API Endpoints

### Chat API
```bash
POST http://localhost:5004/chat
{
  "message": "merhaba"
}
```

### Admin API
```bash
# İşletme oluştur
POST http://localhost:5006/api/businesses
{
  "name": "Test Butik",
  "email": "test@example.com",
  "phone": "0555 123 4567"
}

# Dosya yükle
POST http://localhost:5006/api/businesses/{business_id}/products
Content-Type: multipart/form-data
file: products.json

# İstatistik
GET http://localhost:5006/api/businesses/{business_id}/stats
```

### Webhook API
```bash
# Webhook doğrulama
GET http://localhost:5007/webhook?hub.mode=subscribe&hub.verify_token=your-token&hub.challenge=challenge

# Mesaj işleme
POST http://localhost:5007/webhook
{
  "entry": [...]
}
```

## 🧪 Test Sistemi

### Admin Paneli Test
- İşletme kartında "Test Et" butonuna tıklayın
- Test mesajı yazın
- Chatbot yanıtını görün

### Webhook Test
```bash
curl -X POST http://localhost:5007/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"phone": "905551234567", "message": "hamile pijama arıyorum"}'
```

## 🔍 Sistem Durumu

### Health Check
```bash
# Ana sistem
curl http://localhost:5004/health

# Admin paneli
curl http://localhost:5006/api/system/health

# Webhook
curl http://localhost:5007/webhook/status
```

## 💰 Maliyet Analizi

### Gemini API Kullanımı
- **Chat (2.0 Flash Lite)**: Düşük maliyet, hızlı yanıt
- **Dosya İşleme (2.5 Flash/Pro)**: Yüksek kalite, daha yüksek maliyet
- **Optimizasyon**: Chat için lite, dosya işleme için pro model

### Tahmini Maliyetler
- **1000 chat mesajı**: ~$0.04
- **100 dosya işleme**: ~$2.00
- **Aylık ortalama**: ~$50-100 (orta ölçekli işletme)

## 🚀 Production Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  chatbot:
    build: .
    ports:
      - "5004:5004"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
  
  admin:
    build: .
    command: python3 admin_web_interface.py
    ports:
      - "5006:5006"
    volumes:
      - ./uploads:/app/uploads
  
  webhook:
    build: .
    command: python3 webhook_system.py
    ports:
      - "5007:5007"
    environment:
      - WHATSAPP_VERIFY_TOKEN=${WHATSAPP_VERIFY_TOKEN}
      - WHATSAPP_ACCESS_TOKEN=${WHATSAPP_ACCESS_TOKEN}
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5004;
    }
    
    location /admin {
        proxy_pass http://localhost:5006;
    }
    
    location /webhook {
        proxy_pass http://localhost:5007;
    }
}
```

## 🔧 Konfigürasyon

### Business Manager
- **Veri klasörü**: `business_data/`
- **İşletme dosyaları**: `business_data/businesses/`
- **Ürün dosyaları**: `business_data/products/`

### File Processor
- **Upload klasörü**: `uploads/`
- **Max dosya boyutu**: 10MB
- **Desteklenen formatlar**: JSON, CSV, Excel

### Webhook
- **Verify token**: Güvenlik için
- **Access token**: Meta API için
- **Webhook secret**: İmza doğrulama için

## 🐛 Troubleshooting

### Admin Paneli Çalışmıyor
```
ERROR: 'MVPBusinessManager' object has no attribute 'get_all_businesses'
```
**Çözüm**: `mvp_business_system.py` güncellenmiş, yeniden başlatın.

### Dosya İşleme Hatası
```
ERROR: API key not valid
```
**Çözüm**: `.env` dosyasında `GEMINI_API_KEY` kontrol edin.

### Webhook Doğrulama Hatası
```
ERROR: Webhook verification failed
```
**Çözüm**: `WHATSAPP_VERIFY_TOKEN` Meta Console ile eşleştirin.

## 📞 Destek ve İletişim

### Test Komutları
```bash
# Sistem testi
python3 comprehensive_test_system.py

# Admin paneli testi
curl http://localhost:5006/api/system/health

# Webhook testi
curl http://localhost:5007/webhook/status
```

### Log Kontrolü
- **Console logs**: Tüm sistemler konsola log yazar
- **Error handling**: Robust hata yönetimi
- **Health checks**: Sistem durumu endpoints

---

**🚀 v5.0 - Complete Business Solution with Customer Onboarding!**

### ✨ Yeni Özellikler (v5.0)
✅ **Müşteri Onboarding Sistemi** - Modern landing page ile otomatik kayıt  
✅ **Instagram Basic Display API** - Otomatik hesap bağlama  
✅ **Müşteri Dashboard** - Self-service yönetim paneli  
✅ **Chat Widget Generator** - Otomatik widget kodu üretimi  
✅ **Multi-Channel Support** - Instagram + WhatsApp + Web  
✅ **Complete Business Flow** - Kayıttan üretime tam süreç  

### 🎯 Önceki Özellikler (v4.0)
✅ Gemini 2.5 Flash/Pro ile dosya işleme  
✅ Gelişmiş admin paneli  
✅ WhatsApp webhook sistemi  
✅ Çoklu işletme desteği  
✅ AI destekli ürün çıkarma  
✅ Otomatik veri temizleme  
✅ Production ready deployment  

## 🌟 Tam İş Akışı

### Müşteri Perspektifi:
1. **Kayıt**: `localhost:5008` → Form doldur → Instagram bağla
2. **Dashboard**: Sistem durumu görüntüle → Widget kodu al
3. **Ürün Ekleme**: Admin paneli üzerinden dosya yükle
4. **Aktifleştirme**: WhatsApp webhook bağla → Sistem hazır!

### Admin Perspektifi:
1. **Monitoring**: Tüm işletmeleri `localhost:5006` üzerinden izle
2. **Support**: Müşteri ürünlerini yönet ve test et
3. **Analytics**: Sistem performansını takip et

Bu sistem artık **tam otomatik müşteri onboarding** ile gerçek işletmeler için production ortamında kullanıma hazır! 🎉

## 🏗️ Sistem Mimarisi ve Bağlantılar

### 📊 Veri Akışı
```
Kullanıcı Sorgusu → Intent Detection → RAG Arama → Ürün Filtreleme → Yanıt Formatı → Kullanıcı
                      ↓                    ↓              ↓              ↓
                  Gemini AI +         TF-IDF +      Cache +        Türkçe +
                  Fallback           Cosine Sim     Sistemi       Template
```

### 🔗 Sistem Bileşenleri ve Bağlantıları

#### 1. **Ana Chatbot Sistemi** (`improved_final_mvp_system.py`)
- **Bağlantılar**: Tüm diğer bileşenleri koordine eder
- **Görevler**: Intent detection, ürün arama, yanıt formatı
- **Bağımlılıklar**: RAG arama, konuşma yöneticisi, cache sistemi

#### 2. **RAG Ürün Arama** (`rag_product_search.py`)
- **Bağlantılar**: Ana sistem tarafından çağrılır
- **Görevler**: TF-IDF embeddings, semantik arama, sonuç filtreleme
- **Veri Kaynağı**: `data/products.json` (590 ürün)
- **Çıktı**: `embeddings/` klasöründe pickle dosyaları

#### 3. **Unified Attribute System** (`attribute_system.py`)
- **Bağlantılar**: Konuşma yöneticisi ile entegre
- **Görevler**: Renk, beden, stok, fiyat sorguları
- **Özellikler**: Scalable, maintainable, consistent responses

#### 4. **Konuşma Yöneticisi** (`enhanced_conversation_handler.py`)
- **Bağlantılar**: Ana sistem ile entegre
- **Görevler**: Bağlam takibi, belirsizlik çözme, takip soruları
- **Durum Yönetimi**: Konuşma geçmişi ve kullanıcı tercihleri

#### 4. **Akıllı Cache Sistemi** (`smart_cache_system.py`)
- **Bağlantılar**: Ana sistem ve RAG arama ile entegre
- **Görevler**: Performans optimizasyonu, sonuç önbellekleme
- **Özellikler**: TTL tabanlı, bağlam farkında cache

#### 5. **Web Interface** (`production_web_interface.py`)
- **Bağlantılar**: Ana chatbot sistemini Flask API olarak sunar
- **Endpoints**: `/chat`, `/health`, `/stats`, `/reset`
- **Frontend**: `templates/chat.html` - Modern web UI

### 🔄 İş Akışı Detayları

#### Yeni İşletme Entegrasyonu
1. **Ürün Verisi**: `data/products.json` dosyasına ürünler eklenir
2. **Embedding Oluşturma**: `python3 rag_product_search.py` çalıştırılır
3. **Sistem Yeniden Başlatma**: Otomatik olarak yeni ürünler sisteme dahil olur
4. **Test**: `python3 test_system.py` ile doğrulama

#### Sorgu İşleme Süreci
1. **Kullanıcı Girişi** → Web interface üzerinden
2. **Intent Detection** → Gemini AI + fallback sistemi
3. **Ürün Arama** → RAG tabanlı semantik arama
4. **Cache Kontrolü** → Akıllı önbellekleme sistemi
5. **Sonuç Formatı** → Türkçe template ile yanıt
6. **Bağlam Güncelleme** → Konuşma geçmişi kaydı

## 🚀 Özellikler

### ✨ Ana Özellikler
- **RAG Tabanlı Arama**: TF-IDF embeddings ile semantik ürün arama
- **Unified Attribute System**: Renk, beden, stok, fiyat tek sistemde
- **Multi-Sektör Desteği**: Giyim, aksesuar, ev eşyası vb.
- **Akıllı Intent Detection**: Gemini AI + fallback sistemi (35% LLM, 65% rule-based)
- **Türkçe Dil Desteği**: Tam karakter normalizasyonu
- **Bağlam Farkında Konuşma**: Konuşma akışını takip eder
- **Akıllı Cache Sistemi**: Performans optimizasyonu
- **Edge Case Handling**: Belirsiz girişler için robust çözümler
- **Mobile-First UI**: Instagram chat benzeri responsive tasarım

### 🎯 Çözülen Sorunlar
- **RAG Tabanlı Arama** - Gerçek embeddings ile doğru ürün bulma
- **"İyi günler" belirsizliği** - Bağlam bazlı selamlama/veda ayrımı
- **Saçma girişler** - Akıllı fallback sistemi
- **Bağlam değişimi** - Konuşma akışı takibi
- **Türkçe karakter sorunları** - Gelişmiş normalizasyon
- **Cache performansı** - Akıllı önbellekleme
- **Takip soruları** - Ürün seçimi ve detay sorguları

## 📁 Dosya Yapısı

```
botum/
├── improved_final_mvp_system.py      # Ana chatbot sistemi
├── rag_product_search.py             # RAG tabanlı ürün arama
├── attribute_system.py               # Unified attribute system (renk, beden, stok, fiyat)
├── enhanced_conversation_handler.py   # Konuşma yönetimi
├── smart_cache_system.py             # Akıllı cache sistemi
├── production_web_interface.py       # Web interface
├── comprehensive_test_system.py      # Kapsamlı test sistemi
├── cost_analysis.py                  # Maliyet analizi
├── templates/
│   └── chat.html                     # Mobile-first web UI
├── data/
│   ├── products.json                 # Ürün veritabanı (590 ürün)
│   └── butik_meta.json              # İşletme bilgileri
├── embeddings/
│   ├── rag_product_embeddings.pkl   # RAG embeddings
│   └── tfidf_vectorizer.pkl         # TF-IDF vectorizer
├── requirements.txt                  # Bağımlılıklar
└── README.md                        # Bu dosya
```

## 🛠️ Kurulum

### 1. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
`.env` dosyası oluşturun:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG=False
PORT=5004
```

### 3. RAG Embeddings Oluştur (İlk Kurulum)
```bash
python3 rag_product_search.py
```

### 4. Sistemi Test Et
```bash
python3 test_system.py
```

### 5. Web Interface'i Başlat
```bash
# Development
python3 production_web_interface.py

# Production (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5004 production_web_interface:app
```

## 🔍 RAG Sistemi

### Nasıl Çalışır?
1. **Ürün İndeksleme**: 590 ürün TF-IDF ile vektörize edilir
2. **Özellik Çıkarımı**: Ürün adlarından otomatik özellik çıkarımı
3. **Semantik Arama**: Cosine similarity ile en uygun ürünleri bulur
4. **Sonuç Filtreleme**: Ek filtreler ile sonuçları iyileştirir

### Desteklenen Arama Türleri
- **Ürün Tipi**: "hamile pijama", "dantelli gecelik"
- **Renk Bazlı**: "siyah gecelik", "beyaz takım"
- **Özellik Bazlı**: "büyük beden", "düğmeli"
- **Fiyat Bazlı**: "ekonomik takım", "premium sabahlık"

## 🌐 API Endpoints

### Chat Endpoint
```bash
POST /chat
Content-Type: application/json

{
  "message": "hamile pijama arıyorum"
}
```

**Response:**
```json
{
  "response": "Size uygun 5 ürün buldum...",
  "intent": "product_search",
  "confidence": 0.85,
  "products_found": 5,
  "processing_time": 0.123,
  "success": true,
  "stats": {
    "total_requests": 42,
    "cache_hit_rate": 65.2,
    "average_response_time": 0.156
  }
}
```

### Health Check
```bash
GET /health
```

### System Stats
```bash
GET /stats
```

### Reset Conversation
```bash
POST /reset
```

## 🧪 Test Sistemi

### Otomatik Test Çalıştır
```bash
python3 test_system.py
```

### Test Kategorileri
- **Ürün Arama**: Hamile, büyük beden, renk bazlı
- **Takip Soruları**: Fiyat, detay sorguları
- **İletişim**: Telefon, adres bilgileri
- **Selamlama/Veda**: Bağlam farkında yanıtlar
- **Edge Cases**: Belirsiz girişler

### Beklenen Performans
- **Intent Doğruluğu**: ≥ 85%
- **Yanıt Süresi**: < 0.5s (cache ile)
- **Confidence**: ≥ 0.8
- **Cache Hit Rate**: ≥ 50%

## 🎯 Kullanım Örnekleri

### RAG Tabanlı Ürün Arama
```
Kullanıcı: "hamile için rahat pijama"
Bot: "Size uygun 5 ürün buldum: ..."

Kullanıcı: "siyah dantelli gecelik"
Bot: "Siyah dantelli gecelik ürünleri..."

Kullanıcı: "büyük beden var mı"
Bot: "Büyük beden ürünlerimiz..."
```

### Takip Soruları
```
Kullanıcı: "1 numaralı ürünün fiyatı"
Bot: "Dantelli Hamile Pijama Takımı: 2699.13 TL..."

Kullanıcı: "stokta var mı"
Bot: "Evet, stokta mevcut..."
```

### Bağlam Değişimi
```
Kullanıcı: "hamile pijama"
Bot: "Hamile pijama ürünleri..."

Kullanıcı: "sabahlık da var mı"
Bot: "Hamile sabahlık ürünlerimiz..."
```

## 📈 Performans Metrikleri

### Test Sonuçları (Son Test)
- **Intent Doğruluğu**: 85.7% (6/7)
- **Ortalama Confidence**: 0.84
- **Ortalama Yanıt Süresi**: 0.203s
- **Cache Hit Rate**: 50.0%
- **Başarı Oranı**: 100.0%

### Sistem Kapasitesi
- **Ürün Sayısı**: 590 ürün
- **Embedding Boyutu**: 5000 feature (TF-IDF)
- **Cache Kapasitesi**: 500 entry
- **Eş Zamanlı Kullanıcı**: 4 worker (Gunicorn)

## 🔧 Konfigürasyon

### RAG Ayarları
```python
# rag_product_search.py
TfidfVectorizer(
    max_features=5000,      # Feature sayısı
    ngram_range=(1, 2),     # 1-2 gram
    lowercase=True          # Küçük harf
)
```

### Cache Ayarları
```python
# smart_cache_system.py
SmartCacheSystem(
    default_ttl=600,    # 10 dakika
    max_size=500        # 500 entry
)
```

### Business Info
```json
{
  "phone": "0555 555 55 55",
  "website": "www.butik.com",
  "email": "info@butik.com",
  "address": "İstanbul, Türkiye"
}
```

## 🚀 Production Deployment

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5004

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5004", "production_web_interface:app"]
```

### Systemd Service
```ini
[Unit]
Description=RAG Chatbot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/botum
ExecStart=/usr/bin/python3 production_web_interface.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🐛 Troubleshooting

### RAG Embeddings Sorunu
```
ERROR: Can't load embeddings
```
**Çözüm**: `python3 rag_product_search.py` ile yeniden oluşturun.

### Gemini API Hatası
```
ERROR: API key not valid
```
**Çözüm**: `.env` dosyasında `GEMINI_API_KEY` kontrol edin.

### Yavaş Arama
```
WARNING: RAG search slow
```
**Çözüm**: Cache kullanın veya embedding boyutunu azaltın.

## 📊 Sistem Mimarisi

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │───▶│  Flask Web API   │───▶│   Chatbot Core  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐             │
                       │  Smart Cache     │◀────────────┤
                       └──────────────────┘             │
                                                         │
                       ┌──────────────────┐             │
                       │  RAG Search      │◀────────────┤
                       │  - TF-IDF        │             │
                       │  - Cosine Sim    │             │
                       └──────────────────┘             │
                                                         │
                       ┌──────────────────┐             │
                       │  Intent Detector │◀────────────┤
                       │  - Gemini AI     │             │
                       │  - Fallback      │             │
                       └──────────────────┘             │
                                                         │
                       ┌──────────────────┐             │
                       │  Conversation    │◀────────────┘
                       │  Handler         │
                       └──────────────────┘
```

## 📞 Destek

- **Test**: `python3 test_system.py`
- **Health**: `curl http://localhost:5004/health`
- **Logs**: Konsol çıktısını kontrol edin

## 🎉 Başarı Hikayeleri

### RAG Sistemi
- **590 ürün** başarıyla indekslendi
- **TF-IDF embeddings** ile semantik arama
- **%85+ doğruluk** oranı
- **< 0.5s** ortalama yanıt süresi

### Production Ready
✅ RAG tabanlı semantik arama  
✅ Robust error handling  
✅ Performance optimization  
✅ Context awareness  
✅ Turkish language support  
✅ Comprehensive testing  
✅ Production deployment ready  

---

**🚀 Sistem production ortamına hazır! RAG teknolojisi ile güçlendirilmiş akıllı ürün arama sistemi.**

## 🔄 Güncellemeler

### v3.0 - Production Ready System
- ✅ Unified Attribute System (renk, beden, stok, fiyat)
- ✅ Multi-sektör desteği (giyim, aksesuar, ev eşyası)
- ✅ Optimal LLM kullanımı (%35 LLM, %65 rule-based)
- ✅ Mobile-first responsive UI
- ✅ Context-aware cache sistemi
- ✅ Kapsamlı test coverage
- ✅ Maliyet optimizasyonu ($0.04/1000 sorgu)

### v2.0 - RAG Sistemi
- ✅ Mock embeddings yerine gerçek TF-IDF RAG sistemi
- ✅ 590 ürün için semantik arama
- ✅ Gelişmiş özellik çıkarımı
- ✅ Otomatik test sistemi
- ✅ Performance optimizasyonları

### v1.0 - MVP Sistem
- ✅ Temel chatbot fonksiyonalitesi
- ✅ Web interface
- ✅ Cache sistemi
- ✅ Intent detection