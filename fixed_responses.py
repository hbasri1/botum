# Fixed responses with selective WhatsApp support
def get_fixed_responses(business_info, get_whatsapp_func):
    return {
        "greeting": "Merhaba! 👋 Size nasıl yardımcı olabilirim? Ürünlerimiz hakkında bilgi alabilir, fiyat sorabilirsiniz.",
        "thanks": "Rica ederim! 😊 Başka sorunuz var mı?",
        "goodbye": "Görüşmek üzere! İyi günler dilerim. 👋",
        "phone_inquiry": f"📞 Telefon numaramız: {business_info.get('phone', '0212 123 45 67')}",
        "return_policy": f"📋 İade politikamız: 14 gün içinde iade kabul edilir. Ürün kullanılmamış ve etiketli olmalıdır.{get_whatsapp_func('return_policy')}",
        "shipping_info": f"🚚 Kargo bilgileri: Türkiye geneli ücretsiz kargo. 1-3 iş günü içinde teslimat.{get_whatsapp_func('shipping_info')}",
        "website_inquiry": f"🌐 Web sitemiz: {business_info.get('website', 'www.butik.com')}",
        "size_inquiry": f"📏 Beden bilgileri için web sitemizi ziyaret edebilirsiniz: {business_info.get('website', 'www.butik.com')} \n\n📞 Detaylı bilgi için bizi arayabilirsiniz: {business_info.get('phone', '0212 123 45 67')}{get_whatsapp_func('size_inquiry')}",
        "order_request": f"🛒 Sipariş vermek için web sitemizi ziyaret edebilirsiniz: {business_info.get('website', 'www.butik.com')} \n\n📞 Telefon ile sipariş: {business_info.get('phone', '0212 123 45 67')}",
        "order_status": f"📦 Sipariş durumunuz için lütfen bizi arayın: {business_info.get('phone', '0212 123 45 67')} \n\nSipariş numaranızı hazır bulundurun.{get_whatsapp_func('order_status')}",
        "complaint": f"😔 Üzgünüz! Sorununuz için lütfen bizi arayın: {business_info.get('phone', '0212 123 45 67')} \n\nMüşteri hizmetlerimiz size yardımcı olacaktır.{get_whatsapp_func('complaint')}",
        "contact_info": f"📞 Telefon: {business_info.get('phone', '0212 123 45 67')}\n🌐 Web: {business_info.get('website', 'www.butik.com')}\n📧 Email: {business_info.get('email', 'info@butik.com')}",
        "payment_info": f"💳 Ödeme seçenekleri için web sitemizi ziyaret edin: {business_info.get('website', 'www.butik.com')}\n📞 Detaylı bilgi: {business_info.get('phone', '0212 123 45 67')}",
        "address_inquiry": f"📍 Adres bilgileri için lütfen bizi arayın: {business_info.get('phone', '0212 123 45 67')}",
        "stock_inquiry": f"📦 Hangi ürünün stok durumunu öğrenmek istiyorsunuz?\n\n💡 **Örnek:** 'hamile pijama stok' veya ürün adını yazın.\n\n📞 Detaylı bilgi: {business_info.get('phone', '0212 123 45 67')}",
        "price_inquiry": f"💰 Hangi ürünün fiyatını öğrenmek istiyorsunuz?\n\n💡 **Lütfen ürün adını belirtin:**\n• 'Afrika gecelik fiyatı'\n• 'Hamile pijama ne kadar'\n• 'Dantelli sabahlık fiyat'\n\n📞 **Yardım için:** {business_info.get('phone', '0212 123 45 67')}{get_whatsapp_func('price_help')}",
        "negative_response": "Anladım. 😊 Başka bir konuda size yardımcı olabilir miyim?\n\n💡 **Yapabileceklerim:**\n• 🔍 Ürün arama\n• 💰 Fiyat bilgisi\n• 📦 Stok durumu\n• 🏢 Mağaza bilgileri",
        "no_products_found": f"Üzgünüm, aradığınız kriterlere uygun ürün bulamadım. 😔\n\n💡 **Öneriler:**\n• Ürünün tam adını yazın (örn: 'Afrika Etnik Baskılı Gecelik')\n• Farklı renk deneyin\n• Daha genel arama yapın\n\n📞 **Yardım için:** {business_info.get('phone', '0212 123 45 67')}{get_whatsapp_func('product_help')}",
        "image_reference_help": f"📸 Gönderdiğiniz görselle ilgili yardım için:\n\n💡 **Lütfen ürünün adını yazın** veya görseldeki ürünü tarif edin\n\n📞 **Hızlı yardım:** {business_info.get('phone', '0212 123 45 67')}{get_whatsapp_func('image_help')}"
    }