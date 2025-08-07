#!/usr/bin/env python3
"""
Confidence-Based Result Presenter - Intelligent result presentation based on confidence levels
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .result_fusion_engine import FusedResult, Alternative
    from .product_feature_extractor import ProductFeatureExtractor
    from .feature_synonym_mapper import FeatureSynonymMapper
    from .turkish_language_rules import TurkishLanguageRules
except ImportError:
    from result_fusion_engine import FusedResult, Alternative
    from product_feature_extractor import ProductFeatureExtractor
    from feature_synonym_mapper import FeatureSynonymMapper
    from turkish_language_rules import TurkishLanguageRules

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence seviyeleri"""
    VERY_HIGH = "very_high"  # 0.9+
    HIGH = "high"           # 0.7-0.89
    MEDIUM = "medium"       # 0.5-0.69
    LOW = "low"            # 0.3-0.49
    VERY_LOW = "very_low"  # <0.3

class PresentationMode(Enum):
    """Sunum modları"""
    SINGLE_BEST = "single_best"
    MULTIPLE_OPTIONS = "multiple_options"
    ALTERNATIVES_FOCUS = "alternatives_focus"
    EXPLANATION_HEAVY = "explanation_heavy"

@dataclass
class PresentedResult:
    """Sunulan sonuç"""
    product: Dict[str, Any]
    confidence_level: ConfidenceLevel
    presentation_text: str
    explanation: str
    feature_highlights: List[str]
    confidence_indicators: List[str]
    user_guidance: Optional[str] = None

@dataclass
class ResultPresentation:
    """Sonuç sunumu"""
    mode: PresentationMode
    primary_results: List[PresentedResult]
    alternatives: List[Alternative]
    overall_confidence: float
    summary_text: str
    user_guidance: str
    confidence_explanation: str

