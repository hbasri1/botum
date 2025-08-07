"""
Configuration Settings
Çevre değişkenleri ve uygulama ayarları
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field
from dataclasses import dataclass

class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # Uygulama
    app_name: str = "Multi-Tenant Chatbot Orchestrator"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Veritabanı
    database_url: str = Field(
        default="postgresql://user:password@localhost/chatbot_db",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    redis_cache_url: str = Field(
        default="redis://localhost:6379/1", 
        env="REDIS_CACHE_URL"
    )
    
    # Vertex AI / Gemini
    google_cloud_project: str = Field(
        default="your-project-id",
        env="GOOGLE_CLOUD_PROJECT"
    )
    google_cloud_location: str = Field(
        default="us-central1",
        env="GOOGLE_CLOUD_LOCATION"
    )
    gemini_model_name: str = Field(
        default="your-fine-tuned-model",
        env="GEMINI_MODEL_NAME"
    )
    google_credentials_path: Optional[str] = Field(
        default=None,
        env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    
    # LLM Ayarları
    llm_max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")
    llm_timeout: int = Field(default=30, env="LLM_TIMEOUT")
    llm_temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    
    # Cache Ayarları
    cache_default_ttl: int = Field(default=3600, env="CACHE_DEFAULT_TTL")  # 1 saat
    cache_faq_ttl: int = Field(default=86400, env="CACHE_FAQ_TTL")  # 24 saat
    
    # Session Ayarları
    session_ttl: int = Field(default=86400, env="SESSION_TTL")  # 24 saat
    session_cleanup_interval: int = Field(default=3600, env="SESSION_CLEANUP_INTERVAL")  # 1 saat
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # API Ayarları
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Güvenlik
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    allowed_origins: list = Field(
        default=["*"],
        env="ALLOWED_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # saniye
    
    # Function Calling Ayarları
    enable_function_calling: bool = Field(default=True, env="ENABLE_FUNCTION_CALLING")
    function_calling_model: str = Field(
        default="gemini-1.5-flash-latest",
        env="FUNCTION_CALLING_MODEL"
    )
    function_calling_temperature: float = Field(
        default=0.1,
        env="FUNCTION_CALLING_TEMPERATURE"
    )
    function_calling_max_retries: int = Field(
        default=3,
        env="FUNCTION_CALLING_MAX_RETRIES"
    )
    function_calling_timeout: int = Field(
        default=30,
        env="FUNCTION_CALLING_TIMEOUT"
    )
    
    # Function Cache Ayarları
    function_cache_enabled: bool = Field(default=True, env="FUNCTION_CACHE_ENABLED")
    function_cache_product_ttl: int = Field(
        default=300,  # 5 dakika
        env="FUNCTION_CACHE_PRODUCT_TTL"
    )
    function_cache_general_info_ttl: int = Field(
        default=3600,  # 1 saat
        env="FUNCTION_CACHE_GENERAL_INFO_TTL"
    )
    function_cache_default_ttl: int = Field(
        default=600,  # 10 dakika
        env="FUNCTION_CACHE_DEFAULT_TTL"
    )
    
    # Function Performance Monitoring
    function_performance_tracking: bool = Field(
        default=True,
        env="FUNCTION_PERFORMANCE_TRACKING"
    )
    function_performance_log_slow_queries: bool = Field(
        default=True,
        env="FUNCTION_PERFORMANCE_LOG_SLOW_QUERIES"
    )
    function_performance_slow_query_threshold: int = Field(
        default=1000,  # 1 saniye (ms)
        env="FUNCTION_PERFORMANCE_SLOW_QUERY_THRESHOLD"
    )
    
    # Fallback Ayarları
    function_fallback_enabled: bool = Field(default=True, env="FUNCTION_FALLBACK_ENABLED")
    function_fallback_max_attempts: int = Field(
        default=2,
        env="FUNCTION_FALLBACK_MAX_ATTEMPTS"
    )
    
    # Eskalasyon Ayarları
    confidence_threshold: float = Field(default=0.80, env="CONFIDENCE_THRESHOLD")
    escalation_webhook_timeout: int = Field(default=10, env="ESCALATION_WEBHOOK_TIMEOUT")
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # Email Ayarları (eskalasyon bildirimleri için)
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")
    escalation_email_recipients: list = Field(
        default=[],
        env="ESCALATION_EMAIL_RECIPIENTS"
    )
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development ortamı ayarları"""
    debug: bool = True
    log_level: str = "DEBUG"

class ProductionSettings(Settings):
    """Production ortamı ayarları"""
    debug: bool = False
    log_level: str = "INFO"
    api_workers: int = 4

class TestSettings(Settings):
    """Test ortamı ayarları"""
    debug: bool = True
    database_url: str = "postgresql://user:password@localhost/chatbot_test_db"
    redis_url: str = "redis://localhost:6379/10"
    redis_cache_url: str = "redis://localhost:6379/11"

