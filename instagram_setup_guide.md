# Instagram Integration Setup Guide for kobibot.com

## 🎯 Genel Bakış

Bu rehber, kobibot.com domain'i için Instagram Basic Display API ve webhook entegrasyonunu kurmanız için gerekli adımları içerir.

## 📋 Gereksinimler

- Meta Developer hesabı
- Instagram Business hesabı
- kobibot.com domain'i (SSL sertifikası ile)
- Server erişimi (AWS EC2)

## 🚀 Adım 1: Meta Developer Console Setup

### 1.1 Yeni App Oluşturma
1. [Meta Developer Console](https://developers.facebook.com/) → "Create App"
2. **App Type**: "Business" seçin
3. **Use Case**: "Other" seçin
4. **App Name**: "KobiBot Instagram Integration"
5. **App Contact Email**: admin@kobibot.com

### 1.2 Instagram Basic Display Ekleme
1. Dashboard → "Add Product" → "Instagram Basic Display"
2. **Instagram App ID** ve **Instagram App Secret** kaydedin
3. `.env` dosyasına ekleyin:
```env
INSTAGRAM_APP_ID=your-app-id-here
INSTAGRAM_APP_SECRET=your-app-secret-here
```

### 1.3 OAuth Redirect URI Ayarlama
1. Instagram Basic Display → Settings
2. **Valid OAuth Redirect URIs** ekleyin:
   - `https://customer.kobibot.com/instagram/callback`
   - `https://kobibot.com/instagram/callback` (backup)

### 1.4 Test Kullanıcıları Ekleme
1. Instagram Basic Display → Roles → Roles
2. **Instagram Testers** bölümüne test hesapları ekleyin
3. Test hesabı sahipleri daveti kabul etmeli

## 🔗 Adım 2: Instagram Webhook Setup (Gelecek için)

### 2.1 Webhook URL Konfigürasyonu
Instagram Messaging API için (şu anda Basic Display API messaging desteklemiyor):

**Webhook URL**: `https://webhook.kobibot.com/instagram/webhook`

### 2.2 Webhook Verification
```bash
# Test webhook verification
curl "https://webhook.kobibot.com/instagram/webhook?hub.mode=subscribe&hub.verify_token=kobibot-webhook-verify-2024&hub.challenge=test123"
```

## 📱 Adım 3: WhatsApp Business API Setup

### 3.1 WhatsApp Business Account
1. [Meta Business Manager](https://business.facebook.com/) → WhatsApp
2. **Phone Number**: İşletme telefon numaranızı ekleyin
3. **Verification**: SMS ile doğrulayın

### 3.2 Webhook Configuration
1. WhatsApp Business API → Configuration
2. **Webhook URL**: `https://webhook.kobibot.com/webhook`
3. **Verify Token**: `kobibot-webhook-verify-2024`
4. **Webhook Fields**: `messages` seçin

### 3.3 Access Token
1. WhatsApp Business API → API Setup
2. **Temporary Access Token** kopyalayın
3. `.env` dosyasına ekleyin:
```env
WHATSAPP_ACCESS_TOKEN=your-access-token-here
```

## 🛠️ Adım 4: Server Configuration

### 4.1 Environment Variables
Server'da `.env` dosyasını güncelleyin:
```env
# Instagram Basic Display API
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret
INSTAGRAM_REDIRECT_URI=https://customer.kobibot.com/instagram/callback

# WhatsApp Business API Configuration
WHATSAPP_VERIFY_TOKEN=kobibot-webhook-verify-2024
WHATSAPP_ACCESS_TOKEN=your-access-token-from-meta
WHATSAPP_WEBHOOK_SECRET=kobibot-webhook-secret-2024

# Domain Configuration
BASE_DOMAIN=kobibot.com
ADMIN_SUBDOMAIN=admin.kobibot.com
API_SUBDOMAIN=api.kobibot.com
WEBHOOK_SUBDOMAIN=webhook.kobibot.com
CUSTOMER_SUBDOMAIN=customer.kobibot.com
CHAT_SUBDOMAIN=chat.kobibot.com
```

### 4.2 Service Restart
```bash
# Restart all services
sudo systemctl restart kobibot-admin
sudo systemctl restart kobibot-api
sudo systemctl restart kobibot-webhook
sudo systemctl restart kobibot-customer
```

## 🧪 Adım 5: Testing

### 5.1 Instagram OAuth Test
1. `https://customer.kobibot.com` adresine gidin
2. Müşteri kayıt formunu doldurun
3. Instagram bağlantısını test edin

### 5.2 WhatsApp Webhook Test
```bash
# Test WhatsApp webhook
curl -X POST https://webhook.kobibot.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"phone": "905551234567", "message": "test mesajı"}'
```

### 5.3 Instagram Webhook Test (Future)
```bash
# Test Instagram webhook
curl -X POST https://webhook.kobibot.com/instagram/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "12345", "message": "Instagram test"}'
```

## 📊 Adım 6: Monitoring

### 6.1 Service Status
```bash
# Check all services
sudo systemctl status kobibot-admin
sudo systemctl status kobibot-api
sudo systemctl status kobibot-webhook
sudo systemctl status kobibot-customer
```

### 6.2 Logs
```bash
# View logs
sudo journalctl -u kobibot-webhook -f
sudo journalctl -u kobibot-customer -f
```

### 6.3 Webhook Status
```bash
# Check webhook status
curl https://webhook.kobibot.com/webhook/status
```

## 🔧 Troubleshooting

### Instagram OAuth Issues
```
ERROR: Invalid redirect URI
```
**Çözüm**: Meta Developer Console'da redirect URI'yi kontrol edin.

### WhatsApp Webhook Verification Failed
```
ERROR: Webhook verification failed
```
**Çözüm**: Verify token'ı Meta Console ile eşleştirin.

### SSL Certificate Issues
```
ERROR: SSL certificate not found
```
**Çözüm**: Certbot ile sertifikaları yenileyin:
```bash
sudo certbot renew
sudo systemctl restart nginx
```

## 📋 Checklist

### Instagram Setup
- [ ] Meta Developer App oluşturuldu
- [ ] Instagram Basic Display eklendi
- [ ] OAuth redirect URI ayarlandı
- [ ] Test kullanıcıları eklendi
- [ ] App ID ve Secret .env'e eklendi

### WhatsApp Setup
- [ ] WhatsApp Business hesabı oluşturuldu
- [ ] Webhook URL konfigüre edildi
- [ ] Verify token ayarlandı
- [ ] Access token alındı ve .env'e eklendi

### Server Setup
- [ ] Domain DNS ayarları yapıldı
- [ ] SSL sertifikaları kuruldu
- [ ] Nginx reverse proxy konfigüre edildi
- [ ] Systemd servisleri oluşturuldu
- [ ] Environment variables ayarlandı

### Testing
- [ ] Instagram OAuth test edildi
- [ ] WhatsApp webhook test edildi
- [ ] Tüm servisler çalışıyor
- [ ] Domain'ler erişilebilir

## 🌐 Final URLs

Kurulum tamamlandığında aşağıdaki URL'ler aktif olacak:

- **Ana Site**: https://kobibot.com
- **Admin Panel**: https://admin.kobibot.com
- **Chat API**: https://api.kobibot.com
- **Webhook**: https://webhook.kobibot.com
- **Customer Portal**: https://customer.kobibot.com
- **Chat Interface**: https://chat.kobibot.com

## 📞 Support

Sorun yaşarsanız:
1. Server loglarını kontrol edin
2. Service status'larını kontrol edin
3. Meta Developer Console'da webhook test edin
4. SSL sertifikalarını kontrol edin

---

**🚀 Instagram ve WhatsApp entegrasyonu ile kobibot.com hazır!**