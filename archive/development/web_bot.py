#!/usr/bin/env python3
"""
Web Bot Interface - Gemini Function Calling ile
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.services.llm_service import LLMService
from orchestrator.services.function_execution_coordinator import FunctionExecutionCoordinator
from orchestrator.services.database_service import DatabaseService
from orchestrator.services.function_cache_manager import FunctionCacheManager

app = FastAPI(title="Gemini Function Calling Bot", version="2.0.0")

# Initialize function calling system - SIMPLE SYSTEM
llm_service = LLMService(enable_function_calling=True)

# Maliyet takibi için
try:
    from orchestrator.services.cost_optimizer import cost_optimizer
except ImportError:
    cost_optimizer = None

# Initialize services for function coordinator
db_service = DatabaseService()
cache_manager = FunctionCacheManager()
function_coordinator = FunctionExecutionCoordinator(db_service, cache_manager)

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    business_id: str = "fashion_boutique"

class ChatResponse(BaseModel):
    answer: str
    method: str
    confidence: float
    execution_time_ms: int

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Ana sayfa - Gelişmiş web interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Gemini Function Calling Bot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container { 
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 90%;
                max-width: 800px;
                height: 600px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .header h1 { font-size: 24px; margin-bottom: 5px; }
            .header p { opacity: 0.9; font-size: 14px; }
            .status {
                background: #f8f9fa;
                padding: 10px 20px;
                border-bottom: 1px solid #e9ecef;
                font-size: 12px;
                color: #6c757d;
                display: flex;
                justify-content: space-between;
            }
            .chat-container { 
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f8f9fa;
            }
            .message { 
                margin: 15px 0;
                display: flex;
                align-items: flex-start;
            }
            .message.user { justify-content: flex-end; }
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 14px;
                line-height: 1.4;
            }
            .user .message-content {
                background: #007bff;
                color: white;
                border-bottom-right-radius: 4px;
            }
            .bot .message-content {
                background: white;
                color: #333;
                border: 1px solid #e9ecef;
                border-bottom-left-radius: 4px;
            }
            .message-meta {
                font-size: 11px;
                opacity: 0.7;
                margin-top: 4px;
            }
            .input-container { 
                padding: 20px;
                background: white;
                border-top: 1px solid #e9ecef;
                display: flex;
                gap: 10px;
            }
            .input-container input {
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #e9ecef;
                border-radius: 25px;
                font-size: 14px;
                outline: none;
            }
            .input-container input:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
            }
            .input-container button {
                padding: 12px 24px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.2s;
            }
            .input-container button:hover { background: #0056b3; }
            .input-container button:disabled { 
                background: #6c757d;
                cursor: not-allowed;
            }
            .typing {
                display: none;
                padding: 12px 16px;
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 18px;
                border-bottom-left-radius: 4px;
                max-width: 70%;
            }
            .typing-dots {
                display: flex;
                gap: 4px;
            }
            .typing-dots span {
                width: 8px;
                height: 8px;
                background: #6c757d;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }
            .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
            .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }
            .method-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: bold;
                margin-left: 8px;
            }
            .method-function { background: #28a745; color: white; }
            .method-intent { background: #ffc107; color: black; }
            .method-error { background: #dc3545; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Gemini Function Calling Bot</h1>
                <p>Akıllı müşteri hizmetleri asistanı</p>
            </div>
            
            <div class="status">
                <span>🟢 Sistem Aktif</span>
                <span id="stats">Function Calling: Aktif | Cache: Aktif</span>
            </div>
            
            <div id="chat-container" class="chat-container">
                <div class="message bot">
                    <div class="message-content">
                        Merhaba! Ben Gemini Function Calling ile çalışan akıllı asistanınızım. 
                        Size nasıl yardımcı olabilirim?
                        <div class="message-meta">
                            <span class="method-badge method-function">FUNCTION CALLING</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="typing" id="typing">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Mesajınızı yazın... (örn: gecelik fiyatı ne kadar?)" onkeypress="handleKeyPress(event)">
                <button id="sendButton" onclick="sendMessage()">Gönder</button>
            </div>
        </div>
        
        <script>
            let sessionId = 'web_' + Date.now();
            
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const button = document.getElementById('sendButton');
                const message = input.value.trim();
                
                if (!message) return;
                
                // UI güncellemeleri
                addMessage(message, 'user');
                input.value = '';
                button.disabled = true;
                showTyping();
                
                try {
                    const startTime = Date.now();
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            question: message,
                            session_id: sessionId,
                            business_id: 'fashion_boutique'
                        })
                    });
                    
                    const data = await response.json();
                    const responseTime = Date.now() - startTime;
                    
                    hideTyping();
                    addMessage(data.answer, 'bot', data.method, data.confidence, responseTime);
                    
                } catch (error) {
                    hideTyping();
                    addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', 'bot', 'error', 0, 0);
                } finally {
                    button.disabled = false;
                    input.focus();
                }
            }
            
            function addMessage(text, sender, method = null, confidence = 0, responseTime = 0) {
                const container = document.getElementById('chat-container');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = text;
                
                if (sender === 'bot' && method) {
                    const metaDiv = document.createElement('div');
                    metaDiv.className = 'message-meta';
                    
                    const methodBadge = document.createElement('span');
                    methodBadge.className = `method-badge method-${method.includes('function') ? 'function' : method.includes('intent') ? 'intent' : 'error'}`;
                    methodBadge.textContent = method.toUpperCase();
                    
                    metaDiv.appendChild(methodBadge);
                    
                    if (confidence > 0) {
                        metaDiv.appendChild(document.createTextNode(` | Güven: ${(confidence * 100).toFixed(0)}%`));
                    }
                    
                    if (responseTime > 0) {
                        metaDiv.appendChild(document.createTextNode(` | ${responseTime}ms`));
                    }
                    
                    contentDiv.appendChild(metaDiv);
                }
                
                messageDiv.appendChild(contentDiv);
                container.appendChild(messageDiv);
                container.scrollTop = container.scrollHeight;
            }
            
            function showTyping() {
                const typing = document.getElementById('typing');
                const container = document.getElementById('chat-container');
                typing.style.display = 'block';
                container.appendChild(typing);
                container.scrollTop = container.scrollHeight;
            }
            
            function hideTyping() {
                const typing = document.getElementById('typing');
                typing.style.display = 'none';
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            }
            
            // Auto-focus input
            document.getElementById('messageInput').focus();
            
            // Test mesajları için örnekler
            const examples = [
                'gecelik fiyatı ne kadar?',
                'telefon numaranız nedir?',
                'iade koşulları nelerdir?',
                'pijama stok durumu nedir?'
            ];
            
            // Placeholder'ı dinamik yap
            let exampleIndex = 0;
            setInterval(() => {
                const input = document.getElementById('messageInput');
                if (input !== document.activeElement) {
                    input.placeholder = `Mesajınızı yazın... (örn: ${examples[exampleIndex]})`;
                    exampleIndex = (exampleIndex + 1) % examples.length;
                }
            }, 3000);
        </script>
    </body>
    </html>
    """

