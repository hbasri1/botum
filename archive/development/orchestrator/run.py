#!/usr/bin/env python3
"""
Multi-Tenant Chatbot Orchestrator
Ana başlatma scripti
"""

import asyncio
import uvicorn
from app.main import app
from services.database_service import DatabaseService
from services.session_manager import SessionManager
from services.cache_manager import CacheManager
from config.settings import app_settings
from utils.logger import setup_logger

logger = setup_logger(__name__, app_settings.log_level, app_settings.log_file)

async def initialize_services():
    """Servisleri başlat"""
    logger.info("Initializing services...")
    
    try:
        # Database
        db_service = DatabaseService(app_settings.database_url)
        await db_service.initialize()
        logger.info("Database service initialized")
        
        # Session Manager
        session_manager = SessionManager(app_settings.redis_url)
        health = await session_manager.health_check()
        if health:
            logger.info("Session manager initialized")
        else:
            logger.error("Session manager health check failed")
        
        # Cache Manager
        cache_manager = CacheManager(app_settings.redis_cache_url)
        health = await cache_manager.health_check()
        if health:
            logger.info("Cache manager initialized")
        else:
            logger.error("Cache manager health check failed")
        
        logger.info("All services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Service initialization failed: {str(e)}")
        return False

async def cleanup_services():
    """Servisleri temizle"""
    logger.info("Cleaning up services...")
    
    try:
        # Database bağlantılarını kapat
        db_service = DatabaseService()
        await db_service.close()
        
        logger.info("Services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Service cleanup failed: {str(e)}")

def main():
    """Ana fonksiyon"""
    logger.info(f"Starting {app_settings.app_name} v{app_settings.app_version}")
    logger.info(f"Environment: {app_settings.debug and 'development' or 'production'}")
    
    # Servisleri başlat
    init_success = asyncio.run(initialize_services())
    
    if not init_success:
        logger.error("Failed to initialize services, exiting...")
        return 1
    
    try:
        # Uvicorn server'ı başlat
        uvicorn.run(
            "app.main:app",
            host=app_settings.api_host,
            port=app_settings.api_port,
            workers=app_settings.api_workers,
            log_level=app_settings.log_level.lower(),
            reload=app_settings.debug,
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return 1
        
    finally:
        # Temizlik
        asyncio.run(cleanup_services())
        logger.info("Application shutdown complete")
    
    return 0

if __name__ == "__main__":
    exit(main())