"""
Database Models - SQLAlchemy ve Pydantic modelleri
Multi-tenant yapı için veritabanı şeması
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

Base = declarative_base()

# SQLAlchemy Models

class Business(Base):
    """İşletme tablosu"""
    __tablename__ = "businesses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    whatsapp = Column(String(20))
    website = Column(String(255))
    
    # Chatbot ayarları
    greeting_message = Column(Text)
    thanks_message = Column(Text)
    error_message = Column(Text)
    
    # Meta veriler (JSON formatında)
    meta_data = Column(JSON)  # telefon, iade, kargo bilgileri
    
    # Durum
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    products = relationship("Product", back_populates="business")
    interactions = relationship("Interaction", back_populates="business")

class Product(Base):
    """Ürün tablosu"""
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    
    # Ürün bilgileri
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    tags = Column(String(500))  # Arama için etiketler
    
    # Fiyat bilgileri
    price = Column(Float)
    original_price = Column(Float)
    discount_percentage = Column(Float)
    
    # Stok bilgileri
    stock_quantity = Column(Integer, default=0)
    
    # Özellikler
    color = Column(String(50))
    size = Column(String(50))
    material = Column(String(100))
    
    # Ek veriler (JSON formatında)
    attributes = Column(JSON)  # Esnek özellikler için
    
    # Durum
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    business = relationship("Business", back_populates="products")

class Interaction(Base):
    """Etkileşim logları tablosu"""
    __tablename__ = "interactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(50), nullable=False)
    session_id = Column(String(100), nullable=False)
    
    # Kullanıcı bilgileri
    user_id = Column(String(100), nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    platform = Column(String(50))  # instagram, whatsapp, web
    
    # Mesaj içerikleri
    user_message = Column(Text, nullable=False)
    llm_response = Column(JSON)  # LLM'den gelen yapısal yanıt
    final_response = Column(Text, nullable=False)
    
    # Performans metrikleri
    response_time_ms = Column(Integer)
    
    # Zaman damgası
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    business = relationship("Business", back_populates="interactions")

class Session(Base):
    """Session bilgileri tablosu (Redis'e ek olarak)"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String(100), nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    
    # Session durumu
    state = Column(String(50), default="active")
    context_data = Column(JSON)
    
    # Zaman bilgileri
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class EscalationTicket(Base):
    """Eskalasyon ticket'ları tablosu"""
    __tablename__ = "escalation_tickets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(50), unique=True, nullable=False)
    session_id = Column(String(100), nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    
    # Eskalasyon bilgileri
    user_message = Column(Text, nullable=False)
    escalation_reason = Column(String(100), nullable=False)  # low_confidence, escalation_intent, etc.
    
    # Ticket durumu
    status = Column(String(50), default="open")  # open, assigned, in_progress, resolved, closed
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # LLM ve hata detayları
    llm_response = Column(JSON)
    error_details = Column(Text)
    conversation_history = Column(JSON)
    
    # Atama ve çözüm
    assigned_agent = Column(String(100))
    resolution = Column(Text)
    
    # Zaman damgaları
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # İlişkiler
    business = relationship("Business")

class EscalationCounter(Base):
    """Eskalasyon sayaçları tablosu (istatistik için)"""
    __tablename__ = "escalation_counters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    reason = Column(String(100), nullable=False)
    count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

class FunctionCallLog(Base):
    """Function call logs tablosu - Gemini function calling logları"""
    __tablename__ = "function_call_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(255), nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    function_name = Column(String(100), nullable=False)
    arguments = Column(JSON, nullable=False)
    response = Column(Text)
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    cached = Column(Boolean, default=False)
    fallback_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    business = relationship("Business")

class FunctionPerformanceStats(Base):
    """Function performance stats tablosu - Günlük performans metrikleri"""
    __tablename__ = "function_performance_stats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    function_name = Column(String(100), nullable=False)
    date = Column(DateTime, nullable=False)  # Date only, no time
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    total_execution_time_ms = Column(Integer, default=0)  # Changed to Integer for consistency
    cache_hits = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    business = relationship("Business")
    
    # Unique constraint
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

# Pydantic Models (API için)

class BusinessCreate(BaseModel):
    """İşletme oluşturma modeli"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    whatsapp: Optional[str] = None
    website: Optional[str] = None
    
    greeting_message: Optional[str] = None
    thanks_message: Optional[str] = None
    error_message: Optional[str] = None
    
    meta_data: Optional[Dict[str, Any]] = None

class BusinessResponse(BaseModel):
    """İşletme yanıt modeli"""
    id: str
    name: str
    description: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    whatsapp: Optional[str]
    website: Optional[str]
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    """Ürün oluşturma modeli"""
    business_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    
    price: Optional[float] = Field(None, ge=0)
    original_price: Optional[float] = Field(None, ge=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    
    stock_quantity: int = Field(0, ge=0)
    
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    
    attributes: Optional[Dict[str, Any]] = None

class ProductResponse(BaseModel):
    """Ürün yanıt modeli"""
    id: str
    business_id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    price: Optional[float]
    stock_quantity: int
    color: Optional[str]
    size: Optional[str]
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class InteractionCreate(BaseModel):
    """Etkileşim oluşturma modeli"""
    request_id: str
    session_id: str
    user_id: str
    business_id: str
    platform: str
    user_message: str
    llm_response: Dict[str, Any]
    final_response: str
    response_time_ms: Optional[int] = None

class InteractionResponse(BaseModel):
    """Etkileşim yanıt modeli"""
    id: str
    request_id: str
    session_id: str
    user_id: str
    business_id: str
    platform: str
    user_message: str
    final_response: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class BusinessStats(BaseModel):
    """İşletme istatistikleri modeli"""
    total_interactions_30d: int
    intent_distribution: List[Dict[str, Any]]
    daily_interactions_7d: List[Dict[str, Any]]

class EscalationTicketCreate(BaseModel):
    """Eskalasyon ticket oluşturma modeli"""
    ticket_id: str
    session_id: str
    business_id: str
    user_message: str
    escalation_reason: str
    status: str = "open"
    priority: str = "medium"
    llm_response: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None

class EscalationTicketResponse(BaseModel):
    """Eskalasyon ticket yanıt modeli"""
    id: str
    ticket_id: str
    session_id: str
    business_id: str
    user_message: str
    escalation_reason: str
    status: str
    priority: str
    assigned_agent: Optional[str]
    resolution: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class EscalationStats(BaseModel):
    """Eskalasyon istatistikleri modeli"""
    total_escalations: int
    reason_distribution: List[Dict[str, Any]]
    status_distribution: List[Dict[str, Any]]
    avg_resolution_hours: Optional[float]

class FunctionCallLogCreate(BaseModel):
    """Function call log oluşturma modeli"""
    session_id: str = Field(..., max_length=255)
    business_id: str
    function_name: str = Field(..., max_length=100)
    arguments: Dict[str, Any]
    response: Optional[str] = None
    execution_time_ms: Optional[int] = Field(None, ge=0)
    success: bool = False
    error_message: Optional[str] = None
    cached: bool = False
    fallback_used: bool = False

class FunctionCallLogResponse(BaseModel):
    """Function call log yanıt modeli"""
    id: str
    session_id: str
    business_id: str
    function_name: str
    arguments: Dict[str, Any]
    response: Optional[str]
    execution_time_ms: Optional[int]
    success: bool
    error_message: Optional[str]
    cached: bool
    fallback_used: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class FunctionPerformanceStatsCreate(BaseModel):
    """Function performance stats oluşturma modeli"""
    business_id: str
    function_name: str = Field(..., max_length=100)
    date: datetime
    total_calls: int = Field(0, ge=0)
    successful_calls: int = Field(0, ge=0)
    total_execution_time_ms: int = Field(0, ge=0)
    cache_hits: int = Field(0, ge=0)
    errors: int = Field(0, ge=0)

class FunctionPerformanceStatsResponse(BaseModel):
    """Function performance stats yanıt modeli"""
    id: str
    business_id: str
    function_name: str
    date: datetime
    total_calls: int
    successful_calls: int
    total_execution_time_ms: int
    cache_hits: int
    errors: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FunctionCallStats(BaseModel):
    """Function call istatistikleri modeli"""
    total_calls: int
    successful_calls: int
    success_rate: float
    average_execution_time_ms: float
    cache_hit_rate: float
    most_used_functions: List[Dict[str, Any]]
    error_distribution: List[Dict[str, Any]]

# Database Schema Creation SQL

DATABASE_SCHEMA = """
-- İşletmeler tablosu
CREATE TABLE IF NOT EXISTS businesses (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    whatsapp VARCHAR(20),
    website VARCHAR(255),
    greeting_message TEXT,
    thanks_message TEXT,
    error_message TEXT,
    meta_data JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ürünler tablosu
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tags VARCHAR(500),
    price DECIMAL(10,2),
    original_price DECIMAL(10,2),
    discount_percentage DECIMAL(5,2),
    stock_quantity INTEGER DEFAULT 0,
    color VARCHAR(50),
    size VARCHAR(50),
    material VARCHAR(100),
    attributes JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Etkileşimler tablosu
CREATE TABLE IF NOT EXISTS interactions (
    id VARCHAR(36) PRIMARY KEY,
    request_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    business_id VARCHAR(36) REFERENCES businesses(id) ON DELETE CASCADE,
    platform VARCHAR(50),
    user_message TEXT NOT NULL,
    llm_response JSONB,
    final_response TEXT NOT NULL,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session'lar tablosu
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    business_id VARCHAR(36) REFERENCES businesses(id) ON DELETE CASCADE,
    state VARCHAR(50) DEFAULT 'active',
    context_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_products_business_id ON products(business_id);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_interactions_business_id ON interactions(business_id);
CREATE INDEX IF NOT EXISTS idx_interactions_session_id ON interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_user_business ON sessions(user_id, business_id);

-- Eskalasyon ticket'ları tablosu
CREATE TABLE IF NOT EXISTS escalation_tickets (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    business_id VARCHAR(36) REFERENCES businesses(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    escalation_reason VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium',
    llm_response JSONB,
    error_details TEXT,
    conversation_history JSONB,
    assigned_agent VARCHAR(100),
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Eskalasyon sayaçları tablosu
CREATE TABLE IF NOT EXISTS escalation_counters (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) REFERENCES businesses(id) ON DELETE CASCADE,
    reason VARCHAR(100) NOT NULL,
    count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, reason)
);

-- İşletmelere webhook URL'leri ekle
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS webhook_urls JSONB;
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS escalation_message TEXT;

-- Eskalasyon indeksleri
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_business_id ON escalation_tickets(business_id);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_status ON escalation_tickets(status);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_priority ON escalation_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_created_at ON escalation_tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_escalation_counters_business_reason ON escalation_counters(business_id, reason);

-- PostgreSQL similarity extension (ürün arama için)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin(name gin_trgm_ops);

-- Function Call Logs Table
CREATE TABLE IF NOT EXISTS function_call_logs (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    business_id VARCHAR(36) REFERENCES businesses(id) ON DELETE CASCADE,
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

-- Function Performance Stats Table
CREATE TABLE IF NOT EXISTS function_performance_stats (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) REFERENCES businesses(id) ON DELETE CASCADE,
    function_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    total_execution_time_ms INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, function_name, date)
);

-- Function calling indexes
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
"""