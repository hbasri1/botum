#!/usr/bin/env python3
"""
AWS Bedrock Integration - Mistral 7B Model
"""

import boto3
import json
import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import base64

logger = logging.getLogger(__name__)

@dataclass
class BedrockResponse:
    """Bedrock yanıt modeli"""
    text: str
    confidence: float
    model_used: str
    tokens_used: int

class AWSBedrockClient:
    """AWS Bedrock Mistral client"""
    
    def __init__(self):
        """Initialize Bedrock client"""
        
        # AWS credentials from API key
        self.api_key = "ABSKQmVkcm9ja0FQSUtleS12OXUzLWF0LTczMDQ3MDA5MDM2MzoxdmVEV2hUZFlCSVJ0K25JWWlUdTgzYlJJajhYWG5jNXpHeStsZWV2SkxtbmZnQ3BQS1Uyd2VaTE9mST0="
        
        try:
            # For now, disable Bedrock and use fallback
            # AWS Bedrock requires proper IAM credentials setup
            logger.warning("⚠️ AWS Bedrock disabled - using Gemini fallback")
            self.bedrock_client = None
            return
            
            self.model_id = "mistral.mistral-7b-instruct-v0:2"
            
            logger.info("✅ AWS Bedrock Mistral client initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bedrock client: {e}")
            self.bedrock_client = None
    
    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Optional[BedrockResponse]:
        """Generate response using Mistral 7B"""
        
        if not self.bedrock_client:
            logger.error("❌ Bedrock client not initialized")
            return None
        
        try:
            # Prepare request body for Mistral
            request_body = {
                "prompt": f"<s>[INST] {prompt} [/INST]",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 50
            }
            
            # Make request to Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text
            generated_text = response_body.get('outputs', [{}])[0].get('text', '')
            
            # Calculate confidence (simple heuristic)
            confidence = min(1.0, len(generated_text) / 100)
            
            # Token usage
            tokens_used = response_body.get('usage', {}).get('total_tokens', 0)
            
            return BedrockResponse(
                text=generated_text.strip(),
                confidence=confidence,
                model_used=self.model_id,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"❌ Bedrock generation error: {e}")
            return None
    
    def chat_completion(self, messages: list, system_prompt: str = "") -> Optional[str]:
        """Chat completion with conversation context"""
        
        # Build conversation prompt
        conversation = ""
        if system_prompt:
            conversation += f"System: {system_prompt}\n\n"
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            conversation += f"{role.capitalize()}: {content}\n"
        
        conversation += "Assistant:"
        
        # Generate response
        response = self.generate_response(conversation)
        
        if response:
            return response.text
        return None
    
    def intent_detection(self, user_message: str) -> Dict[str, Any]:
        """Intent detection using Mistral"""
        
        prompt = f"""
Aşağıdaki kullanıcı mesajının intent'ini (amacını) belirle ve JSON formatında döndür.

Kullanıcı mesajı: "{user_message}"

Mümkün intent'ler:
- greeting: selamlama
- product_search: ürün arama
- price_inquiry: fiyat sorgusu
- shipping_info: kargo bilgisi
- return_policy: iade politikası
- contact_info: iletişim bilgisi
- complaint: şikayet
- compliment: övgü
- goodbye: veda
- other: diğer

JSON formatı:
{{
    "intent": "intent_adı",
    "confidence": 0.95,
    "entities": {{"ürün": "ürün_adı", "renk": "renk_adı"}},
    "explanation": "kısa açıklama"
}}
"""
        
        response = self.generate_response(prompt, max_tokens=200, temperature=0.3)
        
        if response:
            try:
                # JSON parse et
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # Fallback
                return {
                    "intent": "other",
                    "confidence": 0.5,
                    "entities": {},
                    "explanation": "JSON parse error"
                }
        
        return {
            "intent": "error",
            "confidence": 0.0,
            "entities": {},
            "explanation": "Model response error"
        }
    
    def product_recommendation(self, user_query: str, products: list) -> str:
        """Product recommendation using Mistral"""
        
        # Prepare products for prompt
        products_text = ""
        for i, product in enumerate(products[:10], 1):  # Limit to 10 products
            products_text += f"{i}. {product.get('name', 'N/A')} - {product.get('price', 0)} TL - {product.get('color', 'N/A')} - Stok: {product.get('stock', 0)}\n"
        
        prompt = f"""
Müşteri şu ürünü arıyor: "{user_query}"

Mevcut ürünler:
{products_text}

Müşteriye uygun ürünleri öner ve Türkçe olarak samimi bir şekilde yanıtla. 
Ürün numaralarını kullan ve fiyat bilgilerini de ver.
Maksimum 3 ürün öner.
"""
        
        response = self.generate_response(prompt, max_tokens=300, temperature=0.7)
        
        if response:
            return response.text
        
        return "Üzgünüm, şu anda ürün önerisi yapamıyorum."
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for Bedrock service"""
        
        if not self.bedrock_client:
            return {
                'status': 'unhealthy',
                'error': 'Client not initialized'
            }
        
        try:
            # Simple test request
            test_response = self.generate_response("Test", max_tokens=10)
            
            if test_response:
                return {
                    'status': 'healthy',
                    'model': self.model_id,
                    'test_response_length': len(test_response.text),
                    'tokens_used': test_response.tokens_used
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'No response from model'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Global instance
bedrock_client = AWSBedrockClient()

def get_bedrock_client():
    """Global Bedrock client'ı döndür"""
    return bedrock_client

# Test function
def test_bedrock():
    """Test Bedrock integration"""
    client = get_bedrock_client()
    
    print("🧪 Testing Bedrock Mistral...")
    
    # Health check
    health = client.health_check()
    print(f"Health: {health}")
    
    # Simple generation
    response = client.generate_response("Merhaba, nasılsın?")
    if response:
        print(f"Response: {response.text}")
        print(f"Confidence: {response.confidence}")
        print(f"Tokens: {response.tokens_used}")
    
    # Intent detection
    intent = client.intent_detection("hamile pijama arıyorum")
    print(f"Intent: {intent}")
    
    # Product recommendation
    test_products = [
        {"name": "Hamile Pijama", "price": 299, "color": "mavi", "stock": 5},
        {"name": "Gecelik", "price": 199, "color": "siyah", "stock": 3}
    ]
    
    recommendation = client.product_recommendation("hamile pijama", test_products)
    print(f"Recommendation: {recommendation}")

if __name__ == '__main__':
    test_bedrock()