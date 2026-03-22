import httpx
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.config import settings


class WhatsAppService:
    """WhatsApp Cloud API integration service."""

    def __init__(self):
        self.api_url = settings.whatsapp_api_url
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        to: str,
        message: str,
    ) -> Dict[str, Any]:
        """Send a text message to a WhatsApp number."""
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        to_number = to.replace("+", "").replace(" ", "").replace("-", "")

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            return response.json()

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Send a template message (for sending outside 24h window)."""
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        to_number = to.replace("+", "").replace(" ", "").replace("-", "")

        template = {
            "name": template_name,
            "language": {
                "code": language_code,
            },
        }

        if components:
            template["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "template",
            "template": template,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            return response.json()

    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an image message."""
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        to_number = to.replace("+", "").replace(" ", "").replace("-", "")

        image_data = {"link": image_url}
        if caption:
            image_data["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "image",
            "image": image_data,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            return response.json()

    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a document (PDF, brochure, etc.)."""
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        to_number = to.replace("+", "").replace(" ", "").replace("-", "")

        document_data = {
            "link": document_url,
            "filename": filename,
        }
        if caption:
            document_data["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "document",
            "document": document_data,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            return response.json()

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read."""
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            return response.json()

    def parse_webhook_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse incoming webhook message from WhatsApp."""
        try:
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            if "messages" not in value:
                return None

            message = value["messages"][0]
            contact = value.get("contacts", [{}])[0]

            return {
                "message_id": message.get("id"),
                "from": message.get("from"),
                "contact_name": contact.get("profile", {}).get("name"),
                "timestamp": message.get("timestamp"),
                "type": message.get("type"),
                "text": message.get("text", {}).get("body") if message.get("type") == "text" else None,
            }
        except (IndexError, KeyError):
            return None


whatsapp_service = WhatsAppService()
