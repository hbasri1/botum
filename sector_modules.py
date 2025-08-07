#!/usr/bin/env python3
"""
Multi-Sector Modular System
Different sectors have different product categories and attributes
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class SectorType(Enum):
    FASHION = "fashion"  # Giyim, aksesuar
    HOME = "home"        # Ev eşyası, dekorasyon
    ELECTRONICS = "electronics"  # Elektronik
    BEAUTY = "beauty"    # Kozmetik, bakım
    FOOD = "food"        # Gıda, içecek

@dataclass
class SectorConfig:
    """Sector-specific configuration"""
    name: str
    categories: List[str]
    attributes: List[str]
    size_types: List[str]
    color_relevant: bool
    clarification_examples: List[str]

class SectorManager:
    """Manages different sector configurations"""
    
    def __init__(self):
        self.sectors = {
            SectorType.FASHION: SectorConfig(
                name="Moda & Giyim",
                categories=['gecelik', 'pijama', 'sabahlık', 'takım', 'elbise', 'şort', 'bluz', 'pantolon'],
                attributes=['renk', 'beden', 'kumaş', 'desen', 'stil'],
                size_types=['XS', 'S', 'M', 'L', 'XL', 'XXL', '36', '38', '40', '42', '44', '46'],
                color_relevant=True,
                clarification_examples=[
                    'siyah gecelik',
                    'afrika gecelik', 
                    'hamile pijama',
                    'dantelli sabahlık',
                    'büyük beden takım'
                ]
            ),
            
            SectorType.HOME: SectorConfig(
                name="Ev & Yaşam",
                categories=['masa', 'sandalye', 'koltuk', 'yatak', 'dolap', 'lamba', 'halı', 'perde'],
                attributes=['renk', 'malzeme', 'boyut', 'stil', 'oda'],
                size_types=['küçük', 'orta', 'büyük', '2 kişilik', '3 kişilik', 'tek kişilik'],
                color_relevant=True,
                clarification_examples=[
                    'siyah masa',
                    'ahşap sandalye',
                    'büyük koltuk',
                    'yatak odası dolabı'
                ]
            ),
            
            SectorType.ELECTRONICS: SectorConfig(
                name="Elektronik",
                categories=['telefon', 'laptop', 'tablet', 'kulaklık', 'şarj', 'kılıf', 'aksesuar'],
                attributes=['marka', 'model', 'renk', 'kapasite', 'özellik'],
                size_types=['32GB', '64GB', '128GB', '256GB', '13 inç', '15 inç'],
                color_relevant=True,
                clarification_examples=[
                    'iphone kılıfı',
                    'samsung kulaklık',
                    'laptop çantası',
                    'wireless şarj'
                ]
            ),
            
            SectorType.BEAUTY: SectorConfig(
                name="Güzellik & Bakım",
                categories=['ruj', 'fondöten', 'maskara', 'krem', 'parfüm', 'şampuan', 'sabun'],
                attributes=['renk', 'ton', 'cilt tipi', 'saç tipi', 'koku'],
                size_types=['30ml', '50ml', '100ml', '250ml', '500ml'],
                color_relevant=True,
                clarification_examples=[
                    'kırmızı ruj',
                    'mat fondöten',
                    'yağlı cilt kremi',
                    'erkek parfümü'
                ]
            )
        }
        
        # Default to fashion sector
        self.current_sector = SectorType.FASHION
    
    def get_current_config(self) -> SectorConfig:
        """Get current sector configuration"""
        return self.sectors[self.current_sector]
    
    def set_sector(self, sector: SectorType):
        """Set active sector"""
        self.current_sector = sector
    
    def detect_sector_from_query(self, query: str) -> Optional[SectorType]:
        """Auto-detect sector from user query"""
        query_lower = query.lower()
        
        # Check each sector's categories
        for sector_type, config in self.sectors.items():
            for category in config.categories:
                if category in query_lower:
                    return sector_type
        
        return None
    
    def get_clarification_response(self, category: str) -> str:
        """Get sector-specific clarification response"""
        config = self.get_current_config()
        
        response = f"{category.title()} arıyorsunuz. Hangi özellikte olsun?\n\n"
        response += f"💡 **{config.name} Örnekleri:**\n"
        
        for example in config.clarification_examples[:4]:
            response += f"• '{example}'\n"
        
        return response
    
    def is_general_category(self, query: str) -> bool:
        """Check if query is a general category for current sector"""
        config = self.get_current_config()
        query_lower = query.strip().lower()
        
        # Check exact matches and "var mı" patterns
        for category in config.categories:
            if query_lower == category or query_lower == f"{category} var mı":
                return True
        
        return False
    
    def get_relevant_attributes(self) -> List[str]:
        """Get relevant attributes for current sector"""
        return self.get_current_config().attributes
    
    def is_color_relevant(self) -> bool:
        """Check if color is relevant for current sector"""
        return self.get_current_config().color_relevant

# Global sector manager instance
sector_manager = SectorManager()

def get_sector_manager() -> SectorManager:
    """Get global sector manager instance"""
    return sector_manager