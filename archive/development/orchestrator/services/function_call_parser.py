"""
Function Call Parser - Gemini function calling yanıtlarını parse etme ve doğrulama
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ValidationError
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(str, Enum):
    """Ürün sorgu türleri"""
    FIYAT = "fiyat"
    STOK = "stok"
    DETAY = "detay"
    RENK = "renk"
    BEDEN = "beden"

class InfoType(str, Enum):
    """Genel bilgi türleri"""
    TELEFON = "telefon"
    ADRES = "adres"
    IADE = "iade"
    KARGO = "kargo"
    ODEME = "ödeme"

class ProductInfoArgs(BaseModel):
    """getProductInfo fonksiyon argümanları"""
    product_name: str = Field(..., min_length=1, max_length=100, description="Ürün adı")
    query_type: QueryType = Field(..., description="Sorgu türü")

class GeneralInfoArgs(BaseModel):
    """getGeneralInfo fonksiyon argümanları"""
    info_type: InfoType = Field(..., description="Bilgi türü")

class FunctionCall(BaseModel):
    """Function call modeli"""
    name: str = Field(..., description="Fonksiyon adı")
    arguments: Dict[str, Any] = Field(..., description="Fonksiyon argümanları")
    session_id: str = Field(..., description="Session ID")
    business_id: str = Field(..., description="İşletme ID")

class ParsedFunctionCall(BaseModel):
    """Parse edilmiş function call"""
    function_name: str
    validated_args: Dict[str, Any]
    session_id: str
    business_id: str
    success: bool = True
    error_message: Optional[str] = None

class FunctionCallParser:
    """Function call parsing ve validation sınıfı"""
    
    def __init__(self):
        self.supported_functions = {
            "getProductInfo": ProductInfoArgs,
            "getGeneralInfo": GeneralInfoArgs
        }
    
    async def parse_function_call(self, response, session_id: str, business_id: str) -> Optional[ParsedFunctionCall]:
        """
        Gemini yanıtından function call'ı parse et
        """
        try:
            if not response or not response.candidates:
                logger.warning("No candidates in Gemini response")
                return None
            
            candidate = response.candidates[0]
            
            if not candidate.content or not candidate.content.parts:
                logger.warning("No content parts in Gemini response")
                return None
            
            # Function call'ı ara
            for part in candidate.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    
                    # Function call bilgilerini çıkar
                    function_name = function_call.name
                    function_args = dict(function_call.args) if function_call.args else {}
                    
                    logger.info(f"Parsing function call: {function_name} with args: {function_args}")
                    
                    # Function call'ı validate et
                    validated_call = await self._validate_function_call(
                        function_name, function_args, session_id, business_id
                    )
                    
                    return validated_call
            
            logger.info("No function call found in response")
            return None
            
        except Exception as e:
            logger.error(f"Function call parse error: {str(e)}")
            return ParsedFunctionCall(
                function_name="unknown",
                validated_args={},
                session_id=session_id,
                business_id=business_id,
                success=False,
                error_message=f"Parse error: {str(e)}"
            )
    
    async def _validate_function_call(self, function_name: str, args: Dict[str, Any], 
                                    session_id: str, business_id: str) -> ParsedFunctionCall:
        """
        Function call argümanlarını validate et
        """
        try:
            # Desteklenen fonksiyon mu kontrol et
            if function_name not in self.supported_functions:
                return ParsedFunctionCall(
                    function_name=function_name,
                    validated_args=args,
                    session_id=session_id,
                    business_id=business_id,
                    success=False,
                    error_message=f"Unsupported function: {function_name}"
                )
            
            # Argümanları validate et
            validator_class = self.supported_functions[function_name]
            
            try:
                validated_args = validator_class(**args)
                
                return ParsedFunctionCall(
                    function_name=function_name,
                    validated_args=validated_args.dict(),
                    session_id=session_id,
                    business_id=business_id,
                    success=True
                )
                
            except ValidationError as ve:
                error_details = []
                for error in ve.errors():
                    field = error.get('loc', ['unknown'])[0]
                    message = error.get('msg', 'validation error')
                    error_details.append(f"{field}: {message}")
                
                error_message = f"Validation failed for {function_name}: {'; '.join(error_details)}"
                
                return ParsedFunctionCall(
                    function_name=function_name,
                    validated_args=args,
                    session_id=session_id,
                    business_id=business_id,
                    success=False,
                    error_message=error_message
                )
            
        except Exception as e:
            logger.error(f"Function validation error: {str(e)}")
            return ParsedFunctionCall(
                function_name=function_name,
                validated_args=args,
                session_id=session_id,
                business_id=business_id,
                success=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    def _validate_function_args(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fonksiyon argümanlarını schema'ya göre validate et
        """
        if function_name == "getProductInfo":
            return self._validate_product_info_args(args)
        elif function_name == "getGeneralInfo":
            return self._validate_general_info_args(args)
        else:
            raise ValueError(f"Unknown function: {function_name}")
    
    def _validate_product_info_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """getProductInfo argümanlarını validate et"""
        try:
            validated = ProductInfoArgs(**args)
            return validated.dict()
        except ValidationError as e:
            logger.error(f"ProductInfo validation error: {str(e)}")
            raise
    
    def _validate_general_info_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """getGeneralInfo argümanlarını validate et"""
        try:
            validated = GeneralInfoArgs(**args)
            return validated.dict()
        except ValidationError as e:
            logger.error(f"GeneralInfo validation error: {str(e)}")
            raise
    
    async def handle_parsing_error(self, error: Exception, session_id: str, 
                                 business_id: str) -> Dict[str, Any]:
        """
        Parsing hatalarını handle et
        """
        logger.error(f"Function call parsing failed for session {session_id}: {str(error)}")
        
        return {
            "type": "parsing_error",
            "error_message": str(error),
            "session_id": session_id,
            "business_id": business_id,
            "fallback_required": True,
            "timestamp": logger.time.time() if hasattr(logger, 'time') else None
        }
    
    async def handle_validation_error(self, function_name: str, args: Dict[str, Any], 
                                    validation_error: ValidationError, session_id: str, 
                                    business_id: str) -> Dict[str, Any]:
        """
        Validation hatalarını handle et
        """
        error_details = []
        for error in validation_error.errors():
            field = error.get('loc', ['unknown'])[0]
            message = error.get('msg', 'validation error')
            error_details.append(f"{field}: {message}")
        
        error_message = f"Function {function_name} validation failed: {'; '.join(error_details)}"
        
        logger.error(f"Function validation failed for session {session_id}: {error_message}")
        
        return {
            "type": "validation_error",
            "function_name": function_name,
            "provided_args": args,
            "error_message": error_message,
            "error_details": error_details,
            "session_id": session_id,
            "business_id": business_id,
            "fallback_required": True
        }
    
    def get_function_schema(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Fonksiyon schema'sını getir
        """
        if function_name not in self.supported_functions:
            return None
        
        validator_class = self.supported_functions[function_name]
        return validator_class.schema()
    
    def get_supported_functions(self) -> List[str]:
        """
        Desteklenen fonksiyonların listesini getir
        """
        return list(self.supported_functions.keys())
    
    async def extract_function_details(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Text response'dan function call detaylarını çıkarmaya çalış (fallback)
        """
        try:
            # JSON formatında function call arama
            if "function_call" in response_text.lower():
                # Basit regex ile function call çıkarma
                import re
                
                # Function name pattern
                name_pattern = r'"name":\s*"([^"]+)"'
                args_pattern = r'"arguments":\s*({[^}]+})'
                
                name_match = re.search(name_pattern, response_text)
                args_match = re.search(args_pattern, response_text)
                
                if name_match and args_match:
                    function_name = name_match.group(1)
                    args_json = args_match.group(1)
                    
                    try:
                        args = json.loads(args_json)
                        return {
                            "function_name": function_name,
                            "arguments": args,
                            "extracted_from_text": True
                        }
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse extracted function arguments")
            
            return None
            
        except Exception as e:
            logger.error(f"Function detail extraction error: {str(e)}")
            return None