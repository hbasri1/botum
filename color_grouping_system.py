#!/usr/bin/env python3
"""
Color Grouping System
Groups same products with different colors
"""

from typing import Dict, List
from collections import defaultdict

def group_products_by_base_name(products):
    """Group products by base name, collecting colors"""
    grouped = defaultdict(lambda: {
        'base_product': None,
        'colors': [],
        'prices': set(),
        'stock_status': []
    })
    
    for product in products:
        # Extract base name (remove color-specific parts)
        base_name = extract_base_name(product.name)
        
        if grouped[base_name]['base_product'] is None:
            grouped[base_name]['base_product'] = product
        
        grouped[base_name]['colors'].append({
            'color': product.color,
            'price': product.final_price,
            'stock': product.stock,
            'product': product
        })
        grouped[base_name]['prices'].add(product.final_price)
    
    return dict(grouped)

def extract_base_name(product_name):
    """Extract base product name without color specifics"""
    # Remove common color indicators
    color_indicators = [
        'Siyah', 'Beyaz', 'Kırmızı', 'Mavi', 'Yeşil', 'Sarı', 
        'Mor', 'Pembe', 'Lacivert', 'Bordo', 'Vizon', 'Ekru'
    ]
    
    base_name = product_name
    for color in color_indicators:
        base_name = base_name.replace(color, '').strip()
    
    # Clean up extra spaces
    base_name = ' '.join(base_name.split())
    
    return base_name

def format_grouped_products(grouped_products):
    """Format grouped products for display"""
    response = ""
    
    for i, (base_name, group_data) in enumerate(grouped_products.items(), 1):
        base_product = group_data['base_product']
        colors = group_data['colors']
        
        if len(colors) > 1:
            # Multiple colors - show grouped
            response += f"**{i}.** {base_name}\n"
            
            # Show price range
            prices = [c['price'] for c in colors]
            min_price = min(prices)
            max_price = max(prices)
            
            if min_price == max_price:
                response += f"   💰 Fiyat: **{min_price:.2f} TL**\n"
            else:
                response += f"   💰 Fiyat: **{min_price:.2f} - {max_price:.2f} TL**\n"
            
            # Show available colors
            color_list = []
            for color_info in colors:
                stock_emoji = "✅" if color_info['stock'] > 0 else "❌"
                color_list.append(f"{color_info['color']} {stock_emoji}")
            
            response += f"   🎨 Renkler: {', '.join(color_list)}\n\n"
        else:
            # Single color - show normally
            color_info = colors[0]
            product = color_info['product']
            stock_emoji = "✅" if product.stock > 0 else "❌"
            
            response += f"**{i}.** {product.name}\n"
            response += f"   🎨 Renk: {product.color} - 💰 **{product.final_price:.2f} TL**"
            
            if product.discount > 0:
                response += f" 🏷️ *(%{product.discount:.1f} indirim)*"
            
            response += f" - 📦 {stock_emoji} {'Mevcut' if product.stock > 0 else 'Tükendi'}\n\n"
    
    return response

# Test the system
if __name__ == "__main__":
    # Mock products for testing
    class MockProduct:
        def __init__(self, name, color, price, discount, final_price, stock):
            self.name = name
            self.color = color
            self.price = price
            self.discount = discount
            self.final_price = final_price
            self.stock = stock
    
    test_products = [
        MockProduct("Afrika Etnik Baskılı Dantelli Gecelik", "BEJ", 869.9, 35, 565.44, 5),
        MockProduct("Afrika Etnik Baskılı Dantelli Gecelik", "SİYAH", 869.9, 35, 565.44, 3),
        MockProduct("Afrika Etnik Baskılı Dantelli Gecelik", "BEYAZ", 869.9, 35, 565.44, 0),
        MockProduct("Hamile Lohusa Pijama Takımı", "PEMBE", 1200, 20, 960, 2)
    ]
    
    grouped = group_products_by_base_name(test_products)
    formatted = format_grouped_products(grouped)
    print(formatted)