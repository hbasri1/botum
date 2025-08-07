#!/usr/bin/env python3
"""
Domain Configuration for kobibot.com
Instagram webhook ve subdomain yönetimi için
"""

import os
from typing import Dict, Any

class DomainConfig:
    """Domain konfigürasyon yöneticisi"""
    
    def __init__(self):
        self.base_domain = "kobibot.com"
        self.subdomains = {
            'admin': 'admin.kobibot.com',
            'api': 'api.kobibot.com', 
            'webhook': 'webhook.kobibot.com',
            'customer': 'customer.kobibot.com',
            'chat': 'chat.kobibot.com'
        }
        
        # Port mappings for reverse proxy
        self.port_mappings = {
            'admin': 5006,      # Admin paneli
            'api': 5004,        # Ana chat API
            'webhook': 5007,    # WhatsApp webhook
            'customer': 5008,   # Müşteri onboarding
            'chat': 5004        # Chat interface
        }
    
    def get_subdomain_url(self, service: str, path: str = "") -> str:
        """Subdomain URL'i oluştur"""
        if service in self.subdomains:
            base_url = f"https://{self.subdomains[service]}"
            return f"{base_url}{path}" if path else base_url
        return f"https://{self.base_domain}{path}"
    
    def get_instagram_redirect_uri(self) -> str:
        """Instagram OAuth redirect URI"""
        return self.get_subdomain_url('customer', '/instagram/callback')
    
    def get_webhook_url(self) -> str:
        """WhatsApp webhook URL"""
        return self.get_subdomain_url('webhook', '/webhook')
    
    def get_nginx_config(self) -> str:
        """Nginx reverse proxy konfigürasyonu"""
        config = f"""
# Nginx configuration for {self.base_domain}

# Main domain redirect to customer onboarding
server {{
    listen 80;
    server_name {self.base_domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.base_domain};
    
    ssl_certificate /etc/letsencrypt/live/{self.base_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.base_domain}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:{self.port_mappings['customer']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# Admin subdomain
server {{
    listen 80;
    server_name {self.subdomains['admin']};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.subdomains['admin']};
    
    ssl_certificate /etc/letsencrypt/live/{self.base_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.base_domain}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:{self.port_mappings['admin']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# API subdomain
server {{
    listen 80;
    server_name {self.subdomains['api']};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.subdomains['api']};
    
    ssl_certificate /etc/letsencrypt/live/{self.base_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.base_domain}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:{self.port_mappings['api']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# Webhook subdomain
server {{
    listen 80;
    server_name {self.subdomains['webhook']};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.subdomains['webhook']};
    
    ssl_certificate /etc/letsencrypt/live/{self.base_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.base_domain}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:{self.port_mappings['webhook']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# Customer subdomain
server {{
    listen 80;
    server_name {self.subdomains['customer']};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.subdomains['customer']};
    
    ssl_certificate /etc/letsencrypt/live/{self.base_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.base_domain}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:{self.port_mappings['customer']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# Chat subdomain
server {{
    listen 80;
    server_name {self.subdomains['chat']};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.subdomains['chat']};
    
    ssl_certificate /etc/letsencrypt/live/{self.base_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.base_domain}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:{self.port_mappings['chat']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        return config
    
    def get_systemd_services(self) -> Dict[str, str]:
        """Systemd service dosyaları"""
        services = {}
        
        # Admin service
        services['kobibot-admin'] = f"""[Unit]
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
"""

        # API service
        services['kobibot-api'] = f"""[Unit]
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
"""

        # Webhook service
        services['kobibot-webhook'] = f"""[Unit]
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
"""

        # Customer service
        services['kobibot-customer'] = f"""[Unit]
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
"""
        
        return services

# Global instance
domain_config = DomainConfig()

if __name__ == "__main__":
    print("🌐 KobiBot Domain Configuration")
    print(f"Base domain: {domain_config.base_domain}")
    print("\nSubdomains:")
    for service, subdomain in domain_config.subdomains.items():
        print(f"  {service}: {subdomain}")
    
    print("\nPort mappings:")
    for service, port in domain_config.port_mappings.items():
        print(f"  {service}: {port}")
    
    print(f"\nInstagram redirect URI: {domain_config.get_instagram_redirect_uri()}")
    print(f"WhatsApp webhook URL: {domain_config.get_webhook_url()}")