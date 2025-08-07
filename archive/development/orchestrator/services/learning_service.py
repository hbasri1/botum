"""
Learning Service - Sistemin kendi kendine öğrenmesi ve gelişmesi
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from .database_service import DatabaseService
from .llm_service import LLMService
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class LearningService:
    def __init__(self, db_service: DatabaseService, llm_service: LLMService, 
                 cache_manager: CacheManager):
        self.db_service = db_service
        self.llm_service = llm_service
        self.cache_manager = cache_manager
        
        # Öğrenme parametreleri
        self.learning_config = {
            "min_confidence_for_learning": 0.85,
            "min_interactions_for_pattern": 5,
            "pattern_analysis_interval": 3600,  # 1 saat
            "auto_improvement_enabled": True,
            "feedback_weight": 0.3
        }
        
        # Pattern detection
        self.detected_patterns = {}
        self.improvement_suggestions = []
        
        # Background task
        self.learning_task = None
    
    async def start_learning_loop(self):
        """Öğrenme döngüsünü başlat"""
        if self.learning_task:
            return
        
        self.learning_task = asyncio.create_task(self._learning_loop())
        logger.info("Learning loop started")
    
    async def stop_learning_loop(self):
        """Öğrenme döngüsünü durdur"""
        if self.learning_task:
            self.learning_task.cancel()
            self.learning_task = None
        logger.info("Learning loop stopped")
    
    async def _learning_loop(self):
        """Ana öğrenme döngüsü"""
        while True:
            try:
                await asyncio.sleep(self.learning_config["pattern_analysis_interval"])
                
                logger.info("Starting learning cycle...")
                
                # 1. Pattern analizi
                await self._analyze_interaction_patterns()
                
                # 2. Performance analizi
                await self._analyze_performance_metrics()
                
                # 3. Cache optimizasyonu
                await self._optimize_cache_patterns()
                
                # 4. Intent accuracy analizi
                await self._analyze_intent_accuracy()
                
                # 5. Improvement önerileri üret
                await self._generate_improvement_suggestions()
                
                # 6. Auto-improvement (eğer etkinse)
                if self.learning_config["auto_improvement_enabled"]:
                    await self._apply_auto_improvements()
                
                logger.info("Learning cycle completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Learning loop error: {str(e)}")
                await asyncio.sleep(60)  # Hata durumunda 1 dakika bekle
    
    async def _analyze_interaction_patterns(self):
        """Etkileşim pattern'lerini analiz et"""
        try:
            # Son 24 saatteki etkileşimleri al
            since_time = time.time() - 86400  # 24 saat
            
            interactions = [
                interaction for interaction in self.llm_service.conversation_memory
                if interaction.get("timestamp", 0) > since_time
            ]
            
            if len(interactions) < self.learning_config["min_interactions_for_pattern"]:
                return
            
            # Intent pattern'leri
            intent_patterns = {}
            message_patterns = {}
            confidence_patterns = {}
            
            for interaction in interactions:
                if not interaction.get("success", False):
                    continue
                
                intent = interaction.get("intent", "unknown")
                message = interaction.get("user_message", "").lower()
                confidence = interaction.get("confidence", 0)
                isletme_id = interaction.get("isletme_id", "")
                
                # Intent patterns
                key = f"{isletme_id}:{intent}"
                if key not in intent_patterns:
                    intent_patterns[key] = {"count": 0, "messages": [], "avg_confidence": 0}
                
                intent_patterns[key]["count"] += 1
                intent_patterns[key]["messages"].append(message)
                intent_patterns[key]["avg_confidence"] = (
                    intent_patterns[key]["avg_confidence"] + confidence
                ) / 2
                
                # Message patterns (sık kullanılan kelimeler)
                words = message.split()
                for word in words:
                    if len(word) > 2:  # Kısa kelimeleri filtrele
                        if word not in message_patterns:
                            message_patterns[word] = {"count": 0, "intents": set()}
                        message_patterns[word]["count"] += 1
                        message_patterns[word]["intents"].add(intent)
                
                # Confidence patterns
                conf_range = self._get_confidence_range(confidence)
                if conf_range not in confidence_patterns:
                    confidence_patterns[conf_range] = {"count": 0, "intents": {}}
                confidence_patterns[conf_range]["count"] += 1
                
                if intent not in confidence_patterns[conf_range]["intents"]:
                    confidence_patterns[conf_range]["intents"][intent] = 0
                confidence_patterns[conf_range]["intents"][intent] += 1
            
            # Pattern'leri kaydet
            self.detected_patterns = {
                "intent_patterns": intent_patterns,
                "message_patterns": message_patterns,
                "confidence_patterns": confidence_patterns,
                "analysis_timestamp": time.time(),
                "total_interactions": len(interactions)
            }
            
            logger.info(f"Analyzed {len(interactions)} interactions, found {len(intent_patterns)} intent patterns")
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {str(e)}")
    
    def _get_confidence_range(self, confidence: float) -> str:
        """Confidence'ı aralığa çevir"""
        if confidence >= 0.90:
            return "very_high"
        elif confidence >= 0.80:
            return "high"
        elif confidence >= 0.70:
            return "medium"
        elif confidence >= 0.60:
            return "low"
        else:
            return "very_low"
    
    async def _analyze_performance_metrics(self):
        """Performance metriklerini analiz et"""
        try:
            insights = await self.llm_service.get_learning_insights()
            
            # Kritik metrikler
            success_rate = insights.get("success_rate", 0)
            avg_confidence = insights.get("overall_metrics", {}).get("average_confidence", 0)
            low_perf_intents = insights.get("low_performance_intents", [])
            
            # Performance sorunları tespit et
            performance_issues = []
            
            if success_rate < 0.90:
                performance_issues.append({
                    "type": "low_success_rate",
                    "value": success_rate,
                    "severity": "high" if success_rate < 0.80 else "medium",
                    "recommendation": "LLM model fine-tuning gerekli"
                })
            
            if avg_confidence < 0.80:
                performance_issues.append({
                    "type": "low_confidence",
                    "value": avg_confidence,
                    "severity": "high",
                    "recommendation": "Training data kalitesi artırılmalı"
                })
            
            if len(low_perf_intents) > 0:
                performance_issues.append({
                    "type": "low_performance_intents",
                    "value": low_perf_intents,
                    "severity": "medium",
                    "recommendation": f"Bu intent'ler için özel training: {', '.join(low_perf_intents)}"
                })
            
            # Sonuçları kaydet
            self.detected_patterns["performance_issues"] = performance_issues
            
            logger.info(f"Performance analysis: {len(performance_issues)} issues detected")
            
        except Exception as e:
            logger.error(f"Performance analysis error: {str(e)}")
    
    async def _optimize_cache_patterns(self):
        """Cache pattern'lerini optimize et"""
        try:
            # Sık sorulan sorular pattern'i
            intent_patterns = self.detected_patterns.get("intent_patterns", {})
            
            cache_optimizations = []
            
            for pattern_key, pattern_data in intent_patterns.items():
                isletme_id, intent = pattern_key.split(":", 1)
                count = pattern_data["count"]
                avg_confidence = pattern_data["avg_confidence"]
                
                # Sık sorulan ve yüksek confidence'lı intent'ler için cache süresi artır
                if count >= 10 and avg_confidence >= 0.85:
                    if intent in ["meta_query", "greeting", "thanks"]:
                        cache_optimizations.append({
                            "type": "extend_cache_ttl",
                            "isletme_id": isletme_id,
                            "intent": intent,
                            "current_count": count,
                            "suggested_ttl": 7200  # 2 saat
                        })
                
                # Düşük confidence'lı intent'ler için cache'i kısalt
                elif avg_confidence < 0.70:
                    cache_optimizations.append({
                        "type": "reduce_cache_ttl",
                        "isletme_id": isletme_id,
                        "intent": intent,
                        "avg_confidence": avg_confidence,
                        "suggested_ttl": 1800  # 30 dakika
                    })
            
            self.detected_patterns["cache_optimizations"] = cache_optimizations
            
            logger.info(f"Cache optimization: {len(cache_optimizations)} suggestions generated")
            
        except Exception as e:
            logger.error(f"Cache optimization error: {str(e)}")
    
    async def _analyze_intent_accuracy(self):
        """Intent accuracy'yi analiz et"""
        try:
            # Eskalasyon oranlarını analiz et
            escalation_patterns = {}
            
            for interaction in self.llm_service.conversation_memory:
                if not interaction.get("success", False):
                    continue
                
                intent = interaction.get("intent", "unknown")
                confidence = interaction.get("confidence", 0)
                isletme_id = interaction.get("isletme_id", "")
                
                # Düşük confidence'lı intent'leri takip et (eskalasyon adayları)
                if confidence < 0.80:
                    key = f"{isletme_id}:{intent}"
                    if key not in escalation_patterns:
                        escalation_patterns[key] = {"count": 0, "avg_confidence": 0, "messages": []}
                    
                    escalation_patterns[key]["count"] += 1
                    escalation_patterns[key]["avg_confidence"] = (
                        escalation_patterns[key]["avg_confidence"] + confidence
                    ) / 2
                    escalation_patterns[key]["messages"].append(interaction.get("user_message", ""))
            
            # Yüksek eskalasyon oranına sahip intent'leri tespit et
            high_escalation_intents = []
            for key, data in escalation_patterns.items():
                if data["count"] >= 5 and data["avg_confidence"] < 0.75:
                    high_escalation_intents.append({
                        "pattern": key,
                        "escalation_count": data["count"],
                        "avg_confidence": data["avg_confidence"],
                        "sample_messages": data["messages"][:3]
                    })
            
            self.detected_patterns["high_escalation_intents"] = high_escalation_intents
            
            logger.info(f"Intent accuracy analysis: {len(high_escalation_intents)} high-escalation intents found")
            
        except Exception as e:
            logger.error(f"Intent accuracy analysis error: {str(e)}")
    
    async def _generate_improvement_suggestions(self):
        """Gelişim önerilerini üret"""
        try:
            suggestions = []
            
            # Performance issues'dan öneriler
            performance_issues = self.detected_patterns.get("performance_issues", [])
            for issue in performance_issues:
                suggestions.append({
                    "type": "performance",
                    "priority": issue["severity"],
                    "description": issue["recommendation"],
                    "data": issue
                })
            
            # Cache optimizations'dan öneriler
            cache_opts = self.detected_patterns.get("cache_optimizations", [])
            for opt in cache_opts:
                suggestions.append({
                    "type": "cache_optimization",
                    "priority": "low",
                    "description": f"Cache TTL optimize et: {opt['type']} for {opt['intent']}",
                    "data": opt
                })
            
            # High escalation intents'den öneriler
            high_esc = self.detected_patterns.get("high_escalation_intents", [])
            for esc in high_esc:
                suggestions.append({
                    "type": "training_needed",
                    "priority": "high",
                    "description": f"Training data gerekli: {esc['pattern']} (eskalasyon: {esc['escalation_count']})",
                    "data": esc
                })
            
            # Öncelik sırasına göre sırala
            priority_order = {"high": 3, "medium": 2, "low": 1}
            suggestions.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
            
            self.improvement_suggestions = suggestions
            
            logger.info(f"Generated {len(suggestions)} improvement suggestions")
            
        except Exception as e:
            logger.error(f"Improvement suggestions error: {str(e)}")
    
    async def _apply_auto_improvements(self):
        """Otomatik iyileştirmeleri uygula"""
        try:
            applied_improvements = []
            
            for suggestion in self.improvement_suggestions:
                if suggestion["type"] == "cache_optimization" and suggestion["priority"] == "low":
                    # Düşük riskli cache optimizasyonlarını otomatik uygula
                    data = suggestion["data"]
                    
                    if data["type"] == "extend_cache_ttl":
                        # Cache TTL'yi artır
                        await self.cache_manager.set_intent_cache(
                            data["isletme_id"],
                            data["intent"],
                            "optimized_response",
                            ttl=data["suggested_ttl"]
                        )
                        applied_improvements.append(suggestion)
            
            if applied_improvements:
                logger.info(f"Applied {len(applied_improvements)} auto-improvements")
            
        except Exception as e:
            logger.error(f"Auto-improvement error: {str(e)}")
    
    async def get_learning_report(self) -> Dict[str, Any]:
        """Öğrenme raporu getir"""
        try:
            return {
                "timestamp": time.time(),
                "learning_config": self.learning_config,
                "detected_patterns": self.detected_patterns,
                "improvement_suggestions": self.improvement_suggestions,
                "llm_insights": await self.llm_service.get_learning_insights(),
                "status": "active" if self.learning_task else "stopped"
            }
        except Exception as e:
            logger.error(f"Learning report error: {str(e)}")
            return {"error": str(e)}
    
    async def export_fine_tuning_data(self) -> Dict[str, Any]:
        """Fine-tuning için veri export et"""
        try:
            # LLM service'den training data al
            training_data = await self.llm_service.export_training_data()
            
            # Pattern'lerden ek örnekler üret
            pattern_examples = []
            intent_patterns = self.detected_patterns.get("intent_patterns", {})
            
            for pattern_key, pattern_data in intent_patterns.items():
                if pattern_data["avg_confidence"] >= 0.85 and pattern_data["count"] >= 5:
                    isletme_id, intent = pattern_key.split(":", 1)
                    
                    # En sık kullanılan mesajları al
                    messages = pattern_data["messages"][:10]
                    
                    for message in messages:
                        pattern_examples.append({
                            "input": message,
                            "output": {
                                "intent": intent,
                                "confidence": pattern_data["avg_confidence"]
                            },
                            "source": "pattern_analysis",
                            "isletme_id": isletme_id
                        })
            
            return {
                "training_data": training_data,
                "pattern_examples": pattern_examples,
                "total_examples": len(training_data.get("training_examples", [])) + len(pattern_examples),
                "export_timestamp": time.time(),
                "quality_metrics": {
                    "min_confidence": self.learning_config["min_confidence_for_learning"],
                    "pattern_threshold": self.learning_config["min_interactions_for_pattern"]
                }
            }
            
        except Exception as e:
            logger.error(f"Fine-tuning data export error: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Learning service sağlık kontrolü"""
        try:
            return self.learning_task is not None and not self.learning_task.done()
        except Exception as e:
            logger.error(f"Learning service health check failed: {str(e)}")
            return False