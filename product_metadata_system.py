#!/usr/bin/env python3
"""
Product Metadata System
Separates product search metadata from product details
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProductMetadata:
    """Product metadata for search and matching"""
    product_id: str
    search_terms: List[str]  # For embedding and search
    category: str
    features: List[str]      # hamile, dantelli, büyük_beden
    colors: List[str]        # Available colors
    product_type: str        # gecelik, pijama, sabahlık

@dataclass
class ProductDetails:
    """Product details for display and business logic"""
    product_id: str
    name: str
    description: str
    price: float
    discount: float
    final_price: float
    stock: int
    images: List[str]
    specifications: Dict[str, str]
    last_updated: str

class ProductMetadataSystem:
    """Manages product metadata and details separately"""
    
    def __init__(self):
        self.metadata: Dict[str, ProductMetadata] = {}
        self.details: Dict[str, ProductDetails] = {}
        self._load_data()
    
    def _load_data(self):
        """Load metadata and details from separate files"""
        try:
            # Load search metadata
            with open('data/product_metadata.json', 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
            
            for item in metadata_data:
                metadata = ProductMetadata(
                    product_id=item['product_id'],
                    search_terms=item['search_terms'],
                    category=item['category'],
                    features=item['features'],
                    colors=item['colors'],
                    product_type=item['product_type']
                )
                self.metadata[metadata.product_id] = metadata
            
            # Load product details
            with open('data/product_details.json', 'r', encoding='utf-8') as f:
                details_data = json.load(f)
            
            for item in details_data:
                details = ProductDetails(
                    product_id=item['product_id'],
                    name=item['name'],
                    description=item.get('description', ''),
                    price=item['price'],
                    discount=item['discount'],
                    final_price=item['final_price'],
                    stock=item['stock'],
                    images=item.get('images', []),
                    specifications=item.get('specifications', {}),
                    last_updated=item.get('last_updated', '')
                )
                self.details[details.product_id] = details
                
            logger.info(f"✅ Loaded {len(self.metadata)} product metadata and {len(self.details)} product details")
            
        except Exception as e:
            logger.error(f"❌ Error loading product data: {e}")
    
    def search_products(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search products using metadata"""
        results = []
        query_lower = query.lower()
        
        for product_id, metadata in self.metadata.items():
            score = 0
            
            # Check search terms
            for term in metadata.search_terms:
                if query_lower in term.lower():
                    score += 10
            
            # Check features
            for feature in metadata.features:
                if feature.lower() in query_lower:
                    score += 8
            
            # Check colors
            for color in metadata.colors:
                if color.lower() in query_lower:
                    score += 6
            
            if score > 0:
                # Get product details
                details = self.details.get(product_id)
                if details:
                    results.append({
                        'product_id': product_id,
                        'metadata': metadata,
                        'details': details,
                        'score': score
                    })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def update_product_details(self, product_id: str, updates: Dict):
        """Update product details without affecting search metadata"""
        if product_id in self.details:
            details = self.details[product_id]
            for key, value in updates.items():
                if hasattr(details, key):
                    setattr(details, key, value)
            
            # Save to file
            self._save_details()
            logger.info(f"✅ Updated product details for {product_id}")
        else:
            logger.error(f"❌ Product {product_id} not found")
    
    def _save_details(self):
        """Save product details to file"""
        try:
            details_data = []
            for details in self.details.values():
                details_data.append({
                    'product_id': details.product_id,
                    'name': details.name,
                    'description': details.description,
                    'price': details.price,
                    'discount': details.discount,
                    'final_price': details.final_price,
                    'stock': details.stock,
                    'images': details.images,
                    'specifications': details.specifications,
                    'last_updated': details.last_updated
                })
            
            with open('data/product_details.json', 'w', encoding='utf-8') as f:
                json.dump(details_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error saving product details: {e}")

# Example usage
if __name__ == "__main__":
    system = ProductMetadataSystem()
    
    # Search example
    results = system.search_products("afrika gecelik")
    for result in results:
        print(f"Found: {result['details'].name} (Score: {result['score']})")
    
    # Update example
    system.update_product_details("prod_001", {
        "price": 299.99,
        "stock": 15
    })