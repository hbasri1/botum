#!/usr/bin/env python3
"""
Comprehensive Product Search Test
Real database products with typos, abbreviations, variations
"""

import json
import random
from final_mvp_system import FinalMVPChatbot
import logging

logging.basicConfig(level=logging.INFO)

def load_sample_products():
    """Load sample products from our database"""
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
        return products[:50]  # Test with first 50 products
    except Exception as e:
        print(f"Error loading products: {e}")
        return []

def generate_search_variations(product_name):
    """Generate realistic search variations for a product"""
    variations = []
    name_lower = product_name.lower()
    
    # 1. Exact name
    variations.append(product_name)
    
    # 2. Common typos
    typo_map = {
        'dantelli': ['danteli', 'dantel', 'danteli'],
        'gecelik': ['gecelik', 'geclik', 'gecelik'],
        'hamile': ['hamile', 'hamle', 'hamil'],
        'lohusa': ['lohusa', 'lohsa', 'lousa'],
        'dekolteli': ['dekolteli', 'dekolte', 'dekolteli'],
        'sabahlık': ['sabahlık', 'sabahlik', 'sabahlk'],
        'pijama': ['pijama', 'pjama', 'pijma'],
        'takımı': ['takımı', 'takimi', 'takım']
    }
    
    for correct, typos in typo_map.items():
        if correct in name_lower:
            for typo in typos:
                variations.append(name_lower.replace(correct, typo))
    
    # 3. Abbreviations and shortcuts
    if 'dantelli' in name_lower and 'gecelik' in name_lower:
        variations.extend(['dantelli gecelik', 'dantel gecelik', 'danteli geclik'])
    
    if 'hamile' in name_lower and 'lohusa' in name_lower:
        variations.extend(['hamile lohusa', 'hamile', 'lohusa', 'hamil lohsa'])
    
    if 'dekolteli' in name_lower:
        variations.extend(['dekolte', 'dekolteli', 'dekolte li'])
    
    # 4. Partial matches (key words)
    words = name_lower.split()
    if len(words) > 2:
        variations.append(' '.join(words[:2]))  # First 2 words
        variations.append(' '.join(words[-2:]))  # Last 2 words
    
    # 5. Color + type combinations
    colors = ['siyah', 'beyaz', 'kırmızı', 'mavi', 'yeşil', 'mor']
    types = ['gecelik', 'pijama', 'takım', 'sabahlık']
    
    for color in colors:
        for type_word in types:
            if type_word in name_lower:
                variations.append(f"{color} {type_word}")
    
    return list(set(variations))  # Remove duplicates

def test_product_search_comprehensive():
    """Run comprehensive product search tests"""
    print("🔍 Comprehensive Product Search Test")
    print("=" * 60)
    
    chatbot = FinalMVPChatbot()
    products = load_sample_products()
    
    if not products:
        print("❌ No products loaded")
        return
    
    # Test categories
    test_results = {
        'exact_matches': {'total': 0, 'found': 0},
        'typo_matches': {'total': 0, 'found': 0},
        'partial_matches': {'total': 0, 'found': 0},
        'color_type_matches': {'total': 0, 'found': 0},
        'abbreviation_matches': {'total': 0, 'found': 0}
    }
    
    # Test sample of products
    test_products = random.sample(products, min(10, len(products)))
    
    for product in test_products:
        product_name = product['name']
        print(f"\n🧪 Testing: {product_name}")
        print("-" * 40)
        
        variations = generate_search_variations(product_name)
        
        for i, variation in enumerate(variations[:5]):  # Test first 5 variations
            print(f"\n  Query {i+1}: '{variation}'")
            
            try:
                response = chatbot.chat(variation)
                
                # Check if original product is found
                found_original = product_name.lower() in response.message.lower()
                
                if found_original:
                    print(f"  ✅ Found original product")
                    if i == 0:  # Exact match
                        test_results['exact_matches']['found'] += 1
                    elif any(typo in variation for typo in ['danteli', 'geclik', 'hamle']):
                        test_results['typo_matches']['found'] += 1
                    elif len(variation.split()) < len(product_name.split()):
                        test_results['partial_matches']['found'] += 1
                    else:
                        test_results['abbreviation_matches']['found'] += 1
                else:
                    print(f"  ❌ Original product not found")
                    print(f"     Response: {response.message[:100]}...")
                
                # Update totals
                if i == 0:
                    test_results['exact_matches']['total'] += 1
                elif any(typo in variation for typo in ['danteli', 'geclik', 'hamle']):
                    test_results['typo_matches']['total'] += 1
                elif len(variation.split()) < len(product_name.split()):
                    test_results['partial_matches']['total'] += 1
                else:
                    test_results['abbreviation_matches']['total'] += 1
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    # Special test cases from our database
    special_tests = [
        ("afrika gecelik", "Should find Afrika Etnik product"),
        ("afirka geclik", "Typo test for Afrika"),
        ("hamile takım", "Should find maternity sets"),
        ("danteli pijama", "Typo test for dantelli"),
        ("siyah gecelik", "Color + type search"),
        ("dekolteli", "Single feature search"),
        ("lohusa", "Single word search"),
        ("brode dantelli", "Multiple features"),
        ("v yaka", "Specific neckline"),
        ("büyük beden", "Size related search")
    ]
    
    print(f"\n🎯 Special Test Cases")
    print("-" * 40)
    
    special_results = {'total': 0, 'successful': 0}
    
    for query, description in special_tests:
        special_results['total'] += 1
        print(f"\n  Query: '{query}' ({description})")
        
        try:
            response = chatbot.chat(query)
            
            # Simple success criteria
            has_products = response.products_found > 0 or "ürün buldum" in response.message.lower()
            
            if has_products:
                print(f"  ✅ Success: Found {response.products_found} products")
                special_results['successful'] += 1
            else:
                print(f"  ❌ No products found")
                print(f"     Response: {response.message[:100]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Final report
    print(f"\n{'='*60}")
    print(f"📊 COMPREHENSIVE SEARCH TEST REPORT")
    print(f"{'='*60}")
    
    for category, results in test_results.items():
        if results['total'] > 0:
            success_rate = (results['found'] / results['total']) * 100
            print(f"{category.replace('_', ' ').title()}: {results['found']}/{results['total']} ({success_rate:.1f}%)")
    
    special_success_rate = (special_results['successful'] / special_results['total']) * 100
    print(f"Special Cases: {special_results['successful']}/{special_results['total']} ({special_success_rate:.1f}%)")
    
    # Overall assessment
    total_tests = sum(r['total'] for r in test_results.values()) + special_results['total']
    total_successful = sum(r['found'] for r in test_results.values()) + special_results['successful']
    overall_success = (total_successful / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n🎯 Overall Success Rate: {overall_success:.1f}%")
    
    if overall_success >= 90:
        print("🎉 EXCELLENT! Search system is highly accurate")
    elif overall_success >= 80:
        print("✅ GOOD! Search system works well")
    elif overall_success >= 70:
        print("⚠️ ACCEPTABLE! Some improvements needed")
    else:
        print("❌ NEEDS WORK! Search accuracy is low")
    
    return overall_success

if __name__ == "__main__":
    success_rate = test_product_search_comprehensive()
    print(f"\nFinal Search Accuracy: {success_rate:.1f}%")