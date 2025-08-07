#!/usr/bin/env python3
"""
Semantic Search Engine - Google Embedding API + pgvector
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import numpy as np
from dataclasses import dataclass
import asyncpg

logger = logging.getLogger(__name__)

def create_rich_embedding_text(product_data: dict) -> str:
    """
    Bir ürünün sözlük (dict) verisini alıp, anlamsal arama için zenginleştirilmiş
    bir metin string'i oluşturur. Eksik alanları görmezden gelir.
    """
    text_parts = []
    
    # 1. Ürün Adı (Zorunlu)
    if product_name := product_data.get('name'):
        text_parts.append(f"Ürün: {product_name}.")
    
    # 2. Kategori (Varsa ekle)
    if category := product_data.get('category'):
        text_parts.append(f"Kategori: {category}.")
    
    # 3. Renk (Varsa ekle)
    if color := product_data.get('color'):
        text_parts.append(f"Renk: {color}.")
    
    # 4. Malzeme (Varsa ekle)
    if material := product_data.get('material'):
        text_parts.append(f"Malzeme: {material}.")
    
    # 5. Beden (Varsa ekle)
    if size := product_data.get('size'):
        text_parts.append(f"Beden: {size}.")
    
    # 6. Fiyat (Varsa ekle)
    if price := product_data.get('final_price'):
        text_parts.append(f"Fiyat: {price} TL.")
    
    # 7. İndirim (Varsa ekle)
    if discount := product_data.get('discount'):
        if discount and str(discount) != '0':
            text_parts.append(f"İndirim: %{discount}.")
    
    # 8. Etiketler (Liste ise birleştirip ekle)
    if tags := product_data.get('tags'):
        if isinstance(tags, list) and tags:
            tag_string = ", ".join(tags)
            text_parts.append(f"Etiketler: {tag_string}.")
    
    # 9. Özel özellikler (ürün adından çıkar)
    special_features = []
    name_lower = product_data.get('name', '').lower()
    
    if 'hamile' in name_lower or 'lohusa' in name_lower:
        special_features.append('hamile ve lohusa için uygun')
    if 'afrika' in name_lower or 'etnik' in name_lower:
        special_features.append('afrika tarzı etnik desen')
    if 'dantelli' in name_lower or 'dantel' in name_lower:
        special_features.append('dantelli süsleme')
    if 'düğmeli' in name_lower:
        special_features.append('düğmeli kapama')
    if 'askılı' in name_lower:
        special_features.append('askılı model')
    if 'takım' in name_lower:
        special_features.append('takım ürün')
    
    if special_features:
        text_parts.append(f"Özellikler: {', '.join(special_features)}.")
    
    # 10. Açıklama (En sona ekle, en uzun metin genellikle budur)
    if description := product_data.get('description'):
        # Açıklamayı kısaltarak gürültüyü azalt
        short_description = (description[:200] + '...') if len(description) > 200 else description
        text_parts.append(f"Açıklama: {short_description}")
    
    # Tüm parçaları birleştir
    return " ".join(text_parts)

@dataclass
class ProductEmbedding:
    """Ürün embedding modeli"""
    product_id: str
    name: str
    embedding: List[float]
    rich_text: str
    metadata: Dict[str, Any]

class SemanticSearchEngine:
    """Google Embedding API + pgvector ile semantic search"""
    
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db_pool = db_pool
        self.embedding_cache = {}  # Simple cache
        
    async def initialize_database(self):
        """pgvector database'i initialize et"""
        if not self.db_pool:
            return False
            
        try:
            async with self.db_pool.acquire() as conn:
                # pgvector extension'ı aktifleştir
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # product_embeddings tablosunu oluştur
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS product_embeddings (
                        id SERIAL PRIMARY KEY,
                        product_id VARCHAR(50) NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        embedding vector(768),
                        rich_text TEXT NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                
                # Vector similarity index oluştur
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS product_embeddings_embedding_idx 
                    ON product_embeddings USING ivfflat (embedding vector_cosine_ops);
                """)
                
                logger.info("✅ pgvector database initialized")
                return True
                
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            return False
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Google Embedding API ile embedding oluştur"""
        # Cache kontrolü
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        try:
            # Google Embedding API çağrısı (mock implementation)
            # Production'da: google.cloud.aiplatform.gapic.PredictionServiceClient
            
            # Şimdilik mock embedding (768 dimension)
            import hashlib
            import random
            
            # Deterministic mock embedding (text'e göre)
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            embedding = [random.uniform(-1, 1) for _ in range(768)]
            
            # Cache'e kaydet
            self.embedding_cache[text] = embedding
            
            logger.info(f"Generated embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            return None
    
    async def create_product_embeddings(self, products: List[Dict]) -> int:
        """Tüm ürünler için embeddings oluştur ve kaydet"""
        if not self.db_pool:
            logger.error("Database pool not available")
            return 0
        
        created_count = 0
        
        try:
            async with self.db_pool.acquire() as conn:
                for product in products:
                    try:
                        # Rich text oluştur
                        rich_text = create_rich_embedding_text(product)
                        
                        # Embedding oluştur
                        embedding = await self.generate_embedding(rich_text)
                        if not embedding:
                            continue
                        
                        # Database'e kaydet
                        await conn.execute("""
                            INSERT INTO product_embeddings 
                            (product_id, name, embedding, rich_text, metadata)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (product_id) DO UPDATE SET
                            name = $2, embedding = $3, rich_text = $4, metadata = $5
                        """, 
                        str(product.get('id', '')),
                        product.get('name', ''),
                        embedding,
                        rich_text,
                        json.dumps(product)
                        )
                        
                        created_count += 1
                        
                        if created_count % 50 == 0:
                            logger.info(f"Created {created_count} embeddings...")
                            
                    except Exception as e:
                        logger.error(f"Error creating embedding for product {product.get('name', 'unknown')}: {str(e)}")
                        continue
            
            logger.info(f"✅ Created {created_count} product embeddings")
            return created_count
            
        except Exception as e:
            logger.error(f"Batch embedding creation error: {str(e)}")
            return created_count
    
    async def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search yap"""
        if not self.db_pool:
            return []
        
        try:
            # Query için embedding oluştur
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                return []
            
            async with self.db_pool.acquire() as conn:
                # Vector similarity search
                rows = await conn.fetch("""
                    SELECT 
                        product_id,
                        name,
                        rich_text,
                        metadata,
                        1 - (embedding <=> $1) as similarity
                    FROM product_embeddings
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """, query_embedding, limit)
                
                results = []
                for row in rows:
                    try:
                        metadata = json.loads(row['metadata']) if row['metadata'] else {}
                        results.append({
                            'product_id': row['product_id'],
                            'name': row['name'],
                            'similarity': float(row['similarity']),
                            'rich_text': row['rich_text'],
                            'metadata': metadata
                        })
                    except Exception as e:
                        logger.error(f"Error parsing search result: {str(e)}")
                        continue
                
                logger.info(f"Semantic search for '{query}' returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return []
    
    async def hybrid_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Hybrid search: Semantic + Fuzzy matching"""
        # Önce semantic search
        semantic_results = await self.semantic_search(query, limit * 2)
        
        # Fuzzy matching ile de ara (fallback için)
        # Bu kısım mevcut database_service'i kullanabilir
        
        # Şimdilik sadece semantic results döndür
        return semantic_results[:limit]
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Embedding istatistikleri"""
        return {
            "cache_size": len(self.embedding_cache),
            "total_embeddings": "database'den alınacak"
        }

# Test fonksiyonu
async def test_semantic_search():
    """Semantic search sistemini test et"""
    
    # Test ürünleri
    test_products = [
        {
            'id': 1,
            'name': 'Afrika Etnik Baskılı Dantelli "Africa Style" Gecelik',
            'category': 'İç Giyim',
            'color': 'BEJ',
            'final_price': '565.44',
            'discount': '35.0'
        },
        {
            'id': 2,
            'name': 'Dantelli Önü Düğmeli Hamile Lohusa Gecelik',
            'category': 'İç Giyim', 
            'color': 'EKRU',
            'final_price': '1632.33',
            'discount': '30.0'
        },
        {
            'id': 3,
            'name': 'Sırtı Dekolteli Tüllü ve Dantelli Pijama Takımı',
            'category': 'İç Giyim',
            'color': 'SİYAH',
            'final_price': '1821.33'
        }
    ]
    
    # Rich text oluşturma testi
    print("🧪 Rich Text Generation Test:")
    for product in test_products:
        rich_text = create_rich_embedding_text(product)
        print(f"\n{product['name'][:30]}...")
        print(f"Rich Text: {rich_text}")
    
    # Semantic search engine testi (mock)
    engine = SemanticSearchEngine()
    
    # Mock embedding generation testi
    test_queries = [
        "afrika gecelik",
        "hamile geceliği",
        "siyah pijama takımı"
    ]
    
    print(f"\n🔍 Embedding Generation Test:")
    for query in test_queries:
        embedding = await engine.generate_embedding(query)
        print(f"'{query}' -> {len(embedding) if embedding else 0} dimensions")

if __name__ == "__main__":
    asyncio.run(test_semantic_search())