import logging
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

from .runtime_context import current_user_id, current_channel
from ..services import whatsapp as whatsapp_service

logger = logging.getLogger(__name__)


class WhatsAppMessageInput(BaseModel):
    """Input schema for WhatsApp message tool."""
    to: str = Field(..., description="Phone number of the recipient (with country code)")
    message: str = Field(..., description="Text message to send")
    message_type: str = Field(default="text", description="Type of message: text, voice, call")


class WhatsAppTool(BaseTool):
    name: str = "WhatsApp Message Tool"
    description: str = (
        "Send messages, voice messages, or initiate calls through WhatsApp Business API. "
        "Useful for responding to WhatsApp conversations with text, voice, or initiating voice calls."
    )
    args_schema: Type[BaseModel] = WhatsAppMessageInput

    def _run(self, to: str, message: str, message_type: str = "text") -> str:
        """Send WhatsApp message, voice message, or initiate call.

        Only override the destination with context when channel is WhatsApp and the
        context ID looks like a phone. For other channels (instagram, messenger, gmail)
        we keep the provided `to` (e.g., clinic_number) to avoid sending to PSIDs/emails.
        """
        channel = (current_channel() or "whatsapp").lower()

        # Default to the provided destination; only override for WhatsApp with a valid phone-like context ID
        safe_to = to
        if channel == "whatsapp":
            ctx_id = current_user_id()
            if ctx_id:
                normalized_ctx = ctx_id.strip('+').replace('-', '').replace(' ', '')
                if normalized_ctx.isdigit() and 9 <= len(normalized_ctx) <= 15:
                    safe_to = ctx_id

        if message_type == "text":
            result = whatsapp_service.send_text_message(safe_to, message)
        elif message_type == "voice":
            result = whatsapp_service.send_voice_message(safe_to, message)
        else:
            return "Error: Unsupported message type"

        if result["success"]:
            return f"WhatsApp message sent successfully. Message ID: {result['message_id']}"

        error = result.get("error", "unknown error")
        # Surface user-friendly messages for known error codes
        if "131030" in error:
            clean_to = whatsapp_service.normalize_phone(safe_to)
            return (
                f"Error: El número {clean_to} no está en la lista de números permitidos "
                "de WhatsApp Business API (modo desarrollo). Agrega este número en Meta Business Suite."
            )
        if "131026" in error:
            return f"WhatsApp message queued (rate limit - will be sent shortly). Message: {message}"

        return f"Failed to send message: {error}"


class WhatsAppWebhookTool(BaseTool):
    name: str = "WhatsApp Webhook Tool"
    description: str = (
        "Process incoming WhatsApp webhook messages and extract relevant information."
    )
    args_schema: Type[BaseModel] = BaseModel  # No specific input needed for webhook processing

    def _run(self) -> str:
        """Process WhatsApp webhook data."""
        # This would typically be called by the webhook endpoint
        # Implementation would depend on the webhook framework being used
        return "WhatsApp webhook processed successfully"

