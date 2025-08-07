"""
Configuration Manager - Configuration validation ve management için
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from orchestrator.config.settings import Settings, FunctionCallingConfig, RuntimeConfigManager

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration management sınıfı"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.runtime_manager = RuntimeConfigManager(settings)
        self.config_backup_dir = Path("config_backups")
        self.config_backup_dir.mkdir(exist_ok=True)
        
        # Configuration change log
        self.config_changes = []
        
        # Health check status
        self.health_status = {
            "function_calling": True,
            "database": True,
            "cache": True,
            "llm_service": True
        }
    
    def validate_configuration_on_startup(self) -> Dict[str, Any]:
        """
        Startup'ta configuration'ı validate et
        
        Returns:
            Dict: Validation sonucu
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "components_checked": []
            }
            
            # Function calling config validation
            fc_validation = self._validate_function_calling_config()
            validation_result["components_checked"].append("function_calling")
            
            if not fc_validation["valid"]:
                validation_result["valid"] = False
                validation_result["errors"].extend(fc_validation["errors"])
            
            validation_result["warnings"].extend(fc_validation.get("warnings", []))
            
            # Database config validation
            db_validation = self._validate_database_config()
            validation_result["components_checked"].append("database")
            
            if not db_validation["valid"]:
                validation_result["valid"] = False
                validation_result["errors"].extend(db_validation["errors"])
            
            # Cache config validation
            cache_validation = self._validate_cache_config()
            validation_result["components_checked"].append("cache")
            
            if not cache_validation["valid"]:
                validation_result["valid"] = False
                validation_result["errors"].extend(cache_validation["errors"])
            
            # LLM config validation
            llm_validation = self._validate_llm_config()
            validation_result["components_checked"].append("llm")
            
            if not llm_validation["valid"]:
                validation_result["valid"] = False
                validation_result["errors"].extend(llm_validation["errors"])
            
            # Log validation result
            if validation_result["valid"]:
                logger.info("Configuration validation passed")
            else:
                logger.error(f"Configuration validation failed: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Configuration validation error: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "components_checked": []
            }
    
    def _validate_function_calling_config(self) -> Dict[str, Any]:
        """Function calling config'i validate et"""
        try:
            fc_config = self.runtime_manager.get_function_calling_config()
            
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Model validation
            if not fc_config.model or fc_config.model.strip() == "":
                validation_result["valid"] = False
                validation_result["errors"].append("Function calling model is not configured")
            
            # Temperature validation
            if fc_config.temperature < 0 or fc_config.temperature > 2:
                validation_result["valid"] = False
                validation_result["errors"].append("Function calling temperature must be between 0 and 2")
            
            # Max retries validation
            if fc_config.max_retries < 1 or fc_config.max_retries > 10:
                validation_result["valid"] = False
                validation_result["errors"].append("Function calling max retries must be between 1 and 10")
            
            # Timeout validation
            if fc_config.timeout < 5 or fc_config.timeout > 300:
                validation_result["valid"] = False
                validation_result["errors"].append("Function calling timeout must be between 5 and 300 seconds")
            
            # Cache TTL validation
            if fc_config.cache_product_ttl < 60 or fc_config.cache_product_ttl > 86400:
                validation_result["valid"] = False
                validation_result["errors"].append("Product cache TTL must be between 60 and 86400 seconds")
            
            if fc_config.cache_general_info_ttl < 60 or fc_config.cache_general_info_ttl > 86400:
                validation_result["valid"] = False
                validation_result["errors"].append("General info cache TTL must be between 60 and 86400 seconds")
            
            # Performance threshold validation
            if fc_config.slow_query_threshold < 100 or fc_config.slow_query_threshold > 10000:
                validation_result["warnings"].append("Slow query threshold should be between 100 and 10000 ms")
            
            # Fallback validation
            if fc_config.fallback_max_attempts < 1 or fc_config.fallback_max_attempts > 5:
                validation_result["valid"] = False
                validation_result["errors"].append("Fallback max attempts must be between 1 and 5")
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Function calling config validation error: {str(e)}"],
                "warnings": []
            }
    
    def _validate_database_config(self) -> Dict[str, Any]:
        """Database config'i validate et"""
        try:
            validation_result = {
                "valid": True,
                "errors": []
            }
            
            # Database URL validation
            if not self.settings.database_url or self.settings.database_url.strip() == "":
                validation_result["valid"] = False
                validation_result["errors"].append("Database URL is not configured")
            
            # Database URL format validation
            if not self.settings.database_url.startswith(("postgresql://", "postgres://")):
                validation_result["valid"] = False
                validation_result["errors"].append("Database URL must be a PostgreSQL connection string")
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Database config validation error: {str(e)}"]
            }
    
    def _validate_cache_config(self) -> Dict[str, Any]:
        """Cache config'i validate et"""
        try:
            validation_result = {
                "valid": True,
                "errors": []
            }
            
            # Redis URL validation
            if not self.settings.redis_url or self.settings.redis_url.strip() == "":
                validation_result["valid"] = False
                validation_result["errors"].append("Redis URL is not configured")
            
            if not self.settings.redis_cache_url or self.settings.redis_cache_url.strip() == "":
                validation_result["valid"] = False
                validation_result["errors"].append("Redis cache URL is not configured")
            
            # TTL validation
            if self.settings.cache_default_ttl < 60 or self.settings.cache_default_ttl > 86400:
                validation_result["valid"] = False
                validation_result["errors"].append("Default cache TTL must be between 60 and 86400 seconds")
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Cache config validation error: {str(e)}"]
            }
    
    def _validate_llm_config(self) -> Dict[str, Any]:
        """LLM config'i validate et"""
        try:
            validation_result = {
                "valid": True,
                "errors": []
            }
            
            # Google Cloud project validation
            if not self.settings.google_cloud_project or self.settings.google_cloud_project.strip() == "":
                validation_result["valid"] = False
                validation_result["errors"].append("Google Cloud project is not configured")
            
            # Model name validation
            if not self.settings.gemini_model_name or self.settings.gemini_model_name.strip() == "":
                validation_result["valid"] = False
                validation_result["errors"].append("Gemini model name is not configured")
            
            # Temperature validation
            if self.settings.llm_temperature < 0 or self.settings.llm_temperature > 2:
                validation_result["valid"] = False
                validation_result["errors"].append("LLM temperature must be between 0 and 2")
            
            # Max retries validation
            if self.settings.llm_max_retries < 1 or self.settings.llm_max_retries > 10:
                validation_result["valid"] = False
                validation_result["errors"].append("LLM max retries must be between 1 and 10")
            
            # Timeout validation
            if self.settings.llm_timeout < 5 or self.settings.llm_timeout > 300:
                validation_result["valid"] = False
                validation_result["errors"].append("LLM timeout must be between 5 and 300 seconds")
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"LLM config validation error: {str(e)}"]
            }
    
    def backup_configuration(self, backup_name: Optional[str] = None) -> str:
        """
        Configuration backup oluştur
        
        Args:
            backup_name: Backup adı (optional)
            
        Returns:
            str: Backup dosya yolu
        """
        try:
            if not backup_name:
                backup_name = f"config_backup_{int(time.time())}"
            
            backup_data = {
                "timestamp": time.time(),
                "backup_name": backup_name,
                "settings": {
                    # Function calling settings
                    "enable_function_calling": self.settings.enable_function_calling,
                    "function_calling_model": self.settings.function_calling_model,
                    "function_calling_temperature": self.settings.function_calling_temperature,
                    "function_calling_max_retries": self.settings.function_calling_max_retries,
                    "function_calling_timeout": self.settings.function_calling_timeout,
                    
                    # Cache settings
                    "function_cache_enabled": self.settings.function_cache_enabled,
                    "function_cache_product_ttl": self.settings.function_cache_product_ttl,
                    "function_cache_general_info_ttl": self.settings.function_cache_general_info_ttl,
                    "function_cache_default_ttl": self.settings.function_cache_default_ttl,
                    
                    # Performance settings
                    "function_performance_tracking": self.settings.function_performance_tracking,
                    "function_performance_log_slow_queries": self.settings.function_performance_log_slow_queries,
                    "function_performance_slow_query_threshold": self.settings.function_performance_slow_query_threshold,
                    
                    # Fallback settings
                    "function_fallback_enabled": self.settings.function_fallback_enabled,
                    "function_fallback_max_attempts": self.settings.function_fallback_max_attempts,
                    
                    # Other important settings
                    "llm_temperature": self.settings.llm_temperature,
                    "llm_max_retries": self.settings.llm_max_retries,
                    "llm_timeout": self.settings.llm_timeout,
                    "confidence_threshold": self.settings.confidence_threshold
                }
            }
            
            backup_file = self.config_backup_dir / f"{backup_name}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Configuration backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Configuration backup error: {str(e)}")
            raise e
    
    def restore_configuration(self, backup_file: str) -> bool:
        """
        Configuration'ı backup'tan restore et
        
        Args:
            backup_file: Backup dosya yolu
            
        Returns:
            bool: Restore başarılı mı?
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            settings_data = backup_data.get("settings", {})
            
            # Function calling config'i restore et
            fc_config_dict = {
                "enabled": settings_data.get("enable_function_calling", True),
                "model": settings_data.get("function_calling_model", "gemini-1.5-flash-latest"),
                "temperature": settings_data.get("function_calling_temperature", 0.1),
                "max_retries": settings_data.get("function_calling_max_retries", 3),
                "timeout": settings_data.get("function_calling_timeout", 30),
                "cache": {
                    "enabled": settings_data.get("function_cache_enabled", True),
                    "product_ttl": settings_data.get("function_cache_product_ttl", 300),
                    "general_info_ttl": settings_data.get("function_cache_general_info_ttl", 3600),
                    "default_ttl": settings_data.get("function_cache_default_ttl", 600)
                },
                "performance": {
                    "tracking": settings_data.get("function_performance_tracking", True),
                    "log_slow_queries": settings_data.get("function_performance_log_slow_queries", True),
                    "slow_query_threshold": settings_data.get("function_performance_slow_query_threshold", 1000)
                },
                "fallback": {
                    "enabled": settings_data.get("function_fallback_enabled", True),
                    "max_attempts": settings_data.get("function_fallback_max_attempts", 2)
                }
            }
            
            # Config'i güncelle
            success = self.runtime_manager.update_function_calling_config(fc_config_dict)
            
            if success:
                # Configuration change'i logla
                self._log_configuration_change(
                    "restore",
                    f"Configuration restored from {backup_file}",
                    fc_config_dict
                )
                
                logger.info(f"Configuration restored from: {backup_file}")
                return True
            else:
                logger.error("Configuration restore failed")
                return False
            
        except Exception as e:
            logger.error(f"Configuration restore error: {str(e)}")
            return False
    
    def _log_configuration_change(self, change_type: str, description: str, 
                                config_data: Dict[str, Any]) -> None:
        """
        Configuration change'i logla
        
        Args:
            change_type: Change türü (update, restore, etc.)
            description: Change açıklaması
            config_data: Config verisi
        """
        try:
            change_log = {
                "timestamp": time.time(),
                "change_type": change_type,
                "description": description,
                "config_data": config_data
            }
            
            self.config_changes.append(change_log)
            
            # Son 100 change'i tut
            if len(self.config_changes) > 100:
                self.config_changes = self.config_changes[-100:]
            
            logger.info(f"Configuration change logged: {change_type} - {description}")
            
        except Exception as e:
            logger.error(f"Configuration change logging error: {str(e)}")
    
    def get_configuration_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Configuration change history'sini getir
        
        Args:
            limit: Maksimum change sayısı
            
        Returns:
            List: Configuration changes
        """
        try:
            return self.config_changes[-limit:] if self.config_changes else []
            
        except Exception as e:
            logger.error(f"Get configuration changes error: {str(e)}")
            return []
    
    async def health_check_function_calling_components(self) -> Dict[str, Any]:
        """
        Function calling component'larının health check'i
        
        Returns:
            Dict: Health check sonucu
        """
        try:
            health_result = {
                "overall_healthy": True,
                "components": {},
                "timestamp": time.time()
            }
            
            # Function calling config health
            fc_config = self.runtime_manager.get_function_calling_config()
            fc_health = {
                "healthy": fc_config.enabled,
                "status": "enabled" if fc_config.enabled else "disabled",
                "model": fc_config.model,
                "temperature": fc_config.temperature
            }
            health_result["components"]["function_calling"] = fc_health
            
            if not fc_health["healthy"]:
                health_result["overall_healthy"] = False
            
            # Cache health (mock - gerçek implementasyon cache manager'dan gelecek)
            cache_health = {
                "healthy": fc_config.cache_enabled,
                "status": "enabled" if fc_config.cache_enabled else "disabled",
                "product_ttl": fc_config.cache_product_ttl,
                "general_info_ttl": fc_config.cache_general_info_ttl
            }
            health_result["components"]["cache"] = cache_health
            
            # Performance monitoring health
            perf_health = {
                "healthy": fc_config.performance_tracking,
                "status": "enabled" if fc_config.performance_tracking else "disabled",
                "slow_query_threshold": fc_config.slow_query_threshold
            }
            health_result["components"]["performance_monitoring"] = perf_health
            
            # Fallback health
            fallback_health = {
                "healthy": fc_config.fallback_enabled,
                "status": "enabled" if fc_config.fallback_enabled else "disabled",
                "max_attempts": fc_config.fallback_max_attempts
            }
            health_result["components"]["fallback"] = fallback_health
            
            # Global health status'u güncelle
            self.health_status["function_calling"] = health_result["overall_healthy"]
            
            return health_result
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return {
                "overall_healthy": False,
                "components": {},
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_current_configuration_summary(self) -> Dict[str, Any]:
        """
        Mevcut configuration'ın özetini getir
        
        Returns:
            Dict: Configuration özeti
        """
        try:
            fc_config = self.runtime_manager.get_function_calling_config()
            
            return {
                "function_calling": {
                    "enabled": fc_config.enabled,
                    "model": fc_config.model,
                    "temperature": fc_config.temperature,
                    "max_retries": fc_config.max_retries,
                    "timeout": fc_config.timeout
                },
                "cache": {
                    "enabled": fc_config.cache_enabled,
                    "product_ttl": fc_config.cache_product_ttl,
                    "general_info_ttl": fc_config.cache_general_info_ttl,
                    "default_ttl": fc_config.cache_default_ttl
                },
                "performance": {
                    "tracking": fc_config.performance_tracking,
                    "log_slow_queries": fc_config.log_slow_queries,
                    "slow_query_threshold": fc_config.slow_query_threshold
                },
                "fallback": {
                    "enabled": fc_config.fallback_enabled,
                    "max_attempts": fc_config.fallback_max_attempts
                },
                "health_status": self.health_status,
                "last_updated": time.time()
            }
            
        except Exception as e:
            logger.error(f"Get configuration summary error: {str(e)}")
            return {"error": str(e)}