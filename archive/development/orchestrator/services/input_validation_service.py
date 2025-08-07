"""
Input Validation Service - Function calling için güvenlik validasyonu
"""

import re
import html
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ValidationError, validator

logger = logging.getLogger(__name__)

class FunctionCallInput(BaseModel):
    """Function call input validation model"""
    function_name: str
    arguments: Dict[str, Any]
    session_id: str
    business_id: str
    
    @validator('function_name')
    def validate_function_name(cls, v):
        allowed_functions = ['getProductInfo', 'getGeneralInfo']
        if v not in allowed_functions:
            raise ValueError(f'Function {v} not allowed')
        return v
    
    @validator('session_id', 'business_id')
    def validate_ids(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid ID format')
        if len(v) > 100:
            raise ValueError('ID too long')
        return v

class ProductInfoArgs(BaseModel):
    """getProductInfo arguments validation"""
    product_name: str
    query_type: Optional[str] = "fiyat"
    
    @validator('product_name')
    def validate_product_name(cls, v):
        if len(v) > 100:
            raise ValueError('Product name too long')
        # SQL injection koruması
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', 'DROP', 'DELETE', 'UPDATE']
        v_upper = v.upper()
        for char in dangerous_chars:
            if char in v_upper:
                raise ValueError('Invalid characters in product name')
        return v.strip()
    
    @validator('query_type')
    def validate_query_type(cls, v):
        if v is None:
            return "fiyat"
        allowed_types = ['fiyat', 'stok', 'detay', 'all']
        if v not in allowed_types:
            raise ValueError(f'Query type {v} not allowed')
        return v

class GeneralInfoArgs(BaseModel):
    """getGeneralInfo arguments validation"""
    info_type: str
    
    @validator('info_type')
    def validate_info_type(cls, v):
        allowed_types = ['iletişim', 'iade', 'kargo', 'ödeme', 'genel']
        if v not in allowed_types:
            raise ValueError(f'Info type {v} not allowed')
        return v

class InputValidationService:
    """Input validation ve sanitization service"""
    
    def __init__(self):
        self.validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "blocked_attempts": 0,
            "by_function": {}
        }
        
        # Rate limiting için
        self.rate_limits = {}
    
    async def validate_function_call(self, function_name: str, arguments: Dict[str, Any], 
                                   session_id: str, business_id: str) -> Dict[str, Any]:
        """
        Function call input'unu validate et
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            session_id: Session ID
            business_id: İşletme ID
            
        Returns:
            Dict: Validation sonucu
        """
        try:
            self.validation_stats["total_validations"] += 1
            
            # Function stats güncelle
            if function_name not in self.validation_stats["by_function"]:
                self.validation_stats["by_function"][function_name] = {
                    "total": 0, "successful": 0, "failed": 0
                }
            
            self.validation_stats["by_function"][function_name]["total"] += 1
            
            # 1. Temel input validation
            try:
                function_input = FunctionCallInput(
                    function_name=function_name,
                    arguments=arguments,
                    session_id=session_id,
                    business_id=business_id
                )
            except ValidationError as e:
                self.validation_stats["failed_validations"] += 1
                self.validation_stats["by_function"][function_name]["failed"] += 1
                
                logger.warning(f"Basic validation failed: {str(e)}")
                return {
                    "valid": False,
                    "error": "Invalid input format",
                    "details": str(e)
                }
            
            # 2. Function-specific validation
            validation_result = await self._validate_function_arguments(
                function_name, arguments
            )
            
            if not validation_result["valid"]:
                self.validation_stats["failed_validations"] += 1
                self.validation_stats["by_function"][function_name]["failed"] += 1
                return validation_result
            
            # 3. Rate limiting kontrolü
            rate_limit_result = await self._check_rate_limit(session_id, business_id)
            if not rate_limit_result["allowed"]:
                self.validation_stats["blocked_attempts"] += 1
                
                logger.warning(f"Rate limit exceeded: {session_id}")
                return {
                    "valid": False,
                    "error": "Rate limit exceeded",
                    "retry_after": rate_limit_result.get("retry_after", 60)
                }
            
            # 4. Input sanitization
            sanitized_arguments = await self._sanitize_arguments(function_name, arguments)
            
            # Başarılı validation
            self.validation_stats["successful_validations"] += 1
            self.validation_stats["by_function"][function_name]["successful"] += 1
            
            logger.debug(f"Validation successful for {function_name}")
            
            return {
                "valid": True,
                "sanitized_arguments": sanitized_arguments,
                "original_arguments": arguments
            }
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            self.validation_stats["failed_validations"] += 1
            
            return {
                "valid": False,
                "error": "Validation system error",
                "details": str(e)
            }
    
    async def _validate_function_arguments(self, function_name: str, 
                                         arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Function-specific argument validation"""
        try:
            if function_name == "getProductInfo":
                try:
                    ProductInfoArgs(**arguments)
                    return {"valid": True}
                except ValidationError as e:
                    return {
                        "valid": False,
                        "error": "Invalid product info arguments",
                        "details": str(e)
                    }
            
            elif function_name == "getGeneralInfo":
                try:
                    GeneralInfoArgs(**arguments)
                    return {"valid": True}
                except ValidationError as e:
                    return {
                        "valid": False,
                        "error": "Invalid general info arguments",
                        "details": str(e)
                    }
            
            else:
                return {
                    "valid": False,
                    "error": f"Unknown function: {function_name}"
                }
                
        except Exception as e:
            logger.error(f"Function argument validation error: {str(e)}")
            return {
                "valid": False,
                "error": "Argument validation failed"
            }
    
    async def _sanitize_arguments(self, function_name: str, 
                                arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Input sanitization"""
        try:
            sanitized = {}
            
            for key, value in arguments.items():
                if isinstance(value, str):
                    # HTML escape
                    sanitized_value = html.escape(value)
                    
                    # SQL injection koruması
                    sanitized_value = self._prevent_sql_injection(sanitized_value)
                    
                    # XSS koruması
                    sanitized_value = self._prevent_xss(sanitized_value)
                    
                    # Whitespace temizleme
                    sanitized_value = sanitized_value.strip()
                    
                    sanitized[key] = sanitized_value
                else:
                    sanitized[key] = value
            
            logger.debug(f"Arguments sanitized for {function_name}")
            return sanitized
            
        except Exception as e:
            logger.error(f"Sanitization error: {str(e)}")
            return arguments  # Fallback to original
    
    def _prevent_sql_injection(self, value: str) -> str:
        """SQL injection koruması"""
        # Tehlikeli SQL keyword'leri kaldır
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b',
            r'\bSELECT\b', r'\bUNION\b', r'\bEXEC\b', r'\bEXECUTE\b',
            r'--', r'/\*', r'\*/', r';'
        ]
        
        for pattern in dangerous_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        return value
    
    def _prevent_xss(self, value: str) -> str:
        """XSS koruması"""
        # Script tag'leri kaldır
        value = re.sub(r'<script.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Tehlikeli HTML tag'leri kaldır
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form']
        for tag in dangerous_tags:
            value = re.sub(f'<{tag}.*?>', '', value, flags=re.IGNORECASE)
            value = re.sub(f'</{tag}>', '', value, flags=re.IGNORECASE)
        
        # JavaScript event handler'ları kaldır
        value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
        
        return value
    
    async def _check_rate_limit(self, session_id: str, business_id: str) -> Dict[str, Any]:
        """Rate limiting kontrolü"""
        try:
            import time
            
            current_time = time.time()
            rate_key = f"{business_id}:{session_id}"
            
            # Rate limit: 60 request per minute per session
            limit = 60
            window = 60  # seconds
            
            if rate_key not in self.rate_limits:
                self.rate_limits[rate_key] = {
                    "requests": [],
                    "blocked_until": 0
                }
            
            rate_data = self.rate_limits[rate_key]
            
            # Blocked durumu kontrol et
            if current_time < rate_data["blocked_until"]:
                return {
                    "allowed": False,
                    "retry_after": int(rate_data["blocked_until"] - current_time)
                }
            
            # Eski request'leri temizle
            rate_data["requests"] = [
                req_time for req_time in rate_data["requests"]
                if current_time - req_time < window
            ]
            
            # Rate limit kontrolü
            if len(rate_data["requests"]) >= limit:
                # Rate limit aşıldı - 1 dakika block
                rate_data["blocked_until"] = current_time + 60
                
                logger.warning(f"Rate limit exceeded for {rate_key}")
                return {
                    "allowed": False,
                    "retry_after": 60
                }
            
            # Request'i kaydet
            rate_data["requests"].append(current_time)
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return {"allowed": True}  # Hata durumunda allow et
    
    async def detect_anomalies(self, session_id: str, business_id: str, 
                             function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Anormal kullanım pattern'lerini tespit et"""
        try:
            anomalies = []
            
            # 1. Aynı query'nin çok tekrarlanması
            if await self._check_repeated_queries(session_id, function_name, arguments):
                anomalies.append("repeated_queries")
            
            # 2. Çok uzun string'ler
            for key, value in arguments.items():
                if isinstance(value, str) and len(value) > 200:
                    anomalies.append("oversized_input")
                    break
            
            # 3. Şüpheli karakterler
            for key, value in arguments.items():
                if isinstance(value, str):
                    if re.search(r'[<>"\';\\]', value):
                        anomalies.append("suspicious_characters")
                        break
            
            # 4. Çok hızlı request'ler
            if await self._check_rapid_requests(session_id):
                anomalies.append("rapid_requests")
            
            return {
                "anomalies_detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "risk_level": self._calculate_risk_level(anomalies)
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {str(e)}")
            return {"anomalies_detected": False, "anomalies": []}
    
    async def _check_repeated_queries(self, session_id: str, function_name: str, 
                                    arguments: Dict[str, Any]) -> bool:
        """Aynı query'nin tekrarlanıp tekrarlanmadığını kontrol et"""
        # Basit implementation - gerçekte cache'de tutulabilir
        return False
    
    async def _check_rapid_requests(self, session_id: str) -> bool:
        """Çok hızlı request kontrolü"""
        rate_key = f"rapid:{session_id}"
        if rate_key in self.rate_limits:
            requests = self.rate_limits[rate_key]["requests"]
            if len(requests) > 10:  # Son 10 saniyede 10'dan fazla request
                return True
        return False
    
    def _calculate_risk_level(self, anomalies: List[str]) -> str:
        """Risk level hesapla"""
        if not anomalies:
            return "low"
        elif len(anomalies) == 1:
            return "medium"
        else:
            return "high"
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Validation istatistiklerini getir"""
        try:
            total = self.validation_stats["total_validations"]
            successful = self.validation_stats["successful_validations"]
            
            return {
                "total_validations": total,
                "successful_validations": successful,
                "failed_validations": self.validation_stats["failed_validations"],
                "blocked_attempts": self.validation_stats["blocked_attempts"],
                "success_rate": successful / total if total > 0 else 0,
                "by_function": self.validation_stats["by_function"]
            }
            
        except Exception as e:
            logger.error(f"Validation stats error: {str(e)}")
            return {"error": str(e)}
    
    def reset_validation_stats(self) -> None:
        """Validation istatistiklerini sıfırla"""
        self.validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "blocked_attempts": 0,
            "by_function": {}
        }
        logger.info("Validation stats reset")
    
    async def cleanup_rate_limits(self) -> int:
        """Eski rate limit verilerini temizle"""
        try:
            import time
            current_time = time.time()
            cleaned_count = 0
            
            keys_to_remove = []
            for key, data in self.rate_limits.items():
                # 1 saatten eski verileri temizle
                if (current_time - max(data["requests"]) > 3600 
                    if data["requests"] else True):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.rate_limits[key]
                cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned {cleaned_count} old rate limit entries")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Rate limit cleanup error: {str(e)}")
            return 0