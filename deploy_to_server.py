#!/usr/bin/env python3
"""
Server Deployment Script for kobibot.com
AWS EC2 server'a deployment için
"""

import os
import subprocess
import sys
from pathlib import Path
from domain_config import domain_config

class ServerDeployment:
    """Server deployment yöneticisi"""
    
    def __init__(self):
        self.server_ip = "YOUR_SERVER_IP"
        self.server_user = "ubuntu"
        self.key_path = "~/Downloads/kobibot-key.pem"
        self.remote_path = "/home/ubuntu/kobibot"
        
    def run_command(self, command: str, check=True):
        """Komut çalıştır"""
        print(f"🔧 Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Error: {result.stderr}")
            
        if check and result.returncode != 0:
            print(f"❌ Command failed with exit code {result.returncode}")
            sys.exit(1)
            
        return result
    
    def ssh_command(self, command: str):
        """SSH ile server'da komut çalıştır"""
        ssh_cmd = f'ssh -i {self.key_path} {self.server_user}@{self.server_ip} "{command}"'
        return self.run_command(ssh_cmd)
    
    def scp_file(self, local_path: str, remote_path: str):
        """Dosya kopyala"""
        scp_cmd = f'scp -i {self.key_path} {local_path} {self.server_user}@{self.server_ip}:{remote_path}'
        return self.run_command(scp_cmd)
    
    def scp_directory(self, local_path: str, remote_path: str):
        """Klasör kopyala"""
        scp_cmd = f'scp -r -i {self.key_path} {local_path} {self.server_user}@{self.server_ip}:{remote_path}'
        return self.run_command(scp_cmd)
    
    def prepare_git_repo(self):
        """Git repo'yu hazırla"""
        print("📦 Preparing git repository...")
        
        # Add all files
        self.run_command("git add .")
        
        # Commit changes
        commit_msg = "Deploy to kobibot.com with Instagram integration"
        self.run_command(f'git commit -m "{commit_msg}"', check=False)
        
        # Push to origin
        self.run_command("git push origin chatbot-optimization-jules", check=False)
        
        print("✅ Git repository prepared")
    
    def setup_server_environment(self):
        """Server ortamını hazırla"""
        print("🖥️ Setting up server environment...")
        
        # Update system
        self.ssh_command("sudo apt update && sudo apt upgrade -y")
        
        # Install required packages
        packages = [
            "python3", "python3-pip", "python3-venv", 
            "nginx", "git", "certbot", "python3-certbot-nginx",
            "htop", "curl", "wget", "unzip"
        ]
        self.ssh_command(f"sudo apt install -y {' '.join(packages)}")
        
        # Create project directory
        self.ssh_command(f"mkdir -p {self.remote_path}")
        
        print("✅ Server environment ready")
    
    def clone_repository(self):
        """Repository'yi clone et"""
        print("📥 Cloning repository...")
        
        # Remove existing directory if exists
        self.ssh_command(f"rm -rf {self.remote_path}")
        
        # Clone repository
        repo_url = "https://github.com/YOUR_USERNAME/YOUR_REPO.git"  # Update this
        self.ssh_command(f"git clone {repo_url} {self.remote_path}")
        
        # Switch to correct branch
        self.ssh_command(f"cd {self.remote_path} && git checkout chatbot-optimization-jules")
        
        print("✅ Repository cloned")
    
    def setup_python_environment(self):
        """Python ortamını hazırla"""
        print("🐍 Setting up Python environment...")
        
        # Create virtual environment
        self.ssh_command(f"cd {self.remote_path} && python3 -m venv venv")
        
        # Install requirements
        self.ssh_command(f"cd {self.remote_path} && venv/bin/pip install -r requirements.txt")
        
        # Create necessary directories
        directories = ["uploads", "logs", "business_data", "embeddings", "data"]
        for directory in directories:
            self.ssh_command(f"mkdir -p {self.remote_path}/{directory}")
        
        print("✅ Python environment ready")
    
    def setup_environment_variables(self):
        """Environment variables'ları ayarla"""
        print("🔐 Setting up environment variables...")
        
        # Create .env file with production settings
        env_content = f"""# Production Environment for kobibot.com

# Google Gemini API Key
GEMINI_API_KEY=your-gemini-api-key-here

# AWS Bedrock API Key
AWS_BEDROCK_API_KEY=your-aws-bedrock-api-key-here

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Search Configuration
MAX_SEARCH_RESULTS=10
EMBEDDING_BATCH_SIZE=10
RATE_LIMIT_DELAY=0.5

# WhatsApp Business API Configuration
WHATSAPP_VERIFY_TOKEN=your-verify-token-change-this
WHATSAPP_ACCESS_TOKEN=your-access-token-from-meta
WHATSAPP_WEBHOOK_SECRET=your-webhook-secret-change-this

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
"""
        
        # Write .env file to server
        env_file_path = "/tmp/kobibot_env"
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        
        self.scp_file(env_file_path, f"{self.remote_path}/.env")
        os.remove(env_file_path)
        
        print("✅ Environment variables configured")
    
    def setup_nginx(self):
        """Nginx'i yapılandır"""
        print("🌐 Setting up Nginx...")
        
        # Generate nginx config
        nginx_config = domain_config.get_nginx_config()
        
        # Write config to temp file
        config_file_path = "/tmp/kobibot_nginx"
        with open(config_file_path, 'w') as f:
            f.write(nginx_config)
        
        # Copy to server
        self.scp_file(config_file_path, "/tmp/kobibot_nginx")
        
        # Move to nginx sites-available
        self.ssh_command("sudo mv /tmp/kobibot_nginx /etc/nginx/sites-available/kobibot.com")
        
        # Enable site
        self.ssh_command("sudo ln -sf /etc/nginx/sites-available/kobibot.com /etc/nginx/sites-enabled/")
        
        # Remove default site
        self.ssh_command("sudo rm -f /etc/nginx/sites-enabled/default")
        
        # Test nginx config
        self.ssh_command("sudo nginx -t")
        
        # Restart nginx
        self.ssh_command("sudo systemctl restart nginx")
        self.ssh_command("sudo systemctl enable nginx")
        
        os.remove(config_file_path)
        print("✅ Nginx configured")
    
    def setup_ssl_certificates(self):
        """SSL sertifikalarını ayarla"""
        print("🔒 Setting up SSL certificates...")
        
        # Get certificates for all subdomains
        domains = [domain_config.base_domain] + list(domain_config.subdomains.values())
        domain_list = " -d ".join(domains)
        
        certbot_cmd = f"sudo certbot --nginx -d {domain_list} --non-interactive --agree-tos --email admin@kobibot.com"
        self.ssh_command(certbot_cmd)
        
        # Setup auto-renewal
        self.ssh_command("sudo systemctl enable certbot.timer")
        
        print("✅ SSL certificates configured")
    
    def setup_systemd_services(self):
        """Systemd servislerini ayarla"""
        print("⚙️ Setting up systemd services...")
        
        services = domain_config.get_systemd_services()
        
        for service_name, service_content in services.items():
            # Write service file
            service_file_path = f"/tmp/{service_name}.service"
            with open(service_file_path, 'w') as f:
                f.write(service_content)
            
            # Copy to server
            self.scp_file(service_file_path, f"/tmp/{service_name}.service")
            
            # Move to systemd directory
            self.ssh_command(f"sudo mv /tmp/{service_name}.service /etc/systemd/system/")
            
            # Enable and start service
            self.ssh_command("sudo systemctl daemon-reload")
            self.ssh_command(f"sudo systemctl enable {service_name}")
            self.ssh_command(f"sudo systemctl start {service_name}")
            
            os.remove(service_file_path)
        
        print("✅ Systemd services configured")
    
    def setup_firewall(self):
        """Firewall'ı yapılandır"""
        print("🔥 Setting up firewall...")
        
        # Enable UFW
        self.ssh_command("sudo ufw --force enable")
        
        # Allow SSH
        self.ssh_command("sudo ufw allow ssh")
        
        # Allow HTTP and HTTPS
        self.ssh_command("sudo ufw allow 'Nginx Full'")
        
        # Allow specific ports for development
        ports = [5004, 5006, 5007, 5008]
        for port in ports:
            self.ssh_command(f"sudo ufw allow {port}")
        
        print("✅ Firewall configured")
    
    def initialize_embeddings(self):
        """Embeddings'leri başlat"""
        print("🧠 Initializing embeddings...")
        
        # Run RAG product search to create embeddings
        self.ssh_command(f"cd {self.remote_path} && venv/bin/python rag_product_search.py")
        
        print("✅ Embeddings initialized")
    
    def test_deployment(self):
        """Deployment'ı test et"""
        print("🧪 Testing deployment...")
        
        # Test all services
        services = ['kobibot-admin', 'kobibot-api', 'kobibot-webhook', 'kobibot-customer']
        
        for service in services:
            result = self.ssh_command(f"sudo systemctl is-active {service}")
            if "active" in result.stdout:
                print(f"✅ {service} is running")
            else:
                print(f"❌ {service} is not running")
        
        # Test nginx
        result = self.ssh_command("sudo systemctl is-active nginx")
        if "active" in result.stdout:
            print("✅ Nginx is running")
        else:
            print("❌ Nginx is not running")
        
        print("✅ Deployment test completed")
    
    def deploy(self):
        """Full deployment"""
        print("🚀 Starting full deployment to kobibot.com...")
        
        try:
            # 1. Prepare local repository
            self.prepare_git_repo()
            
            # 2. Setup server environment
            self.setup_server_environment()
            
            # 3. Clone repository
            self.clone_repository()
            
            # 4. Setup Python environment
            self.setup_python_environment()
            
            # 5. Setup environment variables
            self.setup_environment_variables()
            
            # 6. Initialize embeddings
            self.initialize_embeddings()
            
            # 7. Setup Nginx
            self.setup_nginx()
            
            # 8. Setup SSL certificates
            self.setup_ssl_certificates()
            
            # 9. Setup systemd services
            self.setup_systemd_services()
            
            # 10. Setup firewall
            self.setup_firewall()
            
            # 11. Test deployment
            self.test_deployment()
            
            print("🎉 Deployment completed successfully!")
            print("\n📋 Next Steps:")
            print("1. Configure Instagram App in Meta Developer Console:")
            print(f"   - Redirect URI: {domain_config.get_instagram_redirect_uri()}")
            print("2. Configure WhatsApp Business API:")
            print(f"   - Webhook URL: {domain_config.get_webhook_url()}")
            print("3. Update .env file with actual Instagram and WhatsApp tokens")
            print("\n🌐 Your services are available at:")
            for service, subdomain in domain_config.subdomains.items():
                print(f"   {service}: https://{subdomain}")
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    deployment = ServerDeployment()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "prepare":
            deployment.prepare_git_repo()
        elif command == "setup":
            deployment.setup_server_environment()
        elif command == "clone":
            deployment.clone_repository()
        elif command == "python":
            deployment.setup_python_environment()
        elif command == "env":
            deployment.setup_environment_variables()
        elif command == "nginx":
            deployment.setup_nginx()
        elif command == "ssl":
            deployment.setup_ssl_certificates()
        elif command == "services":
            deployment.setup_systemd_services()
        elif command == "firewall":
            deployment.setup_firewall()
        elif command == "embeddings":
            deployment.initialize_embeddings()
        elif command == "test":
            deployment.test_deployment()
        else:
            print("❌ Unknown command")
            print("Available commands: prepare, setup, clone, python, env, nginx, ssl, services, firewall, embeddings, test")
    else:
        deployment.deploy()