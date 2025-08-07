#!/usr/bin/env python3
"""
Production Web Interface for Improved Chatbot
Flask web interface with enhanced features
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_cors import CORS
from improved_final_mvp_system import ImprovedFinalMVPChatbot
from mvp_business_system import get_business_manager
import logging
import os
import time
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)  # Enable CORS for all routes

# Initialize business manager
business_manager = get_business_manager()

# Initialize chatbot with Bedrock + Gemini support
try:
    chatbot = ImprovedFinalMVPChatbot()
    logger.info("✅ Chatbot initialized successfully (Bedrock + Gemini)")
except Exception as e:
    logger.error(f"❌ Failed to initialize chatbot: {e}")
    chatbot = None

@app.route('/')
def index():
    """Main landing page with demo chat"""
    return render_template('public_demo.html')

@app.route('/demo')
def demo_chat():
    """Demo chat interface for public testing"""
    return render_template('chat.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/admin')
def admin_panel():
    """Admin panel redirect"""
    from flask import redirect
    return redirect('https://admin.kobibot.com', code=302)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with session management"""
    if not chatbot:
        return jsonify({
            'error': 'Chatbot not available',
            'response': 'Üzgünüm, sistem şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.',
            'success': False
        }), 500
    
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
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'response': 'Lütfen bir mesaj yazın.',
                'success': False
            }), 400
        
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

@app.route('/health')
def health():
    """Enhanced health check endpoint"""
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

@app.route('/stats')
def get_stats():
    """Get detailed system statistics"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not available'}), 500
    
    try:
        stats = chatbot.get_stats()
        cache_info = chatbot.smart_cache.get_cache_info()[:10]  # Top 10 cache entries
        
        return jsonify({
            'system_stats': stats,
            'cache_info': cache_info,
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation context and session cache"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not available'}), 500
    
    try:
        # Reset conversation context
        chatbot.conversation_handler.reset_context()
        
        # Clear session cache if session exists
        if 'session_id' in session:
            session_id = session['session_id']
            chatbot.smart_cache.clear_session(session_id)
            # Generate new session ID
            session['session_id'] = str(uuid.uuid4())
        
        return jsonify({
            'message': 'Konuşma ve cache sıfırlandı.',
            'success': True,
            'new_session_id': session.get('session_id')
        })
    except Exception as e:
        logger.error(f"❌ Reset error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/session/clear', methods=['POST'])
def clear_session():
    """Clear current session cache"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not available'}), 500
    
    try:
        if 'session_id' in session:
            session_id = session['session_id']
            chatbot.smart_cache.clear_session(session_id)
            return jsonify({
                'message': f'Session cache cleared: {session_id}',
                'success': True
            })
        else:
            return jsonify({
                'message': 'No active session found',
                'success': True
            })
    except Exception as e:
        logger.error(f"❌ Session clear error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/instagram-post', methods=['POST'])
def handle_instagram_post():
    """Handle Instagram post reference queries"""
    if not chatbot:
        return jsonify({'error': 'Chatbot not available'}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        post_text = data.get('post_text', '')
        user_query = data.get('user_query', '')
        
        # Extract product name from post text
        if post_text:
            # Simple product name extraction
            product_keywords = ['afrika', 'hamile', 'dantelli', 'gecelik', 'pijama', 'sabahlık', 'takım']
            found_products = [keyword for keyword in product_keywords if keyword.lower() in post_text.lower()]
            
            if found_products:
                # Create enhanced query
                enhanced_query = f"{' '.join(found_products)} {user_query}"
                
                # Get session ID
                if 'session_id' not in session:
                    session['session_id'] = str(uuid.uuid4())
                session_id = session['session_id']
                
                # Process with chatbot
                response = chatbot.chat(enhanced_query, session_id=session_id)
                
                return jsonify({
                    'response': response.message,
                    'intent': response.intent,
                    'confidence': response.confidence,
                    'extracted_products': found_products,
                    'enhanced_query': enhanced_query,
                    'success': True
                })
        
        # Fallback to normal chat
        return jsonify({
            'message': 'Instagram gönderisinden ürün bilgisi çıkarılamadı. Lütfen ürün adını belirtin.',
            'success': False
        })
        
    except Exception as e:
        logger.error(f"❌ Instagram post error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.route('/error-report', methods=['POST'])
def error_report():
    """Handle client-side error reports"""
    try:
        data = request.get_json()
        if data:
            logger.error(f"Client error report: {data}")
        return jsonify({'status': 'received'}), 200
    except Exception as e:
        logger.error(f"Error handling error report: {e}")
        return jsonify({'status': 'error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🌐 Production Web Interface başlatılıyor...")
    print(f"📱 http://localhost:{port} adresinde erişilebilir")
    print(f"🔧 Debug mode: {debug}")
    
    if chatbot:
        print("✅ Chatbot hazır!")
        health = chatbot.health_check()
        print(f"🏥 Health: {health}")
    else:
        print("❌ Chatbot başlatılamadı!")
    
    app.run(debug=debug, host='0.0.0.0', port=port)