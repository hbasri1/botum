#!/usr/bin/env python3
"""
Realistic Pricing Model - Gerçek Maliyet Bazlı
Sadece gerçek maliyetler + makul kar marjı
"""

from dataclasses import dataclass
from typing import Dict, List
import json

@dataclass
class RealisticCosts:
    """Gerçekçi maliyet yapısı"""
    llm_cost_per_1m: float
    server_cost_per_1m: float
    base_monthly_cost: float
    profit_margin: float

class RealisticPricingModel:
    """Gerçekçi fiyatlandırma modeli"""
    
    def __init__(self):
        self.usd_to_try = 34.0
        
    def calculate_real_costs_per_query_volume(self) -> Dict[str, Dict]:
        """Sorgu hacmine göre gerçek maliyetler"""
        
        # Temel maliyetler (aylık)
        base_costs = {
            "sunucu": 1000,      # Sunucu + DB + CDN
            "llm_sabit": 200,    # Minimum LLM maliyeti
            "bakım": 500,        # Sistem bakımı
            "destek": 300,       # Temel destek
        }
        
        base_monthly = sum(base_costs.values())  # 2000 TL
        
        # Sorgu hacmine göre değişken maliyetler
        query_volumes = {
            "10k": {
                "monthly_queries": 10000,
                "llm_cost": 70,      # 10K sorgu için LLM maliyeti
                "server_extra": 0,   # Ek sunucu maliyeti yok
                "total_cost": base_monthly + 70,
                "cost_per_query": (base_monthly + 70) / 10000
            },
            
            "50k": {
                "monthly_queries": 50000,
                "llm_cost": 350,     # 50K sorgu için LLM maliyeti
                "server_extra": 200, # Biraz ek sunucu
                "total_cost": base_monthly + 350 + 200,
                "cost_per_query": (base_monthly + 350 + 200) / 50000
            },
            
            "100k": {
                "monthly_queries": 100000,
                "llm_cost": 700,     # 100K sorgu için LLM maliyeti
                "server_extra": 300, # Ek sunucu maliyeti
                "total_cost": base_monthly + 700 + 300,
                "cost_per_query": (base_monthly + 700 + 300) / 100000
            },
            
            "500k": {
                "monthly_queries": 500000,
                "llm_cost": 3500,    # 500K sorgu için LLM maliyeti
                "server_extra": 1000, # Daha güçlü sunucu
                "total_cost": base_monthly + 3500 + 1000,
                "cost_per_query": (base_monthly + 3500 + 1000) / 500000
            },
            
            "1m": {
                "monthly_queries": 1000000,
                "llm_cost": 7000,    # 1M sorgu için LLM maliyeti
                "server_extra": 1500, # En güçlü sunucu
                "total_cost": base_monthly + 7000 + 1500,
                "cost_per_query": (base_monthly + 7000 + 1500) / 1000000
            }
        }
        
        return query_volumes
    
    def calculate_competitive_pricing(self) -> Dict[str, Dict]:
        """Rekabetçi fiyatlandırma modeli"""
        
        costs = self.calculate_real_costs_per_query_volume()
        
        # Farklı kar marjları
        pricing_strategies = {
            "agresif": 1.5,      # %50 kar
            "standart": 2.0,     # %100 kar  
            "premium": 3.0,      # %200 kar
        }
        
        pricing_tiers = {}
        
        for volume_name, volume_data in costs.items():
            pricing_tiers[volume_name] = {
                "monthly_queries": volume_data["monthly_queries"],
                "our_cost": volume_data["total_cost"],
                "cost_per_query": volume_data["cost_per_query"],
                "pricing_options": {}
            }
            
            for strategy_name, multiplier in pricing_strategies.items():
                price = volume_data["total_cost"] * multiplier
                pricing_tiers[volume_name]["pricing_options"][strategy_name] = {
                    "monthly_price": price,
                    "price_per_query": price / volume_data["monthly_queries"],
                    "profit": price - volume_data["total_cost"],
                    "profit_margin": ((price - volume_data["total_cost"]) / volume_data["total_cost"]) * 100
                }
        
        return pricing_tiers
    
    def get_market_comparison(self) -> Dict[str, Dict]:
        """Piyasa karşılaştırması"""
        
        # Mevcut piyasa fiyatları (tahmini)
        market_prices = {
            "ticimax_chatbot": {"setup": 5000, "monthly": 2000, "per_query": 0.20},
            "iyzico_chatbot": {"setup": 8000, "monthly": 3500, "per_query": 0.35},
            "shopify_chatbot": {"setup": 0, "monthly": 1500, "per_query": 0.15},
            "custom_solutions": {"setup": 15000, "monthly": 5000, "per_query": 0.50},
        }
        
        return market_prices
    
    def recommend_final_pricing(self) -> Dict[str, Dict]:
        """Final önerilen fiyatlandırma"""
        
        costs = self.calculate_real_costs_per_query_volume()
        
        # Basit ve net fiyatlandırma
        final_pricing = {
            "starter": {
                "queries": "10K/ay",
                "our_cost": costs["10k"]["total_cost"],
                "price": 3500,  # Maliyetin ~1.7 katı
                "setup_fee": 2500,
                "features": ["Temel chatbot", "Email destek", "Temel raporlar"]
            },
            
            "business": {
                "queries": "50K/ay",
                "our_cost": costs["50k"]["total_cost"],
                "price": 5000,  # Maliyetin ~2 katı
                "setup_fee": 3500,
                "features": ["Gelişmiş chatbot", "Öncelikli destek", "Detaylı raporlar", "API entegrasyonu"]
            },
            
            "professional": {
                "queries": "100K/ay",
                "our_cost": costs["100k"]["total_cost"],
                "price": 6500,  # Maliyetin ~2.2 katı
                "setup_fee": 4000,
                "features": ["Premium chatbot", "7/24 destek", "Özel raporlar", "Tam entegrasyon"]
            },
            
            "enterprise": {
                "queries": "500K/ay",
                "our_cost": costs["500k"]["total_cost"],
                "price": 12000, # Maliyetin ~1.8 katı (hacim indirimi)
                "setup_fee": 5000,
                "features": ["Kurumsal chatbot", "Özel hesap yöneticisi", "Özel geliştirmeler"]
            },
            
            "enterprise_plus": {
                "queries": "1M/ay",
                "our_cost": costs["1m"]["total_cost"],
                "price": 18000, # Maliyetin ~1.7 katı (büyük hacim indirimi)
                "setup_fee": 6000,
                "features": ["Tam özelleştirilmiş", "Özel SLA", "Özel geliştirme ekibi"]
            }
        }
        
        # Kar hesaplamaları
        for tier_name, tier in final_pricing.items():
            tier["monthly_profit"] = tier["price"] - tier["our_cost"]
            tier["profit_margin"] = (tier["monthly_profit"] / tier["our_cost"]) * 100
            tier["yearly_profit"] = tier["monthly_profit"] * 12
            # Cost per query calculation
            if "1M" in tier["queries"]:
                query_count = 1000000
            else:
                query_count = int(tier["queries"].split("K")[0]) * 1000
            tier["cost_per_query"] = tier["price"] / query_count
        
        return final_pricing
    
    def generate_sales_pitch(self) -> Dict[str, str]:
        """Satış argümanları"""
        
        return {
            "value_proposition": [
                "Müşteri hizmetleri maliyetinizi %70 azaltır",
                "24/7 otomatik müşteri desteği",
                "Satış dönüşümünüzü %20 artırır",
                "Kurulum 1 hafta, entegrasyon kolay",
                "Türkçe dil desteği mükemmel"
            ],
            
            "cost_savings": {
                "traditional_support": "1 müşteri temsilcisi: 8000 TL/ay",
                "our_solution": "Starter plan: 3500 TL/ay",
                "savings": "4500 TL/ay tasarruf + 24/7 hizmet"
            },
            
            "roi_calculation": {
                "investment": "3500 TL/ay",
                "savings": "4500 TL/ay (personel maliyeti)",
                "additional_sales": "2000 TL/ay (dönüşüm artışı)",
                "net_benefit": "3000 TL/ay kar"
            }
        }

