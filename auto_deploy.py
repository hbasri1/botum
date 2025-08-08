#!/usr/bin/env python3
"""
Otomatik Deploy Sistemi - GitHub Webhook ile
Tek push'ta server'a otomatik deploy
"""

from flask import Flask, request, jsonify
import os
import subprocess
import logging
import hmac
import hashlib
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# GitHub webhook secret (güvenlik için)
WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'your-github-webhook-secret')
PROJECT_PATH = '/home/ubuntu/kobibot'
BRANCH = 'main'

def verify_signature(payload_body, signature_header):
    """GitHub webhook signature doğrulama"""
    if not signature_header:
        return False
    
    sha_name, signature = signature_header.split('=')
    if sha_name != 'sha256':
        return False
    
    mac = hmac.new(WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

def run_command(command, cwd=None):
    """Komut çalıştır ve sonucu döndür"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True,
            timeout=300  # 5 dakika timeout
        )
        
        logger.info(f"Command: {command}")
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"Output: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"Error: {result.stderr}")
        
        return result.returncode == 0, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {command}")
        return False, "", "Command timeout"
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return False, "", str(e)

@app.route('/deploy', methods=['POST'])
def deploy():
    """GitHub webhook deploy endpoint"""
    try:
        # Signature doğrulama
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_signature(request.data, signature):
            logger.error("❌ Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 403
        
        # Webhook payload
        payload = request.get_json()
        
        # Sadece main/master branch push'larını işle
        if payload.get('ref') != f'refs/heads/{BRANCH}':
            logger.info(f"⏭️ Ignoring push to {payload.get('ref')}")
            return jsonify({'message': 'Branch ignored'}), 200
        
        logger.info("🚀 Starting auto-deploy...")
        
        deploy_steps = []
        
        # 1. Git pull
        logger.info("📥 Pulling latest changes...")
        success, stdout, stderr = run_command(f'/usr/bin/git fetch origin {BRANCH}', PROJECT_PATH)
        if not success:
            return jsonify({'error': f'Git fetch failed: {stderr}'}), 500
        
        success, stdout, stderr = run_command(f'/usr/bin/git reset --hard origin/{BRANCH}', PROJECT_PATH)
        if not success:
            return jsonify({'error': f'Git reset failed: {stderr}'}), 500
        
        deploy_steps.append("✅ Git pull completed")
        
        # 2. Python dependencies güncelle
        logger.info("📦 Updating Python dependencies...")
        success, stdout, stderr = run_command(f'source venv/bin/activate && pip install -r requirements.txt', PROJECT_PATH)
        if success:
            deploy_steps.append("✅ Dependencies updated")
        else:
            deploy_steps.append("⚠️ Dependencies update failed (continuing)")
        
        # 3. Embeddings güncelle (eğer gerekirse)
        logger.info("🧠 Checking embeddings...")
        if os.path.exists(f'{PROJECT_PATH}/data/products.json'):
            success, stdout, stderr = run_command(f'source venv/bin/activate && python rag_product_search.py', PROJECT_PATH)
            if success:
                deploy_steps.append("✅ Embeddings updated")
            else:
                deploy_steps.append("⚠️ Embeddings update failed (continuing)")
        
        # 4. Servisleri yeniden başlat
        logger.info("🔄 Restarting services...")
        services = ['kobibot-api', 'kobibot-admin', 'kobibot-webhook', 'kobibot-customer']
        
        for service in services:
            success, stdout, stderr = run_command(f'sudo systemctl restart {service}')
            if success:
                deploy_steps.append(f"✅ {service} restarted")
            else:
                deploy_steps.append(f"❌ {service} restart failed")
        
        # 5. Nginx reload
        success, stdout, stderr = run_command('sudo systemctl reload nginx')
        if success:
            deploy_steps.append("✅ Nginx reloaded")
        
        # 6. Health check
        logger.info("🏥 Running health checks...")
        import time
        time.sleep(5)  # Servislerin başlaması için bekle
        
        health_checks = []
        endpoints = [
            ('API', 'http://localhost:5004/health'),
            ('Admin', 'http://localhost:5006/api/system/health'),
            ('Webhook', 'http://localhost:5007/webhook/status'),
            ('Customer', 'http://localhost:5008/')
        ]
        
        for name, url in endpoints:
            success, stdout, stderr = run_command(f'curl -s -f {url} > /dev/null')
            if success:
                health_checks.append(f"✅ {name} healthy")
            else:
                health_checks.append(f"❌ {name} unhealthy")
        
        # Deploy sonucu
        deploy_info = {
            'timestamp': datetime.now().isoformat(),
            'commit': payload.get('head_commit', {}).get('id', 'unknown')[:8],
            'message': payload.get('head_commit', {}).get('message', 'No message'),
            'author': payload.get('head_commit', {}).get('author', {}).get('name', 'Unknown'),
            'steps': deploy_steps,
            'health_checks': health_checks,
            'status': 'success'
        }
        
        logger.info("🎉 Deploy completed successfully!")
        return jsonify(deploy_info), 200
        
    except Exception as e:
        logger.error(f"❌ Deploy failed: {e}")
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/deploy/status')
def deploy_status():
    """Deploy sistemi durumu"""
    try:
        # Git durumu
        success, stdout, stderr = run_command('/usr/bin/git log -1 --oneline', PROJECT_PATH)
        last_commit = stdout.strip() if success else 'Unknown'
        
        # Servis durumları
        services = ['kobibot-api', 'kobibot-admin', 'kobibot-webhook', 'kobibot-customer']
        service_status = {}
        
        for service in services:
            success, stdout, stderr = run_command(f'sudo systemctl is-active {service}')
            service_status[service] = 'active' if success and 'active' in stdout else 'inactive'
        
        return jsonify({
            'status': 'healthy',
            'last_commit': last_commit,
            'services': service_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/deploy/manual', methods=['POST'])
def manual_deploy():
    """Manuel deploy (test için)"""
    try:
        logger.info("🔧 Manual deploy triggered...")
        
        # Basit git pull ve restart
        success, stdout, stderr = run_command(f'/usr/bin/git pull origin {BRANCH}', PROJECT_PATH)
        if not success:
            return jsonify({'error': f'Git pull failed: {stderr}'}), 500
        
        # Servisleri yeniden başlat
        services = ['kobibot-api', 'kobibot-admin', 'kobibot-webhook', 'kobibot-customer']
        for service in services:
            run_command(f'sudo systemctl restart {service}')
        
        return jsonify({
            'status': 'success',
            'message': 'Manual deploy completed',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/')
def index():
    """Deploy sistemi ana sayfa"""
    return """
    <h1>🚀 KobiBot Auto Deploy System</h1>
    <p>GitHub webhook ile otomatik deploy sistemi</p>
    <ul>
        <li><a href="/deploy/status">Deploy Status</a></li>
        <li><strong>POST /deploy</strong> - GitHub webhook endpoint</li>
        <li><strong>POST /deploy/manual</strong> - Manuel deploy</li>
    </ul>
    <p>Sistem çalışıyor ve webhook'ları bekliyor...</p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_PORT', 9000))
    
    print("🚀 KobiBot Auto Deploy System başlatılıyor...")
    print(f"📡 Port: {port}")
    print(f"📂 Project path: {PROJECT_PATH}")
    print(f"🌿 Branch: {BRANCH}")
    print(f"🔐 Webhook secret configured: {bool(WEBHOOK_SECRET)}")
    print("\n📋 GitHub Webhook Setup:")
    print(f"   URL: http://YOUR_SERVER_IP:{port}/deploy")
    print("   Content type: application/json")
    print("   Secret: your-github-webhook-secret")
    print("   Events: Just the push event")
    
    app.run(host='0.0.0.0', port=port, debug=False)