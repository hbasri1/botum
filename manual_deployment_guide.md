# Manual Deployment Guide for kobibot.com

## 🚨 SSH Bağlantı Sorunu Çözümü

Server'a SSH bağlantısı kesildi. Bu durumda AWS Console üzerinden işlem yapmanız gerekiyor.

### 1. AWS Console'dan Server'a Erişim

1. **AWS EC2 Console** → Instances
2. **kobibot server** instance'ını seçin
3. **Connect** → **Session Manager** ile bağlanın

### 2. Firewall Düzeltmesi

```bash
# SSH erişimini tekrar etkinleştir
sudo ufw allow ssh
sudo ufw allow 22

# Firewall durumunu kontrol et
sudo ufw status
```

### 3. Manual Deployment Steps

Server'a erişim sağlandıktan sonra:

#### 3.1 Repository Clone
```bash
# Proje dizinini oluştur
mkdir -p /home/ubuntu/kobibot
cd /home/ubuntu/kobibot

# Git repository'yi clone et (manuel olarak dosyaları yükle)
# Alternatif: SCP ile dosyaları kopyala
```

#### 3.2 Python Environment Setup
```bash
cd /home/ubuntu/kobibot

# Virtual environment oluştur
python3 -m venv venv

# Virtual environment'ı aktifleştir
source venv/bin/activate

# Requirements yükle (requirements.txt dosyası gerekli)
pip install flask flask-cors python-dotenv requests scikit-learn numpy pandas google-generativeai boto3
```

#### 3.3 Environment Variables
```bash
# .env dosyası oluştur
cat > .env << 'EOF'
# Google Gemini API Key
GEMINI_API_KEY=AIzaSyDNcOfDasPMbZdaZ_rkMDQ4u-OraAHbNcI

# AWS Bedrock API Key
AWS_BEDROCK_API_KEY=ABSKQmVkcm9ja0FQSUtleS12OXUzLWF0LTczMDQ3MDA5MDM2MzoxdmVEV2hUZFlCSVJ0K25JWWlUdTgzYlJJajhYWG5jNXpHeStsZWV2SkxtbmZnQ3BQS1Uyd2VaTE9mST0=

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Search Configuration
MAX_SEARCH_RESULTS=10
EMBEDDING_BATCH_SIZE=10
RATE_LIMIT_DELAY=0.5

# WhatsApp Business API Configuration
WHATSAPP_VERIFY_TOKEN=kobibot-webhook-verify-2024
WHATSAPP_ACCESS_TOKEN=your-access-token-from-meta
WHATSAPP_WEBHOOK_SECRET=kobibot-webhook-secret-2024

# Server Ports
ADMIN_PORT=5006
WEBHOOK_PORT=5007
CUSTOMER_PORT=5008

# Instagram Basic Display API
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret
INSTAGRAM_REDIRECT_URI=https://customer.kobibot.com/instagram/callback

# Domain Configuration
BASE_DOMAIN=kobibot.com
ADMIN_SUBDOMAIN=admin.kobibot.com
API_SUBDOMAIN=api.kobibot.com
WEBHOOK_SUBDOMAIN=webhook.kobibot.com
CUSTOMER_SUBDOMAIN=customer.kobibot.com
CHAT_SUBDOMAIN=chat.kobibot.com
EOF
```

#### 3.4 Directory Structure
```bash
# Gerekli dizinleri oluştur
mkdir -p uploads logs business_data embeddings data static templates
```

#### 3.5 Nginx Configuration
```bash
# Nginx config dosyası oluştur
sudo tee /etc/nginx/sites-available/kobibot.com << 'EOF'
# Main domain redirect to customer onboarding
server {
    listen 80;
    server_name kobibot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Admin subdomain
server {
    listen 80;
    server_name admin.kobibot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name admin.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API subdomain
server {
    listen 80;
    server_name api.kobibot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Webhook subdomain
server {
    listen 80;
    server_name webhook.kobibot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name webhook.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Customer subdomain
server {
    listen 80;
    server_name customer.kobibot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name customer.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Chat subdomain
server {
    listen 80;
    server_name chat.kobibot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chat.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Site'ı etkinleştir
sudo ln -sf /etc/nginx/sites-available/kobibot.com /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx test et
sudo nginx -t
```

#### 3.6 SSL Certificates
```bash
# SSL sertifikaları al
sudo certbot --nginx -d kobibot.com -d admin.kobibot.com -d api.kobibot.com -d webhook.kobibot.com -d customer.kobibot.com -d chat.kobibot.com --non-interactive --agree-tos --email admin@kobibot.com

# Auto-renewal etkinleştir
sudo systemctl enable certbot.timer
```

