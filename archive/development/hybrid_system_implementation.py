#!/usr/bin/env python3
"""
3 Katmanlı Hibrit Chatbot Sistemi - Temel Implementation
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import asyncpg
import redis.asyncio as redis
from rapidfuzz import fuzz

@dataclass
class QueryResult:
    response: str
    layer: int  # 1=Cache, 2=Router, 3=Gemini
    confidence: float
    response_time_ms: int
    cost: float = 0.0

class QueryPreprocessor:
    """Sorgu ön işleme sistemi"""
    
    def __init__(self):
        # Türkçe normalizasyon kuralları
        self.turkish_replacements = {
            'geceliği': 'gecelik', 'geceliğin': 'gecelik',
            'pijamayı': 'pijama', 'pijamanın': 'pijama',
            'elbiseyi': 'elbise', 'elbisenin': 'elbise',
            'sabahlığı': 'sabahlık', 'sabahlığın': 'sabahlık'
        }
        
        # Yaygın yazım hataları
        self.typo_corrections = {
            'gecelig': 'gecelik',
            'afirca': 'afrika',
            'afirka': 'afrika',
            'danteli': 'dantelli'
        }
    
    def normalize_query(self, query: str) -> str:
        """Sorguyu normalize et"""
        if not query:
            return ""
        
        # Küçük harfe çevir ve temizle
        normalized = query.lower().strip()
        
        # Türkçe ekleri düzelt
        for old, new in self.turkish_replacements.items():
            normalized = normalized.replace(old, new)
        
        # Yazım hatalarını düzelt
        words = normalized.split()
        corrected_words = []
        for word in words:
            corrected_words.append(self.typo_corrections.get(word, word))
        
        return ' '.join(corrected_words)
    
    def generate_cache_key(self, query: str) -> str:
        """Cache key oluştur"""
        normalized = self.normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def extract_keywords(self, query: str) -> List[str]:
        """Anahtar kelimeleri çıkar"""
        normalized = self.normalize_query(query)
        # Stop words'leri filtrele
        stop_words = {'ve', 'ile', 'için', 'bir', 'bu', 'şu', 'o'}
        words = [w for w in normalized.split() if w not in stop_words and len(w) > 2]
        return words

class CacheLayer:
    """Layer 1: Cache sistemi"""
    
    def __init__(self, redis_client=None, db_pool=None):
        self.redis_client = redis_client
        self.db_pool = db_pool
        self.hit_count = 0
        self.miss_count = 0
    
    async def get_response(self, cache_key: str) -> Optional[str]:
        """Cache'den cevap al"""
        try:
            # Önce Redis'ten dene
            if self.redis_client:
                response = await self.redis_client.get(f"cache:{cache_key}")
                if response:
                    self.hit_count += 1
                    await self._update_hit_count(cache_key)
                    return response.decode()
            
            # Redis yoksa veya bulamazsa PostgreSQL'den dene
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT response FROM cache_entries WHERE cache_key = $1 AND "
                        "created_at + INTERVAL '1 second' * ttl > NOW()",
                        cache_key
                    )
                    if row:
                        self.hit_count += 1
                        await self._update_hit_count(cache_key)
                        return row['response']
            
            self.miss_count += 1
            return None
            
        except Exception as e:
            print(f"Cache error: {e}")
            self.miss_count += 1
            return None
    
    async def set_response(self, cache_key: str, query: str, response: str, ttl: int = 3600):
        """Cache'e cevap kaydet"""
        try:
            # Redis'e kaydet
            if self.redis_client:
                await self.redis_client.setex(f"cache:{cache_key}", ttl, response)
            
            # PostgreSQL'e de kaydet
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """INSERT INTO cache_entries (cache_key, query, response, ttl) 
                           VALUES ($1, $2, $3, $4) 
                           ON CONFLICT (cache_key) DO UPDATE SET 
                           response = $3, last_accessed = NOW()""",
                        cache_key, query, response, ttl
                    )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def _update_hit_count(self, cache_key: str):
        """Hit count'u güncelle"""
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE cache_entries SET hit_count = hit_count + 1, last_accessed = NOW() WHERE cache_key = $1",
                        cache_key
                    )
            except Exception as e:
                print(f"Hit count update error: {e}")
    
    def get_hit_rate(self) -> float:
        """Cache hit rate'i döndür"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0

class RouterLayer:
    """Layer 2: Router sistemi"""
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self.routing_rules = {}
        self.success_count = 0
        self.total_count = 0
    
    async def load_routing_rules(self):
        """Routing kurallarını yükle"""
        if not self.db_pool:
            # Varsayılan kurallar
            self.routing_rules = {
                'telefon': {
                    'keywords': ['telefon', 'phone', 'iletişim', 'numar'],
                    'response': 'Telefon numaramız: 0555 555 55 55',
                    'confidence': 0.95
                },
                'iade': {
                    'keywords': ['iade', 'return', 'geri'],
                    'response': 'İade politikamız: 14 gün içinde iade edilebilir.',
                    'confidence': 0.9
                },
                'kargo': {
                    'keywords': ['kargo', 'teslimat', 'shipping', 'cargo'],
                    'response': 'Kargo bilgilerimiz: Ücretsiz kargo 200 TL üzeri siparişlerde.',
                    'confidence': 0.9
                },
                'site': {
                    'keywords': ['site', 'web', 'website'],
                    'response': 'Web sitemiz: www.butikcemunay.com',
                    'confidence': 0.9
                }
            }
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM router_rules")
                for row in rows:
                    self.routing_rules[row['intent']] = {
                        'keywords': row['keywords'],
                        'response': row['response_template'],
                        'confidence': row['confidence_threshold']
                    }
        except Exception as e:
            print(f"Router rules loading error: {e}")
    
    async def match_keywords(self, keywords: List[str]) -> Optional[Tuple[str, str, float]]:
        """Anahtar kelime eşleştirme"""
        self.total_count += 1
        
        if not self.routing_rules:
            await self.load_routing_rules()
        
        best_match = None
        best_score = 0
        
        for intent, rule in self.routing_rules.items():
            score = 0
            for keyword in keywords:
                for rule_keyword in rule['keywords']:
                    # Exact match
                    if keyword == rule_keyword:
                        score += 1.0
                    # Fuzzy match
                    elif fuzz.ratio(keyword, rule_keyword) > 80:
                        score += 0.8
            
            # Normalize score
            normalized_score = score / len(rule['keywords'])
            
            if normalized_score > best_score and normalized_score >= rule['confidence']:
                best_score = normalized_score
                best_match = (intent, rule['response'], normalized_score)
        
        if best_match:
            self.success_count += 1
            await self._update_usage_stats(best_match[0])
        
        return best_match
    
    async def _update_usage_stats(self, intent: str):
        """Kullanım istatistiklerini güncelle"""
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE router_rules SET usage_count = usage_count + 1 WHERE intent = $1",
                        intent
                    )
            except Exception as e:
                print(f"Usage stats update error: {e}")
    
    def get_success_rate(self) -> float:
        """Router başarı oranı"""
        return self.success_count / self.total_count if self.total_count > 0 else 0.0

class GeminiLayer:
    """Layer 3: Gemini AI sistemi"""
    
    def __init__(self, existing_llm_service):
        self.llm_service = existing_llm_service
        self.api_calls = 0
        self.total_cost = 0.0
    
    async def process_query(self, query: str, session_id: str, business_id: str) -> Dict[str, Any]:
        """Gemini ile sorguyu işle"""
        self.api_calls += 1
        
        try:
            # Mevcut LLM service'i kullan
            result = await self.llm_service.process_message_with_functions(
                prompt=query,
                session_id=session_id,
                isletme_id=business_id
            )
            
            # Maliyet hesapla (yaklaşık)
            estimated_cost = self._estimate_cost(query, result)
            self.total_cost += estimated_cost
            
            return result
            
        except Exception as e:
            print(f"Gemini processing error: {e}")
            return {
                "intent": "error",
                "final_response": "Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin.",
                "confidence": 0.0,
                "method": "error"
            }
    
    def _estimate_cost(self, query: str, result: Dict) -> float:
        """Maliyet tahmini"""
        # Basit tahmin: ~150 input + 100 output token
        input_tokens = len(query.split()) * 1.3  # Rough estimate
        output_tokens = len(result.get("final_response", "")).split() * 1.3
        
        # Gemini 1.5 Flash pricing
        input_cost = (input_tokens / 1000) * 0.000075
        output_cost = (output_tokens / 1000) * 0.0003
        
        return input_cost + output_cost
    
    def get_api_stats(self) -> Dict[str, Any]:
        """API istatistikleri"""
        return {
            "total_calls": self.api_calls,
            "total_cost": self.total_cost,
            "avg_cost_per_call": self.total_cost / self.api_calls if self.api_calls > 0 else 0
        }

class HybridChatbotSystem:
    """3 katmanlı hibrit chatbot sistemi"""
    
    def __init__(self, existing_llm_service, existing_function_coordinator):
        self.preprocessor = QueryPreprocessor()
        self.cache_layer = CacheLayer()
        self.router_layer = RouterLayer()
        self.gemini_layer = GeminiLayer(existing_llm_service)
        self.function_coordinator = existing_function_coordinator
        
        # İstatistikler
        self.layer_stats = {1: 0, 2: 0, 3: 0}
        self.total_queries = 0
    
    async def initialize(self, db_pool=None, redis_client=None):
        """Sistemi initialize et"""
        self.cache_layer.db_pool = db_pool
        self.cache_layer.redis_client = redis_client
        self.router_layer.db_pool = db_pool
        
        await self.router_layer.load_routing_rules()
        print("✅ Hybrid chatbot system initialized")
    
    async def process_query(self, query: str, session_id: str = "default", 
                          business_id: str = "fashion_boutique") -> QueryResult:
        """Ana sorgu işleme fonksiyonu"""
        start_time = time.time()
        self.total_queries += 1
        
        # 1. Ön işleme
        normalized_query = self.preprocessor.normalize_query(query)
        cache_key = self.preprocessor.generate_cache_key(query)
        keywords = self.preprocessor.extract_keywords(query)
        
        # Layer 1: Cache
        cached_response = await self.cache_layer.get_response(cache_key)
        if cached_response:
            self.layer_stats[1] += 1
            response_time = int((time.time() - start_time) * 1000)
            
            await self._log_query(query, 1, cached_response, True, response_time)
            
            return QueryResult(
                response=cached_response,
                layer=1,
                confidence=1.0,
                response_time_ms=response_time,
                cost=0.0
            )
        
        # Layer 2: Router
        router_match = await self.router_layer.match_keywords(keywords)
        if router_match:
            intent, response, confidence = router_match
            self.layer_stats[2] += 1
            response_time = int((time.time() - start_time) * 1000)
            
            # Cache'e kaydet
            await self.cache_layer.set_response(cache_key, query, response)
            await self._log_query(query, 2, response, True, response_time)
            
            return QueryResult(
                response=response,
                layer=2,
                confidence=confidence,
                response_time_ms=response_time,
                cost=0.0
            )
        
        # Layer 3: Gemini AI
        self.layer_stats[3] += 1
        
        try:
            # Gemini ile işle
            gemini_result = await self.gemini_layer.process_query(query, session_id, business_id)
            
            # Function call varsa execute et
            final_response = gemini_result.get("final_response", "")
            
            if gemini_result.get("function_call") and self.function_coordinator:
                function_call = gemini_result["function_call"]
                execution_result = await self.function_coordinator.execute_function_call(
                    function_name=function_call["name"],
                    arguments=function_call["args"],
                    session_id=session_id,
                    business_id=business_id
                )
                
                if execution_result and execution_result.get("success"):
                    final_response = execution_result.get("result", {}).get("response", final_response)
            
            response_time = int((time.time() - start_time) * 1000)
            confidence = gemini_result.get("confidence", 0.8)
            cost = self.gemini_layer._estimate_cost(query, gemini_result)
            
            # Cache'e kaydet (yüksek confidence'lı cevapları)
            if confidence > 0.8:
                await self.cache_layer.set_response(cache_key, query, final_response)
            
            await self._log_query(query, 3, final_response, True, response_time, cost)
            
            return QueryResult(
                response=final_response,
                layer=3,
                confidence=confidence,
                response_time_ms=response_time,
                cost=cost
            )
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_response = "Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin."
            
            await self._log_query(query, 3, error_response, False, response_time)
            
            return QueryResult(
                response=error_response,
                layer=3,
                confidence=0.0,
                response_time_ms=response_time,
                cost=0.0
            )
    
    async def _log_query(self, query: str, layer: int, response: str, success: bool, 
                        response_time: int, cost: float = 0.0):
        """Sorguyu logla"""
        # Basit loglama (production'da database'e kaydedilecek)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "layer": layer,
            "response": response[:100] + "..." if len(response) > 100 else response,
            "success": success,
            "response_time_ms": response_time,
            "cost": cost
        }
        
        print(f"📝 Query Log: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Sistem istatistikleri"""
        total = sum(self.layer_stats.values())
        
        return {
            "total_queries": self.total_queries,
            "layer_distribution": {
                f"layer_{k}": {"count": v, "percentage": (v/total*100) if total > 0 else 0}
                for k, v in self.layer_stats.items()
            },
            "cache_hit_rate": self.cache_layer.get_hit_rate(),
            "router_success_rate": self.router_layer.get_success_rate(),
            "gemini_stats": self.gemini_layer.get_api_stats(),
            "estimated_monthly_cost": self._estimate_monthly_cost()
        }
    
    def _estimate_monthly_cost(self) -> float:
        """Aylık maliyet tahmini"""
        if self.total_queries == 0:
            return 0.0
        
        # Mevcut layer 3 oranına göre tahmin
        layer3_ratio = self.layer_stats[3] / self.total_queries
        avg_cost_per_layer3 = self.gemini_layer.total_cost / max(self.layer_stats[3], 1)
        
        # 100K sorgu için tahmin
        monthly_queries = 100000
        monthly_layer3_queries = monthly_queries * layer3_ratio
        monthly_cost = monthly_layer3_queries * avg_cost_per_layer3
        
        return monthly_cost

