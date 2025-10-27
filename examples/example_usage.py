#!/usr/bin/env python3
"""
Ejemplo de uso del Sistema Multiagente Omnicanal Integrado
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrado.crew import Integrado

def main():
    """Función principal de ejemplo"""
    
    print("🚀 Iniciando Sistema Multiagente Omnicanal Integrado")
    print("=" * 60)
    
    # Inicializar el crew
    try:
        crew = Integrado()
        print("✅ Crew inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando crew: {e}")
        return
    
    # Ejemplo 1: Procesar mensaje de WhatsApp
    print("\n📱 Ejemplo 1: Mensaje de WhatsApp")
    print("-" * 40)
    
    try:
        result = crew.process_omnicanal_message(
            channel="whatsapp",
            user_id="1234567890",
            message="Hola, quiero agendar una cita para mañana",
            message_type="text"
        )
        print(f"✅ Resultado WhatsApp: {result}")
    except Exception as e:
        print(f"❌ Error procesando WhatsApp: {e}")
    
    # Ejemplo 2: Procesar mensaje de Messenger
    print("\n💬 Ejemplo 2: Mensaje de Messenger")
    print("-" * 40)
    
    try:
        result = crew.process_omnicanal_message(
            channel="messenger",
            user_id="facebook_user_123",
            message="Necesito información sobre sus servicios",
            message_type="text"
        )
        print(f"✅ Resultado Messenger: {result}")
    except Exception as e:
        print(f"❌ Error procesando Messenger: {e}")
    
    # Ejemplo 3: Procesar mensaje de Instagram
    print("\n📸 Ejemplo 3: Mensaje de Instagram")
    print("-" * 40)
    
    try:
        result = crew.process_omnicanal_message(
            channel="instagram",
            user_id="instagram_user_456",
            message="Me encanta tu contenido! ¿Tienes más información?",
            message_type="text"
        )
        print(f"✅ Resultado Instagram: {result}")
    except Exception as e:
        print(f"❌ Error procesando Instagram: {e}")
    
    # Ejemplo 4: Procesar email de Gmail
    print("\n📧 Ejemplo 4: Email de Gmail")
    print("-" * 40)
    
    try:
        result = crew.process_omnicanal_message(
            channel="gmail",
            user_id="user@example.com",
            message="Asunto: Consulta sobre productos - Hola, me interesa conocer más sobre sus productos",
            message_type="email"
        )
        print(f"✅ Resultado Gmail: {result}")
    except Exception as e:
        print(f"❌ Error procesando Gmail: {e}")
    
    # Ejemplo 5: Programar evento en calendario
    print("\n📅 Ejemplo 5: Programar evento en calendario")
    print("-" * 40)
    
    try:
        # Crear fecha para mañana
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        event_details = {
            'title': 'Cita de consulta',
            'description': 'Consulta inicial con el cliente',
            'start_datetime': start_time.isoformat(),
            'end_datetime': end_time.isoformat(),
            'location': 'Oficina principal',
            'timezone': 'America/Mexico_City'
        }
        
        result = crew.schedule_calendar_event(
            user_id="1234567890",
            event_details=event_details
        )
        print(f"✅ Resultado Calendar: {result}")
    except Exception as e:
        print(f"❌ Error programando evento: {e}")
    
    # Ejemplo 6: Llamada de voz con ElevenLabs
    print("\n🎤 Ejemplo 6: Llamada de voz")
    print("-" * 40)
    
    try:
        result = crew.process_omnicanal_message(
            channel="whatsapp",
            user_id="1234567890",
            message="Por favor, llámame para confirmar la cita",
            message_type="voice_call"
        )
        print(f"✅ Resultado Llamada: {result}")
    except Exception as e:
        print(f"❌ Error procesando llamada: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Ejemplos completados!")
    print("\nPara más información, consulta el README.md")
    print("Para iniciar el servidor API, ejecuta: python -m integrado.main")

def test_individual_tools():
    """Función para probar herramientas individuales"""
    
    print("\n🔧 Probando herramientas individuales")
    print("-" * 40)
    
    # Importar herramientas
    try:
        from integrado.tools.whatsapp_tool import WhatsAppTool
        from integrado.tools.context_manager import ConversationContextTool
        from integrado.tools.elevenlabs_tool import ElevenLabsVoiceTool
        
        print("✅ Herramientas importadas correctamente")
        
        # Probar herramienta de contexto
        context_tool = ConversationContextTool()
        result = context_tool._run(
            user_id="test_user",
            channel="whatsapp",
            message="Mensaje de prueba",
            message_type="text"
        )
        print(f"✅ Contexto: {result[:100]}...")
        
    except Exception as e:
        print(f"❌ Error probando herramientas: {e}")

if __name__ == "__main__":
    # Verificar variables de entorno
    required_env_vars = [
        'OPENAI_API_KEY',
        'WHATSAPP_ACCESS_TOKEN',
        'ELEVENLABS_API_KEY'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nConfigura estas variables en tu archivo .env")
        print("Puedes usar env.example como referencia")
        
        # Continuar con ejemplos básicos
        print("\nContinuando con ejemplos básicos (sin APIs externas)...")
    
    # Ejecutar ejemplos
    main()
    
    # Probar herramientas individuales
    test_individual_tools()