#### 3.7 Systemd Services
```bash
# Admin service
sudo tee /etc/systemd/system/kobibot-admin.service << 'EOF'
[Unit]
Description=KobiBot Admin Panel
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kobibot
Environment=PATH=/home/ubuntu/kobibot/venv/bin
ExecStart=/home/ubuntu/kobibot/venv/bin/python admin_web_interface.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# API service
sudo tee /etc/systemd/system/kobibot-api.service << 'EOF'
[Unit]
Description=KobiBot Chat API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kobibot
Environment=PATH=/home/ubuntu/kobibot/venv/bin
ExecStart=/home/ubuntu/kobibot/venv/bin/python production_web_interface.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Webhook service
sudo tee /etc/systemd/system/kobibot-webhook.service << 'EOF'
[Unit]
Description=KobiBot WhatsApp Webhook
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kobibot
Environment=PATH=/home/ubuntu/kobibot/venv/bin
ExecStart=/home/ubuntu/kobibot/venv/bin/python webhook_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Customer service
sudo tee /etc/systemd/system/kobibot-customer.service << 'EOF'
[Unit]
Description=KobiBot Customer Onboarding
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kobibot
Environment=PATH=/home/ubuntu/kobibot/venv/bin
ExecStart=/home/ubuntu/kobibot/venv/bin/python customer_onboarding_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Systemd reload ve servisleri etkinleştir
sudo systemctl daemon-reload
sudo systemctl enable kobibot-admin kobibot-api kobibot-webhook kobibot-customer
```

#### 3.8 File Upload via SCP

Local makinenizden server'a dosyaları yüklemek için:

```bash
# Tüm proje dosyalarını yükle
scp -i ~/Downloads/kobibot-key.pem -r . ubuntu@3.74.156.223:/home/ubuntu/kobibot/

# Veya tek tek önemli dosyaları yükle
scp -i ~/Downloads/kobibot-key.pem *.py ubuntu@3.74.156.223:/home/ubuntu/kobibot/
scp -i ~/Downloads/kobibot-key.pem -r templates ubuntu@3.74.156.223:/home/ubuntu/kobibot/
scp -i ~/Downloads/kobibot-key.pem -r data ubuntu@3.74.156.223:/home/ubuntu/kobibot/
```

#### 3.9 Initialize Embeddings
```bash
cd /home/ubuntu/kobibot
source venv/bin/activate

# RAG embeddings oluştur
python rag_product_search.py
```

#### 3.10 Start Services
```bash
# Nginx'i yeniden başlat
sudo systemctl restart nginx

# KobiBot servislerini başlat
sudo systemctl start kobibot-admin
sudo systemctl start kobibot-api
sudo systemctl start kobibot-webhook
sudo systemctl start kobibot-customer

# Servis durumlarını kontrol et
sudo systemctl status kobibot-admin
sudo systemctl status kobibot-api
sudo systemctl status kobibot-webhook
sudo systemctl status kobibot-customer
```

### 4. Domain DNS Ayarları

kobibot.com domain'i için DNS ayarları:

```
A Record: kobibot.com → 3.74.156.223
A Record: admin.kobibot.com → 3.74.156.223
A Record: api.kobibot.com → 3.74.156.223
A Record: webhook.kobibot.com → 3.74.156.223
A Record: customer.kobibot.com → 3.74.156.223
A Record: chat.kobibot.com → 3.74.156.223
```

### 5. Test Deployment

```bash
# Health check
curl http://localhost:5004/health
curl http://localhost:5006/api/system/health
curl http://localhost:5007/webhook/status
curl http://localhost:5008/

# External test (DNS propagation sonrası)
curl https://api.kobibot.com/health
curl https://admin.kobibot.com/api/system/health
curl https://webhook.kobibot.com/webhook/status
curl https://kobibot.com/
```

### 6. Troubleshooting

#### Service Logs
```bash
# Servis loglarını kontrol et
sudo journalctl -u kobibot-admin -f
sudo journalctl -u kobibot-api -f
sudo journalctl -u kobibot-webhook -f
sudo journalctl -u kobibot-customer -f
```

#### Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

#### Port Check
```bash
# Port'ların açık olduğunu kontrol et
sudo netstat -tlnp | grep :500
```

### 7. Security Group Ayarları

AWS EC2 Security Group'ta aşağıdaki port'ları açın:

- **22** (SSH)
- **80** (HTTP)
- **443** (HTTPS)
- **5004** (API - development)
- **5006** (Admin - development)
- **5007** (Webhook - development)
- **5008** (Customer - development)

### 8. Final Checklist

- [ ] SSH erişimi düzeltildi
- [ ] Python environment kuruldu
- [ ] Tüm dosyalar yüklendi
- [ ] Environment variables ayarlandı
- [ ] Nginx konfigüre edildi
- [ ] SSL sertifikaları alındı
- [ ] Systemd servisleri oluşturuldu
- [ ] Embeddings initialize edildi
- [ ] Servisler başlatıldı
- [ ] DNS ayarları yapıldı
- [ ] Test edildi

---

**🚀 Manual deployment tamamlandığında kobibot.com sistemi hazır olacak!**