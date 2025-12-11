#!/usr/bin/env python3
"""
Script para probar la prevención de duplicados
"""

import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from integrado.crew import Integrado

load_dotenv()

def test_duplicate_prevention():
    """Probar la prevención de duplicados"""
    
    print("🧪 PRUEBA DE PREVENCIÓN DE DUPLICADOS")
    print("=" * 60)
    
    # Crear instancia del crew
    integrado_crew = Integrado()
    
    user_id = "5493755629953"
    message = "ya no quiero nada de eso"
    
    print(f"📱 Simulando mensaje: '{message}'")
    print("🔄 Simulando envío duplicado...")
    
    try:
        # Simular el mismo mensaje dos veces (como haría WhatsApp)
        for i in range(2):
            print(f"\n--- Intento {i+1} ---")
            
            result = integrado_crew.process_omnicanal_message(
                channel="whatsapp",
                user_id=user_id,
                message=message,
                message_type="text"
            )
            
            print(f"✅ Resultado {i+1}: {result}")
            
            # Pausa pequeña
            time.sleep(1)
        
        print("\n🎉 Prueba completada")
        print("💡 Verifica si se generaron respuestas duplicadas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_duplicate_prevention()
    
    if success:
        print("\n✅ ¡Prueba de duplicados completada!")
        print("💡 Revisa los logs para ver si se evitaron duplicados")
    else:
        print("\n❌ Error en la prueba")




