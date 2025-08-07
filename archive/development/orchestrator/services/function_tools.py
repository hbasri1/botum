"""
Function Tools - Gemini function calling için araç tanımları
"""

from typing import List, Dict, Any

# Gemini function calling için araç tanımları
FUNCTION_TOOLS = [
    {
        "name": "getProductInfo",
        "description": "Ürün fiyat, stok, detay veya içerik bilgisi sorgular.",
        "parameters": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string", 
                    "description": "Niyet: 'fiyat', 'stok', 'ürün_detayı', 'içerik'.",
                    "enum": ["fiyat", "stok", "ürün_detayı", "içerik", "renk", "beden"]
                },
                "product_name": {
                    "type": "string", 
                    "description": "Ürünün adı."
                }
            },
            "required": ["query_type"]
        }
    },
    {
        "name": "getGeneralInfo",
        "description": "Şirketin iade, kargo, ödeme ve iletişim bilgilerini sorgular.",
        "parameters": {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string", 
                    "description": "Niyet: 'iade_politikasi', 'kargo_detaylari', 'odeme_secenekleri', 'telefon_numarasi', 'website'.",
                    "enum": ["iade_politikasi", "kargo_detaylari", "odeme_secenekleri", "telefon_numarasi", "website", "adres", "iletisim"]
                }
            },
            "required": ["info_type"]
        }
    }
]

def get_function_tools_definition() -> List[Dict[str, Any]]:
    """
    Gemini function calling için araç tanımlarını döndürür
    """
    return FUNCTION_TOOLS

def get_function_schema(function_name: str) -> Dict[str, Any]:
    """
    Belirli bir fonksiyon için şema tanımını döndürür
    """
    for tool in FUNCTION_TOOLS:
        if tool["name"] == function_name:
            return tool["parameters"]
    return {}