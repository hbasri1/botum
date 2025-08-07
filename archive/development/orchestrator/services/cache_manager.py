"""
Cache Manager - Redis tabanlı önbellekleme sistemi
Sık sorulan sorular ve LLM yanıtları için cache
"""

import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = 3600  # 1 saat
    
    def _generate_cache_key(self, isletme_id: str, query: str) -> str:
        """Cache anahtarı oluştur"""
        # Query'yi normalize et
        normalized_query = query.lower().strip()
        
        # Hash oluştur (uzun query'ler için)
        query_hash = hashlib.md5(normalized_query.encode()).hexdigest()
        
        return f"cache:{isletme_id}:{query_hash}"
    
    async def get(self, key: str) -> Optional[str]:
        """Cache'den değer getir"""
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return value
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Cache'e değer kaydet"""
        try:
            ttl = ttl or self.default_ttl
            await self.redis_client.setex(key, ttl, value)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def get_or_set_query_response(self, isletme_id: str, query: str, 
                                      response: str, ttl: Optional[int] = None) -> Optional[str]:
        """Query için cache kontrol et, yoksa kaydet"""
        cache_key = self._generate_cache_key(isletme_id, query)
        
        # Önce cache'den kontrol et
        cached_response = await self.get(cache_key)
        if cached_response:
            return cached_response
        
        # Cache'e kaydet
        await self.set(cache_key, response, ttl)
        return None
    
    async def cache_business_faq(self, isletme_id: str, faq_data: dict):
        """İşletme SSS'lerini cache'e al"""
        try:
            for question, answer in faq_data.items():
                cache_key = self._generate_cache_key(isletme_id, question)
                await self.set(cache_key, answer, ttl=86400)  # 24 saat
            
            logger.info(f"Cached {len(faq_data)} FAQ items for business {isletme_id}")
        except Exception as e:
            logger.error(f"FAQ caching error: {str(e)}")
    
    async def invalidate_business_cache(self, isletme_id: str):
        """İşletme cache'ini temizle"""
        try:
            pattern = f"cache:{isletme_id}:*"
            keys_to_delete = []
            
            async for key in self.redis_client.scan_iter(match=pattern):
                keys_to_delete.append(key)
            
            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} cache keys for business {isletme_id}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
    
    async def invalidate_product_cache(self, isletme_id: str, product_id: str = None, product_name: str = None):
        """
        Ürün cache'ini temizle - ÇOK ÖNEMLİ
        Ürün bilgileri güncellendiğinde çağrılmalıdır
        """
        try:
            patterns_to_invalidate = []
            
            if product_name:
                # Ürün adı ile ilgili tüm cache'leri temizle
                product_patterns = [
                    f"cache:{isletme_id}:*{product_name.lower()}*",
                    f"cache:{isletme_id}:*fiyat*{product_name.lower()}*",
                    f"cache:{isletme_id}:*stok*{product_name.lower()}*",
                    f"cache:{isletme_id}:*{product_name.lower()}*fiyat*",
                    f"cache:{isletme_id}:*{product_name.lower()}*stok*"
                ]
                patterns_to_invalidate.extend(product_patterns)
            
            # Genel ürün sorguları
            general_patterns = [
                f"cache:{isletme_id}:*fiyat*",
                f"cache:{isletme_id}:*stok*",
                f"cache:{isletme_id}:*ürün*",
                f"cache:{isletme_id}:*katalog*",
                f"cache:{isletme_id}:*product*"
            ]
            patterns_to_invalidate.extend(general_patterns)
            
            keys_to_delete = []
            for pattern in patterns_to_invalidate:
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys_to_delete.append(key)
            
            # Duplicate'leri kaldır
            keys_to_delete = list(set(keys_to_delete))
            
            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} product cache keys for business {isletme_id}, product: {product_name or product_id}")
            
        except Exception as e:
            logger.error(f"Product cache invalidation error: {str(e)}")
    
    async def invalidate_business_info_cache(self, isletme_id: str, info_type: str = None):
        """
        İşletme bilgi cache'ini temizle
        İade politikası, telefon, adres vb. güncellendiğinde çağrılmalıdır
        """
        try:
            if info_type:
                # Belirli bilgi türü için cache temizle
                patterns = [
                    f"cache:{isletme_id}:*{info_type}*",
                    f"cache:{isletme_id}:*{info_type.lower()}*"
                ]
            else:
                # Tüm işletme bilgi cache'lerini temizle
                patterns = [
                    f"cache:{isletme_id}:*telefon*",
                    f"cache:{isletme_id}:*iade*",
                    f"cache:{isletme_id}:*kargo*",
                    f"cache:{isletme_id}:*adres*",
                    f"cache:{isletme_id}:*iletişim*",
                    f"cache:{isletme_id}:*politika*"
                ]
            
            keys_to_delete = []
            for pattern in patterns:
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys_to_delete.append(key)
            
            keys_to_delete = list(set(keys_to_delete))
            
            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} business info cache keys for {isletme_id}, type: {info_type}")
                
        except Exception as e:
            logger.error(f"Business info cache invalidation error: {str(e)}")
    
    async def invalidate_intent_cache(self, isletme_id: str, intent: str):
        """
        Intent bazlı cache temizleme
        Belirli intent'ler için cache'i temizle
        """
        try:
            pattern = f"intent_cache:{isletme_id}:{intent}"
            await self.redis_client.delete(pattern)
            logger.info(f"Invalidated intent cache for {isletme_id}:{intent}")
        except Exception as e:
            logger.error(f"Intent cache invalidation error: {str(e)}")
    
    async def set_intent_cache(self, isletme_id: str, intent: str, response: str, ttl: int = 86400):
        """
        Intent bazlı cache kaydetme
        İade politikası gibi sabit cevaplar için
        """
        try:
            cache_key = f"intent_cache:{isletme_id}:{intent}"
            await self.redis_client.setex(cache_key, ttl, response)
            logger.debug(f"Intent cache set: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Intent cache set error: {str(e)}")
    
    async def get_intent_cache(self, isletme_id: str, intent: str) -> Optional[str]:
        """Intent bazlı cache getirme"""
        try:
            cache_key = f"intent_cache:{isletme_id}:{intent}"
            value = await self.redis_client.get(cache_key)
            if value:
                logger.debug(f"Intent cache hit: {cache_key}")
            return value
        except Exception as e:
            logger.error(f"Intent cache get error: {str(e)}")
            return None
    
    async def get_cache_stats(self, isletme_id: str) -> dict:
        """İşletme cache istatistikleri"""
        try:
            pattern = f"cache:{isletme_id}:*"
            total_keys = 0
            total_memory = 0
            
            async for key in self.redis_client.scan_iter(match=pattern):
                total_keys += 1
                memory_usage = await self.redis_client.memory_usage(key)
                if memory_usage:
                    total_memory += memory_usage
            
            return {
                "total_cached_queries": total_keys,
                "memory_usage_bytes": total_memory,
                "memory_usage_mb": round(total_memory / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"error": str(e)}
    
    async def warm_up_cache(self, isletme_id: str):
        """Cache'i önceden doldur (sık sorulan sorular)"""
        try:
            # Bu fonksiyon işletme kurulumu sırasında çalıştırılabilir
            common_queries = [
                ("merhaba", "Merhaba! Size nasıl yardımcı olabilirim?"),
                ("teşekkürler", "Rica ederim! Başka bir sorunuz var mı?"),
                ("telefon numarası", "İletişim bilgilerimiz için müşteri hizmetlerimizle iletişime geçebilirsiniz."),
                ("iade politikası", "İade politikamız hakkında detaylı bilgi için müşteri hizmetlerimizle iletişime geçebilirsiniz."),
                ("kargo bilgisi", "Kargo ve teslimat bilgileri için müşteri hizmetlerimizle iletişime geçebilirsiniz.")
            ]
            
            for query, response in common_queries:
                cache_key = self._generate_cache_key(isletme_id, query)
                await self.set(cache_key, response, ttl=86400)  # 24 saat
            
            logger.info(f"Cache warmed up for business {isletme_id}")
        except Exception as e:
            logger.error(f"Cache warm-up error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Redis bağlantı kontrolü"""
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return False
    
    async def cleanup_expired_cache(self):
        """Süresi dolmuş cache'leri temizle"""
        try:
            # Redis otomatik olarak TTL'si dolmuş anahtarları siler
            # Bu fonksiyon manuel temizlik için kullanılabilir
            info = await self.redis_client.info("keyspace")
            logger.info(f"Cache keyspace info: {info}")
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")