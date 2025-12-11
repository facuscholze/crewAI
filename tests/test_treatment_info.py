#!/usr/bin/env python3
"""
Script para probar la información de tratamientos
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from integrado.crew import Integrado

load_dotenv()

def test_treatment_info():
    """Probar la información de tratamientos"""
    
    print("🧪 PRUEBA DE INFORMACIÓN DE TRATAMIENTOS")
    print("=" * 60)
    
    # Crear instancia del crew
    integrado_crew = Integrado()
    
    user_id = "5493755629953"
    
    # Mensajes de prueba sobre tratamientos
    test_messages = [
        "¿Cuánto cuesta el botox?",
        "¿Tiene efectos secundarios el botox?",
        "¿Cuánto cuesta un tratamiento para el cuello?",
        "¿Y para las rodillas cuánto cuesta?"
    ]
    
    print(f"📱 Probando información de tratamientos con {user_id}")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"💬 Pregunta {i}: '{message}'")
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
            
        except Exception as e:
            print(f"❌ Error en pregunta {i}: {str(e)}")
            return False
    
    print("🎉 Prueba de tratamientos completada")
    return True

if __name__ == "__main__":
    success = test_treatment_info()
    
    if success:
        print("\n✅ ¡Información de tratamientos funcionando!")
        print("💡 Verifica que Jennifer responda con precios específicos")
    else:
        print("\n❌ Error en la prueba de tratamientos")




