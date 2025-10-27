#!/usr/bin/env python3
"""
Script para probar el contexto de conversación
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from integrado.tools.context_manager import ConversationContextTool

def test_conversation_context():
    """Prueba el contexto de conversación"""
    
    print("🧪 PRUEBA DE CONTEXTO DE CONVERSACIÓN")
    print("=" * 50)
    
    context_tool = ConversationContextTool()
    
    # Simular conversación
    user_id = "5493755629953"
    channel = "whatsapp"
    
    print("1️⃣ Primer mensaje: 'Hola'")
    result1 = context_tool._run(user_id, channel, "Hola", "text")
    print(f"   Resultado: {result1}")
    
    print("\n2️⃣ Segundo mensaje: '¿Cómo estás?'")
    result2 = context_tool._run(user_id, channel, "¿Cómo estás?", "text")
    print(f"   Resultado: {result2}")
    
    print("\n3️⃣ Tercer mensaje: 'Necesito agendar una cita'")
    result3 = context_tool._run(user_id, channel, "Necesito agendar una cita", "text")
    print(f"   Resultado: {result3}")
    
    print("\n4️⃣ Cuarto mensaje: 'Para mañana a las 3pm'")
    result4 = context_tool._run(user_id, channel, "Para mañana a las 3pm", "text")
    print(f"   Resultado: {result4}")

if __name__ == "__main__":
    test_conversation_context()






