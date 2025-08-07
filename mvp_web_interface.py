#!/usr/bin/env python3
"""
MVP Web Interface - Business Management Destekli
Manuel süreçlerle başlayan basit sistem
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_cors import CORS
from mvp_business_system import get_business_manager
from improved_final_mvp_system import ImprovedFinalMVPChatbot
import logging
import os
import time
import uuid
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mvp-secret-key-change-in-production')
CORS(app)  # Enable CORS for all routes

# Initialize business manager
business_manager = get_business_manager()

# Default demo chatbot
try:
    demo_chatbot = ImprovedFinalMVPChatbot()
    logger.info("✅ Demo Chatbot initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize demo chatbot: {e}")
    demo_chatbot = None

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('chat.html')

@app.route('/admin')
def admin():
    """Admin panel for business management"""
    businesses = business_manager.list_businesses()
    return render_template('admin.html', businesses=businesses)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with business-specific chatbot"""
    try:
        # Generate or get session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session['session_id']
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'response': 'Geçersiz istek formatı.',
                'success': False
            }), 400
        
        user_message = data.get('message', '').strip()
        business_id = data.get('business_id', 'demo')  # Default demo business
        
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'response': 'Lütfen bir mesaj yazın.',
                'success': False
            }), 400
        
        # Get business-specific chatbot
        if business_id == 'demo':
            chatbot = demo_chatbot
        else:
            chatbot = business_manager.get_business_chatbot_instance(business_id)
        
        if not chatbot:
            return jsonify({
                'error': 'Business chatbot not available',
                'response': 'İşletme chatbot\'u bulunamadı.',
                'success': False
            }), 404
        
        # Get response from chatbot with session ID
        start_time = time.time()
        chat_response = chatbot.chat(user_message, session_id=session_id)
        processing_time = time.time() - start_time
        
        # Get system stats
        stats = chatbot.get_stats()
        
        return jsonify({
            'response': chat_response.message,
            'intent': chat_response.intent,
            'confidence': round(chat_response.confidence, 2),
            'products_found': chat_response.products_found,
            'processing_time': round(processing_time, 3),
            'business_id': business_id,
            'success': True,
            'stats': {
                'total_requests': stats['total_requests'],
                'cache_hit_rate': round(stats['cache_hit_rate'], 1),
                'average_response_time': round(stats['average_response_time'], 3)
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        return jsonify({
            'error': str(e),
            'response': 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.',
            'success': False
        }), 500

# Business Management Endpoints

@app.route('/api/businesses', methods=['GET'])
def list_businesses():
    """List all businesses"""
    try:
        businesses = business_manager.list_businesses()
        return jsonify({
            'businesses': businesses,
            'success': True
        })
    except Exception as e:
        logger.error(f"❌ List businesses error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/businesses', methods=['POST'])
def create_business():
    """Create new business"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['name', 'email', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        business_id = business_manager.create_business(data)
        
        return jsonify({
            'business_id': business_id,
            'message': 'İşletme başarıyla oluşturuldu',
            'success': True
        })
        
    except Exception as e:
        logger.error(f"❌ Create business error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/businesses/<business_id>/products', methods=['POST'])
def upload_products():
    """Upload products for a business (Manual process)"""
    try:
        business_id = request.view_args['business_id']
        
        # Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        upload_dir = f"business_data/uploads/{business_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        
        # Load products from file
        product_count = business_manager.load_business_products(business_id, file_path)
        
        return jsonify({
            'message': f'{product_count} ürün başarıyla yüklendi',
            'product_count': product_count,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"❌ Upload products error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/businesses/<business_id>/stats', methods=['GET'])
def get_business_stats():
    """Get business statistics"""
    try:
        business_id = request.view_args['business_id']
        stats = business_manager.get_business_stats(business_id)
        
        if not stats:
            return jsonify({'error': 'Business not found'}), 404
        
        return jsonify({
            'stats': stats,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"❌ Get business stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/businesses/<business_id>/test', methods=['POST'])
def test_business_chatbot():
    """Test business chatbot"""
    try:
        business_id = request.view_args['business_id']
        data = request.get_json()
        
        test_message = data.get('message', 'merhaba')
        
        chatbot = business_manager.get_business_chatbot_instance(business_id)
        if not chatbot:
            return jsonify({'error': 'Business chatbot not found'}), 404
        
        # Test the chatbot
        response = chatbot.chat(test_message)
        
        return jsonify({
            'test_message': test_message,
            'response': response.message,
            'intent': response.intent,
            'confidence': response.confidence,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"❌ Test business chatbot error: {e}")
        return jsonify({'error': str(e)}), 500

# Instagram Webhook (Hazırlık)
@app.route('/webhook/instagram/<business_id>', methods=['GET', 'POST'])
def instagram_webhook():
    """Instagram webhook handler (Future implementation)"""
    business_id = request.view_args['business_id']
    
    if request.method == 'GET':
        # Webhook verification
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # TODO: Verify token validation
        return challenge
    
    elif request.method == 'POST':
        # Handle Instagram webhook data
        data = request.get_json()
        
        # TODO: Process Instagram post data
        logger.info(f"Instagram webhook data for {business_id}: {data}")
        
        return jsonify({'status': 'received'})

@app.route('/health')
def health():
    """Enhanced health check endpoint"""
    try:
        businesses = business_manager.list_businesses()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'demo_chatbot_available': demo_chatbot is not None,
            'total_businesses': len(businesses),
            'uptime': 'Running'
        })
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print("🚀 MVP Web Interface başlatılıyor...")
    print(f"📱 http://localhost:{port} adresinde erişilebilir")
    print(f"🔧 Debug mode: {debug}")
    print(f"👥 Admin panel: http://localhost:{port}/admin")
    
    if demo_chatbot:
        print("✅ Demo chatbot hazır!")
    else:
        print("❌ Demo chatbot başlatılamadı!")
    
    # Create sample business for testing
    try:
        sample_business = {
            "name": "Demo Butik",
            "email": "demo@butik.com",
            "phone": "0555 555 55 55",
            "website": "www.demobutik.com",
            "instagram_handle": "@demobutik",
            "sector": "fashion"
        }
        
        businesses = business_manager.list_businesses()
        if not businesses:
            business_id = business_manager.create_business(sample_business)
            print(f"✅ Demo business created: {business_id}")
    except Exception as e:
        print(f"⚠️ Demo business creation failed: {e}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)