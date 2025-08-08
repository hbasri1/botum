#!/usr/bin/env python3
"""
Webhook System - Meta WhatsApp Business API ve Instagram için
"""

from flask import Flask, request, jsonify
import os
import json
import logging
import hmac
import hashlib
from typing import Dict, Any
from improved_final_mvp_system import ImprovedFinalMVPChatbot
from mvp_business_system import get_business_manager
from domain_config import domain_config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# WhatsApp Business API Configuration
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'your-verify-token-change-this')
WEBHOOK_SECRET = os.getenv('WHATSAPP_WEBHOOK_SECRET', 'your-webhook-secret-change-this')
ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', 'your-access-token-from-meta')

# Initialize components
business_manager = get_business_manager()

class WhatsAppWebhookHandler:
    """WhatsApp webhook handler"""
    
    def __init__(self):
        self.business_chatbots = {}  # Cache for business chatbots
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Verify webhook subscription"""
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("✅ Webhook verified successfully")
            return challenge
        else:
            logger.error("❌ Webhook verification failed")
            return "Verification failed"
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        if not WEBHOOK_SECRET:
            logger.warning("⚠️ No webhook secret configured")
            return True  # Skip verification if no secret
        
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook data"""
        try:
            # Extract message data
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Check if it's a message
            messages = value.get('messages', [])
            if not messages:
                return {'status': 'no_messages'}
            
            message = messages[0]
            
            # Extract sender info
            from_number = message.get('from')
            message_type = message.get('type')
            
            # Extract message content
            if message_type == 'text':
                message_text = message.get('text', {}).get('body', '')
            else:
                logger.info(f"Unsupported message type: {message_type}")
                return {'status': 'unsupported_type'}
            
            # Determine business from phone number or context
            business_id = self._determine_business(from_number, value)
            
            if not business_id:
                logger.error(f"❌ Could not determine business for number: {from_number}")
                return {'status': 'business_not_found'}
            
            # Get or create chatbot for business
            chatbot = self._get_business_chatbot(business_id)
            
            if not chatbot:
                logger.error(f"❌ Could not create chatbot for business: {business_id}")
                return {'status': 'chatbot_error'}
            
            # Process message with chatbot
            session_id = f"whatsapp_{from_number}"
            response = chatbot.chat(message_text, session_id=session_id)
            
            # Send response back via WhatsApp API
            self._send_whatsapp_message(from_number, response.message)
            
            logger.info(f"✅ Processed message from {from_number}: {message_text[:50]}...")
            
            return {
                'status': 'success',
                'business_id': business_id,
                'response_sent': True,
                'intent': response.intent,
                'confidence': response.confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Webhook processing error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _determine_business(self, phone_number: str, webhook_data: Dict) -> str:
        """Determine which business this message belongs to"""
        # Method 1: Check if phone number is registered to a specific business
        businesses = business_manager.get_all_businesses()
        
        for business in businesses:
            # Check if phone number matches business phone
            business_phone = business.get('phone', '').replace(' ', '').replace('+', '')
            incoming_phone = phone_number.replace(' ', '').replace('+', '')
            
            if business_phone and business_phone in incoming_phone:
                return business['business_id']
        
        # Method 2: Use webhook metadata (if available)
        metadata = webhook_data.get('metadata', {})
        if 'business_id' in metadata:
            return metadata['business_id']
        
        # Method 3: Default to first active business (for demo)
        active_businesses = [b for b in businesses if b.get('status') == 'active']
        if active_businesses:
            return active_businesses[0]['business_id']
        
        # Method 4: Use first available business
        if businesses:
            return businesses[0]['business_id']
        
        return None
    
    def _get_business_chatbot(self, business_id: str):
        """Get or create chatbot for business"""
        if business_id not in self.business_chatbots:
            try:
                # Create business-specific chatbot
                chatbot = ImprovedFinalMVPChatbot(business_id=business_id)
                self.business_chatbots[business_id] = chatbot
                logger.info(f"✅ Created chatbot for business: {business_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create chatbot for {business_id}: {e}")
                return None
        
        return self.business_chatbots[business_id]
    
    def _send_whatsapp_message(self, to_number: str, message: str):
        """Send message via WhatsApp Business API"""
        import requests
        
        if not ACCESS_TOKEN:
            logger.error("❌ No WhatsApp access token configured")
            return False
        
        # WhatsApp Business API endpoint
        url = f"https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages"
        
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': to_number,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to {to_number}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}")
            return False

class InstagramWebhookHandler:
    """Instagram webhook handler"""
    
    def __init__(self):
        self.business_chatbots = {}  # Cache for business chatbots
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Verify Instagram webhook subscription"""
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("✅ Instagram webhook verified successfully")
            return challenge
        else:
            logger.error("❌ Instagram webhook verification failed")
            return "Verification failed"
    
    def process_instagram_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Instagram webhook data"""
        try:
            # Extract Instagram message data
            entry = data.get('entry', [{}])[0]
            messaging = entry.get('messaging', [])
            
            if not messaging:
                return {'status': 'no_messages'}
            
            message_data = messaging[0]
            
            # Extract sender info
            sender_id = message_data.get('sender', {}).get('id')
            recipient_id = message_data.get('recipient', {}).get('id')
            
            # Extract message content
            message = message_data.get('message', {})
            message_text = message.get('text', '')
            
            if not message_text:
                logger.info("No text message found in Instagram webhook")
                return {'status': 'no_text_message'}
            
            # Determine business from recipient ID
            business_id = self._determine_business_from_instagram(recipient_id)
            
            if not business_id:
                logger.error(f"❌ Could not determine business for Instagram ID: {recipient_id}")
                return {'status': 'business_not_found'}
            
            # Get or create chatbot for business
            chatbot = self._get_business_chatbot(business_id)
            
            if not chatbot:
                logger.error(f"❌ Could not create chatbot for business: {business_id}")
                return {'status': 'chatbot_error'}
            
            # Process message with chatbot
            session_id = f"instagram_{sender_id}"
            response = chatbot.chat(message_text, session_id=session_id)
            
            # Send response back via Instagram API
            self._send_instagram_message(sender_id, response.message)
            
            logger.info(f"✅ Processed Instagram message from {sender_id}: {message_text[:50]}...")
            
            return {
                'status': 'success',
                'business_id': business_id,
                'response_sent': True,
                'intent': response.intent,
                'confidence': response.confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Instagram webhook processing error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _determine_business_from_instagram(self, instagram_id: str) -> str:
        """Determine which business this Instagram message belongs to"""
        businesses = business_manager.get_all_businesses()
        
        for business in businesses:
            # Check if Instagram ID matches business Instagram account
            instagram_account = business.get('instagram_account', {})
            if instagram_account.get('id') == instagram_id:
                return business['business_id']
        
        # Default to first active business (for demo)
        active_businesses = [b for b in businesses if b.get('status') == 'active']
        if active_businesses:
            return active_businesses[0]['business_id']
        
        return None
    
    def _get_business_chatbot(self, business_id: str):
        """Get or create chatbot for business"""
        if business_id not in self.business_chatbots:
            try:
                # Create business-specific chatbot
                chatbot = ImprovedFinalMVPChatbot(business_id=business_id)
                self.business_chatbots[business_id] = chatbot
                logger.info(f"✅ Created Instagram chatbot for business: {business_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create Instagram chatbot for {business_id}: {e}")
                return None
        
        return self.business_chatbots[business_id]
    
    def _send_instagram_message(self, recipient_id: str, message: str):
        """Send message via Instagram Basic Display API"""
        # Note: Instagram Basic Display API doesn't support sending messages
        # This would require Instagram Messaging API (different from Basic Display)
        # For now, we'll log the response
        logger.info(f"📱 Instagram response to {recipient_id}: {message[:100]}...")
        
        # TODO: Implement Instagram Messaging API when available
        # This requires business verification and additional permissions
        
        return True
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Verify webhook subscription"""
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("✅ Webhook verified successfully")
            return challenge
        else:
            logger.error("❌ Webhook verification failed")
            return "Verification failed"
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        if not WEBHOOK_SECRET:
            logger.warning("⚠️ No webhook secret configured")
            return True  # Skip verification if no secret
        
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook data"""
        try:
            # Extract message data
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Check if it's a message
            messages = value.get('messages', [])
            if not messages:
                return {'status': 'no_messages'}
            
            message = messages[0]
            
            # Extract sender info
            from_number = message.get('from')
            message_type = message.get('type')
            
            # Extract message content
            if message_type == 'text':
                message_text = message.get('text', {}).get('body', '')
            else:
                logger.info(f"Unsupported message type: {message_type}")
                return {'status': 'unsupported_type'}
            
            # Determine business from phone number or context
            business_id = self._determine_business(from_number, value)
            
            if not business_id:
                logger.error(f"❌ Could not determine business for number: {from_number}")
                return {'status': 'business_not_found'}
            
            # Get or create chatbot for business
            chatbot = self._get_business_chatbot(business_id)
            
            if not chatbot:
                logger.error(f"❌ Could not create chatbot for business: {business_id}")
                return {'status': 'chatbot_error'}
            
            # Process message with chatbot
            session_id = f"whatsapp_{from_number}"
            response = chatbot.chat(message_text, session_id=session_id)
            
            # Send response back via WhatsApp API
            self._send_whatsapp_message(from_number, response.message)
            
            logger.info(f"✅ Processed message from {from_number}: {message_text[:50]}...")
            
            return {
                'status': 'success',
                'business_id': business_id,
                'response_sent': True,
                'intent': response.intent,
                'confidence': response.confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Webhook processing error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _determine_business(self, phone_number: str, webhook_data: Dict) -> str:
        """Determine which business this message belongs to"""
        # Method 1: Check if phone number is registered to a specific business
        businesses = business_manager.get_all_businesses()
        
        for business in businesses:
            # Check if phone number matches business phone
            business_phone = business.get('phone', '').replace(' ', '').replace('+', '')
            incoming_phone = phone_number.replace(' ', '').replace('+', '')
            
            if business_phone and business_phone in incoming_phone:
                return business['business_id']
        
        # Method 2: Use webhook metadata (if available)
        metadata = webhook_data.get('metadata', {})
        if 'business_id' in metadata:
            return metadata['business_id']
        
        # Method 3: Default to first active business (for demo)
        active_businesses = [b for b in businesses if b.get('status') == 'active']
        if active_businesses:
            return active_businesses[0]['business_id']
        
        # Method 4: Use first available business
        if businesses:
            return businesses[0]['business_id']
        
        return None
    
    def _get_business_chatbot(self, business_id: str):
        """Get or create chatbot for business"""
        if business_id not in self.business_chatbots:
            try:
                # Create business-specific chatbot
                chatbot = ImprovedFinalMVPChatbot(business_id=business_id)
                self.business_chatbots[business_id] = chatbot
                logger.info(f"✅ Created chatbot for business: {business_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create chatbot for {business_id}: {e}")
                return None
        
        return self.business_chatbots[business_id]
    
    def _send_whatsapp_message(self, to_number: str, message: str):
        """Send message via WhatsApp Business API"""
        import requests
        
        if not ACCESS_TOKEN:
            logger.error("❌ No WhatsApp access token configured")
            return False
        
        # WhatsApp Business API endpoint
        url = f"https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages"
        
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': to_number,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to {to_number}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}")
            return False

# Initialize webhook handlers
whatsapp_handler = WhatsAppWebhookHandler()
instagram_handler = InstagramWebhookHandler()

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """WhatsApp webhook verification endpoint"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        result = whatsapp_handler.verify_webhook(mode, token, challenge)
        if result != "Verification failed":
            return result, 200
        else:
            return "Forbidden", 403
    else:
        return "Bad Request", 400

@app.route('/instagram/webhook', methods=['GET'])
def verify_instagram_webhook():
    """Instagram webhook verification endpoint"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        result = instagram_handler.verify_webhook(mode, token, challenge)
        if result != "Verification failed":
            return result, 200
        else:
            return "Forbidden", 403
    else:
        return "Bad Request", 400

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming WhatsApp webhook messages"""
    try:
        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not whatsapp_handler.verify_signature(request.data, signature):
            logger.error("❌ Invalid WhatsApp webhook signature")
            return "Forbidden", 403
        
        # Process webhook data
        data = request.get_json()
        if not data:
            return "Bad Request", 400
        
        result = whatsapp_handler.process_webhook(data)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ WhatsApp webhook handling error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/instagram/webhook', methods=['POST'])
def handle_instagram_webhook():
    """Handle incoming Instagram webhook messages"""
    try:
        # Verify signature (Instagram uses same signature method as Facebook)
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not whatsapp_handler.verify_signature(request.data, signature):
            logger.error("❌ Invalid Instagram webhook signature")
            return "Forbidden", 403
        
        # Process Instagram webhook data
        data = request.get_json()
        if not data:
            return "Bad Request", 400
        
        result = instagram_handler.process_instagram_webhook(data)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Instagram webhook handling error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Test webhook functionality"""
    try:
        data = request.get_json()
        
        # Simulate webhook data
        test_data = {
            'entry': [{
                'changes': [{
                    'value': {
                        'messages': [{
                            'from': data.get('phone', '905551234567'),
                            'type': 'text',
                            'text': {
                                'body': data.get('message', 'test mesajı')
                            }
                        }]
                    }
                }]
            }]
        }
        
        result = whatsapp_handler.process_webhook(test_data)
        
        return jsonify({
            'success': True,
            'test_result': result,
            'message': 'Webhook test completed'
        })
        
    except Exception as e:
        logger.error(f"❌ Webhook test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/webhook/status')
def webhook_status():
    """Get webhook status"""
    return jsonify({
        'status': 'active',
        'verify_token_configured': bool(VERIFY_TOKEN),
        'access_token_configured': bool(ACCESS_TOKEN),
        'webhook_secret_configured': bool(WEBHOOK_SECRET),
        'active_whatsapp_chatbots': len(whatsapp_handler.business_chatbots),
        'active_instagram_chatbots': len(instagram_handler.business_chatbots),
        'businesses_available': len(business_manager.get_all_businesses())
    })

@app.route('/webhook/businesses')
def webhook_businesses():
    """List businesses for webhook configuration"""
    businesses = business_manager.get_all_businesses()
    return jsonify({
        'businesses': businesses,
        'count': len(businesses)
    })

@app.route('/instagram/webhook/test', methods=['POST'])
def test_instagram_webhook():
    """Test Instagram webhook functionality"""
    try:
        data = request.get_json()
        
        # Simulate Instagram webhook data
        test_data = {
            'entry': [{
                'messaging': [{
                    'sender': {
                        'id': data.get('sender_id', '12345678901234567')
                    },
                    'recipient': {
                        'id': data.get('recipient_id', '98765432109876543')
                    },
                    'message': {
                        'text': data.get('message', 'Instagram test mesajı')
                    }
                }]
            }]
        }
        
        result = instagram_handler.process_instagram_webhook(test_data)
        
        return jsonify({
            'success': True,
            'test_result': result,
            'message': 'Instagram webhook test completed'
        })
        
    except Exception as e:
        logger.error(f"❌ Instagram webhook test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('WEBHOOK_PORT', 5007))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🔗 WhatsApp Webhook System başlatılıyor...")
    print(f"📱 http://localhost:{port}/webhook adresinde erişilebilir")
    print(f"🔧 Debug mode: {debug}")
    print(f"🔑 Verify token configured: {bool(VERIFY_TOKEN)}")
    print(f"🔐 Access token configured: {bool(ACCESS_TOKEN)}")
    
    if not VERIFY_TOKEN or VERIFY_TOKEN == 'your-verify-token-here':
        print("⚠️  WHATSAPP_VERIFY_TOKEN environment variable not configured!")
    
    if not ACCESS_TOKEN or ACCESS_TOKEN == 'your-access-token':
        print("⚠️  WHATSAPP_ACCESS_TOKEN environment variable not configured!")
    
    print("\n📋 Webhook Setup Instructions:")
    print("1. Set environment variables in .env file:")
    print("   WHATSAPP_VERIFY_TOKEN=your-verify-token")
    print("   WHATSAPP_ACCESS_TOKEN=your-access-token")
    print("   WHATSAPP_WEBHOOK_SECRET=your-webhook-secret")
    print("2. Use ngrok or similar to expose webhook publicly:")
    print("   ngrok http 5007")
    print("3. Configure webhook URL in Meta Developer Console:")
    print("   https://your-domain.com/webhook")
    
    app.run(debug=debug, host='0.0.0.0', port=port)