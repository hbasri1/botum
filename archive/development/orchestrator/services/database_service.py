"""
Database Service - Gerçek ürün verileriyle çalışan veritabanı servisi
"""

import logging
import json
import time
import os
from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service sınıfı - gerçek ürün verileriyle"""
    
    def __init__(self):
        # Multi-business yapısı
        self.businesses = {}  # business_id -> business_data
        self.products = []  # Backward compatibility
        self.business_info = {}  # Backward compatibility
        self._load_all_businesses()
    
    def _load_all_businesses(self):
        """Tüm işletmeleri yükle"""
        try:
            # Yeni multi-business yapısını yükle
            businesses_dir = os.path.join(os.path.dirname(__file__), '../../data/businesses')
            
            if os.path.exists(businesses_dir):
                for filename in os.listdir(businesses_dir):
                    if filename.endswith('.json'):
                        business_id = filename.replace('.json', '')
                        business_path = os.path.join(businesses_dir, filename)
                        
                        with open(business_path, 'r', encoding='utf-8') as f:
                            business_data = json.load(f)
                            self.businesses[business_id] = business_data
                            
                        logger.info(f"Loaded business: {business_id} with {len(business_data.get('products', []))} products")
            
            # Backward compatibility - fashion_boutique için eski dosyaları yükle
            if 'fashion_boutique' not in self.businesses:
                self._load_legacy_data()
            
            # Default business için products ve business_info set et
            if 'fashion_boutique' in self.businesses:
                self.products = self.businesses['fashion_boutique'].get('products', [])
                self.business_info = {'fashion_boutique': self.businesses['fashion_boutique'].get('business_info', {})}
                
        except Exception as e:
            logger.error(f"Error loading businesses: {str(e)}")
            self.businesses = {}
            self._load_legacy_data()
    
    def _load_legacy_data(self):
        """Eski format verileri yükle (backward compatibility)"""
        try:
            # Products.json dosyasını yükle
            products_path = os.path.join(os.path.dirname(__file__), '../../data/products.json')
            if os.path.exists(products_path):
                with open(products_path, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                logger.info(f"Loaded {len(products)} products from legacy format")
            else:
                products = []
            
            # Business meta verilerini yükle
            meta_path = os.path.join(os.path.dirname(__file__), '../../data/butik_meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
            else:
                meta_data = {
                    "phone": "0555 555 55 55",
                    "iade_policy": "14 gün içinde iade edilebilir",
                    "shipping_info": "Ücretsiz kargo 200 TL üzeri",
                    "site": "www.butikcemunay.com"
                }
            
            # Legacy format'ı yeni format'a çevir
            self.businesses['fashion_boutique'] = {
                'business_info': {
                    'id': 'fashion_boutique',
                    'name': 'Butik Cemünay',
                    'contact': {
                        'phone': meta_data.get('phone', ''),
                    },
                    'policies': {
                        'return_policy': meta_data.get('iade_policy', ''),
                        'shipping_info': meta_data.get('shipping_info', ''),
                    },
                    'website': meta_data.get('site', '')
                },
                'products': products
            }
            
            # Backward compatibility
            self.products = products
            self.business_info = {'fashion_boutique': meta_data}
                
        except Exception as e:
            logger.error(f"Error loading legacy data: {str(e)}")
            self.products = []
            self.business_info = {}
    
    def _normalize_turkish_text(self, text: str) -> str:
        """Türkçe metni normalize et - Geliştirilmiş"""
        if not text:
            return ""
        
        text = text.lower().strip()
        
        # Türkçe ekleri temizle - daha kapsamlı
        replacements = {
            'geceliği': 'gecelik', 'geceliğin': 'gecelik', 'geceliğe': 'gecelik',
            'pijamayı': 'pijama', 'pijamanın': 'pijama', 'pijamaya': 'pijama',
            'elbiseyi': 'elbise', 'elbisenin': 'elbise', 'elbiseye': 'elbise',
            'sabahlığı': 'sabahlık', 'sabahlığın': 'sabahlık', 'sabahlığa': 'sabahlık',
            'takımı': 'takım', 'takımın': 'takım', 'takıma': 'takım', 'takimi': 'takım'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Özel keyword mapping
        keyword_mapping = {
            'hamile lohusa': 'hamile',  # "hamile lohusa takım" -> "hamile takım"
            'lohusa hamile': 'hamile',
        }
        
        for old, new in keyword_mapping.items():
            text = text.replace(old, new)
        
        return text
    
    async def get_product_info(self, business_id: str, product_name: str) -> Optional[Dict[str, Any]]:
        """
        Ürün bilgisini getir - Business-aware Semantic Search ile
        
        Args:
            business_id: İşletme ID
            product_name: Ürün adı
            
        Returns:
            Dict: Ürün bilgisi veya None
        """
        try:
            # İşletme verilerini al
            business_data = self.businesses.get(business_id)
            if not business_data:
                logger.warning(f"Business not found: {business_id}")
                return None
            
            products = business_data.get('products', [])
            if not products:
                return None
            
            # Business-specific semantic search
            try:
                from .simple_semantic_search import SimpleSemanticSearch
                semantic_search = SimpleSemanticSearch()
                # Override products for this business
                semantic_search.products = products
                semantic_search.product_embeddings = {}  # Reset cache for business-specific products
                
                # En iyi eşleşmeyi bul
                best_match = await semantic_search.find_best_match(product_name)
            except Exception as e:
                logger.error(f"Semantic search error: {str(e)}")
                # Fallback to business-specific fuzzy search
                return await self._fallback_product_search_for_business(business_id, product_name)
            
            if best_match and best_match.get('similarity', 0) > 0.4:  # Minimum threshold
                # Ürün bilgisini standardize et
                return {
                    "id": best_match.get("id", 0),
                    "name": best_match.get("name", ""),
                    "price": best_match.get("price", 0),
                    "original_price": best_match.get("original_price"),
                    "stock_quantity": best_match.get("stock_quantity", 0),
                    "category": best_match.get("category", ""),
                    "description": best_match.get("description", ""),
                    "color": best_match.get("color", ""),
                    "size": best_match.get("size", ""),
                    "code": best_match.get("code", ""),
                    "discount": best_match.get("discount", ""),
                    "material": best_match.get("material", ""),
                    "features": best_match.get("features", []),
                    "tags": best_match.get("tags", []),
                    "attributes": {
                        "colors": [best_match.get("color", "")] if best_match.get("color") else [],
                        "sizes": [best_match.get("size", "")] if best_match.get("size") else [],
                        "code": best_match.get("code", ""),
                        "discount": best_match.get("discount", "")
                    },
                    "business_id": business_id,
                    "match_score": best_match.get("similarity", 0),
                    "semantic_similarity": best_match.get("semantic_similarity", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Get product info error: {str(e)}")
            return None
    
    async def _fallback_product_search_for_business(self, business_id: str, product_name: str) -> Optional[Dict[str, Any]]:
        """Business-specific fallback product search"""
        try:
            business_data = self.businesses.get(business_id)
            if not business_data:
                return None
            
            products = business_data.get('products', [])
            if not products:
                return None
            
            normalized_query = self._normalize_turkish_text(product_name)
            best_match = None
            best_score = 0
            
            for product in products:
                product_name_normalized = self._normalize_turkish_text(product.get("name", ""))
                
                # Token set ratio
                score = fuzz.token_set_ratio(normalized_query, product_name_normalized)
                
                # Bonuslar
                query_words = normalized_query.split()
                
                # Hamile/lohusa bonus
                if "hamile" in normalized_query:
                    if "hamile" in product_name_normalized or "lohusa" in product_name_normalized:
                        score += 20
                
                # Takım bonus
                if "takım" in normalized_query:
                    if "takım" in product_name_normalized:
                        score += 15
                    elif any(word in product_name_normalized for word in ["alt", "üst"]):
                        score += 10
                
                # Kelime eşleştirme
                if len(query_words) > 0:
                    matched_words = sum(1 for word in query_words if word in product_name_normalized)
                    match_ratio = matched_words / len(query_words)
                    
                    if match_ratio >= 0.8:
                        score += 15
                    elif match_ratio >= 0.5:
                        score += 8
                
                if score > best_score and score > 65:
                    best_score = score
                    best_match = product
            
            if best_match:
                return {
                    "id": best_match.get("id", 0),
                    "name": best_match.get("name", ""),
                    "price": float(best_match.get("final_price", 0)),
                    "original_price": float(best_match.get("price", 0)) if best_match.get("price") else None,
                    "stock_quantity": int(best_match.get("stock", 0)),
                    "category": best_match.get("category", ""),
                    "description": best_match.get("description", ""),
                    "color": best_match.get("color", ""),
                    "size": best_match.get("size", ""),
                    "code": best_match.get("code", ""),
                    "discount": best_match.get("discount", ""),
                    "material": best_match.get("material", ""),
                    "features": best_match.get("features", []),
                    "tags": best_match.get("tags", []),
                    "attributes": {
                        "colors": [best_match.get("color", "")] if best_match.get("color") else [],
                        "sizes": [best_match.get("size", "")] if best_match.get("size") else [],
                        "code": best_match.get("code", ""),
                        "discount": best_match.get("discount", "")
                    },
                    "business_id": business_id,
                    "match_score": best_score
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Fallback product search error: {str(e)}")
            return None
    
    async def _fallback_product_search(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Fallback product search with enhanced fuzzy matching"""
        try:
            if not self.products:
                return None
            
            normalized_query = self._normalize_turkish_text(product_name)
            best_match = None
            best_score = 0
            
            for product in self.products:
                product_name_normalized = self._normalize_turkish_text(product["name"])
                
                # Token set ratio
                score = fuzz.token_set_ratio(normalized_query, product_name_normalized)
                
                # Bonuslar
                query_words = normalized_query.split()
                
                # Hamile/lohusa bonus
                if "hamile" in normalized_query:
                    if "hamile" in product_name_normalized or "lohusa" in product_name_normalized:
                        score += 20
                
                # Takım bonus
                if "takım" in normalized_query:
                    if "takım" in product_name_normalized:
                        score += 15
                    elif any(word in product_name_normalized for word in ["alt", "üst"]):
                        score += 10
                
                # Kelime eşleştirme
                if len(query_words) > 0:
                    matched_words = sum(1 for word in query_words if word in product_name_normalized)
                    match_ratio = matched_words / len(query_words)
                    
                    if match_ratio >= 0.8:
                        score += 15
                    elif match_ratio >= 0.5:
                        score += 8
                
                if score > best_score and score > 65:
                    best_score = score
                    best_match = product
            
            if best_match:
                return {
                    "id": best_match.get("id", 0),
                    "name": best_match["name"],
                    "price": float(best_match.get("final_price", 0)),
                    "original_price": float(best_match.get("price", 0)) if best_match.get("price") else None,
                    "stock_quantity": int(best_match.get("stock", 0)),
                    "category": best_match.get("category", ""),
                    "description": best_match.get("description", ""),
                    "color": best_match.get("color", ""),
                    "size": best_match.get("size", ""),
                    "code": best_match.get("code", ""),
                    "discount": best_match.get("discount", ""),
                    "material": best_match.get("material", ""),
                    "attributes": {
                        "colors": [best_match.get("color", "")] if best_match.get("color") else [],
                        "sizes": [best_match.get("size", "")] if best_match.get("size") else [],
                        "code": best_match.get("code", ""),
                        "discount": best_match.get("discount", "")
                    },
                    "business_id": "fashion_boutique",
                    "match_score": best_score
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Fallback product search error: {str(e)}")
            return None
    
    async def get_business_info(self, business_id: str, info_type: str) -> Optional[str]:
        """
        İşletme bilgisini getir
        
        Args:
            business_id: İşletme ID
            info_type: Bilgi türü
            
        Returns:
            str: İşletme bilgisi veya None
        """
        try:
            business_data = self.business_info.get(business_id, {})
            
            # Info type mapping
            info_mapping = {
                "telefon": "phone",
                "phone": "phone",
                "iade": "iade_policy",
                "iade_policy": "iade_policy",
                "kargo": "shipping_info",
                "shipping_info": "shipping_info",
                "teslimat": "shipping_info",
                "site": "site",
                "web": "site",
                "website": "site"
            }
            
            mapped_key = info_mapping.get(info_type.lower(), info_type.lower())
            return business_data.get(mapped_key)
            
        except Exception as e:
            logger.error(f"Get business info error: {str(e)}")
            return None
    
    async def get_popular_products(self, business_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Popüler ürünleri getir - gerçek verilerle
        
        Args:
            business_id: İşletme ID
            limit: Maksimum ürün sayısı
            
        Returns:
            List: Popüler ürünler listesi
        """
        try:
            if not self.products:
                return []
            
            # İlk N ürünü popüler kabul et (gerçekte popularity score olacak)
            popular_products = []
            
            for product in self.products[:limit]:
                popular_products.append({
                    "id": product.get("id", 0),
                    "name": product["name"],
                    "price": float(product.get("final_price", 0)),
                    "stock_quantity": int(product.get("stock", 0)),
                    "category": product.get("category", ""),
                    "code": product.get("code", "")
                })
            
            return popular_products
            
        except Exception as e:
            logger.error(f"Get popular products error: {str(e)}")
            return []
    
    async def find_similar_products(self, business_id: str, product_name: str, 
                                  limit: int = 3) -> List[Dict[str, Any]]:
        """
        Benzer ürünleri bul - gerçek verilerle
        
        Args:
            business_id: İşletme ID
            product_name: Ürün adı
            limit: Maksimum ürün sayısı
            
        Returns:
            List: Benzer ürünler listesi
        """
        try:
            if not self.products:
                return []
            
            normalized_query = self._normalize_turkish_text(product_name)
            similar_products = []
            
            for product in self.products:
                product_name_normalized = self._normalize_turkish_text(product["name"])
                
                # Similarity score hesapla
                score = fuzz.token_set_ratio(normalized_query, product_name_normalized)
                
                # Orta seviye benzerlik (50-75 arası)
                if 50 <= score <= 75:
                    similar_products.append({
                        "id": product.get("id", 0),
                        "name": product["name"],
                        "price": float(product.get("final_price", 0)),
                        "stock_quantity": int(product.get("stock", 0)),
                        "category": product.get("category", ""),
                        "code": product.get("code", ""),
                        "similarity_score": score
                    })
            
            # Score'a göre sırala ve limit uygula
            similar_products.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_products[:limit]
            
        except Exception as e:
            logger.error(f"Find similar products error: {str(e)}")
            return []
    
    async def get_all_products(self, business_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Tüm ürünleri getir - gerçek verilerle
        
        Args:
            business_id: İşletme ID
            limit: Maksimum ürün sayısı
            
        Returns:
            List: Ürünler listesi
        """
        try:
            if not self.products:
                return []
            
            all_products = []
            
            for product in self.products[:limit]:
                all_products.append({
                    "id": product.get("id", 0),
                    "name": product["name"],
                    "price": float(product.get("final_price", 0)),
                    "stock_quantity": int(product.get("stock", 0)),
                    "category": product.get("category", ""),
                    "code": product.get("code", "")
                })
            
            return all_products
            
        except Exception as e:
            logger.error(f"Get all products error: {str(e)}")
            return []
    
    async def search_products_by_name(self, product_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Ürün adına göre arama yap
        
        Args:
            product_name: Ürün adı
            limit: Maksimum sonuç sayısı
            
        Returns:
            List: Bulunan ürünler
        """
        try:
            if not self.products or not product_name:
                return []
            
            normalized_query = self._normalize_turkish_text(product_name)
            scored_products = []
            
            for product in self.products:
                product_name_normalized = self._normalize_turkish_text(product["name"])
                
                # Token set ratio kullan
                score = fuzz.token_set_ratio(normalized_query, product_name_normalized)
                
                # Bonus puanlar
                if all(word in product_name_normalized for word in normalized_query.split()):
                    score += 10
                
                if normalized_query == product_name_normalized:
                    score += 20
                
                if score > 75:  # Threshold
                    scored_products.append({
                        "product": product,
                        "score": score
                    })
            
            # Score'a göre sırala
            scored_products.sort(key=lambda x: x["score"], reverse=True)
            
            # Sonuçları formatla
            results = []
            for item in scored_products[:limit]:
                product = item["product"]
                results.append({
                    "id": product.get("id", 0),
                    "name": product["name"],
                    "final_price": product.get("final_price", ""),
                    "price": product.get("price", ""),
                    "stock": product.get("stock", ""),
                    "color": product.get("color", ""),
                    "size": product.get("size", ""),
                    "code": product.get("code", ""),
                    "category": product.get("category", ""),
                    "discount": product.get("discount", ""),
                    "match_score": item["score"]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search products error: {str(e)}")
            return []
    
    async def log_function_call(self, function_name: str, arguments: Dict[str, Any], 
                              session_id: str, business_id: str, execution_time: int,
                              success: bool, error_message: Optional[str] = None) -> bool:
        """
        Function call'ı logla
        
        Args:
            function_name: Fonksiyon adı
            arguments: Fonksiyon parametreleri
            session_id: Session ID
            business_id: İşletme ID
            execution_time: Execution time (ms)
            success: Başarılı mı?
            error_message: Hata mesajı
            
        Returns:
            bool: Loglama başarılı mı?
        """
        try:
            log_entry = {
                "function_name": function_name,
                "arguments": arguments,
                "session_id": session_id,
                "business_id": business_id,
                "execution_time_ms": execution_time,
                "success": success,
                "error_message": error_message,
                "timestamp": time.time()
            }
            
            logger.info(f"Function call logged: {json.dumps(log_entry)}")
            return True
            
        except Exception as e:
            logger.error(f"Function call logging error: {str(e)}")
            return False
    
    async def get_function_call_stats(self, business_id: str, 
                                    time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Function call istatistiklerini getir
        
        Args:
            business_id: İşletme ID
            time_range_hours: Zaman aralığı (saat)
            
        Returns:
            Dict: İstatistikler
        """
        try:
            # Mock implementation - gerçekte veritabanından alınacak
            return {
                "total_calls": 150,
                "successful_calls": 142,
                "failed_calls": 8,
                "success_rate": 0.947,
                "average_execution_time_ms": 245,
                "most_used_functions": [
                    {"function_name": "getProductInfo", "count": 89},
                    {"function_name": "getGeneralInfo", "count": 61}
                ]
            }
            
        except Exception as e:
            logger.error(f"Get function call stats error: {str(e)}")
            return {}
    
    async def health_check(self) -> bool:
        """
        Database health check
        
        Returns:
            bool: Database sağlıklı mı?
        """
        try:
            # Ürün verilerinin yüklenip yüklenmediğini kontrol et
            return len(self.products) > 0
            
        except Exception as e:
            logger.error(f"Database health check error: {str(e)}")
            return False    

    async def get_general_info(self, business_id: str, info_type: str) -> Optional[Dict[str, Any]]:
        """
        İşletme genel bilgilerini getir - Multi-business aware
        
        Args:
            business_id: İşletme ID
            info_type: Bilgi türü (telefon, iade, kargo, site)
            
        Returns:
            Dict: Bilgi veya None
        """
        try:
            # Yeni format'tan business info al
            business_data = self.businesses.get(business_id)
            if business_data:
                business_info = business_data.get('business_info', {})
                contact = business_info.get('contact', {})
                policies = business_info.get('policies', {})
            else:
                # Fallback to legacy format
                business_info = self.business_info.get(business_id, {})
                contact = {'phone': business_info.get('phone', '')}
                policies = {
                    'return_policy': business_info.get('iade_policy', ''),
                    'shipping_info': business_info.get('shipping_info', '')
                }
            
            if info_type == "telefon":
                phone = contact.get("phone", "Telefon bilgisi bulunamadı")
                return {
                    "info_type": "telefon",
                    "content": f"Telefon numaramız: {phone}",
                    "business_id": business_id
                }
            
            elif info_type == "iade":
                iade_policy = policies.get("return_policy", "İade politikası bilgisi bulunamadı")
                return {
                    "info_type": "iade",
                    "content": f"İade politikamız: {iade_policy}",
                    "business_id": business_id
                }
            
            elif info_type == "kargo":
                shipping_info = policies.get("shipping_info", "Kargo bilgisi bulunamadı")
                return {
                    "info_type": "kargo",
                    "content": f"Kargo bilgilerimiz: {shipping_info}",
                    "business_id": business_id
                }
            
            elif info_type == "site":
                site = business_info.get("website", business_info.get("site", "Website bilgisi bulunamadı"))
                return {
                    "info_type": "site",
                    "content": f"Web sitemiz: {site}",
                    "business_id": business_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Get general info error: {str(e)}")
            return None