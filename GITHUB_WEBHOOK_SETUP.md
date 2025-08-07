# 🚀 GitHub Webhook Otomatik Deploy Kurulumu

## 🎯 Amaç
Tek `git push` ile server'a otomatik deploy sistemi kuruyoruz. Artık kod değişikliği yaptığınızda sadece push yapacaksınız, server otomatik güncellenecek!

## 📋 Kurulum Adımları

### 1. Server'da Auto Deploy Sistemini Kur
```bash
# Auto deploy sistemini server'a kur
./setup_auto_deploy.sh
```

### 2. GitHub'da Webhook Ekle

#### 2.1 GitHub Repository'ye Git
- GitHub'da repo sayfanıza gidin
- **Settings** sekmesine tıklayın
- Sol menüden **Webhooks** seçin
- **Add webhook** butonuna tıklayın

#### 2.2 Webhook Ayarları
```
Payload URL: http://3.74.156.223:9000/deploy
Content type: application/json
Secret: kobibot-deploy-secret-2024
Which events: Just the push event
Active: ✅ (checked)
```

#### 2.3 Webhook'u Kaydet
- **Add webhook** butonuna tıklayın
- GitHub webhook'u test edecek ve yeşil ✅ işareti gösterecek

### 3. Test Et

#### 3.1 Quick Deploy ile Test
```bash
# Tek komutla deploy
./quick_deploy.sh "Test otomatik deploy"
```

#### 3.2 Normal Git Push ile Test
```bash
# Normal git workflow
git add .
git commit -m "Test webhook deploy"
git push origin chatbot-optimization-jules

# Server otomatik güncellenecek!
```

## 🔧 Kullanım

### Günlük Geliştirme
```bash
# Kod değişikliği yap
# Sonra tek komut:
./quick_deploy.sh "Bug fix: webhook handler düzeltildi"

# Veya normal git:
git add .
git commit -m "Feature: yeni özellik eklendi"
git push origin chatbot-optimization-jules
```

### Acil Durum Manuel Deploy
```bash
# Eğer webhook çalışmazsa
curl -X POST http://3.74.156.223:9000/deploy/manual
```

### Deploy Durumu Kontrol
```bash
# Deploy sisteminin durumunu kontrol et
curl http://3.74.156.223:9000/deploy/status
```

## 📊 Deploy Süreci

Webhook tetiklendiğinde server'da şunlar olur:

1. **Git Pull** - Son kodları çeker
2. **Dependencies** - Python paketlerini günceller  
3. **Embeddings** - RAG embeddings'leri günceller
4. **Services Restart** - Tüm servisleri yeniden başlatır
5. **Health Check** - Servislerin çalıştığını kontrol eder

## 🔍 Monitoring

### Deploy Logları
```bash
# Server'da deploy loglarını izle
ssh -i ~/Downloads/kobibot-key.pem ubuntu@3.74.156.223 "sudo journalctl -u kobibot-deploy -f"
```

### Servis Durumları
```bash
# Tüm servislerin durumunu kontrol et
ssh -i ~/Downloads/kobibot-key.pem ubuntu@3.74.156.223 "sudo systemctl status kobibot-*"
```

### Health Check
```bash
# Tüm endpoint'leri kontrol et
curl http://3.74.156.223:5004/health      # API
curl http://3.74.156.223:5006/api/system/health  # Admin
curl http://3.74.156.223:5007/webhook/status     # Webhook
curl http://3.74.156.223:5008/                   # Customer
```

## 🛠️ Troubleshooting

### Webhook Çalışmıyor
```bash
# Deploy servisini kontrol et
ssh -i ~/Downloads/kobibot-key.pem ubuntu@3.74.156.223 "sudo systemctl status kobibot-deploy"

# Port açık mı kontrol et
ssh -i ~/Downloads/kobibot-key.pem ubuntu@3.74.156.223 "sudo ufw status | grep 9000"
```

### Deploy Başarısız
```bash
# Manuel deploy dene
curl -X POST http://3.74.156.223:9000/deploy/manual

# Logları kontrol et
ssh -i ~/Downloads/kobibot-key.pem ubuntu@3.74.156.223 "sudo journalctl -u kobibot-deploy -n 50"
```

### Servis Çalışmıyor
```bash
# Servisleri manuel restart
ssh -i ~/Downloads/kobibot-key.pem ubuntu@3.74.156.223 "
sudo systemctl restart kobibot-api
sudo systemctl restart kobibot-admin  
sudo systemctl restart kobibot-webhook
sudo systemctl restart kobibot-customer
"
```

## 🎉 Avantajlar

✅ **Tek Push Deploy** - Sadece `git push` yeterli  
✅ **Otomatik Restart** - Servisler otomatik yeniden başlar  
✅ **Health Check** - Deploy sonrası sistem kontrolü  
✅ **Rollback Ready** - Sorun olursa hızla geri alınabilir  
✅ **Log Tracking** - Tüm deploy işlemleri loglanır  
✅ **Security** - Webhook secret ile güvenli  

## 🚀 Workflow

```
Local Development → Git Push → GitHub Webhook → Server Auto Deploy → Live System
      ↓                ↓            ↓                    ↓              ↓
   Code changes    Triggers     Calls deploy      Updates server    Users see
   committed       webhook      endpoint          & restarts        changes
```

---

**🎯 Artık geliştirme süper hızlı! Kod yazdın, push yaptın, canlıda!**