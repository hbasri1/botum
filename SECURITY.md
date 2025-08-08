# 🔒 Güvenlik Rehberi

Bu dokümanda projenin güvenlik önlemleri ve best practice'leri açıklanmaktadır.

## 🚨 Güvenlik Açığı Bildirimi

Eğer bir güvenlik açığı keşfederseniz, lütfen hemen bildirin:
- **Email**: security@your-domain.com
- **Acil Durum**: Kritik güvenlik açıkları için derhal iletişime geçin

## 🔐 API Key ve Secret Yönetimi

### ✅ Güvenli Uygulamalar
- Tüm API key'ler environment variable'larda saklanır
- Production'da gerçek key'ler, development'ta placeholder'lar kullanılır
- `.env` dosyası `.gitignore`'da yer alır
- Hiçbir secret hardcode edilmez

### ❌ Yapılmaması Gerekenler
- API key'leri kod içinde hardcode etmeyin
- Secret'ları commit etmeyin
- Public repository'lerde gerçek credential'ları paylaşmayın

## 🛡️ Environment Variables

### Gerekli Environment Variables
```bash
# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key-here

# AWS Bedrock API
AWS_BEDROCK_API_KEY=your-aws-bedrock-api-key-here

# WhatsApp Business API
WHATSAPP_VERIFY_TOKEN=your-verify-token-change-this
WHATSAPP_ACCESS_TOKEN=your-access-token-from-meta
WHATSAPP_WEBHOOK_SECRET=your-webhook-secret-change-this

# Instagram Basic Display API
INSTAGRAM_APP_ID=your-instagram-app-id-here
INSTAGRAM_APP_SECRET=your-instagram-app-secret-here

# Flask Secret Key
SECRET_KEY=your-secret-key-change-in-production
```

### Production Deployment
```bash
# .env dosyasını production server'a güvenli şekilde kopyalayın
scp -i your-key.pem .env user@server:/path/to/app/

# Dosya izinlerini kısıtlayın
chmod 600 .env
```

## 🔍 Güvenlik Taraması

### Otomatik Güvenlik Kontrolü
```bash
# Gerçek güvenlik açıklarını tara
python3 final_security_check.py

# Kapsamlı güvenlik taraması
python3 security_check.py
```

### Manuel Kontrol Listesi
- [ ] Tüm API key'ler environment variable'larda
- [ ] Hiçbir hardcoded secret yok
- [ ] `.env` dosyası `.gitignore`'da
- [ ] Production'da güçlü secret key'ler kullanılıyor
- [ ] HTTPS kullanılıyor (production)
- [ ] Rate limiting aktif
- [ ] CORS whitelist yapılandırılmış

## 🌐 Network Güvenliği

### CORS Konfigürasyonu
```python
CORS(app, origins=[
    "https://api.whatsapp.com",
    "https://graph.facebook.com", 
    "https://webhook.your-domain.com",
    "https://your-domain.com",
    "http://localhost:5007"  # Development only
])
```

### Rate Limiting
```python
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour", "10 per minute"]
)
```

## 🔒 HTTPS ve SSL

### Production SSL Kurulumu
```bash
# Let's Encrypt ile SSL sertifikası
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# SSL sertifikasını otomatik yenile
sudo crontab -e
0 12 * * * /usr/bin/certbot renew --quiet
```

### SSL Doğrulama
```bash
# SSL sertifikasını kontrol et
curl -I https://your-domain.com

# SSL rating kontrolü
curl -s https://api.ssllabs.com/api/v3/analyze?host=your-domain.com
```

## 🛠️ Güvenlik Araçları

### 1. Güvenlik Tarayıcısı
- `security_check.py`: Kapsamlı güvenlik taraması
- `final_security_check.py`: Gerçek tehdit tespiti

### 2. .gitignore Koruması
```gitignore
# Security - Never commit these
*.key
*.pem
*.p12
*.pfx
secrets/
credentials/
*_secret.*
*_key.*
*_token.*
*_password.*
```

### 3. Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
python3 final_security_check.py
if [ $? -ne 0 ]; then
    echo "❌ Security check failed! Commit blocked."
    exit 1
fi
```

## 📋 Güvenlik Checklist

### Development
- [ ] Environment variables kullanılıyor
- [ ] Placeholder değerler commit ediliyor
- [ ] Güvenlik taraması geçiyor
- [ ] .env dosyası ignore ediliyor

### Staging
- [ ] Gerçek API key'ler test ediliyor
- [ ] HTTPS kullanılıyor
- [ ] Rate limiting test ediliyor
- [ ] CORS konfigürasyonu doğru

### Production
- [ ] Tüm secret'lar güvenli
- [ ] SSL sertifikası aktif
- [ ] Firewall kuralları yapılandırılmış
- [ ] Log monitoring aktif
- [ ] Backup stratejisi mevcut

## 🚨 Incident Response

### Güvenlik Açığı Tespit Edildiğinde
1. **Derhal**: Etkilenen servisleri durdur
2. **5 dakika**: Güvenlik açığını değerlendir
3. **15 dakika**: Geçici çözüm uygula
4. **1 saat**: Kalıcı çözüm geliştir
5. **24 saat**: Post-mortem raporu hazırla

### API Key Sızıntısı Durumunda
1. Sızan key'i derhal iptal et
2. Yeni key oluştur ve güvenli şekilde dağıt
3. Etkilenen sistemleri yeniden başlat
4. Log'ları kontrol et
5. Güvenlik taraması yap

## 📞 İletişim

- **Güvenlik Ekibi**: security@your-domain.com
- **Acil Durum**: +90 XXX XXX XX XX
- **Slack**: #security-alerts

---

**Son Güncelleme**: 2025-08-08  
**Güvenlik Seviyesi**: ✅ SECURE  
**Son Tarama**: 2025-08-08 - Temiz