#!/usr/bin/env python3
"""
Function Calling Setup Script
Gemini Function Calling entegrasyonu için gerekli setup'ları yapar
"""

import os
import sys
import subprocess
import asyncio

def install_requirements():
    """Gerekli paketleri yükle"""
    print("📦 Installing required packages...")
    
    requirements = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "asyncpg",
        "redis",
        "google-generativeai",
        "google-auth",
        "pytest",
        "pytest-asyncio"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")

def setup_environment():
    """Environment variables setup"""
    print("\n🔧 Setting up environment...")
    
    env_template = """
# Gemini Function Calling Configuration
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost/chatbot_db
REDIS_URL=redis://localhost:6379/1

# Function Calling Settings
ENABLE_FUNCTION_CALLING=true
FUNCTION_CALLING_MODEL=gemini-1.5-flash-latest
FUNCTION_CALLING_TEMPERATURE=0.1

# Cache Settings
DEFAULT_CACHE_TTL=300
PRODUCT_INFO_TTL=300
GENERAL_INFO_TTL=3600

# Security Settings
RATE_LIMIT_BASIC=30
RATE_LIMIT_PREMIUM=100
RATE_LIMIT_ENTERPRISE=500
"""
    
    with open('.env', 'w') as f:
        f.write(env_template)
    
    print("✅ .env file created")
    print("⚠️  Please update the API keys and database URLs in .env file")

def create_database_setup():
    """Database setup script oluştur"""
    print("\n🗄️ Creating database setup...")
    
    db_setup = """
-- Function Calling Database Setup
-- Run this script in your PostgreSQL database

-- Create function_call_logs table
CREATE TABLE IF NOT EXISTS function_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    business_id VARCHAR(255) NOT NULL,
    function_name VARCHAR(100) NOT NULL,
    arguments JSONB,
    response TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    cached BOOLEAN DEFAULT false,
    fallback_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create function_performance_stats table
CREATE TABLE IF NOT EXISTS function_performance_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id VARCHAR(255) NOT NULL,
    function_name VARCHAR(100) NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    avg_execution_time_ms FLOAT DEFAULT 0,
    cache_hit_rate FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_function_logs_business_id ON function_call_logs(business_id);
CREATE INDEX IF NOT EXISTS idx_function_logs_session_id ON function_call_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_function_logs_function_name ON function_call_logs(function_name);
CREATE INDEX IF NOT EXISTS idx_function_logs_created_at ON function_call_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_function_stats_business_id ON function_performance_stats(business_id);
CREATE INDEX IF NOT EXISTS idx_function_stats_function_name ON function_performance_stats(function_name);
CREATE INDEX IF NOT EXISTS idx_function_stats_date ON function_performance_stats(date);

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON function_call_logs TO your_app_user;
-- GRANT ALL PRIVILEGES ON function_performance_stats TO your_app_user;

COMMIT;
"""
    
    with open('setup_database.sql', 'w') as f:
        f.write(db_setup)
    
    print("✅ setup_database.sql created")

def create_docker_compose():
    """Docker compose file oluştur"""
    print("\n🐳 Creating Docker Compose setup...")
    
    docker_compose = """
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: chatbot_db
      POSTGRES_USER: chatbot_user
      POSTGRES_PASSWORD: chatbot_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./setup_database.sql:/docker-entrypoint-initdb.d/setup_database.sql

  chatbot:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=postgresql://chatbot_user:chatbot_password@postgres/chatbot_db
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - .:/app
    command: python orchestrator/app/main.py

volumes:
  redis_data:
  postgres_data:
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    
    print("✅ docker-compose.yml created")

def create_dockerfile():
    """Dockerfile oluştur"""
    print("\n🐳 Creating Dockerfile...")
    
    dockerfile = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "orchestrator/app/main.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    # Create requirements.txt
    requirements_txt = """
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
asyncpg==0.29.0
redis==5.0.1
google-generativeai==0.3.2
google-auth==2.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_txt)
    
    print("✅ Dockerfile and requirements.txt created")

def create_run_script():
    """Run script oluştur"""
    print("\n🚀 Creating run script...")
    
    run_script = """#!/bin/bash

echo "🚀 Starting Gemini Function Calling Chatbot"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run setup_function_calling.py first"
    exit 1
fi

# Check if database is running
echo "🔍 Checking database connection..."
python -c "
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def check_db():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.close()
        print('✅ Database connection successful')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

if not asyncio.run(check_db()):
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "💡 Tip: Start database with: docker-compose up -d postgres redis"
    exit 1
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
python -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()

try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "💡 Tip: Start Redis with: docker-compose up -d redis"
    exit 1
fi

# Run tests
echo "🧪 Running function calling tests..."
python test_function_calling.py

# Start the application
echo "🚀 Starting the application..."
python orchestrator/app/main.py
"""
    
    with open('run_chatbot.sh', 'w') as f:
        f.write(run_script)
    
    # Make executable
    os.chmod('run_chatbot.sh', 0o755)
    
    print("✅ run_chatbot.sh created")

def main():
    """Ana setup fonksiyonu"""
    print("🔧 Gemini Function Calling Setup")
    print("=" * 40)
    
    install_requirements()
    setup_environment()
    create_database_setup()
    create_docker_compose()
    create_dockerfile()
    create_run_script()
    
    print("\n" + "=" * 40)
    print("✅ Setup completed!")
    print("\n📋 Next Steps:")
    print("1. Update .env file with your API keys")
    print("2. Start services: docker-compose up -d")
    print("3. Run database setup: psql -f setup_database.sql")
    print("4. Test the setup: python test_function_calling.py")
    print("5. Start the bot: ./run_chatbot.sh")
    
    print("\n🔗 Useful Commands:")
    print("- Test function calling: python test_function_calling.py")
    print("- Start services: docker-compose up -d")
    print("- View logs: docker-compose logs -f")
    print("- Stop services: docker-compose down")

if __name__ == "__main__":
    main()