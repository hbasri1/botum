"""
General Info Function Handler - getGeneralInfo function'ı için handler
"""

import logging
from typing import Dict, Any, Optional
from orchestrator.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class GeneralInfoFunctionHandler:
    """General info function handler sınıfı"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.response_templates = {
            "telefon": "Telefon numaramız: {phone}",
            "iade": "İade politikamız: {iade_policy}",
            "kargo": "Kargo bilgilerimiz: {shipping_info}",
            "site": "Web sitemiz: {site}"
        }
    
    async def handle_general_info(self, info_type: str, business_id: str) -> Dict[str, Any]:
        """
        General info query'sini handle et
        
        Args:
            info_type: Bilgi türü (telefon, iade, kargo, site)
            business_id: İşletme ID
            
        Returns:
            Dict: Handler sonucu
        """
        try:
            # İşletme bilgisini veritabanından al
            info_value = await self.db_service.get_business_info(business_id, info_type)
            
            if not info_value:
                return {
                    "success": False,
                    "error": f"'{info_type}' bilgisi bulunamadı",
                    "response": f"Üzgünüm, {info_type} bilgisi şu anda mevcut değil."
                }
            
            # Response formatla
            return await self._format_info_response(info_type, info_value)
            
        except Exception as e:
            logger.error(f"General info handling error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "İşletme bilgisi alınırken bir hata oluştu."
            }
    
    async def _format_info_response(self, info_type: str, info_value: str) -> Dict[str, Any]:
        """
        İşletme bilgisini formatla
        
        Args:
            info_type: Bilgi türü
            info_value: Bilgi değeri
            
        Returns:
            Dict: Formatlanmış response
        """
        try:
            # Template'e göre formatla
            template = self.response_templates.get(info_type, "{info_value}")
            
            if info_type == "telefon":
                response = f"Telefon numaramız: {info_value}"
            elif info_type == "iade":
                response = f"İade politikamız: {info_value}"
            elif info_type == "kargo":
                response = f"Kargo bilgilerimiz: {info_value}"
            elif info_type == "site":
                response = f"Web sitemiz: {info_value}"
            else:
                response = f"{info_type.capitalize()}: {info_value}"
            
            return {
                "success": True,
                "info_type": info_type,
                "info_value": info_value,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Info response formatting error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Bilgi formatlanırken hata oluştu."
            }