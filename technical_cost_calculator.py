#!/usr/bin/env python3
"""
Technical Cost Calculator - Sistemimizin Gerçek Maliyetleri
Mevcut sistemin çalışma mantığına göre hesaplama
"""

from dataclasses import dataclass
from typing import Dict
import json

class TechnicalCostCalculator:
    """Teknik maliyet hesaplayıcısı"""
    
    def __init__(self):
        self.usd_to_try = 34.0
        
    def analyze_system_architecture(self) -> Dict:
        """Sistemimizin mimarisini analiz et"""
        
        return {
            "components": {
                "gemini_2_0_flash": "Ana LLM model",
                "rag_system": "TF-IDF + Cosine similarity (590 ürün)",
                "smart_cache": "In-memory cache sistemi",
                "ultra_fast_rules": "Rule-based intent detection",
                "conversation_handler": "Context management",
                "flask_api": "Web interface",
                "product_database": "JSON-based ürün veritabanı"
            },
            
            "request_flow": [
                "1. Ultra fast rules check (0 token)",
                "2. Cache check (0 token)", 
                "3. Gemini API call (eğer gerekli)",
                "4. RAG search (local)",
                "5. Response formatting (local)"
            ],
            
            "llm_usage_ratio": {
                "rule_based": 0.65,  # %65 ultra fast rules
                "llm_based": 0.35    # %35 Gemini API
            }
        }
    
    def calculate_gemini_costs_1m_queries(self) -> Dict:
        """1M sorgu için Gemini maliyetleri"""
        
        # Sistemimizin gerçek kullanım oranları
        total_queries = 1_000_000
        llm_queries = int(total_queries * 0.35)  # %35'i LLM'e gidiyor
        rule_based_queries = total_queries - llm_queries
        
        # Gemini 2.0 Flash fiyatları (Aralık 2024)
        gemini_pricing = {
            "input_price_per_1m": 0.075,   # $0.075 per 1M input tokens
            "output_price_per_1m": 0.30,   # $0.30 per 1M output tokens
        }
        
        # Ortalama token kullanımı (gerçek sistemimize göre)
        avg_tokens_per_query = {
            "input": 80,   # Intent detection prompt + user message
            "output": 30,  # Function call response
        }
        
        # Token hesaplamaları
        total_input_tokens = llm_queries * avg_tokens_per_query["input"]
        total_output_tokens = llm_queries * avg_tokens_per_query["output"]
        
        # Maliyet hesaplamaları (USD)
        input_cost_usd = (total_input_tokens / 1_000_000) * gemini_pricing["input_price_per_1m"]
        output_cost_usd = (total_output_tokens / 1_000_000) * gemini_pricing["output_price_per_1m"]
        total_cost_usd = input_cost_usd + output_cost_usd
        
        # TL'ye çevir
        total_cost_try = total_cost_usd * self.usd_to_try
        
        return {
            "total_queries": total_queries,
            "llm_queries": llm_queries,
            "rule_based_queries": rule_based_queries,
            "llm_usage_percentage": 35,
            
            "token_usage": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "avg_input_per_query": avg_tokens_per_query["input"],
                "avg_output_per_query": avg_tokens_per_query["output"]
            },
            
            "costs_usd": {
                "input_cost": input_cost_usd,
                "output_cost": output_cost_usd,
                "total_cost": total_cost_usd
            },
            
            "costs_try": {
                "total_monthly_cost": total_cost_try,
                "cost_per_query": total_cost_try / total_queries,
                "cost_per_llm_query": total_cost_try / llm_queries
            }
        }
    
    def calculate_server_requirements_1m_queries(self) -> Dict:
        """1M sorgu için sunucu gereksinimleri"""
        
        # 1M sorgu/ay = ~33K sorgu/gün = ~1.4K sorgu/saat = ~23 sorgu/dakika
        queries_per_second = 1_000_000 / (30 * 24 * 3600)  # ~0.38 QPS
        peak_qps = queries_per_second * 5  # Peak trafiği 5x varsayalım = ~2 QPS
        
        # Sistemimizin resource kullanımı
        system_requirements = {
            "cpu_per_query": 0.1,      # 100ms CPU time per query
            "memory_per_query": 50,    # 50MB memory per concurrent query
            "storage_per_business": 1,  # 1GB per business (ürün veritabanı)
        }
        
        # Sunucu spekleri
        server_specs = {
            "cpu_cores": 4,             # 4 vCPU yeterli
            "ram_gb": 16,               # 16GB RAM
            "storage_gb": 100,          # 100GB SSD (100 işletme için)
            "bandwidth_gb": 1000,       # 1TB bandwidth/ay
        }
        
        # Cloud provider maliyetleri (AWS/DigitalOcean benzeri)
        monthly_costs = {
            "compute": 150,             # 4 vCPU, 16GB RAM
            "storage": 20,              # 100GB SSD
            "bandwidth": 30,            # 1TB transfer
            "load_balancer": 25,        # Load balancer
            "backup": 15,               # Automated backups
            "monitoring": 10,           # Monitoring tools
        }
        
        total_server_cost = sum(monthly_costs.values())
        
        return {
            "traffic_analysis": {
                "queries_per_month": 1_000_000,
                "queries_per_day": 33_333,
                "queries_per_hour": 1_389,
                "queries_per_second_avg": round(queries_per_second, 2),
                "queries_per_second_peak": round(peak_qps, 2)
            },
            
            "server_specs": server_specs,
            "monthly_costs_usd": monthly_costs,
            "total_monthly_cost_usd": total_server_cost,
            "total_monthly_cost_try": total_server_cost * self.usd_to_try,
            "cost_per_query": (total_server_cost * self.usd_to_try) / 1_000_000
        }
    
    def calculate_additional_costs(self) -> Dict:
        """Ek maliyetler"""
        
        additional_costs = {
            "database_hosting": {
                "description": "PostgreSQL/MongoDB hosting",
                "monthly_cost_try": 200,
                "reason": "Ürün veritabanı, kullanıcı verileri"
            },
            
            "cdn_bandwidth": {
                "description": "CDN ve static file serving",
                "monthly_cost_try": 100,
                "reason": "Web interface, static assets"
            },
            
            "ssl_certificates": {
                "description": "SSL sertifikaları",
                "monthly_cost_try": 50,
                "reason": "HTTPS güvenliği"
            },
            
            "domain_dns": {
                "description": "Domain ve DNS yönetimi",
                "monthly_cost_try": 30,
                "reason": "Domain hosting"
            },
            
            "error_tracking": {
                "description": "Sentry/Bugsnag error tracking",
                "monthly_cost_try": 80,
                "reason": "Hata takibi ve monitoring"
            },
            
            "uptime_monitoring": {
                "description": "Uptime monitoring servisi",
                "monthly_cost_try": 40,
                "reason": "Sistem durumu takibi"
            }
        }
        
        total_additional = sum(cost["monthly_cost_try"] for cost in additional_costs.values())
        
        return {
            "breakdown": additional_costs,
            "total_monthly_cost": total_additional,
            "cost_per_query": total_additional / 1_000_000
        }
    
    def generate_comprehensive_cost_report(self) -> Dict:
        """Kapsamlı maliyet raporu"""
        
        architecture = self.analyze_system_architecture()
        gemini_costs = self.calculate_gemini_costs_1m_queries()
        server_costs = self.calculate_server_requirements_1m_queries()
        additional_costs = self.calculate_additional_costs()
        
        # Toplam maliyetler
        total_monthly_cost = (
            gemini_costs["costs_try"]["total_monthly_cost"] +
            server_costs["total_monthly_cost_try"] +
            additional_costs["total_monthly_cost"]
        )
        
        cost_per_query = total_monthly_cost / 1_000_000
        
        return {
            "system_architecture": architecture,
            "gemini_analysis": gemini_costs,
            "server_analysis": server_costs,
            "additional_costs": additional_costs,
            
            "summary": {
                "gemini_cost_try": gemini_costs["costs_try"]["total_monthly_cost"],
                "server_cost_try": server_costs["total_monthly_cost_try"],
                "additional_cost_try": additional_costs["total_monthly_cost"],
                "total_monthly_cost": total_monthly_cost,
                "cost_per_query": cost_per_query,
                
                "cost_breakdown_percentage": {
                    "gemini": (gemini_costs["costs_try"]["total_monthly_cost"] / total_monthly_cost) * 100,
                    "server": (server_costs["total_monthly_cost_try"] / total_monthly_cost) * 100,
                    "additional": (additional_costs["total_monthly_cost"] / total_monthly_cost) * 100
                }
            }
        }

