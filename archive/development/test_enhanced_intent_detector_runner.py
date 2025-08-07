#!/usr/bin/env python3
"""
Enhanced Intent Detector Test Runner - Pytest olmadan test çalıştırma
"""

import asyncio
import sys
import traceback
from orchestrator.services.enhanced_intent_detector import (
    EnhancedIntentDetector, IntentType, ConfidenceLevel
)

class TestRunner:
    def __init__(self):
        self.detector = EnhancedIntentDetector()
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_equal(self, actual, expected, message=""):
        if actual != expected:
            raise AssertionError(f"{message}: Expected {expected}, got {actual}")
    
    def assert_true(self, condition, message=""):
        if not condition:
            raise AssertionError(f"{message}: Condition is False")
    
    def assert_in(self, item, container, message=""):
        if item not in container:
            raise AssertionError(f"{message}: {item} not in {container}")
    
    def assert_greater_equal(self, actual, expected, message=""):
        if actual < expected:
            raise AssertionError(f"{message}: {actual} < {expected}")
    
    async def run_test(self, test_func, test_name):
        """Tek bir test çalıştır"""
        try:
            await test_func()
            print(f"✅ {test_name}")
            self.passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
            self.failed += 1
            self.errors.append((test_name, str(e), traceback.format_exc()))
    
    async def test_empty_message(self):
        """Boş mesaj testi"""
        result = await self.detector.detect_intent("")
        self.assert_equal(result.intent, IntentType.CLARIFICATION_NEEDED)
        self.assert_greater_equal(result.confidence, ConfidenceLevel.VERY_HIGH.value)
        self.assert_in("Merhaba!", result.response)
        self.assert_equal(result.method, "empty_message")
    
    async def test_exact_patterns_greeting(self):
        """Kesin selamlama pattern testleri"""
        test_cases = ["merhaba", "selam", "hello", "hi"]
        
        for greeting in test_cases:
            result = await self.detector.detect_intent(greeting)
            self.assert_equal(result.intent, IntentType.GREETING, f"Greeting: {greeting}")
            self.assert_greater_equal(result.confidence, ConfidenceLevel.VERY_HIGH.value)
            self.assert_in("Butik Cemünay", result.response)
            self.assert_equal(result.method, "exact_pattern")
    
    async def test_nonsense_detection(self):
        """Anlamsız sorgu tespiti"""
        test_cases = ["fiyat sorcaktım", "annen", "asdfgh"]
        
        for nonsense in test_cases:
            result = await self.detector.detect_intent(nonsense)
            self.assert_equal(result.intent, IntentType.CLARIFICATION_NEEDED)
            self.assert_greater_equal(result.confidence, ConfidenceLevel.VERY_HIGH.value)
            self.assert_in("Anlayamadım", result.response)
            self.assert_equal(result.method, "nonsense_detection")
    
    async def test_business_info_detection(self):
        """İşletme bilgi sorgu tespiti"""
        test_cases = [
            ("telefon", "telefon"),
            ("iade var mı", "iade"),
            ("kargo ücreti", "kargo"),
            ("website", "site")
        ]
        
        for query, expected_info_type in test_cases:
            result = await self.detector.detect_intent(query)
            self.assert_equal(result.intent, IntentType.BUSINESS_INFO)
            self.assert_greater_equal(result.confidence, ConfidenceLevel.HIGH.value)
            self.assert_true(result.function_call is not None)
            self.assert_equal(result.function_call["name"], "getGeneralInfo")
            self.assert_equal(result.function_call["args"]["info_type"], expected_info_type)
    
    async def test_product_query_detection(self):
        """Ürün sorgu tespiti"""
        test_cases = [
            "siyah gecelik fiyatı",
            "hamile pijama stok var mı",
            "dantelli sabahlık"
        ]
        
        for query in test_cases:
            result = await self.detector.detect_intent(query)
            print(f"Debug - Query: '{query}' -> Intent: {result.intent}, Method: {result.method}")
            self.assert_equal(result.intent, IntentType.PRODUCT_INQUIRY, f"Query: {query}")
            self.assert_greater_equal(result.confidence, 0.5)
            self.assert_true(len(result.entities) > 0, f"No entities for query: {query}")
    
    async def test_incomplete_query(self):
        """Eksik sorgu testi"""
        result = await self.detector.detect_intent("fiyat")
        self.assert_equal(result.intent, IntentType.CLARIFICATION_NEEDED)
        self.assert_in("Hangi ürünün fiyat", result.response)
        self.assert_equal(result.method, "incomplete_query")
    
    async def test_context_management(self):
        """Context yönetimi"""
        session_id = "test_session"
        
        # Context güncelle
        self.detector.update_context(session_id, {"last_product": "siyah gecelik"})
        
        # Context'i al
        context = self.detector.get_context(session_id)
        self.assert_equal(context["last_product"], "siyah gecelik")
        
        # Contextual query
        result = await self.detector.detect_intent("bunun fiyatı", session_id)
        self.assert_equal(result.intent, IntentType.PRODUCT_INQUIRY)
        self.assert_equal(result.method, "contextual_query")
    
    async def test_entity_extraction(self):
        """Entity extraction"""
        result = await self.detector.detect_intent("siyah dantelli gecelik fiyatı")
        
        # Color entity kontrolü
        color_entities = [e for e in result.entities if e.type == "color"]
        self.assert_true(len(color_entities) > 0)
        self.assert_equal(color_entities[0].value, "siyah")
        
        # Feature entity kontrolü
        feature_entities = [e for e in result.entities if e.type == "feature"]
        self.assert_true(len(feature_entities) > 0)
        self.assert_equal(feature_entities[0].value, "dantelli")
    
    async def test_turkish_patterns(self):
        """Türkçe pattern testleri"""
        turkish_queries = [
            "geceliği ne kadar",
            "pijamayı görebilir miyim",
            "sabahlığın fiyatı"
        ]
        
        for query in turkish_queries:
            result = await self.detector.detect_intent(query)
            self.assert_equal(result.intent, IntentType.PRODUCT_INQUIRY)
            self.assert_greater_equal(result.confidence, 0.5)
    
    async def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🧪 Enhanced Intent Detector Tests")
        print("=" * 50)
        
        tests = [
            (self.test_empty_message, "Empty Message"),
            (self.test_exact_patterns_greeting, "Exact Patterns - Greeting"),
            (self.test_nonsense_detection, "Nonsense Detection"),
            (self.test_business_info_detection, "Business Info Detection"),
            (self.test_product_query_detection, "Product Query Detection"),
            (self.test_incomplete_query, "Incomplete Query"),
            (self.test_context_management, "Context Management"),
            (self.test_entity_extraction, "Entity Extraction"),
            (self.test_turkish_patterns, "Turkish Patterns")
        ]
        
        for test_func, test_name in tests:
            await self.run_test(test_func, test_name)
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        
        if self.errors:
            print("\n❌ Errors:")
            for test_name, error, traceback_str in self.errors:
                print(f"\n{test_name}:")
                print(f"  Error: {error}")
        
        return self.failed == 0

async def main():
    """Ana test fonksiyonu"""
    runner = TestRunner()
    success = await runner.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 {runner.failed} tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())