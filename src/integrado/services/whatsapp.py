"""
WhatsApp Business API service.
Pure HTTP functions – no CrewAI / BaseTool dependencies.
"""
import logging
import requests
from .. import config

logger = logging.getLogger(__name__)


def send_text_message(to: str, message: str) -> dict:
    """
    Send a WhatsApp text message.

    Returns a dict with keys:
      - success (bool)
      - message_id (str | None)
      - error (str | None)
    """
    if not config.WHATSAPP_ACCESS_TOKEN or not config.WHATSAPP_PHONE_NUMBER_ID:
        return {"success": False, "message_id": None, "error": "WhatsApp credentials not configured"}

    clean_to = normalize_phone(to)
    url = f"https://graph.facebook.com/v23.0/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_to,
        "type": "text",
        "text": {"body": message},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json() if response.content else {}

        if response.status_code == 200:
            if "error" in response_data:
                error_code = response_data["error"].get("code", "unknown")
                error_message = response_data["error"].get("message", "unknown")
                logger.warning(f"WhatsApp API error {error_code} for {clean_to}: {error_message}")
                return {"success": False, "message_id": None, "error": f"Error {error_code}: {error_message}"}

            message_id = response_data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"WhatsApp message sent to {clean_to}. Message ID: {message_id}")
            return {"success": True, "message_id": message_id, "error": None}
        else:
            error_code = response_data.get("error", {}).get("code", "unknown")
            error_message = response_data.get("error", {}).get("message", response.text)
            logger.error(f"WhatsApp API HTTP {response.status_code} for {clean_to}: {error_message}")
            return {"success": False, "message_id": None, "error": f"HTTP {response.status_code}: Error {error_code}: {error_message}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp request exception for {clean_to}: {str(e)}", exc_info=True)
        return {"success": False, "message_id": None, "error": str(e)}


def send_voice_message(to: str, audio_url: str) -> dict:
    """
    Send a WhatsApp voice/audio message by URL.

    Returns a dict with keys:
      - success (bool)
      - message_id (str | None)
      - error (str | None)
    """
    if not config.WHATSAPP_ACCESS_TOKEN or not config.WHATSAPP_PHONE_NUMBER_ID:
        return {"success": False, "message_id": None, "error": "WhatsApp credentials not configured"}

    clean_to = normalize_phone(to)
    url = f"https://graph.facebook.com/v23.0/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_to,
        "type": "audio",
        "audio": {"link": audio_url},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json() if response.content else {}

        if response.status_code == 200 and "error" not in response_data:
            message_id = response_data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"WhatsApp voice message sent to {clean_to}. Message ID: {message_id}")
            return {"success": True, "message_id": message_id, "error": None}

        error_code = response_data.get("error", {}).get("code", "unknown")
        error_message = response_data.get("error", {}).get("message", response.text)
        logger.error(f"WhatsApp voice API error for {clean_to}: {error_message}")
        return {"success": False, "message_id": None, "error": f"Error {error_code}: {error_message}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp voice request exception for {clean_to}: {str(e)}", exc_info=True)
        return {"success": False, "message_id": None, "error": str(e)}


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number:
    - Strip non-digit characters (except leading + which is removed too)
    - Fix Argentine numbers with extra 9 (5493... -> 543...)
    """
    clean = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Fix Argentine number: remove extra 9 after country code 54
    if clean.startswith("549") and len(clean) == 13:
        clean = "54" + clean[3:]

    # Specific correction for known mis-formatted number
    if clean == "54375629953":
        clean = "543755629953"

    return clean
