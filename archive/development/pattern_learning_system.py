#!/usr/bin/env python3
"""
Real-time Pattern Learning System - Gemini 2.5 Pro ile
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import google.generativeai as genai

class PatternLearningSystem:
    """Gemini 2.5 Pro ile pattern learning"""
    
    def __init__(self):
        self.gemini_pro = genai.GenerativeModel('gemini-2.5-pro')
        self.pattern_database = []  # Öğrenilen pattern'ler
        self.learning_queue = []    # Analiz bekleyen etkileşimler
        
    async def log_interaction(self, query: str, intent: str, response: str, 
                            success: bool, user_feedback: float = None):
        """Kullanıcı etkileşimini logla"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "detected_intent": intent,
            "response": response,
            "success": success,
            "user_feedback": user_feedback,
            "confidence": 0.8  # Mevcut sistemden
        }
        
        self.learning_queue.append(interaction)
        
        # 10 etkileşim birikince analiz yap
        if len(self.learning_queue) >= 10:
            await self.analyze_patterns()
    
    async def analyze_patterns(self):
        """Gemini 2.5 Pro ile pattern analizi"""
        
        # Son etkileşimleri al
        recent_interactions = self.learning_queue[-10:]
        
        # Gemini'ye gönderilecek prompt
        analysis_prompt = f"""
Sen bir chatbot pattern analisti olarak çalışıyorsın. Aşağıdaki kullanıcı etkileşimlerini analiz et ve yeni pattern'ler öner.

ETKILEŞIMLER:
{json.dumps(recent_interactions, indent=2, ensure_ascii=False)}

GÖREVLER:
1. Başarısız sorguları analiz et ve neden başarısız olduğunu belirle
2. Başarılı pattern'leri tespit et ve benzerlerini öner
3. Yeni intent pattern'leri oluştur
4. Türkçe dil özelliklerini (ek, çekim vb.) dikkate al

ÇIKTI FORMATI (JSON):
{{
  "failed_queries_analysis": [
    {{
      "query": "sorgu metni",
      "failure_reason": "neden başarısız",
      "suggested_fix": "önerilen çözüm"
    }}
  ],
  "new_patterns": [
    {{
      "pattern_text": "yeni pattern",
      "intent": "intent türü",
      "confidence_threshold": 0.8,
      "examples": ["örnek1", "örnek2"]
    }}
  ],
  "optimization_suggestions": [
    "öneri 1",
    "öneri 2"
  ]
}}
"""
        
        try:
            # Gemini 2.5 Pro'ya gönder
            response = await self.gemini_pro.generate_content_async(analysis_prompt)
            analysis_result = json.loads(response.text)
            
            # Öğrenilen pattern'leri kaydet
            await self.save_learned_patterns(analysis_result)
            
            # Queue'yu temizle
            self.learning_queue = []
            
            print(f"✅ Pattern analysis completed: {len(analysis_result.get('new_patterns', []))} new patterns learned")
            
        except Exception as e:
            print(f"❌ Pattern analysis failed: {e}")
    
    async def save_learned_patterns(self, analysis: Dict):
        """Öğrenilen pattern'leri sisteme entegre et"""
        
        # Yeni pattern'leri database'e ekle
        for pattern in analysis.get("new_patterns", []):
            self.pattern_database.append({
                "id": len(self.pattern_database) + 1,
                "pattern": pattern["pattern_text"],
                "intent": pattern["intent"],
                "confidence": pattern["confidence_threshold"],
                "examples": pattern["examples"],
                "learned_at": datetime.now().isoformat(),
                "usage_count": 0
            })
        
        # Dosyaya kaydet (production'da database'e)
        with open("learned_patterns.json", "w", encoding="utf-8") as f:
            json.dump(self.pattern_database, f, indent=2, ensure_ascii=False)
        
        print(f"💾 {len(analysis.get('new_patterns', []))} pattern saved to database")

# Kullanım örneği
async def demo_pattern_learning():
    learner = PatternLearningSystem()
    
    # Örnek başarısız etkileşimler
    failed_interactions = [
        ("afrika geceliği", "intent_detection", "Anlayamadım", False),
        ("hangi ürünler var", "intent_detection", "Anlayamadım", False),
        ("stokta ne var", "intent_detection", "Anlayamadım", False),
    ]
    
    # Başarılı etkileşimler
    successful_interactions = [
        ("afrika gecelik fiyatı", "function_calling", "565.44 TL", True),
        ("hamile pijama var mı", "function_calling", "Stokta mevcut", True),
    ]
    
    # Etkileşimleri logla
    for query, intent, response, success in failed_interactions + successful_interactions:
        await learner.log_interaction(query, intent, response, success)

if __name__ == "__main__":
    asyncio.run(demo_pattern_learning())