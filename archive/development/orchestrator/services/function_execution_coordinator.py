"""
Function Execution Coordinator - Function call'ları route etmek ve execute etmek için
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from orchestrator.services.database_service import DatabaseService
from orchestrator.services.product_function_handler import ProductFunctionHandler
from orchestrator.services.general_info_function_handler import GeneralInfoFunctionHandler
from orchestrator.services.function_cache_manager import FunctionCacheManager

logger = logging.getLogger(__name__)

class FunctionExecutionCoordinator:
    """Function execution coordinator sınıfı"""
    
    def __init__(self, db_service: DatabaseService, function_cache_manager: FunctionCacheManager):
        self.db_service = db_service
        self.function_cache_manager = function_cache_manager
        
        # Function handler'ları initialize et
        self.product_handler = ProductFunctionHandler(db_service)
        self.general_info_handler = GeneralInfoFunctionHandler(db_service)
        
        # Performance tracking
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "cache_hits": 0,
            "by_function": {}
        }
    
    async def execute_function_call(self, function_name: str, arguments: Dict[str, Any], 
                                  session_id: str, business_id: str) -> Dict[str, Any]:
        """
        Function call'ı route et ve execute et
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            session_id: Session ID
            business_id: İşletme ID
            
        Returns:
            Dict: Execution sonucu
        """
        start_time = time.time()
        
        try:
            # Performance tracking
            self.execution_stats["total_executions"] += 1
            
            if function_name not in self.execution_stats["by_function"]:
                self.execution_stats["by_function"][function_name] = {
                    "total": 0, "successful": 0, "failed": 0, "cache_hits": 0
                }
            
            self.execution_stats["by_function"][function_name]["total"] += 1
            
            # Cache kontrolü
            cache_result = await self._check_cache(function_name, arguments, business_id)
            if cache_result:
                self.execution_stats["cache_hits"] += 1
                self.execution_stats["by_function"][function_name]["cache_hits"] += 1
                
                execution_time = int((time.time() - start_time) * 1000)
                
                # Cache hit'i logla
                await self._log_function_call(
                    function_name, arguments, session_id, business_id,
                    execution_time, True, None, cached=True
                )
                
                return {
                    "success": True,
                    "function_name": function_name,
                    "arguments": arguments,
                    "result": cache_result,
                    "response": cache_result.get("response", "İşlem tamamlandı.") if cache_result else "İşlem tamamlandı.",
                    "cached": True,
                    "execution_time_ms": execution_time
                }
            
            # Function'ı execute et
            result = await self._route_function_call(function_name, arguments, business_id)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            if result and result.get("success", False):
                # Başarılı execution
                self.execution_stats["successful_executions"] += 1
                self.execution_stats["by_function"][function_name]["successful"] += 1
                
                # Cache'e kaydet
                await self._cache_result(function_name, arguments, business_id, result)
                
                # Başarılı execution'ı logla
                await self._log_function_call(
                    function_name, arguments, session_id, business_id,
                    execution_time, True, None, cached=False
                )
                
                return {
                    "success": True,
                    "function_name": function_name,
                    "arguments": arguments,
                    "result": result,
                    "response": result.get("response", "İşlem tamamlandı.") if result else "İşlem tamamlandı.",
                    "cached": False,
                    "execution_time_ms": execution_time
                }
            else:
                # Başarısız execution
                self.execution_stats["failed_executions"] += 1
                self.execution_stats["by_function"][function_name]["failed"] += 1
                
                error_message = result.get("error", "Unknown error") if result else "No result"
                
                # Başarısız execution'ı logla
                await self._log_function_call(
                    function_name, arguments, session_id, business_id,
                    execution_time, False, error_message, cached=False
                )
                
                return {
                    "success": False,
                    "function_name": function_name,
                    "arguments": arguments,
                    "error": error_message,
                    "execution_time_ms": execution_time
                }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.error(f"Function execution error: {str(e)}")
            
            # Exception'ı logla
            await self._log_function_call(
                function_name, arguments, session_id, business_id,
                execution_time, False, str(e), cached=False
            )
            
            self.execution_stats["failed_executions"] += 1
            if function_name in self.execution_stats["by_function"]:
                self.execution_stats["by_function"][function_name]["failed"] += 1
            
            return {
                "success": False,
                "function_name": function_name,
                "arguments": arguments,
                "error": str(e),
                "execution_time_ms": execution_time
            }
    
    async def _route_function_call(self, function_name: str, arguments: Dict[str, Any], 
                                 business_id: str) -> Dict[str, Any]:
        """
        Function call'ı uygun handler'a route et
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            business_id: İşletme ID
            
        Returns:
            Dict: Handler sonucu
        """
        try:
            if function_name == "getProductInfo":
                product_name = arguments.get("product_name", "")
                query_type = arguments.get("query_type", "")
                
                return await self.product_handler.handle_product_query(
                    product_name, query_type, business_id
                )
            
            elif function_name == "getGeneralInfo":
                info_type = arguments.get("info_type", "")
                
                return await self.product_handler.handle_general_info_query(
                    info_type, business_id
                )
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported function: {function_name}"
                }
            
        except Exception as e:
            logger.error(f"Function routing error: {str(e)}")
            return {
                "success": False,
                "error": f"Function routing error: {str(e)}"
            }
    
    async def _check_cache(self, function_name: str, arguments: Dict[str, Any], 
                         business_id: str) -> Optional[Dict[str, Any]]:
        """
        Cache'den sonuç kontrol et
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            business_id: İşletme ID
            
        Returns:
            Dict: Cache'den gelen sonuç veya None
        """
        try:
            # Function cache manager'dan al
            cached_result = await self.function_cache_manager.get(
                function_name, arguments, business_id
            )
            
            if cached_result:
                logger.info(f"Cache hit for function {function_name}")
                return cached_result
            
            return None
            
        except Exception as e:
            logger.error(f"Cache check error: {str(e)}")
            return None
    
    async def _cache_result(self, function_name: str, arguments: Dict[str, Any], 
                          business_id: str, result: Dict[str, Any]) -> None:
        """
        Sonucu cache'e kaydet
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            business_id: İşletme ID
            result: Kaydedilecek sonuç
        """
        try:
            # TTL belirle (function type'a göre)
            ttl = self._get_cache_ttl(function_name)
            
            # Function cache manager ile kaydet
            success = await self.function_cache_manager.set(
                function_name, arguments, business_id, result, ttl
            )
            
            if success:
                logger.info(f"Cached result for function {function_name} with TTL {ttl}s")
            else:
                logger.warning(f"Failed to cache result for function {function_name}")
            
        except Exception as e:
            logger.error(f"Cache save error: {str(e)}")
    
    def _generate_cache_key(self, function_name: str, arguments: Dict[str, Any], 
                          business_id: str) -> str:
        """
        Cache key oluştur
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            business_id: İşletme ID
            
        Returns:
            str: Cache key
        """
        # Arguments'ı sırala (consistent key için)
        sorted_args = json.dumps(arguments, sort_keys=True)
        
        return f"function_call:{business_id}:{function_name}:{hash(sorted_args)}"
    
    def _get_cache_ttl(self, function_name: str) -> int:
        """
        Function type'a göre cache TTL döndür
        
        Args:
            function_name: Fonksiyon adı
            
        Returns:
            int: TTL (saniye)
        """
        ttl_config = {
            "getProductInfo": 300,  # 5 dakika (ürün bilgileri sık değişebilir)
            "getGeneralInfo": 3600,  # 1 saat (genel bilgiler daha az değişir)
        }
        
        return ttl_config.get(function_name, 600)  # Default 10 dakika
    
    async def _log_function_call(self, function_name: str, arguments: Dict[str, Any], 
                               session_id: str, business_id: str, execution_time: int,
                               success: bool, error_message: Optional[str], 
                               cached: bool = False) -> None:
        """
        Function call'ı logla
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            session_id: Session ID
            business_id: İşletme ID
            execution_time: Execution time (ms)
            success: Başarılı mı?
            error_message: Hata mesajı
            cached: Cache'den mi geldi?
        """
        try:
            # TODO: Veritabanına function_call_logs tablosuna kaydet
            # Şimdilik sadece log
            
            log_data = {
                "function_name": function_name,
                "arguments": arguments,
                "session_id": session_id,
                "business_id": business_id,
                "execution_time_ms": execution_time,
                "success": success,
                "error_message": error_message,
                "cached": cached,
                "timestamp": time.time()
            }
            
            if success:
                logger.info(f"Function call logged: {json.dumps(log_data)}")
            else:
                logger.error(f"Failed function call logged: {json.dumps(log_data)}")
            
        except Exception as e:
            logger.error(f"Function call logging error: {str(e)}")
    
    async def handle_execution_error(self, function_name: str, arguments: Dict[str, Any], 
                                   error: Exception, session_id: str, 
                                   business_id: str) -> Dict[str, Any]:
        """
        Execution error'ı handle et
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            error: Hata
            session_id: Session ID
            business_id: İşletme ID
            
        Returns:
            Dict: Error handling sonucu
        """
        try:
            error_message = str(error)
            
            # Error type'a göre recovery stratejisi
            if "timeout" in error_message.lower():
                # Timeout error - retry öner
                return {
                    "success": False,
                    "error_type": "timeout",
                    "error_message": "İstek zaman aşımına uğradı. Lütfen tekrar deneyin.",
                    "retry_suggested": True
                }
            
            elif "connection" in error_message.lower():
                # Connection error - sistem hatası
                return {
                    "success": False,
                    "error_type": "connection",
                    "error_message": "Bağlantı hatası oluştu. Lütfen daha sonra tekrar deneyin.",
                    "retry_suggested": True
                }
            
            elif "validation" in error_message.lower():
                # Validation error - kullanıcı hatası
                return {
                    "success": False,
                    "error_type": "validation",
                    "error_message": "Geçersiz parametre. Lütfen isteğinizi kontrol edin.",
                    "retry_suggested": False
                }
            
            else:
                # Genel hata
                return {
                    "success": False,
                    "error_type": "general",
                    "error_message": "Bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
                    "retry_suggested": True
                }
            
        except Exception as e:
            logger.error(f"Error handling error: {str(e)}")
            return {
                "success": False,
                "error_type": "unknown",
                "error_message": "Bilinmeyen bir hata oluştu.",
                "retry_suggested": False
            }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Execution istatistiklerini getir
        
        Returns:
            Dict: Execution istatistikleri
        """
        try:
            total_executions = self.execution_stats["total_executions"]
            successful_executions = self.execution_stats["successful_executions"]
            cache_hits = self.execution_stats["cache_hits"]
            
            return {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": self.execution_stats["failed_executions"],
                "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                "cache_hits": cache_hits,
                "cache_hit_rate": cache_hits / total_executions if total_executions > 0 else 0,
                "by_function": self.execution_stats["by_function"]
            }
            
        except Exception as e:
            logger.error(f"Execution stats error: {str(e)}")
            return {"error": str(e)}
    
    def reset_execution_stats(self) -> None:
        """Execution istatistiklerini sıfırla"""
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "cache_hits": 0,
            "by_function": {}
        }
        logger.info("Execution stats reset")
    
    async def invalidate_cache_for_business(self, business_id: str) -> None:
        """
        Belirli bir işletme için cache'i invalidate et
        
        Args:
            business_id: İşletme ID
        """
        try:
            # Function cache manager ile invalidate et
            deleted_count = await self.function_cache_manager.invalidate(
                business_id=business_id
            )
            
            logger.info(f"Cache invalidated for business {business_id}: {deleted_count} entries deleted")
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
    
    async def warm_cache_for_popular_queries(self, business_id: str) -> None:
        """
        Popüler sorgular için cache warming
        
        Args:
            business_id: İşletme ID
        """
        try:
            # Popüler ürünleri al
            popular_products = await self.db_service.get_popular_products(business_id, limit=5)
            
            # Popüler query type'lar
            popular_query_types = ["fiyat", "stok"]
            
            # Cache warming
            for product in popular_products:
                for query_type in popular_query_types:
                    try:
                        await self.execute_function_call(
                            "getProductInfo",
                            {"product_name": product["name"], "query_type": query_type},
                            "cache_warming",
                            business_id
                        )
                    except Exception as e:
                        logger.warning(f"Cache warming failed for {product['name']}: {str(e)}")
            
            # Genel bilgiler için cache warming
            general_info_types = ["telefon", "iade", "kargo"]
            
            for info_type in general_info_types:
                try:
                    await self.execute_function_call(
                        "getGeneralInfo",
                        {"info_type": info_type},
                        "cache_warming",
                        business_id
                    )
                except Exception as e:
                    logger.warning(f"Cache warming failed for {info_type}: {str(e)}")
            
            logger.info(f"Cache warming completed for business {business_id}")
            
        except Exception as e:
            logger.error(f"Cache warming error: {str(e)}")
    
    async def get_cache_hit_rate_monitoring(self) -> Dict[str, Any]:
        """
        Cache hit rate monitoring bilgilerini getir
        
        Returns:
            Dict: Cache hit rate monitoring bilgileri
        """
        try:
            # Function cache manager'dan hit rate al
            cache_hit_rate = await self.function_cache_manager.get_cache_hit_rate()
            
            # Execution stats ile birleştir
            execution_stats = self.get_execution_stats()
            
            return {
                "cache_performance": cache_hit_rate,
                "execution_performance": execution_stats,
                "combined_metrics": {
                    "total_requests": execution_stats["total_executions"],
                    "cache_efficiency": cache_hit_rate.get("hit_rate", 0),
                    "execution_success_rate": execution_stats["success_rate"],
                    "overall_performance_score": (
                        cache_hit_rate.get("hit_rate", 0) * 0.4 + 
                        execution_stats["success_rate"] * 0.6
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Cache hit rate monitoring error: {str(e)}")
            return {"error": str(e)}
    
    async def invalidate_cache_for_product_update(self, business_id: str, 
                                                product_name: Optional[str] = None) -> int:
        """
        Ürün güncellemesi için cache invalidation
        
        Args:
            business_id: İşletme ID
            product_name: Ürün adı (optional)
            
        Returns:
            int: Silinen cache entry sayısı
        """
        try:
            deleted_count = await self.function_cache_manager.invalidate_for_product_update(
                business_id, product_name
            )
            
            logger.info(f"Product cache invalidated: {deleted_count} entries for business {business_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Product cache invalidation error: {str(e)}")
            return 0
    
    async def invalidate_cache_for_business_info_update(self, business_id: str) -> int:
        """
        İşletme bilgi güncellemesi için cache invalidation
        
        Args:
            business_id: İşletme ID
            
        Returns:
            int: Silinen cache entry sayısı
        """
        try:
            deleted_count = await self.function_cache_manager.invalidate_for_business_update(
                business_id
            )
            
            logger.info(f"Business info cache invalidated: {deleted_count} entries for business {business_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Business info cache invalidation error: {str(e)}")
            return 0