#!/usr/bin/env python3
"""
Script para probar el flujo de conversación completo
"""

import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from integrado.crew import Integrado

load_dotenv()

def test_conversation_flow():
    """Probar el flujo de conversación completo"""
    
    print("🧪 PRUEBA DE FLUJO DE CONVERSACIÓN")
    print("=" * 60)
    
    # Crear instancia del crew
    integrado_crew = Integrado()
    
    user_id = "5493755629953"
    
    # Simular la conversación real
    messages = [
        "Me gustaría algo para el cuello",
        "Y también para las rodillas"
    ]
    
    print(f"📱 Simulando conversación con {user_id}")
    print()
    
    for i, message in enumerate(messages, 1):
        print(f"💬 Mensaje {i}: '{message}'")
        print("⏳ Procesando...")
        
        try:
            result = integrado_crew.process_omnicanal_message(
                channel="whatsapp",
                user_id=user_id,
                message=message,
                message_type="text"
            )
            
            print(f"✅ Respuesta {i}: {result}")
            print("-" * 40)
            
            # Pausa pequeña entre mensajes
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error en mensaje {i}: {str(e)}")
            return False
    
    print("🎉 Prueba de conversación completada")
    return True

if __name__ == "__main__":
    success = test_conversation_flow()
    
    if success:
        print("\n✅ ¡Flujo de conversación funcionando!")
        print("💡 Verifica si Jennifer respondió correctamente manteniendo el contexto")
    else:
        print("\n❌ Error en el flujo de conversación")




