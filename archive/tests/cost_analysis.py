#!/usr/bin/env python3
"""
LLM Cost Analysis for MVP Chatbot System
"""

import json
from final_mvp_system import FinalMVPChatbot

def analyze_token_usage():
    """Analyze token usage and calculate costs"""
    
    # Gemini 2.0 Flash pricing (as of 2024)
    GEMINI_PRICING = {
        "input_tokens_per_1k": 0.000075,  # $0.000075 per 1K input tokens
        "output_tokens_per_1k": 0.0003,   # $0.0003 per 1K output tokens
    }
    
    # Estimate average tokens per request
    ESTIMATED_TOKENS = {
        "system_prompt": 200,      # Our function calling prompt
        "user_query": 15,          # Average user message
        "function_call": 50,       # Function call response
        "total_input": 265,        # system + user + context
        "total_output": 50         # function call response
    }
    
    print("🔍 LLM Token Usage Analysis")
    print("=" * 50)
    
    # Per request cost
    input_cost_per_request = (ESTIMATED_TOKENS["total_input"] / 1000) * GEMINI_PRICING["input_tokens_per_1k"]
    output_cost_per_request = (ESTIMATED_TOKENS["total_output"] / 1000) * GEMINI_PRICING["output_tokens_per_1k"]
    total_cost_per_request = input_cost_per_request + output_cost_per_request
    
    print(f"📊 Per Request Analysis:")
    print(f"   Input tokens: ~{ESTIMATED_TOKENS['total_input']}")
    print(f"   Output tokens: ~{ESTIMATED_TOKENS['total_output']}")
    print(f"   Cost per request: ${total_cost_per_request:.6f}")
    
    # Monthly projections
    monthly_requests = [1000, 10000, 100000, 1000000]
    
    print(f"\n💰 Monthly Cost Projections:")
    for requests in monthly_requests:
        monthly_cost = requests * total_cost_per_request
        print(f"   {requests:,} requests/month: ${monthly_cost:.2f}")
    
    # Fallback usage estimation
    print(f"\n🔄 Fallback System Impact:")
    print(f"   With 20% fallback usage: ${1000000 * total_cost_per_request * 0.8:.2f}/month for 1M requests")
    print(f"   With 50% fallback usage: ${1000000 * total_cost_per_request * 0.5:.2f}/month for 1M requests")
    
    # Cost optimization suggestions
    print(f"\n💡 Cost Optimization:")
    print(f"   - Fallback system reduces costs significantly")
    print(f"   - Caching common queries can reduce LLM calls")
    print(f"   - Batch processing for similar queries")
    
    return total_cost_per_request

if __name__ == "__main__":
    cost_per_request = analyze_token_usage()
    print(f"\n🎯 Bottom Line: ${cost_per_request:.6f} per request")