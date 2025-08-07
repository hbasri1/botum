"""
Multi-Tenant Chatbot Orchestrator
Ana uygulama dosyası - Webhook endpoint'leri ve iş mantığı yönlendiricisi
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.services.session_manager import SessionManager
from orchestrator.services.cache_manager import CacheManager
from orchestrator.services.llm_service import LLMService
from orchestrator.services.business_logic_router import BusinessLogicRouter
from orchestrator.services.database_service import DatabaseService
from orchestrator.services.learning_service import LearningService
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Tenant Chatbot Orchestrator", version="1.0.0")

# Service instances
session_manager = SessionManager()
cache_manager = CacheManager()
llm_service = LLMService()
db_service = DatabaseService(cache_manager=cache_manager)  # Cache manager enjekte et
business_router = BusinessLogicRouter()
learning_service = LearningService(db_service, llm_service, cache_manager)

class WebhookRequest(BaseModel):
    """Gelen webhook isteği modeli"""
    mesaj_metni: str
    kullanici_id: str
    isletme_id: str
    platform: Optional[str] = "unknown"  # instagram, whatsapp, web
    timestamp: Optional[datetime] = None

class WebhookResponse(BaseModel):
    """Webhook yanıt modeli"""
    success: bool
    message: str
    session_id: Optional[str] = None
    response_time_ms: Optional[int] = None

@app.post("/webhook", response_model=WebhookResponse)
async def webhook_handler(request: WebhookRequest, background_tasks: BackgroundTasks):
    """
    Ana webhook endpoint - Tüm platformlardan gelen mesajları işler
    """
    start_time = datetime.now()
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[{request_id}] Webhook request received", extra={
        "kullanici_id": request.kullanici_id,
        "isletme_id": request.isletme_id,
        "platform": request.platform,
        "mesaj_length": len(request.mesaj_metni)
    })
    
    try:
        # 1. Session ID oluştur veya getir
        session_id = await session_manager.get_or_create_session(
            kullanici_id=request.kullanici_id,
            isletme_id=request.isletme_id
        )
        
        # 2. Akıllı Cache Kontrolü
        normalized_message = request.mesaj_metni.lower().strip()
        
        # LLM Cache kontrolü
        llm_cache_key = f"{request.isletme_id}:{normalized_message}"
        cached_llm_response = await cache_manager.get(llm_cache_key)
        
        if cached_llm_response:
            logger.info(f"[{request_id}] LLM Cache hit")
            # Cache'den gelen yanıtı JSON olarak parse et
            try:
                llm_response = json.loads(cached_llm_response)
                
                # İş mantığı yönlendiricisine gönder
                final_response = await business_router.route_intent(
                    llm_response=llm_response,
                    session_id=session_id,
                    isletme_id=request.isletme_id,
                    original_message=request.mesaj_metni
                )
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                return WebhookResponse(
                    success=True,
                    message=final_response,
                    session_id=session_id,
                    response_time_ms=int(response_time)
                )
                
            except json.JSONDecodeError:
                logger.warning(f"[{request_id}] Invalid cached LLM response, proceeding to LLM")
        
        # 3. Metin dışı içerik kontrolü
        if not await _is_text_message(request.mesaj_metni):
            logger.info(f"[{request_id}] Non-text content detected")
            return WebhookResponse(
                success=True,
                message="Sadece yazılı mesajları işleyebiliyorum. Lütfen sorunuzu yazarak iletin.",
                session_id=session_id,
                response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
        
        # 4. LLM'e gönder (Function calling ile)
        llm_response = await llm_service.process_message_with_functions(
            prompt=normalized_message,
            session_id=session_id,
            isletme_id=request.isletme_id
        )
        
        if not llm_response:
            logger.error(f"[{request_id}] LLM service unavailable")
            raise HTTPException(status_code=500, detail="LLM service unavailable")
        
        # 5. LLM yanıtını cache'e kaydet (1 saat TTL)
        await cache_manager.set(llm_cache_key, json.dumps(llm_response), ttl=3600)
        
        # 6. İş mantığı yönlendiricisi (güven skoru kontrolü dahil)
        final_response = await business_router.route_intent(
            llm_response=llm_response,
            session_id=session_id,
            isletme_id=request.isletme_id,
            original_message=request.mesaj_metni
        )
        
        # 7. Background task - logging
        background_tasks.add_task(
            log_interaction,
            request_id=request_id,
            request=request,
            llm_response=llm_response,
            final_response=final_response,
            session_id=session_id
        )
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return WebhookResponse(
            success=True,
            message=final_response,
            session_id=session_id,
            response_time_ms=int(response_time)
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Webhook error: {str(e)}", exc_info=True)
        
        # Genel hata mesajı - işletme bazlı olabilir
        error_message = await get_error_message(request.isletme_id)
        
        return WebhookResponse(
            success=False,
            message=error_message,
            session_id=session_id if 'session_id' in locals() else None
        )

async def log_interaction(request_id: str, request: WebhookRequest, 
                         llm_response: Dict[str, Any], final_response: str, 
                         session_id: str):
    """Background task - Etkileşimi detaylı logla"""
    try:
        await db_service.log_interaction(
            request_id=request_id,
            session_id=session_id,
            kullanici_id=request.kullanici_id,
            isletme_id=request.isletme_id,
            platform=request.platform,
            user_message=request.mesaj_metni,
            llm_response=llm_response,
            final_response=final_response,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to log interaction {request_id}: {str(e)}")

async def _is_text_message(message: str) -> bool:
    """Mesajın metin olup olmadığını kontrol et"""
    try:
        # Boş veya çok kısa mesajları filtrele
        if not message or len(message.strip()) < 2:
            return False
        
        # Sadece emoji/sticker kontrolü
        import re
        
        # Temel metin karakterleri var mı kontrol et
        text_chars = re.findall(r'[a-zA-ZçğıöşüÇĞIİÖŞÜ0-9\s.,!?]', message)
        
        # En az %30'u metin karakteri olmalı
        if len(text_chars) / len(message) < 0.3:
            return False
        
        # Yaygın metin dışı içerik belirteçleri
        non_text_indicators = [
            "[resim]", "[ses]", "[video]", "[sticker]", 
            "[konum]", "[dosya]", "[link]"
        ]
        
        message_lower = message.lower()
        for indicator in non_text_indicators:
            if indicator in message_lower:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Text validation error: {str(e)}")
        return True  # Hata durumunda metin kabul et

async def get_error_message(isletme_id: str) -> str:
    """İşletme bazlı hata mesajı getir"""
    try:
        business_info = await db_service.get_business_info(isletme_id)
        if business_info and business_info.get("error_message"):
            return business_info["error_message"]
    except:
        pass
    
    return "Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin."

@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "session_manager": await session_manager.health_check(),
            "cache_manager": await cache_manager.health_check(),
            "llm_service": await llm_service.health_check(),
            "database": await db_service.health_check(),
            "learning_service": await learning_service.health_check()
        }
    }

@app.get("/stats/{isletme_id}")
async def get_business_stats(isletme_id: str):
    """İşletme istatistikleri"""
    try:
        stats = await db_service.get_business_stats(isletme_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats for {isletme_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Stats unavailable")

# Cache Management Endpoints

@app.post("/admin/cache/invalidate/{isletme_id}")
async def invalidate_business_cache(isletme_id: str):
    """İşletme cache'ini temizle - Admin endpoint"""
    try:
        await cache_manager.invalidate_business_cache(isletme_id)
        return {"success": True, "message": f"Cache invalidated for business {isletme_id}"}
    except Exception as e:
        logger.error(f"Cache invalidation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache invalidation failed")