class ConfidenceBasedPresenter:
    """Confidence-based result presentation engine"""
    
    def __init__(self):
        self.feature_extractor = ProductFeatureExtractor()
        self.synonym_mapper = FeatureSynonymMapper()
        self.turkish_rules = TurkishLanguageRules()
        
        # Confidence thresholds
        self.confidence_thresholds = {
            ConfidenceLevel.VERY_HIGH: 0.9,
            ConfidenceLevel.HIGH: 0.7,
            ConfidenceLevel.MEDIUM: 0.5,
            ConfidenceLevel.LOW: 0.3,
            ConfidenceLevel.VERY_LOW: 0.0
        }
        
        # Presentation templates
        self.templates = {
            ConfidenceLevel.VERY_HIGH: {
                'intro': "Tam olarak aradığınız ürünü bulduk:",
                'confidence_text': "Çok yüksek eşleşme",
                'guidance': "Bu ürün arama kriterlerinize mükemmel uyuyor."
            },
            ConfidenceLevel.HIGH: {
                'intro': "Size uygun olabilecek ürünü bulduk:",
                'confidence_text': "Yüksek eşleşme",
                'guidance': "Bu ürün arama kriterlerinizin çoğuna uyuyor."
            },
            ConfidenceLevel.MEDIUM: {
                'intro': "Benzer özellikli ürünler buldum:",
                'confidence_text': "Orta seviye eşleşme",
                'guidance': "Bu ürünler kısmen arama kriterlerinize uyuyor."
            },
            ConfidenceLevel.LOW: {
                'intro': "Yakın sonuçlar buldum, ancak tam eşleşme değil:",
                'confidence_text': "Düşük eşleşme",
                'guidance': "Bu ürünler arama kriterlerinize kısmen uyuyor. Daha spesifik arama yapabilirsiniz."
            },
            ConfidenceLevel.VERY_LOW: {
                'intro': "Arama kriterlerinize tam uygun ürün bulamadım:",
                'confidence_text': "Çok düşük eşleşme",
                'guidance': "Farklı arama terimleri deneyebilir veya alternatif önerilere bakabilirsiniz."
            }
        }
    
    def present_results(self, fused_results: List[FusedResult], 
                       alternatives: List[Alternative], 
                       overall_confidence: float,
                       query: str) -> ResultPresentation:
        """
        Sonuçları confidence'a göre sun
        
        Args:
            fused_results: Fused search results
            alternatives: Alternative suggestions
            overall_confidence: Overall confidence score
            query: Original query
            
        Returns:
            ResultPresentation: Formatted presentation
        """
        try:
            # Determine presentation mode
            mode = self._determine_presentation_mode(fused_results, overall_confidence)
            
            # Create presented results
            primary_results = self._create_presented_results(fused_results, query, mode)
            
            # Generate summary and guidance
            summary_text = self._generate_summary(primary_results, overall_confidence, query)
            user_guidance = self._generate_user_guidance(primary_results, alternatives, overall_confidence)
            confidence_explanation = self._generate_confidence_explanation(overall_confidence, fused_results)
            
            return ResultPresentation(
                mode=mode,
                primary_results=primary_results,
                alternatives=alternatives,
                overall_confidence=overall_confidence,
                summary_text=summary_text,
                user_guidance=user_guidance,
                confidence_explanation=confidence_explanation
            )
            
        except Exception as e:
            logger.error(f"Result presentation error: {str(e)}")
            return self._create_error_presentation(query)
    
    def _determine_presentation_mode(self, results: List[FusedResult], 
                                   overall_confidence: float) -> PresentationMode:
        """Sunum modunu belirle"""
        if not results:
            return PresentationMode.ALTERNATIVES_FOCUS
        
        if overall_confidence >= 0.8 and len(results) >= 1:
            return PresentationMode.SINGLE_BEST
        elif overall_confidence >= 0.5 and len(results) >= 2:
            return PresentationMode.MULTIPLE_OPTIONS
        elif overall_confidence < 0.5:
            return PresentationMode.ALTERNATIVES_FOCUS
        else:
            return PresentationMode.EXPLANATION_HEAVY
    
    def _create_presented_results(self, fused_results: List[FusedResult], 
                                query: str, mode: PresentationMode) -> List[PresentedResult]:
        """Presented results oluştur"""
        presented_results = []
        
        # Limit results based on mode
        if mode == PresentationMode.SINGLE_BEST:
            results_to_present = fused_results[:1]
        elif mode == PresentationMode.MULTIPLE_OPTIONS:
            results_to_present = fused_results[:3]
        else:
            results_to_present = fused_results[:5]
        
        for result in results_to_present:
            confidence_level = self._get_confidence_level(result.confidence)
            
            # Create presentation text
            presentation_text = self._create_presentation_text(result, confidence_level, query)
            
            # Generate explanation
            explanation = self._create_result_explanation(result, query)
            
            # Extract feature highlights
            feature_highlights = self._extract_feature_highlights(result, query)
            
            # Generate confidence indicators
            confidence_indicators = self._generate_confidence_indicators(result)
            
            # User guidance for this specific result
            user_guidance = self._create_result_guidance(result, confidence_level)
            
            presented_result = PresentedResult(
                product=result.product,
                confidence_level=confidence_level,
                presentation_text=presentation_text,
                explanation=explanation,
                feature_highlights=feature_highlights,
                confidence_indicators=confidence_indicators,
                user_guidance=user_guidance
            )
            
            presented_results.append(presented_result)
        
        return presented_results
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Confidence score'dan level belirle"""
        if confidence >= self.confidence_thresholds[ConfidenceLevel.VERY_HIGH]:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif confidence >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif confidence >= self.confidence_thresholds[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _create_presentation_text(self, result: FusedResult, 
                                confidence_level: ConfidenceLevel, 
                                query: str) -> str:
        """Sunum metni oluştur"""
        product_name = result.product.get('name', 'Ürün')
        price = result.product.get('price', result.product.get('final_price', ''))
        
        # Base presentation
        text = f"**{product_name}**"
        
        if price:
            text += f" - {price} TL"
        
        # Add confidence indicator
        template = self.templates[confidence_level]
        text += f"\n*{template['confidence_text']} ({result.confidence:.0%})*"
        
        # Add feature highlights if available
        if result.feature_matches:
            highlights = ', '.join(result.feature_matches[:3])
            text += f"\n✨ Eşleşen özellikler: {highlights}"
        
        return text
    
    def _create_result_explanation(self, result: FusedResult, query: str) -> str:
        """Sonuç açıklaması oluştur"""
        explanation_parts = []
        
        # Method breakdown
        method_count = len(result.method_scores)
        explanation_parts.append(f"{method_count} farklı arama yöntemi kullanıldı")
        
        # Best method
        if result.method_scores:
            best_method = max(result.method_scores.keys(), key=lambda k: result.method_scores[k])
            best_score = result.method_scores[best_method]
            method_names = {
                'semantic': 'anlamsal arama',
                'fuzzy': 'benzerlik araması',
                'keyword': 'kelime araması',
                'feature_based': 'özellik araması'
            }
            method_name = method_names.get(best_method.value, best_method.value)
            explanation_parts.append(f"en iyi sonuç {method_name} ile bulundu ({best_score:.0%})")
        
        # Validation score
        if hasattr(result, 'validation_score') and result.validation_score:
            explanation_parts.append(f"doğrulama skoru: {result.validation_score:.0%}")
        
        return ", ".join(explanation_parts).capitalize() + "."
    
    def _extract_feature_highlights(self, result: FusedResult, query: str) -> List[str]:
        """Öne çıkarılacak özellikleri çıkar"""
        highlights = []
        
        # Feature matches from result
        if result.feature_matches:
            highlights.extend(result.feature_matches[:3])
        
        # Extract additional features from product
        product_features = self.feature_extractor.extract_features(result.product.get('name', ''))
        query_features = self.feature_extractor.extract_features(query)
        
        # Find important matching features
        query_feature_values = {f.value for f in query_features}
        for feature in product_features:
            if (feature.value in query_feature_values and 
                feature.value not in highlights and 
                feature.weight > 0.7):
                highlights.append(feature.value)
        
        return highlights[:5]  # Limit to 5 highlights
    
    def _generate_confidence_indicators(self, result: FusedResult) -> List[str]:
        """Confidence göstergeleri oluştur"""
        indicators = []
        
        # Method count indicator
        method_count = len(result.method_scores)
        if method_count >= 3:
            indicators.append(f"✅ {method_count} yöntem onayladı")
        elif method_count == 2:
            indicators.append(f"✅ {method_count} yöntem onayladı")
        else:
            indicators.append(f"⚠️ Tek yöntem sonucu")
        
        # Score consistency
        if result.method_scores:
            scores = list(result.method_scores.values())
            if len(scores) > 1:
                score_range = max(scores) - min(scores)
                if score_range < 0.2:
                    indicators.append("✅ Tutarlı skorlar")
                elif score_range > 0.4:
                    indicators.append("⚠️ Değişken skorlar")
        
        # Validation indicator
        if hasattr(result, 'validation_score'):
            if result.validation_score > 0.7:
                indicators.append("✅ Yüksek doğrulama")
            elif result.validation_score < 0.3:
                indicators.append("⚠️ Düşük doğrulama")
        
        # Feature match indicator
        if result.feature_matches:
            feature_count = len(result.feature_matches)
            if feature_count >= 3:
                indicators.append(f"✅ {feature_count} özellik eşleşmesi")
            elif feature_count >= 1:
                indicators.append(f"✅ {feature_count} özellik eşleşmesi")
        
        return indicators
    
    def _create_result_guidance(self, result: FusedResult, 
                              confidence_level: ConfidenceLevel) -> str:
        """Sonuç için kullanıcı rehberliği"""
        template = self.templates[confidence_level]
        base_guidance = template['guidance']
        
        # Add specific guidance based on result
        if confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]:
            if not result.feature_matches:
                base_guidance += " Daha spesifik özellikler belirtebilirsiniz."
            else:
                base_guidance += " Alternatif önerilere göz atabilirsiniz."
        
        return base_guidance
    
    def _generate_summary(self, results: List[PresentedResult], 
                         overall_confidence: float, query: str) -> str:
        """Özet metin oluştur"""
        if not results:
            return f"'{query}' araması için uygun ürün bulunamadı."
        
        result_count = len(results)
        overall_level = self._get_confidence_level(overall_confidence)
        template = self.templates[overall_level]
        
        if result_count == 1:
            summary = f"{template['intro']} {results[0].product.get('name', 'Ürün')}"
        else:
            summary = f"{template['intro']} {result_count} ürün bulundu"
        
        summary += f" (Genel güven: {overall_confidence:.0%})"
        
        return summary
    
    def _generate_user_guidance(self, results: List[PresentedResult], 
                              alternatives: List[Alternative], 
                              overall_confidence: float) -> str:
        """Kullanıcı rehberliği oluştur"""
        guidance_parts = []
        
        if overall_confidence >= 0.8:
            guidance_parts.append("Sonuçlar yüksek güvenilirlikte.")
        elif overall_confidence >= 0.5:
            guidance_parts.append("Sonuçlar orta güvenilirlikte.")
        else:
            guidance_parts.append("Sonuçlar düşük güvenilirlikte.")
        
        if alternatives:
            guidance_parts.append(f"{len(alternatives)} alternatif öneri mevcut.")
        
        if overall_confidence < 0.6:
            guidance_parts.append("Daha iyi sonuçlar için:")
            guidance_parts.append("• Daha spesifik terimler kullanın")
            guidance_parts.append("• Ürün özelliklerini belirtin")
            guidance_parts.append("• Alternatif önerileri deneyin")
        
        return " ".join(guidance_parts)
    
    def _generate_confidence_explanation(self, overall_confidence: float, 
                                       results: List[FusedResult]) -> str:
        """Confidence açıklaması oluştur"""
        explanation_parts = []
        
        # Overall confidence explanation
        if overall_confidence >= 0.8:
            explanation_parts.append("Yüksek güven: Arama kriterlerinize çok iyi uyuyor")
        elif overall_confidence >= 0.6:
            explanation_parts.append("Orta güven: Arama kriterlerinize iyi uyuyor")
        elif overall_confidence >= 0.4:
            explanation_parts.append("Düşük güven: Kısmen arama kriterlerinize uyuyor")
        else:
            explanation_parts.append("Çok düşük güven: Arama kriterlerinize az uyuyor")
        
        # Method diversity
        if results:
            all_methods = set()
            for result in results:
                all_methods.update(result.method_scores.keys())
            
            method_count = len(all_methods)
            explanation_parts.append(f"{method_count} farklı arama yöntemi kullanıldı")
        
        return ". ".join(explanation_parts) + "."
    
    def _create_error_presentation(self, query: str) -> ResultPresentation:
        """Hata durumu için presentation"""
        return ResultPresentation(
            mode=PresentationMode.ALTERNATIVES_FOCUS,
            primary_results=[],
            alternatives=[],
            overall_confidence=0.0,
            summary_text=f"'{query}' araması sırasında bir hata oluştu.",
            user_guidance="Lütfen farklı arama terimleri deneyin.",
            confidence_explanation="Arama işlemi tamamlanamadı."
        )
    
    def format_for_display(self, presentation: ResultPresentation) -> str:
        """Display için formatla"""
        output_lines = []
        
        # Summary
        output_lines.append(f"🔍 {presentation.summary_text}")
        output_lines.append("")
        
        # Primary results
        for i, result in enumerate(presentation.primary_results, 1):
            output_lines.append(f"{i}. {result.presentation_text}")
            output_lines.append(f"   📝 {result.explanation}")
            
            if result.feature_highlights:
                highlights = ", ".join(result.feature_highlights)
                output_lines.append(f"   🎯 Özellikler: {highlights}")
            
            if result.confidence_indicators:
                indicators = " | ".join(result.confidence_indicators)
                output_lines.append(f"   📊 {indicators}")
            
            output_lines.append("")
        
        # Alternatives
        if presentation.alternatives:
            output_lines.append("💡 Alternatif öneriler:")
            for alt in presentation.alternatives[:3]:
                output_lines.append(f"   • '{alt.suggestion}' - {alt.reason}")
            output_lines.append("")
        
        # Guidance
        output_lines.append(f"ℹ️ {presentation.user_guidance}")
        output_lines.append(f"📈 {presentation.confidence_explanation}")
        
        return "\n".join(output_lines)
    
    def get_presenter_stats(self) -> Dict[str, Any]:
        """Presenter istatistikleri"""
        return {
            'confidence_levels': list(self.confidence_thresholds.keys()),
            'presentation_modes': list(PresentationMode),
            'templates': len(self.templates)
        }

