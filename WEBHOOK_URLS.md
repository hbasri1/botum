# 🔗 KobiBot Webhook URL'leri

## 📱 Meta Developer Console için URL'ler

### WhatsApp Business API
```
Webhook URL: https://webhook.kobibot.com/webhook
Verify Token: kobibot-webhook-verify-2024
```

### Instagram Basic Display API
```
Webhook URL: https://webhook.kobibot.com/instagram/webhook
Verify Token: kobibot-webhook-verify-2024
OAuth Redirect URI: https://customer.kobibot.com/instagram/callback
```

## 🌐 Sistem URL'leri

### Ana Servisler (DNS sonrası)
- **Ana Site**: https://kobibot.com
- **Admin Panel**: https://admin.kobibot.com
- **Chat API**: https://api.kobibot.com
- **Webhook**: https://webhook.kobibot.com
- **Customer Portal**: https://customer.kobibot.com
- **Chat Interface**: https://chat.kobibot.com

### Geçici URL'ler (DNS öncesi)
- **Ana Site**: http://3.74.156.223:5004
- **Admin Panel**: http://3.74.156.223:5006
- **Chat API**: http://3.74.156.223:5004
- **Webhook**: http://3.74.156.223:5007
- **Customer Portal**: http://3.74.156.223:5008

## 🧪 Test URL'leri

### WhatsApp Webhook Test
```bash
curl -X POST https://webhook.kobibot.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"phone": "905551234567", "message": "test mesajı"}'
```

### Instagram Webhook Test
```bash
curl -X POST https://webhook.kobibot.com/instagram/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "12345", "message": "Instagram test"}'
```

### Health Check
```bash
curl https://webhook.kobibot.com/webhook/status
```

## 📋 Meta Developer Console Ayarları

### 1. WhatsApp Business API
1. Meta Business Manager → WhatsApp
2. Configuration → Webhook
3. **Webhook URL**: `https://webhook.kobibot.com/webhook`
4. **Verify Token**: `kobibot-webhook-verify-2024`
5. **Webhook Fields**: `messages` seçin

### 2. Instagram Basic Display API
1. Meta Developer Console → Your App
2. Instagram Basic Display → Settings
3. **Valid OAuth Redirect URIs**: `https://customer.kobibot.com/instagram/callback`
4. **Deauthorize Callback URL**: `https://customer.kobibot.com/instagram/deauth`

### 3. Instagram Access Token
Mevcut token'ınız:
```
IGAAVPSog3VRBBZAE5LZAmxPd3dtZAEJ6d0M4ZAl9sZAXhPTmRmTWQtRExhbEtKUkxMbkJRWWZAGLXBhbFU4SDlhODltZAFJvOTlrOFFqVDBZAV2cteGR5ZA1M4NURndGw2bGZAkR3dKVDY5dEc5a0xLdjl6c0ZAnVHFNVU9Idk1felJxZAVpfRQZDZD
```

Bu token sisteme eklendi ve customer onboarding'de kullanılacak.

## 🔄 GitHub Webhook
```
URL: http://3.74.156.223:9000/deploy
Content type: application/json
Secret: kobibot-deploy-secret-2024
Events: Just the push event
```

✅ **Webhook başarıyla kuruldu ve test edildi!**