# Demo ve test fonksiyonu
async def demo_hybrid_system():
    """Hibrit sistemi demo et"""
    
    # Mevcut sistemlerden mock'lar
    class MockLLMService:
        async def process_message_with_functions(self, prompt, session_id, isletme_id):
            return {
                "intent": "product_query",
                "final_response": f"Mock response for: {prompt}",
                "confidence": 0.85,
                "method": "function_calling"
            }
    
    class MockFunctionCoordinator:
        async def execute_function_call(self, function_name, arguments, session_id, business_id):
            return {
                "success": True,
                "result": {"response": f"Mock function result for {arguments}"}
            }
    
    # Sistemi initialize et
    system = HybridChatbotSystem(MockLLMService(), MockFunctionCoordinator())
    await system.initialize()
    
    # Test sorguları
    test_queries = [
        "telefon numaranız nedir?",  # Layer 2'de yakalanmalı
        "telefon numaranız nedir?",  # Layer 1'de cache'den gelmeli
        "iade nasıl yapılır?",       # Layer 2'de yakalanmalı
        "afrika gecelik fiyatı",     # Layer 3'e gitmeli
        "hamile pijama var mı",      # Layer 3'e gitmeli
        "kargo ücreti ne kadar",     # Layer 2'de yakalanmalı
    ]
    
    print("🚀 Hibrit Sistem Demo Başlıyor...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: '{query}'")
        result = await system.process_query(query)
        
        print(f"   Layer: {result.layer}")
        print(f"   Response: {result.response[:80]}...")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Time: {result.response_time_ms}ms")
        print(f"   Cost: ${result.cost:.6f}")
        print()
    
    # Sistem istatistikleri
    stats = system.get_system_stats()
    print("📊 Sistem İstatistikleri:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(demo_hybrid_system())