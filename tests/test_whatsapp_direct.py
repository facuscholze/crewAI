#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test directo de WhatsApp para verificar el envío a un número específico
"""

import os
import sys
import io
import requests
from pathlib import Path
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()


def test_whatsapp_direct(number: str):
    """Test directo de envío de WhatsApp"""
    
    print("TEST DIRECTO DE WHATSAPP")
    print("=" * 60)
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    if not access_token or not phone_number_id:
        print("ERROR: WhatsApp credentials not configured")
        return False
    
    print(f"\nPhone Number ID: {phone_number_id}")
    print(f"Numero destino: {number}")
    
    # Limpiar número
    clean_to = number.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    print(f"Numero limpio: {clean_to}")
    
    url = f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_to,
        "type": "text",
        "text": {"body": f"Test directo de WhatsApp al numero {clean_to}"}
    }
    
    print(f"\nEnviando mensaje...")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json() if response.content else {}
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response_data}")
        print("\n" + "=" * 60)
        
        if response.status_code == 200:
            if 'error' in response_data:
                error_code = response_data['error'].get('code', 'unknown')
                error_message = response_data['error'].get('message', 'unknown')
                error_subcode = response_data['error'].get('error_subcode', '')
                
                print(f"\nERROR EN RESPUESTA:")
                print(f"   Codigo: {error_code}")
                print(f"   Subcodigo: {error_subcode}")
                print(f"   Mensaje: {error_message}")
                
                if error_code == 131030 or error_subcode == 131030:
                    print(f"\n⚠️ PROBLEMA DETECTADO:")
                    print(f"   El numero {clean_to} NO esta en la lista permitida")
                    print(f"   SOLUCION: Agrega este numero en Meta Business Suite")
                    print(f"   Ruta: WhatsApp > Configuracion > Numeros permitidos")
                    return False
                else:
                    print(f"\n❌ Error desconocido: {error_code}")
                    return False
            else:
                message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                contacts = response_data.get('contacts', [])
                wa_id = contacts[0].get('wa_id', 'unknown') if contacts else 'unknown'
                
                print(f"\n✅ MENSAJE ACEPTADO POR WHATSAPP API")
                print(f"   Message ID: {message_id}")
                print(f"   Numero enviado: {clean_to}")
                print(f"   WA ID detectado: {wa_id}")
                
                if clean_to != wa_id:
                    print(f"\n⚠️ DIFERENCIA DETECTADA:")
                    print(f"   Numero enviado: {clean_to}")
                    print(f"   WA ID de WhatsApp: {wa_id}")
                    print(f"   Esto puede indicar que WhatsApp normalizo el numero")
                
                print(f"\nNOTA: Si no recibiste el mensaje, verifica:")
                print(f"   1. Que el numero {wa_id} (o {clean_to}) este en la lista permitida")
                print(f"   2. Que el numero {wa_id} tenga WhatsApp activo y registrado")
                print(f"   3. Que no tengas el numero bloqueado")
                print(f"   4. Revisa el estado del mensaje en Meta Business Suite")
                print(f"      usando el Message ID: {message_id}")
                return True
        else:
            error_code = response_data.get('error', {}).get('code', 'unknown')
            error_message = response_data.get('error', {}).get('message', 'unknown')
            error_subcode = response_data.get('error', {}).get('error_subcode', '')
            
            print(f"\n❌ ERROR AL ENVIAR:")
            print(f"   Status: {response.status_code}")
            print(f"   Codigo: {error_code}")
            print(f"   Subcodigo: {error_subcode}")
            print(f"   Mensaje: {error_message}")
            
            if error_code == 131030 or error_subcode == 131030:
                print(f"\n⚠️ PROBLEMA DETECTADO:")
                print(f"   El numero {clean_to} NO esta en la lista permitida")
                print(f"   SOLUCION: Agrega este numero en Meta Business Suite")
                return False
            
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPCION:")
        print(f"   {str(e)}")
        return False


if __name__ == "__main__":
    # Probar ambos números
    print("\n" + "=" * 60)
    print("PROBANDO NUMERO 1: 543755629953 (que funciona)")
    print("=" * 60)
    result1 = test_whatsapp_direct("543755629953")
    
    print("\n\n" + "=" * 60)
    print("PROBANDO NUMERO 2: 543755585557 (que no funciona)")
    print("=" * 60)
    result2 = test_whatsapp_direct("543755585557")
    
    print("\n\n" + "=" * 60)
    print("RESUMEN:")
    print(f"   Numero 543755629953: {'✅ OK' if result1 else '❌ FALLO'}")
    print(f"   Numero 543755585557: {'✅ OK' if result2 else '❌ FALLO'}")
    print("=" * 60)
    
    sys.exit(0 if (result1 and result2) else 1)

