#!/usr/bin/env python3
"""
Migration Script: Mevcut sistemden yeni orkestratör yapısına geçiş
"""

import json
import asyncio
import asyncpg
from datetime import datetime

# Mevcut sistem verilerini yeni yapıya migrate et

async def migrate_existing_data():
    """Mevcut verileri yeni veritabanı yapısına migrate et"""
    
    # Mevcut ürün verilerini oku
    with open("data/products.json", "r", encoding="utf-8") as f:
        products = json.load(f)
    
    with open("data/butik_meta.json", "r", encoding="utf-8") as f:
        meta_data = json.load(f)
    
    # Veritabanı bağlantısı
    conn = await asyncpg.connect("postgresql://chatbot_user:chatbot_password@localhost/chatbot_db")
    
    try:
        # Test işletmesi oluştur (mevcut sistem için)
        business_id = "cemunay-butik"
        
        await conn.execute("""
            INSERT INTO businesses (id, name, description, phone, whatsapp, meta_data, 
                                  greeting_message, thanks_message, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id) DO UPDATE SET
                meta_data = EXCLUDED.meta_data,
                updated_at = CURRENT_TIMESTAMP
        """, 
        business_id,
        "Butik Cemünay",
        "Kadın giyim ve iç giyim mağazası",
        meta_data.get("phone", "0555 555 55 55"),
        meta_data.get("phone", "0555 555 55 55"),
        json.dumps(meta_data),
        "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?",
        "Rica ederim! Başka sorunuz var mı?",
        "Üzgünüm, şu anda yanıt veremiyorum. Lütfen tekrar deneyin."
        )
        
        print(f"✅ Business created: {business_id}")
        
        # Ürünleri migrate et
        migrated_count = 0
        
        for product in products:
            try:
                await conn.execute("""
                    INSERT INTO products (business_id, name, description, category, 
                                        price, original_price, discount_percentage,
                                        stock_quantity, color, size, attributes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT DO NOTHING
                """,
                business_id,
                product.get("name", ""),
                product.get("description", ""),
                product.get("category", "gecelik"),  # Default kategori
                float(product.get("final_price", 0)) if product.get("final_price") else None,
                float(product.get("price", 0)) if product.get("price") else None,
                float(product.get("discount", 0)) if product.get("discount") else None,
                int(product.get("stock", 0)) if product.get("stock") else 0,
                product.get("color", ""),
                product.get("size", ""),
                json.dumps({
                    "code": product.get("code", ""),
                    "original_data": product
                })
                )
                
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Product migration error: {product.get('name', 'Unknown')} - {str(e)}")
        
        print(f"✅ Products migrated: {migrated_count}/{len(products)}")
        
        # İstatistikleri göster
        business_count = await conn.fetchval("SELECT COUNT(*) FROM businesses")
        product_count = await conn.fetchval("SELECT COUNT(*) FROM products")
        
        print(f"\n📊 Migration Summary:")
        print(f"   Businesses: {business_count}")
        print(f"   Products: {product_count}")
        print(f"   Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        
    finally:
        await conn.close()

async def create_test_interactions():
    """Test etkileşimleri oluştur"""
    
    conn = await asyncpg.connect("postgresql://chatbot_user:chatbot_password@localhost/chatbot_db")
    
    try:
        test_interactions = [
            {
                "user_message": "merhaba",
                "intent": "greeting",
                "final_response": "Merhaba! Butik Cemünay'a hoş geldiniz. Size nasıl yardımcı olabilirim?"
            },
            {
                "user_message": "afrika gecelik ne kadar",
                "intent": "product_query",
                "final_response": "Afrika Etnik Baskılı Dantelli Gecelik\nFiyat: 565.44 TL"
            },
            {
                "user_message": "telefon numarası",
                "intent": "meta_query",
                "final_response": "Telefon: 0555 555 55 55"
            }
        ]
        
        for i, interaction in enumerate(test_interactions):
            await conn.execute("""
                INSERT INTO interactions (request_id, session_id, user_id, business_id,
                                        platform, user_message, llm_response, final_response)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            f"test-req-{i+1}",
            f"test-session-{i+1}",
            "test-user",
            "cemunay-butik",
            "test",
            interaction["user_message"],
            json.dumps({
                "intent": interaction["intent"],
                "session_id": f"test-session-{i+1}",
                "isletme_id": "cemunay-butik",
                "confidence": 0.95
            }),
            interaction["final_response"]
            )
        
        print(f"✅ Test interactions created: {len(test_interactions)}")
        
    except Exception as e:
        print(f"❌ Test interaction creation failed: {str(e)}")
        
    finally:
        await conn.close()

def create_env_file():
    """Yeni sistem için .env dosyası oluştur"""
    
    env_content = """# Multi-Tenant Chatbot Orchestrator Environment Variables

# Database
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost/chatbot_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Google Cloud / Vertex AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL_NAME=your-fine-tuned-model
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=true

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Cache Settings
CACHE_DEFAULT_TTL=3600
CACHE_FAQ_TTL=86400

# Session Settings
SESSION_TTL=86400
SESSION_CLEANUP_INTERVAL=3600

# LLM Settings
LLM_MAX_RETRIES=3
LLM_TIMEOUT=30
LLM_TEMPERATURE=0.1

# Security (opsiyonel)
# API_KEY=your-secret-api-key
ALLOWED_ORIGINS=["*"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
"""
    
    with open("orchestrator/.env", "w") as f:
        f.write(env_content)
    
    print("✅ .env file created")

def create_startup_script():
    """Başlangıç scripti oluştur"""
    
    script_content = """#!/bin/bash
# Multi-Tenant Chatbot Orchestrator Startup Script

echo "🚀 Starting Multi-Tenant Chatbot Orchestrator..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "📦 Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec postgres psql -U chatbot_user -d chatbot_db -f /docker-entrypoint-initdb.d/init.sql

# Start the orchestrator
echo "🤖 Starting Chatbot Orchestrator..."
python run.py

echo "✅ Orchestrator started successfully!"
echo "📡 API available at: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health"
"""
    
    with open("orchestrator/start.sh", "w") as f:
        f.write(script_content)
    
    # Make executable
    import os
    os.chmod("orchestrator/start.sh", 0o755)
    
    print("✅ Startup script created")

async def main():
    """Ana migration fonksiyonu"""
    
    print("🔄 Starting migration to Multi-Tenant Orchestrator...")
    print("=" * 60)
    
    # 1. Veritabanı verilerini migrate et
    print("\n1️⃣ Migrating existing data...")
    await migrate_existing_data()
    
    # 2. Test etkileşimleri oluştur
    print("\n2️⃣ Creating test interactions...")
    await create_test_interactions()
    
    # 3. Konfigürasyon dosyaları oluştur
    print("\n3️⃣ Creating configuration files...")
    create_env_file()
    create_startup_script()
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("\n📋 Next Steps:")
    print("   1. cd orchestrator/")
    print("   2. Update .env file with your actual credentials")
    print("   3. ./start.sh")
    print("   4. Test: curl http://localhost:8000/health")
    print("\n🔗 Webhook URL: http://localhost:8000/webhook")

if __name__ == "__main__":
    asyncio.run(main())