def main():
    """Ana rapor"""
    calculator = TechnicalCostCalculator()
    report = calculator.generate_comprehensive_cost_report()
    
    print("🔧 TEKNİK MALİYET ANALİZİ - 1M SORGU/AY")
    print("=" * 60)
    
    # Sistem mimarisi
    arch = report["system_architecture"]
    print(f"\n🏗️ SİSTEM MİMARİSİ:")
    print(f"LLM Kullanım Oranı: %{arch['llm_usage_ratio']['llm_based']*100:.0f}")
    print(f"Rule-based Oranı: %{arch['llm_usage_ratio']['rule_based']*100:.0f}")
    
    # Gemini maliyetleri
    gemini = report["gemini_analysis"]
    print(f"\n🤖 GEMİNİ 2.0 FLASH MALİYETLERİ:")
    print(f"Toplam Sorgu: {gemini['total_queries']:,}")
    print(f"LLM'e Giden: {gemini['llm_queries']:,} (%{gemini['llm_usage_percentage']})")
    print(f"Rule-based: {gemini['rule_based_queries']:,}")
    print(f"Toplam Token: {gemini['token_usage']['total_input_tokens'] + gemini['token_usage']['total_output_tokens']:,}")
    print(f"Aylık Maliyet: {gemini['costs_try']['total_monthly_cost']:.0f} TL")
    print(f"Sorgu Başı: {gemini['costs_try']['cost_per_query']:.6f} TL")
    
    # Sunucu maliyetleri
    server = report["server_analysis"]
    print(f"\n🖥️ SUNUCU GEREKSİNİMLERİ:")
    print(f"Ortalama QPS: {server['traffic_analysis']['queries_per_second_avg']}")
    print(f"Peak QPS: {server['traffic_analysis']['queries_per_second_peak']}")
    print(f"Sunucu Spec: {server['server_specs']['cpu_cores']} vCPU, {server['server_specs']['ram_gb']}GB RAM")
    print(f"Aylık Maliyet: {server['total_monthly_cost_try']:.0f} TL")
    print(f"Sorgu Başı: {server['cost_per_query']:.6f} TL")
    
    # Ek maliyetler
    additional = report["additional_costs"]
    print(f"\n💾 EK MALİYETLER:")
    for service, details in additional["breakdown"].items():
        print(f"{details['description']}: {details['monthly_cost_try']} TL")
    print(f"Toplam Ek: {additional['total_monthly_cost']} TL")
    
    # Özet
    summary = report["summary"]
    print(f"\n📊 ÖZET (1M SORGU/AY):")
    print(f"Gemini Maliyeti: {summary['gemini_cost_try']:.0f} TL (%{summary['cost_breakdown_percentage']['gemini']:.0f})")
    print(f"Sunucu Maliyeti: {summary['server_cost_try']:.0f} TL (%{summary['cost_breakdown_percentage']['server']:.0f})")
    print(f"Ek Maliyetler: {summary['additional_cost_try']:.0f} TL (%{summary['cost_breakdown_percentage']['additional']:.0f})")
    print(f"TOPLAM: {summary['total_monthly_cost']:.0f} TL")
    print(f"SORGU BAŞI: {summary['cost_per_query']:.6f} TL")

if __name__ == "__main__":
    main()