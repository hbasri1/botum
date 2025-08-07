"""
Function Cache Manager - Basit in-memory cache
"""

import json
import hashlib
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FunctionCacheManager:
    """Basit in-memory function cache manager"""
    
    def __init__(self):
        # In-memory cache
        self.cache = {}
        
        # Cache configuration
        self.default_ttl = 300  # 5 dakika
        self.function_ttls = {
            "getProductInfo": 300,    # 5 dakika
            "getGeneralInfo": 3600,   # 1 saat
        }
        
        # Cache statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "cache_invalidations": 0
        }
    
    def _generate_cache_key(self, function_name: str, arguments: Dict[str, Any], 
                          business_id: str) -> str:
        """Cache key oluştur"""
        # Arguments'ı sırala (consistent key için)
        sorted_args = json.dumps(arguments, sort_keys=True)
        key_data = f"{business_id}:{function_name}:{sorted_args}"
        
        # Hash'le
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"func_cache:{key_hash}"
    
    async def get(self, function_name: str, arguments: Dict[str, Any], 
                 business_id: str) -> Optional[Dict[str, Any]]:
        """Cache'den değer al"""
        try:
            self.stats["total_requests"] += 1
            
            cache_key = self._generate_cache_key(function_name, arguments, business_id)
            
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                
                # TTL kontrolü
                if time.time() - entry["created_at"] < entry["ttl"]:
                    self.stats["cache_hits"] += 1
                    entry["hit_count"] += 1
                    entry["last_accessed"] = time.time()
                    
                    logger.info(f"Cache hit for {function_name}")
                    return entry["value"]
                else:
                    # Expired, sil
                    del self.cache[cache_key]
            
            self.stats["cache_misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, function_name: str, arguments: Dict[str, Any], 
                 business_id: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache'e değer kaydet"""
        try:
            cache_key = self._generate_cache_key(function_name, arguments, business_id)
            
            if ttl is None:
                ttl = self.function_ttls.get(function_name, self.default_ttl)
            
            self.cache[cache_key] = {
                "value": value,
                "ttl": ttl,
                "created_at": time.time(),
                "hit_count": 0,
                "last_accessed": time.time(),
                "function_name": function_name,
                "business_id": business_id
            }
            
            self.stats["cache_sets"] += 1
            logger.info(f"Cached result for {function_name} with TTL {ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def invalidate(self, business_id: Optional[str] = None, 
                        function_name: Optional[str] = None) -> int:
        """Cache'i invalidate et"""
        try:
            deleted_count = 0
            keys_to_delete = []
            
            for key, entry in self.cache.items():
                should_delete = False
                
                if business_id and entry.get("business_id") == business_id:
                    should_delete = True
                elif function_name and entry.get("function_name") == function_name:
                    should_delete = True
                elif business_id is None and function_name is None:
                    should_delete = True
                
                if should_delete:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
                deleted_count += 1
            
            self.stats["cache_invalidations"] += deleted_count
            logger.info(f"Cache invalidated: {deleted_count} entries deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
            return 0
    
    async def get_cache_hit_rate(self) -> Dict[str, Any]:
        """Cache hit rate bilgilerini getir"""
        try:
            total_requests = self.stats["total_requests"]
            cache_hits = self.stats["cache_hits"]
            
            hit_rate = cache_hits / total_requests if total_requests > 0 else 0
            
            return {
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "cache_misses": self.stats["cache_misses"],
                "hit_rate": hit_rate,
                "cache_size": len(self.cache),
                "stats": self.stats
            }
            
        except Exception as e:
            logger.error(f"Cache hit rate error: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup_expired(self) -> int:
        """Expired cache entries'leri temizle"""
        try:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self.cache.items():
                if current_time - entry["created_at"] >= entry["ttl"]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")
            return 0
    
    async def invalidate_for_product_update(self, business_id: str, 
                                          product_name: Optional[str] = None) -> int:
        """Ürün güncellemesi için cache invalidation"""
        try:
            deleted_count = 0
            keys_to_delete = []
            
            for key, entry in self.cache.items():
                if (entry.get("business_id") == business_id and 
                    entry.get("function_name") == "getProductInfo"):
                    
                    if product_name is None:
                        # Tüm ürün cache'lerini sil
                        keys_to_delete.append(key)
                    else:
                        # Sadece belirli ürün için
                        # Bu basit implementasyonda tüm ürün cache'lerini siliyoruz
                        keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Product cache invalidation error: {str(e)}")
            return 0
    
    async def invalidate_for_business_update(self, business_id: str) -> int:
        """İşletme bilgi güncellemesi için cache invalidation"""
        try:
            deleted_count = 0
            keys_to_delete = []
            
            for key, entry in self.cache.items():
                if (entry.get("business_id") == business_id and 
                    entry.get("function_name") == "getGeneralInfo"):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Business cache invalidation error: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Cache istatistiklerini getir"""
        return {
            "cache_size": len(self.cache),
            "stats": self.stats.copy(),
            "memory_usage_estimate": len(str(self.cache))  # Rough estimate
        }
    
    def clear_all(self) -> None:
        """Tüm cache'i temizle"""
        self.cache.clear()
        logger.info("All cache cleared")