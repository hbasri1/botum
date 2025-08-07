#!/usr/bin/env python3
"""
Gemini Function Calling Bot Starter
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Ana başlatma fonksiyonu"""
    print("🤖 Gemini Function Calling Bot")
    print("=" * 40)
    print("1. 🌐 Web Interface (Önerilen)")
    print("2. 🧪 Console Test")
    print("3. 📊 System Health Check")
    print("=" * 40)
    
    choice = input("Seçiminizi yapın (1-3): ").strip()
    
    if choice == "1":
        start_web_interface()
    elif choice == "2":
        start_console_test()
    elif choice == "3":
        start_health_check()
    else:
        print("❌ Geçersiz seçim!")
        main()

def start_web_interface():
    """Web interface'i başlat"""
    print("\n🌐 Web Interface başlatılıyor...")
    print("🔗 URL: http://localhost:8001")
    print("📖 API Docs: http://localhost:8001/docs")
    print("🔍 Health: http://localhost:8001/health")
    print("\n💡 Tarayıcınızda http://localhost:8001 adresini açın")
    print("⏹️  Durdurmak için Ctrl+C")
    
    os.system("python3 web_bot.py")

def start_console_test():
    """Console test'i başlat"""
    print("\n🧪 Console Test başlatılıyor...")
    os.system("python3 test_function_calling.py")

def start_health_check():
    """System health check"""
    print("\n🔍 System Health Check...")
    
    try:
        from orchestrator.services.llm_service import LLMService
        
        # LLM Service test
        llm_service = LLMService(enable_function_calling=True)
        print("✅ LLM Service: OK")
        
        # Function calling test
        async def test_function_calling():
            result = await llm_service.process_message_with_functions(
                "test", "health_check", "test_business"
            )
            return result is not None
        
        if asyncio.run(test_function_calling()):
            print("✅ Function Calling: OK")
        else:
            print("❌ Function Calling: FAILED")
        
        print("✅ System Health: GOOD")
        
    except Exception as e:
        print(f"❌ System Health: ERROR - {str(e)}")

if __name__ == "__main__":
    main()