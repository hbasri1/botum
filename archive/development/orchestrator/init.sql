-- Multi-Tenant Chatbot Database Schema
-- PostgreSQL initialization script

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- İşletmeler tablosu
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    whatsapp VARCHAR(20),
    website VARCHAR(255),
    
    -- Chatbot mesajları
    greeting_message TEXT DEFAULT 'Merhaba! Size nasıl yardımcı olabilirim?',
    thanks_message TEXT DEFAULT 'Rica ederim! Başka bir sorunuz var mı?',
    error_message TEXT DEFAULT 'Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin.',
    
    -- Meta veriler (JSON)
    meta_data JSONB DEFAULT '{}',
    
    -- Durum
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ürünler tablosu
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    
    -- Ürün bilgileri
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tags VARCHAR(500),
    
    -- Fiyat bilgileri
    price DECIMAL(10,2),
    original_price DECIMAL(10,2),
    discount_percentage DECIMAL(5,2),
    
    -- Stok
    stock_quantity INTEGER DEFAULT 0,
    
    -- Özellikler
    color VARCHAR(50),
    size VARCHAR(50),
    material VARCHAR(100),
    
    -- Ek özellikler (JSON)
    attributes JSONB DEFAULT '{}',
    
    -- Durum
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Etkileşimler tablosu
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    
    -- Kullanıcı bilgileri
    user_id VARCHAR(100) NOT NULL,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    platform VARCHAR(50) DEFAULT 'unknown',
    
    -- Mesajlar
    user_message TEXT NOT NULL,
    llm_response JSONB,
    final_response TEXT NOT NULL,
    
    -- Performans
    response_time_ms INTEGER,
    
    -- Zaman
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session'lar tablosu
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    
    -- Durum
    state VARCHAR(50) DEFAULT 'active',
    context_data JSONB DEFAULT '{}',
    
    -- Zaman
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Eskalasyon ticket'ları tablosu
CREATE TABLE IF NOT EXISTS escalation_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    
    -- Eskalasyon bilgileri
    user_message TEXT NOT NULL,
    escalation_reason VARCHAR(100) NOT NULL,
    
    -- Ticket durumu
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium',
    
    -- Detaylar
    llm_response JSONB,
    error_details TEXT,
    conversation_history JSONB DEFAULT '[]',
    
    -- Atama ve çözüm
    assigned_agent VARCHAR(100),
    resolution TEXT,
    
    -- Zaman damgaları
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Eskalasyon sayaçları tablosu
CREATE TABLE IF NOT EXISTS escalation_counters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    reason VARCHAR(100) NOT NULL,
    count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, reason)
);

-- İşletmelere yeni alanlar ekle
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS webhook_urls JSONB DEFAULT '[]';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS escalation_message TEXT;

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_businesses_active ON businesses(active);
CREATE INDEX IF NOT EXISTS idx_products_business_id ON products(business_id);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(active);
CREATE INDEX IF NOT EXISTS idx_interactions_business_id ON interactions(business_id);
CREATE INDEX IF NOT EXISTS idx_interactions_session_id ON interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_business ON sessions(user_id, business_id);

-- Eskalasyon indeksleri
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_business_id ON escalation_tickets(business_id);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_session_id ON escalation_tickets(session_id);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_status ON escalation_tickets(status);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_priority ON escalation_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_created_at ON escalation_tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_reason ON escalation_tickets(escalation_reason);
CREATE INDEX IF NOT EXISTS idx_escalation_counters_business_reason ON escalation_counters(business_id, reason);

-- Function calling indeksleri
CREATE INDEX IF NOT EXISTS idx_function_call_logs_session ON function_call_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_business ON function_call_logs(business_id);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_function ON function_call_logs(function_name);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_created ON function_call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_success ON function_call_logs(success);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_business_function ON function_call_logs(business_id, function_name);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_business_created ON function_call_logs(business_id, created_at);

CREATE INDEX IF NOT EXISTS idx_function_stats_business_date ON function_performance_stats(business_id, date);
CREATE INDEX IF NOT EXISTS idx_function_stats_function ON function_performance_stats(function_name);
CREATE INDEX IF NOT EXISTS idx_function_stats_date ON function_performance_stats(date);
CREATE INDEX IF NOT EXISTS idx_function_stats_business_function ON function_performance_stats(business_id, function_name);

-- Trigram indeksleri (fuzzy search için)
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_description_trgm ON products USING gin(description gin_trgm_ops);

-- Function Call Logs Table (Gemini function calling için)
CREATE TABLE IF NOT EXISTS function_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    function_name VARCHAR(100) NOT NULL,
    arguments JSONB NOT NULL,
    response TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    cached BOOLEAN DEFAULT false,
    fallback_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function Performance Stats Table (Günlük performans metrikleri)
CREATE TABLE IF NOT EXISTS function_performance_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    function_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    total_execution_time_ms BIGINT DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, function_name, date)
);

-- Trigger fonksiyonu (updated_at için)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger'lar
CREATE TRIGGER update_businesses_updated_at 
    BEFORE UPDATE ON businesses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_escalation_tickets_updated_at 
    BEFORE UPDATE ON escalation_tickets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_function_performance_stats_updated_at 
    BEFORE UPDATE ON function_performance_stats 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Örnek veri (test için)
INSERT INTO businesses (id, name, description, phone, whatsapp, meta_data) VALUES 
(
    'test-business-1',
    'Test Butik',
    'Test amaçlı örnek işletme',
    '0555 555 55 55',
    '0555 555 55 55',
    '{
        "telefon": "0555 555 55 55",
        "iade": "İade 14 gün içinde yapılabilir",
        "kargo": "Kargo 2-3 iş günü içinde gönderilir",
        "adres": "Test Mahallesi, Test Sokak No:1"
    }'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO products (business_id, name, description, category, price, stock_quantity, color) VALUES 
(
    'test-business-1',
    'Test Gecelik',
    'Test amaçlı örnek gecelik',
    'gecelik',
    299.99,
    10,
    'siyah'
),
(
    'test-business-1',
    'Test Pijama Takımı',
    'Test amaçlı örnek pijama takımı',
    'pijama',
    199.99,
    5,
    'mavi'
) ON CONFLICT DO NOTHING;