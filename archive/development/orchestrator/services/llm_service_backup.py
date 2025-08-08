"""
LLM Service - Fine-tuned Vertex AI Gemini ile iletişim
"""

import json
import requests
import time
import asyncio
from typing import Dict, Any, Optional, List, Union, Tuple
import logging
from pydantic import BaseModel, Field, ValidationError
import google.generativeai as genai
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Function calling imports
from .function_call_parser import FunctionCallParser

logger = logging.getLogger(__name__)

class LLMEntity(BaseModel):
    """LLM Entity modeli - Pydantic doğrulama için"""
    type: str = Field(..., description="Entity türü: product, attribute, value")
    value: str = Field(..., description="Entity değeri")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Entity güven skoru")

class LLMContext(BaseModel):
    """LLM Context modeli"""
    requires_followup: bool = Field(default=False)
    waiting_for: Optional[str] = None
    product_mentioned: Optional[str] = None
    attribute_requested: Optional[str] = None

class LLMResponse(BaseModel):
    """
    LLM yanıt modeli - Katı Pydantic doğrulama
    Bu model LLM'den dönen JSON'ı doğrulamak için kullanılır
    """
    session_id: str = Field(..., description="Session ID")
    isletme_id: str = Field(..., description="İşletme ID")
    intent: str = Field(..., description="Tespit edilen niyet")
    entities: List[LLMEntity] = Field(default=[], description="Çıkarılan entity'ler")
    context: LLMContext = Field(default_factory=LLMContext, description="Konuşma bağlamı")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Genel güven skoru")
    language: str = Field(default="tr", description="Dil kodu")
    
    class Config:
        extra = "forbid"  # Ekstra alanları kabul etme

