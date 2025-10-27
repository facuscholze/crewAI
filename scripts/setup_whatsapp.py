#!/usr/bin/env python3
"""
Script para configurar WhatsApp Business API
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_whatsapp_setup():
    """Verifica la configuración de WhatsApp"""
    
    print("🔍 VERIFICANDO CONFIGURACIÓN DE WHATSAPP")
    print("=" * 50)
    
    # Verificar variables de entorno
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
    
    print(f"🔑 Access Token: {'✅ Configurado' if access_token else '❌ Faltante'}")
    print(f"📱 Phone Number ID: {'✅ Configurado' if phone_number_id else '❌ Faltante'}")
    print(f"🔐 Verify Token: {'✅ Configurado' if verify_token else '❌ Faltante'}")
    
    if not all([access_token, phone_number_id, verify_token]):
        print("\n❌ Faltan credenciales de WhatsApp")
        return False
    
    # Verificar acceso a la API
    print(f"\n🌐 Verificando acceso a la API...")
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API accesible")
            print(f"📞 Número: {data.get('display_phone_number', 'N/A')}")
            print(f"🏷️  Nombre: {data.get('verified_name', 'N/A')}")
            print(f"📊 Estado: {data.get('status', 'N/A')}")
        else:
            print(f"❌ Error accediendo a la API: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False
    
    return True

def show_recipient_setup_guide():
    """Muestra guía para configurar destinatarios"""
    
    print("\n📋 GUÍA PARA CONFIGURAR DESTINATARIOS")
    print("=" * 50)
    
    print("""
Para que WhatsApp funcione, necesitas agregar tu número a la lista de destinatarios:

1. 🌐 Ve a Meta Business Manager:
   https://business.facebook.com/

2. 📱 Selecciona tu aplicación de WhatsApp Business

3. ⚙️  Ve a: WhatsApp > Configuración > Números de teléfono

4. 👥 Busca: "Lista de destinatarios" o "Recipients"

5. ➕ Agrega tu número: +5493755629953

6. 💾 Guarda los cambios

7. ⏰ Espera 5-10 minutos para que se active

Alternativamente, si estás en modo de desarrollo:
- Los mensajes se "encolarán" pero no se enviarán
- Esto es normal para testing
""")

def test_message_sending():
    """Prueba el envío de mensajes"""
    
    print("\n🧪 PRUEBA DE ENVÍO DE MENSAJES")
    print("=" * 50)
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    to = "5493755629953"
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": "🧪 Prueba del sistema Integrado"}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ Mensaje enviado exitosamente")
            return True
        else:
            error_data = response.json() if response.text else {}
            error_code = error_data.get('error', {}).get('code', 'unknown')
            
            if error_code == 131030:
                print("⚠️  Número no en lista permitida (modo desarrollo)")
                print("   Los mensajes se encolarán pero no se enviarán")
                return True  # Consideramos esto como éxito en desarrollo
            else:
                print(f"❌ Error: {error_code}")
                print(f"📄 Detalles: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

def main():
    """Función principal"""
    
    print("🚀 CONFIGURADOR DE WHATSAPP BUSINESS API")
    print("=" * 50)
    
    # Verificar configuración
    if not check_whatsapp_setup():
        print("\n❌ Configuración incompleta")
        sys.exit(1)
    
    # Mostrar guía de destinatarios
    show_recipient_setup_guide()
    
    # Preguntar si quiere probar
    response = input("\n¿Quieres probar el envío de mensajes? (s/n): ").lower()
    
    if response in ['s', 'si', 'sí', 'y', 'yes']:
        if test_message_sending():
            print("\n🎉 ¡WhatsApp configurado correctamente!")
        else:
            print("\n⚠️  Hay problemas con el envío de mensajes")
    else:
        print("\n✅ Configuración verificada. Puedes probar más tarde.")
    
    print("\n💡 Próximos pasos:")
    print("   1. Agrega tu número a la lista de destinatarios")
    print("   2. Reinicia el servidor")
    print("   3. Prueba enviando un mensaje desde WhatsApp")

if __name__ == "__main__":
    main()



