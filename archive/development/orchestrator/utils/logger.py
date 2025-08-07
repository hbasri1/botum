"""
Logging Utilities
Structured logging için yardımcı fonksiyonlar
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Özel JSON log formatter"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Timestamp ekle
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Service bilgisi ekle
        log_record['service'] = 'chatbot-orchestrator'
        
        # Level'ı string olarak ekle
        log_record['level'] = record.levelname
        
        # Module bilgisi ekle
        log_record['module'] = record.module

def setup_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Logger kurulumu"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Mevcut handler'ları temizle
    logger.handlers.clear()
    
    # JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(module)s %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (opsiyonel)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

class StructuredLogger:
    """Yapısal logging için yardımcı sınıf"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(self, request_id: str, method: str, path: str, 
                   user_id: str = None, business_id: str = None, **kwargs):
        """HTTP request logla"""
        self.logger.info("HTTP request", extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "user_id": user_id,
            "business_id": business_id,
            **kwargs
        })
    
    def log_response(self, request_id: str, status_code: int, 
                    response_time_ms: int, **kwargs):
        """HTTP response logla"""
        self.logger.info("HTTP response", extra={
            "request_id": request_id,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            **kwargs
        })
    
    def log_llm_call(self, session_id: str, business_id: str, 
                    prompt_length: int, response_time_ms: int, 
                    success: bool, **kwargs):
        """LLM çağrısını logla"""
        self.logger.info("LLM call", extra={
            "session_id": session_id,
            "business_id": business_id,
            "prompt_length": prompt_length,
            "response_time_ms": response_time_ms,
            "success": success,
            **kwargs
        })
    
    def log_database_query(self, query_type: str, table: str, 
                          execution_time_ms: int, success: bool, **kwargs):
        """Veritabanı sorgusu logla"""
        self.logger.info("Database query", extra={
            "query_type": query_type,
            "table": table,
            "execution_time_ms": execution_time_ms,
            "success": success,
            **kwargs
        })
    
    def log_cache_operation(self, operation: str, key: str, 
                           hit: bool = None, **kwargs):
        """Cache operasyonu logla"""
        self.logger.info("Cache operation", extra={
            "operation": operation,
            "key": key,
            "hit": hit,
            **kwargs
        })
    
    def log_business_event(self, business_id: str, event_type: str, 
                          details: Dict[str, Any] = None, **kwargs):
        """İşletme eventi logla"""
        self.logger.info("Business event", extra={
            "business_id": business_id,
            "event_type": event_type,
            "details": details or {},
            **kwargs
        })
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Dict[str, Any] = None, **kwargs):
        """Hata logla"""
        self.logger.error("Application error", extra={
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            **kwargs
        })

# Global logger instances
main_logger = setup_logger("orchestrator.main")
structured_logger = StructuredLogger(main_logger)