"""
Enhanced Intent Detector Tests - Comprehensive test suite
"""

import pytest
import asyncio
from orchestrator.services.enhanced_intent_detector import (
    EnhancedIntentDetector, IntentType, ConfidenceLevel, Entity, IntentResult
)

class TestEnhancedIntentDetector:
    """Enhanced Intent Detector test sınıfı"""
    
    def setup_method(self):
        """Her test öncesi setup"""
        self.detector = EnhancedIntentDetector()
    
    @pytest.mark.asyncio
    async def test_empty_message(self):
        """Boş mesaj testi"""
        result = await self.detector.detect_intent("")
        assert result.intent == IntentType.CLARIFICATION_NEEDED
        assert result.confidence >= ConfidenceLevel.VERY_HIGH.value
        assert "Merhaba!" in result.response
        assert result.method == "empty_message"
    
    @pytest.mark.asyncio
    async def test_exact_patterns_greeting(self):
        """Kesin selamlama pattern testleri"""
        test_cases = ["merhaba", "selam", "hello", "hi"]
        
        for greeting in test_cases:
            result = await self.detector.detect_intent(greeting)
            assert result.intent == IntentType.GREETING
            assert result.confidence >= ConfidenceLevel.VERY_HIGH.value
            assert "Butik Cemünay" in result.response
            assert result.method == "exact_pattern"
    
    @pytest.mark.asyncio
    async def test_exact_patterns_thanks(self):
        """Kesin teşekkür pattern testleri"""
        test_cases = ["teşekkürler", "teşekkür", "sağol", "thanks"]
        
        for thanks in test_cases:
            result = await self.detector.detect_intent(thanks)
            assert result.intent == IntentType.THANKS
            assert result.confidence >= ConfidenceLevel.VERY_HIGH.value
            assert "Rica ederim" in result.response
            assert result.method == "exact_pattern"
    
    @pytest.mark.asyncio
    async def test_exact_patterns_farewell(self):
        """Kesin vedalaşma pattern testleri"""
        test_cases = ["hoşça kal", "güle güle", "görüşürüz", "bye"]
        
        for farewell in test_cases:
            result = await self.detector.detect_intent(farewell)
            assert result.intent == IntentType.FAREWELL
            assert result.confidence >= ConfidenceLevel.VERY_HIGH.value
            assert "Hoşça kalın" in result.response
            assert result.method == "exact_pattern"
    
    @pytest.mark.asyncio
    async def test_nonsense_detection(self):
        """Anlamsız sorgu tespiti"""
        test_cases = [
            "fiyat sorcaktım",
            "fiyat sroacaktım", 
            "annen",
            "asdfgh",
            "123456"
        ]
        
        for nonsense in test_cases:
            result = await self.detector.detect_intent(nonsense)
            assert result.intent == IntentType.CLARIFICATION_NEEDED
            assert result.confidence >= ConfidenceLevel.VERY_HIGH.value
            assert "Anlayamadım" in result.response
            assert result.method == "nonsense_detection"
    
    @pytest.mark.asyncio
    async def test_business_info_detection(self):
        """İşletme bilgi sorgu tespiti"""
        test_cases = [
            ("telefon", "telefon"),
            ("phone numaranız", "telefon"),
            ("iade var mı", "iade"),
            ("iade policy", "iade"),
            ("kargo ücreti", "kargo"),
            ("website", "site")
        ]
        
        for query, expected_info_type in test_cases:
            result = await self.detector.detect_intent(query)
            assert result.intent == IntentType.BUSINESS_INFO
            assert result.confidence >= ConfidenceLevel.HIGH.value
            assert result.function_call is not None
            assert result.function_call["name"] == "getGeneralInfo"
            assert result.function_call["args"]["info_type"] == expected_info_type
            assert result.method == "business_pattern"
    
    @pytest.mark.asyncio
    async def test_product_query_with_both_query_and_name(self):
        """Hem sorgu türü hem ürün adı olan sorgular"""
        test_cases = [
            "siyah gecelik fiyatı",
            "hamile pijama stok var mı",
            "dantelli sabahlık ne kadar",
            "afrika gecelik renkleri"
        ]
        
        for query in test_cases:
            result = await self.detector.detect_intent(query)
            assert result.intent == IntentType.PRODUCT_INQUIRY
            assert result.confidence >= ConfidenceLevel.HIGH.value
            assert result.method == "product_pattern"
            assert len(result.entities) > 0
    
    @pytest.mark.asyncio
    async def test_product_query_name_only(self):
        """Sadece ürün adı olan sorgular"""
        test_cases = [
            "siyah gecelik",
            "hamile pijama",
            "dantelli sabahlık",
            "afrika gecelik"
        ]
        
        for query in test_cases:
            result = await self.detector.detect_intent(query)
            assert result.intent == IntentType.PRODUCT_INQUIRY
            assert result.confidence >= ConfidenceLevel.MEDIUM.value
            assert result.method == "product_name_only"
            assert len(result.entities) > 0
    
    @pytest.mark.asyncio
    async def test_incomplete_query_single_word(self):
        """Tek kelime eksik sorgular"""
        test_cases = ["fiyat", "stok", "renk", "beden"]
        
        for query_word in test_cases:
            result = await self.detector.detect_intent(query_word)
            assert result.intent == IntentType.CLARIFICATION_NEEDED
            assert result.confidence >= ConfidenceLevel.HIGH.value
            assert f"Hangi ürünün {query_word}" in result.response
            assert result.method == "incomplete_query"
    
    @pytest.mark.asyncio
    async def test_short_messages(self):
        """Kısa mesaj işleme"""
        test_cases = ["ne var", "bilgi", "yardım"]
        
        for short_msg in test_cases:
            result = await self.detector.detect_intent(short_msg)
            assert result.intent == IntentType.CLARIFICATION_NEEDED
            assert result.confidence >= ConfidenceLevel.MEDIUM.value
            assert "Tam olarak ne hakkında" in result.response
            assert result.method == "short_message"
    
    @pytest.mark.asyncio
    async def test_complex_query_needs_llm(self):
        """Karmaşık sorgular - LLM gerekli"""
        test_cases = [
            "Bu ürünün kalitesi nasıl ve hangi malzemeden yapılmış",
            "Hamile kadınlar için en uygun model hangisi",
            "Kış aylarında giyilebilecek sıcak tutan modeller"
        ]
        
        for complex_query in test_cases:
            result = await self.detector.detect_intent(complex_query)
            assert result.intent == IntentType.NEEDS_LLM
            assert result.requires_llm == True
            assert result.method == "needs_llm"
            assert len(result.entities) >= 0  # May have some entities
    
    @pytest.mark.asyncio
    async def test_entity_extraction_colors(self):
        """Renk entity extraction"""
        query = "siyah ve beyaz gecelik var mı"
        result = await self.detector.detect_intent(query)
        
        color_entities = [e for e in result.entities if e.type == "color"]
        assert len(color_entities) >= 2
        
        color_values = [e.value for e in color_entities]
        assert "siyah" in color_values
        assert "beyaz" in color_values
    
    @pytest.mark.asyncio
    async def test_entity_extraction_features(self):
        """Özellik entity extraction"""
        query = "dantelli düğmeli dekolteli gecelik"
        result = await self.detector.detect_intent(query)
        
        feature_entities = [e for e in result.entities if e.type == "feature"]
        assert len(feature_entities) >= 3
        
        feature_values = [e.value for e in feature_entities]
        assert "dantelli" in feature_values
        assert "düğmeli" in feature_values
        assert "dekolteli" in feature_values
    
    @pytest.mark.asyncio
    async def test_context_management(self):
        """Context yönetimi testleri"""
        session_id = "test_session_123"
        
        # Context güncelle
        self.detector.update_context(session_id, {"last_product": "siyah gecelik"})
        
        # Context'i al
        context = self.detector.get_context(session_id)
        assert context["last_product"] == "siyah gecelik"
        
        # Contextual query test et
        result = await self.detector.detect_intent("bunun fiyatı ne", session_id)
        assert result.intent == IntentType.PRODUCT_INQUIRY
        assert result.method == "contextual_query"
        assert result.context["referenced_product"] == "siyah gecelik"
        
        # Context temizle
        self.detector.clear_context(session_id)
        context = self.detector.get_context(session_id)
        assert context == {}
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self):
        """Confidence hesaplama testleri"""
        # Yüksek confidence
        matches_high = [("exact_match", 1.0), ("pattern_match", 0.9)]
        confidence_high = self.detector.calculate_confidence(matches_high)
        assert confidence_high >= 0.9
        
        # Orta confidence
        matches_medium = [("partial_match", 0.6), ("weak_match", 0.4)]
        confidence_medium = self.detector.calculate_confidence(matches_medium)
        assert 0.4 <= confidence_medium <= 0.7
        
        # Boş matches
        confidence_empty = self.detector.calculate_confidence([])
        assert confidence_empty == 0.0
    
    @pytest.mark.asyncio
    async def test_business_info_vs_product_query_disambiguation(self):
        """İşletme bilgisi vs ürün sorgusu ayrımı"""
        # Sadece işletme bilgisi
        result1 = await self.detector.detect_intent("telefon numaranız")
        assert result1.intent == IntentType.BUSINESS_INFO
        
        # İşletme bilgisi + ürün adı = ürün sorgusu olmalı
        result2 = await self.detector.detect_intent("siyah gecelik telefon ile sipariş")
        # Bu durumda ürün sorgusu olarak algılanmalı çünkü ürün adı var
        assert result2.intent == IntentType.PRODUCT_INQUIRY
    
    @pytest.mark.asyncio
    async def test_turkish_specific_patterns(self):
        """Türkçe-specific pattern testleri"""
        turkish_queries = [
            "geceliği ne kadar",  # Türkçe ek
            "pijamayı görebilir miyim",  # Türkçe ek
            "sabahlığın fiyatı",  # Türkçe ek
            "takımı var mı"  # Türkçe ek
        ]
        
        for query in turkish_queries:
            result = await self.detector.detect_intent(query)
            assert result.intent == IntentType.PRODUCT_INQUIRY
            assert result.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self):
        """Büyük/küçük harf duyarsızlığı"""
        test_cases = [
            ("MERHABA", IntentType.GREETING),
            ("Siyah Gecelik", IntentType.PRODUCT_INQUIRY),
            ("TELEFON", IntentType.BUSINESS_INFO),
            ("FİYAT", IntentType.CLARIFICATION_NEEDED)
        ]
        
        for query, expected_intent in test_cases:
            result = await self.detector.detect_intent(query)
            assert result.intent == expected_intent
    
    def test_intent_result_structure(self):
        """IntentResult yapısı testi"""
        # Örnek bir IntentResult oluştur
        result = IntentResult(
            intent=IntentType.PRODUCT_INQUIRY,
            confidence=0.85,
            entities=[Entity("product", "gecelik", 0.9, 0, 7)],
            context={"test": True},
            requires_llm=False,
            function_call=None,
            response="Test response",
            method="test_method",
            explanation="Test explanation"
        )
        
        # Tüm alanların doğru tipte olduğunu kontrol et
        assert isinstance(result.intent, IntentType)
        assert isinstance(result.confidence, float)
        assert isinstance(result.entities, list)
        assert isinstance(result.context, dict)
        assert isinstance(result.requires_llm, bool)
        assert isinstance(result.response, str)
        assert isinstance(result.method, str)
        assert isinstance(result.explanation, str)

if __name__ == "__main__":
    pytest.main([__file__])