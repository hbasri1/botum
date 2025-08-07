#!/usr/bin/env python3
"""
MVP Web Interface for Chatbot
Simple Flask web interface
"""

from flask import Flask, render_template, request, jsonify
from improved_final_mvp_system import ImprovedFinalMVPChatbot
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize chatbot
try:
    chatbot = ImprovedFinalMVPChatbot()
    logger.info("Chatbot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize chatbot: {e}")
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
            'response': 'Üzgünüm, sistem şu anda kullanılamıyor.'
        }), 500
    
    try:
        user_message = request.json.get('message', '').strip()
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'response': 'Lütfen bir mesaj yazın.'
            }), 400
        
        # Get response from chatbot
        chat_response = chatbot.chat(user_message)
        
        return jsonify({
            'response': chat_response.message,
            'intent': chat_response.intent,
            'confidence': chat_response.confidence,
            'products_found': chat_response.products_found,
            'processing_time': chat_response.processing_time,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            'error': str(e),
            'response': 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.'
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if chatbot else 'unhealthy',
        'chatbot_available': chatbot is not None
    })

if __name__ == '__main__':
    print("🌐 MVP Web Interface başlatılıyor...")
    print("📱 http://localhost:5004 adresinde erişilebilir")
    app.run(debug=False, host='0.0.0.0', port=5004)