@app.post("/admin/cache/invalidate-product/{isletme_id}/{product_id}")
async def invalidate_product_cache(isletme_id: str, product_id: str):
    """Ürün cache'ini temizle - Admin endpoint"""
    try:
        await cache_manager.invalidate_product_cache(isletme_id, product_id)
        return {"success": True, "message": f"Product cache invalidated for {product_id}"}
    except Exception as e:
        logger.error(f"Product cache invalidation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Product cache invalidation failed")

@app.get("/admin/cache/stats/{isletme_id}")
async def get_cache_stats(isletme_id: str):
    """İşletme cache istatistikleri - Admin endpoint"""
    try:
        stats = await cache_manager.get_cache_stats(isletme_id)
        return stats
    except Exception as e:
        logger.error(f"Cache stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache stats unavailable")

# Product Management Endpoints (Cache invalidation ile)

class ProductUpdateRequest(BaseModel):
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

@app.put("/admin/products/{isletme_id}/{product_id}")
async def update_product(isletme_id: str, product_id: str, update_data: ProductUpdateRequest):
    """Ürün güncelle - Cache invalidation ile"""
    try:
        success = False
        
        if update_data.price is not None:
            success = await db_service.update_product_price(isletme_id, product_id, update_data.price)
        
        if update_data.stock_quantity is not None:
            success = await db_service.update_product_stock(isletme_id, product_id, update_data.stock_quantity)
        
        if success:
            return {"success": True, "message": "Product updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
            
    except Exception as e:
        logger.error(f"Product update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Product update failed")

class BusinessMetaUpdateRequest(BaseModel):
    info_type: str
    new_value: str

@app.put("/admin/business/{isletme_id}/meta")
async def update_business_meta(isletme_id: str, update_data: BusinessMetaUpdateRequest):
    """İşletme meta bilgisini güncelle - Cache invalidation ile"""
    try:
        success = await db_service.update_business_meta_info(
            isletme_id, 
            update_data.info_type, 
            update_data.new_value
        )
        
        if success:
            return {"success": True, "message": f"Business {update_data.info_type} updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Business not found")
            
    except Exception as e:
        logger.error(f"Business meta update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Business meta update failed")

# Learning and AI Improvement Endpoints

@app.post("/admin/learning/start")
async def start_learning():
    """Öğrenme döngüsünü başlat"""
    try:
        await learning_service.start_learning_loop()
        return {"success": True, "message": "Learning loop started"}
    except Exception as e:
        logger.error(f"Failed to start learning: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start learning")

@app.post("/admin/learning/stop")
async def stop_learning():
    """Öğrenme döngüsünü durdur"""
    try:
        await learning_service.stop_learning_loop()
        return {"success": True, "message": "Learning loop stopped"}
    except Exception as e:
        logger.error(f"Failed to stop learning: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop learning")

@app.get("/admin/learning/report")
async def get_learning_report():
    """Öğrenme raporu getir"""
    try:
        report = await learning_service.get_learning_report()
        return report
    except Exception as e:
        logger.error(f"Failed to get learning report: {str(e)}")
        raise HTTPException(status_code=500, detail="Learning report unavailable")

@app.get("/admin/learning/insights")
async def get_learning_insights():
    """LLM öğrenme içgörüleri"""
    try:
        insights = await llm_service.get_learning_insights()
        return insights
    except Exception as e:
        logger.error(f"Failed to get learning insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Learning insights unavailable")

@app.get("/admin/learning/export-training-data")
async def export_training_data():
    """Fine-tuning için training data export et"""
    try:
        training_data = await learning_service.export_fine_tuning_data()
        return training_data
    except Exception as e:
        logger.error(f"Failed to export training data: {str(e)}")
        raise HTTPException(status_code=500, detail="Training data export failed")

@app.get("/admin/model/info")
async def get_model_info():
    """Model bilgileri ve performans metrikleri"""
    try:
        model_info = await llm_service.get_model_info()
        return model_info
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail="Model info unavailable")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında çalışacak"""
    try:
        # Database bağlantısını başlat
        await db_service.initialize()
        
        # Learning service'i başlat
        await learning_service.start_learning_loop()
        
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanırken çalışacak"""
    try:
        # Learning service'i durdur
        await learning_service.stop_learning_loop()
        
        # Database bağlantısını kapat
        await db_service.close()
        
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)