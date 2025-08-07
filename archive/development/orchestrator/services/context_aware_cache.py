#!/usr/bin/env python3
"""
Context-Aware Cache System - Smart caching with conversation context integration
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

try:
    from .conversation_context_manager import ConversationContext, ContextEntity, ContextType
except ImportError:
    from conversation_context_manager import ConversationContext, ContextEntity, ContextType

logger = logging.getLogger(__name__)

class CacheType(Enum):
    """Cache türleri"""
    SEARCH_RESULT = "search_result"
    PRODUCT_INFO = "product_info"
    CONTEXT_RESOLUTION = "context_resolution"
    FEATURE_EXTRACTION = "feature_extraction"
    SIMILARITY_SCORE = "similarity_score"

class ContextChange(Enum):
    """Context değişim türleri"""
    NEW_PRODUCT = "new_product"
    TOPIC_SWITCH = "topic_switch"
    PREFERENCE_UPDATE = "preference_update"
    SESSION_RESET = "session_reset"
    ENTITY_EXPIRY = "entity_expiry"

@dataclass
class CachedResult:
    """Cached result with context information"""
    key: str
    value: Any
    cache_type: CacheType
    session_id: str
    context_signature: str
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int
    context_entities: List[str]  # Entity IDs that this cache depends on
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Cache expired mi?"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def update_access(self):
        """Access bilgilerini güncelle"""
        self.last_accessed = datetime.now()
        self.access_count += 1

@dataclass
class CacheStats:
    """Cache istatistikleri"""
    total_entries: int
    hit_count: int
    miss_count: int
    invalidation_count: int
    memory_usage_mb: float
    hit_rate: float
    avg_ttl_seconds: float
    entries_by_type: Dict[CacheType, int]

class ContextAwareCache:
    """Context-aware caching system"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 1800):  # 30 minutes default
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Cache storage
        self.cache: Dict[str, CachedResult] = {}
        self.session_cache_keys: Dict[str, Set[str]] = {}  # session_id -> cache_keys
        self.entity_cache_keys: Dict[str, Set[str]] = {}   # entity_id -> cache_keys
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'evictions': 0
        }
        
        # TTL settings by cache type
        self.type_ttl = {
            CacheType.SEARCH_RESULT: 1800,      # 30 minutes
            CacheType.PRODUCT_INFO: 3600,       # 1 hour
            CacheType.CONTEXT_RESOLUTION: 900,  # 15 minutes
            CacheType.FEATURE_EXTRACTION: 7200, # 2 hours
            CacheType.SIMILARITY_SCORE: 1800    # 30 minutes
        }
        
        # Context sensitivity weights
        self.context_weights = {
            ContextType.PRODUCT_INQUIRY: 1.0,
            ContextType.PRODUCT_COMPARISON: 0.8,
            ContextType.GENERAL_INFO: 0.3,
            ContextType.SEARCH_REFINEMENT: 0.9,
            ContextType.FOLLOW_UP: 0.7
        }
    
    async def get(self, key: str, context: ConversationContext) -> Optional[Any]:
        """
        Context-aware cache get
        
        Args:
            key: Base cache key
            context: Conversation context
            
        Returns:
            Cached value or None
        """
        try:
            # Generate context-aware key
            context_key = self.generate_context_key(key, context)
            
            # Check if exists and not expired
            if context_key in self.cache:
                cached_result = self.cache[context_key]
                
                if cached_result.is_expired():
                    # Remove expired entry
                    await self._remove_cache_entry(context_key)
                    self.stats['misses'] += 1
                    return None
                
                # Validate context compatibility
                if self._is_context_compatible(cached_result, context):
                    cached_result.update_access()
                    self.stats['hits'] += 1
                    logger.debug(f"Cache hit for key: {context_key}")
                    return cached_result.value
                else:
                    # Context incompatible, invalidate
                    await self._remove_cache_entry(context_key)
                    self.stats['invalidations'] += 1
                    logger.debug(f"Cache invalidated due to context incompatibility: {context_key}")
            
            self.stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            self.stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: Any, context: ConversationContext, 
                 cache_type: CacheType = CacheType.SEARCH_RESULT, 
                 ttl: Optional[int] = None) -> bool:
        """
        Context-aware cache set
        
        Args:
            key: Base cache key
            value: Value to cache
            context: Conversation context
            cache_type: Type of cache entry
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        try:
            # Generate context-aware key
            context_key = self.generate_context_key(key, context)
            
            # Determine TTL
            if ttl is None:
                ttl = self.type_ttl.get(cache_type, self.default_ttl)
            
            # Create context signature
            context_signature = self._create_context_signature(context)
            
            # Extract relevant entity IDs
            context_entities = self._extract_context_entities(context)
            
            # Create cached result
            cached_result = CachedResult(
                key=context_key,
                value=value,
                cache_type=cache_type,
                session_id=context.session_id,
                context_signature=context_signature,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl_seconds=ttl,
                context_entities=context_entities,
                metadata={'original_key': key}
            )
            
            # Check cache size and evict if necessary
            if len(self.cache) >= self.max_size:
                await self._evict_lru_entries()
            
            # Store in cache
            self.cache[context_key] = cached_result
            
            # Update indexes
            self._update_indexes(context_key, context.session_id, context_entities)
            
            logger.debug(f"Cached entry: {context_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def invalidate_context(self, session_id: str, context_change: ContextChange, 
                               entity_id: Optional[str] = None):
        """
        Context değişiminde cache'i invalidate et
        
        Args:
            session_id: Session ID
            context_change: Change type
            entity_id: Specific entity ID (optional)
        """
        try:
            keys_to_remove = set()
            
            if context_change == ContextChange.SESSION_RESET:
                # Remove all cache entries for session
                if session_id in self.session_cache_keys:
                    keys_to_remove.update(self.session_cache_keys[session_id])
            
            elif context_change == ContextChange.NEW_PRODUCT:
                # Invalidate search results and context resolutions
                if session_id in self.session_cache_keys:
                    for cache_key in self.session_cache_keys[session_id]:
                        if cache_key in self.cache:
                            cached_result = self.cache[cache_key]
                            if cached_result.cache_type in [CacheType.SEARCH_RESULT, CacheType.CONTEXT_RESOLUTION]:
                                keys_to_remove.add(cache_key)
            
            elif context_change == ContextChange.TOPIC_SWITCH:
                # Invalidate context-sensitive caches
                if session_id in self.session_cache_keys:
                    for cache_key in self.session_cache_keys[session_id]:
                        if cache_key in self.cache:
                            cached_result = self.cache[cache_key]
                            if cached_result.cache_type == CacheType.CONTEXT_RESOLUTION:
                                keys_to_remove.add(cache_key)
            
            elif context_change == ContextChange.ENTITY_EXPIRY and entity_id:
                # Remove caches dependent on specific entity
                if entity_id in self.entity_cache_keys:
                    keys_to_remove.update(self.entity_cache_keys[entity_id])
            
            # Remove identified keys
            for key in keys_to_remove:
                await self._remove_cache_entry(key)
                self.stats['invalidations'] += 1
            
            if keys_to_remove:
                logger.info(f"Invalidated {len(keys_to_remove)} cache entries for {context_change.value}")
                
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
    
    def generate_context_key(self, base_key: str, context: ConversationContext) -> str:
        """Context-aware cache key oluştur"""
        try:
            # Base components
            key_components = [base_key, context.session_id]
            
            # Add current topic if exists
            if context.current_topic:
                key_components.append(f"topic:{context.current_topic}")
            
            # Add recent product IDs
            recent_products = context.discussed_products[-2:] if context.discussed_products else []
            for product in recent_products:
                if hasattr(product, 'entity_id'):
                    key_components.append(f"product:{product.entity_id}")
            
            # Add active context types
            if context.context_stack:
                recent_contexts = context.context_stack[-2:]
                context_str = ",".join([ct.value for ct in recent_contexts])
                key_components.append(f"contexts:{context_str}")
            
            # Add user preferences hash
            if context.user_preferences:
                prefs_str = json.dumps(context.user_preferences, sort_keys=True)
                prefs_hash = hashlib.md5(prefs_str.encode()).hexdigest()[:8]
                key_components.append(f"prefs:{prefs_hash}")
            
            # Create final key
            combined_key = "|".join(key_components)
            context_key = hashlib.sha256(combined_key.encode()).hexdigest()[:16]
            
            return f"{base_key}:{context_key}"
            
        except Exception as e:
            logger.error(f"Context key generation error: {str(e)}")
            return f"{base_key}:fallback"
    
    def _create_context_signature(self, context: ConversationContext) -> str:
        """Context signature oluştur"""
        try:
            signature_data = {
                'session_id': context.session_id,
                'current_topic': context.current_topic,
                'product_count': len(context.discussed_products),
                'context_stack': [ct.value for ct in context.context_stack[-3:]],  # Last 3
                'preferences_hash': hashlib.md5(
                    json.dumps(context.user_preferences, sort_keys=True).encode()
                ).hexdigest()[:8] if context.user_preferences else None
            }
            
            signature_str = json.dumps(signature_data, sort_keys=True)
            return hashlib.md5(signature_str.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Context signature creation error: {str(e)}")
            return "fallback_signature"
    
    def _extract_context_entities(self, context: ConversationContext) -> List[str]:
        """Context'ten entity ID'leri çıkar"""
        entity_ids = []
        
        try:
            # From discussed products
            for product in context.discussed_products[-3:]:  # Last 3 products
                if hasattr(product, 'entity_id'):
                    entity_ids.append(product.entity_id)
            
            # From active entities
            for entity_id in list(context.active_entities.keys())[-5:]:  # Last 5 active
                entity_ids.append(entity_id)
            
        except Exception as e:
            logger.error(f"Entity extraction error: {str(e)}")
        
        return list(set(entity_ids))  # Remove duplicates
    
    def _is_context_compatible(self, cached_result: CachedResult, 
                             current_context: ConversationContext) -> bool:
        """Cache entry context ile uyumlu mu?"""
        try:
            # Session must match
            if cached_result.session_id != current_context.session_id:
                return False
            
            # Check context signature similarity
            current_signature = self._create_context_signature(current_context)
            
            # For some cache types, exact context match is required
            if cached_result.cache_type == CacheType.CONTEXT_RESOLUTION:
                return cached_result.context_signature == current_signature
            
            # For others, check entity compatibility
            current_entities = set(self._extract_context_entities(current_context))
            cached_entities = set(cached_result.context_entities)
            
            # If no common entities, might be incompatible
            if cached_entities and current_entities:
                overlap = len(cached_entities.intersection(current_entities))
                overlap_ratio = overlap / len(cached_entities.union(current_entities))
                return overlap_ratio >= 0.3  # At least 30% overlap
            
            return True  # Compatible if no specific entities
            
        except Exception as e:
            logger.error(f"Context compatibility check error: {str(e)}")
            return False
    
    def _update_indexes(self, cache_key: str, session_id: str, entity_ids: List[str]):
        """Cache indexes'leri güncelle"""
        try:
            # Session index
            if session_id not in self.session_cache_keys:
                self.session_cache_keys[session_id] = set()
            self.session_cache_keys[session_id].add(cache_key)
            
            # Entity indexes
            for entity_id in entity_ids:
                if entity_id not in self.entity_cache_keys:
                    self.entity_cache_keys[entity_id] = set()
                self.entity_cache_keys[entity_id].add(cache_key)
                
        except Exception as e:
            logger.error(f"Index update error: {str(e)}")
    
    async def _remove_cache_entry(self, cache_key: str):
        """Cache entry'sini kaldır"""
        try:
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                
                # Remove from main cache
                del self.cache[cache_key]
                
                # Remove from session index
                session_id = cached_result.session_id
                if session_id in self.session_cache_keys:
                    self.session_cache_keys[session_id].discard(cache_key)
                    if not self.session_cache_keys[session_id]:
                        del self.session_cache_keys[session_id]
                
                # Remove from entity indexes
                for entity_id in cached_result.context_entities:
                    if entity_id in self.entity_cache_keys:
                        self.entity_cache_keys[entity_id].discard(cache_key)
                        if not self.entity_cache_keys[entity_id]:
                            del self.entity_cache_keys[entity_id]
                            
        except Exception as e:
            logger.error(f"Cache entry removal error: {str(e)}")
    
    async def _evict_lru_entries(self, count: int = None):
        """LRU eviction"""
        try:
            if count is None:
                count = max(1, len(self.cache) // 10)  # Evict 10%
            
            # Sort by last accessed time
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove oldest entries
            for i in range(min(count, len(sorted_entries))):
                cache_key = sorted_entries[i][0]
                await self._remove_cache_entry(cache_key)
                self.stats['evictions'] += 1
                
        except Exception as e:
            logger.error(f"LRU eviction error: {str(e)}")
    
    async def cleanup_expired(self):
        """Expired entries'leri temizle"""
        try:
            expired_keys = []
            
            for cache_key, cached_result in self.cache.items():
                if cached_result.is_expired():
                    expired_keys.append(cache_key)
            
            for cache_key in expired_keys:
                await self._remove_cache_entry(cache_key)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Expired cleanup error: {str(e)}")
    
    def get_cache_stats(self) -> CacheStats:
        """Cache istatistikleri"""
        try:
            total_hits = self.stats['hits']
            total_misses = self.stats['misses']
            hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0
            
            # Memory usage estimation (rough)
            memory_usage = 0
            for cached_result in self.cache.values():
                try:
                    memory_usage += len(json.dumps(asdict(cached_result), default=str))
                except:
                    memory_usage += 1000  # Rough estimate
            
            memory_usage_mb = memory_usage / (1024 * 1024)
            
            # Entries by type
            entries_by_type = {}
            for cached_result in self.cache.values():
                cache_type = cached_result.cache_type
                entries_by_type[cache_type] = entries_by_type.get(cache_type, 0) + 1
            
            # Average TTL
            avg_ttl = sum(cr.ttl_seconds for cr in self.cache.values()) / len(self.cache) if self.cache else 0
            
            return CacheStats(
                total_entries=len(self.cache),
                hit_count=total_hits,
                miss_count=total_misses,
                invalidation_count=self.stats['invalidations'],
                memory_usage_mb=memory_usage_mb,
                hit_rate=hit_rate,
                avg_ttl_seconds=avg_ttl,
                entries_by_type=entries_by_type
            )
            
        except Exception as e:
            logger.error(f"Stats calculation error: {str(e)}")
            return CacheStats(0, 0, 0, 0, 0.0, 0.0, 0.0, {})
    
    async def clear_session_cache(self, session_id: str):
        """Session cache'ini temizle"""
        await self.invalidate_context(session_id, ContextChange.SESSION_RESET)
    
    async def clear_all_cache(self):
        """Tüm cache'i temizle"""
        self.cache.clear()
        self.session_cache_keys.clear()
        self.entity_cache_keys.clear()
        self.stats = {'hits': 0, 'misses': 0, 'invalidations': 0, 'evictions': 0}
        logger.info("All cache cleared")

# Test fonksiyonu
async def test_context_aware_cache():
    """Context-aware cache test"""
    
    # Mock context
    from conversation_context_manager import ConversationContext, ContextEntity, ContextType, EntityType
    from datetime import datetime
    
    cache = ContextAwareCache(max_size=100)
    
    # Create test context
    context = ConversationContext(
        session_id="test_session_789",
        current_topic="gecelik",
        discussed_products=[
            ContextEntity(
                entity_id="product_1",
                entity_type=EntityType.PRODUCT,
                value={"id": 1, "name": "Siyah Gecelik"},
                confidence=0.9,
                mentioned_at=datetime.now(),
                context_type=ContextType.PRODUCT_INQUIRY
            )
        ],
        user_preferences={"color": "siyah"},
        conversation_history=[],
        last_activity=datetime.now(),
        context_confidence=0.8,
        active_entities={},
        context_stack=[ContextType.PRODUCT_INQUIRY]
    )
    
    print("🗄️ Context-Aware Cache Test:")
    print("=" * 50)
    
    # Test 1: Cache set and get
    test_key = "search_result_siyah_gecelik"
    test_value = {"results": ["Siyah Tüllü Gecelik", "Siyah Dantelli Gecelik"]}
    
    success = await cache.set(test_key, test_value, context, CacheType.SEARCH_RESULT)
    print(f"✅ Cache set success: {success}")
    
    # Generate context key for verification
    context_key = cache.generate_context_key(test_key, context)
    print(f"🔑 Generated context key: {context_key}")
    
    # Test get
    cached_value = await cache.get(test_key, context)
    print(f"✅ Cache get success: {cached_value is not None}")
    
    # Test 2: Context compatibility
    # Modify context slightly
    context.current_topic = "pijama"
    cached_value_2 = await cache.get(test_key, context)
    print(f"🔄 Cache after context change: {cached_value_2 is not None}")
    
    # Test 3: Cache invalidation
    await cache.invalidate_context("test_session_789", ContextChange.TOPIC_SWITCH)
    cached_value_3 = await cache.get(test_key, context)
    print(f"🗑️ Cache after invalidation: {cached_value_3 is not None}")
    
    # Test 4: Multiple cache entries
    for i in range(5):
        await cache.set(f"test_key_{i}", f"value_{i}", context, CacheType.PRODUCT_INFO)
    
    # Test 5: Cache stats
    stats = cache.get_cache_stats()
    print(f"\n📊 Cache Stats:")
    print(f"  Total entries: {stats.total_entries}")
    print(f"  Hit rate: {stats.hit_rate:.2%}")
    print(f"  Memory usage: {stats.memory_usage_mb:.2f} MB")
    print(f"  Entries by type: {stats.entries_by_type}")
    
    # Test 6: Cleanup
    await cache.cleanup_expired()
    print(f"✅ Cleanup completed")
    
    # Test 7: Clear session cache
    await cache.clear_session_cache("test_session_789")
    final_stats = cache.get_cache_stats()
    print(f"🗑️ After session clear - Total entries: {final_stats.total_entries}")

if __name__ == "__main__":
    asyncio.run(test_context_aware_cache())