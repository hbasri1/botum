#!/usr/bin/env python3
"""
Mock Semantic Search - Demo için sahte embeddings kullanır
Gerçek API key olmadan sistemi test etmek için
"""

import json
import logging
import os
import pickle
import random
from typing import Dict, List, Optional
import numpy as np
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity

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

class MockSemanticProductSearch:
    """Mock semantic search for demo purposes"""
    
    def __init__(self):
        self.embeddings_file = 'embeddings/mock_product_embeddings.pkl'
        self.product_embeddings: List[ProductEmbedding] = []
        self._load_embeddings()
        
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
        
        if features:
            parts.append(f"Özellikler: {', '.join(features)}")
        
        return ". ".join(parts) + "."
    
    def create_mock_embedding(self, text: str) -> List[float]:
        """Create mock embedding based on text features"""
        # 384 boyutlu mock embedding (sentence-transformers boyutu)
        embedding = np.random.normal(0, 0.1, 384).tolist()
        
        # Text'e göre bazı boyutları ayarla (basit feature matching)
        text_lower = text.lower()
        
        # Hamile/lohusa için özel boyutlar
        if 'hamile' in text_lower or 'lohusa' in text_lower:
            for i in range(10, 20):
                embedding[i] += 0.5
        
        # Renk için özel boyutlar
        if 'siyah' in text_lower:
            for i in range(20, 30):
                embedding[i] += 0.3
        elif 'beyaz' in text_lower or 'ekru' in text_lower:
            for i in range(30, 40):
                embedding[i] += 0.3
        
        # Ürün tipi için özel boyutlar
        if 'pijama' in text_lower:
            for i in range(40, 50):
                embedding[i] += 0.4
        elif 'gecelik' in text_lower:
            for i in range(50, 60):
                embedding[i] += 0.4
        elif 'sabahlık' in text_lower:
            for i in range(60, 70):
                embedding[i] += 0.4
        
        # Dantelli için özel boyutlar
        if 'dantelli' in text_lower:
            for i in range(70, 80):
                embedding[i] += 0.3
        
        # Fiyat aralığı için özel boyutlar
        if 'ekonomik' in text_lower:
            for i in range(80, 90):
                embedding[i] += 0.2
        elif 'premium' in text_lower:
            for i in range(90, 100):
                embedding[i] += 0.2
        
        return embedding
    
    def create_embeddings(self, products: List[Dict]) -> bool:
        """Create mock embeddings for all products"""
        logger.info(f"Creating mock embeddings for {len(products)} products...")
        
        embeddings = []
        for i, product in enumerate(products):
            try:
                # Create rich text
                rich_text = self.create_rich_text(product)
                
                # Create mock embedding
                embedding = self.create_mock_embedding(rich_text)
                
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
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Created {i + 1}/{len(products)} mock embeddings...")
                    
            except Exception as e:
                logger.error(f"Error creating mock embedding for {product.get('name', 'unknown')}: {e}")
                continue
        
        # Save embeddings
        try:
            os.makedirs(os.path.dirname(self.embeddings_file), exist_ok=True)
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(embeddings, f)
            
            self.product_embeddings = embeddings
            logger.info(f"✅ Created and saved {len(embeddings)} mock embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Error saving mock embeddings: {e}")
            return False
    
    def _load_embeddings(self) -> bool:
        """Load existing embeddings"""
        try:
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'rb') as f:
                    self.product_embeddings = pickle.load(f)
                logger.info(f"✅ Loaded {len(self.product_embeddings)} mock embeddings")
                return True
            else:
                logger.info("No existing mock embeddings found")
                return False
        except Exception as e:
            logger.error(f"Error loading mock embeddings: {e}")
            return False
    
    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Perform mock semantic search"""
        if not self.product_embeddings:
            return []
        
        try:
            # Create mock query embedding
            query_embedding = self.create_mock_embedding(query)
            
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
            
            logger.info(f"Mock semantic search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Mock semantic search error: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if mock semantic search is available"""
        return bool(self.product_embeddings)

# Test function
def test_mock_semantic_search():
    """Test mock semantic search system"""
    
    # Load products
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"Error loading products: {e}")
        return
    
    # Initialize mock semantic search
    search_engine = MockSemanticProductSearch()
    
    # Load or create embeddings
    if not search_engine._load_embeddings():
        print("Creating new mock embeddings...")
        if not search_engine.create_embeddings(products):
            print("Failed to create mock embeddings")
            return
    
    # Test searches
    test_queries = [
        "hamile için rahat pijama",
        "siyah dantelli gecelik",
        "ekonomik takım",
        "premium sabahlık",
        "beyaz gecelik",
        "düğmeli pijama"
    ]
    
    print(f"\n🔍 Mock Semantic Search Test:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n👤 Query: {query}")
        results = search_engine.semantic_search(query, 3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['name'][:50]}...")
                print(f"   Renk: {result['color']} - Fiyat: {result['final_price']} TL")
                print(f"   Similarity: {result['similarity']:.3f}")
        else:
            print("   No results found")

if __name__ == "__main__":
    test_mock_semantic_search()