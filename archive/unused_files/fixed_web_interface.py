#!/usr/bin/env python3
"""
Fixed Web Interface
Simple, reliable Flask interface
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from fixed_final_system import FixedFinalChatbot
import logging
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize chatbot
try:
    chatbot = FixedFinalChatbot()
    logger.info("✅ Fixed Chatbot initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize chatbot: {e}")
    chatbot = None

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    if not chatbot:
        return jsonify({
            'error': 'Chatbot not available',
            'response': 'Üzgünüm, sistem şu anda kullanılamıyor.',
            'success': False
        }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'response': 'Geçersiz istek formatı.',
                'success': False
            }), 400
        
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'response': 'Lütfen bir mesaj yazın.',
                'success': False
            }), 400
        
        # Get response from chatbot
        start_time = time.time()
        chat_response = chatbot.chat(user_message)
        processing_time = time.time() - start_time
        
        # Get system stats
        stats = chatbot.get_stats()
        
        return jsonify({
            'response': chat_response.message,
            'intent': chat_response.intent,
            'confidence': round(chat_response.confidence, 2),
            'products_found': chat_response.products_found,
            'processing_time': round(processing_time, 3),
            'success': True,
            'stats': {
                'total_requests': stats['total_requests'],
                'success_rate': round(stats['success_rate'], 1),
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

@app.route('/health')
def health():
    """Health check endpoint"""
    if not chatbot:
        return jsonify({
            'status': 'unhealthy',
            'chatbot_available': False,
            'error': 'Chatbot not initialized'
        }), 500
    
    try:
        health_check = chatbot.health_check()
        stats = chatbot.get_stats()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'chatbot_available': True,
            'health_check': health_check,
            'stats': stats,
            'uptime': 'Running'
        })
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation context"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not available'}), 500
    
    try:
        chatbot.reset_conversation()
        return jsonify({
            'message': 'Konuşma sıfırlandı.',
            'success': True
        })
    except Exception as e:
        logger.error(f"❌ Reset error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🌐 Fixed Web Interface başlatılıyor...")
    print(f"📱 http://localhost:{port} adresinde erişilebilir")
    
    if chatbot:
        print("✅ Chatbot hazır!")
        health = chatbot.health_check()
        print(f"🏥 Health: {health}")
    else:
        print("❌ Chatbot başlatılamadı!")
    
    app.run(debug=debug, host='0.0.0.0', port=port)