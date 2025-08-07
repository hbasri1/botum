#!/usr/bin/env python3
"""
Smart Cache System for Chatbot
Handles intelligent caching with context awareness
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any
    timestamp: float
    access_count: int
    context_hash: str
    ttl: float

class SmartCacheSystem:
    """Intelligent caching system with context awareness"""
    
    def __init__(self, default_ttl: float = 300, max_size: int = 1000):
        self.cache: Dict[str, CacheEntry] = {}
        self.session_cache: Dict[str, Dict[str, CacheEntry]] = {}  # session_id -> cache
        self.default_ttl = default_ttl  # 5 minutes
        self.max_size = max_size
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def _generate_key(self, query: str, features: List[str] = None, color: str = None, context: str = None) -> str:
        """Generate cache key from query parameters"""
        # Normalize inputs
        query_norm = query.lower().strip() if query else ""
        features_norm = sorted([f.lower().strip() for f in (features or [])])
        color_norm = color.lower().strip() if color else ""
        context_norm = context.lower().strip() if context else ""
        
        # Create composite key
        key_parts = [query_norm]
        if features_norm:
            key_parts.append("_".join(features_norm))
        if color_norm:
            key_parts.append(color_norm)
        if context_norm:
            key_parts.append(context_norm)
        
        return "_".join(key_parts)
    
    def _generate_context_hash(self, conversation_history: List[Dict]) -> str:
        """Generate hash from conversation context"""
        if not conversation_history:
            return ""
        
        # Use last 3 messages for context
        recent_messages = conversation_history[-3:]
        context_str = json.dumps(recent_messages, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()[:8]
    
    def get(self, query: str, features: List[str] = None, color: str = None, 
            conversation_history: List[Dict] = None) -> Optional[Any]:
        """Get cached result with context awareness"""
        self.stats['total_requests'] += 1
        
        key = self._generate_key(query, features, color)
        context_hash = self._generate_context_hash(conversation_history or [])
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                self.stats['misses'] += 1
                return None
            
            # Context-aware cache hit
            # If context has changed significantly, consider it a miss
            if entry.context_hash and context_hash and entry.context_hash != context_hash:
                # But still return if query is exactly the same (user repeated query)
                if query.lower().strip() == key.split('_')[0]:
                    entry.access_count += 1
                    entry.timestamp = time.time()  # Refresh timestamp
                    self.stats['hits'] += 1
                    logger.info(f"Context-aware cache hit: {key}")
                    return entry.data
                else:
                    self.stats['misses'] += 1
                    return None
            
            # Regular cache hit
            entry.access_count += 1
            entry.timestamp = time.time()  # Refresh timestamp
            self.stats['hits'] += 1
            logger.info(f"Cache hit: {key}")
            return entry.data
        
        self.stats['misses'] += 1
        return None
    
    def put(self, query: str, data: Any, features: List[str] = None, color: str = None,
            conversation_history: List[Dict] = None, ttl: float = None) -> None:
        """Store data in cache with context"""
        key = self._generate_key(query, features, color)
        context_hash = self._generate_context_hash(conversation_history or [])
        
        # Evict if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        entry = CacheEntry(
            key=key,
            data=data,
            timestamp=time.time(),
            access_count=1,
            context_hash=context_hash,
            ttl=ttl or self.default_ttl
        )
        
        self.cache[key] = entry
        logger.info(f"Cached: {key}")
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find entry with oldest timestamp and lowest access count
        lru_key = min(self.cache.keys(), 
                     key=lambda k: (self.cache[k].timestamp, self.cache[k].access_count))
        
        del self.cache[lru_key]
        self.stats['evictions'] += 1
        logger.info(f"Evicted LRU entry: {lru_key}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        pattern_lower = pattern.lower()
        keys_to_remove = []
        
        for key in self.cache.keys():
            if pattern_lower in key.lower():
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.info(f"Invalidated {len(keys_to_remove)} entries matching pattern: {pattern}")
        return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats['total_requests']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': hit_rate,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'total_requests': total_requests
        }
    
    def get_cache_info(self) -> List[Dict]:
        """Get detailed cache information"""
        info = []
        for key, entry in self.cache.items():
            age = time.time() - entry.timestamp
            info.append({
                'key': key,
                'age_seconds': age,
                'access_count': entry.access_count,
                'context_hash': entry.context_hash,
                'ttl': entry.ttl,
                'expires_in': entry.ttl - age
            })
        
        # Sort by access count (most accessed first)
        info.sort(key=lambda x: x['access_count'], reverse=True)
        return info
    
    def get_session(self, query: str, session_id: str, features: List[str] = None, 
                   color: str = None, conversation_history: List[Dict] = None) -> Optional[Any]:
        """Get data from session-specific cache"""
        if not session_id or session_id not in self.session_cache:
            return self.get(query, features, color, conversation_history)
        
        session_cache = self.session_cache[session_id]
        key = self._generate_key(query, features, color)
        
        if key in session_cache:
            entry = session_cache[key]
            
            # Check if expired
            if time.time() - entry.timestamp > entry.ttl:
                del session_cache[key]
                return None
            
            entry.access_count += 1
            entry.timestamp = time.time()
            self.stats['hits'] += 1
            logger.info(f"Session cache hit: {session_id}:{key}")
            return entry.data
        
        # Fallback to global cache
        return self.get(query, features, color, conversation_history)
    
    def put_session(self, query: str, data: Any, session_id: str, features: List[str] = None,
                   color: str = None, conversation_history: List[Dict] = None, ttl: float = None) -> None:
        """Store data in session-specific cache"""
        if not session_id:
            return self.put(query, data, features, color, conversation_history, ttl)
        
        # Initialize session cache if needed
        if session_id not in self.session_cache:
            self.session_cache[session_id] = {}
        
        session_cache = self.session_cache[session_id]
        key = self._generate_key(query, features, color)
        context_hash = self._generate_context_hash(conversation_history or [])
        
        # Limit session cache size
        if len(session_cache) >= 50:  # Max 50 entries per session
            # Remove oldest entry
            oldest_key = min(session_cache.keys(), 
                           key=lambda k: session_cache[k].timestamp)
            del session_cache[oldest_key]
        
        entry = CacheEntry(
            key=key,
            data=data,
            timestamp=time.time(),
            access_count=1,
            context_hash=context_hash,
            ttl=ttl or self.default_ttl
        )
        
        session_cache[key] = entry
        logger.info(f"Session cached: {session_id}:{key}")
        
        # Also store in global cache
        self.put(query, data, features, color, conversation_history, ttl)
    
    def clear_session(self, session_id: str) -> None:
        """Clear session-specific cache"""
        if session_id in self.session_cache:
            count = len(self.session_cache[session_id])
            del self.session_cache[session_id]
            logger.info(f"Cleared session cache for {session_id}: {count} entries")
    
    def cleanup_expired_sessions(self, max_age: float = 1800) -> int:
        """Clean up expired sessions (default: 30 minutes)"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_cache in self.session_cache.items():
            if not session_cache:
                expired_sessions.append(session_id)
                continue
            
            # Check if all entries in session are old
            newest_timestamp = max(entry.timestamp for entry in session_cache.values())
            if current_time - newest_timestamp > max_age:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.clear_session(session_id)
        
        return len(expired_sessions)

