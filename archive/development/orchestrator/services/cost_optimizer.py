"""
Cost Optimizer - 1M sorgu/ay $30 hedefi
"""

import logging
import time
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CostOptimizer:
    """Maliyet optimizasyonu - 1M sorgu/ay $30"""
    
    def __init__(self):
        # Hedef: 1M sorgu/ay = 33,333 sorgu/gün
        # Bütçe: $30/ay = $1/gün
        self.daily_query_limit = 33333
        self.daily_budget_usd = 1.0
        
        # Günlük sayaçlar
        self.daily_stats = {
            "date": datetime.now().date(),
            "total_queries": 0,
            "pattern_queries": 0,  # $0
            "llm_queries": 0,      # ~$0.0003 each
            "total_cost": 0.0
        }
        
        # LLM maliyet tablosu (token başına)
        self.llm_costs = {
            "gemini-flash": 0.000001,  # $0.000001/token
            "gemini-pro": 0.00001      # $0.00001/token
        }
    
    def should_use_llm(self, message: str, pattern_confidence: float) -> bool:
        """LLM kullanılmalı mı karar ver"""
        
        # Günlük reset kontrolü
        self._check_daily_reset()
        
        # Günlük limit kontrolü
        if self.daily_stats["total_queries"] >= self.daily_query_limit:
            logger.warning(f"Daily query limit reached: {self.daily_query_limit}")
            return False
        
        # Bütçe kontrolü
        if self.daily_stats["total_cost"] >= self.daily_budget_usd:
            logger.warning(f"Daily budget exceeded: ${self.daily_budget_usd}")
            return False
        
        # Pattern matching yeterli mi?
        if pattern_confidence >= 0.8:
            logger.info("Pattern matching sufficient, skipping LLM")
            return False
        
        # LLM kullanılabilir
        return True
    
    def track_query(self, method: str, tokens_used: int = 0, model: str = "gemini-flash"):
        """Sorgu maliyetini takip et"""
        
        self._check_daily_reset()
        
        # Toplam sorgu sayısını artır
        self.daily_stats["total_queries"] += 1
        
        if method in ["simple_exact_pattern", "simple_business_pattern", "simple_nonsense_detection", "simple_short_message"]:
            # Pattern matching - ücretsiz
            self.daily_stats["pattern_queries"] += 1
            cost = 0.0
        
        elif method in ["simple_intelligent_search", "simple_needs_llm", "function_calling", "llm_analysis", "force_llm"]:
            # LLM kullanımı - ücretli
            self.daily_stats["llm_queries"] += 1
            
            # Token sayısı tahmin et (yoksa)
            if tokens_used == 0:
                tokens_used = 100  # Ortalama tahmin
            
            cost = tokens_used * self.llm_costs.get(model, self.llm_costs["gemini-flash"])
            self.daily_stats["total_cost"] += cost
        
        else:
            # Bilinmeyen method - LLM olarak say
            self.daily_stats["llm_queries"] += 1
            cost = 100 * self.llm_costs["gemini-flash"]
            self.daily_stats["total_cost"] += cost
        
        # Log
        logger.info(f"Query tracked: method={method}, cost=${cost:.6f}, daily_total=${self.daily_stats['total_cost']:.4f}")
        
        return cost
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Günlük istatistikleri getir"""
        self._check_daily_reset()
        
        total_queries = self.daily_stats["total_queries"]
        pattern_queries = self.daily_stats["pattern_queries"]
        llm_queries = self.daily_stats["llm_queries"]
        
        return {
            "date": self.daily_stats["date"].isoformat(),
            "total_queries": total_queries,
            "pattern_queries": pattern_queries,
            "llm_queries": llm_queries,
            "pattern_percentage": (pattern_queries / total_queries * 100) if total_queries > 0 else 0,
            "llm_percentage": (llm_queries / total_queries * 100) if total_queries > 0 else 0,
            "total_cost_usd": self.daily_stats["total_cost"],
            "remaining_budget": self.daily_budget_usd - self.daily_stats["total_cost"],
            "queries_remaining": self.daily_query_limit - total_queries,
            "cost_per_query": self.daily_stats["total_cost"] / total_queries if total_queries > 0 else 0,
            "projected_monthly_cost": self.daily_stats["total_cost"] * 30,
            "efficiency_score": (pattern_queries / total_queries * 100) if total_queries > 0 else 100
        }
    
    def _check_daily_reset(self):
        """Günlük reset kontrolü"""
        today = datetime.now().date()
        
        if self.daily_stats["date"] != today:
            # Yeni gün - istatistikleri sıfırla
            logger.info(f"Daily reset: {self.daily_stats['date']} -> {today}")
            
            self.daily_stats = {
                "date": today,
                "total_queries": 0,
                "pattern_queries": 0,
                "llm_queries": 0,
                "total_cost": 0.0
            }
    
    def get_cost_projection(self, queries_per_day: int) -> Dict[str, Any]:
        """Maliyet projeksiyonu hesapla"""
        
        # Mevcut efficiency'ye göre hesapla
        current_stats = self.get_daily_stats()
        pattern_ratio = current_stats["pattern_percentage"] / 100
        llm_ratio = current_stats["llm_percentage"] / 100
        
        # Günlük maliyet tahmini
        daily_pattern_queries = queries_per_day * pattern_ratio
        daily_llm_queries = queries_per_day * llm_ratio
        
        daily_cost = daily_llm_queries * 100 * self.llm_costs["gemini-flash"]  # 100 token ortalama
        monthly_cost = daily_cost * 30
        
        return {
            "queries_per_day": queries_per_day,
            "daily_pattern_queries": int(daily_pattern_queries),
            "daily_llm_queries": int(daily_llm_queries),
            "daily_cost_usd": daily_cost,
            "monthly_cost_usd": monthly_cost,
            "within_budget": monthly_cost <= 30.0,
            "efficiency_needed": pattern_ratio,
            "recommendation": "Increase pattern matching" if monthly_cost > 30.0 else "Cost target achievable"
        }

# Global instance
cost_optimizer = CostOptimizer()