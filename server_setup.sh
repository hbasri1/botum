#!/bin/bash
"""
Server Setup Script for kobibot.com
AWS EC2 Ubuntu server için otomatik kurulum
"""

set -e  # Exit on any error

echo "🚀 KobiBot Server Setup Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server configuration
SERVER_IP="3.74.156.223"
SERVER_USER="ubuntu"
KEY_PATH="~/Downloads/kobibot-key.pem"
REMOTE_PATH="/home/ubuntu/kobibot"
DOMAIN="kobibot.com"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to run SSH commands
ssh_run() {
    ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "$1"
}

# Function to copy files
scp_copy() {
    scp -i $KEY_PATH "$1" $SERVER_USER@$SERVER_IP:"$2"
}

# Function to copy directories
scp_copy_dir() {
    scp -r -i $KEY_PATH "$1" $SERVER_USER@$SERVER_IP:"$2"
}

# 1. Update system packages
print_status "Updating system packages..."
ssh_run "sudo apt update && sudo apt upgrade -y"

# 2. Install required packages
print_status "Installing required packages..."
ssh_run "sudo apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx htop curl wget unzip ufw"

# 3. Setup firewall
print_status "Setting up firewall..."
ssh_run "sudo ufw --force enable"
ssh_run "sudo ufw allow ssh"
ssh_run "sudo ufw allow 'Nginx Full'"
ssh_run "sudo ufw allow 5004"
ssh_run "sudo ufw allow 5006"
ssh_run "sudo ufw allow 5007"
ssh_run "sudo ufw allow 5008"

# 4. Create project directory
print_status "Creating project directory..."
ssh_run "mkdir -p $REMOTE_PATH"

# 5. Clone repository (if not exists)
print_status "Setting up repository..."
if ssh_run "[ ! -d $REMOTE_PATH/.git ]"; then
    print_warning "Repository not found, you need to upload files manually"
    print_warning "Run: python3 deploy_to_server.py clone"
fi

# 6. Setup Python virtual environment
print_status "Setting up Python environment..."
ssh_run "cd $REMOTE_PATH && python3 -m venv venv"

# 7. Create necessary directories
print_status "Creating necessary directories..."
ssh_run "mkdir -p $REMOTE_PATH/{uploads,logs,business_data,embeddings,data,static,templates}"

# 8. Setup Nginx configuration
print_status "Setting up Nginx..."

# Create Nginx config
cat > /tmp/kobibot_nginx << 'EOF'
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

# Copy Nginx config to server
scp_copy "/tmp/kobibot_nginx" "/tmp/kobibot_nginx"
ssh_run "sudo mv /tmp/kobibot_nginx /etc/nginx/sites-available/kobibot.com"
ssh_run "sudo ln -sf /etc/nginx/sites-available/kobibot.com /etc/nginx/sites-enabled/"
ssh_run "sudo rm -f /etc/nginx/sites-enabled/default"

# Test Nginx config
ssh_run "sudo nginx -t"

# 9. Setup SSL certificates
print_status "Setting up SSL certificates..."
ssh_run "sudo certbot --nginx -d kobibot.com -d admin.kobibot.com -d api.kobibot.com -d webhook.kobibot.com -d customer.kobibot.com -d chat.kobibot.com --non-interactive --agree-tos --email admin@kobibot.com"

# Enable auto-renewal
ssh_run "sudo systemctl enable certbot.timer"

# 10. Restart Nginx
print_status "Restarting Nginx..."
ssh_run "sudo systemctl restart nginx"
ssh_run "sudo systemctl enable nginx"

# 11. Create systemd services
print_status "Creating systemd services..."

# Admin service
cat > /tmp/kobibot-admin.service << 'EOF'
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
cat > /tmp/kobibot-api.service << 'EOF'
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
cat > /tmp/kobibot-webhook.service << 'EOF'
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
cat > /tmp/kobibot-customer.service << 'EOF'
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

# Copy service files
for service in admin api webhook customer; do
    scp_copy "/tmp/kobibot-${service}.service" "/tmp/kobibot-${service}.service"
    ssh_run "sudo mv /tmp/kobibot-${service}.service /etc/systemd/system/"
done

# Reload systemd
ssh_run "sudo systemctl daemon-reload"

print_status "Server setup completed!"
print_warning "Next steps:"
echo "1. Upload your code: python3 deploy_to_server.py"
echo "2. Install Python dependencies on server"
echo "3. Configure environment variables"
echo "4. Start services"
echo ""
echo "🌐 Your domains will be available at:"
echo "   Main: https://kobibot.com"
echo "   Admin: https://admin.kobibot.com"
echo "   API: https://api.kobibot.com"
echo "   Webhook: https://webhook.kobibot.com"
echo "   Customer: https://customer.kobibot.com"
echo "   Chat: https://chat.kobibot.com"

# Clean up temp files
rm -f /tmp/kobibot_nginx /tmp/kobibot-*.service

print_status "Setup script completed successfully!"