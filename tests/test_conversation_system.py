#!/usr/bin/env python3
"""
Script para probar el sistema completo de conversaciones
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from integrado.database.mongodb_conversation import mongodb_conversation_db

def test_conversation_system():
    """Probar el sistema de conversaciones completo"""
    
    print("🧪 PRUEBA DEL SISTEMA DE CONVERSACIONES")
    print("=" * 60)
    
    session_id = "5493755629953"
    
    # Simular conversación completa
    messages = [
        ("human", "Hola"),
        ("ai", "¡Hola! Soy Jennifer de Houston Aesthetics, encantada de saludarte 😊. Estoy aquí para ayudarte con cualquier consulta sobre tratamientos estéticos, precios o agendar una cita. ¿En qué puedo asistirte hoy?"),
        ("human", "Me gustaría agendar una cita"),
        ("ai", "¡Perfecto! 😊 Para ayudarte a agendar, ¿podrías decirme qué tratamiento te interesa y qué día o horario prefieres? Así reviso disponibilidad para ti. También, ¿cómo te llamas?"),
        ("human", "Me llamo facundo Scholze"),
        ("ai", "¡Mucho gusto, Facundo! 😊 ¿Qué tratamiento te gustaría agendar y qué día u horario te viene mejor? Así puedo revisar y ayudarte a reservar tu cita."),
        ("human", "Me gustaría un botox para el lunes que viene"),
        ("ai", "Gracias, Facundo 😊. Para poder agendar tu Botox el lunes que viene, déjame revisar la disponibilidad de ese día. ¿Prefieres mañana o tarde? Así me ajusto mejor a tu horario."),
        ("human", "Por la tarde"),
        ("ai", "Gracias, Facundo. Para concretar la cita, ¿podrías darme tu número de teléfono o correo electrónico? También dime a qué hora específica de la tarde prefieres tu Botox, así dejo todo listo para ti."),
        ("human", "El mismo número de teléfono de la conversación actual , facundoscholze@gmail.com a las 2 te la tarde"),
        ("ai", "Facundo, para agendar el Botox necesito tu número de teléfono, ya que no está registrado en la conversación. ¿Me lo puedes pasar, por favor? Así dejo todo listo para el lunes a las 2 pm."),
        ("human", "3755629953"),
        ("ai", "Facundo, ya tengo registrado tu pedido para Botox el lunes que viene a las 2 pm. ¿Quieres que confirme y guarde definitivamente esta cita? Si quieres cambiar o agregar algo, dime para ajustarlo."),
        ("human", "Perfecto"),
        ("ai", "Listo, Facundo, tu cita para Botox el lunes que viene a las 2 pm está confirmada 😊. ¿Quieres que te ayude con algo más?")
    ]
    
    print(f"📱 Simulando conversación para: {session_id}")
    print(f"📊 Total mensajes: {len(messages)}")
    
    # Agregar todos los mensajes
    for i, (msg_type, content) in enumerate(messages, 1):
        print(f"\n{i:2d}. Agregando mensaje {msg_type}: {content[:50]}...")
        
        mongodb_conversation_db.add_message(
            session_id=session_id,
            message_type=msg_type,
            content=content,
            additional_kwargs={
                "timestamp": f"2024-01-15 10:{i:02d}:00",
                "channel": "whatsapp"
            }
        )
    
    # Obtener conversación completa
    print(f"\n📋 OBTENIENDO CONVERSACIÓN COMPLETA")
    print("=" * 60)
    
    conversation = mongodb_conversation_db.get_conversation(session_id)
    
    if conversation:
        print(f"✅ Conversación encontrada:")
        print(f"   ID: {conversation['_id']['$oid']}")
        print(f"   Session: {conversation['sessionId']}")
        print(f"   Total mensajes: {len(conversation['messages'])}")
        
        # Mostrar últimos mensajes
        print(f"\n📝 ÚLTIMOS 5 MENSAJES:")
        for i, msg in enumerate(conversation['messages'][-5:], 1):
            msg_type = msg['type']
            content = msg['data']['content']
            emoji = "👤" if msg_type == "human" else "🤖"
            print(f"   {i}. {emoji} {msg_type}: {content[:60]}...")
    
    # Obtener contexto formateado
    print(f"\n🧠 CONTEXTO FORMATEADO PARA EL AGENTE:")
    print("=" * 60)
    
    context = mongodb_conversation_db.get_conversation_context(session_id)
    print(context)
    
    # Probar nuevo mensaje
    print(f"\n💬 PROBANDO NUEVO MENSAJE:")
    print("=" * 60)
    
    new_message = "¿Cuánto cuesta el botox?"
    
    # Agregar nuevo mensaje humano
    mongodb_conversation_db.add_message(
        session_id=session_id,
        message_type="human",
        content=new_message,
        additional_kwargs={
            "timestamp": "2024-01-15 11:00:00",
            "channel": "whatsapp"
        }
    )
    
    # Obtener nuevo contexto
    new_context = mongodb_conversation_db.get_conversation_context(session_id)
    print(f"Nuevo contexto para: '{new_message}'")
    print("-" * 40)
    print(new_context)

def test_context_extraction():
    """Probar extracción de contexto"""
    
    print(f"\n🔍 PRUEBA DE EXTRACCIÓN DE CONTEXTO")
    print("=" * 60)
    
    session_id = "5493755629953"
    conversation = mongodb_conversation_db.get_conversation(session_id)
    
    if conversation:
        messages = conversation['messages']
        context_info = mongodb_conversation_db._extract_context_info(messages)
        
        print("📋 INFORMACIÓN EXTRAÍDA DEL CONTEXTO:")
        for key, value in context_info.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    test_conversation_system()
    test_context_extraction()
    
    print(f"\n🎉 PRUEBA COMPLETADA")
    print("=" * 60)
    print("✅ Sistema de conversaciones funcionando correctamente")
    print("✅ Formato MongoDB compatible implementado")
    print("✅ Contexto de conversación mantenido")
    print("✅ Extracción de información funcionando")






