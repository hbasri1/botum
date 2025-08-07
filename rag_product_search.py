#!/usr/bin/env python3
"""
RAG-based Product Search System
Gerçek embeddings ile ürün arama sistemi
"""

import json
import logging
import os
import pickle
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class ProductEmbedding:
    """Product embedding with metadata"""
    name: str
    color: str
    price: float
    final_price: float
    category: str
    stock: int
    embedding: np.ndarray
    features: List[str]
    search_text: str

class RAGProductSearch:
    """RAG-based product search with real embeddings"""
    
    def __init__(self):
        self.embeddings_file = 'embeddings/rag_product_embeddings.pkl'
        self.vectorizer_file = 'embeddings/tfidf_vectorizer.pkl'
        self.product_embeddings: List[ProductEmbedding] = []
        self.vectorizer = None
        self.tfidf_matrix = None
        
        # Setup Gemini for query enhancement (optional)
        self._setup_gemini()
        
        # Load or create embeddings
        self._load_or_create_embeddings()
    
    def _setup_gemini(self):
        """Setup Gemini for query enhancement"""
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
                logger.info("✅ Gemini initialized for query enhancement")
            except Exception as e:
                logger.warning(f"Gemini setup failed: {e}")
                self.model = None
        else:
            self.model = None
    
    def _extract_product_features(self, product: Dict) -> List[str]:
        """Extract searchable features from product"""
        features = []
        name_lower = product.get('name', '').lower()
        
        # Ürün tipi
        if 'pijama' in name_lower:
            features.append('pijama')
        if 'gecelik' in name_lower:
            features.append('gecelik')
        if 'sabahlık' in name_lower:
            features.append('sabahlık')
        if 'takım' in name_lower:
            features.append('takım')
        
        # Özellikler
        if 'dantelli' in name_lower:
            features.append('dantelli')
        if 'dekolteli' in name_lower or 'dekolte' in name_lower:
            features.append('dekolteli')
        if 'düğmeli' in name_lower:
            features.append('düğmeli')
        if 'askılı' in name_lower:
            features.append('askılı')
        if 'hamile' in name_lower:
            features.append('hamile')
        if 'lohusa' in name_lower:
            features.append('lohusa')
        if 'büyük beden' in name_lower:
            features.append('büyük_beden')
        
        # Renk
        color = product.get('color', '').lower()
        if color:
            features.append(f'renk_{color}')
        
        # Fiyat kategorisi
        price = product.get('final_price', 0)
        if price < 1000:
            features.append('ekonomik')
        elif price < 2000:
            features.append('orta_segment')
        else:
            features.append('premium')
        
        return features
    
    def _create_search_text(self, product: Dict) -> str:
        """Create comprehensive search text"""
        parts = []
        
        # Ürün adı
        if name := product.get('name'):
            parts.append(name)
        
        # Renk
        if color := product.get('color'):
            parts.append(f"{color} renk")
        
        # Kategori
        if category := product.get('category'):
            parts.append(category)
        
        # Özellikler (ürün adından çıkarılan)
        features = self._extract_product_features(product)
        parts.extend(features)
        
        # Fiyat bilgisi
        if price := product.get('final_price'):
            parts.append(f"{price} TL fiyat")
        
        return ' '.join(parts).lower()
    
    def _load_or_create_embeddings(self):
        """Load existing embeddings or create new ones"""
        if self._load_embeddings():
            logger.info(f"✅ Loaded {len(self.product_embeddings)} product embeddings")
        else:
            logger.info("Creating new RAG embeddings...")
            self._create_embeddings()
    
    def _load_embeddings(self) -> bool:
        """Load existing embeddings"""
        try:
            if os.path.exists(self.embeddings_file) and os.path.exists(self.vectorizer_file):
                with open(self.embeddings_file, 'rb') as f:
                    self.product_embeddings = pickle.load(f)
                
                with open(self.vectorizer_file, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                
                # Recreate TF-IDF matrix
                search_texts = [emb.search_text for emb in self.product_embeddings]
                self.tfidf_matrix = self.vectorizer.transform(search_texts)
                
                return True
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
        
        return False
    
    def _create_embeddings(self):
        """Create new embeddings using TF-IDF"""
        try:
            # Load products
            with open('data/products.json', 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            logger.info(f"Creating embeddings for {len(products)} products...")
            
            # Create search texts
            search_texts = []
            embeddings = []
            
            for i, product in enumerate(products):
                search_text = self._create_search_text(product)
                features = self._extract_product_features(product)
                
                embedding = ProductEmbedding(
                    name=product['name'],
                    color=product['color'],
                    price=product['price'],
                    final_price=product['final_price'],
                    category=product['category'],
                    stock=product['stock'],
                    embedding=None,  # Will be set after TF-IDF
                    features=features,
                    search_text=search_text
                )
                
                embeddings.append(embedding)
                search_texts.append(search_text)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(products)} products...")
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words=None,  # Keep Turkish words
                lowercase=True,
                token_pattern=r'\b\w+\b'
            )
            
            # Fit and transform
            self.tfidf_matrix = self.vectorizer.fit_transform(search_texts)
            
            # Set embeddings
            for i, embedding in enumerate(embeddings):
                embedding.embedding = self.tfidf_matrix[i].toarray()[0]
            
            self.product_embeddings = embeddings
            
            # Save embeddings
            os.makedirs(os.path.dirname(self.embeddings_file), exist_ok=True)
            
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.product_embeddings, f)
            
            with open(self.vectorizer_file, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            logger.info(f"✅ Created and saved {len(self.product_embeddings)} RAG embeddings")
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            self.product_embeddings = []
    
    def enhance_query(self, query: str) -> str:
        """Enhance query using Gemini (optional)"""
        if not self.model:
            return query
        
        try:
            prompt = f"""
Türkçe ürün arama sorgusunu genişlet ve optimize et:
Sorgu: "{query}"

İç giyim mağazası için:
- Eş anlamlı kelimeler ekle
- Türkçe varyasyonları dahil et
- Ürün özelliklerini genişlet

Sadece genişletilmiş sorguyu döndür, açıklama yapma.
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=100
                )
            )
            
            if response.text:
                enhanced = response.text.strip()
                logger.info(f"Query enhanced: '{query}' -> '{enhanced}'")
                return enhanced
                
        except Exception as e:
            logger.warning(f"Query enhancement failed: {e}")
        
        return query
    
    def search(self, query: str, limit: int = 5, enhance_query: bool = False) -> List[Dict]:
        """Search products using RAG"""
        if not self.product_embeddings or not self.vectorizer:
            return []
        
        try:
            # Clean and normalize query
            clean_query = self._clean_query(query)
            
            # Enhance query if enabled (disabled by default for performance)
            if enhance_query:
                enhanced_query = self.enhance_query(clean_query)
            else:
                enhanced_query = clean_query
            
            # Create query vector
            query_vector = self.vectorizer.transform([enhanced_query.lower()])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
            
            # Get top results with better threshold
            top_indices = np.argsort(similarities)[::-1][:limit * 3]  # Get more for filtering
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.01:  # Even lower threshold for better recall
                    embedding = self.product_embeddings[idx]
                    results.append({
                        'name': embedding.name,
                        'color': embedding.color,
                        'price': embedding.price,
                        'final_price': embedding.final_price,
                        'category': embedding.category,
                        'stock': embedding.stock,
                        'features': embedding.features,
                        'similarity': float(similarities[idx])
                    })
            
            # Additional filtering for better results
            filtered_results = self._filter_results(results, query)
            
            logger.info(f"RAG search for '{query}' returned {len(filtered_results)} results")
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return []
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query for better search"""
        # Remove common words that don't help with search
        stop_words = ['ne', 'kadar', 'var', 'mı', 'mi', 'mu', 'mü', 'için', 'arıyorum', 'istiyorum']
        
        # Normalize plural forms
        query = query.replace('sabahlıklar', 'sabahlık')
        query = query.replace('gecelikler', 'gecelik')
        query = query.replace('pijamalar', 'pijama')
        query = query.replace('takımlar', 'takım')
        
        # Remove stop words
        words = query.split()
        cleaned_words = [word for word in words if word.lower() not in stop_words]
        
        return ' '.join(cleaned_words) if cleaned_words else query
    
    def _filter_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Additional filtering for better results with brand filtering"""
        query_lower = query.lower()
        
        # Generic brand filtering
        results = self._apply_brand_filtering(query_lower, results)
        
        # Boost exact matches
        for result in results:
            name_lower = result['name'].lower()
            
            # Exact word matches get higher score
            query_words = query_lower.split()
            matches = sum(1 for word in query_words if len(word) > 2 and word in name_lower)
            if matches > 0:
                result['similarity'] += matches * 0.1
            
            # Product type specific boosts
            if 'sabahlık' in query_lower and 'sabahlık' in name_lower:
                result['similarity'] += 0.3
            elif 'gecelik' in query_lower and 'gecelik' in name_lower:
                result['similarity'] += 0.3
            elif 'pijama' in query_lower and 'pijama' in name_lower:
                result['similarity'] += 0.3
            elif 'takım' in query_lower and 'takım' in name_lower:
                result['similarity'] += 0.2
            
            # Color matches
            if any(color in query_lower for color in ['siyah', 'beyaz', 'kırmızı', 'mavi', 'yeşil']):
                color_lower = result['color'].lower()
                if any(color in color_lower for color in query_lower.split()):
                    result['similarity'] += 0.15
        
        # Sort by enhanced similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results
    
    def is_available(self) -> bool:
        """Check if RAG search is available"""
        return bool(self.product_embeddings and self.vectorizer)

    def _apply_brand_filtering(self, query_lower: str, results: List[Dict]) -> List[Dict]:
        """Generic brand filtering for RAG search results"""
        brand_patterns = {
            'stay strong': ['stay strong', 'stay', 'strong'],
            'calm down': ['calm down', 'calm', 'down'],
            'africa style': ['africa style', 'afrika', 'etnik'],
            'basic': ['basic', 'temel'],
            'premium': ['premium', 'lüks'],
            'comfort': ['comfort', 'rahat'],
            'sport': ['sport', 'spor'],
            'classic': ['classic', 'klasik']
        }
        
        # Check if query contains any brand-specific terms
        for brand_name, variations in brand_patterns.items():
            # Check for exact brand match
            if brand_name in query_lower:
                return [r for r in results if brand_name in r['name'].lower()]
            
            # Check for multi-word brand components
            if len(variations) > 1:
                brand_words = brand_name.split()
                if len(brand_words) == 2:
                    word1, word2 = brand_words
                    if word1 in query_lower and word2 in query_lower:
                        return [r for r in results if brand_name in r['name'].lower()]
        
        # If no specific brand mentioned, return all results
        return results

# Test function
def test_rag_search():
    """Test RAG search system"""
    rag = RAGProductSearch()
    
    if not rag.is_available():
        print("❌ RAG search not available")
        return
    
    test_queries = [
        "hamile pijama arıyorum",
        "siyah dantelli gecelik",
        "ekonomik takım",
        "premium sabahlık",
        "büyük beden gecelik",
        "düğmeli pijama"
    ]
    
    print(f"\n🔍 RAG Product Search Test:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n👤 Query: {query}")
        results = rag.search(query, 3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['name'][:50]}...")
                print(f"   Renk: {result['color']} - Fiyat: {result['final_price']} TL")
                print(f"   Similarity: {result['similarity']:.3f}")
        else:
            print("   No results found")

if __name__ == "__main__":
    test_rag_search() 
