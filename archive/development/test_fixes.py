#!/usr/bin/env python3
"""
Test script for the fixes we made
"""

import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'orchestrator'))

import requests
import json

# Test için local server kullan
BASE_URL = "http://localhost:8000"

def make_request(question):
    """API'ye request gönder"""
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"question": question},
            timeout=10
        )
        return response
    except requests.exceptions.ConnectionError:
        print("❌ Server çalışmıyor. Önce 'python main.py' ile başlatın.")
        return None
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
        return None

def test_intent_detection():
    """Test intent detection improvements"""
    print("🧪 Testing Intent Detection Improvements...")
    
    test_cases = [
        {
            "question": "iade var mı acaba",
            "expected_intent": "meta_query",
            "description": "İade sorgusu - basit"
        },
        {
            "question": "iade yapabilir miyim",
            "expected_intent": "meta_query", 
            "description": "İade sorgusu - karmaşık"
        },
        {
            "question": "telefon numaranız nedir",
            "expected_intent": "meta_query",
            "description": "Telefon sorgusu"
        },
        {
            "question": "tamam iyi günler",
            "expected_intent": "conversation_end",
            "description": "Konuşma bitirme"
        },
        {
            "question": "yok teşekkürler",
            "expected_intent": "conversation_end", 
            "description": "Konuşma bitirme - 2"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Soru: '{test_case['question']}'")
        
        response = make_request(test_case["question"])
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"   ✅ Cevap: {data['answer'][:100]}...")
            print(f"   📊 Method: {data.get('method', 'unknown')}")
            print(f"   🎯 Confidence: {data.get('confidence', 0)}")
        elif response:
            print(f"   ❌ HTTP Error: {response.status_code}")
        else:
            return

def test_product_search():
    """Test improved product search"""
    print("\n🔍 Testing Product Search Improvements...")
    
    test_cases = [
        {
            "question": "dantelli hamile gecelik",
            "description": "Birleşik ürün adı"
        },
        {
            "question": "afrika geceliği fiyatı",
            "description": "Ürün + fiyat sorgusu"
        },
        {
            "question": "hamile pijama var mı",
            "description": "Hamile ürün stok sorgusu"
        },
        {
            "question": "gecelik fiyatları",
            "description": "Genel kategori sorgusu"
        },
        {
            "question": "lohusa takımı",
            "description": "Lohusa ürün sorgusu"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Soru: '{test_case['question']}'")
        
        response = make_request(test_case["question"])
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"   ✅ Cevap: {data['answer'][:150]}...")
            print(f"   📊 Method: {data.get('method', 'unknown')}")
            print(f"   ⏱️ Time: {data.get('execution_time_ms', 0)}ms")
        elif response:
            print(f"   ❌ HTTP Error: {response.status_code}")
        else:
            return

def test_conversation_flow():
    """Test conversation flow improvements"""
    print("\n💬 Testing Conversation Flow...")
    
    conversation = [
        "merhaba",
        "afrika gecelik fiyatı ne kadar",
        "teşekkürler",
        "tamam iyi günler"
    ]
    
    for i, message in enumerate(conversation, 1):
        print(f"\n{i}. Kullanıcı: '{message}'")
        
        response = make_request(message)
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"   🤖 Bot: {data['answer']}")
            print(f"   📊 Method: {data.get('method', 'unknown')}")
        elif response:
            print(f"   ❌ HTTP Error: {response.status_code}")
        else:
            return

if __name__ == "__main__":
    print("🚀 Testing System Fixes...")
    print("=" * 50)
    
    try:
        test_intent_detection()
        test_product_search()
        test_conversation_flow()
        
        print("\n" + "=" * 50)
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()