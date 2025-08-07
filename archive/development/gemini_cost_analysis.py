#!/usr/bin/env python3
"""
Gemini 1.5 Flash Maliyet Analizi - 1 Milyon Sorgu/Ay
"""

def calculate_gemini_costs():
    """Gemini 1.5 Flash maliyet hesaplaması"""
    
    # Gemini 1.5 Flash fiyatları (Aralık 2024)
    input_cost_per_1k_tokens = 0.000075  # $0.000075 per 1K input tokens
    output_cost_per_1k_tokens = 0.0003   # $0.0003 per 1K output tokens
    
    # Ortalama token kullanımı (tahmin)
    avg_input_tokens_per_query = 150     # Kullanıcı sorusu + system prompt
    avg_output_tokens_per_query = 100    # Bot cevabı
    
    # Aylık sorgu sayısı
    monthly_queries = 1_000_000
    
    # Maliyet hesaplamaları
    monthly_input_tokens = monthly_queries * avg_input_tokens_per_query
    monthly_output_tokens = monthly_queries * avg_output_tokens_per_query
    
    monthly_input_cost = (monthly_input_tokens / 1000) * input_cost_per_1k_tokens
    monthly_output_cost = (monthly_output_tokens / 1000) * output_cost_per_1k_tokens
    
    total_monthly_cost = monthly_input_cost + monthly_output_cost
    
    # Sonuçları yazdır
    print("🔍 Gemini 1.5 Flash Maliyet Analizi")
    print("=" * 50)
    print(f"📊 Aylık Sorgu Sayısı: {monthly_queries:,}")
    print(f"📝 Ortalama Input Token/Sorgu: {avg_input_tokens_per_query}")
    print(f"💬 Ortalama Output Token/Sorgu: {avg_output_tokens_per_query}")
    print()
    print("💰 Maliyet Detayları:")
    print(f"   • Input Tokens/Ay: {monthly_input_tokens:,}")
    print(f"   • Output Tokens/Ay: {monthly_output_tokens:,}")
    print(f"   • Input Maliyeti: ${monthly_input_cost:.2f}")
    print(f"   • Output Maliyeti: ${monthly_output_cost:.2f}")
    print(f"   • TOPLAM AYLIK MALİYET: ${total_monthly_cost:.2f}")
    print()
    print("📈 Diğer Metrikler:")
    print(f"   • Sorgu Başına Maliyet: ${total_monthly_cost/monthly_queries:.6f}")
    print(f"   • Günlük Maliyet: ${total_monthly_cost/30:.2f}")
    print(f"   • Yıllık Maliyet: ${total_monthly_cost*12:.2f}")
    
    # Farklı senaryolar
    print("\n🎯 Farklı Senaryolar:")
    
    scenarios = [
        ("Düşük Kullanım", 100, 50),
        ("Orta Kullanım", 150, 100),
        ("Yoğun Kullanım", 200, 150),
        ("Çok Yoğun", 300, 200)
    ]
    
    for scenario_name, input_tokens, output_tokens in scenarios:
        input_cost = (monthly_queries * input_tokens / 1000) * input_cost_per_1k_tokens
        output_cost = (monthly_queries * output_tokens / 1000) * output_cost_per_1k_tokens
        total_cost = input_cost + output_cost
        print(f"   • {scenario_name}: ${total_cost:.2f}/ay")
    
    # Optimizasyon önerileri
    print("\n💡 Maliyet Optimizasyon Önerileri:")
    print("   1. Cache sistemi ile tekrar eden sorguları azalt (%30-50 tasarruf)")
    print("   2. Kısa cevaplar için output token'ları optimize et")
    print("   3. System prompt'u kısalt (input token tasarrufu)")
    print("   4. Batch processing ile API çağrılarını optimize et")
    print("   5. Function calling ile gereksiz LLM çağrılarını azalt")
    
    # Cache ile tasarruf hesabı
    cache_hit_rates = [30, 50, 70]
    print("\n📊 Cache Tasarrufu Analizi:")
    for hit_rate in cache_hit_rates:
        savings = total_monthly_cost * (hit_rate / 100)
        new_cost = total_monthly_cost - savings
        print(f"   • %{hit_rate} Cache Hit Rate: ${new_cost:.2f}/ay (${savings:.2f} tasarruf)")

if __name__ == "__main__":
    calculate_gemini_costs()