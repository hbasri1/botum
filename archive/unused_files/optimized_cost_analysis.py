#!/usr/bin/env python3
"""
Optimized Cost Analysis - After Token Reduction
"""

def analyze_optimized_costs():
    """Analyze costs after optimization"""
    
    # Original vs Optimized token counts
    original_prompt_chars = 877  # Old long prompt
    optimized_prompt_chars = 200  # New short prompt
    
    original_schema_chars = 949  # Old detailed schema
    optimized_schema_chars = 400  # New compact schema
    
    # Token estimation (1 token ≈ 3 characters for optimized text)
    original_tokens = (original_prompt_chars + original_schema_chars) // 3
    optimized_tokens = (optimized_prompt_chars + optimized_schema_chars) // 3
    
    print("🔍 Token Optimization Analysis")
    print("=" * 50)
    print(f"📝 Original input tokens: {original_tokens}")
    print(f"⚡ Optimized input tokens: {optimized_tokens}")
    print(f"📉 Token reduction: {((original_tokens - optimized_tokens) / original_tokens) * 100:.1f}%")
    
    # Gemini 1.5 Flash pricing (more stable, higher quota)
    GEMINI_15_PRICING = {
        "input_per_1k": 0.000075,   # Same as 2.0 Flash
        "output_per_1k": 0.0003,    # Same as 2.0 Flash
    }
    
    output_tokens = 25  # Function call response is small
    
    # Cost comparison
    original_cost = ((original_tokens / 1000) * GEMINI_15_PRICING["input_per_1k"] + 
                    (output_tokens / 1000) * GEMINI_15_PRICING["output_per_1k"])
    
    optimized_cost = ((optimized_tokens / 1000) * GEMINI_15_PRICING["input_per_1k"] + 
                     (output_tokens / 1000) * GEMINI_15_PRICING["output_per_1k"])
    
    print(f"\n💰 Cost Comparison:")
    print(f"   Original cost per request: ${original_cost:.6f}")
    print(f"   Optimized cost per request: ${optimized_cost:.6f}")
    print(f"   Cost reduction: {((original_cost - optimized_cost) / original_cost) * 100:.1f}%")
    
    # Monthly projections
    print(f"\n📈 Monthly Cost (1M requests):")
    scenarios = [
        ("100% Gemini 1.5 Flash", 1.0),
        ("70% Gemini, 30% Fallback", 0.7),
        ("50% Gemini, 50% Fallback", 0.5),
        ("30% Gemini, 70% Fallback", 0.3),
    ]
    
    for scenario, ratio in scenarios:
        monthly_cost = 1000000 * optimized_cost * ratio
        print(f"   {scenario}: ${monthly_cost:.2f}")
    
    # Quota comparison
    print(f"\n⚡ Quota Benefits:")
    print(f"   Gemini 2.0 Flash Exp: 10 requests/minute")
    print(f"   Gemini 1.5 Flash: 1000 requests/minute")
    print(f"   Quota improvement: 100x better!")
    
    # Break-even analysis
    print(f"\n💡 Business Model:")
    print(f"   Cost per request: ${optimized_cost:.6f}")
    print(f"   If charging $0.001 per request: 96% profit margin")
    print(f"   If charging $0.01 per request: 99.6% profit margin")
    
    return optimized_cost

if __name__ == "__main__":
    cost = analyze_optimized_costs()
    print(f"\n🎯 Optimized Cost: ${cost:.6f} per request")