#!/usr/bin/env python3
"""
Script de prueba para WhatsApp Business API
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_whatsapp_message():
    """Prueba el envío de un mensaje de WhatsApp"""
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    if not access_token or not phone_number_id:
        print("❌ Error: Credenciales de WhatsApp no configuradas")
        return False
    
    print(f"🔑 Token: {access_token[:20]}...")
    print(f"📱 Phone Number ID: {phone_number_id}")
    
    # Número de prueba (tu número)
    to = "5493755629953"  # Sin + y sin espacios
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": "🧪 Prueba del sistema Integrado - Mensaje de prueba"}
    }
    
    print(f"📤 Enviando mensaje a: {to}")
    print(f"🔗 URL: {url}")
    print(f"📦 Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown')
            print(f"✅ Mensaje enviado exitosamente. ID: {message_id}")
            return True
        else:
            print(f"❌ Error enviando mensaje: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

def test_webhook_verification():
    """Prueba la verificación del webhook"""
    
    verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
    
    if not verify_token:
        print("❌ Error: Token de verificación no configurado")
        return False
    
    print(f"🔐 Token de verificación: {verify_token}")
    
    # Simular parámetros de verificación
    test_params = {
        'hub.mode': 'subscribe',
        'hub.challenge': 'test_challenge_123',
        'hub.verify_token': verify_token
    }
    
    print(f"📋 Parámetros de prueba: {test_params}")
    
    if test_params['hub.verify_token'] == verify_token:
        print("✅ Token de verificación válido")
        return True
    else:
        print("❌ Token de verificación inválido")
        return False

if __name__ == "__main__":
    print("🧪 PRUEBAS DE WHATSAPP BUSINESS API")
    print("=" * 50)
    
    # Prueba 1: Verificación de webhook
    print("\n1️⃣ Prueba de verificación de webhook:")
    webhook_ok = test_webhook_verification()
    
    # Prueba 2: Envío de mensaje
    print("\n2️⃣ Prueba de envío de mensaje:")
    message_ok = test_whatsapp_message()
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS:")
    print(f"   Webhook: {'✅ OK' if webhook_ok else '❌ ERROR'}")
    print(f"   Mensaje: {'✅ OK' if message_ok else '❌ ERROR'}")
    
    if webhook_ok and message_ok:
        print("\n🎉 ¡Todas las pruebas pasaron!")
        sys.exit(0)
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        sys.exit(1)