@app.post("/ask", response_model=ChatResponse)
async def ask(request: ChatRequest):
    """Chat endpoint - Function calling ile"""
    start_time = time.time()
    
    try:
        # Session ID oluştur
        session_id = request.session_id or f"web_{int(time.time())}"
        
        # LLM service ile process et - SIMPLE SYSTEM
        result = await llm_service.process_message_with_functions(
            prompt=request.question,
            session_id=session_id,
            isletme_id=request.business_id
        )
        
        # Maliyet takibi
        if cost_optimizer and result:
            method = result.get("method", "unknown")
            cost_optimizer.track_query(method)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        if result:
            method = result.get("method", "unknown")
            confidence = result.get("confidence", 0.0)
            
            # Function call varsa execute et
            if result.get("function_call"):
                function_call = result["function_call"]
                execution_result = await function_coordinator.execute_function_call(
                    function_name=function_call["name"],
                    arguments=function_call["args"],
                    session_id=session_id,
                    business_id=request.business_id
                )
                
                if execution_result and execution_result.get("success"):
                    final_response = execution_result.get("result", {}).get("response", "İşlem tamamlandı.")
                    method = "function_calling"
                else:
                    # Function call başarısızsa fallback
                    final_response = await handle_fallback_response(request.question, result)
                    method = "fallback"
            else:
                # Direct response varsa kullan
                final_response = result.get("final_response", "")
                
                if not final_response:
                    # Intent'e göre response oluştur
                    intent = result.get("intent", "unknown")
                    if intent == "greeting":
                        final_response = "Merhaba! Size nasıl yardımcı olabilirim?"
                    elif intent == "product_query":
                        final_response = "Hangi ürün hakkında bilgi almak istiyorsunuz?"
                    elif intent == "meta_query":
                        final_response = "Genel bilgi sorgunuz alındı. Size yardımcı olmaya çalışıyorum..."
                    elif intent == "unknown":
                        final_response = "Üzgünüm, sorunuzu tam olarak anlayamadım. Lütfen daha açık bir şekilde sorabilir misiniz?"
                    else:
                        final_response = f"Sorgunuz işleniyor... (Intent: {intent})"
            
            return ChatResponse(
                answer=final_response,
                method=method,
                confidence=confidence,
                execution_time_ms=execution_time
            )
        else:
            return ChatResponse(
                answer="Üzgünüm, size şu anda yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin.",
                method="error",
                confidence=0.0,
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        return ChatResponse(
            answer=f"Sistem hatası oluştu: {str(e)}",
            method="error",
            confidence=0.0,
            execution_time_ms=execution_time
        )

async def handle_fallback_response(query: str, llm_result: dict) -> str:
    """Function call başarısızsa fallback response"""
    intent = llm_result.get("intent", "unknown")
    
    if intent == "greeting":
        return "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"
    elif intent == "thanks":
        return "Rica ederim! Başka sorunuz var mı?"
    elif intent == "product_query":
        return "Ürün bilgisi için lütfen daha spesifik olabilir misiniz?"
    elif intent == "meta_query":
        return "İşletme bilgileri için WhatsApp: 0555 555 55 55"
    else:
        return "Anlayamadım. Ürün, fiyat veya iletişim hakkında sorabilirsiniz."

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "function_calling": "enabled",
        "llm_service": await llm_service.health_check()
    }

@app.get("/stats")
async def stats():
    """Sistem istatistikleri"""
    return {
        "system": "Gemini Function Calling Bot",
        "version": "2.0.0",
        "function_calling": "enabled",
        "cache": "enabled",
        "security": "enabled",
        "uptime": "active"
    }

if __name__ == "__main__":
    import uvicorn
    print("🌐 Starting Gemini Function Calling Web Bot...")
    print("🔗 Web Interface: http://localhost:8003")
    print("📖 API Docs: http://localhost:8003/docs")
    print("🔍 Health Check: http://localhost:8003/health")
    print("📊 Stats: http://localhost:8003/stats")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)