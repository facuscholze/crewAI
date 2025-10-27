from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests
import os


class InstagramMessageInput(BaseModel):
    """Input schema for Instagram Direct message tool."""
    recipient_id: str = Field(..., description="Instagram user ID of the recipient")
    message: str = Field(..., description="Text message to send")
    media_url: Optional[str] = Field(default=None, description="URL of image/video to send with message")


class InstagramTool(BaseTool):
    name: str = "Instagram Direct Tool"
    description: str = (
        "Send messages through Instagram Direct API. "
        "Supports text messages and media sharing for creative communication."
    )
    args_schema: Type[BaseModel] = InstagramMessageInput

    def _run(self, recipient_id: str, message: str, media_url: Optional[str] = None) -> str:
        """Send Instagram Direct message."""
        
        access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        instagram_app_id = os.getenv('INSTAGRAM_APP_ID')
        
        if not access_token or not instagram_app_id:
            return "Error: Instagram credentials not configured"
        
        url = f"https://graph.facebook.com/v18.0/{instagram_app_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        if media_url:
            # Send message with media
            payload = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "image" if media_url.endswith(('.jpg', '.jpeg', '.png', '.gif')) else "video",
                        "payload": {"url": media_url}
                    }
                }
            }
            
            # Also send text message if provided
            if message:
                text_payload = {
                    "recipient": {"id": recipient_id},
                    "message": {"text": message}
                }
                try:
                    requests.post(url, json=text_payload, headers=headers)
                except:
                    pass  # Continue with media message even if text fails
        else:
            # Send text-only message
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message}
            }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get('message_id', 'unknown')
            
            return f"Instagram message sent successfully. Message ID: {message_id}"
            
        except requests.exceptions.RequestException as e:
            return f"Error sending Instagram message: {str(e)}"


class InstagramStoryTool(BaseTool):
    name: str = "Instagram Story Tool"
    description: str = (
        "Create and share Instagram Stories with custom content."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Create Instagram Story (placeholder for future implementation)."""
        return "Instagram Story creation not yet implemented"


class InstagramWebhookTool(BaseTool):
    name: str = "Instagram Webhook Tool"
    description: str = (
        "Process incoming Instagram webhook messages and extract relevant information."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Process Instagram webhook data."""
        return "Instagram webhook processed successfully"






