# 🚀 KobiBot.com Deployment Summary

## ✅ Tamamlanan İşlemler

### 1. Domain Configuration
- **kobibot.com** domain'i için subdomain yapısı oluşturuldu
- **admin.kobibot.com** - Admin paneli
- **api.kobibot.com** - Chat API
- **webhook.kobibot.com** - WhatsApp/Instagram webhook
- **customer.kobibot.com** - Müşteri onboarding
- **chat.kobibot.com** - Chat interface

### 2. Instagram Webhook Integration
- Instagram Basic Display API entegrasyonu eklendi
- Webhook handler'ları oluşturuldu
- OAuth redirect URI konfigürasyonu yapıldı
- Test endpoint'leri eklendi

### 3. Server Configuration Files
- **domain_config.py** - Subdomain yönetimi
- **deploy_to_server.py** - Otomatik deployment script
- **server_setup.sh** - Server kurulum script'i
- **manual_deployment_guide.md** - Manuel kurulum rehberi
- **requirements.txt** - Python dependencies

### 4. Nginx Reverse Proxy
- Tüm subdomain'ler için reverse proxy konfigürasyonu
- SSL sertifika desteği
- Port mapping (5004, 5006, 5007, 5008)

### 5. Systemd Services
- **kobibot-admin.service** - Admin paneli servisi
- **kobibot-api.service** - Chat API servisi
- **kobibot-webhook.service** - Webhook servisi
- **kobibot-customer.service** - Customer onboarding servisi

### 6. Environment Variables
- Production ortamı için .env konfigürasyonu
- Instagram API credentials
- WhatsApp webhook tokens
- Domain ayarları

## 🔧 Sonraki Adımlar

### 1. Server Erişimi Düzeltme
```bash
# AWS Console → EC2 → Connect → Session Manager
# Veya Security Group'tan SSH port'unu kontrol et
```

### 2. Manual Deployment
```bash
# Server'da çalıştır:
cd /home/ubuntu
git clone https://github.com/hbasri1/botum.git kobibot
cd kobibot
git checkout chatbot-optimization-jules

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Directories
mkdir -p uploads logs business_data embeddings data static templates

# Environment variables
cp .env.example .env  # ve düzenle

# Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/kobibot.com
sudo ln -sf /etc/nginx/sites-available/kobibot.com /etc/nginx/sites-enabled/
sudo nginx -t

# SSL certificates
sudo certbot --nginx -d kobibot.com -d admin.kobibot.com -d api.kobibot.com -d webhook.kobibot.com -d customer.kobibot.com -d chat.kobibot.com

# Systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kobibot-*
sudo systemctl start kobibot-*
```

### 3. DNS Configuration
AWS Route 53 veya domain provider'da:
```
A Record: kobibot.com → YOUR_SERVER_IP
A Record: *.kobibot.com → YOUR_SERVER_IP
```

### 4. Meta Developer Console Setup

#### Instagram Basic Display API
1. [Meta Developer Console](https://developers.facebook.com/)
2. Create App → Business → Other
3. Add Product → Instagram Basic Display
4. OAuth Redirect URI: `https://customer.kobibot.com/instagram/callback`
5. Add test users

#### WhatsApp Business API
1. WhatsApp Business → Configuration
2. Webhook URL: `https://webhook.kobibot.com/webhook`
3. Verify Token: `kobibot-webhook-verify-2024`
4. Subscribe to messages

### 5. Testing
```bash
# Health checks
curl https://api.kobibot.com/health
curl https://admin.kobibot.com/api/system/health
curl https://webhook.kobibot.com/webhook/status

# Webhook tests
curl -X POST https://webhook.kobibot.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"phone": "905551234567", "message": "test"}'

curl -X POST https://webhook.kobibot.com/instagram/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "12345", "message": "Instagram test"}'
```

## 📋 Checklist

### Server Setup
- [ ] SSH erişimi düzeltildi
- [ ] Repository clone edildi
- [ ] Python environment kuruldu
- [ ] Dependencies yüklendi
- [ ] Environment variables ayarlandı
- [ ] Directories oluşturuldu

### Web Server
- [ ] Nginx konfigüre edildi
- [ ] SSL sertifikaları alındı
- [ ] Reverse proxy test edildi
- [ ] Firewall ayarları yapıldı

### Services
- [ ] Systemd servisleri oluşturuldu
- [ ] Servisler etkinleştirildi
- [ ] Servisler başlatıldı
- [ ] Log'lar kontrol edildi

### DNS & Domain
- [ ] DNS kayıtları oluşturuldu
- [ ] Domain propagation tamamlandı
- [ ] Subdomain'ler erişilebilir
- [ ] SSL sertifikaları geçerli

### API Integrations
- [ ] Instagram App oluşturuldu
- [ ] OAuth redirect URI ayarlandı
- [ ] WhatsApp webhook konfigüre edildi
- [ ] Test kullanıcıları eklendi

### Testing
- [ ] Health endpoint'leri test edildi
- [ ] Webhook'lar test edildi
- [ ] Instagram OAuth test edildi
- [ ] WhatsApp mesaj test edildi

## 🌐 Final URLs

Deployment tamamlandığında:

- **Ana Site**: https://kobibot.com
- **Admin Panel**: https://admin.kobibot.com
- **Chat API**: https://api.kobibot.com
- **Webhook**: https://webhook.kobibot.com
- **Customer Portal**: https://customer.kobibot.com
- **Chat Interface**: https://chat.kobibot.com

## 🔍 Troubleshooting

### Common Issues
1. **SSH Connection Timeout**: AWS Security Group veya UFW firewall
2. **SSL Certificate Error**: DNS propagation veya Certbot configuration
3. **Service Not Starting**: Environment variables veya file permissions
4. **Webhook Verification Failed**: Token mismatch veya URL configuration

### Log Locations
```bash
# Service logs
sudo journalctl -u kobibot-* -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Application logs
tail -f /home/ubuntu/kobibot/logs/*.log
```

---

**🎉 KobiBot sistemi kobibot.com domain'i ile Instagram webhook entegrasyonu için hazır!**

Deployment tamamlandığında tam otomatik müşteri onboarding, Instagram entegrasyonu ve WhatsApp webhook sistemi çalışır durumda olacak.