"""
Product Function Handler - getProductInfo function'ı için handler
"""

import logging
from typing import Dict, Any, Optional, List
from orchestrator.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class ProductFunctionHandler:
    """Product function handler sınıfı"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.response_templates = {
            "fiyat": "{product_name} fiyatı {price} TL'dir.",
            "stok": "{product_name} {stock_status}.",
            "detay": "{product_name} detayları: {details}",
            "renk": "{product_name} renk seçenekleri: {colors}",
            "beden": "{product_name} beden seçenekleri: {sizes}"
        }
    
    async def handle_product_query(self, product_name: str, query_type: str, 
                                 business_id: str) -> Dict[str, Any]:
        """
        Product query'sini handle et
        
        Args:
            product_name: Ürün adı
            query_type: Sorgu türü (fiyat, stok, detay, renk, beden, katalog)
            business_id: İşletme ID
            
        Returns:
            Dict: Handler sonucu
        """
        try:
            # Katalog sorguları için özel handling
            if product_name == "katalog" or query_type == "katalog":
                return await self._handle_catalog_query(business_id)
            
            # Ürün adı eksikse clarification iste
            if not product_name or product_name.strip() == "":
                return await self._handle_missing_product_name(query_type, business_id)
            
            # Ürün bilgisini veritabanından al
            product_info = await self.db_service.get_product_info(
                business_id, product_name
            )
            
            if not product_info:
                # Ürün bulunamadı, benzer ürün öner
                return await self._handle_product_not_found(
                    product_name, query_type, business_id
                )
            
            # Query type'a göre response formatla
            return await self._format_product_response(
                product_info, query_type, business_id
            )
            
        except Exception as e:
            logger.error(f"Product query handling error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Ürün bilgisi alınırken bir hata oluştu."
            }
    
    async def _handle_missing_product_name(self, query_type: str, 
                                         business_id: str) -> Dict[str, Any]:
        """
        Ürün adı eksik olduğunda clarification logic
        
        Args:
            query_type: Sorgu türü
            business_id: İşletme ID
            
        Returns:
            Dict: Clarification response
        """
        try:
            # Popüler ürünleri al
            popular_products = await self.db_service.get_popular_products(business_id, limit=5)
            
            if popular_products:
                product_list = ", ".join([p["name"] for p in popular_products])
                
                clarification_messages = {
                    "fiyat": f"Hangi ürünün fiyatını öğrenmek istiyorsunuz? Popüler ürünlerimiz: {product_list}",
                    "stok": f"Hangi ürünün stok durumunu kontrol etmek istiyorsunuz? Mevcut ürünlerimiz: {product_list}",
                    "detay": f"Hangi ürün hakkında detay almak istiyorsunuz? Ürünlerimiz: {product_list}",
                    "renk": f"Hangi ürünün renk seçeneklerini görmek istiyorsunuz? Ürünlerimiz: {product_list}",
                    "beden": f"Hangi ürünün beden seçeneklerini görmek istiyorsunuz? Ürünlerimiz: {product_list}"
                }
                
                response = clarification_messages.get(
                    query_type, 
                    f"Hangi ürün hakkında bilgi almak istiyorsunuz? Ürünlerimiz: {product_list}"
                )
            else:
                response = f"Hangi ürün hakkında {query_type} bilgisi almak istiyorsunuz?"
            
            return {
                "success": True,
                "requires_clarification": True,
                "clarification_type": "missing_product_name",
                "query_type": query_type,
                "response": response,
                "suggested_products": popular_products
            }
            
        except Exception as e:
            logger.error(f"Missing product name handling error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Hangi ürün hakkında {query_type} bilgisi almak istiyorsunuz?"
            }
    
    async def _handle_product_not_found(self, product_name: str, query_type: str, 
                                      business_id: str) -> Dict[str, Any]:
        """
        Ürün bulunamadığında benzer ürün önerme logic
        
        Args:
            product_name: Aranan ürün adı
            query_type: Sorgu türü
            business_id: İşletme ID
            
        Returns:
            Dict: Similar product suggestions
        """
        try:
            # Benzer ürünleri bul
            similar_products = await self.db_service.find_similar_products(
                business_id, product_name, limit=3
            )
            
            if similar_products:
                # Benzer ürünler bulundu
                product_names = [p["name"] for p in similar_products]
                product_list = ", ".join(product_names)
                
                response = (
                    f"'{product_name}' ürünü bulunamadı. "
                    f"Benzer ürünlerimiz: {product_list}. "
                    f"Bunlardan hangisi hakkında {query_type} bilgisi almak istiyorsunuz?"
                )
                
                return {
                    "success": True,
                    "product_not_found": True,
                    "original_product": product_name,
                    "query_type": query_type,
                    "response": response,
                    "similar_products": similar_products
                }
            else:
                # Hiç benzer ürün yok
                all_products = await self.db_service.get_all_products(business_id, limit=5)
                
                if all_products:
                    product_list = ", ".join([p["name"] for p in all_products])
                    response = (
                        f"'{product_name}' ürünü bulunamadı. "
                        f"Mevcut ürünlerimiz: {product_list}"
                    )
                else:
                    response = f"'{product_name}' ürünü bulunamadı ve şu anda başka ürünümüz bulunmamaktadır."
                
                return {
                    "success": True,
                    "product_not_found": True,
                    "original_product": product_name,
                    "query_type": query_type,
                    "response": response,
                    "available_products": all_products
                }
            
        except Exception as e:
            logger.error(f"Product not found handling error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": f"'{product_name}' ürünü bulunamadı."
            }
    
    async def _format_product_response(self, product_info: Dict[str, Any], 
                                     query_type: str, business_id: str) -> Dict[str, Any]:
        """
        Ürün bilgisini query type'a göre formatla
        
        Args:
            product_info: Ürün bilgisi
            query_type: Sorgu türü
            business_id: İşletme ID
            
        Returns:
            Dict: Formatlanmış response
        """
        try:
            product_name = product_info.get("name", "Ürün")
            
            # MVP: Store context for follow-up questions
            try:
                from .simple_semantic_search import semantic_search
                if semantic_search and hasattr(semantic_search, 'store_context'):
                    session_id = business_id  # Simple approach for MVP
                    semantic_search.store_context(session_id, product_name)
            except Exception as e:
                logger.error(f"Context storage error: {str(e)}")
            
            if query_type == "fiyat":
                return await self._format_price_response(product_info)
            elif query_type == "stok":
                return await self._format_stock_response(product_info)
            elif query_type == "detay":
                return await self._format_detail_response(product_info)
            elif query_type == "renk":
                return await self._format_color_response(product_info)
            elif query_type == "beden":
                return await self._format_size_response(product_info)
            else:
                # Genel bilgi
                return await self._format_general_response(product_info)
            
        except Exception as e:
            logger.error(f"Product response formatting error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Ürün bilgisi formatlanırken hata oluştu."
            }
    
    async def _format_price_response(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fiyat response'unu formatla"""
        product_name = product_info.get("name", "Ürün")
        price = product_info.get("price")
        original_price = product_info.get("original_price")
        discount_percentage = product_info.get("discount_percentage")
        
        if price is None:
            return {
                "success": True,
                "query_type": "fiyat",
                "product_name": product_name,
                "response": f"{product_name} için fiyat bilgisi şu anda mevcut değil."
            }
        
        # Fiyat formatla
        price_text = f"{price:.2f} TL"
        
        # İndirim varsa belirt
        if original_price and original_price > price:
            discount_text = f" (İndirimli fiyat! Eski fiyat: {original_price:.2f} TL"
            if discount_percentage:
                discount_text += f", %{discount_percentage:.0f} indirim"
            discount_text += ")"
            price_text += discount_text
        
        response = f"{product_name} fiyatı {price_text}"
        
        return {
            "success": True,
            "query_type": "fiyat",
            "product_name": product_name,
            "price": price,
            "original_price": original_price,
            "discount_percentage": discount_percentage,
            "response": response
        }
    
    async def _format_stock_response(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Stok response'unu formatla"""
        product_name = product_info.get("name", "Ürün")
        stock_quantity = product_info.get("stock_quantity", 0)
        
        if stock_quantity > 10:
            stock_status = "stokta mevcut"
        elif stock_quantity > 0:
            stock_status = f"stokta mevcut (son {stock_quantity} adet)"
        else:
            stock_status = "stokta yok"
        
        response = f"{product_name} {stock_status}."
        
        return {
            "success": True,
            "query_type": "stok",
            "product_name": product_name,
            "stock_quantity": stock_quantity,
            "stock_status": stock_status,
            "response": response
        }
    
    async def _format_detail_response(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detay response'unu formatla"""
        product_name = product_info.get("name", "Ürün")
        description = product_info.get("description", "")
        category = product_info.get("category", "")
        material = product_info.get("material", "")
        attributes = product_info.get("attributes", {})
        
        details = []
        
        if description:
            details.append(description)
        
        if category:
            details.append(f"Kategori: {category}")
        
        if material:
            details.append(f"Malzeme: {material}")
        
        # Attributes'tan ek bilgiler
        if attributes:
            for key, value in attributes.items():
                if value:
                    details.append(f"{key.capitalize()}: {value}")
        
        if details:
            details_text = ". ".join(details)
            response = f"{product_name} detayları: {details_text}."
        else:
            response = f"{product_name} için detaylı bilgi şu anda mevcut değil."
        
        return {
            "success": True,
            "query_type": "detay",
            "product_name": product_name,
            "description": description,
            "category": category,
            "material": material,
            "attributes": attributes,
            "response": response
        }
    
    async def _format_color_response(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Renk response'unu formatla"""
        product_name = product_info.get("name", "Ürün")
        color = product_info.get("color", "")
        attributes = product_info.get("attributes", {})
        
        # Renk bilgisini topla
        colors = []
        if color:
            colors.append(color)
        
        # Attributes'tan renk bilgisi
        if attributes.get("colors"):
            colors.extend(attributes["colors"])
        elif attributes.get("available_colors"):
            colors.extend(attributes["available_colors"])
        
        if colors:
            # Tekrarları kaldır
            unique_colors = list(set(colors))
            colors_text = ", ".join(unique_colors)
            response = f"{product_name} renk seçenekleri: {colors_text}"
        else:
            response = f"{product_name} için renk bilgisi şu anda mevcut değil."
        
        return {
            "success": True,
            "query_type": "renk",
            "product_name": product_name,
            "colors": colors,
            "response": response
        }
    
    async def _format_size_response(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Beden response'unu formatla"""
        product_name = product_info.get("name", "Ürün")
        size = product_info.get("size", "")
        attributes = product_info.get("attributes", {})
        
        # Beden bilgisini topla
        sizes = []
        if size:
            sizes.append(size)
        
        # Attributes'tan beden bilgisi
        if attributes.get("sizes"):
            sizes.extend(attributes["sizes"])
        elif attributes.get("available_sizes"):
            sizes.extend(attributes["available_sizes"])
        
        if sizes:
            # Tekrarları kaldır
            unique_sizes = list(set(sizes))
            sizes_text = ", ".join(unique_sizes)
            response = f"{product_name} beden seçenekleri: {sizes_text}"
        else:
            response = f"{product_name} için beden bilgisi şu anda mevcut değil."
        
        return {
            "success": True,
            "query_type": "beden",
            "product_name": product_name,
            "sizes": sizes,
            "response": response
        }
    
    async def _format_general_response(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Genel ürün bilgisi response'unu formatla"""
        product_name = product_info.get("name", "Ürün")
        price = product_info.get("price")
        stock_quantity = product_info.get("stock_quantity", 0)
        description = product_info.get("description", "")
        
        response_parts = [f"{product_name} hakkında:"]
        
        if description:
            response_parts.append(description)
        
        if price:
            response_parts.append(f"Fiyat: {price:.2f} TL")
        
        if stock_quantity > 0:
            response_parts.append("Stokta mevcut")
        else:
            response_parts.append("Stokta yok")
        
        response = ". ".join(response_parts) + "."
        
        return {
            "success": True,
            "query_type": "genel",
            "product_name": product_name,
            "product_info": product_info,
            "response": response
        }
    
    async def _handle_catalog_query(self, business_id: str) -> Dict[str, Any]:
        """Katalog sorgularını handle et"""
        try:
            # Popüler ürünleri al
            popular_products = await self.db_service.get_popular_products(business_id, limit=10)
            
            if not popular_products:
                return {
                    "success": True,
                    "response": "Şu anda ürün bilgisi mevcut değil."
                }
            
            # Kategorilere göre grupla
            categories = {}
            for product in popular_products:
                category = "Genel"
                name = product["name"].lower()
                
                if "gecelik" in name:
                    category = "Gecelikler"
                elif "pijama" in name:
                    category = "Pijamalar"
                elif "sabahlık" in name:
                    category = "Sabahlıklar"
                elif "elbise" in name:
                    category = "Elbiseler"
                
                if category not in categories:
                    categories[category] = []
                categories[category].append(product)
            
            # Response oluştur
            response = "Mevcut ürünlerimiz:\n\n"
            
            for category, products in categories.items():
                response += f"🔸 {category}:\n"
                for product in products[:3]:  # Her kategoriden max 3 ürün
                    response += f"  • {product['name']}\n"
                    response += f"    Fiyat: {product.get('price', 'Bilgi yok')} TL\n"
                response += "\n"
            
            response += "Detaylı bilgi için ürün adını sorabilirsiniz.\nTelefon: 0555 555 55 55"
            
            return {
                "success": True,
                "response": response,
                "catalog_products": popular_products
            }
            
        except Exception as e:
            logger.error(f"Catalog query handling error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Katalog bilgisi alınırken hata oluştu."
            }    

    async def handle_general_info_query(self, info_type: str, business_id: str) -> Dict[str, Any]:
        """
        General info query'sini handle et
        
        Args:
            info_type: Bilgi türü (telefon, iade, kargo, site)
            business_id: İşletme ID
            
        Returns:
            Dict: Handler sonucu
        """
        try:
            # Database service'ten bilgiyi al
            info_result = await self.db_service.get_general_info(business_id, info_type)
            
            if info_result:
                return {
                    "success": True,
                    "response": info_result["content"],
                    "info_type": info_result["info_type"],
                    "business_id": info_result["business_id"]
                }
            else:
                return {
                    "success": False,
                    "error": f"'{info_type}' bilgisi bulunamadı",
                    "response": f"Üzgünüm, {info_type} bilgisi şu anda mevcut değil. Lütfen daha sonra tekrar deneyin."
                }
                
        except Exception as e:
            logger.error(f"General info query error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Bilgi alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            }