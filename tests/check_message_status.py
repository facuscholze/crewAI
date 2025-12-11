#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado de un mensaje de WhatsApp usando el Message ID
"""

import os
import sys
import io
import requests
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()


def check_message_status(message_id: str):
    """Verificar el estado de un mensaje de WhatsApp"""
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    if not access_token or not phone_number_id:
        print("ERROR: WhatsApp credentials not configured")
        return
    
    print(f"Verificando estado del mensaje: {message_id}")
    print("=" * 60)
    
    # La API de WhatsApp no tiene un endpoint directo para verificar el estado
    # Pero podemos intentar obtener información del webhook o usar la API de conversaciones
    # Por ahora, solo podemos mostrar información útil
    
    print("\nNOTA: WhatsApp Business API no proporciona un endpoint directo")
    print("para verificar el estado de mensajes individuales.")
    print("\nPara verificar el estado del mensaje:")
    print("1. Ve a Meta Business Suite: https://business.facebook.com")
    print("2. Navega a: WhatsApp > Mensajes")
    print("3. Busca el Message ID: " + message_id)
    print("\nO verifica los webhooks de estado que recibes en tu servidor.")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Message IDs de los últimos tests
    message_ids = [
        "wamid.HBgNNTQ5Mzc1NTU4NTU1NxUCABEYEjBGMjFCMTY4M0MzNkZBNTdCNgA=",  # 543755585557
        "wamid.HBgNNTQ5Mzc1NTYyOTk1MxUCABEYEkJCMTFDQjNFMzMzQkY4N0ZCMwA=",  # 543755629953
    ]
    
    print("VERIFICACION DE ESTADO DE MENSAJES")
    print("=" * 60)
    
    for msg_id in message_ids:
        check_message_status(msg_id)
        print("\n")
    
    print("\nRECOMENDACIONES:")
    print("=" * 60)
    print("1. Verifica en Meta Business Suite si los mensajes fueron entregados")
    print("2. Asegurate de que ambos numeros esten en la lista permitida:")
    print("   - 5493755629953 (funciona)")
    print("   - 5493755585557 (no funciona)")
    print("3. Verifica que el numero 5493755585557 tenga WhatsApp activo")
    print("4. Revisa los webhooks de estado en tu servidor para ver si hay errores")


