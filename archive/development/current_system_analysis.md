# Mevcut Chatbot Sistemi - Detaylı Analiz

## 🏗️ Sistem Mimarisi

### Mevcut Akış
```
User Query → web_bot.py → LLMService → Function Coordinator → Product Handler → Database → Response
```

### Dosya Yapısı
```
├── web_bot.py (Port 8003 - Ana interface)
├── main.py (Port 8000 - Eski sistem)
├── orchestrator/
│   ├── services/
│   │   ├── llm_service.py (Gemini 1.5 Flash)
│   │   ├── function_execution_coordinator.py
│   │   ├── product_function_handler.py
│   │   ├── general_info_function_handler.py
│   │   ├── database_service.py (692 ürün, fuzzy search)
│   │   └── function_cache_manager.py (in-memory)
│   └── models/database_models.py
├── data/
│   ├── products.json (692 ürün)
│   └── butik_meta.json (işletme bilgileri)
```

## 🔍 Mevcut Sistem Analizi

### ✅ Çalışan Özellikler
1. **Function Calling**: Gemini 1.5 Flash ile intent detection
2. **Ürün Arama**: 692 ürün içinde fuzzy matching (rapidfuzz)
3. **İşletme Bilgileri**: Telefon, iade, kargo, site bilgileri
4. **Türkçe Desteği**: Temel normalizasyon (_extract_product_name)
5. **Cache Sistemi**: In-memory function cache
6. **Performance**: 2,086 RPS, 13.7ms ortalama

### ❌ Mevcut Sorunlar
1. **Search Accuracy**: %70-80 (fuzzy matching sınırları)
2. **Semantic Understanding**: Yok ("kırmızı gecelik" bulamıyor)
3. **Intent Gaps**: Bazı sorgular INTENT_DETECTION'a düşüyor
4. **Normalization**: Türkçe ekleri tam handle edilmiyor
5. **Learning**: Sistem kendini geliştiremiyor
6. **Cost Tracking**: Gerçek maliyet takibi yok

### 📊 Test Sonuçları (Son Test)
- **Toplam Test**: 41
- **Başarılı**: 35 (%85)
- **Başarısız**: 6 (%15)
- **Method Dağılımı**: 
  - Function Calling: 28 ✅
  - Direct Response: 6 ✅
  - Intent Detection: 7 (bazıları başarısız)

### 🔧 Başarısız Test Örnekleri
- "afrika geceliği" → Yanlış ürün döndürüyor
- "hangi ürünler var" → Anlayamıyor
- "stokta ne var" → Anlayamıyor

## 💰 Maliyet Durumu
- **Gemini 1.5 Flash**: $41.25/ay (1M sorgu)
- **Cache ile %50 tasarruf**: $20.62/ay
- **Mevcut cache hit rate**: Bilinmiyor (tracking yok)

## 🎯 MVP İçin Kritik İhtiyaçlar

### 1. Acil Düzeltmeler (1-2 gün)
- Türkçe normalizasyon güçlendirme
- Search accuracy artırma
- Intent detection boşluklarını kapatma

### 2. Semantic Search (2-3 gün)
- Google Embedding API
- pgvector entegrasyonu
- Ürün embeddings

### 3. Monitoring (1 gün)
- Gerçek maliyet takibi
- Performance monitoring
- Error tracking

## 🚀 MVP Hedefleri
- **Accuracy**: %70 → %90+
- **Coverage**: Tüm ürün sorguları handle edilsin
- **Response Time**: <500ms (mevcut: 13.7ms)
- **Cost**: <$25/ay (100K sorgu)
- **Reliability**: %99+ uptime