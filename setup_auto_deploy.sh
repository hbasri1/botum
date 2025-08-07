#!/bin/bash
"""
Auto Deploy Setup Script
Server'da otomatik deploy sistemini kurar
"""

set -e

SERVER_IP="3.74.156.223"
SERVER_USER="ubuntu"
KEY_PATH="~/Downloads/kobibot-key.pem"

echo "🚀 Setting up Auto Deploy System on server..."

# 1. Copy auto deploy script to server
echo "📤 Copying auto deploy script..."
scp -i $KEY_PATH auto_deploy.py $SERVER_USER@$SERVER_IP:/home/ubuntu/kobibot/

# 2. Setup systemd service for auto deploy
echo "⚙️ Setting up systemd service..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "
sudo tee /etc/systemd/system/kobibot-deploy.service << 'EOF'
[Unit]
Description=KobiBot Auto Deploy System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kobibot
Environment=PATH=/home/ubuntu/kobibot/venv/bin
Environment=GITHUB_WEBHOOK_SECRET=kobibot-deploy-secret-2024
Environment=DEPLOY_PORT=9000
ExecStart=/home/ubuntu/kobibot/venv/bin/python auto_deploy.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
"

# 3. Enable and start deploy service
echo "🔄 Starting deploy service..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "
sudo systemctl daemon-reload &&
sudo systemctl enable kobibot-deploy &&
sudo systemctl start kobibot-deploy
"

# 4. Open firewall port
echo "🔥 Opening firewall port..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "sudo ufw allow 9000"

# 5. Test deploy system
echo "🧪 Testing deploy system..."
sleep 3
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "curl -s http://localhost:9000/deploy/status" || echo "Deploy system not ready yet"

echo ""
echo "✅ Auto Deploy System setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. GitHub'da webhook ekle:"
echo "   - Repo Settings > Webhooks > Add webhook"
echo "   - URL: http://$SERVER_IP:9000/deploy"
echo "   - Content type: application/json"
echo "   - Secret: kobibot-deploy-secret-2024"
echo "   - Events: Just the push event"
echo ""
echo "2. Test deploy:"
echo "   ./quick_deploy.sh \"Test deploy message\""
echo ""
echo "3. Manuel deploy (acil durum):"
echo "   curl -X POST http://$SERVER_IP:9000/deploy/manual"
echo ""
echo "🎉 Artık tek push ile otomatik deploy!"