def get_settings() -> Settings:
    """Ortam değişkenine göre ayarları getir"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()

@dataclass
class FunctionCallingConfig:
    """Function calling için yapılandırılmış config sınıfı"""
    
    enabled: bool
    model: str
    temperature: float
    max_retries: int
    timeout: int
    
    # Cache config
    cache_enabled: bool
    cache_product_ttl: int
    cache_general_info_ttl: int
    cache_default_ttl: int
    
    # Performance config
    performance_tracking: bool
    log_slow_queries: bool
    slow_query_threshold: int
    
    # Fallback config
    fallback_enabled: bool
    fallback_max_attempts: int
    
    @classmethod
    def from_settings(cls, settings: Settings) -> 'FunctionCallingConfig':
        """Settings'den FunctionCallingConfig oluştur"""
        return cls(
            enabled=settings.enable_function_calling,
            model=settings.function_calling_model,
            temperature=settings.function_calling_temperature,
            max_retries=settings.function_calling_max_retries,
            timeout=settings.function_calling_timeout,
            
            cache_enabled=settings.function_cache_enabled,
            cache_product_ttl=settings.function_cache_product_ttl,
            cache_general_info_ttl=settings.function_cache_general_info_ttl,
            cache_default_ttl=settings.function_cache_default_ttl,
            
            performance_tracking=settings.function_performance_tracking,
            log_slow_queries=settings.function_performance_log_slow_queries,
            slow_query_threshold=settings.function_performance_slow_query_threshold,
            
            fallback_enabled=settings.function_fallback_enabled,
            fallback_max_attempts=settings.function_fallback_max_attempts
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Config'i dict'e çevir"""
        return {
            "enabled": self.enabled,
            "model": self.model,
            "temperature": self.temperature,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "cache": {
                "enabled": self.cache_enabled,
                "product_ttl": self.cache_product_ttl,
                "general_info_ttl": self.cache_general_info_ttl,
                "default_ttl": self.cache_default_ttl
            },
            "performance": {
                "tracking": self.performance_tracking,
                "log_slow_queries": self.log_slow_queries,
                "slow_query_threshold": self.slow_query_threshold
            },
            "fallback": {
                "enabled": self.fallback_enabled,
                "max_attempts": self.fallback_max_attempts
            }
        }
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Dict'den config'i güncelle"""
        if "enabled" in config_dict:
            self.enabled = config_dict["enabled"]
        if "model" in config_dict:
            self.model = config_dict["model"]
        if "temperature" in config_dict:
            self.temperature = config_dict["temperature"]
        if "max_retries" in config_dict:
            self.max_retries = config_dict["max_retries"]
        if "timeout" in config_dict:
            self.timeout = config_dict["timeout"]
        
        # Cache config
        if "cache" in config_dict:
            cache_config = config_dict["cache"]
            if "enabled" in cache_config:
                self.cache_enabled = cache_config["enabled"]
            if "product_ttl" in cache_config:
                self.cache_product_ttl = cache_config["product_ttl"]
            if "general_info_ttl" in cache_config:
                self.cache_general_info_ttl = cache_config["general_info_ttl"]
            if "default_ttl" in cache_config:
                self.cache_default_ttl = cache_config["default_ttl"]
        
        # Performance config
        if "performance" in config_dict:
            perf_config = config_dict["performance"]
            if "tracking" in perf_config:
                self.performance_tracking = perf_config["tracking"]
            if "log_slow_queries" in perf_config:
                self.log_slow_queries = perf_config["log_slow_queries"]
            if "slow_query_threshold" in perf_config:
                self.slow_query_threshold = perf_config["slow_query_threshold"]
        
        # Fallback config
        if "fallback" in config_dict:
            fallback_config = config_dict["fallback"]
            if "enabled" in fallback_config:
                self.fallback_enabled = fallback_config["enabled"]
            if "max_attempts" in fallback_config:
                self.fallback_max_attempts = fallback_config["max_attempts"]

class RuntimeConfigManager:
    """Runtime configuration updates için manager"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.function_calling_config = FunctionCallingConfig.from_settings(settings)
        self._config_backup = None
    
    def get_function_calling_config(self) -> FunctionCallingConfig:
        """Function calling config'i getir"""
        return self.function_calling_config
    
    def update_function_calling_config(self, config_dict: Dict[str, Any]) -> bool:
        """Function calling config'i güncelle"""
        try:
            # Backup oluştur
            self._config_backup = self.function_calling_config.to_dict()
            
            # Config'i güncelle
            self.function_calling_config.update_from_dict(config_dict)
            
            return True
            
        except Exception as e:
            # Hata durumunda backup'tan restore et
            if self._config_backup:
                self.function_calling_config.update_from_dict(self._config_backup)
            
            raise e
    
    def restore_config_backup(self) -> bool:
        """Config backup'ını restore et"""
        try:
            if self._config_backup:
                self.function_calling_config.update_from_dict(self._config_backup)
                return True
            return False
            
        except Exception:
            return False
    
    def validate_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Config'i validate et"""
        validation_result = {
            "valid": True,
            "errors": []
        }
        
        # Temperature validation
        if "temperature" in config_dict:
            temp = config_dict["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                validation_result["valid"] = False
                validation_result["errors"].append("Temperature must be between 0 and 2")
        
        # Max retries validation
        if "max_retries" in config_dict:
            retries = config_dict["max_retries"]
            if not isinstance(retries, int) or retries < 1 or retries > 10:
                validation_result["valid"] = False
                validation_result["errors"].append("Max retries must be between 1 and 10")
        
        # Timeout validation
        if "timeout" in config_dict:
            timeout = config_dict["timeout"]
            if not isinstance(timeout, int) or timeout < 5 or timeout > 300:
                validation_result["valid"] = False
                validation_result["errors"].append("Timeout must be between 5 and 300 seconds")
        
        # Cache TTL validation
        if "cache" in config_dict:
            cache_config = config_dict["cache"]
            for ttl_key in ["product_ttl", "general_info_ttl", "default_ttl"]:
                if ttl_key in cache_config:
                    ttl = cache_config[ttl_key]
                    if not isinstance(ttl, int) or ttl < 60 or ttl > 86400:
                        validation_result["valid"] = False
                        validation_result["errors"].append(f"{ttl_key} must be between 60 and 86400 seconds")
        
        return validation_result

# Kullanım için
app_settings = get_settings()
runtime_config_manager = RuntimeConfigManager(app_settings)