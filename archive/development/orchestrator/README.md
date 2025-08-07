# Multi-Tenant Chatbot Orchestrator

Çok-işletmeli (multi-tenant) yapay zeka chatbot orkestratörü. Bu sistem, gelen mesajları işleyerek fine-tune edilmiş Gemini LLM ile iletişim kurar ve iş mantığını yürütür.

## 🏗️ Mimari

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Webhook       │    │   Orchestrator   │    │   Fine-tuned    │
│   Endpoints     │───▶│   (FastAPI)      │───▶│   Gemini LLM    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Business       │    │   Redis         │
│   Database      │◀───│   Logic Router   │───▶│   Cache/Session │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Özellikler

### 🎯 Temel Özellikler
- **Multi-tenant yapı**: Birden fazla işletme desteği
- **Session yönetimi**: Redis tabanlı gelişmiş oturum yönetimi
- **Fine-tuned LLM**: Vertex AI Gemini entegrasyonu
- **İş mantığı yönlendirici**: Intent bazlı akıllı routing

### 🧠 Akıllı Önbellekleme Sistemi
- **LLM Cache**: Aynı sorular için LLM çağrısını atla (1 saat TTL)
- **Intent Cache**: İade politikası gibi sabit cevaplar (24 saat TTL)
- **Otomatik Cache Invalidation**: Veri güncellendiğinde cache temizleme
- **Ürün Cache Yönetimi**: Fiyat/stok güncellemelerinde akıllı temizlik

### 🔒 Güvenlik ve Doğrulama
- **Pydantic Doğrulama**: LLM yanıtlarının katı şema kontrolü
- **Güven skoru kontrolü**: %80 altı güven skorunda otomatik eskalasyon
- **JSON Doğrulama**: Bozuk yanıtlarda otomatik eskalasyon

### 🎫 Eskalasyon Sistemi
- **İnsana aktarma sistemi**: Ticket tabanlı eskalasyon
- **Bildirim sistemi**: Slack, email ve webhook entegrasyonları
- **Öncelik yönetimi**: Otomatik öncelik belirleme

### 📊 Monitoring ve Yönetim
- **Kapsamlı logging**: Structured JSON logging
- **Health monitoring**: Sistem sağlık kontrolleri
- **Cache istatistikleri**: Detaylı cache performans metrikleri
- **Admin API'leri**: Cache yönetimi ve ürün güncelleme
- **Docker desteği**: Kolay deployment

## 📋 Gereksinimler

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Google Cloud Platform hesabı (Vertex AI için)

## 🛠️ Kurulum

### 1. Repository'yi klonlayın
```bash
git clone <repository-url>
cd orchestrator
```

### 2. Sanal ortam oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

### 4. Çevre değişkenlerini ayarlayın
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

### 5. Veritabanını başlatın
```bash
# Docker ile
docker-compose up -d postgres redis

# Veya manuel olarak PostgreSQL ve Redis'i başlatın
```

### 6. Uygulamayı çalıştırın
```bash
python run.py
```

## 🐳 Docker ile Çalıştırma

```bash
# Tüm servisleri başlat
docker-compose up -d

# Logları izle
docker-compose logs -f orchestrator

# Servisleri durdur
docker-compose down
```

## 📡 API Kullanımı

### Ana Webhook Endpoint

```bash
POST /webhook
Content-Type: application/json

{
    "mesaj_metni": "gecelik fiyatı ne kadar?",
    "kullanici_id": "user123",
    "isletme_id": "business456",
    "platform": "whatsapp"
}
```

### Yanıt Formatı

```json
{
    "success": true,
    "message": "Test Gecelik\nFiyat: 299.99 TL",
    "session_id": "session-uuid",
    "response_time_ms": 150
}
```

### Admin API'leri

#### Cache Yönetimi
```bash
# İşletme cache'ini temizle
POST /admin/cache/invalidate/{isletme_id}

# Ürün cache'ini temizle
POST /admin/cache/invalidate-product/{isletme_id}/{product_id}

# Cache istatistikleri
GET /admin/cache/stats/{isletme_id}
```

#### Ürün Yönetimi (Cache Invalidation ile)
```bash
PUT /admin/products/{isletme_id}/{product_id}
Content-Type: application/json

{
    "price": 349.99,
    "stock_quantity": 15
}
```

#### İşletme Meta Bilgi Güncelleme
```bash
PUT /admin/business/{isletme_id}/meta
Content-Type: application/json

{
    "info_type": "iade",
    "new_value": "İade 30 gün içinde yapılabilir"
}
```

### Sistem Endpoint'leri

```bash
# Sağlık kontrolü
GET /health

# İşletme istatistikleri
GET /stats/{isletme_id}
```

## 🔧 Konfigürasyon

### Çevre Değişkenleri

```bash
# Veritabanı
DATABASE_URL=postgresql://user:password@localhost/chatbot_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL_NAME=your-fine-tuned-model
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Eskalasyon
CONFIDENCE_THRESHOLD=0.80
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ESCALATION_EMAIL_RECIPIENTS=["support@company.com"]

# Uygulama
LOG_LEVEL=INFO
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
```

## 📊 Veritabanı Şeması

### İşletmeler (businesses)
- `id`: UUID (Primary Key)
- `name`: İşletme adı
- `meta_data`: JSON (telefon, iade, kargo bilgileri)
- `greeting_message`: Özel selamlama mesajı

### Ürünler (products)
- `id`: UUID (Primary Key)
- `business_id`: İşletme referansı
- `name`: Ürün adı
- `price`: Fiyat
- `stock_quantity`: Stok miktarı

### Etkileşimler (interactions)
- `id`: UUID (Primary Key)
- `session_id`: Oturum ID'si
- `user_message`: Kullanıcı mesajı
- `llm_response`: LLM yanıtı (JSON)
- `final_response`: Son yanıt

### Eskalasyon Ticket'ları (escalation_tickets)
- `id`: UUID (Primary Key)
- `ticket_id`: Benzersiz ticket ID'si
- `session_id`: Oturum referansı
- `escalation_reason`: Eskalasyon sebebi
- `status`: Ticket durumu (open, assigned, resolved)
- `priority`: Öncelik seviyesi (low, medium, high)
- `conversation_history`: Konuşma geçmişi (JSON)

## 🧪 Test

```bash
# Unit testler
pytest tests/

# Belirli bir test
pytest tests/test_webhook.py

# Coverage ile
pytest --cov=orchestrator tests/
```

## 📈 Monitoring

### Metrics Endpoint
```bash
GET /metrics
```

### Log Formatı
```json
{
    "timestamp": "2024-01-20T10:30:00Z",
    "level": "INFO",
    "service": "chatbot-orchestrator",
    "module": "main",
    "message": "HTTP request",
    "request_id": "req-123",
    "user_id": "user456",
    "business_id": "biz789"
}
```

## 🔒 Güvenlik

- API key authentication (opsiyonel)
- Rate limiting
- Input validation
- SQL injection koruması
- CORS ayarları

## 🚀 Deployment

### Production Checklist

- [ ] Çevre değişkenleri ayarlandı
- [ ] SSL sertifikaları kuruldu
- [ ] Veritabanı backup'ı ayarlandı
- [ ] Monitoring kuruldu
- [ ] Log rotation ayarlandı
- [ ] Health check'ler çalışıyor

### Scaling

- Horizontal scaling: Birden fazla orchestrator instance
- Database connection pooling
- Redis cluster
- Load balancer (Nginx)

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 Destek

Sorularınız için:
- Issue açın
- E-posta: support@example.com
- Dokümantasyon: [docs.example.com](https://docs.example.com)