#!/bin/bash
"""
Quick Deploy Script - Tek komutla server'a deploy
Usage: ./quick_deploy.sh "commit message"
"""

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BRANCH="main"
SERVER_IP="3.74.156.223"
SERVER_USER="ubuntu"
KEY_PATH="~/Downloads/kobibot-key.pem"

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Commit message
COMMIT_MSG="${1:-Quick deploy $(date '+%Y-%m-%d %H:%M:%S')}"

echo "🚀 KobiBot Quick Deploy"
echo "======================="
echo "Branch: $BRANCH"
echo "Commit: $COMMIT_MSG"
echo "Server: $SERVER_IP"
echo ""

# 1. Local changes commit
print_info "Committing local changes..."
git add .
git commit -m "$COMMIT_MSG" || print_warning "No changes to commit"

# 2. Push to GitHub
print_info "Pushing to GitHub..."
git push origin $BRANCH

# 3. Trigger server deploy
print_info "Triggering server deploy..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "curl -s -X POST http://localhost:9000/deploy/manual" || {
    print_warning "Auto-deploy failed, trying manual deploy..."
    
    # Manual deploy fallback
    print_info "Running manual deploy on server..."
    ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "
        cd /home/ubuntu/kobibot && 
        git pull origin $BRANCH && 
        sudo systemctl restart kobibot-api kobibot-admin kobibot-webhook kobibot-customer &&
        echo 'Manual deploy completed'
    "
}

# 4. Health check
print_info "Running health checks..."
sleep 5

# Check services
SERVICES=("kobibot-api:5004" "kobibot-admin:5006" "kobibot-webhook:5007" "kobibot-customer:5008")

for service_port in "${SERVICES[@]}"; do
    IFS=':' read -r service port <<< "$service_port"
    
    if ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "curl -s -f http://localhost:$port/health > /dev/null 2>&1 || curl -s -f http://localhost:$port/ > /dev/null 2>&1"; then
        print_status "$service is healthy"
    else
        print_error "$service is not responding"
    fi
done

# 5. Show final status
print_info "Getting deploy status..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP "curl -s http://localhost:9000/deploy/status" 2>/dev/null || print_warning "Deploy status not available"

echo ""
print_status "Deploy completed!"
print_info "Your services are available at:"
echo "   🌐 Main: http://$SERVER_IP (when DNS is ready)"
echo "   🔧 Admin: http://$SERVER_IP:5006"
echo "   🤖 API: http://$SERVER_IP:5004"
echo "   📱 Webhook: http://$SERVER_IP:5007"
echo "   👥 Customer: http://$SERVER_IP:5008"
echo ""
print_info "Auto-deploy webhook: http://$SERVER_IP:9000/deploy"