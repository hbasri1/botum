#!/usr/bin/env python3
"""
Database Analyzer
Analyzes product database structure and available fields
"""

import json
import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class DatabaseAnalyzer:
    """Analyzes database structure for dynamic responses"""
    
    def __init__(self, products_file: str = 'data/products.json'):
        self.products_file = products_file
        self.available_fields = set()
        self.field_samples = {}
        self._analyze_database()
    
    def _analyze_database(self):
        """Analyze database structure"""
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            if not products:
                return
            
            # Analyze all fields across all products
            for product in products:
                for field, value in product.items():
                    self.available_fields.add(field)
                    
                    # Store sample values
                    if field not in self.field_samples:
                        self.field_samples[field] = []
                    
                    if value and len(self.field_samples[field]) < 3:
                        self.field_samples[field].append(str(value))
            
            logger.info(f"Database analysis complete. Available fields: {self.available_fields}")
            
        except Exception as e:
            logger.error(f"Database analysis error: {e}")
    
    def has_field(self, field_name: str) -> bool:
        """Check if database has a specific field"""
        return field_name.lower() in [f.lower() for f in self.available_fields]
    
    def has_size_info(self) -> bool:
        """Check if database has size/beden information"""
        size_fields = ['size', 'beden', 'sizes', 'bedenler', 'boy', 'kilo', 'measurements']
        return any(self.has_field(field) for field in size_fields)
    
    def has_material_info(self) -> bool:
        """Check if database has material information"""
        material_fields = ['material', 'malzeme', 'fabric', 'kumaş', 'composition']
        return any(self.has_field(field) for field in material_fields)
    
    def has_care_info(self) -> bool:
        """Check if database has care instructions"""
        care_fields = ['care', 'bakım', 'washing', 'yıkama', 'instructions']
        return any(self.has_field(field) for field in care_fields)
    
    def get_field_info(self, field_name: str) -> Dict:
        """Get information about a specific field"""
        for field in self.available_fields:
            if field.lower() == field_name.lower():
                return {
                    'exists': True,
                    'field_name': field,
                    'samples': self.field_samples.get(field, [])
                }
        return {'exists': False}
    
    def get_available_info_types(self) -> List[str]:
        """Get list of available information types"""
        info_types = []
        
        if self.has_size_info():
            info_types.append('beden')
        if self.has_material_info():
            info_types.append('malzeme')
        if self.has_care_info():
            info_types.append('bakım')
        if self.has_field('weight'):
            info_types.append('ağırlık')
        if self.has_field('dimensions'):
            info_types.append('ölçüler')
        
        return info_types
    
    def generate_dynamic_response(self, query_type: str, business_info: Dict) -> str:
        """Generate dynamic response based on available data"""
        query_lower = query_type.lower()
        
        # Size inquiry
        if any(word in query_lower for word in ['beden', 'size', 'boy', 'kilo']):
            if self.has_size_info():
                size_field = next((f for f in self.available_fields 
                                 if f.lower() in ['size', 'beden', 'sizes', 'bedenler']), None)
                samples = self.field_samples.get(size_field, [])
                response = f"📏 **Beden Bilgileri:**\n\n"
                if samples:
                    response += f"Mevcut bedenler: {', '.join(samples[:3])}\n\n"
                response += f"📞 Detaylı beden tablosu için: {business_info.get('phone', '0555 555 55 55')}"
                return response
            else:
                return f"📏 Beden bilgileri için web sitemizi ziyaret edebilirsiniz: {business_info.get('website', 'www.butik.com')}\n\n📞 Detaylı bilgi için bizi arayabilirsiniz: {business_info.get('phone', '0555 555 55 55')}"
        
        # Material inquiry
        elif any(word in query_lower for word in ['malzeme', 'material', 'kumaş', 'fabric']):
            if self.has_material_info():
                material_field = next((f for f in self.available_fields 
                                     if f.lower() in ['material', 'malzeme', 'fabric', 'kumaş']), None)
                samples = self.field_samples.get(material_field, [])
                response = f"🧵 **Malzeme Bilgileri:**\n\n"
                if samples:
                    response += f"Kullanılan malzemeler: {', '.join(samples[:3])}\n\n"
                response += f"📞 Detaylı malzeme bilgisi için: {business_info.get('phone', '0555 555 55 55')}"
                return response
            else:
                return f"🧵 Malzeme bilgileri için web sitemizi ziyaret edebilirsiniz: {business_info.get('website', 'www.butik.com')}\n\n📞 Detaylı bilgi için bizi arayabilirsiniz: {business_info.get('phone', '0555 555 55 55')}"
        
        # Care inquiry
        elif any(word in query_lower for word in ['bakım', 'care', 'yıkama', 'washing']):
            if self.has_care_info():
                care_field = next((f for f in self.available_fields 
                                 if f.lower() in ['care', 'bakım', 'washing', 'yıkama']), None)
                samples = self.field_samples.get(care_field, [])
                response = f"🧼 **Bakım Bilgileri:**\n\n"
                if samples:
                    response += f"Bakım talimatları: {', '.join(samples[:3])}\n\n"
                response += f"📞 Detaylı bakım bilgisi için: {business_info.get('phone', '0555 555 55 55')}"
                return response
            else:
                return f"🧼 Bakım bilgileri için web sitemizi ziyaret edebilirsiniz: {business_info.get('website', 'www.butik.com')}\n\n📞 Detaylı bilgi için bizi arayabilirsiniz: {business_info.get('phone', '0555 555 55 55')}"
        
        # Default response
        return f"ℹ️ Bu bilgi için web sitemizi ziyaret edebilirsiniz: {business_info.get('website', 'www.butik.com')}\n\n📞 Detaylı bilgi için bizi arayabilirsiniz: {business_info.get('phone', '0555 555 55 55')}"