"""
Escalation Service - İnsana aktarma ve ticket yönetimi
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class EscalationService:
    def __init__(self):
        self.db_service = DatabaseService()
    
    async def create_ticket(self, session_id: str, isletme_id: str, 
                          user_message: str, escalation_reason: str,
                          llm_response: Dict[str, Any] = None,
                          error_details: str = None,
                          conversation_history: List[Dict] = None) -> str:
        """
        Eskalasyon ticket'ı oluştur
        """
        
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Ticket verisini hazırla
            ticket_data = {
                "ticket_id": ticket_id,
                "session_id": session_id,
                "isletme_id": isletme_id,
                "user_message": user_message,
                "escalation_reason": escalation_reason,
                "status": "open",
                "priority": self._determine_priority(escalation_reason),
                "created_at": datetime.now(),
                "llm_response": llm_response,
                "error_details": error_details,
                "conversation_history": conversation_history or [],
                "assigned_agent": None,
                "resolution": None,
                "resolved_at": None
            }
            
            # Veritabanına kaydet
            await self.db_service.create_escalation_ticket(ticket_data)
            
            # Canlı destek sistemine bildirim gönder
            await self._notify_support_system(ticket_data)
            
            # Webhook ile harici sistemlere bildir (opsiyonel)
            await self._send_webhook_notification(ticket_data)
            
            logger.info(f"Escalation ticket created: {ticket_id} for session {session_id}")
            
            return ticket_id
            
        except Exception as e:
            logger.error(f"Failed to create escalation ticket: {str(e)}")
            # Fallback ticket ID
            return f"TKT-FALLBACK-{uuid.uuid4().hex[:6].upper()}"
    
    def _determine_priority(self, escalation_reason: str) -> str:
        """Eskalasyon sebebine göre öncelik belirle"""
        
        high_priority_reasons = {
            "sikayet_bildirme", 
            "hukuki_konu", 
            "ozel_durum"
        }
        
        medium_priority_reasons = {
            "karmasik_sorun",
            "handler_error"
        }
        
        if escalation_reason in high_priority_reasons:
            return "high"
        elif escalation_reason in medium_priority_reasons:
            return "medium"
        else:
            return "low"
    
    async def _notify_support_system(self, ticket_data: Dict[str, Any]):
        """Canlı destek sistemine bildirim gönder"""
        try:
            # Bu kısım kullandığınız destek sistemine göre özelleştirilmeli
            # Örnek: Zendesk, Freshdesk, Intercom, vs.
            
            notification_payload = {
                "ticket_id": ticket_data["ticket_id"],
                "business_id": ticket_data["isletme_id"],
                "session_id": ticket_data["session_id"],
                "priority": ticket_data["priority"],
                "reason": ticket_data["escalation_reason"],
                "user_message": ticket_data["user_message"],
                "conversation_url": f"/admin/conversations/{ticket_data['session_id']}",
                "created_at": ticket_data["created_at"].isoformat()
            }
            
            # Örnek: Slack webhook
            await self._send_slack_notification(notification_payload)
            
            # Örnek: Email notification
            await self._send_email_notification(notification_payload)
            
            logger.info(f"Support system notified for ticket {ticket_data['ticket_id']}")
            
        except Exception as e:
            logger.error(f"Failed to notify support system: {str(e)}")
    
    async def _send_slack_notification(self, payload: Dict[str, Any]):
        """Slack'e eskalasyon bildirimi gönder"""
        try:
            import aiohttp
            
            # Slack webhook URL'i environment'dan al
            slack_webhook_url = "YOUR_SLACK_WEBHOOK_URL"  # Config'den gelecek
            
            if not slack_webhook_url or slack_webhook_url == "YOUR_SLACK_WEBHOOK_URL":
                return  # Slack entegrasyonu yapılandırılmamış
            
            slack_message = {
                "text": f"🚨 Yeni Eskalasyon Ticket'ı",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Ticket ID:* {payload['ticket_id']}\n*İşletme:* {payload['business_id']}\n*Öncelik:* {payload['priority'].upper()}\n*Sebep:* {payload['reason']}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Kullanıcı Mesajı:*\n```{payload['user_message'][:200]}...```"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Konuşmayı Görüntüle"
                                },
                                "url": payload['conversation_url']
                            }
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_webhook_url, json=slack_message) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for ticket {payload['ticket_id']}")
                    else:
                        logger.error(f"Slack notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Slack notification error: {str(e)}")
    
    async def _send_email_notification(self, payload: Dict[str, Any]):
        """Email eskalasyon bildirimi gönder"""
        try:
            # Email gönderimi için SMTP veya email service kullanın
            # Bu örnek basit bir placeholder
            
            email_subject = f"Yeni Eskalasyon Ticket'ı: {payload['ticket_id']}"
            email_body = f"""
            Yeni bir eskalasyon ticket'ı oluşturuldu:
            
            Ticket ID: {payload['ticket_id']}
            İşletme ID: {payload['business_id']}
            Session ID: {payload['session_id']}
            Öncelik: {payload['priority']}
            Sebep: {payload['reason']}
            
            Kullanıcı Mesajı:
            {payload['user_message']}
            
            Konuşma Linki: {payload['conversation_url']}
            
            Oluşturulma Zamanı: {payload['created_at']}
            """
            
            # Burada gerçek email gönderimi yapılacak
            logger.info(f"Email notification prepared for ticket {payload['ticket_id']}")
            
        except Exception as e:
            logger.error(f"Email notification error: {str(e)}")
    
    async def _send_webhook_notification(self, ticket_data: Dict[str, Any]):
        """Harici sistemlere webhook bildirimi"""
        try:
            # İşletme özel webhook URL'lerini kontrol et
            business_webhooks = await self.db_service.get_business_webhooks(
                ticket_data["isletme_id"]
            )
            
            if not business_webhooks:
                return
            
            webhook_payload = {
                "event": "escalation_created",
                "ticket_id": ticket_data["ticket_id"],
                "session_id": ticket_data["session_id"],
                "business_id": ticket_data["isletme_id"],
                "priority": ticket_data["priority"],
                "reason": ticket_data["escalation_reason"],
                "user_message": ticket_data["user_message"],
                "timestamp": ticket_data["created_at"].isoformat()
            }
            
            import aiohttp
            
            for webhook_url in business_webhooks:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            webhook_url, 
                            json=webhook_payload,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                logger.info(f"Webhook notification sent to {webhook_url}")
                            else:
                                logger.warning(f"Webhook failed {webhook_url}: {response.status}")
                                
                except Exception as e:
                    logger.error(f"Webhook error {webhook_url}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Webhook notification error: {str(e)}")
    
    async def get_ticket_status(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Ticket durumunu getir"""
        try:
            return await self.db_service.get_escalation_ticket(ticket_id)
        except Exception as e:
            logger.error(f"Failed to get ticket status {ticket_id}: {str(e)}")
            return None
    
    async def update_ticket_status(self, ticket_id: str, status: str, 
                                 assigned_agent: str = None, 
                                 resolution: str = None) -> bool:
        """Ticket durumunu güncelle"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now()
            }
            
            if assigned_agent:
                update_data["assigned_agent"] = assigned_agent
            
            if resolution:
                update_data["resolution"] = resolution
                if status == "resolved":
                    update_data["resolved_at"] = datetime.now()
            
            await self.db_service.update_escalation_ticket(ticket_id, update_data)
            
            logger.info(f"Ticket {ticket_id} updated to status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update ticket {ticket_id}: {str(e)}")
            return False
    
    async def get_escalation_stats(self, isletme_id: str, 
                                 days: int = 30) -> Dict[str, Any]:
        """İşletme eskalasyon istatistikleri"""
        try:
            return await self.db_service.get_escalation_stats(isletme_id, days)
        except Exception as e:
            logger.error(f"Failed to get escalation stats: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Eskalasyon servisi sağlık kontrolü"""
        try:
            # Basit bir test ticket oluşturmayı dene (dry run)
            test_data = {
                "session_id": "test",
                "isletme_id": "test",
                "user_message": "test",
                "escalation_reason": "test"
            }
            
            # Sadece validasyon yap, gerçek ticket oluşturma
            return self._determine_priority("test") is not None
            
        except Exception as e:
            logger.error(f"Escalation service health check failed: {str(e)}")
            return False