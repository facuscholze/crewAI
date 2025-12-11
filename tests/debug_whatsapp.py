#!/usr/bin/env python3
"""
Debug script para WhatsApp - verificar formato de números
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_different_formats():
    """Prueba diferentes formatos de número"""
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    if not access_token or not phone_number_id:
        print("❌ Credenciales no configuradas")
        return
    
    # Diferentes formatos del mismo número
    test_numbers = [
        "5493755629953",      # Formato del webhook
        "+5493755629953",     # Con +
        "549 375 562 9953",   # Con espacios
        "549-375-562-9953",   # Con guiones
        "(549) 375-562-9953", # Con paréntesis
    ]
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    for i, number in enumerate(test_numbers, 1):
        print(f"\n🧪 Prueba {i}: {number}")
        
        # Limpiar número
        clean_number = number.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Corregir número argentino: remover 9 extra si está presente
        if clean_number.startswith('549') and len(clean_number) == 13:
            clean_number = '54' + clean_number[3:]  # Remover el 9 extra
            print(f"   Limpio: {number} -> {clean_number} (corregido)")
        else:
            print(f"   Limpio: {clean_number}")
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "text",
            "text": {"body": f"🧪 Prueba formato {i}: {number}"}
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"   ✅ ÉXITO")
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                print(f"   📨 Message ID: {message_id}")
                break  # Si funciona, no necesitamos probar más
            else:
                error_data = response.json() if response.text else {}
                error_code = error_data.get('error', {}).get('code', 'unknown')
                error_message = error_data.get('error', {}).get('message', 'No details')
                print(f"   ❌ Error {response.status_code}: {error_code}")
                print(f"   📄 Mensaje: {error_message}")
                
        except Exception as e:
            print(f"   ❌ Excepción: {str(e)}")

def test_webhook_format():
    """Simula el formato que viene del webhook"""
    
    print("\n🔍 SIMULANDO FORMATO DEL WEBHOOK")
    print("=" * 50)
    
    # Simular datos del webhook
    webhook_data = {
        'object': 'whatsapp_business_account',
        'entry': [{
            'id': '1888652925325892',
            'changes': [{
                'value': {
                    'messaging_product': 'whatsapp',
                    'metadata': {
                        'display_phone_number': '15551649758',
                        'phone_number_id': '870456789473633'
                    },
                    'contacts': [{
                        'profile': {'name': 'Facundo Scholze'},
                        'wa_id': '5493755629953'  # Este es el formato que viene del webhook
                    }],
                    'messages': [{
                        'from': '5493755629953',  # Este es el user_id que extraemos
                        'id': 'test_message_id',
                        'timestamp': '1760468386',
                        'text': {'body': 'Hola'},
                        'type': 'text'
                    }]
                },
                'field': 'messages'
            }]
        }]
    }
    
    # Extraer user_id como lo hace main.py
    entry = webhook_data['entry'][0]
    change = entry['changes'][0]
    messages = change['value']['messages']
    
    for message in messages:
        user_id = message.get('from', 'unknown')
        message_text = message.get('text', {}).get('body', '')
        
        print(f"📱 User ID extraído: {user_id}")
        print(f"📝 Mensaje: {message_text}")
        print(f"🔢 Tipo: {type(user_id)}")
        print(f"📏 Longitud: {len(user_id)}")
        
        # Probar envío con este formato
        print(f"\n🚀 Probando envío con user_id: {user_id}")
        test_single_number(user_id)

def test_single_number(number):
    """Prueba un solo número"""
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    if not access_token or not phone_number_id:
        print("❌ Credenciales no configuradas")
        return
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Limpiar número
    clean_number = number.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Corregir número argentino: remover 9 extra si está presente
    # Formato incorrecto: 5493755629953 (con 9 extra)
    # Formato correcto: 54375629953 (sin 9 extra)
    if clean_number.startswith('549') and len(clean_number) == 13:
        clean_number = '54' + clean_number[3:]  # Remover el 9 extra
        print(f"   🔧 Corregido: {number} -> {clean_number}")
    
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_number,
        "type": "text",
        "text": {"body": f"🧪 Prueba directa con: {number} -> {clean_number}"}
    }
    
    print(f"   📤 Enviando a: {clean_number}")
    print(f"   📦 Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"   📊 Status: {response.status_code}")
        print(f"   📄 Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ ¡ÉXITO!")
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown')
            print(f"   📨 Message ID: {message_id}")
        else:
            error_data = response.json() if response.text else {}
            error_code = error_data.get('error', {}).get('code', 'unknown')
            error_message = error_data.get('error', {}).get('message', 'No details')
            print(f"   ❌ Error {error_code}: {error_message}")
            
    except Exception as e:
        print(f"   ❌ Excepción: {str(e)}")

if __name__ == "__main__":
    print("🔍 DEBUG DE WHATSAPP - FORMATO DE NÚMEROS")
    print("=" * 60)
    
    # Probar formato del webhook primero
    test_webhook_format()
    
    # Probar diferentes formatos
    print("\n" + "=" * 60)
    print("🧪 PROBANDO DIFERENTES FORMATOS")
    print("=" * 60)
    test_different_formats()
