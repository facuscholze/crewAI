#!/usr/bin/env python3
"""
Script para debuggear el contexto de conversación
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from integrado.database.mongodb_conversation import mongodb_conversation_db

load_dotenv()

def debug_conversation_context():
    """Debuggear el contexto de conversación"""
    
    print("🔍 DEBUG DEL CONTEXTO DE CONVERSACIÓN")
    print("=" * 60)
    
    user_id = "5493755629953"
    
    try:
        # Obtener contexto completo
        context = mongodb_conversation_db.get_conversation_context(user_id)
        print("📋 CONTEXTO COMPLETO:")
        print(context)
        print()
        
        # Obtener historial completo
        history = mongodb_conversation_db.get_conversation_history(user_id, limit=20)
        print("📚 HISTORIAL COMPLETO:")
        for i, msg in enumerate(history, 1):
            print(f"{i}. {msg}")
        print()
        
        # Obtener estadísticas
        stats = mongodb_conversation_db.get_conversation_stats(user_id)
        print("📊 ESTADÍSTICAS:")
        print(stats)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = debug_conversation_context()
    
    if success:
        print("\n✅ Debug completado")
    else:
        print("\n❌ Error en el debug")




