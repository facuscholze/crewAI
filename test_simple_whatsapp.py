#!/usr/bin/env python3
"""
Script simple para probar WhatsApp con el agente optimizado
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from integrado.crew import Integrado

load_dotenv()

def test_simple_whatsapp():
    """Probar WhatsApp con configuración optimizada"""
    
    print("🧪 PRUEBA SIMPLE WHATSAPP - AGENTE OPTIMIZADO")
    print("=" * 60)
    
    # Crear instancia del crew
    integrado_crew = Integrado()
    
    # Mensaje simple
    channel = "whatsapp"
    user_id = "5493755629953"
    message = "Hola"
    
    print(f"📱 Enviando: '{message}' a {user_id}")
    print("⏳ Procesando...")
    
    try:
        result = integrado_crew.process_omnicanal_message(
            channel=channel,
            user_id=user_id,
            message=message,
            message_type="text"
        )
        
        print("✅ Procesamiento completado")
        print(f"📄 Resultado: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando prueba...")
    success = test_simple_whatsapp()
    
    if success:
        print("\n🎉 ¡Prueba completada!")
        print("💡 Verifica si recibiste el mensaje en WhatsApp")
    else:
        print("\n⚠️ Error en la prueba")




