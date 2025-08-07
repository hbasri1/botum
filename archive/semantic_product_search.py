#!/usr/bin/env python3
"""
Semantic Product Search - Production Ready
Uses Google Gemini embeddings for better product matching
"""

import json
import logging
import os
import pickle
import time
from typing import Dict, List, Optional, Any
import numpy as np
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class ProductEmbedding:
    """Product embedding model"""
    name: str
    color: str
    price: float
    final_price: float
    category: str
    stock: int
    embedding: List[float]
    rich_text: str

class SemanticProductSearch:
    """Semantic search for products using Google Gemini embeddings"""
    
    def __init__(self):
        self.embeddings_file = 'embeddings/product_embeddings.pkl'
        self.product_embeddings: List[ProductEmbedding] = []
        self.genai = None
        self._setup_google_ai()
        self._load_embeddings()
        
    def _setup_google_ai(self):
        """Setup Google Generative AI for embeddings"""
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.genai = genai
                logger.info("✅ Google Generative AI initialized for embeddings")
            except ImportError:
                logger.error("❌ google-generativeai package not found. Install with: pip install google-generativeai")
                self.genai = None
        else:
            logger.warning("⚠️ GEMINI_API_KEY not found, semantic search disabled")
            self.genai = None
    
    def create_rich_text(self, product: Dict) -> str:
        """Create rich text for embedding"""
        parts = []
        
        # Product name
        if name := product.get('name'):
            parts.append(f"Ürün: {name}")
        
        # Color
        if color := product.get('color'):
            parts.append(f"Renk: {color}")
        
        # Category
        if category := product.get('category'):
            parts.append(f"Kategori: {category}")
        
        # Price range
        if price := product.get('final_price'):
            parts.append(f"Fiyat: {price} TL")
            if price < 1000:
                parts.append("Ekonomik fiyat")
            elif price < 2000:
                parts.append("Orta segment fiyat")
            else:
                parts.append("Premium fiyat")
        
        # Extract features from name
        name_lower = product.get('name', '').lower()
        features = []
        
        if 'hamile' in name_lower or 'lohusa' in name_lower:
            features.append('hamile ve lohusa için uygun')
        if 'dantelli' in name_lower:
            features.append('dantelli süsleme')
        if 'düğmeli' in name_lower:
            features.append('düğmeli kapama')
        if 'askılı' in name_lower:
            features.append('askılı model')
        if 'takım' in name_lower:
            features.append('takım ürün')
        if 'gecelik' in name_lower:
            features.append('gecelik')
        if 'pijama' in name_lower:
            features.append('pijama')
        if 'sabahlık' in name_lower:
            features.append('sabahlık')
        if 'elbise' in name_lower:
            features.append('elbise')
        if 'şort' in name_lower:
            features.append('şort')
        if 'tulum' in name_lower:
            features.append('tulum')
        
        if features:
            parts.append(f"Özellikler: {', '.join(features)}")
        
        return ". ".join(parts) + "."
    
    def get_embedding_sync(self, text: str) -> Optional[List[float]]:
        """Get embedding from Google Generative AI"""
        if not self.genai:
            return None
        
        try:
            # Google'ın text-embedding-004 modelini kullan
            result = self.genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Google embedding error: {e}")
            return None
    
    def create_embeddings(self, products: List[Dict]) -> bool:
        """Create embeddings for all products with rate limiting"""
        if not self.genai:
            logger.warning("Google AI not available, skipping embedding creation")
            return False
        
        logger.info(f"Creating embeddings for {len(products)} products...")
        
        embeddings = []
        batch_size = 10  # Küçük batch size
        delay = 2  # 2 saniye bekleme
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            
            for j, product in enumerate(batch):
                try:
                    # Create rich text
                    rich_text = self.create_rich_text(product)
                    
                    # Get embedding with retry
                    embedding = None
                    for retry in range(3):
                        try:
                            embedding = self.get_embedding_sync(rich_text)
                            if embedding:
                                break
                        except Exception as e:
                            if retry < 2:
                                logger.warning(f"Retry {retry + 1} for {product.get('name', 'unknown')}: {e}")
                                time.sleep(delay * (retry + 1))
                            else:
                                logger.error(f"Failed after 3 retries for {product.get('name', 'unknown')}: {e}")
                    
                    if not embedding:
                        continue
                    
                    # Create ProductEmbedding
                    product_embedding = ProductEmbedding(
                        name=product['name'],
                        color=product['color'],
                        price=product['price'],
                        final_price=product['final_price'],
                        category=product['category'],
                        stock=product['stock'],
                        embedding=embedding,
                        rich_text=rich_text
                    )
                    
                    embeddings.append(product_embedding)
                    
                    # Rate limiting
                    time.sleep(0.5)  # 500ms delay between requests
                    
                except Exception as e:
                    logger.error(f"Error creating embedding for {product.get('name', 'unknown')}: {e}")
                    continue
            
            # Batch completed
            logger.info(f"Batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size} completed. Total embeddings: {len(embeddings)}")
            
            # Longer delay between batches
            if i + batch_size < len(products):
                time.sleep(delay)
        
        # Save embeddings
        try:
            os.makedirs(os.path.dirname(self.embeddings_file), exist_ok=True)
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(embeddings, f)
            
            self.product_embeddings = embeddings
            logger.info(f"✅ Created and saved {len(embeddings)} embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            return False
    
    def _load_embeddings(self) -> bool:
        """Load existing embeddings"""
        try:
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'rb') as f:
                    self.product_embeddings = pickle.load(f)
                logger.info(f"✅ Loaded {len(self.product_embeddings)} embeddings")
                return True
            else:
                logger.info("No existing embeddings found")
                return False
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return False
    
    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Perform semantic search"""
        if not self.product_embeddings or not self.genai:
            return []
        
        try:
            # Get query embedding
            query_embedding = self.get_embedding_sync(query)
            if not query_embedding:
                return []
            
            # Calculate similarities
            similarities = []
            query_vec = np.array(query_embedding).reshape(1, -1)
            
            for product_emb in self.product_embeddings:
                product_vec = np.array(product_emb.embedding).reshape(1, -1)
                similarity = cosine_similarity(query_vec, product_vec)[0][0]
                
                similarities.append({
                    'product': product_emb,
                    'similarity': float(similarity)
                })
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Convert to product format
            results = []
            for item in similarities[:limit]:
                product = item['product']
                results.append({
                    'name': product.name,
                    'color': product.color,
                    'price': product.price,
                    'final_price': product.final_price,
                    'category': product.category,
                    'stock': product.stock,
                    'similarity': item['similarity']
                })
            
            logger.info(f"Semantic search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if semantic search is available"""
        return bool(self.genai and self.product_embeddings)

# Test function
def test_semantic_search():
    """Test semantic search system"""
    
    # Load products
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"Error loading products: {e}")
        return
    
    # Initialize semantic search
    search_engine = SemanticProductSearch()
    
    # Load or create embeddings
    if not search_engine._load_embeddings():
        print("Creating new embeddings...")
        if not search_engine.create_embeddings(products):
            print("Failed to create embeddings")
            return
    
    # Test searches
    test_queries = [
        "hamile için rahat pijama",
        "gece için şık bir şey",
        "dantelli gecelik",
        "siyah renkte takım",
        "ekonomik fiyatlı ürün",
        "premium sabahlık"
    ]
    
    print(f"\n🔍 Semantic Search Test:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n👤 Query: {query}")
        results = search_engine.semantic_search(query, 3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['name'][:60]}...")
                print(f"   Renk: {result['color']} - Fiyat: {result['final_price']} TL")
                print(f"   Similarity: {result['similarity']:.3f}")
        else:
            print("   No results found")

if __name__ == "__main__":
    test_semantic_search()