class LLMService:
    def __init__(self, project_id: str = None, location: str = "us-central1", 
                 model_name: str = None, credentials_path: str = None,
                 enable_function_calling: bool = True):
        self.project_id = project_id or "cobalt-anchor-466417-j0"
        self.location = location
        self.model_name = model_name or "gemini-2.0-flash-exp"  # En gelişmiş model
        self.credentials_path = credentials_path or "credentials.json"
        
        # Function calling configuration
        self.enable_function_calling = enable_function_calling
        self.function_calling_model = "gemini-1.5-flash-latest"  # Function calling için model
        self.function_calling_temperature = 0.1
        
        self.max_retries = 3
        self.timeout = 30
        
        # Öğrenme ve gelişim için
        self.conversation_memory = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_confidence": 0.0,
            "intent_accuracy": {},
            "function_calls": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "by_function": {}
            },
            "fallback_to_intent": 0
        }
        
        # Google AI Studio API key ile başlat
        self._initialize_gemini()
        
        # Fallback handler'ı başlat
        self.fallback_handler = None  # Lazy initialization
    
    def _initialize_gemini(self):
        """Gemini API'yi başlat"""
        try:
            # Service account ile authentication
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # API key almak için token al
            credentials.refresh(Request())
            
            # Gemini'yi yapılandır
            genai.configure(api_key=self._get_api_key_from_credentials())
            
            # Model'i başlat
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json"
                }
            )
            
            # Function calling için model başlat
            self.function_model = genai.GenerativeModel(
                model_name=self.function_calling_model,
                generation_config={
                    "temperature": self.function_calling_temperature,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            logger.info(f"Gemini {self.model_name} initialized successfully")
            logger.info(f"Gemini function model {self.function_calling_model} initialized successfully")
            
        except Exception as e:
            logger.error(f"Gemini initialization error: {str(e)}")
            # Fallback: Doğrudan API key ile
            self._initialize_with_api_key()
    
    def _initialize_fallback_handler(self):
        """Fallback handler'ı lazy initialization ile başlat"""
        if not self.fallback_handler:
            from .function_call_fallback import FunctionCallFallback
            self.fallback_handler = FunctionCallFallback(self)
    
    def _get_api_key_from_credentials(self) -> str:
        """Service account'tan API key türet (basitleştirilmiş)"""
        # Bu gerçek implementasyonda OAuth2 flow ile yapılmalı
        # Şimdilik environment variable veya direct API key kullanacağız
        import os
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            # Geçici çözüm: Google AI Studio'dan alınan API key
            api_key = "your-gemini-api-key-here"  # Placeholder
        return api_key
    
    def _initialize_with_api_key(self):
        """API key ile direkt başlatma"""
        try:
            import os
            api_key = os.getenv('GEMINI_API_KEY', 'your-api-key-here')
            genai.configure(api_key=api_key)
            
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            # Function calling için model başlat
            self.function_model = genai.GenerativeModel(
                model_name=self.function_calling_model,
                generation_config={
                    "temperature": self.function_calling_temperature,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            logger.info("Gemini initialized with API key")
            
        except Exception as e:
            logger.error(f"API key initialization failed: {str(e)}")
            # Son çare: Mock mode
            self.model = None
            self.function_model = None
            logger.warning("LLM running in mock mode")
    
    async def process_message_with_functions(self, prompt: str, session_id: str, 
                                           isletme_id: str) -> Optional[Dict[str, Any]]:
        """
        Function calling ile mesaj işle - Ana entry point
        Seamless transition ile fallback sağlar
        """
        if not self.enable_function_calling:
            return await self.process_message(prompt, session_id, isletme_id)
        
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["function_calls"]["total"] += 1
        
        try:
            # Function calling ile Gemini'yi çağır
            start_time = time.time()
            response = await self._call_gemini_with_functions(prompt, session_id, isletme_id)
            execution_time = int((time.time() - start_time) * 1000)  # ms
            
            if response:
                # Function calling başarılı
                self.performance_metrics["successful_requests"] += 1
                self.performance_metrics["function_calls"]["successful"] += 1
                
                # Response'a metadata ekle
                response["method"] = "function_calling"
                response["execution_time_ms"] = execution_time
                response["fallback_used"] = False
                
                # Performance comparison logla
                await self._log_performance_comparison(
                    prompt, session_id, isletme_id, response, "function_calling_successful"
                )
                
                return response
            else:
                # Function calling başarısız - seamless fallback
                logger.warning(f"Function calling failed, seamlessly falling back to intent detection for session {session_id}")
                return await self._ensure_seamless_transition(
                    None, prompt, session_id, isletme_id, "function_call_failed"
                )
                
        except Exception as e:
            logger.error(f"Function calling error: {str(e)}")
            self.performance_metrics["failed_requests"] += 1
            self.performance_metrics["function_calls"]["failed"] += 1
            
            # Hata durumunda seamless fallback
            return await self._ensure_seamless_transition(
                None, prompt, session_id, isletme_id, "function_calling_error"
            )
    
    async def _ensure_seamless_transition(self, function_result: Optional[Dict[str, Any]], 
                                        prompt: str, session_id: str, 
                                        isletme_id: str, reason: str) -> Optional[Dict[str, Any]]:
        """
        Function calling ve intent detection arasında seamless transition sağla
        API değişikliği olmadan fallback yapar
        
        Args:
            function_result: Function calling sonucu
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            reason: Fallback sebebi
            
        Returns:
            Dict: Seamless transition sonucu
        """
        try:
            if function_result:
                # Function calling başarılı
                return function_result
            else:
                # Function calling başarısız, fallback yap
                self._initialize_fallback_handler()
                
                result = await self.fallback_handler.ensure_seamless_transition(
                    function_result, prompt, session_id, isletme_id
                )
                
                if result:
                    # Fallback başarılı
                    self.performance_metrics["fallback_to_intent"] += 1
                    
                    # Performance comparison logla
                    await self._log_performance_comparison(
                        prompt, session_id, isletme_id, result, "seamless_fallback", reason
                    )
                    
                    logger.info(f"Seamless transition successful for session {session_id}")
                    return result
                else:
                    logger.error(f"Seamless transition failed for session {session_id}")
                    return None
            
        except Exception as e:
            logger.error(f"Seamless transition error: {str(e)}")
            # Son çare olarak traditional intent detection
            return await self.process_message(prompt, session_id, isletme_id)

    async def process_message(self, prompt: str, session_id: str, 
                            isletme_id: str) -> Optional[Dict[str, Any]]:
        """
        LLM'e mesaj gönder ve yapısal yanıt al
        Kendi kendine öğrenme ve gelişim dahil
        """
        
        self.performance_metrics["total_requests"] += 1
        
        for attempt in range(self.max_retries):
            try:
                # Gemini'ye istek gönder
                response = await self._call_gemini(prompt, session_id, isletme_id)
                
                if response:
                    # JSON parse et ve doğrula
                    parsed_response = self._parse_llm_response(response)
                    
                    if parsed_response:
                        # Başarılı yanıt - öğrenme verisi olarak kaydet
                        await self._record_successful_interaction(
                            prompt, parsed_response, session_id, isletme_id
                        )
                        
                        self.performance_metrics["successful_requests"] += 1
                        
                        logger.info(f"LLM response parsed successfully for session {session_id}")
                        return parsed_response
                
                logger.warning(f"LLM attempt {attempt + 1} failed for session {session_id}")
                
            except Exception as e:
                logger.error(f"LLM error attempt {attempt + 1}: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Başarısız istek
        self.performance_metrics["failed_requests"] += 1
        await self._record_failed_interaction(prompt, session_id, isletme_id)
        
        logger.error(f"LLM failed after {self.max_retries} attempts for session {session_id}")
        return None
    
    async def _call_gemini_with_functions(self, prompt: str, session_id: str, 
                                        isletme_id: str) -> Optional[Dict[str, Any]]:
        """Gemini'yi function calling ile çağır"""
        try:
            if not self.model:
                # Mock mode - test için
                return await self._mock_function_response(prompt, session_id, isletme_id)
            
            # Function tools tanımını al
            tools = self._get_function_tools_definition()
            
            # Function calling için özel model oluştur
            function_model = genai.GenerativeModel(
                model_name=self.function_calling_model,
                generation_config={
                    "temperature": self.function_calling_temperature,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                },
                tools=tools
            )
            
            # Prompt'u formatla
            formatted_prompt = self._format_function_prompt(prompt, session_id, isletme_id)
            
            # Gemini'ye istek gönder
            response = await asyncio.to_thread(
                function_model.generate_content, formatted_prompt
            )
            
            if response and response.candidates:
                # Function call'ları parse et
                return await self._parse_function_response(response, session_id, isletme_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini function call error: {str(e)}")
            return None
    
    async def _fallback_to_intent_detection(self, prompt: str, session_id: str, 
                                          isletme_id: str, reason: str = "unknown") -> Optional[Dict[str, Any]]:
        """
        Traditional intent detection'a fallback yap
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            reason: Fallback sebebi
            
        Returns:
            Dict: Intent detection yanıtı veya None
        """
        try:
            # Fallback handler'ı lazy initialize et
            self._initialize_fallback_handler()
            
            # Fallback istatistiklerini güncelle
            self.performance_metrics["fallback_to_intent"] += 1
            
            # Fallback handler'ı kullan
            result = await self.fallback_handler.fallback_to_intent_detection(
                prompt, session_id, isletme_id, reason
            )
            
            if result:
                # Performance comparison logla
                await self._log_performance_comparison(
                    prompt, session_id, isletme_id, result, "fallback_successful", reason
                )
                
                logger.info(f"Fallback successful for session {session_id}")
                return result
            else:
                logger.error(f"Fallback failed for session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Fallback error: {str(e)}")
            return None
    
    async def _log_performance_comparison(self, prompt: str, session_id: str, 
                                        isletme_id: str, result: Dict[str, Any],
                                        comparison_type: str, reason: str = None) -> None:
        """
        Performance comparison logla
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            result: Sonuç
            comparison_type: Karşılaştırma türü
            reason: Fallback sebebi
        """
        try:
            log_data = {
                "timestamp": time.time(),
                "session_id": session_id,
                "isletme_id": isletme_id,
                "user_message": prompt,
                "comparison_type": comparison_type,
                "method": result.get("method", "unknown"),
                "execution_time_ms": result.get("execution_time_ms", 0),
                "success": result is not None,
                "fallback_reason": reason,
                "confidence": result.get("confidence", 0) if result else 0
            }
            
            # TODO: Veritabanına performance comparison verilerini kaydet
            # Şimdilik sadece log
            logger.info(f"Performance comparison: {comparison_type} - {log_data['method']} - {log_data['execution_time_ms']}ms")
            
        except Exception as e:
            logger.error(f"Performance comparison logging error: {str(e)}")
    
    def _get_function_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Function calling için tools tanımını getir
        
        Returns:
            List: Function tools tanımları
        """
        try:
            tools = [
                {
                    "function_declarations": [
                        {
                            "name": "getProductInfo",
                            "description": "Ürün bilgilerini getir (fiyat, stok, detaylar)",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "product_name": {
                                        "type": "string",
                                        "description": "Ürün adı"
                                    },
                                    "query_type": {
                                        "type": "string",
                                        "enum": ["fiyat", "stok", "detay", "all"],
                                        "description": "Sorgu türü"
                                    }
                                },
                                "required": ["product_name"]
                            }
                        },
                        {
                            "name": "getGeneralInfo",
                            "description": "Genel işletme bilgilerini getir (iletişim, iade, kargo vb.)",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "info_type": {
                                        "type": "string",
                                        "enum": ["iletişim", "iade", "kargo", "ödeme", "genel"],
                                        "description": "Bilgi türü"
                                    }
                                },
                                "required": ["info_type"]
                            }
                        }
                    ]
                }
            ]
            
            return tools
            
        except Exception as e:
            logger.error(f"Function tools definition error: {str(e)}")
            return []
    
    def _format_function_prompt(self, prompt: str, session_id: str, isletme_id: str) -> str:
        """
        Function calling için prompt formatla
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            str: Formatlanmış prompt
        """
        try:
            formatted_prompt = f"""Sen Türkiye pazarındaki KOBİ'ler için özelleştirilmiş bir müşteri hizmetleri AI asistanısın.

## GÖREV
Gelen müşteri mesajlarını analiz et ve uygun function'ları çağır.

## KURALLAR
1. Ürün sorguları için getProductInfo function'ını kullan
2. Genel bilgi sorguları için getGeneralInfo function'ını kullan
3. Belirsiz durumlarda kullanıcıdan açıklama iste
4. Her zaman Türkçe yanıt ver

## BAĞLAM
Session ID: {session_id}
İşletme ID: {isletme_id}

## KULLANICI MESAJI
{prompt}

Lütfen uygun function'ı çağır veya doğrudan yanıt ver."""
            
            return formatted_prompt
            
        except Exception as e:
            logger.error(f"Function prompt formatting error: {str(e)}")
            return prompt
    
    async def _parse_function_response(self, response, session_id: str, 
                                     isletme_id: str) -> Optional[Dict[str, Any]]:
        """
        Function calling response'unu parse et
        
        Args:
            response: Gemini response
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Dict: Parse edilmiş response
        """
        try:
            # Function call parser'ı lazy initialize et
            if not hasattr(self, 'function_parser'):
                self.function_parser = FunctionCallParser()
            
            # Response'u parse et
            parsed_response = await self.function_parser.parse_function_response(
                response, session_id, isletme_id
            )
            
            # Function execution coordinator'a yönlendir
            if parsed_response and "function_call" in parsed_response:
                function_name = parsed_response["function_call"].get("name")
                arguments = parsed_response["function_call"].get("args", {})
                
                # Function execution coordinator'ı lazy initialize et
                if not hasattr(self, 'function_executor'):
                    from .function_execution_coordinator import FunctionExecutionCoordinator
                    from .database_service import DatabaseService
                    from .function_cache_manager import FunctionCacheManager
                    
                    # Dependency'leri initialize et
                    db_service = DatabaseService()
                    cache_manager = FunctionCacheManager()
                    await cache_manager.initialize()
                    
                    self.function_executor = FunctionExecutionCoordinator(db_service, cache_manager)
                
                # Function'ı execute et (cache kontrolü dahil)
                execution_result = await self.function_executor.execute_function_call(
                    function_name, arguments, session_id, isletme_id
                )
                
                # Execution sonucunu parsed_response'a ekle
                if execution_result:
                    parsed_response["execution_result"] = execution_result
                    
                    # Cache bilgisini ekle
                    if "cached" in execution_result:
                        parsed_response["cached"] = execution_result["cached"]
                    
                    # Execution time'ı ekle
                    if "execution_time_ms" in execution_result:
                        parsed_response["execution_time_ms"] = execution_result["execution_time_ms"]
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Function response parsing error: {str(e)}")
            return None
    
    async def _mock_function_response(self, prompt: str, session_id: str, 
                                    isletme_id: str) -> Optional[Dict[str, Any]]:
        """
        Mock function calling response - test için
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Dict: Mock response
        """
        try:
            message = prompt.lower()
            
            # Ürün fiyat sorgusu
            if any(word in message for word in ["fiyat", "kaç para", "ne kadar"]):
                if "gecelik" in message:
                    return {
                        "session_id": session_id,
                        "isletme_id": isletme_id,
                        "function_call": {
                            "name": "getProductInfo",
                            "args": {
                                "product_name": "gecelik",
                                "query_type": "fiyat"
                            }
                        },
                        "method": "function_calling",
                        "confidence": 0.9,
                        "language": "tr"
                    }
            
            # Genel bilgi sorgusu
            elif any(word in message for word in ["iletişim", "telefon", "adres"]):
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "function_call": {
                        "name": "getGeneralInfo",
                        "args": {
                            "info_type": "iletişim"
                        }
                    },
                    "method": "function_calling",
                    "confidence": 0.85,
                    "language": "tr"
                }
            
            # Function calling uygun değil - None döndür (fallback'e geçer)
            return None
            
        except Exception as e:
            logger.error(f"Mock function response error: {str(e)}")
            return None

    async def _call_gemini(self, prompt: str, session_id: str, 
                         isletme_id: str) -> Optional[str]:
        """Gemini 2.5 Pro model'ini çağır"""
        try:
            if not self.model:
                # Mock mode - test için
                return await self._mock_response(prompt, session_id, isletme_id)
            
            # Prompt'u formatla
            formatted_prompt = self._format_prompt_for_gemini(
                prompt, session_id, isletme_id
            )
            
            # Gemini'ye istek gönder
            response = await asyncio.to_thread(
                self.model.generate_content, formatted_prompt
            )
            
            if response and response.text:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini call error: {str(e)}")
            # Fallback to mock
            return await self._mock_response(prompt, session_id, isletme_id)
    
    async def _mock_response(self, prompt: str, session_id: str, isletme_id: str) -> str:
        """Mock LLM yanıtı - test ve geliştirme için"""
        message = prompt.lower()
        
        # Selamlama
        if any(word in message for word in ["merhaba", "selam", "hey"]):
            return json.dumps({
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "greeting",
                "entities": [],
                "context": {"requires_followup": False},
                "confidence": 0.95,
                "language": "tr"
            }, ensure_ascii=False)
        
        # Ürün fiyat sorgusu
        elif any(word in message for word in ["fiyat", "kaç para", "ne kadar"]):
            if "gecelik" in message:
                return json.dumps({
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_query",
                    "entities": [
                        {"type": "product", "value": "gecelik", "confidence": 0.9},
                        {"type": "attribute", "value": "fiyat", "confidence": 0.95}
                    ],
                    "context": {"product_mentioned": "gecelik"},
                    "confidence": 0.88,
                    "language": "tr"
                }, ensure_ascii=False)
            else:
                # Belirsiz ürün - düşük güven
                return json.dumps({
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "product_query",
                    "entities": [],
                    "context": {"requires_followup": True},
                    "confidence": 0.65,  # Düşük güven - eskalasyon
                    "language": "tr"
                }, ensure_ascii=False)
        
        # Şikayet
        elif any(word in message for word in ["şikayet", "problem", "sorun"]):
            return json.dumps({
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "sikayet_bildirme",
                "entities": [],
                "context": {"requires_followup": True},
                "confidence": 0.92,
                "language": "tr"
            }, ensure_ascii=False)
        
        # Bilinmeyen
        else:
            return json.dumps({
                "session_id": session_id,
                "isletme_id": isletme_id,
                "intent": "unknown",
                "entities": [],
                "context": {},
                "confidence": 0.45,  # Düşük güven - eskalasyon
                "language": "tr"
            }, ensure_ascii=False)
    
    def _format_prompt_for_gemini(self, prompt: str, session_id: str, 
                                isletme_id: str) -> str:
        """Gemini 2.5 Pro için gelişmiş prompt formatla"""
        
        # Konuşma geçmişini dahil et
        conversation_context = self._get_conversation_context(session_id)
        
        # Öğrenme verilerini dahil et
        learning_examples = self._get_learning_examples()
        
        formatted_prompt = f"""Sen Türkiye pazarındaki KOBİ'ler için özelleştirilmiş bir müşteri hizmetleri AI asistanısın.

## GÖREV
Gelen müşteri mesajlarını analiz et ve yapısal JSON yanıt üret.

## KURALLAR
1. Sadece anladığın konularda yüksek güven skoru ver (>0.80)
2. Belirsiz durumlarda düşük güven skoru ver (<0.80) - bu eskalasyona yol açar
3. Şikayet, problem gibi hassas konularda "sikayet_bildirme" intent'i kullan
4. Asla tahmin yürütme, emin olmadığın durumda düşük güven skoru ver

## BAĞLAM
Session ID: {session_id}
İşletme ID: {isletme_id}
Konuşma Geçmişi: {conversation_context}

## ÖĞRENME ÖRNEKLERİ
{learning_examples}

## KULLANICI MESAJI
{prompt}

## BEKLENEN YANIT FORMATI
Lütfen aşağıdaki JSON formatında yanıt ver:
{{
    "session_id": "{session_id}",
    "isletme_id": "{isletme_id}",
    "intent": "greeting|thanks|meta_query|product_query|clarify|contact|sikayet_bildirme|unknown",
    "entities": [
        {{
            "type": "product|attribute|value",
            "value": "çıkarılan_değer",
            "confidence": 0.95
        }}
    ],
    "context": {{
        "requires_followup": false,
        "waiting_for": null,
        "product_mentioned": null,
        "attribute_requested": null
    }},
    "confidence": 0.95,
    "language": "tr",
    "reasoning": "Kısa açıklama"
}}

YANIT:"""
        
        return formatted_prompt
    
    def _get_conversation_context(self, session_id: str) -> str:
        """Session için konuşma bağlamını getir"""
        # Son 3 etkileşimi al
        recent_conversations = [
            conv for conv in self.conversation_memory 
            if conv.get("session_id") == session_id
        ][-3:]
        
        if not recent_conversations:
            return "Yeni konuşma"
        
        context_parts = []
        for conv in recent_conversations:
            context_parts.append(f"Kullanıcı: {conv.get('user_message', '')}")
            context_parts.append(f"Intent: {conv.get('intent', '')}")
        
        return " | ".join(context_parts)
    
    def _get_learning_examples(self) -> str:
        """Öğrenme örneklerini getir"""
        examples = [
            {
                "input": "merhaba",
                "output": {"intent": "greeting", "confidence": 0.95},
                "explanation": "Açık selamlama"
            },
            {
                "input": "gecelik fiyatı ne kadar?",
                "output": {"intent": "product_query", "confidence": 0.88},
                "explanation": "Belirli ürün fiyat sorgusu"
            },
            {
                "input": "bu şeyin fiyatı ne kadar?",
                "output": {"intent": "product_query", "confidence": 0.65},
                "explanation": "Belirsiz ürün - düşük güven"
            },
            {
                "input": "şikayet etmek istiyorum",
                "output": {"intent": "sikayet_bildirme", "confidence": 0.92},
                "explanation": "Şikayet - eskalasyon gerekli"
            }
        ]
        
        example_text = "ÖRNEKLER:\n"
        for ex in examples:
            example_text += f"- '{ex['input']}' → {ex['output']} ({ex['explanation']})\n"
        
        return example_text
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        LLM yanıtını parse et - Pydantic ile katı doğrulama
        """
        try:
            # JSON'u temizle
            cleaned_response = response_text.strip()
            
            # Markdown kod bloklarını kaldır
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # JSON parse et
            parsed_json = json.loads(cleaned_response)
            
            # Pydantic ile doğrula - ÇOK ÖNEMLİ
            try:
                validated_response = LLMResponse(**parsed_json)
                logger.info(f"LLM response validated successfully with confidence: {validated_response.confidence}")
                
                # Dict'e çevir
                return validated_response.dict()
                
            except ValidationError as ve:
                logger.error(f"Pydantic validation failed: {str(ve)}")
                logger.error(f"Raw response: {cleaned_response}")
                
                # Validation hatası = anlaşılmadı = eskalasyon
                return None
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            logger.error(f"Raw response: {response_text}")
            
            # JSON hatası = anlaşılmadı = eskalasyon
            return None
        
        except Exception as e:
            logger.error(f"Response parse error: {str(e)}")
            return None
    
    def _fallback_parse(self, response_text: str) -> Optional[Dict[str, Any]]:
        """JSON parse başarısız olursa fallback parsing"""
        try:
            import re
            
            # Temel intent'i çıkarmaya çalış
            intent_patterns = {
                "greeting": r"(merhaba|selam|hey|selamlar)",
                "thanks": r"(teşekkür|sağol|tamam|peki)",
                "meta_query": r"(telefon|iade|kargo|adres|ödeme)",
                "product_query": r"(fiyat|stok|renk|beden|ürün)",
                "clarify": r"(hangi|ne|nedir|nasıl)",
                "contact": r"(iletişim|yardım|destek)"
            }
            
            detected_intent = "unknown"
            for intent, pattern in intent_patterns.items():
                if re.search(pattern, response_text.lower()):
                    detected_intent = intent
                    break
            
            return {
                "session_id": "unknown",
                "isletme_id": "unknown", 
                "intent": detected_intent,
                "entities": [],
                "context": {
                    "requires_followup": False,
                    "waiting_for": None
                },
                "confidence": 0.5,
                "language": "tr",
                "fallback_parsed": True
            }
            
        except Exception as e:
            logger.error(f"Fallback parse error: {str(e)}")
            return None
    
    async def health_check(self) -> bool:
        """LLM servis sağlık kontrolü"""
        try:
            # Basit bir test mesajı gönder
            test_response = await self._call_vertex_ai(
                "[session: test] [kimlik: test] merhaba", 
                "test_session", 
                "test_business"
            )
            
            return test_response is not None
            
        except Exception as e:
            logger.error(f"LLM health check failed: {str(e)}")
            return False
    
    async def _record_successful_interaction(self, prompt: str, response: Dict[str, Any], 
                                           session_id: str, isletme_id: str):
        """Başarılı etkileşimi öğrenme verisi olarak kaydet"""
        try:
            interaction_data = {
                "timestamp": time.time(),
                "session_id": session_id,
                "isletme_id": isletme_id,
                "user_message": prompt,
                "intent": response.get("intent"),
                "confidence": response.get("confidence", 0),
                "entities": response.get("entities", []),
                "success": True
            }
            
            # Memory'ye ekle (son 1000 etkileşimi tut)
            self.conversation_memory.append(interaction_data)
            if len(self.conversation_memory) > 1000:
                self.conversation_memory.pop(0)
            
            # Intent accuracy'yi güncelle
            intent = response.get("intent", "unknown")
            if intent not in self.performance_metrics["intent_accuracy"]:
                self.performance_metrics["intent_accuracy"][intent] = {"correct": 0, "total": 0}
            
            self.performance_metrics["intent_accuracy"][intent]["total"] += 1
            
            # Confidence ortalamasını güncelle
            total_requests = self.performance_metrics["total_requests"]
            current_avg = self.performance_metrics["average_confidence"]
            new_confidence = response.get("confidence", 0)
            
            self.performance_metrics["average_confidence"] = (
                (current_avg * (total_requests - 1) + new_confidence) / total_requests
            )
            
            logger.debug(f"Recorded successful interaction: {intent} (confidence: {new_confidence})")
            
        except Exception as e:
            logger.error(f"Failed to record successful interaction: {str(e)}")
    
    async def _record_failed_interaction(self, prompt: str, session_id: str, isletme_id: str):
        """Başarısız etkileşimi kaydet"""
        try:
            interaction_data = {
                "timestamp": time.time(),
                "session_id": session_id,
                "isletme_id": isletme_id,
                "user_message": prompt,
                "success": False,
                "error": "LLM processing failed"
            }
            
            self.conversation_memory.append(interaction_data)
            if len(self.conversation_memory) > 1000:
                self.conversation_memory.pop(0)
            
            logger.warning(f"Recorded failed interaction for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to record failed interaction: {str(e)}")
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Öğrenme içgörülerini getir"""
        try:
            total_interactions = len(self.conversation_memory)
            successful_interactions = len([i for i in self.conversation_memory if i.get("success", False)])
            
            # Intent dağılımı
            intent_distribution = {}
            confidence_by_intent = {}
            
            for interaction in self.conversation_memory:
                if interaction.get("success", False):
                    intent = interaction.get("intent", "unknown")
                    confidence = interaction.get("confidence", 0)
                    
                    if intent not in intent_distribution:
                        intent_distribution[intent] = 0
                        confidence_by_intent[intent] = []
                    
                    intent_distribution[intent] += 1
                    confidence_by_intent[intent].append(confidence)
            
            # Ortalama confidence'ları hesapla
            avg_confidence_by_intent = {}
            for intent, confidences in confidence_by_intent.items():
                avg_confidence_by_intent[intent] = sum(confidences) / len(confidences)
            
            # Düşük performanslı intent'leri tespit et
            low_performance_intents = [
                intent for intent, avg_conf in avg_confidence_by_intent.items()
                if avg_conf < 0.75
            ]
            
            return {
                "total_interactions": total_interactions,
                "successful_interactions": successful_interactions,
                "success_rate": successful_interactions / total_interactions if total_interactions > 0 else 0,
                "intent_distribution": intent_distribution,
                "average_confidence_by_intent": avg_confidence_by_intent,
                "low_performance_intents": low_performance_intents,
                "overall_metrics": self.performance_metrics,
                "recommendations": self._generate_improvement_recommendations(
                    intent_distribution, avg_confidence_by_intent, low_performance_intents
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get learning insights: {str(e)}")
            return {"error": str(e)}
    
    def _generate_improvement_recommendations(self, intent_dist: Dict, avg_conf: Dict, 
                                           low_perf: List) -> List[str]:
        """Gelişim önerileri üret"""
        recommendations = []
        
        # Düşük performanslı intent'ler için öneriler
        if low_perf:
            recommendations.append(
                f"Düşük performanslı intent'ler tespit edildi: {', '.join(low_perf)}. "
                f"Bu intent'ler için daha fazla training verisi gerekli."
            )
        
        # En sık kullanılan intent'ler
        if intent_dist:
            most_common = max(intent_dist.items(), key=lambda x: x[1])
            recommendations.append(
                f"En sık kullanılan intent: {most_common[0]} ({most_common[1]} kez). "
                f"Bu intent için optimizasyon öncelikli."
            )
        
        # Genel confidence durumu
        overall_avg = self.performance_metrics.get("average_confidence", 0)
        if overall_avg < 0.80:
            recommendations.append(
                f"Genel confidence ortalaması düşük ({overall_avg:.2f}). "
                f"Model fine-tuning'e ihtiyaç duyuyor."
            )
        elif overall_avg > 0.90:
            recommendations.append(
                f"Genel confidence ortalaması yüksek ({overall_avg:.2f}). "
                f"Model iyi performans gösteriyor."
            )
        
        return recommendations
    
    async def export_training_data(self) -> Dict[str, Any]:
        """Fine-tuning için training verisi export et"""
        try:
            training_examples = []
            
            for interaction in self.conversation_memory:
                if interaction.get("success", False) and interaction.get("confidence", 0) > 0.85:
                    # Yüksek confidence'lı başarılı etkileşimleri training verisi olarak kullan
                    example = {
                        "input": interaction.get("user_message", ""),
                        "output": {
                            "intent": interaction.get("intent"),
                            "entities": interaction.get("entities", []),
                            "confidence": interaction.get("confidence")
                        },
                        "metadata": {
                            "session_id": interaction.get("session_id"),
                            "isletme_id": interaction.get("isletme_id"),
                            "timestamp": interaction.get("timestamp")
                        }
                    }
                    training_examples.append(example)
            
            return {
                "training_examples": training_examples,
                "total_examples": len(training_examples),
                "export_timestamp": time.time(),
                "model_version": self.model_name,
                "quality_threshold": 0.85
            }
            
        except Exception as e:
            logger.error(f"Failed to export training data: {str(e)}")
            return {"error": str(e)}
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Model bilgilerini getir"""
        try:
            return {
                "project_id": self.project_id,
                "location": self.location,
                "model_name": self.model_name,
                "status": "active" if self.model else "mock_mode",
                "max_retries": self.max_retries,
                "timeout": self.timeout,
                "performance_metrics": self.performance_metrics,
                "memory_size": len(self.conversation_memory)
            }
        except Exception as e:
            logger.error(f"Model info error: {str(e)}")
            return {"error": str(e)}
    
    def _get_function_tools_definition(self) -> List[Dict[str, Any]]:
        """Function calling için mevcut fonksiyonları tanımla"""
        return [
            {
                "function_declarations": [
                    {
                        "name": "getProductInfo",
                        "description": "Ürün bilgilerini getir (fiyat, stok, özellikler)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "product_name": {
                                    "type": "string",
                                    "description": "Ürün adı (gecelik, pijama, etc.)"
                                },
                                "query_type": {
                                    "type": "string",
                                    "enum": ["fiyat", "stok", "detay", "renk", "beden"],
                                    "description": "Sorgu türü"
                                }
                            },
                            "required": ["product_name", "query_type"]
                        }
                    },
                    {
                        "name": "getGeneralInfo",
                        "description": "İşletme genel bilgilerini getir (telefon, adres, iade, kargo)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "info_type": {
                                    "type": "string",
                                    "enum": ["telefon", "adres", "iade", "kargo", "ödeme"],
                                    "description": "Bilgi türü"
                                }
                            },
                            "required": ["info_type"]
                        }
                    }
                ]
            }
        ]
    
    def _format_function_prompt(self, prompt: str, session_id: str, isletme_id: str) -> str:
        """Function calling için prompt formatla"""
        return f"""Sen bir müşteri hizmetleri asistanısın. Kullanıcının sorusunu analiz et ve uygun fonksiyonu çağır.

Kullanıcı mesajı: {prompt}
Session ID: {session_id}
İşletme ID: {isletme_id}

Eğer kullanıcı:
- Ürün fiyatı, stoğu veya detayları soruyorsa -> getProductInfo fonksiyonunu kullan
- İşletme bilgileri (telefon, adres, iade, kargo) soruyorsa -> getGeneralInfo fonksiyonunu kullan

Fonksiyon çağırırken parametreleri doğru şekilde belirle."""
    
    async def _parse_function_response(self, response, session_id: str, isletme_id: str) -> Optional[Dict[str, Any]]:
        """Gemini function calling yanıtını parse et"""
        try:
            candidate = response.candidates[0]
            
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        function_call = part.function_call
                        
                        # Function call bilgilerini çıkar
                        function_name = function_call.name
                        function_args = dict(function_call.args)
                        
                        logger.info(f"Function call detected: {function_name} with args: {function_args}")
                        
                        # Function call'ı execute et (bu başka bir serviste yapılacak)
                        return {
                            "type": "function_call",
                            "function_name": function_name,
                            "function_args": function_args,
                            "session_id": session_id,
                            "isletme_id": isletme_id,
                            "success": True
                        }
            
            # Function call yoksa normal text response
            if candidate.content.parts and candidate.content.parts[0].text:
                return {
                    "type": "text_response",
                    "text": candidate.content.parts[0].text,
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "success": True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Function response parse error: {str(e)}")
            return None
    
    async def _fallback_to_intent_detection(self, prompt: str, session_id: str, isletme_id: str) -> Optional[Dict[str, Any]]:
        """Function calling başarısız olursa intent detection'a geri dön"""
        logger.info(f"Falling back to intent detection for session {session_id}")
        self.performance_metrics["fallback_to_intent"] += 1
        
        # Mevcut process_message metodunu kullan
        result = await self.process_message(prompt, session_id, isletme_id)
        
        if result:
            result["fallback_used"] = True
            
        return result
    
    async def _mock_function_response(self, prompt: str, session_id: str, isletme_id: str) -> Dict[str, Any]:
        """Mock function calling yanıtı - test için"""
        message = prompt.lower()
        
        # Ürün sorguları
        if any(word in message for word in ["fiyat", "kaç para", "ne kadar"]):
            if "gecelik" in message:
                return {
                    "type": "function_call",
                    "function_name": "getProductInfo",
                    "function_args": {
                        "product_name": "gecelik",
                        "query_type": "fiyat"
                    },
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "success": True
                }
        
        # Genel bilgi sorguları
        elif any(word in message for word in ["telefon", "iletişim"]):
            return {
                "type": "function_call",
                "function_name": "getGeneralInfo",
                "function_args": {
                    "info_type": "telefon"
                },
                "session_id": session_id,
                "isletme_id": isletme_id,
                "success": True
            }
        
        # Fallback to text response
        return {
            "type": "text_response",
            "text": "Üzgünüm, sorunuzu anlayamadım. Lütfen daha açık bir şekilde sorabilir misiniz?",
            "session_id": session_id,
            "isletme_id": isletme_id,
            "success": True
        }
    
    async def process_message_with_functions(self, prompt: str, session_id: str, 
                                          isletme_id: str) -> Optional[Dict[str, Any]]:
        """
        LLM'e mesaj gönder ve function calling ile yapısal yanıt al
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Dict: LLM yanıtı veya None
        """
        if not self.function_calling_enabled:
            # Function calling devre dışıysa normal süreci kullan
            logger.info("Function calling disabled, using traditional intent detection")
            return await self.process_message(prompt, session_id, isletme_id)
        
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["function_calls"]["total"] += 1
        
        for attempt in range(self.max_retries):
            try:
                # Gemini'ye function calling ile istek gönder
                start_time = time.time()
                response = await self._call_gemini_with_functions(prompt, session_id, isletme_id)
                execution_time = int((time.time() - start_time) * 1000)  # ms cinsinden
                
                if response:
                    # Function call'ı parse et
                    function_call = await self._parse_function_call(response)
                    
                    if function_call:
                        # Function call başarılı
                        function_name = function_call.get("function_name")
                        arguments = function_call.get("arguments", {})
                        
                        # Function call'ı execute et
                        function_result = await self._execute_function_call(
                            function_name, arguments, session_id, isletme_id, execution_time
                        )
                        
                        # Başarılı yanıt - öğrenme verisi olarak kaydet
                        await self._record_successful_function_call(
                            prompt, function_name, arguments, function_result, 
                            session_id, isletme_id, execution_time
                        )
                        
                        self.performance_metrics["successful_requests"] += 1
                        self.performance_metrics["function_calls"]["successful"] += 1
                        
                        # Function bazlı metrikleri güncelle
                        if function_name not in self.performance_metrics["function_calls"]["by_function"]:
                            self.performance_metrics["function_calls"]["by_function"][function_name] = {
                                "total": 0, "successful": 0, "failed": 0
                            }
                        
                        self.performance_metrics["function_calls"]["by_function"][function_name]["total"] += 1
                        self.performance_metrics["function_calls"]["by_function"][function_name]["successful"] += 1
                        
                        logger.info(f"Function call successful: {function_name} for session {session_id}")
                        
                        # Intent detection formatına dönüştür (geriye uyumluluk için)
                        return self._convert_function_result_to_intent_format(
                            function_name, arguments, function_result, session_id, isletme_id
                        )
                
                logger.warning(f"Function calling attempt {attempt + 1} failed for session {session_id}")
                
                # Son deneme başarısız olduysa fallback yap
                if attempt == self.max_retries - 1:
                    logger.warning(f"All function calling attempts failed, falling back to intent detection")
                    return await self._fallback_to_intent_detection(prompt, session_id, isletme_id)
                
            except Exception as e:
                logger.error(f"Function calling error attempt {attempt + 1}: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Başarısız istek
        self.performance_metrics["failed_requests"] += 1
        self.performance_metrics["function_calls"]["failed"] += 1
        await self._record_failed_interaction(prompt, session_id, isletme_id)
        
        # Fallback to traditional intent detection
        logger.error(f"Function calling failed after {self.max_retries} attempts, falling back to intent detection")
        return await self._fallback_to_intent_detection(prompt, session_id, isletme_id)
    
    async def _call_gemini_with_functions(self, prompt: str, session_id: str, 
                                       isletme_id: str) -> Optional[Any]:
        """
        Gemini'yi function calling ile çağır
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Any: Gemini yanıtı veya None
        """
        try:
            if not self.function_model:
                # Mock mode - test için
                return await self._mock_function_call(prompt, session_id, isletme_id)
            
            # Prompt'u formatla
            formatted_prompt = self._format_prompt_for_function_calling(
                prompt, session_id, isletme_id
            )
            
            # Function tools tanımlarını al
            tools = get_function_tools_definition()
            
            # Gemini'ye istek gönder
            response = await asyncio.to_thread(
                self.function_model.generate_content,
                formatted_prompt,
                tools=tools,
                tool_config={"function_calling_config": {"mode": "AUTO"}}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Gemini function calling error: {str(e)}")
            # Fallback to mock
            return await self._mock_function_call(prompt, session_id, isletme_id)
    
    async def _mock_function_call(self, prompt: str, session_id: str, isletme_id: str) -> Any:
        """
        Mock function call yanıtı - test ve geliştirme için
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Any: Mock function call yanıtı
        """
        message = prompt.lower()
        
        # Mock response class
        class MockResponse:
            def __init__(self, function_name, args):
                self.candidates = [MockCandidate(function_name, args)]
        
        class MockCandidate:
            def __init__(self, function_name, args):
                self.content = MockContent(function_name, args)
        
        class MockContent:
            def __init__(self, function_name, args):
                self.parts = [MockPart(function_name, args)]
        
        class MockPart:
            def __init__(self, function_name, args):
                self.function_call = MockFunctionCall(function_name, args)
        
        class MockFunctionCall:
            def __init__(self, function_name, args):
                self.name = function_name
                self.args = args
        
        # Ürün fiyat sorgusu
        if any(word in message for word in ["fiyat", "kaç para", "ne kadar"]):
            if "gecelik" in message:
                return MockResponse("getProductInfo", {
                    "query_type": "fiyat",
                    "product_name": "gecelik"
                })
            elif "elbise" in message:
                return MockResponse("getProductInfo", {
                    "query_type": "fiyat",
                    "product_name": "elbise"
                })
            else:
                # Belirsiz ürün
                return MockResponse("getProductInfo", {
                    "query_type": "fiyat"
                })
        
        # Ürün stok sorgusu
        elif any(word in message for word in ["stok", "var mı", "mevcut"]):
            if "pijama" in message:
                return MockResponse("getProductInfo", {
                    "query_type": "stok",
                    "product_name": "pijama"
                })
            else:
                return MockResponse("getProductInfo", {
                    "query_type": "stok"
                })
        
        # Genel bilgi sorguları
        elif any(word in message for word in ["iade", "değişim"]):
            return MockResponse("getGeneralInfo", {
                "info_type": "iade_politikasi"
            })
        elif any(word in message for word in ["kargo", "teslimat"]):
            return MockResponse("getGeneralInfo", {
                "info_type": "kargo_detaylari"
            })
        elif any(word in message for word in ["telefon", "numara", "iletişim"]):
            return MockResponse("getGeneralInfo", {
                "info_type": "telefon_numarasi"
            })
        
        # Bilinmeyen - fallback
        else:
            # Function call yapılamadı, None döndür
            return None
    
    def _format_prompt_for_function_calling(self, prompt: str, session_id: str, 
                                         isletme_id: str) -> str:
        """
        Gemini function calling için prompt formatla
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            str: Formatlanmış prompt
        """
        # Konuşma geçmişini dahil et
        conversation_context = self._get_conversation_context(session_id)
        
        formatted_prompt = f"""Sen Türkiye pazarındaki KOBİ'ler için özelleştirilmiş bir müşteri hizmetleri AI asistanısın.

## GÖREV
Gelen müşteri mesajlarını analiz et ve uygun fonksiyonu çağır.

## KURALLAR
1. Ürün bilgisi sorularında getProductInfo fonksiyonunu kullan
2. Genel şirket bilgisi sorularında getGeneralInfo fonksiyonunu kullan
3. Ürün adı belirtilmemişse, query_type'ı belirt ama product_name parametresini boş bırak
4. Emin olmadığın durumlarda fonksiyon çağırma, normal yanıt ver

## BAĞLAM
Session ID: {session_id}
İşletme ID: {isletme_id}
Konuşma Geçmişi: {conversation_context}

## KULLANICI MESAJI
{prompt}

## BEKLENEN YANIT
Lütfen uygun fonksiyonu çağır veya normal yanıt ver.
"""
        
        return formatted_prompt
    
    async def _parse_function_call(self, response) -> Optional[Dict[str, Any]]:
        """
        Gemini function call yanıtını parse et
        
        Args:
            response: Gemini yanıtı
            
        Returns:
            Dict: Parsed function call veya None
        """
        try:
            parser = FunctionCallParser()
            return parser.parse_function_call(response)
        except Exception as e:
            logger.error(f"Function call parsing error: {str(e)}")
            return None
    
    async def _execute_function_call(self, function_name: str, arguments: Dict, 
                                  session_id: str, isletme_id: str, 
                                  execution_time: int) -> str:
        """
        Function call'ı execute et
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            session_id: Session ID
            isletme_id: İşletme ID
            execution_time: Execution time (ms)
            
        Returns:
            str: Fonksiyon yanıtı
        """
        try:
            # Parametreleri validate et
            parser = FunctionCallParser()
            validation_result = parser.validate_function_call(function_name, arguments)
            
            if not validation_result["success"]:
                logger.error(f"Function validation failed: {validation_result['error_message']}")
                return f"Validation error: {validation_result['error_message']}"
            
            # Parametreleri sanitize et
            sanitized_args = parser.sanitize_function_arguments(arguments)
            
            # TODO: Gerçek function handler'ları implement et
            # Şimdilik mock yanıtlar
            
            # Function call'ı logla
            await self._log_function_call(
                function_name, sanitized_args, session_id, isletme_id, 
                execution_time, True, None
            )
            
            # Mock yanıtlar
            if function_name == "getProductInfo":
                return await self._mock_product_info_response(sanitized_args, isletme_id)
            elif function_name == "getGeneralInfo":
                return await self._mock_general_info_response(sanitized_args, isletme_id)
            else:
                return f"Unsupported function: {function_name}"
            
        except Exception as e:
            logger.error(f"Function execution error: {str(e)}")
            
            # Hatayı logla
            await self._log_function_call(
                function_name, arguments, session_id, isletme_id, 
                execution_time, False, str(e)
            )
            
            return f"Function execution error: {str(e)}"
    
    async def _mock_product_info_response(self, args: Dict, isletme_id: str) -> str:
        """
        Mock product info yanıtı
        
        Args:
            args: Fonksiyon parametreleri
            isletme_id: İşletme ID
            
        Returns:
            str: Mock yanıt
        """
        query_type = args.get("query_type")
        product_name = args.get("product_name")
        
        if not product_name:
            if query_type == "fiyat":
                return "Hangi ürünün fiyatını öğrenmek istiyorsunuz?"
            elif query_type == "stok":
                return "Hangi ürünün stok durumunu kontrol etmek istiyorsunuz?"
            else:
                return "Hangi ürün hakkında bilgi almak istiyorsunuz?"
        
        # Mock ürün bilgileri
        products = {
            "gecelik": {
                "fiyat": "299 TL",
                "stok": "Stokta mevcut (10 adet)",
                "ürün_detayı": "Saten kumaş, siyah renk, S/M/L bedenleri mevcut",
                "içerik": "%100 polyester"
            },
            "pijama": {
                "fiyat": "199 TL",
                "stok": "Son 2 adet kaldı",
                "ürün_detayı": "Pamuklu kumaş, mavi renk, M/L bedenleri mevcut",
                "içerik": "%95 pamuk, %5 elastan"
            },
            "elbise": {
                "fiyat": "399 TL",
                "stok": "Stokta mevcut (5 adet)",
                "ürün_detayı": "Şifon kumaş, kırmızı renk, S/M bedenleri mevcut",
                "içerik": "%100 polyester"
            }
        }
        
        # Ürün bilgisini döndür
        if product_name in products:
            if query_type in products[product_name]:
                return f"{product_name.capitalize()}: {products[product_name][query_type]}"
            else:
                return f"{product_name.capitalize()} için {query_type} bilgisi mevcut değil."
        else:
            return f"'{product_name}' ürünü bulunamadı. Mevcut ürünlerimiz: gecelik, pijama, elbise."
    
    async def _mock_general_info_response(self, args: Dict, isletme_id: str) -> str:
        """
        Mock general info yanıtı
        
        Args:
            args: Fonksiyon parametreleri
            isletme_id: İşletme ID
            
        Returns:
            str: Mock yanıt
        """
        info_type = args.get("info_type")
        
        # Mock şirket bilgileri
        info = {
            "iade_politikasi": "14 gün içinde koşulsuz iade hakkınız bulunmaktadır.",
            "kargo_detaylari": "Kargo ücretsiz, 1-3 iş günü içinde teslim.",
            "odeme_secenekleri": "Kredi kartı, havale/EFT ve kapıda ödeme seçenekleri mevcuttur.",
            "telefon_numarasi": "0555 555 55 55",
            "website": "www.testbutik.com",
            "adres": "Test Mahallesi, Test Sokak No:1, İstanbul",
            "iletisim": "Telefon: 0555 555 55 55, E-posta: info@testbutik.com"
        }
        
        if info_type in info:
            return info[info_type]
        else:
            return f"'{info_type}' hakkında bilgi şu anda mevcut değil."
    
    async def _log_function_call(self, function_name: str, arguments: Dict, 
                              session_id: str, isletme_id: str, execution_time: int,
                              success: bool, error_message: Optional[str]) -> None:
        """
        Function call'ı logla
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            session_id: Session ID
            isletme_id: İşletme ID
            execution_time: Execution time (ms)
            success: Başarılı mı?
            error_message: Hata mesajı
        """
        try:
            # TODO: Veritabanına logla
            # Şimdilik sadece log
            log_message = (
                f"Function call: {function_name}, "
                f"Args: {json.dumps(arguments)}, "
                f"Session: {session_id}, "
                f"Business: {isletme_id}, "
                f"Time: {execution_time}ms, "
                f"Success: {success}"
            )
            
            if error_message:
                log_message += f", Error: {error_message}"
            
            if success:
                logger.info(log_message)
            else:
                logger.error(log_message)
            
        except Exception as e:
            logger.error(f"Function call logging error: {str(e)}")
    
    async def _record_successful_function_call(self, prompt: str, function_name: str, 
                                            arguments: Dict, result: str, 
                                            session_id: str, isletme_id: str,
                                            execution_time: int) -> None:
        """
        Başarılı function call'ı kaydet
        
        Args:
            prompt: Kullanıcı mesajı
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            result: Fonksiyon yanıtı
            session_id: Session ID
            isletme_id: İşletme ID
            execution_time: Execution time (ms)
        """
        try:
            interaction_data = {
                "timestamp": time.time(),
                "session_id": session_id,
                "isletme_id": isletme_id,
                "user_message": prompt,
                "function_name": function_name,
                "arguments": arguments,
                "result": result,
                "execution_time_ms": execution_time,
                "success": True
            }
            
            # Memory'ye ekle (son 1000 etkileşimi tut)
            self.conversation_memory.append(interaction_data)
            if len(self.conversation_memory) > 1000:
                self.conversation_memory.pop(0)
            
            logger.debug(f"Recorded successful function call: {function_name}")
            
        except Exception as e:
            logger.error(f"Failed to record successful function call: {str(e)}")
    
    async def _fallback_to_intent_detection(self, prompt: str, session_id: str, 
                                         isletme_id: str) -> Optional[Dict[str, Any]]:
        """
        Intent detection'a fallback yap
        
        Args:
            prompt: Kullanıcı mesajı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Dict: Intent detection yanıtı veya None
        """
        logger.info(f"Falling back to intent detection for session {session_id}")
        
        # Mevcut process_message metodunu çağır
        return await self.process_message(prompt, session_id, isletme_id)
    
    def _convert_function_result_to_intent_format(self, function_name: str, arguments: Dict, 
                                               result: str, session_id: str, 
                                               isletme_id: str) -> Dict[str, Any]:
        """
        Function call sonucunu intent detection formatına dönüştür
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            result: Fonksiyon yanıtı
            session_id: Session ID
            isletme_id: İşletme ID
            
        Returns:
            Dict: Intent detection formatında yanıt
        """
        # Intent ve entity'leri belirle
        intent = "unknown"
        entities = []
        context = {}
        confidence = 0.95  # Function calling için yüksek confidence
        
        if function_name == "getProductInfo":
            intent = "product_query"
            query_type = arguments.get("query_type")
            product_name = arguments.get("product_name")
            
            if product_name:
                entities.append({
                    "type": "product",
                    "value": product_name,
                    "confidence": 0.95
                })
            
            if query_type:
                entities.append({
                    "type": "attribute",
                    "value": query_type,
                    "confidence": 0.95
                })
            
            context = {
                "product_mentioned": product_name,
                "attribute_requested": query_type,
                "requires_followup": not product_name  # Ürün adı yoksa followup gerekli
            }
            
        elif function_name == "getGeneralInfo":
            intent = "meta_query"
            info_type = arguments.get("info_type")
            
            if info_type:
                entities.append({
                    "type": "attribute",
                    "value": info_type,
                    "confidence": 0.95
                })
            
            context = {
                "attribute_requested": info_type,
                "requires_followup": False
            }
        
        # Intent detection formatında yanıt döndür
        return {
            "session_id": session_id,
            "isletme_id": isletme_id,
            "intent": intent,
            "entities": entities,
            "context": context,
            "confidence": confidence,
            "language": "tr",
            "function_call_result": result,  # Ek bilgi olarak function call sonucunu da ekle
            "function_call_used": True  # Function call kullanıldığını belirt
        } 
   async def _call_gemini_with_functions(self, prompt: str, session_id: str, 
                                        isletme_id: str) -> Optional[Dict[str, Any]]:
        """Gemini'yi function calling ile çağır"""
        try:
            if not self.model:
                # Mock mode için fallback
                return await self.fallback_handler.fallback_to_intent_detection(
                    prompt, session_id, isletme_id, "mock_mode"
                )
            
            # Function tools tanımını al
            tools = get_function_tools_definition()
            
            # Function calling için özel model oluştur
            function_model = genai.GenerativeModel(
                model_name=self.function_calling_model,
                tools=tools,
                generation_config={
                    "temperature": self.function_calling_temperature,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            # Prompt'u formatla
            formatted_prompt = self._format_function_calling_prompt(prompt, session_id, isletme_id)
            
            # Gemini'ye function calling ile istek gönder
            response = await asyncio.to_thread(
                function_model.generate_content, formatted_prompt
            )
            
            if response and response.candidates:
                candidate = response.candidates[0]
                
                # Function call var mı kontrol et
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            # Function call bulundu
                            return await self._handle_function_call(
                                part.function_call, session_id, isletme_id, prompt
                            )
                
                # Function call yok, normal text response
                if candidate.content.parts and candidate.content.parts[0].text:
                    # Traditional parsing'e fallback
                    return await self.fallback_handler.fallback_to_intent_detection(
                        prompt, session_id, isletme_id, "no_function_call"
                    )
            
            # Hiçbir yanıt yok
            return await self.fallback_handler.fallback_to_intent_detection(
                prompt, session_id, isletme_id, "no_response"
            )
            
        except Exception as e:
            logger.error(f"Function calling error: {str(e)}")
            return await self.fallback_handler.fallback_to_intent_detection(
                prompt, session_id, isletme_id, "function_calling_exception"
            )
    
    def _format_function_calling_prompt(self, prompt: str, session_id: str, isletme_id: str) -> str:
        """Function calling için prompt formatla"""
        return f"""Sen bir müşteri hizmetleri asistanısın. Kullanıcının sorusunu analiz et ve uygun function'ı çağır.

Kullanılabilir function'lar:
1. getProductInfo - Ürün bilgileri için (fiyat, stok, detay, renk, beden)
2. getGeneralInfo - İşletme bilgileri için (telefon, adres, iade, kargo, ödeme)

Kullanıcı mesajı: {prompt}

Eğer kullanıcı ürün hakkında soru soruyorsa getProductInfo function'ını kullan.
Eğer işletme bilgisi soruyorsa getGeneralInfo function'ını kullan.
Eğer belirsizse veya function call gerektirmiyorsa normal yanıt ver."""
    
    async def _handle_function_call(self, function_call, session_id: str, 
                                  isletme_id: str, original_prompt: str) -> Dict[str, Any]:
        """Function call'ı işle"""
        try:
            function_name = function_call.name
            function_args = dict(function_call.args)
            
            # Function call'ı validate et
            validation_result = self.function_parser.validate_function_call(function_name, function_args)
            
            if not validation_result["success"]:
                logger.error(f"Function validation failed: {validation_result['error_message']}")
                return await self.fallback_handler.fallback_to_intent_detection(
                    original_prompt, session_id, isletme_id, "validation_failed"
                )
            
            # Parametreleri sanitize et
            sanitized_args = self.function_parser.sanitize_function_arguments(function_args)
            
            # Function'ı execute et (şimdilik mock)
            if function_name == "getProductInfo":
                result = await self._mock_product_function(sanitized_args, isletme_id)
            elif function_name == "getGeneralInfo":
                result = await self._mock_general_info_function(sanitized_args, isletme_id)
            else:
                # Bilinmeyen function
                return await self.fallback_handler.fallback_to_intent_detection(
                    original_prompt, session_id, isletme_id, "unknown_function"
                )
            
            if result:
                # Function call başarılı - structured response döndür
                return {
                    "session_id": session_id,
                    "isletme_id": isletme_id,
                    "intent": "function_call_success",
                    "function_name": function_name,
                    "function_args": sanitized_args,
                    "function_result": result,
                    "final_response": result.get("response", ""),
                    "confidence": 0.95,
                    "language": "tr",
                    "method": "function_calling"
                }
            else:
                # Function call başarısız
                return await self.fallback_handler.fallback_to_intent_detection(
                    original_prompt, session_id, isletme_id, "function_execution_failed"
                )
                
        except Exception as e:
            logger.error(f"Function call handling error: {str(e)}")
            return await self.fallback_handler.fallback_to_intent_detection(
                original_prompt, session_id, isletme_id, "function_handling_error"
            )
    
    async def _mock_product_function(self, args: Dict[str, Any], isletme_id: str) -> Optional[Dict[str, Any]]:
        """Mock product function - gerçek implementasyon sonra gelecek"""
        product_name = args.get("product_name", "").lower()
        query_type = args.get("query_type", "")
        
        # Mock data
        if "gecelik" in product_name:
            if query_type == "fiyat":
                return {
                    "product_name": "Test Gecelik",
                    "price": 299.99,
                    "response": "Test Gecelik fiyatı 299.99 TL'dir."
                }
            elif query_type == "stok":
                return {
                    "product_name": "Test Gecelik",
                    "stock": 10,
                    "response": "Test Gecelik stokta mevcut (10 adet)."
                }
        
        return None
    
    async def _mock_general_info_function(self, args: Dict[str, Any], isletme_id: str) -> Optional[Dict[str, Any]]:
        """Mock general info function - gerçek implementasyon sonra gelecek"""
        info_type = args.get("info_type", "")
        
        # Mock data
        if info_type == "telefon":
            return {
                "info_type": "telefon",
                "value": "0555 555 55 55",
                "response": "Telefon numaramız: 0555 555 55 55"
            }
        elif info_type == "iade":
            return {
                "info_type": "iade",
                "value": "14 gün içinde iade yapılabilir",
                "response": "İade politikamız: 14 gün içinde iade yapılabilir."
            }
        
        return None