#!/usr/bin/env python3
"""
Admin File Processor - Gemini 2.5 Flash/Pro ile dosya işleme
"""

import os
import json
import pandas as pd
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminFileProcessor:
    def __init__(self):
        """Initialize file processor with Gemini API"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 1.5 Flash for file processing (faster and cheaper)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # Supported file types
        self.supported_extensions = {'.json', '.csv', '.xlsx', '.xls', '.txt'}
        
        logger.info("✅ Admin File Processor initialized with Gemini 2.5 Flash")
    
    def process_uploaded_file(self, file_path: str, business_id: str) -> Dict[str, Any]:
        """
        Process uploaded file and convert to standardized product format
        """
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension not in self.supported_extensions:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_extension}',
                    'supported_types': list(self.supported_extensions)
                }
            
            # Read file content
            raw_data = self._read_file(file_path, file_extension)
            if not raw_data:
                return {
                    'success': False,
                    'error': 'Could not read file content'
                }
            
            # Process with Gemini
            processed_products = self._process_with_gemini(raw_data, business_id)
            
            if not processed_products:
                return {
                    'success': False,
                    'error': 'Could not process file with Gemini'
                }
            
            # Validate and clean data
            validated_products = self._validate_products(processed_products)
            
            return {
                'success': True,
                'products': validated_products,
                'count': len(validated_products),
                'message': f'Successfully processed {len(validated_products)} products'
            }
            
        except Exception as e:
            logger.error(f"❌ File processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _read_file(self, file_path: str, extension: str) -> Optional[str]:
        """Read file content based on extension"""
        try:
            if extension == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return json.dumps(data, ensure_ascii=False, indent=2)
            
            elif extension == '.csv':
                df = pd.read_csv(file_path)
                return df.to_json(orient='records', force_ascii=False, indent=2)
            
            elif extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return df.to_json(orient='records', force_ascii=False, indent=2)
            
            elif extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ File reading error: {e}")
            return None
    
    def _process_with_gemini(self, raw_data: str, business_id: str) -> Optional[List[Dict]]:
        """Process raw data with Gemini to extract product information"""
        try:
            prompt = f"""
Aşağıdaki veriyi analiz et ve ürün bilgilerini çıkar. Her ürün için şu formatta JSON döndür:

{{
    "name": "ürün adı",
    "price": fiyat_sayı,
    "color": "renk",
    "category": "kategori",
    "stock": stok_sayısı,
    "description": "açıklama",
    "size": "beden/boyut",
    "material": "malzeme",
    "brand": "marka"
}}

KURALLAR:
1. Fiyatları sadece sayı olarak ver (TL, ₺ gibi sembolleri çıkar)
2. Renkleri Türkçe olarak standardize et (kırmızı, mavi, siyah, beyaz, vs.)
3. Kategorileri genel kategorilere ayır (giyim, ayakkabı, aksesuar, vs.)
4. Stok bilgisi yoksa 0 yaz
5. Eksik bilgiler için null kullan
6. Sadece JSON array döndür, başka açıklama yapma

İşletme ID: {business_id}

Veri:
{raw_data[:4000]}  # İlk 4000 karakter
"""

            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("❌ Empty response from Gemini")
                return None
            
            # Parse JSON response
            try:
                # Clean response text
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                products = json.loads(response_text)
                
                if isinstance(products, dict):
                    products = [products]
                
                logger.info(f"✅ Gemini processed {len(products)} products")
                return products
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing error: {e}")
                logger.error(f"Response text: {response.text[:500]}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Gemini processing error: {e}")
            return None
    
    def _validate_products(self, products: List[Dict]) -> List[Dict]:
        """Validate and clean product data"""
        validated = []
        
        for product in products:
            try:
                # Required fields
                if not product.get('name'):
                    continue
                
                # Clean and validate data
                clean_product = {
                    'name': str(product.get('name', '')).strip(),
                    'price': self._clean_price(product.get('price')),
                    'color': self._clean_color(product.get('color')),
                    'category': str(product.get('category', 'genel')).lower().strip(),
                    'stock': max(0, int(product.get('stock', 0))),
                    'description': str(product.get('description', '')).strip(),
                    'size': str(product.get('size', '')).strip(),
                    'material': str(product.get('material', '')).strip(),
                    'brand': str(product.get('brand', '')).strip()
                }
                
                # Remove empty strings
                clean_product = {k: v for k, v in clean_product.items() if v != ''}
                
                validated.append(clean_product)
                
            except Exception as e:
                logger.warning(f"⚠️ Product validation error: {e}")
                continue
        
        logger.info(f"✅ Validated {len(validated)} products")
        return validated
    
    def _clean_price(self, price) -> float:
        """Clean and validate price"""
        if price is None:
            return 0.0
        
        try:
            # Remove currency symbols and convert to float
            if isinstance(price, str):
                price = price.replace('₺', '').replace('TL', '').replace(',', '.').strip()
            
            return max(0.0, float(price))
        except:
            return 0.0
    
    def _clean_color(self, color) -> str:
        """Standardize color names"""
        if not color:
            return 'belirtilmemiş'
        
        color = str(color).lower().strip()
        
        # Color mapping
        color_map = {
            'red': 'kırmızı',
            'blue': 'mavi',
            'green': 'yeşil',
            'yellow': 'sarı',
            'black': 'siyah',
            'white': 'beyaz',
            'gray': 'gri',
            'grey': 'gri',
            'pink': 'pembe',
            'purple': 'mor',
            'orange': 'turuncu',
            'brown': 'kahverengi'
        }
        
        return color_map.get(color, color)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'supported_formats': list(self.supported_extensions),
            'model_used': 'gemini-2.0-flash-exp',
            'max_file_size': '10MB',
            'processing_features': [
                'Automatic product extraction',
                'Price standardization',
                'Color normalization',
                'Category classification',
                'Data validation'
            ]
        }

# Test function
def test_file_processor():
    """Test the file processor"""
    processor = AdminFileProcessor()
    
    # Create test data
    test_data = [
        {
            "name": "Kırmızı Elbise",
            "price": "299.99 TL",
            "color": "red",
            "category": "dress",
            "stock": 5
        },
        {
            "name": "Mavi Pantolon",
            "price": "199₺",
            "color": "blue",
            "category": "pants",
            "stock": 10
        }
    ]
    
    # Save test file
    test_file = 'test_products.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # Process file
    result = processor.process_uploaded_file(test_file, 'test_business')
    
    # Clean up
    os.remove(test_file)
    
    print("Test Result:", json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    test_file_processor()