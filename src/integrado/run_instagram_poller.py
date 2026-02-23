#!/usr/bin/env python3
"""
Script para manejar el polling de Instagram.
"""
import logging
import os
import time
from dotenv import load_dotenv
from integrado.crew import Integrado
from integrado.tools.instagram_tool import InstagramGetUnreadConversationsTool

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

def process_unread_messages(integrado_crew, tool_for_instagram):
    """Busca y procesa mensajes no leídos de Instagram."""
    logger.info(f"Verificando mensajes no leídos de Instagram...")

    # Obtener conversaciones no leídas
    unread_convs = tool_for_instagram._run()

    if not unread_convs:
        logger.debug("No se encontraron conversaciones no leídas.")
        return

    # Procesar cada conversación no leída
    for conv in unread_convs:
        logger.debug(f"Procesando conversation_id: {conv['id']}")
        try:
            # Extraer información necesaria
            user_id = conv.get('last_message_from')  # Cambio: usar last_message_from como user_id
            message = conv.get('last_message_text')  # Cambio: usar last_message_text como mensaje
            message_type = 'text'  # Por ahora solo soportamos mensajes de texto

            if not user_id or not message:
                logger.warning(f"Falta información necesaria para conversation_id: {conv['id']}")
                continue

            logger.info(f"Procesando mensaje omnicanal: instagram - {user_id} - {message[:50]}...")

            result = integrado_crew.process_omnicanal_message(
                channel='instagram',
                user_id=user_id,
                message=message,
                message_type=message_type
            )

            logger.info(f"Mensaje procesado. Resultado: {result}")

        except Exception as e:
            logger.error(f"Error procesando conversación {conv['id']}: {e}", exc_info=True)

    logger.debug("Procesamiento de conversaciones completado.")

def run_continuous_loop(interval_seconds=30):
    """
    Ejecuta el bucle de polling continuo.
    """
    logger.info(f"Iniciando loop continuo de Instagram (verificando cada {interval_seconds} segundos)")

    # Crear instancias que necesitaremos
    integrado_crew = Integrado()
    instagram_tool = InstagramGetUnreadConversationsTool()

    while True:
        try:
            process_unread_messages(integrado_crew, instagram_tool)
        except Exception as e:
            logger.error(f"Error en el ciclo de polling: {e}")

        logger.debug(f"Esperando {interval_seconds} segundos hasta la próxima verificación...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Si se ejecuta directamente, iniciar el loop
    interval = int(os.getenv('INSTAGRAM_POLL_INTERVAL', os.getenv('INSTAGRAM_POLL_SECONDS', '30')))
    run_continuous_loop(interval)
