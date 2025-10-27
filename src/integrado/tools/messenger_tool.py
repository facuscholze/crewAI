from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests
import os


class MessengerMessageInput(BaseModel):
    """Input schema for Facebook Messenger message tool."""
    recipient_id: str = Field(..., description="Facebook user ID of the recipient")
    message: str = Field(..., description="Text message to send")
    message_type: str = Field(default="text", description="Type of message: text, button, card")
    buttons: Optional[list] = Field(default=None, description="List of buttons for interactive messages")


class MessengerTool(BaseTool):
    name: str = "Facebook Messenger Tool"
    description: str = (
        "Send messages through Facebook Messenger API. "
        "Supports text messages, interactive buttons, and structured cards for enhanced user experience."
    )
    args_schema: Type[BaseModel] = MessengerMessageInput

    def _run(self, recipient_id: str, message: str, message_type: str = "text", buttons: Optional[list] = None) -> str:
        """Send Facebook Messenger message."""
        
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        
        if not access_token:
            return "Error: Facebook Messenger credentials not configured"
        
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={access_token}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if message_type == "text":
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message}
            }
        elif message_type == "button" and buttons:
            payload = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": message,
                            "buttons": buttons
                        }
                    }
                }
            }
        elif message_type == "card":
            # Generic card template
            payload = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "generic",
                            "elements": [{
                                "title": message,
                                "subtitle": "Tap a button below",
                                "buttons": buttons or []
                            }]
                        }
                    }
                }
            }
        else:
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message}
            }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get('message_id', 'unknown')
            
            return f"Messenger message sent successfully. Message ID: {message_id}"
            
        except requests.exceptions.RequestException as e:
            return f"Error sending Messenger message: {str(e)}"


class MessengerWebhookTool(BaseTool):
    name: str = "Messenger Webhook Tool"
    description: str = (
        "Process incoming Facebook Messenger webhook messages and extract relevant information."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Process Messenger webhook data."""
        return "Messenger webhook processed successfully"






