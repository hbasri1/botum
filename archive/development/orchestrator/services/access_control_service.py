"""
Access Control Service - Rate limiting ve access control
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Access level enum"""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    cooldown_seconds: int

class AccessControlService:
    """Access control ve rate limiting service"""
    
    def __init__(self):
        # Rate limit configurations per access level
        self.rate_limit_configs = {
            AccessLevel.BASIC: RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=500,
                burst_limit=10,
                cooldown_seconds=60
            ),
            AccessLevel.PREMIUM: RateLimitConfig(
                requests_per_minute=100,
                requests_per_hour=2000,
                burst_limit=20,
                cooldown_seconds=30
            ),
            AccessLevel.ENTERPRISE: RateLimitConfig(
                requests_per_minute=500,
                requests_per_hour=10000,
                burst_limit=50,
                cooldown_seconds=10
            )
        }
        
        # Rate limiting data
        self.rate_data = {}
        
        # Access control stats
        self.access_stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "by_business": {},
            "by_access_level": {}
        }
        
        # Business access levels (mock data - gerçekte DB'den gelecek)
        self.business_access_levels = {}
        
        # Function permissions per access level
        self.function_permissions = {
            AccessLevel.BASIC: ["getProductInfo", "getGeneralInfo"],
            AccessLevel.PREMIUM: ["getProductInfo", "getGeneralInfo"],
            AccessLevel.ENTERPRISE: ["getProductInfo", "getGeneralInfo"]
        }
    
    async def check_access(self, business_id: str, session_id: str, 
                          function_name: str) -> Dict[str, Any]:
        """
        Access control ve rate limiting kontrolü
        
        Args:
            business_id: İşletme ID
            session_id: Session ID
            function_name: Fonksiyon adı
            
        Returns:
            Dict: Access control sonucu
        """
        try:
            self.access_stats["total_requests"] += 1
            
            # Business stats güncelle
            if business_id not in self.access_stats["by_business"]:
                self.access_stats["by_business"][business_id] = {
                    "total": 0, "allowed": 0, "blocked": 0
                }
            
            self.access_stats["by_business"][business_id]["total"] += 1
            
            # 1. Business access level kontrolü
            access_level = await self._get_business_access_level(business_id)
            
            # Access level stats güncelle
            if access_level not in self.access_stats["by_access_level"]:
                self.access_stats["by_access_level"][access_level] = {
                    "total": 0, "allowed": 0, "blocked": 0
                }
            
            self.access_stats["by_access_level"][access_level]["total"] += 1
            
            # 2. Function permission kontrolü
            if not await self._check_function_permission(access_level, function_name):
                self.access_stats["blocked_requests"] += 1
                self.access_stats["by_business"][business_id]["blocked"] += 1
                self.access_stats["by_access_level"][access_level]["blocked"] += 1
                
                logger.warning(f"Function {function_name} not allowed for {access_level}")
                return {
                    "allowed": False,
                    "reason": "function_not_permitted",
                    "message": f"Function {function_name} requires higher access level"
                }
            
            # 3. Rate limiting kontrolü
            rate_limit_result = await self._check_rate_limit(
                business_id, session_id, access_level
            )
            
            if not rate_limit_result["allowed"]:
                self.access_stats["blocked_requests"] += 1
                self.access_stats["by_business"][business_id]["blocked"] += 1
                self.access_stats["by_access_level"][access_level]["blocked"] += 1
                
                return rate_limit_result
            
            # 4. Anomaly detection
            anomaly_result = await self._detect_access_anomalies(
                business_id, session_id, function_name
            )
            
            if anomaly_result["blocked"]:
                self.access_stats["blocked_requests"] += 1
                self.access_stats["by_business"][business_id]["blocked"] += 1
                self.access_stats["by_access_level"][access_level]["blocked"] += 1
                
                return {
                    "allowed": False,
                    "reason": "anomaly_detected",
                    "message": "Unusual access pattern detected",
                    "anomalies": anomaly_result["anomalies"]
                }
            
            # Access allowed
            self.access_stats["allowed_requests"] += 1
            self.access_stats["by_business"][business_id]["allowed"] += 1
            self.access_stats["by_access_level"][access_level]["allowed"] += 1
            
            return {
                "allowed": True,
                "access_level": access_level.value,
                "rate_limit_remaining": rate_limit_result.get("remaining", 0)
            }
            
        except Exception as e:
            logger.error(f"Access control error: {str(e)}")
            # Hata durumunda allow et (fail-open)
            return {"allowed": True, "error": str(e)}
    
    async def _get_business_access_level(self, business_id: str) -> AccessLevel:
        """Business access level'ını getir"""
        try:
            # Mock implementation - gerçekte DB'den gelecek
            if business_id in self.business_access_levels:
                return self.business_access_levels[business_id]
            
            # Default access level
            self.business_access_levels[business_id] = AccessLevel.BASIC
            return AccessLevel.BASIC
            
        except Exception as e:
            logger.error(f"Get access level error: {str(e)}")
            return AccessLevel.BASIC
    
    async def _check_function_permission(self, access_level: AccessLevel, 
                                       function_name: str) -> bool:
        """Function permission kontrolü"""
        try:
            allowed_functions = self.function_permissions.get(access_level, [])
            return function_name in allowed_functions
            
        except Exception as e:
            logger.error(f"Function permission check error: {str(e)}")
            return True  # Hata durumunda allow et
    
    async def _check_rate_limit(self, business_id: str, session_id: str, 
                              access_level: AccessLevel) -> Dict[str, Any]:
        """Rate limiting kontrolü"""
        try:
            current_time = time.time()
            rate_key = f"{business_id}:{session_id}"
            
            config = self.rate_limit_configs[access_level]
            
            # Rate data initialize et
            if rate_key not in self.rate_data:
                self.rate_data[rate_key] = {
                    "requests": [],
                    "blocked_until": 0,
                    "burst_count": 0,
                    "last_request": 0
                }
            
            rate_info = self.rate_data[rate_key]
            
            # Blocked durumu kontrol et
            if current_time < rate_info["blocked_until"]:
                return {
                    "allowed": False,
                    "reason": "rate_limit_exceeded",
                    "message": "Rate limit exceeded, please wait",
                    "retry_after": int(rate_info["blocked_until"] - current_time)
                }
            
            # Burst limit kontrolü
            time_since_last = current_time - rate_info["last_request"]
            if time_since_last < 1:  # 1 saniyeden az
                rate_info["burst_count"] += 1
                if rate_info["burst_count"] > config.burst_limit:
                    # Burst limit aşıldı
                    rate_info["blocked_until"] = current_time + config.cooldown_seconds
                    
                    logger.warning(f"Burst limit exceeded for {rate_key}")
                    return {
                        "allowed": False,
                        "reason": "burst_limit_exceeded",
                        "message": "Too many requests in short time",
                        "retry_after": config.cooldown_seconds
                    }
            else:
                rate_info["burst_count"] = 0
            
            # Minute limit kontrolü
            minute_ago = current_time - 60
            rate_info["requests"] = [
                req_time for req_time in rate_info["requests"]
                if req_time > minute_ago
            ]
            
            if len(rate_info["requests"]) >= config.requests_per_minute:
                rate_info["blocked_until"] = current_time + 60
                
                logger.warning(f"Minute rate limit exceeded for {rate_key}")
                return {
                    "allowed": False,
                    "reason": "minute_limit_exceeded",
                    "message": f"Exceeded {config.requests_per_minute} requests per minute",
                    "retry_after": 60
                }
            
            # Hour limit kontrolü
            hour_ago = current_time - 3600
            hourly_requests = [
                req_time for req_time in rate_info["requests"]
                if req_time > hour_ago
            ]
            
            if len(hourly_requests) >= config.requests_per_hour:
                rate_info["blocked_until"] = current_time + 3600
                
                logger.warning(f"Hourly rate limit exceeded for {rate_key}")
                return {
                    "allowed": False,
                    "reason": "hour_limit_exceeded",
                    "message": f"Exceeded {config.requests_per_hour} requests per hour",
                    "retry_after": 3600
                }
            
            # Request'i kaydet
            rate_info["requests"].append(current_time)
            rate_info["last_request"] = current_time
            
            return {
                "allowed": True,
                "remaining": config.requests_per_minute - len(rate_info["requests"])
            }
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return {"allowed": True}  # Hata durumunda allow et
    
    async def _detect_access_anomalies(self, business_id: str, session_id: str, 
                                     function_name: str) -> Dict[str, Any]:
        """Access anomaly detection"""
        try:
            anomalies = []
            
            # 1. Çok hızlı ardışık request'ler
            rate_key = f"{business_id}:{session_id}"
            if rate_key in self.rate_data:
                rate_info = self.rate_data[rate_key]
                if rate_info["burst_count"] > 5:
                    anomalies.append("rapid_requests")
            
            # 2. Gece saatlerinde yoğun kullanım (02:00-06:00)
            current_hour = time.localtime().tm_hour
            if 2 <= current_hour <= 6:
                if rate_key in self.rate_data:
                    recent_requests = len([
                        req for req in self.rate_data[rate_key]["requests"]
                        if time.time() - req < 300  # Son 5 dakika
                    ])
                    if recent_requests > 20:
                        anomalies.append("night_time_activity")
            
            # 3. Aynı function'ın çok tekrarlanması
            if await self._check_function_repetition(business_id, function_name):
                anomalies.append("function_repetition")
            
            # Risk assessment
            risk_level = len(anomalies)
            blocked = risk_level >= 2  # 2 veya daha fazla anomaly varsa block et
            
            if blocked:
                logger.warning(f"Access anomalies detected for {business_id}: {anomalies}")
            
            return {
                "blocked": blocked,
                "anomalies": anomalies,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {str(e)}")
            return {"blocked": False, "anomalies": []}
    
    async def _check_function_repetition(self, business_id: str, 
                                       function_name: str) -> bool:
        """Function repetition kontrolü"""
        # Basit implementation - gerçekte daha sofistike olabilir
        return False
    
    async def set_business_access_level(self, business_id: str, 
                                      access_level: AccessLevel) -> bool:
        """Business access level'ını set et"""
        try:
            self.business_access_levels[business_id] = access_level
            logger.info(f"Access level set for {business_id}: {access_level.value}")
            return True
            
        except Exception as e:
            logger.error(f"Set access level error: {str(e)}")
            return False
    
    async def get_rate_limit_status(self, business_id: str, 
                                  session_id: str) -> Dict[str, Any]:
        """Rate limit durumunu getir"""
        try:
            rate_key = f"{business_id}:{session_id}"
            
            if rate_key not in self.rate_data:
                return {"status": "no_data"}
            
            rate_info = self.rate_data[rate_key]
            current_time = time.time()
            
            # Access level al
            access_level = await self._get_business_access_level(business_id)
            config = self.rate_limit_configs[access_level]
            
            # Current usage hesapla
            minute_ago = current_time - 60
            minute_requests = len([
                req for req in rate_info["requests"]
                if req > minute_ago
            ])
            
            hour_ago = current_time - 3600
            hour_requests = len([
                req for req in rate_info["requests"]
                if req > hour_ago
            ])
            
            return {
                "access_level": access_level.value,
                "minute_usage": {
                    "used": minute_requests,
                    "limit": config.requests_per_minute,
                    "remaining": config.requests_per_minute - minute_requests
                },
                "hour_usage": {
                    "used": hour_requests,
                    "limit": config.requests_per_hour,
                    "remaining": config.requests_per_hour - hour_requests
                },
                "blocked_until": rate_info["blocked_until"] if current_time < rate_info["blocked_until"] else 0,
                "burst_count": rate_info["burst_count"]
            }
            
        except Exception as e:
            logger.error(f"Get rate limit status error: {str(e)}")
            return {"error": str(e)}
    
    def get_access_stats(self) -> Dict[str, Any]:
        """Access control istatistiklerini getir"""
        try:
            total = self.access_stats["total_requests"]
            allowed = self.access_stats["allowed_requests"]
            
            return {
                "total_requests": total,
                "allowed_requests": allowed,
                "blocked_requests": self.access_stats["blocked_requests"],
                "success_rate": allowed / total if total > 0 else 0,
                "by_business": self.access_stats["by_business"],
                "by_access_level": {
                    level.value: stats for level, stats in self.access_stats["by_access_level"].items()
                }
            }
            
        except Exception as e:
            logger.error(f"Access stats error: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup_old_rate_data(self) -> int:
        """Eski rate data'yı temizle"""
        try:
            current_time = time.time()
            cleaned_count = 0
            
            keys_to_remove = []
            for key, data in self.rate_data.items():
                # 24 saatten eski verileri temizle
                if (not data["requests"] or 
                    current_time - max(data["requests"]) > 86400):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.rate_data[key]
                cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned {cleaned_count} old rate limit entries")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Rate data cleanup error: {str(e)}")
            return 0
    
    async def create_access_audit_log(self, business_id: str, session_id: str,
                                    function_name: str, allowed: bool, 
                                    reason: Optional[str] = None) -> str:
        """Access audit log oluştur"""
        try:
            import uuid
            
            log_id = str(uuid.uuid4())
            
            audit_entry = {
                "log_id": log_id,
                "business_id": business_id,
                "session_id": session_id,
                "function_name": function_name,
                "allowed": allowed,
                "reason": reason,
                "timestamp": time.time(),
                "access_level": (await self._get_business_access_level(business_id)).value
            }
            
            # TODO: Veritabanına kaydet
            logger.info(f"Access audit: {audit_entry}")
            
            return log_id
            
        except Exception as e:
            logger.error(f"Access audit log error: {str(e)}")
            return ""
    
    def reset_access_stats(self) -> None:
        """Access istatistiklerini sıfırla"""
        self.access_stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "by_business": {},
            "by_access_level": {}
        }
        logger.info("Access stats reset")