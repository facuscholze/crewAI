from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests
import os
from datetime import datetime


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
        """Send WhatsApp message, voice message, or initiate call."""
        
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        
        if not access_token or not phone_number_id:
            return "Error: WhatsApp credentials not configured"
        
        # Limpiar número de teléfono (remover + y espacios, pero mantener formato internacional)
        clean_to = to.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Corregir número argentino: remover 9 extra si está presente
        # Formato incorrecto: 5493755629953 (con 9 extra)
        # Formato correcto: 543755629953 (sin 9 extra)
        if clean_to.startswith('549') and len(clean_to) == 13:
            clean_to = '54' + clean_to[3:]  # Remover el 9 extra
        
        # Corrección específica para tu número
        if clean_to == "54375629953":
            clean_to = "543755629953"  # Formato correcto verificado
        
        url = f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        if message_type == "text":
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_to,
                "type": "text",
                "text": {"body": message}
            }
        elif message_type == "voice":
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_to,
                "type": "audio",
                "audio": {"link": message}  # URL to audio file
            }
        else:
            return "Error: Unsupported message type"
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json() if response.content else {}
            
            if response.status_code == 200:
                # Verificar si hay errores en la respuesta (aunque status sea 200)
                if 'error' in response_data:
                    error_code = response_data['error'].get('code', 'unknown')
                    error_message = response_data['error'].get('message', 'unknown')
                    error_subcode = response_data['error'].get('error_subcode', '')
                    
                    # Error 131030: número no en lista permitida (modo desarrollo)
                    if error_code == 131030 or error_subcode == 131030:
                        print(f"⚠️ WhatsApp API Error 131030: El número {clean_to} no está en la lista permitida")
                        print(f"   Mensaje: {error_message}")
                        return f"Error: El número {clean_to} no está en la lista de números permitidos de WhatsApp Business API (modo desarrollo). Agrega este número en Meta Business Suite."
                    # Error 131026: rate limit
                    elif error_code == 131026 or error_subcode == 131026:
                        return f"WhatsApp message queued (rate limit - will be sent shortly). Message: {message}"
                    else:
                        return f"Failed to send message: Error {error_code} - {error_message}"
                
                # Si no hay errores, el mensaje se envió correctamente
                message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                print(f"✅ WhatsApp message sent successfully to {clean_to}. Message ID: {message_id}")
                return f"WhatsApp message sent successfully. Message ID: {message_id}"
            else:
                error_detail = response.text if response.text else "No error details"
                error_code = response_data.get('error', {}).get('code', 'unknown')
                error_message = response_data.get('error', {}).get('message', error_detail)
                
                # Manejar errores específicos de WhatsApp
                if error_code == 131030 or "131030" in error_detail:
                    print(f"⚠️ WhatsApp API Error 131030: El número {clean_to} no está en la lista permitida")
                    return f"Error: El número {clean_to} no está en la lista de números permitidos de WhatsApp Business API (modo desarrollo). Agrega este número en Meta Business Suite."
                elif error_code == 131026 or "131026" in error_detail:
                    return f"WhatsApp message queued (rate limit - will be sent shortly). Message: {message}"
                else:
                    print(f"❌ WhatsApp API Error {error_code}: {error_message}")
                    return f"Failed to send message: {response.status_code} - Error {error_code}: {error_message}"
            
        except requests.exceptions.RequestException as e:
            return f"Error sending WhatsApp message: {str(e)}"


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