def main():
    """Ana rapor"""
    model = RealisticPricingModel()
    
    print("💰 GERÇEKÇİ FİYATLANDIRMA MODELİ")
    print("=" * 50)
    
    # Gerçek maliyetler
    costs = model.calculate_real_costs_per_query_volume()
    print("\n📊 GERÇEK MALİYETLER:")
    print("-" * 30)
    for volume, data in costs.items():
        print(f"{volume.upper()}: {data['total_cost']:,} TL/ay ({data['cost_per_query']:.4f} TL/sorgu)")
    
    # Önerilen fiyatlar
    pricing = model.recommend_final_pricing()
    print(f"\n🎯 ÖNERİLEN FİYATLAR:")
    print("-" * 30)
    for tier_name, tier in pricing.items():
        print(f"\n{tier_name.upper()}:")
        print(f"  Sorgu Limiti: {tier['queries']}")
        print(f"  Maliyetimiz: {tier['our_cost']:,} TL")
        print(f"  Satış Fiyatı: {tier['price']:,} TL")
        print(f"  Aylık Kar: {tier['monthly_profit']:,} TL")
        print(f"  Kar Marjı: %{tier['profit_margin']:.0f}")
        print(f"  Sorgu Başı: {tier['cost_per_query']:.4f} TL")
    
    # Satış argümanları
    pitch = model.generate_sales_pitch()
    print(f"\n💡 SATIŞ ARGÜMANLARI:")
    print("-" * 30)
    for value in pitch["value_proposition"]:
        print(f"• {value}")
    
    print(f"\n💸 MALİYET KARŞILAŞTIRMASI:")
    print(f"Geleneksel: {pitch['cost_savings']['traditional_support']}")
    print(f"Bizim Çözüm: {pitch['cost_savings']['our_solution']}")
    print(f"Tasarruf: {pitch['cost_savings']['savings']}")
    
    print(f"\n📈 ROI HESABI:")
    roi = pitch["roi_calculation"]
    print(f"Yatırım: {roi['investment']}")
    print(f"Tasarruf: {roi['savings']}")
    print(f"Ek Satış: {roi['additional_sales']}")
    print(f"Net Fayda: {roi['net_benefit']}")

if __name__ == "__main__":
    main()