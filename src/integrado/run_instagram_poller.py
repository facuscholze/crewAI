#!/usr/bin/env python3
"""
Script para manejar el polling de Instagram.
"""
import os
import time
from dotenv import load_dotenv
from integrado.crew import Integrado
from integrado.tools.instagram_tool import InstagramGetUnreadConversationsTool

# Cargar variables de entorno
load_dotenv()

def process_unread_messages(integrado_crew, tool_for_instagram):
    """Busca y procesa mensajes no leídos de Instagram."""
    print(f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} - Verificando mensajes...")
    print("🤖 Bot de Instagram - Procesando mensajes no leídos")
    print("=" * 60 + "\n")

    # Obtener conversaciones no leídas
    unread_convs = tool_for_instagram._run()

    print(f"📋 Resultado:\n{unread_convs}")

    if not unread_convs:
        print("\n✅ No se encontraron conversaciones no leídas.")
        return

    # Procesar cada conversación no leída
    for conv in unread_convs:
        print(f"➡️ Procesando conversation_id: {conv['id']}")
        try:
            # Extraer información necesaria
            user_id = conv.get('last_message_from')  # Cambio: usar last_message_from como user_id
            message = conv.get('last_message_text')  # Cambio: usar last_message_text como mensaje
            message_type = 'text'  # Por ahora solo soportamos mensajes de texto

            if not user_id or not message:
                print(f"⚠️ Falta información necesaria para conversation_id: {conv['id']}")
                continue

            print(f"🚀 Procesando mensaje omnicanal: instagram - {user_id} - {message[:50]}...")

            # Procesar con el crew
            print(f"\nProcesando mensaje con:")
            print(f"- Channel: instagram")
            print(f"- User ID: {user_id}")
            print(f"- Message: {message}")
            print(f"- Type: {message_type}\n")

            result = integrado_crew.process_omnicanal_message(
                channel='instagram',
                user_id=user_id,
                message=message,
                message_type=message_type
            )

            print(f"✅ Mensaje procesado. Resultado: {result}")

        except Exception as e:
            import traceback
            print(f"❌ Error procesando conversación {conv['id']}:")
            print(f"Error: {e}")
            print("Traceback:")
            traceback.print_exc()

    print("\n✅ Procesamiento de conversaciones completado.")

def run_continuous_loop(interval_seconds=30):
    """
    Ejecuta el bucle de polling continuo.
    """
    print(f"🔄 Iniciando loop continuo (verificando cada {interval_seconds} segundos)")
    print("Presiona Ctrl+C para detener\n")

    # Crear instancias que necesitaremos
    integrado_crew = Integrado()
    instagram_tool = InstagramGetUnreadConversationsTool()

    while True:
        try:
            process_unread_messages(integrado_crew, instagram_tool)
        except Exception as e:
            print(f"❌ Error en el ciclo de polling: {e}")

        print(f"\n💤 Esperando {interval_seconds} segundos hasta la próxima verificación...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Si se ejecuta directamente, iniciar el loop
    interval = int(os.getenv('INSTAGRAM_POLL_INTERVAL', os.getenv('INSTAGRAM_POLL_SECONDS', '30')))
    run_continuous_loop(interval)