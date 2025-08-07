"""
Function Call Fallback - Function calling başarısız olduğunda traditional intent detection'a fallback
"""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FunctionCallFallback:
    """Function calling fallback mekanizması"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.fallback_stats = {
            "total_fallbacks": 0,
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "fallback_reasons": {}
        }
    
    async def fallback_to_intent_detection(self, prompt: str, session_id: str, 
                                         isletme_id: str, reason: str = "unknown") -> Optional[Dict[str, Any]]:
        """
        Intent detection'a fallback yap
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            reason: Fallback sebebi
            
        Returns:
            Dict: Intent detection yanıtı veya None
        """
        try:
            logger.info(f"Falling back to intent detection for session {session_id}, reason: {reason}")
            
            # Fallback istatistiklerini güncelle
            self.fallback_stats["total_fallbacks"] += 1
            if reason not in self.fallback_stats["fallback_reasons"]:
                self.fallback_stats["fallback_reasons"][reason] = 0
            self.fallback_stats["fallback_reasons"][reason] += 1
            
            # Performance comparison için başlangıç zamanı
            start_time = time.time()
            
            # Traditional intent detection'ı çağır
            result = await self.llm_service.process_message(prompt, session_id, isletme_id)
            
            # Performance comparison için bitiş zamanı
            execution_time = int((time.time() - start_time) * 1000)  # ms
            
            if result:
                # Fallback başarılı
                self.fallback_stats["successful_fallbacks"] += 1
                
                # Fallback kullanıldığını işaretle
                result["fallback_used"] = True
                result["fallback_reason"] = reason
                result["method"] = "intent_detection"
                result["execution_time_ms"] = execution_time
                
                # Performance comparison logla
                await self._log_performance_comparison(
                    prompt, session_id, isletme_id, execution_time, 
                    "intent_detection", True, reason
                )
                
                logger.info(f"Fallback successful for session {session_id}")
                return result
            else:
                # Fallback da başarısız
                self.fallback_stats["failed_fallbacks"] += 1
                
                # Performance comparison logla
                await self._log_performance_comparison(
                    prompt, session_id, isletme_id, execution_time, 
                    "intent_detection", False, reason
                )
                
                logger.error(f"Fallback failed for session {session_id}")
                return None
            
        except Exception as e:
            logger.error(f"Fallback error: {str(e)}")
            self.fallback_stats["failed_fallbacks"] += 1
            return None
    
    async def _log_performance_comparison(self, prompt: str, session_id: str, 
                                        isletme_id: str, execution_time: int,
                                        method: str, success: bool, reason: str) -> None:
        """
        Performance comparison logla
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            execution_time: Execution time (ms)
            method: Kullanılan method (function_calling, intent_detection)
            success: Başarılı mı?
            reason: Fallback sebebi
        """
        try:
            log_data = {
                "timestamp": time.time(),
                "session_id": session_id,
                "isletme_id": isletme_id,
                "user_message": prompt,
                "method": method,
                "execution_time_ms": execution_time,
                "success": success,
                "fallback_reason": reason if method == "intent_detection" else None
            }
            
            # TODO: Veritabanına performance comparison verilerini kaydet
            # Şimdilik sadece log
            logger.info(f"Performance comparison: {method} - {execution_time}ms - Success: {success}")
            
        except Exception as e:
            logger.error(f"Performance comparison logging error: {str(e)}")
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        Fallback istatistiklerini getir
        
        Returns:
            Dict: Fallback istatistikleri
        """
        try:
            total_fallbacks = self.fallback_stats["total_fallbacks"]
            successful_fallbacks = self.fallback_stats["successful_fallbacks"]
            
            return {
                "total_fallbacks": total_fallbacks,
                "successful_fallbacks": successful_fallbacks,
                "failed_fallbacks": self.fallback_stats["failed_fallbacks"],
                "success_rate": successful_fallbacks / total_fallbacks if total_fallbacks > 0 else 0,
                "fallback_reasons": self.fallback_stats["fallback_reasons"],
                "most_common_reason": max(
                    self.fallback_stats["fallback_reasons"].items(), 
                    key=lambda x: x[1]
                )[0] if self.fallback_stats["fallback_reasons"] else None
            }
            
        except Exception as e:
            logger.error(f"Fallback stats error: {str(e)}")
            return {"error": str(e)}
    
    def reset_fallback_stats(self) -> None:
        """Fallback istatistiklerini sıfırla"""
        self.fallback_stats = {
            "total_fallbacks": 0,
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "fallback_reasons": {}
        }
        logger.info("Fallback stats reset")
    
    async def ensure_seamless_transition(self, function_result: Optional[Dict[str, Any]], 
                                       prompt: str, session_id: str, 
                                       isletme_id: str) -> Dict[str, Any]:
        """
        Function calling ve intent detection arasında seamless transition sağla
        
        Args:
            function_result: Function calling sonucu
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Dict: Seamless transition sonucu
        """
        try:
            if function_result:
                # Function calling başarılı
                return function_result
            else:
                # Function calling başarısız, fallback yap
                return await self.fallback_to_intent_detection(
                    prompt, session_id, isletme_id, "function_call_failed"
                )
            
        except Exception as e:
            logger.error(f"Seamless transition error: {str(e)}")
            # Son çare olarak fallback yap
            return await self.fallback_to_intent_detection(
                prompt, session_id, isletme_id, "seamless_transition_error"
            )