# Test fonksiyonu
def test_confidence_based_presenter():
    """Confidence-based presenter test"""
    
    # Mock fused results
    from result_fusion_engine import FusedResult
    from intelligent_search_engine import SearchMethod
    
    test_results = [
        FusedResult(
            product={'id': 1, 'name': 'Siyah Tüllü Askılı Gecelik', 'price': 890.50},
            final_score=1.2,
            confidence=0.9,
            method_scores={SearchMethod.SEMANTIC: 0.9, SearchMethod.FUZZY: 0.95},
            method_ranks={SearchMethod.SEMANTIC: 2, SearchMethod.FUZZY: 1},
            fusion_explanation="High confidence match",
            validation_score=0.8,
            feature_matches=['siyah', 'gecelik', 'askılı']
        ),
        FusedResult(
            product={'id': 2, 'name': 'Dantelli Hamile Gecelik', 'price': 1200.0},
            final_score=0.7,
            confidence=0.6,
            method_scores={SearchMethod.SEMANTIC: 0.7},
            method_ranks={SearchMethod.SEMANTIC: 1},
            fusion_explanation="Medium confidence match",
            validation_score=0.5,
            feature_matches=['gecelik']
        )
    ]
    
    # Mock alternatives
    alternatives = [
        Alternative("black nightgown", "Try English terms", 0.7, "siyah gecelik"),
        Alternative("siyah gece elbisesi", "Try synonym", 0.6, "siyah gecelik")
    ]
    
    presenter = ConfidenceBasedPresenter()
    
    print("📊 Confidence-Based Presenter Test:")
    print("=" * 50)
    
    # Test presentation
    query = "siyah gecelik"
    presentation = presenter.present_results(test_results, alternatives, 0.85, query)
    
    print(f"\n🎯 Presentation Mode: {presentation.mode.value}")
    print(f"📈 Overall Confidence: {presentation.overall_confidence:.0%}")
    
    # Display formatted output
    formatted_output = presenter.format_for_display(presentation)
    print("\n" + "="*50)
    print("FORMATTED OUTPUT:")
    print("="*50)
    print(formatted_output)
    
    # Test different confidence levels
    print("\n" + "="*50)
    print("CONFIDENCE LEVEL TESTS:")
    print("="*50)
    
    confidence_tests = [0.95, 0.75, 0.55, 0.35, 0.15]
    for conf in confidence_tests:
        level = presenter._get_confidence_level(conf)
        template = presenter.templates[level]
        print(f"Confidence {conf:.0%} -> {level.value}: {template['confidence_text']}")
    
    # Stats
    stats = presenter.get_presenter_stats()
    print(f"\n📊 Presenter Stats:")
    print(f"  Confidence levels: {len(stats['confidence_levels'])}")
    print(f"  Presentation modes: {len(stats['presentation_modes'])}")
    print(f"  Templates: {stats['templates']}")

if __name__ == "__main__":
    test_confidence_based_presenter()