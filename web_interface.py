# Multi-Sektör Web Arayüzü - Temel yapı

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

def setup_web_routes(app: FastAPI):
    """Web arayüzü rotalarını kur"""
    
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Multi-Sektör Chatbot Platform</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .sector-selector { margin-bottom: 20px; }
                .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 20px; }
                .input-container { margin-top: 20px; }
                input[type="text"] { width: 70%; padding: 10px; }
                button { padding: 10px 20px; margin-left: 10px; }
                .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
                .user { background: #e3f2fd; text-align: right; }
                .bot { background: #f5f5f5; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Multi-Sektör Chatbot Platform</h1>
                
                <div class="sector-selector">
                    <label>Sektör Seçin:</label>
                    <select id="sector">
                        <option value="fashion">👗 Giyim Sektörü</option>
                        <option value="electronics">📱 Elektronik (Yakında)</option>
                        <option value="food">🍕 Yemek (Yakında)</option>
                        <option value="automotive">🚗 Otomotiv (Yakında)</option>
                    </select>
                </div>
                
                <div id="chat-container" class="chat-container">
                    <div class="message bot">
                        Merhaba! Size nasıl yardımcı olabilirim?
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" id="messageInput" placeholder="Mesajınızı yazın..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Gönder</button>
                </div>
            </div>
            
            <script>
                async function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    // Kullanıcı mesajını göster
                    addMessage(message, 'user');
                    input.value = '';
                    
                    try {
                        const response = await fetch('/ask', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ question: message })
                        });
                        
                        const data = await response.json();
                        addMessage(data.answer, 'bot');
                    } catch (error) {
                        addMessage('Üzgünüm, bir hata oluştu.', 'bot');
                    }
                }
                
                function addMessage(text, sender) {
                    const container = document.getElementById('chat-container');
                    const div = document.createElement('div');
                    div.className = `message ${sender}`;
                    div.textContent = text;
                    container.appendChild(div);
                    container.scrollTop = container.scrollHeight;
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }
            </script>
        </body>
        </html>
        """
    
    @app.get("/admin")
    async def admin_panel():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel - Multi-Sektör Chatbot</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
                .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
                .stat-card { padding: 20px; background: #f5f5f5; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 Admin Panel</h1>
                
                <div class="section">
                    <h2>📊 Sistem İstatistikleri</h2>
                    <div class="stats">
                        <div class="stat-card">
                            <h3>Toplam Sorgular</h3>
                            <p>1,234</p>
                        </div>
                        <div class="stat-card">
                            <h3>Başarı Oranı</h3>
                            <p>87.5%</p>
                        </div>
                        <div class="stat-card">
                            <h3>Aktif Sektörler</h3>
                            <p>1</p>
                        </div>
                        <div class="stat-card">
                            <h3>Cache Hit Rate</h3>
                            <p>65%</p>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🏢 Sektör Yönetimi</h2>
                    <p>Yeni sektör ekleme ve mevcut sektörleri düzenleme</p>
                    <button>Yeni Sektör Ekle</button>
                </div>
                
                <div class="section">
                    <h2>🧪 Test Sistemi</h2>
                    <p>Sistem performansını test et</p>
                    <button onclick="runTests()">Testleri Çalıştır</button>
                    <div id="test-results"></div>
                </div>
            </div>
            
            <script>
                async function runTests() {
                    document.getElementById('test-results').innerHTML = 'Testler çalışıyor...';
                    // Test API'si buraya eklenecek
                }
            </script>
        </body>
        </html>
        """