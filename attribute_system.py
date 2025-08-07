#!/usr/bin/env python3
"""
Unified Attribute System for Product Queries
Handles color, size, stock, and other product attributes in a scalable way
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class AttributeType(Enum):
    COLOR = "color"
    SIZE = "size" 
    STOCK = "stock"
    PRICE = "price"

@dataclass
class AttributeMatch:
    """Attribute match result"""
    found: bool
    attribute_type: AttributeType
    requested_value: str
    available_values: List[str]
    matching_products: List[Dict]
    response_message: str

class AttributeSystem:
    """
    Unified system for handling all product attributes
    Scalable, maintainable, and consistent across all attribute types
    """
    
    def __init__(self):
        # Color mappings
        self.color_mappings = {
            'siyah': ['siyah', 'siyahı', 'black', 'siyahi'],
            'beyaz': ['beyaz', 'beyazı', 'white', 'ekru', 'ekrusu', 'beyazi'],
            'kırmızı': ['kırmızı', 'kırmızısı', 'kirmizi', 'red', 'kirmizisi'],
            'mavi': ['mavi', 'mavisi', 'blue', 'mavii'],
            'lacivert': ['lacivert', 'lacivertı', 'navy', 'laciverti'],
            'yeşil': ['yeşil', 'yeşili', 'yesil', 'green', 'yesili'],
            'sarı': ['sarı', 'sarısı', 'sari', 'yellow', 'sarisi'],
            'mor': ['mor', 'moru', 'purple', 'lila'],
            'pembe': ['pembe', 'pembesi', 'pink'],
            'vizon': ['vizon', 'vizonu', 'beige', 'bej'],
            'bordo': ['bordo', 'bordosu', 'burgundy'],
            'gri': ['gri', 'grisi', 'gray', 'grey'],
            'turuncu': ['turuncu', 'turuncusu', 'orange'],
            'kahverengi': ['kahverengi', 'kahve', 'brown']
        }
        
        # Size mappings
        self.size_mappings = {
            'xs': ['xs', 'extra small', 'çok küçük'],
            's': ['s', 'small', 'küçük'],
            'm': ['m', 'medium', 'orta'],
            'l': ['l', 'large', 'büyük'],
            'xl': ['xl', 'extra large', 'çok büyük'],
            'xxl': ['xxl', '2xl', 'çok çok büyük'],
            'xxxl': ['xxxl', '3xl']
        }
        
        # Stock query indicators
        self.stock_indicators = ['stok', 'var mı', 'mevcut', 'bulunur mu', 'kaldı mı']
        
        # Price query indicators  
        self.price_indicators = ['fiyat', 'ne kadar', 'kaça', 'para', 'tl', 'lira']
        
        # Build reverse mappings for quick lookup
        self._build_reverse_mappings()
    
    def _build_reverse_mappings(self):
        """Build reverse mappings for quick attribute lookup"""
        self.color_variants = {}
        for standard, variants in self.color_mappings.items():
            for variant in variants:
                self.color_variants[variant.lower()] = standard
        
        self.size_variants = {}
        for standard, variants in self.size_mappings.items():
            for variant in variants:
                self.size_variants[variant.lower()] = standard
    
    def extract_attribute_from_query(self, query: str) -> Tuple[Optional[AttributeType], Optional[str]]:
        """
        Extract attribute type and value from user query
        Returns (AttributeType, value) or (None, None)
        """
        query_lower = query.lower().strip()
        
        # Clean query by removing common words
        clean_query = self._clean_query(query_lower)
        
        # Check for color
        color = self._extract_color(clean_query)
        if color:
            return AttributeType.COLOR, color
        
        # Check for size
        size = self._extract_size(clean_query)
        if size:
            return AttributeType.SIZE, size
        
        # Check for stock query
        if any(indicator in query_lower for indicator in self.stock_indicators):
            return AttributeType.STOCK, "stock"
        
        # Check for price query
        if any(indicator in query_lower for indicator in self.price_indicators):
            return AttributeType.PRICE, "price"
        
        return None, None
    
    def _clean_query(self, query: str) -> str:
        """Clean query by removing common words"""
        stop_words = ['var', 'mı', 'mi', 'mu', 'mü', 'mevcut', 'stok', 'stokta', '?', 'var mı', 'mevcut mu']
        clean_query = query
        for word in stop_words:
            clean_query = clean_query.replace(word, ' ')
        return ' '.join(clean_query.split())
    
    def _extract_color(self, query: str) -> Optional[str]:
        """Extract color from query"""
        words = query.split()
        for word in words:
            if word in self.color_variants:
                return self.color_variants[word]
        return None
    
    def _extract_size(self, query: str) -> Optional[str]:
        """Extract size from query"""
        words = query.split()
        for word in words:
            if word in self.size_variants:
                return self.size_variants[word]
        return None
    
    def match_attribute_in_products(self, attr_type: AttributeType, requested_value: str, products: List[Dict]) -> AttributeMatch:
        """
        Match requested attribute against products
        Universal method for all attribute types
        """
        if not products:
            return AttributeMatch(False, attr_type, requested_value, [], [], "")
        
        matching_products = []
        available_values = []
        
        # Get the appropriate field name for the attribute
        field_name = self._get_field_name(attr_type)
        
        for product in products:
            raw_value = product.get(field_name, '')
            if isinstance(raw_value, (int, float)):
                product_value = str(raw_value)
            else:
                product_value = str(raw_value).lower().strip()
            available_values.append(product_value)
            
            # Check if requested value matches product value
            if self._values_match(attr_type, requested_value, product_value):
                matching_products.append(product)
        
        # Remove duplicates and empty values
        available_values = list(set([v for v in available_values if v]))
        
        # Generate response message
        response_message = self._generate_response(attr_type, requested_value, matching_products, available_values, products)
        
        return AttributeMatch(
            found=len(matching_products) > 0,
            attribute_type=attr_type,
            requested_value=requested_value,
            available_values=available_values,
            matching_products=matching_products,
            response_message=response_message
        )
    
    def _get_field_name(self, attr_type: AttributeType) -> str:
        """Get database field name for attribute type"""
        field_mapping = {
            AttributeType.COLOR: 'color',
            AttributeType.SIZE: 'size',
            AttributeType.STOCK: 'stock',
            AttributeType.PRICE: 'final_price'
        }
        return field_mapping.get(attr_type, '')
    
    def _values_match(self, attr_type: AttributeType, requested: str, product_value: str) -> bool:
        """Check if requested value matches product value"""
        if not requested or not product_value:
            return False
        
        requested_lower = requested.lower()
        product_lower = product_value.lower()
        
        if attr_type == AttributeType.COLOR:
            return self._colors_match(requested_lower, product_lower)
        elif attr_type == AttributeType.SIZE:
            return self._sizes_match(requested_lower, product_lower)
        elif attr_type == AttributeType.STOCK:
            return True  # Stock queries don't need value matching
        elif attr_type == AttributeType.PRICE:
            return True  # Price queries don't need value matching
        
        return False
    
    def _colors_match(self, requested: str, product_color: str) -> bool:
        """Check if colors match"""
        # Direct match
        if requested == product_color:
            return True
        
        # Check if requested color is contained in product color
        if requested in product_color:
            return True
        
        # Check variants
        if requested in self.color_mappings:
            variants = self.color_mappings[requested]
            for variant in variants:
                if variant.lower() in product_color:
                    return True
        
        return False
    
    def _sizes_match(self, requested: str, product_size: str) -> bool:
        """Check if sizes match"""
        return requested == product_size or requested in product_size
    
    def _generate_response(self, attr_type: AttributeType, requested_value: str, 
                          matching_products: List[Dict], available_values: List[str], 
                          all_products: List[Dict]) -> str:
        """Generate appropriate response based on attribute match results"""
        
        if attr_type == AttributeType.COLOR:
            return self._generate_color_response(requested_value, matching_products, all_products)
        elif attr_type == AttributeType.SIZE:
            return self._generate_size_response(requested_value, matching_products, available_values)
        elif attr_type == AttributeType.STOCK:
            return self._generate_stock_response(all_products)
        elif attr_type == AttributeType.PRICE:
            return self._generate_price_response(all_products)
        
        return "Üzgünüm, bu konuda yardımcı olamıyorum."
    
    def _generate_color_response(self, requested_color: str, matching_products: List[Dict], all_products: List[Dict]) -> str:
        """Generate color-specific response"""
        if matching_products:
            if len(matching_products) == 1:
                product = matching_products[0]
                stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                
                response = f"🎨 **{requested_color.title()}** renk mevcut!\n\n"
                response += f"✨ **{product.get('name', '')}**\n"
                response += f"💰 **Fiyat:** {product.get('final_price', 0):.2f} TL\n"
                response += f"📦 **Stok:** {stock_status}\n\n"
                response += f"🛒 **Sipariş için:** 0555 555 55 55"
                
                return response
            else:
                response = f"🎨 **{requested_color.title()}** renkte **{len(matching_products)} ürün** mevcut:\n\n"
                
                for i, product in enumerate(matching_products[:3], 1):
                    stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                    response += f"**{i}.** {product.get('name', '')[:40]}...\n"
                    response += f"   💰 **{product.get('final_price', 0):.2f} TL** - {stock_status}\n\n"
                
                response += f"🛒 **Sipariş için:** 0555 555 55 55"
                return response
        else:
            # Color not found - show available colors
            response = f"❌ **{requested_color.title()}** renkte ürün bulunmuyor.\n\n"
            
            # Get unique colors with info
            color_info = []
            seen_colors = set()
            for product in all_products:
                color = product.get('color', '').strip()
                if color and color.lower() not in seen_colors:
                    color_info.append({
                        'color': color,
                        'price': product.get('final_price', 0),
                        'stock': product.get('stock', 0)
                    })
                    seen_colors.add(color.lower())
            
            if color_info:
                response += f"🎨 **Mevcut renkler:**\n\n"
                for i, info in enumerate(color_info[:5], 1):
                    stock_emoji = '✅' if info['stock'] > 0 else '❌'
                    response += f"**{i}.** {info['color']} - **{info['price']:.2f} TL** {stock_emoji}\n"
                response += "\n"
            
            response += f"🛒 **Sipariş için:** 0555 555 55 55"
            return response
    
    def _generate_size_response(self, requested_size: str, matching_products: List[Dict], available_sizes: List[str]) -> str:
        """Generate size-specific response"""
        if matching_products:
            response = f"📏 **{requested_size.upper()}** beden mevcut!\n\n"
            for i, product in enumerate(matching_products[:3], 1):
                stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                response += f"**{i}.** {product.get('name', '')[:40]}...\n"
                response += f"   💰 **{product.get('final_price', 0):.2f} TL** - {stock_status}\n\n"
            response += f"🛒 **Sipariş için:** 0555 555 55 55"
        else:
            response = f"❌ **{requested_size.upper()}** beden bulunmuyor.\n\n"
            if available_sizes:
                response += f"📏 **Mevcut bedenler:** {', '.join(s.upper() for s in available_sizes[:5])}\n\n"
            response += f"🛒 **Sipariş için:** 0555 555 55 55"
        
        return response
    
    def _generate_stock_response(self, products: List[Dict]) -> str:
        """Generate stock-specific response"""
        if len(products) == 1:
            product = products[0]
            stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
            return f"📦 **{product['name']}** stok durumu: {stock_status}"
        else:
            response = "📦 **Stok durumları:**\n\n"
            for i, product in enumerate(products[:5], 1):
                stock_status = '✅ Mevcut' if product.get('stock', 0) > 0 else '❌ Tükendi'
                response += f"**{i}.** {product['name'][:50]}{'...' if len(product['name']) > 50 else ''} - {stock_status}\n"
            return response
    
    def _generate_price_response(self, products: List[Dict]) -> str:
        """Generate price-specific response"""
        if len(products) == 1:
            product = products[0]
            response = f"💰 **{product['name']}** fiyatı: **{product['final_price']:.2f} TL**"
            if product.get('discount', 0) > 0:
                response += f"\n🏷️ **İndirim:** %{product['discount']} (Eski fiyat: {product['price']:.2f} TL)"
            return response
        else:
            response = "💰 **Fiyat listesi:**\n\n"
            for i, product in enumerate(products[:5], 1):
                response += f"**{i}.** {product['name'][:40]}... - **{product['final_price']:.2f} TL**\n"
            return response

# Global instance
attribute_system = AttributeSystem()

def handle_attribute_query(query: str, context_products: List[Dict]) -> Tuple[bool, str]:
    """
    Main function to handle all attribute queries
    Returns (is_attribute_query, response)
    """
    # Extract attribute type and value
    attr_type, requested_value = attribute_system.extract_attribute_from_query(query)
    
    if not attr_type:
        return False, ""
    
    # Check if it's actually an attribute query (has indicators)
    query_lower = query.lower()
    attribute_indicators = ['var mı', 'mevcut', 'stok', 'bulunur mu', 'var mi', 'fiyat', 'ne kadar', 'beden']
    
    if not any(indicator in query_lower for indicator in attribute_indicators):
        return False, ""
    
    # Match attribute in products
    attribute_match = attribute_system.match_attribute_in_products(attr_type, requested_value, context_products)
    
    return True, attribute_match.response_message

if __name__ == "__main__":
    # Test the system
    test_products = [
        {'name': 'Dantelli Gecelik', 'color': 'EKRU', 'size': 'M', 'final_price': 150.0, 'stock': 5},
        {'name': 'Dantelli Gecelik', 'color': 'LACİVERT', 'size': 'L', 'final_price': 150.0, 'stock': 3},
        {'name': 'Pijama Takımı', 'color': 'SİYAH', 'size': 'S', 'final_price': 200.0, 'stock': 2},
    ]
    
    test_queries = [
        "siyahı var mı?",
        "m beden var mı",
        "stokta var mı",
        "fiyatı ne kadar"
    ]
    
    print("🧪 UNIFIED ATTRIBUTE SYSTEM TEST")
    print("=" * 50)
    
    for query in test_queries:
        is_attr, response = handle_attribute_query(query, test_products)
        print(f"\n📝 Query: {query}")
        print(f"🎯 Is Attribute Query: {is_attr}")
        if is_attr:
            print(f"💬 Response: {response[:100]}...")