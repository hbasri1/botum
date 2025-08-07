#!/bin/bash
"""
Domain ve SSL Setup Script
kobibot.com domain'i için HTTPS kurulumu
"""

set -e

SERVER_IP="3.74.156.223"
SERVER_USER="ubuntu"
KEY_PATH="~/Downloads/kobibot-key.pem"
DOMAIN="kobibot.com"

echo "🌐 Setting up kobibot.com domain and SSL..."

# 1. Update Nginx config for HTTPS redirect
echo "📝 Updating Nginx configuration..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "
sudo tee /etc/nginx/sites-available/kobibot.com << 'EOF'
# Main domain - public demo
server {
    listen 80;
    server_name kobibot.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5004;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Admin subdomain
server {
    listen 80;
    server_name admin.kobibot.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name admin.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5006;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# API subdomain
server {
    listen 80;
    server_name api.kobibot.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5004;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Webhook subdomain
server {
    listen 80;
    server_name webhook.kobibot.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name webhook.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5007;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Customer subdomain
server {
    listen 80;
    server_name customer.kobibot.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name customer.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5008;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Chat subdomain
server {
    listen 80;
    server_name chat.kobibot.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chat.kobibot.com;
    
    ssl_certificate /etc/letsencrypt/live/kobibot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kobibot.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5004;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
"

# 2. Test Nginx config
echo "🧪 Testing Nginx configuration..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "sudo nginx -t"

echo ""
echo "✅ Domain setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. DNS ayarlarını yap (domain provider'da):"
echo "   A Record: kobibot.com → $SERVER_IP"
echo "   A Record: admin.kobibot.com → $SERVER_IP"
echo "   A Record: api.kobibot.com → $SERVER_IP"
echo "   A Record: webhook.kobibot.com → $SERVER_IP"
echo "   A Record: customer.kobibot.com → $SERVER_IP"
echo "   A Record: chat.kobibot.com → $SERVER_IP"
echo ""
echo "2. DNS propagation sonrası SSL sertifikaları al:"
echo "   ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP \"sudo certbot --nginx -d kobibot.com -d admin.kobibot.com -d api.kobibot.com -d webhook.kobibot.com -d customer.kobibot.com -d chat.kobibot.com --non-interactive --agree-tos --email admin@kobibot.com\""
echo ""
echo "3. Nginx'i yeniden başlat:"
echo "   ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP \"sudo systemctl restart nginx\""