# Test the cache system
def test_smart_cache():
    """Test the smart cache system"""
    cache = SmartCacheSystem(ttl=60, max_size=5)
    
    # Test basic caching
    print("🧪 Testing Smart Cache System")
    print("=" * 40)
    
    # Test 1: Basic put/get
    cache.put("hamile pijama", ["product1", "product2"], ["hamile"], "siyah")
    result = cache.get("hamile pijama", ["hamile"], "siyah")
    print(f"✅ Basic cache: {'HIT' if result else 'MISS'}")
    
    # Test 2: Context awareness
    history1 = [{"message": "merhaba", "intent": "greeting"}]
    history2 = [{"message": "teşekkürler", "intent": "thanks"}]
    
    cache.put("gecelik", ["product3"], context=history1)
    result1 = cache.get("gecelik", conversation_history=history1)
    result2 = cache.get("gecelik", conversation_history=history2)
    
    print(f"✅ Context-aware cache: Same context {'HIT' if result1 else 'MISS'}")
    print(f"✅ Context-aware cache: Different context {'HIT' if result2 else 'MISS'}")
    
    # Test 3: Cache eviction
    for i in range(10):
        cache.put(f"test{i}", f"data{i}")
    
    print(f"✅ Cache size after eviction: {len(cache.cache)} (max: {cache.max_size})")
    
    # Test 4: Pattern invalidation
    cache.put("hamile takım", "data1")
    cache.put("hamile gecelik", "data2")
    cache.put("normal pijama", "data3")
    
    invalidated = cache.invalidate_pattern("hamile")
    print(f"✅ Pattern invalidation: {invalidated} entries removed")
    
    # Final stats
    stats = cache.get_stats()
    print(f"\n📊 Cache Stats: {stats}")
    
    cache_info = cache.get_cache_info()
    print(f"\n📋 Cache Info: {len(cache_info)} entries")
    for info in cache_info[:3]:  # Show top 3
        print(f"   {info['key']}: {info['access_count']} accesses, {info['age_seconds']:.1f}s old")

if __name__ == "__main__":
    test_smart_cache()