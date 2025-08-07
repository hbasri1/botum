#!/usr/bin/env python3
"""
MVP Business System - Basit ve Etkili
Manuel süreçlerle başlayıp sonra otomatikleştirme
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import os

@dataclass
class Business:
    """İşletme modeli"""
    business_id: str
    name: str
    email: str
    phone: str
    website: str
    instagram_handle: str
    sector: str
    status: str  # active, inactive, trial
    created_at: str
    chatbot_config: Dict
    owner_name: str = ""
    instagram_user_id: str = ""
    instagram_access_token: str = ""
    registration_source: str = "admin"
    registration_date: str = ""
    
@dataclass
class BusinessProduct:
    """İşletme ürünü"""
    product_id: str
    business_id: str
    name: str
    description: str
    price: float
    final_price: float
    discount: float
    color: str
    category: str
    stock: int
    created_at: str

class MVPBusinessManager:
    """MVP İşletme yöneticisi"""
    
    def __init__(self):
        self.data_dir = "business_data"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Gerekli klasörleri oluştur"""
        os.makedirs(f"{self.data_dir}/businesses", exist_ok=True)
        os.makedirs(f"{self.data_dir}/products", exist_ok=True)
        os.makedirs(f"{self.data_dir}/conversations", exist_ok=True)
        os.makedirs(f"{self.data_dir}/uploads", exist_ok=True)
    
    def create_business(self, business_data: Dict) -> str:
        """Yeni işletme oluştur"""
        
        business_id = str(uuid.uuid4())[:8]  # Kısa ID
        
        # Default chatbot config
        default_config = {
            "chatbot_name": "Asistan",
            "welcome_message": f"Merhaba! {business_data['name']} asistanıyım. Size nasıl yardımcı olabilirim?",
            "business_info": {
                "name": business_data["name"],
                "phone": business_data["phone"],
                "website": business_data.get("website", ""),
                "email": business_data["email"]
            },
            "theme": {
                "primary_color": "#2563eb",
                "secondary_color": "#64748b"
            }
        }
        
        business = Business(
            business_id=business_id,
            name=business_data["name"],
            email=business_data["email"],
            phone=business_data["phone"],
            website=business_data.get("website", ""),
            instagram_handle=business_data.get("instagram_handle", ""),
            sector=business_data.get("sector", "fashion"),
            status=business_data.get("status", "trial"),
            created_at=datetime.now().isoformat(),
            chatbot_config=default_config,
            owner_name=business_data.get("owner_name", ""),
            instagram_user_id=business_data.get("instagram_user_id", ""),
            instagram_access_token=business_data.get("instagram_access_token", ""),
            registration_source=business_data.get("registration_source", "admin"),
            registration_date=business_data.get("registration_date", datetime.now().isoformat())
        )
        
        # Dosyaya kaydet
        self._save_business(business)
        
        # İşletme klasörlerini oluştur
        os.makedirs(f"{self.data_dir}/products/{business_id}", exist_ok=True)
        os.makedirs(f"{self.data_dir}/conversations/{business_id}", exist_ok=True)
        
        return business_id
    
    def load_business_products(self, business_id: str, file_path: str) -> int:
        """İşletme ürünlerini dosyadan yükle (Manuel süreç)"""
        
        try:
            # Dosya formatını tespit et
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_products = json.load(f)
            elif file_path.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(file_path)
                raw_products = df.to_dict('records')
            else:
                raise ValueError("Desteklenmeyen dosya formatı")
            
            # Ürünleri standardize et
            products = []
            for item in raw_products:
                product = self._standardize_product(business_id, item)
                products.append(product)
            
            # Ürünleri kaydet
            self._save_products(business_id, products)
            
            return len(products)
            
        except Exception as e:
            print(f"Ürün yükleme hatası: {e}")
            return 0
    
    def _standardize_product(self, business_id: str, raw_product: Dict) -> BusinessProduct:
        """Ürünü standart formata dönüştür"""
        
        # Flexible field mapping
        name = (raw_product.get('name') or 
                raw_product.get('product_name') or 
                raw_product.get('title') or 
                raw_product.get('ürün_adı') or 
                "Ürün")
        
        description = (raw_product.get('description') or 
                      raw_product.get('desc') or 
                      raw_product.get('açıklama') or 
                      "")
        
        price = float(raw_product.get('price', 0) or 
                     raw_product.get('fiyat', 0) or 
                     raw_product.get('original_price', 0) or 0)
        
        final_price = float(raw_product.get('final_price', price) or 
                           raw_product.get('sale_price', price) or 
                           raw_product.get('indirimli_fiyat', price) or price)
        
        discount = float(raw_product.get('discount', 0) or 
                        raw_product.get('indirim', 0) or 0)
        
        color = (raw_product.get('color') or 
                raw_product.get('renk') or 
                raw_product.get('colour') or 
                "")
        
        category = (raw_product.get('category') or 
                   raw_product.get('kategori') or 
                   raw_product.get('type') or 
                   "")
        
        stock = int(raw_product.get('stock', 1) or 
                   raw_product.get('stok', 1) or 
                   raw_product.get('quantity', 1) or 1)
        
        return BusinessProduct(
            product_id=str(uuid.uuid4())[:8],
            business_id=business_id,
            name=name,
            description=description,
            price=price,
            final_price=final_price,
            discount=discount,
            color=color.upper() if color else "",
            category=category,
            stock=stock,
            created_at=datetime.now().isoformat()
        )
    
    def get_business_chatbot_instance(self, business_id: str):
        """İşletmeye özel chatbot instance'ı oluştur"""
        
        business = self._load_business(business_id)
        if not business:
            return None
        
        products = self._load_products(business_id)
        
        # Mevcut chatbot sistemini business-specific hale getir
        from improved_final_mvp_system import ImprovedFinalMVPChatbot
        
        # Business-specific chatbot (normal init)
        chatbot = ImprovedFinalMVPChatbot()
        
        # İşletme bilgilerini güncelle
        chatbot.business_info = {
            'name': business.name,
            'phone': business.phone,
            'email': business.email,
            'website': business.website,
            'instagram': business.instagram_handle
        }
        
        # Sektör bilgisini ekle
        chatbot.sector = business.sector
        
        return chatbot
    
    def _convert_to_product_object(self, business_product: BusinessProduct):
        """BusinessProduct'ı Product object'e dönüştür"""
        from improved_final_mvp_system import Product
        
        return Product(
            name=business_product.name,
            color=business_product.color,
            price=business_product.price,
            discount=business_product.discount,
            final_price=business_product.final_price,
            category=business_product.category,
            stock=business_product.stock,
            description=business_product.description
        )
    
    def _save_business(self, business: Business):
        """İşletmeyi dosyaya kaydet"""
        file_path = f"{self.data_dir}/businesses/{business.business_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(business), f, ensure_ascii=False, indent=2)
    
    def _load_business(self, business_id: str) -> Optional[Business]:
        """İşletmeyi dosyadan yükle"""
        file_path = f"{self.data_dir}/businesses/{business_id}.json"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Business(**data)
        except FileNotFoundError:
            return None
    
    def _save_products(self, business_id: str, products: List[BusinessProduct]):
        """Ürünleri dosyaya kaydet"""
        file_path = f"{self.data_dir}/products/{business_id}/products.json"
        products_data = [asdict(p) for p in products]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, ensure_ascii=False, indent=2)
    
    def _load_products(self, business_id: str) -> List[BusinessProduct]:
        """Ürünleri dosyadan yükle"""
        file_path = f"{self.data_dir}/products/{business_id}/products.json"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [BusinessProduct(**item) for item in data]
        except FileNotFoundError:
            return []
    
    def list_businesses(self) -> List[Dict]:
        """Tüm işletmeleri listele"""
        businesses = []
        business_dir = f"{self.data_dir}/businesses"
        
        if os.path.exists(business_dir):
            for filename in os.listdir(business_dir):
                if filename.endswith('.json'):
                    business_id = filename.replace('.json', '')
                    business = self._load_business(business_id)
                    if business:
                        products = self._load_products(business_id)
                        businesses.append({
                            "business_id": business.business_id,
                            "name": business.name,
                            "email": business.email,
                            "phone": business.phone,
                            "website": business.website,
                            "instagram_handle": business.instagram_handle,
                            "sector": business.sector,
                            "status": business.status,
                            "product_count": len(products),
                            "created_at": business.created_at
                        })
        
        return businesses
    
    def get_business_stats(self, business_id: str) -> Dict:
        """İşletme istatistikleri"""
        business = self._load_business(business_id)
        products = self._load_products(business_id)
        
        if not business:
            return {}
        
        return {
            "business_name": business.name,
            "status": business.status,
            "product_count": len(products),
            "categories": list(set([p.category for p in products if p.category])),
            "colors": list(set([p.color for p in products if p.color])),
            "price_range": {
                "min": min([p.final_price for p in products]) if products else 0,
                "max": max([p.final_price for p in products]) if products else 0
            },
            "created_at": business.created_at
        }
    
    def get_all_businesses(self) -> List[Dict]:
        """Tüm işletmeleri döndür (admin paneli için)"""
        return self.list_businesses()
    
    def get_business(self, business_id: str) -> Optional[Dict]:
        """Tek işletme bilgisi döndür"""
        business = self._load_business(business_id)
        if not business:
            return None
        
        products = self._load_products(business_id)
        return {
            "business_id": business.business_id,
            "name": business.name,
            "email": business.email,
            "phone": business.phone,
            "website": business.website,
            "instagram_handle": business.instagram_handle,
            "sector": business.sector,
            "status": business.status,
            "created_at": business.created_at,
            "product_count": len(products)
        }
    
    def get_products(self, business_id: str) -> List[Dict]:
        """İşletme ürünlerini döndür"""
        products = self._load_products(business_id)
        return [asdict(p) for p in products]
    
    def add_product(self, business_id: str, product_data: Dict) -> str:
        """Tek ürün ekle"""
        # Mevcut ürünleri yükle
        products = self._load_products(business_id)
        
        # Yeni ürün oluştur
        new_product = BusinessProduct(
            product_id=str(uuid.uuid4())[:8],
            business_id=business_id,
            name=product_data.get('name', ''),
            description=product_data.get('description', ''),
            price=float(product_data.get('price', 0)),
            final_price=float(product_data.get('price', 0)),
            discount=0.0,
            color=product_data.get('color', ''),
            category=product_data.get('category', ''),
            stock=int(product_data.get('stock', 0)),
            created_at=datetime.now().isoformat()
        )
        
        # Listeye ekle
        products.append(new_product)
        
        # Kaydet
        self._save_products(business_id, products)
        
        return new_product.product_id
    
    def create_business_from_params(self, name: str, email: str, phone: str, website: str = '', 
                                   instagram_handle: str = '', sector: str = 'general') -> str:
        """Yeni işletme oluştur (admin paneli için)"""
        business_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'website': website,
            'instagram_handle': instagram_handle,
            'sector': sector
        }
        return self.create_business(business_data)

# Global business manager instance
business_manager = MVPBusinessManager()

def get_business_manager():
    """Global business manager'ı döndür"""
    return business_manager