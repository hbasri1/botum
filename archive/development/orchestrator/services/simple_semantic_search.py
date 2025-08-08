#!/usr/bin/env python3
"""
Simple Semantic Search
"""

import json
import logging
import asyncio
import os
from typing import Dict, List, Optional, Any
import numpy as np
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

class SimpleSemanticSearch:
    def __init__(self):
        self.products = []
        self.product_embeddings = {}
        self.query_cache = {}
        self.conversation_context = {}  # MVP: Simple context storage
        self._initialize_google_ai()
        self._load_products()
    
    def _initialize_google_ai(self):
        """Google AI'yi initialize et"""
        try:
            # .env dosyasından API key al
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key or api_key == 'your-gemini-api-key-here':
                logger.warning("GEMINI_API_KEY not set or using mock key, embeddings will use fallback")
                return
            
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            logger.info("Google AI initialized for embeddings")
        except Exception as e:
            logger.error(f"Google AI initialization error: {str(e)}")
    
    def _load_products(self):
        try:
            products_path = os.path.join(os.path.dirname(__file__), '../../data/products.json')
            if os.path.exists(products_path):
                with open(products_path, 'r', encoding='utf-8') as f:
                    self.products = json.load(f)
                logger.info(f"Loaded {len(self.products)} products")
            else:
                self.products = []
        except Exception as e:
            logger.error(f"Error loading products: {str(e)}")
            self.products = []
    
    def _create_rich_text(self, product: Dict[str, Any]) -> str:
        text_parts = []
        
        name = product.get('name')
        if name:
            text_parts.append(f"Ürün: {name}")
        
        category = product.get('category')
        if category:
            text_parts.append(f"Kategori: {category}")
        
        color = product.get('color')
        if color:
            text_parts.append(f"Renk: {color}")
        
        price = product.get('final_price')
        if price:
            text_parts.append(f"Fiyat: {price} TL")
        
        keywords = []
        name_lower = product.get('name', '').lower()
        
        if 'hamile' in name_lower or 'lohusa' in name_lower:
            keywords.extend(['hamile', 'lohusa', 'anne'])
        
        if 'afrika' in name_lower:
            keywords.extend(['afrika', 'etnik'])
        
        if 'takım' in name_lower or 'alt' in name_lower or 'üst' in name_lower:
            keywords.extend(['takım', 'set'])
        
        if 'dantelli' in name_lower:
            keywords.extend(['dantelli', 'dantel'])
        
        if keywords:
            text_parts.append(f"Özellikler: {', '.join(keywords)}")
        
        return '. '.join(text_parts) + '.'
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        try:
            if text in self.query_cache:
                return self.query_cache[text]
            
            # Real Google Embedding API
            try:
                import google.generativeai as genai
                
                # Use text-embedding-004 model
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="semantic_similarity"
                )
                
                embedding = result['embedding']
                self.query_cache[text] = embedding
                
                logger.debug(f"Generated embedding for text: {text[:50]}...")
                return embedding
                
            except Exception as api_error:
                logger.warning(f"Google Embedding API error: {str(api_error)}, falling back to mock")
                
                # Fallback to mock embedding
                import hashlib
                text_hash = hashlib.md5(text.encode()).hexdigest()
                np.random.seed(int(text_hash[:8], 16))
                embedding = np.random.normal(0, 1, 768).tolist()
                
                self.query_cache[text] = embedding
                return embedding
            
        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            return None
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity error: {str(e)}")
            return 0.0
    
    def _hybrid_score(self, query: str, product: Dict[str, Any], semantic_similarity: float) -> float:
        try:
            semantic_score = max(0, semantic_similarity)
            
            product_name = product.get('name', '').lower()
            query_lower = query.lower()
            
            fuzzy_score = fuzz.token_set_ratio(query_lower, product_name) / 100.0
            
            bonus = 0.0
            
            # MVP Enhanced Scoring
            query_words = query_lower.split()
            product_words = product_name.split()
            
            # Exact word matches
            for word in query_words:
                if word in product_words:
                    bonus += 0.1
            
            # Hamile/lohusa bonus
            if any(word in query_lower for word in ['hamile', 'lohusa']):
                if any(word in product_name for word in ['hamile', 'lohusa']):
                    bonus += 0.2
            
            # Takım bonus
            if 'takım' in query_lower:
                if 'takım' in product_name or any(word in product_name for word in ['alt', 'üst']):
                    bonus += 0.15
            
            # MVP: Dekolte bonus (kritik özellik)
            if 'dekolte' in query_lower or 'dekolteli' in query_lower:
                if 'dekolteli' in product_name:
                    bonus += 0.25
            
            # MVP: Göğüs + Sırt kombinasyonu (çok spesifik)
            if 'göğüs' in query_lower and 'sırt' in query_lower:
                if 'göğüs' in product_name and 'sırt' in product_name:
                    bonus += 0.35  # Büyük bonus
                    
                    # Takım aranıyorsa takım ürünlerine ekstra bonus
                    if 'takım' in query_lower and 'takım' in product_name:
                        bonus += 0.25  # Çok büyük bonus
            
            # MVP: Şort takım bonus
            if 'şort' in query_lower:
                if 'şort' in product_name:
                    bonus += 0.2
            
            # MVP: Brode bonus
            if 'brode' in query_lower:
                if 'brode' in product_name:
                    bonus += 0.15
            
            hybrid_score = (semantic_score * 0.6) + (fuzzy_score * 0.4) + bonus
            return min(1.0, hybrid_score)
            
        except Exception as e:
            logger.error(f"Hybrid scoring error: {str(e)}")
            return semantic_similarity
    
    async def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        try:
            if not self.products:
                return []
            
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                return self._fallback_fuzzy_search(query, limit)
            
            scored_products = []
            
            for product in self.products:
                try:
                    product_id = product.get('code', str(product.get('id', '')))
                    
                    if product_id not in self.product_embeddings:
                        rich_text = self._create_rich_text(product)
                        product_embedding = await self._get_embedding(rich_text)
                        if product_embedding:
                            self.product_embeddings[product_id] = product_embedding
                    
                    product_embedding = self.product_embeddings.get(product_id)
                    if not product_embedding:
                        continue
                    
                    semantic_similarity = self._calculate_similarity(query_embedding, product_embedding)
                    final_score = self._hybrid_score(query, product, semantic_similarity)
                    
                    if final_score > 0.3:
                        scored_products.append({
                            'product': product,
                            'similarity': final_score,
                            'semantic_similarity': semantic_similarity
                        })
                        
                except Exception as e:
                    continue
            
            scored_products.sort(key=lambda x: x['similarity'], reverse=True)
            
            results = []
            for item in scored_products[:limit]:
                product = item['product']
                results.append({
                    'id': product.get('id', 0),
                    'name': product.get('name', ''),
                    'price': float(product.get('final_price', 0)),
                    'original_price': float(product.get('price', 0)) if product.get('price') else None,
                    'stock_quantity': int(product.get('stock', 0)),
                    'category': product.get('category', ''),
                    'color': product.get('color', ''),
                    'size': product.get('size', ''),
                    'code': product.get('code', ''),
                    'discount': product.get('discount', ''),
                    'similarity': item['similarity'],
                    'semantic_similarity': item['semantic_similarity']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return self._fallback_fuzzy_search(query, limit)
    
    def _fallback_fuzzy_search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        try:
            scored_products = []
            query_lower = query.lower()
            
            for product in self.products:
                product_name = product.get('name', '').lower()
                score = fuzz.token_set_ratio(query_lower, product_name)
                
                if score > 60:
                    scored_products.append({
                        'product': product,
                        'score': score
                    })
            
            scored_products.sort(key=lambda x: x['score'], reverse=True)
            
            results = []
            for item in scored_products[:limit]:
                product = item['product']
                results.append({
                    'id': product.get('id', 0),
                    'name': product.get('name', ''),
                    'price': float(product.get('final_price', 0)),
                    'original_price': float(product.get('price', 0)) if product.get('price') else None,
                    'stock_quantity': int(product.get('stock', 0)),
                    'category': product.get('category', ''),
                    'color': product.get('color', ''),
                    'size': product.get('size', ''),
                    'code': product.get('code', ''),
                    'discount': product.get('discount', ''),
                    'similarity': item['score'] / 100.0
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback search error: {str(e)}")
            return []
    
    async def find_best_match(self, query: str) -> Optional[Dict[str, Any]]:
        results = await self.search(query, limit=1)
        return results[0] if results else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Search engine istatistikleri"""
        return {
            'total_products': len(self.products),
            'cached_embeddings': len(self.product_embeddings),
            'cached_queries': len(self.query_cache)
        }

# Test
async def test_search():
    search = SimpleSemanticSearch()
    result = await search.find_best_match("hamile lohusa takım")
    if result:
        print(f"Found: {result['name']} - {result['price']} TL")
    else:
        print("Not found")

    def store_context(self, session_id: str, product_name: str):
        """MVP: Store conversation context"""
        import time
        self.conversation_context[session_id] = {
            "last_product": product_name,
            "timestamp": time.time()
        }
    
    def get_context(self, session_id: str) -> Optional[str]:
        """MVP: Get conversation context"""
        import time
        context = self.conversation_context.get(session_id)
        if context:
            # 5 minute timeout
            if time.time() - context["timestamp"] < 300:
                return context["last_product"]
            else:
                # Cleanup expired context
                del self.conversation_context[session_id]
        return None

if __name__ == "__main__":
    asyncio.run(test_search())

# Global instance for easy import
try:
    semantic_search = SimpleSemanticSearch()
except Exception as e:
    print(f"Error creating semantic search instance: {e}")
    semantic_search = None