#!/usr/bin/env python3
"""
Admin Web Interface - Gelişmiş admin paneli
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import logging
from pathlib import Path
import time
import uuid

# Import our modules
from mvp_business_system import get_business_manager
from admin_file_processor import AdminFileProcessor
from improved_final_mvp_system import ImprovedFinalMVPChatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'admin-secret-key-change-in-production')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'json', 'csv', 'xlsx', 'xls', 'txt'}

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize components
business_manager = get_business_manager()
file_processor = AdminFileProcessor()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def admin_dashboard():
    """Admin dashboard"""
    try:
        # Get all businesses
        businesses = business_manager.get_all_businesses()
        
        # Calculate stats
        total_businesses = len(businesses)
        active_businesses = len([b for b in businesses if b.get('status') == 'active'])
        trial_businesses = len([b for b in businesses if b.get('status') == 'trial'])
        
        return render_template('admin_dashboard.html', 
                             businesses=businesses,
                             stats={
                                 'total': total_businesses,
                                 'active': active_businesses,
                                 'trial': trial_businesses
                             })
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        flash(f'Dashboard yüklenirken hata: {e}', 'error')
        return render_template('admin_dashboard.html', businesses=[], stats={})

@app.route('/api/businesses', methods=['POST'])
def create_business():
    """Create new business"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'email', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create business
        business_id = business_manager.create_business_from_params(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            website=data.get('website', ''),
            instagram_handle=data.get('instagram_handle', ''),
            sector=data.get('sector', 'general')
        )
        
        logger.info(f"✅ Created business: {business_id}")
        
        return jsonify({
            'success': True,
            'business_id': business_id,
            'message': 'Business created successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Business creation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/businesses/<business_id>/products', methods=['POST'])
def upload_products(business_id):
    """Upload and process products file"""
    try:
        # Check if business exists
        business = business_manager.get_business(business_id)
        if not business:
            return jsonify({
                'success': False,
                'error': 'Business not found'
            }), 404
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{business_id}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        logger.info(f"📁 File saved: {file_path}")
        
        # Process file with Gemini
        processing_result = file_processor.process_uploaded_file(file_path, business_id)
        
        if not processing_result['success']:
            # Clean up file
            os.remove(file_path)
            return jsonify(processing_result), 400
        
        # Add products to business
        products = processing_result['products']
        added_count = 0
        
        for product in products:
            try:
                business_manager.add_product(business_id, product)
                added_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Failed to add product {product.get('name')}: {e}")
        
        # Clean up uploaded file
        os.remove(file_path)
        
        logger.info(f"✅ Added {added_count} products to business {business_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed and added {added_count} products',
            'processed_count': len(products),
            'added_count': added_count,
            'business_id': business_id
        })
        
    except Exception as e:
        logger.error(f"❌ Product upload error: {e}")
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/businesses/<business_id>/stats')
def get_business_stats(business_id):
    """Get business statistics"""
    try:
        business = business_manager.get_business(business_id)
        if not business:
            return jsonify({
                'success': False,
                'error': 'Business not found'
            }), 404
        
        # Get products
        products = business_manager.get_products(business_id)
        
        # Calculate stats
        categories = list(set([p.get('category', 'unknown') for p in products]))
        colors = list(set([p.get('color', 'unknown') for p in products]))
        total_stock = sum([p.get('stock', 0) for p in products])
        avg_price = sum([p.get('price', 0) for p in products]) / len(products) if products else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'business_name': business['name'],
                'business_id': business_id,
                'product_count': len(products),
                'categories': categories,
                'colors': colors,
                'total_stock': total_stock,
                'average_price': round(avg_price, 2),
                'status': business.get('status', 'unknown')
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Business stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/businesses/<business_id>/test', methods=['POST'])
def test_business_chatbot(business_id):
    """Test business chatbot"""
    try:
        business = business_manager.get_business(business_id)
        if not business:
            return jsonify({
                'success': False,
                'error': 'Business not found'
            }), 404
        
        data = request.get_json()
        test_message = data.get('message', 'merhaba')
        
        # Create chatbot instance for this business
        chatbot = business_manager.get_business_chatbot_instance(business_id)
        
        # Generate test session ID
        session_id = f"test_{uuid.uuid4()}"
        
        # Get response
        start_time = time.time()
        response = chatbot.chat(test_message, session_id=session_id)
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'response': response.message,
            'intent': response.intent,
            'confidence': response.confidence,
            'products_found': response.products_found,
            'processing_time': round(processing_time, 3),
            'business_id': business_id
        })
        
    except Exception as e:
        logger.error(f"❌ Chatbot test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file-processor/stats')
def get_file_processor_stats():
    """Get file processor statistics"""
    try:
        stats = file_processor.get_processing_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"❌ File processor stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system/health')
def system_health():
    """System health check"""
    try:
        # Check components
        health_status = {
            'business_manager': True,
            'file_processor': True,
            'upload_folder': os.path.exists(UPLOAD_FOLDER),
            'gemini_api': bool(os.getenv('GEMINI_API_KEY')),
            'timestamp': time.time()
        }
        
        # Test business manager
        try:
            businesses = business_manager.get_all_businesses()
            health_status['business_count'] = len(businesses)
        except Exception as e:
            health_status['business_manager'] = False
            health_status['business_manager_error'] = str(e)
        
        # Test file processor
        try:
            file_processor.get_processing_stats()
        except Exception as e:
            health_status['file_processor'] = False
            health_status['file_processor_error'] = str(e)
        
        all_healthy = all([
            health_status['business_manager'],
            health_status['file_processor'],
            health_status['upload_folder'],
            health_status['gemini_api']
        ])
        
        return jsonify({
            'success': True,
            'healthy': all_healthy,
            'components': health_status
        })
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('ADMIN_PORT', 5006))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🔧 Admin Web Interface başlatılıyor...")
    print(f"📱 http://localhost:{port} adresinde erişilebilir")
    print(f"🔧 Debug mode: {debug}")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📊 Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Test components
    try:
        businesses = business_manager.get_all_businesses()
        print(f"✅ Business Manager: {len(businesses)} businesses loaded")
    except Exception as e:
        print(f"❌ Business Manager error: {e}")
    
    try:
        stats = file_processor.get_processing_stats()
        print(f"✅ File Processor: {stats['model_used']}")
    except Exception as e:
        print(f"❌ File Processor error: {e}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)