#!/bin/bash

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
