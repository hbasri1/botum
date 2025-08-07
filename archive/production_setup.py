#!/usr/bin/env python3
"""
Production Setup - Veriyi temizle ve sistemi hazırla
"""

import json
import os
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_and_validate_products() -> List[Dict]:
    """Ürün verisini temizle ve doğrula"""
    logger.info("🧹 Ürün verisi temizleniyor...")
    
    with open('data/products.json', 'r', encoding='utf-8') as f:
        raw_products = json.load(f)
    
    logger.info(f"📊 Ham veri: {len(raw_products)} ürün")
    
    valid_products = []
    cleaned_count = 0
    
    for product in raw_products:
        # Veri temizleme
        cleaned_product = {}
        
        # İsim kontrolü ve temizleme
        name = product.get('name', '').strip()
        if not name:
            continue
        cleaned_product['name'] = name
        
        # Renk kontrolü ve temizleme
        color = str(product.get('color', '')).strip().upper()
        if color in ['NAN', 'NULL', '', 'NONE']:
            # Renk yoksa varsayılan renk ata
            color = 'ÇOK RENKLİ'
            cleaned_count += 1
        cleaned_product['color'] = color
        
        # Fiyat kontrolü
        try:
            price = float(product.get('price', 0))
            final_price = float(product.get('final_price', 0))
            
            if price <= 0 or final_price <= 0:
                continue
                
            cleaned_product['price'] = price
            cleaned_product['final_price'] = final_price
            cleaned_product['discount'] = float(product.get('discount', 0))
            
        except (ValueError, TypeError):
            continue
        
        # Diğer alanlar
        cleaned_product['category'] = product.get('category', 'İç Giyim')
        cleaned_product['stock'] = int(product.get('stock', 10))
        
        # Ürün açıklaması oluştur (arama için)
        description_parts = [
            name,
            color,
            cleaned_product['category']
        ]
        
        # Fiyat aralığı ekle
        if final_price < 1000:
            description_parts.append('ekonomik')
        elif final_price < 2000:
            description_parts.append('orta segment')
        else:
            description_parts.append('premium')
        
        cleaned_product['description'] = ' '.join(description_parts).lower()
        
        valid_products.append(cleaned_product)
    
    logger.info(f"✅ Temizlenmiş veri: {len(valid_products)} ürün")
    logger.info(f"🔧 {cleaned_count} ürünün rengi düzeltildi")
    
    # Temizlenmiş veriyi kaydet
    with open('data/products_clean.json', 'w', encoding='utf-8') as f:
        json.dump(valid_products, f, ensure_ascii=False, indent=2)
    
    # Orijinal dosyayı yedekle ve güncelle
    os.rename('data/products.json', 'data/products_backup.json')
    os.rename('data/products_clean.json', 'data/products.json')
    
    logger.info("💾 Temizlenmiş veri kaydedildi")
    
    return valid_products

def setup_environment():
    """Çevre değişkenlerini kontrol et"""
    logger.info("🔧 Çevre değişkenleri kontrol ediliyor...")
    
    required_vars = ['GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Eksik çevre değişkenleri: {missing_vars}")
        logger.info("💡 .env dosyası oluşturun:")
        for var in missing_vars:
            logger.info(f"   {var}=your_api_key_here")
        return False
    
    logger.info("✅ Tüm çevre değişkenleri mevcut")
    return True

def create_production_structure():
    """Production klasör yapısını oluştur"""
    logger.info("📁 Production klasör yapısı oluşturuluyor...")
    
    directories = [
        'data',
        'embeddings',
        'logs',
        'static',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    logger.info("✅ Klasör yapısı hazır")

def main():
    """Ana setup fonksiyonu"""
    logger.info("🚀 Production Setup Başlıyor...")
    
    # 1. Klasör yapısını oluştur
    create_production_structure()
    
    # 2. Çevre değişkenlerini kontrol et
    if not setup_environment():
        return False
    
    # 3. Veriyi temizle
    products = clean_and_validate_products()
    
    # 4. İstatistikler
    colors = {}
    price_ranges = {'0-1000': 0, '1000-2000': 0, '2000+': 0}
    
    for product in products:
        # Renk istatistikleri
        color = product['color']
        colors[color] = colors.get(color, 0) + 1
        
        # Fiyat istatistikleri
        price = product['final_price']
        if price < 1000:
            price_ranges['0-1000'] += 1
        elif price < 2000:
            price_ranges['1000-2000'] += 1
        else:
            price_ranges['2000+'] += 1
    
    logger.info("📈 Ürün İstatistikleri:")
    logger.info(f"   Toplam ürün: {len(products)}")
    logger.info(f"   Renk çeşidi: {len(colors)}")
    logger.info(f"   En çok renk: {max(colors.items(), key=lambda x: x[1])}")
    logger.info(f"   Fiyat dağılımı: {price_ranges}")
    
    logger.info("🎉 Production setup tamamlandı!")
    return True

if __name__ == "__main__":
    main()