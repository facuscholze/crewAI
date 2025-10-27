#!/usr/bin/env python3
"""
Script para debuggear respuestas duplicadas
"""

import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from integrado.crew import Integrado

load_dotenv()

def debug_duplicate_responses():
    """Debuggear respuestas duplicadas"""
    
    print("🔍 DEBUG DE RESPUESTAS DUPLICADAS")
    print("=" * 60)
    
    # Crear instancia del crew
    integrado_crew = Integrado()
    
    user_id = "5493755629953"
    message = "ya no quiero nada de eso"
    
    print(f"📱 Simulando mensaje: '{message}'")
    print("⏳ Procesando...")
    
    try:
        # Capturar timestamp antes
        start_time = time.time()
        
        result = integrado_crew.process_omnicanal_message(
            channel="whatsapp",
            user_id=user_id,
            message=message,
            message_type="text"
        )
        
        # Capturar timestamp después
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ Procesamiento completado en {execution_time:.2f} segundos")
        print(f"📄 Resultado: {result}")
        
        # Verificar si hay duplicados en la base de datos
        print("\n🔍 Verificando duplicados en la base de datos...")
        from integrado.database.mongodb_conversation import mongodb_conversation_db
        
        context = mongodb_conversation_db.get_conversation_context(user_id)
        print("📋 Contexto actualizado:")
        print(context[:500] + "..." if len(context) > 500 else context)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = debug_duplicate_responses()
    
    if success:
        print("\n✅ Debug completado")
        print("💡 Verifica si se generaron respuestas duplicadas")
    else:
        print("\n❌ Error en el debug")




