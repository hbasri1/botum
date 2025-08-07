#!/usr/bin/env python3
"""
MVP Quick Fixes - Hızlı ve etkili çözümler
"""

import asyncio
import json
from typing import Dict, List, Any, Optional

class MVPQuickFixes:
    """MVP için hızlı çözümler"""
    
    def __init__(self):
        self.conversation_context = {}  # session_id -> context
        self.enhanced_keywords = self._load_enhanced_keywords()
    
    def _load_enhanced_keywords(self) -> Dict[str, List[str]]:
        """Gelişmiş keyword mapping"""
        return {
            # Dekolte terimleri
            "dekolte": ["dekolteli", "dekolte", "açık", "göğüs", "sırt"],
            "göğüs_dekolte": ["göğüs dekolteli", "göğüs açık", "v yaka"],
            "sırt_dekolte": ["sırt dekolteli", "sırt açık", "açık sırt"],
            
            # Takım terimleri
            "takım": ["takım", "takımı", "set", "komple", "alt üst"],
            "şort_takım": ["şort takım", "şort takımı", "kısa takım"],
            
            # Stil terimleri
            "brode": ["brode", "brodeli", "işlemeli", "nakışlı"],
            "dantelli": ["dantelli", "dantel", "güpürlü"],
            
            # Renk terimleri
            "afrika": ["afrika", "etnik", "desenli", "tribal"],
        }
    
    def enhance_search_query(self, query: str) -> str:
        """Query'yi geliştirilmiş keywords ile zenginleştir"""
        enhanced_query = query.lower()
        
        # Keyword expansion
        for main_term, synonyms in self.enhanced_keywords.items():
            for synonym in synonyms:
                if synonym in enhanced_query:
                    # Ana terimi de ekle
                    if main_term not in enhanced_query:
                        enhanced_query += f" {main_term}"
        
        return enhanced_query
    
    def store_conversation_context(self, session_id: str, product_name: str, query_type: str):
        """Basit conversation context storage"""
        self.conversation_context[session_id] = {
            "last_product": product_name,
            "last_query_type": query_type,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    def get_conversation_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Conversation context'i al"""
        context = self.conversation_context.get(session_id)
        if context:
            # 5 dakika timeout
            if asyncio.get_event_loop().time() - context["timestamp"] < 300:
                return context
            else:
                # Timeout olmuş, temizle
                del self.conversation_context[session_id]
        return None
    
    def resolve_contextual_query(self, query: str, session_id: str) -> Optional[str]:
        """Contextual query'leri çöz"""
        query_lower = query.lower().strip()
        
        # Fiyat soruları
        if any(word in query_lower for word in ["fiyat", "kaç para", "ne kadar", "price"]):
            context = self.get_conversation_context(session_id)
            if context and context.get("last_product"):
                return context["last_product"]
        
        # Stok soruları
        if any(word in query_lower for word in ["stok", "var mı", "mevcut"]):
            context = self.get_conversation_context(session_id)
            if context and context.get("last_product"):
                return context["last_product"]
        
        return None
    
    def calculate_enhanced_similarity(self, query: str, product_name: str) -> float:
        """Gelişmiş similarity hesaplama"""
        from rapidfuzz import fuzz
        
        # Temel similarity
        base_score = fuzz.token_set_ratio(query.lower(), product_name.lower())
        
        # Keyword bonusları
        bonus = 0
        query_words = query.lower().split()
        product_words = product_name.lower().split()
        
        # Exact keyword matches
        for word in query_words:
            if word in product_words:
                bonus += 10
        
        # Özel keyword bonusları
        if "dekolte" in query.lower():
            if "dekolteli" in product_name.lower():
                bonus += 20
        
        if "göğüs" in query.lower() and "sırt" in query.lower():
            if "göğüs" in product_name.lower() and "sırt" in product_name.lower():
                bonus += 30
        
        if "şort" in query.lower():
            if "şort" in product_name.lower():
                bonus += 25
        
        if "takım" in query.lower():
            if "takım" in product_name.lower():
                bonus += 15
        
        return min(100, base_score + bonus)

# Test fonksiyonu
async def test_mvp_fixes():
    """MVP fixes'i test et"""
    
    print("🚀 MVP Quick Fixes Test")
    print("=" * 30)
    
    mvp = MVPQuickFixes()
    
    # Test 1: Enhanced search query
    test_query = "göğüs ve sırt dekolteli takım"
    enhanced = mvp.enhance_search_query(test_query)
    print(f"Original: {test_query}")
    print(f"Enhanced: {enhanced}")
    
    # Test 2: Similarity calculation
    product_name = "Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı"
    similarity = mvp.calculate_enhanced_similarity(test_query, product_name)
    print(f"Similarity: {similarity}")
    
    # Test 3: Context management
    session_id = "test_session"
    mvp.store_conversation_context(session_id, "Afrika Gecelik", "stok")
    
    contextual_query = "fiyatı nedir"
    resolved = mvp.resolve_contextual_query(contextual_query, session_id)
    print(f"Contextual query: {contextual_query}")
    print(f"Resolved to: {resolved}")

if __name__ == "__main__":
    asyncio.run(test_mvp_fixes())