# 🤖 Gemini 2.5 Pro Kurulum Rehberi

## 1. Google AI Studio'dan API Key Alma

### Adım 1: Google AI Studio'ya Git
- https://aistudio.google.com/ adresine git
- Google hesabınla giriş yap

### Adım 2: API Key Oluştur
- Sol menüden "API keys" seçeneğine tıkla
- "Create API key" butonuna tıkla
- Projen için "cobalt-anchor-466417-j0" seç
- API key'i kopyala

### Adım 3: Environment Variable Olarak Ayarla
```bash
# Terminal'de
export GEMINI_API_KEY="your-actual-api-key-here"

# Veya .env dosyasına ekle
echo "GEMINI_API_KEY=your-actual-api-key-here" >> .env
```

## 2. Gemini Paketini Yükle

```bash
pip install google-generativeai
```

## 3. Test Et

```bash
cd orchestrator
python3 -c "
import google.generativeai as genai
import os

# API key'i ayarla
api_key = os.getenv('GEMINI_API_KEY', 'your-key-here')
genai.configure(api_key=api_key)

# Model'i test et
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content('Merhaba, nasılsın?')
print('✅ Gemini çalışıyor!')
print('Yanıt:', response.text)
"
```

## 4. Sistemde Kullan

### Gerçek LLM ile Test
```bash
# API key'i ayarladıktan sonra
python3 test_learning_simple.py
```

### Uygulamayı Başlat
```bash
# API key'i environment'ta olduğundan emin ol
python3 -m app.main
```

## 5. Fine-tuning için Hazırlık

### Training Data Export Et
```bash
curl http://localhost:8000/admin/learning/export-training-data
```

### Learning Insights Al
```bash
curl http://localhost:8000/admin/learning/insights
```

### Learning Loop Başlat
```bash
curl -X POST http://localhost:8000/admin/learning/start
```

## 6. Model Performance İzle

### Model Bilgileri
```bash
curl http://localhost:8000/admin/model/info
```

### Learning Raporu
```bash
curl http://localhost:8000/admin/learning/report
```

## 7. Fine-tuning Süreci (Gelecek)

### 1. Training Data Hazırla
- Sistem otomatik olarak yüksek kaliteli etkileşimleri topluyor
- Export endpoint'i ile training data'yı al
- Google AI Studio'da fine-tuning için formatla

### 2. Fine-tuned Model Oluştur
- Google AI Studio'da yeni model oluştur
- Training data'yı yükle
- Fine-tuning işlemini başlat

### 3. Yeni Model'i Entegre Et
- Fine-tuned model ID'sini al
- `GEMINI_MODEL_NAME` environment variable'ını güncelle
- Uygulamayı yeniden başlat

## 8. Production Optimizasyonları

### Rate Limiting
```python
# services/llm_service.py'de
generation_config={
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
    "response_mime_type": "application/json"
}
```

### Caching
- Sistem otomatik olarak LLM yanıtlarını cache'liyor
- Cache TTL'leri learning service tarafından optimize ediliyor

### Monitoring
- Performance metrikleri otomatik toplanıyor
- Learning insights düzenli olarak güncelleniyor
- Auto-improvement önerileri üretiliyor

## 9. Troubleshooting

### API Key Hatası
```
Error: API key not found
```
**Çözüm:** `GEMINI_API_KEY` environment variable'ını ayarla

### Rate Limit Hatası
```
Error: Rate limit exceeded
```
**Çözüm:** Request'ler arasında delay ekle veya quota artır

### Model Bulunamadı
```
Error: Model not found
```
**Çözüm:** `GEMINI_MODEL_NAME` değerini kontrol et

## 10. Gelişmiş Özellikler

### Context Window Optimization
- Sistem otomatik olarak conversation history'yi yönetiyor
- Context window'u aşmamak için eski mesajları temizliyor

### Multi-turn Conversations
- Session management ile multi-turn konuşmalar destekleniyor
- Context preservation aktif

### Intent Accuracy Improvement
- Learning service sürekli intent accuracy'yi izliyor
- Düşük performanslı intent'ler için öneriler üretiyor

---

## 🚀 Hızlı Başlangıç

```bash
# 1. API key al ve ayarla
export GEMINI_API_KEY="your-api-key"

# 2. Paketi yükle
pip install google-generativeai

# 3. Test et
python3 test_learning_simple.py

# 4. Uygulamayı başlat
python3 -m app.main

# 5. Learning'i başlat
curl -X POST http://localhost:8000/admin/learning/start
```

**Sistem artık gerçek Gemini 2.5 Pro ile çalışmaya hazır!** 🎉