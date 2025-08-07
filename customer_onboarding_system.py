#!/usr/bin/env python3
"""
Customer Onboarding System - Müşteri kayıt ve Instagram entegrasyonu
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
import os
import json
import logging
import uuid
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from mvp_business_system import get_business_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'customer-onboarding-secret-key')
CORS(app)

# Instagram API Configuration
INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID', 'your-instagram-app-id')
INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET', 'your-instagram-app-secret')
INSTAGRAM_REDIRECT_URI = os.getenv('INSTAGRAM_REDIRECT_URI', 'https://customer.kobibot.com/instagram/callback')

# Domain configuration
from domain_config import domain_config

# Initialize business manager
business_manager = get_business_manager()

class CustomerOnboardingSystem:
    """Müşteri onboarding sistemi"""
    
    def __init__(self):
        self.pending_registrations = {}  # Temporary storage for pending registrations
    
    def create_registration_session(self, customer_data: Dict[str, Any]) -> str:
        """Kayıt oturumu oluştur"""
        session_id = str(uuid.uuid4())
        self.pending_registrations[session_id] = {
            **customer_data,
            'created_at': datetime.now().isoformat(),
            'status': 'pending_instagram'
        }
        return session_id
    
    def get_instagram_auth_url(self, session_id: str) -> str:
        """Instagram yetkilendirme URL'si oluştur"""
        params = {
            'client_id': INSTAGRAM_APP_ID,
            'redirect_uri': INSTAGRAM_REDIRECT_URI,
            'scope': 'user_profile,user_media',
            'response_type': 'code',
            'state': session_id  # Session ID'yi state olarak gönder
        }
        
        base_url = 'https://api.instagram.com/oauth/authorize'
        return f"{base_url}?{urlencode(params)}"
    
    def handle_instagram_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Instagram callback işleme"""
        try:
            # Session ID'yi state'den al
            session_id = state
            
            if session_id not in self.pending_registrations:
                return {'success': False, 'error': 'Invalid session'}
            
            # Access token al
            token_response = self._get_instagram_access_token(code)
            if not token_response['success']:
                return token_response
            
            access_token = token_response['access_token']
            
            # Kullanıcı bilgilerini al
            user_info = self._get_instagram_user_info(access_token)
            if not user_info['success']:
                return user_info
            
            # Kayıt işlemini tamamla
            registration_data = self.pending_registrations[session_id]
            registration_data.update({
                'instagram_access_token': access_token,
                'instagram_user_id': user_info['user_id'],
                'instagram_username': user_info['username'],
                'status': 'instagram_connected'
            })
            
            # İşletmeyi oluştur
            business_result = self._create_business_from_registration(registration_data)
            
            if business_result['success']:
                # Başarılı kayıt
                registration_data['business_id'] = business_result['business_id']
                registration_data['status'] = 'completed'
                
                # Pending registration'ı temizle
                del self.pending_registrations[session_id]
                
                return {
                    'success': True,
                    'business_id': business_result['business_id'],
                    'message': 'Kayıt başarıyla tamamlandı!'
                }
            else:
                return business_result
                
        except Exception as e:
            logger.error(f"❌ Instagram callback error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_instagram_access_token(self, code: str) -> Dict[str, Any]:
        """Instagram access token al"""
        try:
            url = 'https://api.instagram.com/oauth/access_token'
            data = {
                'client_id': INSTAGRAM_APP_ID,
                'client_secret': INSTAGRAM_APP_SECRET,
                'grant_type': 'authorization_code',
                'redirect_uri': INSTAGRAM_REDIRECT_URI,
                'code': code
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data['access_token']
                }
            else:
                logger.error(f"❌ Instagram token error: {response.text}")
                return {
                    'success': False,
                    'error': 'Instagram token alınamadı'
                }
                
        except Exception as e:
            logger.error(f"❌ Instagram token request error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_instagram_user_info(self, access_token: str) -> Dict[str, Any]:
        """Instagram kullanıcı bilgilerini al"""
        try:
            url = f'https://graph.instagram.com/me?fields=id,username&access_token={access_token}'
            response = requests.get(url)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'success': True,
                    'user_id': user_data['id'],
                    'username': user_data['username']
                }
            else:
                logger.error(f"❌ Instagram user info error: {response.text}")
                return {
                    'success': False,
                    'error': 'Instagram kullanıcı bilgileri alınamadı'
                }
                
        except Exception as e:
            logger.error(f"❌ Instagram user info request error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_business_from_registration(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kayıt verilerinden işletme oluştur"""
        try:
            # İşletme verilerini hazırla
            business_data = {
                'name': registration_data['business_name'],
                'email': registration_data['email'],
                'phone': registration_data['phone'],
                'website': registration_data.get('website', ''),
                'instagram_handle': f"@{registration_data['instagram_username']}",
                'sector': registration_data.get('sector', 'general'),
                'owner_name': f"{registration_data['first_name']} {registration_data['last_name']}",
                'instagram_user_id': registration_data['instagram_user_id'],
                'instagram_access_token': registration_data['instagram_access_token'],
                'registration_source': 'customer_onboarding',
                'registration_date': datetime.now().isoformat()
            }
            
            # İşletmeyi oluştur
            business_id = business_manager.create_business(business_data)
            
            logger.info(f"✅ Business created from customer registration: {business_id}")
            
            return {
                'success': True,
                'business_id': business_id,
                'message': 'İşletme başarıyla oluşturuldu'
            }
            
        except Exception as e:
            logger.error(f"❌ Business creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_registration_status(self, session_id: str) -> Dict[str, Any]:
        """Kayıt durumunu kontrol et"""
        if session_id in self.pending_registrations:
            return {
                'success': True,
                'status': self.pending_registrations[session_id]['status'],
                'data': self.pending_registrations[session_id]
            }
        else:
            return {
                'success': False,
                'error': 'Session not found'
            }

# Initialize onboarding system
onboarding_system = CustomerOnboardingSystem()

@app.route('/')
def landing_page():
    """Ana sayfa - müşteri kayıt"""
    return render_template('customer_landing.html')

@app.route('/register', methods=['POST'])
def register_customer():
    """Müşteri kayıt işlemi"""
    try:
        data = request.get_json()
        
        # Gerekli alanları kontrol et
        required_fields = ['first_name', 'last_name', 'email', 'phone', 'business_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Gerekli alan eksik: {field}'
                }), 400
        
        # Email formatını kontrol et
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data['email']):
            return jsonify({
                'success': False,
                'error': 'Geçersiz email formatı'
            }), 400
        
        # Kayıt oturumu oluştur
        session_id = onboarding_system.create_registration_session(data)
        
        # Instagram yetkilendirme URL'si oluştur
        instagram_auth_url = onboarding_system.get_instagram_auth_url(session_id)
        
        # Session'a kaydet
        session['registration_session_id'] = session_id
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'instagram_auth_url': instagram_auth_url,
            'message': 'Kayıt başlatıldı. Instagram hesabınızı bağlayın.'
        })
        
    except Exception as e:
        logger.error(f"❌ Customer registration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/instagram/callback')
def instagram_callback():
    """Instagram callback endpoint"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')  # Session ID
        error = request.args.get('error')
        
        if error:
            flash(f'Instagram bağlantısı başarısız: {error}', 'error')
            return redirect(url_for('registration_failed'))
        
        if not code or not state:
            flash('Instagram callback parametreleri eksik', 'error')
            return redirect(url_for('registration_failed'))
        
        # Instagram callback işle
        result = onboarding_system.handle_instagram_callback(code, state)
        
        if result['success']:
            session['business_id'] = result['business_id']
            flash('Kayıt başarıyla tamamlandı! Hoş geldiniz!', 'success')
            return redirect(url_for('registration_success'))
        else:
            flash(f'Kayıt tamamlanamadı: {result["error"]}', 'error')
            return redirect(url_for('registration_failed'))
            
    except Exception as e:
        logger.error(f"❌ Instagram callback error: {e}")
        flash(f'Sistem hatası: {e}', 'error')
        return redirect(url_for('registration_failed'))

@app.route('/registration/success')
def registration_success():
    """Kayıt başarılı sayfası"""
    business_id = session.get('business_id')
    if not business_id:
        return redirect(url_for('landing_page'))
    
    return render_template('registration_success.html', business_id=business_id)

@app.route('/registration/failed')
def registration_failed():
    """Kayıt başarısız sayfası"""
    return render_template('registration_failed.html')

@app.route('/dashboard/<business_id>')
def customer_dashboard(business_id):
    """Müşteri dashboard"""
    try:
        # İşletme bilgilerini al
        business = business_manager.get_business(business_id)
        if not business:
            flash('İşletme bulunamadı', 'error')
            return redirect(url_for('landing_page'))
        
        # İstatistikleri al
        stats = business_manager.get_business_stats(business_id)
        
        return render_template('customer_dashboard.html', 
                             business=business, 
                             stats=stats)
        
    except Exception as e:
        logger.error(f"❌ Customer dashboard error: {e}")
        flash(f'Dashboard yüklenemedi: {e}', 'error')
        return redirect(url_for('landing_page'))

@app.route('/api/business/<business_id>/chat-widget')
def get_chat_widget(business_id):
    """Chat widget kodu al"""
    try:
        business = business_manager.get_business(business_id)
        if not business:
            return jsonify({'success': False, 'error': 'Business not found'}), 404
        
        # Chat widget HTML kodu
        widget_code = f"""
<!-- Chatbot Widget -->
<div id="chatbot-widget-{business_id}"></div>
<script>
(function() {{
    var script = document.createElement('script');
    script.src = 'http://localhost:5004/widget.js';
    script.onload = function() {{
        ChatbotWidget.init({{
            businessId: '{business_id}',
            apiUrl: 'http://localhost:5004',
            theme: {{
                primaryColor: '#3b82f6',
                position: 'bottom-right'
            }}
        }});
    }};
    document.head.appendChild(script);
}})();
</script>
"""
        
        return jsonify({
            'success': True,
            'widget_code': widget_code,
            'business_id': business_id
        })
        
    except Exception as e:
        logger.error(f"❌ Chat widget error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/registration/status/<session_id>')
def get_registration_status(session_id):
    """Kayıt durumunu kontrol et"""
    try:
        status = onboarding_system.get_registration_status(session_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"❌ Registration status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/stats')
def get_system_stats():
    """Sistem istatistikleri"""
    try:
        businesses = business_manager.get_all_businesses()
        
        # Kayıt kaynaklarına göre grupla
        registration_sources = {}
        for business in businesses:
            source = business.get('registration_source', 'unknown')
            registration_sources[source] = registration_sources.get(source, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_businesses': len(businesses),
                'customer_registrations': registration_sources.get('customer_onboarding', 0),
                'admin_created': registration_sources.get('admin', 0),
                'pending_registrations': len(onboarding_system.pending_registrations),
                'registration_sources': registration_sources
            }
        })
        
    except Exception as e:
        logger.error(f"❌ System stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('CUSTOMER_PORT', 5008))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🎯 Customer Onboarding System başlatılıyor...")
    print(f"📱 http://localhost:{port} adresinde erişilebilir")
    print(f"🔧 Debug mode: {debug}")
    print(f"📸 Instagram App ID: {INSTAGRAM_APP_ID}")
    print(f"🔗 Instagram Redirect URI: {INSTAGRAM_REDIRECT_URI}")
    
    if not INSTAGRAM_APP_ID or INSTAGRAM_APP_ID == 'your-instagram-app-id':
        print("⚠️  INSTAGRAM_APP_ID environment variable not configured!")
        print("   1. Go to https://developers.facebook.com/")
        print("   2. Create Instagram Basic Display App")
        print("   3. Set INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET in .env")
    
    print("\n📋 Instagram App Setup Instructions:")
    print("1. Go to https://developers.facebook.com/")
    print("2. Create new app → Instagram Basic Display")
    print("3. Add Instagram Basic Display product")
    print("4. Configure OAuth Redirect URIs:")
    print(f"   {INSTAGRAM_REDIRECT_URI}")
    print("5. Set environment variables in .env:")
    print("   INSTAGRAM_APP_ID=your-app-id")
    print("   INSTAGRAM_APP_SECRET=your-app-secret")
    
    app.run(debug=debug, host='0.0.0.0', port=port)