import os
import logging
import signal
from fastapi import APIRouter, Request
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
from datetime import datetime
import glob

# REMOVED: from ..crew import Integrado  # Import circular - se importará dinámicamente
from ..database.conversation_db import conversation_db
from ..database.models import Conversation, Message, UserPreferences
from .rag_tool import RagRetrieverTool

# Parche para compatibilidad con Windows - Añadir SIGHUP si no existe
if not hasattr(signal, 'SIGHUP'):
    signal.SIGHUP = signal.SIGTERM  # Usar SIGTERM como fallback en Windows

logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "profisio_verify_2025")
messenger_router = APIRouter()


class MessengerMessageInput(BaseModel):
    """Esquema de entrada para enviar mensajes de Messenger."""

    recipient_id: str = Field(..., description="ID of the recipient")
    message: str = Field(..., description="Text message to send")


class MessengerTool(BaseTool):
    name: str = "Messenger Tool"
    description: str = (
        "Tool para enviar mensajes de texto a usuarios de Facebook Messenger. "
        "Útil para responder a los usuarios directamente en Messenger."
    )
    args_schema: Type[BaseModel] = MessengerMessageInput

    def _run(self, recipient_id: str, message: str) -> str:
        """Envía un mensaje de texto a un usuario de Messenger."""

        access_token = os.getenv('FB_ACCESS_TOKEN')

        if not access_token:
            return "Error: FB_ACCESS_TOKEN no está configurado."

        url = "https://graph.facebook.com/v18.0/me/messages"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        data = {"recipient": {"id": recipient_id}, "message": {"text": message}}

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return f"Mensaje enviado correctamente a usuario: {recipient_id}"
            else:
                return (
                    f"Error enviando mensaje: {response.status_code} - {response.text}"
                )
        except Exception as e:
            return f"Error enviando mensaje: {str(e)}"


# Instancia del MessengerTool para envío de mensajes
messenger_tool = MessengerTool()


def obtener_o_crear_conversacion_con_usuario(sender_id: str) -> tuple[bool, dict]:
    """Obtiene o crea una conversación para el usuario de Messenger.

    Returns:
        tuple: (es_primera_interaccion, conversation_data)
    """
    try:
        # Obtener o crear sesión de conversación
        session = conversation_db.get_or_create_session(sender_id, "messenger")

        # Verificar si es la primera interacción (no hay mensajes previos)
        history = conversation_db.get_conversation_history(sender_id)
        es_primera = len(history) == 0

        # Obtener contexto existente
        context = conversation_db.get_all_context(sender_id, "messenger")

        conversation_data = {
            'session_id': session.session_id,
            'channel': session.channel,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'context': context,
            'message_count': len(history),
        }

        print(
            f"{'🆕' if es_primera else '🔄'} Usuario {sender_id} - {'Primera' if es_primera else 'Conversación existente'} interacción (Total mensajes: {len(history)})"
        )

        return es_primera, conversation_data

    except Exception as e:
        logger.error(
            f"❌ Error al obtener/crear conversación para {sender_id}: {str(e)}",
            exc_info=True,
        )
        # Fallback: asumimos que no es primera interacción para evitar errores
        return False, {}


def guardar_mensaje_de_usuario(
    sender_id: str, message: str, message_metadata: dict = None  # type: ignore
) -> bool:
    """Guarda el mensaje del usuario en la base de datos."""
    try:
        conversation_db.add_message(
            session_id=sender_id,
            message_type="human",
            content=message,
            metadata=message_metadata or {},
            channel="messenger",
        )
        print(f"💾 Mensaje del usuario {sender_id} guardado en BD")
        return True
    except Exception as e:
        logger.error(
            f"❌ Error al guardar mensaje del usuario {sender_id}: {str(e)}",
            exc_info=True,
        )
        return False


def guardar_mensaje_de_agente(sender_id: str, response: str, metadata: dict = None) -> bool:  # type: ignore
    """Guarda la respuesta del agente en la base de datos."""
    try:
        conversation_db.add_message(
            session_id=sender_id,
            message_type="ai",
            content=response,
            metadata=metadata or {},
            channel="messenger",
        )
        print(f"💾 Respuesta del bot para {sender_id} guardada en BD")
        return True
    except Exception as e:
        logger.error(
            f"❌ Error al guardar respuesta del bot para {sender_id}: {str(e)}",
            exc_info=True,
        )
        return False


def guardar_contexto_de_usuario(sender_id: str, context_updates: dict) -> bool:
    """Actualiza el contexto del usuario."""
    try:
        for key, value in context_updates.items():
            conversation_db.set_context(sender_id, key, str(value), "messenger")
        print(
            f"🔄 Contexto actualizado para usuario {sender_id}: {list(context_updates.keys())}"
        )
        return True
    except Exception as e:
        logger.error(
            f"❌ Error al actualizar contexto para {sender_id}: {str(e)}", exc_info=True
        )
        return False


@messenger_router.get("/webhook/messenger")
async def verificar_webhook_meta(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado correctamente por Meta.")
        return int(challenge)  # pyright: ignore[reportArgumentType]

    logger.warning("Fallo en verificación del webhook de Messenger.")
    return {"error": "Token de verificación inválido"}, 403


@messenger_router.post("/webhook/messenger")
async def messenger_webhook(request: Request):
    """Webhook que Meta invoca cuando llega un mensaje de Messenger."""

    body = await request.json()
    print(f"📥 Mensaje entrante de Messenger: {body}")

    if body.get("object") != "page":
        print("🚫 Objeto no es 'page', ignorando mensaje")
        return {"status": "ignored"}

    print(f"🔍 Procesando {len(body.get('entry', []))} entradas")

    for entry_idx, entry in enumerate(body.get("entry", [])):
        print(f"📝 Procesando entrada {entry_idx + 1}/{len(body.get('entry', []))}")

        for event_idx, event in enumerate(entry.get("messaging", [])):
            print(
                f"🎯 Procesando evento {event_idx + 1}/{len(entry.get('messaging', []))}"
            )

            sender_id = event["sender"]["id"]
            print(f"👤 Sender ID: {sender_id}")

            # SI (El usuario envía un mensaje de texto) ENTONCES
            if "message" in event:
                texto_mensaje = event["message"].get("text", "")
                print(
                    f"📥 Procesando mensaje de texto del usuario {sender_id}: {texto_mensaje}"
                )

                # Obtener información de la conversación desde la BD
                es_primera_interaccion, conversation_data = (
                    obtener_o_crear_conversacion_con_usuario(sender_id)
                )

                # Guardar mensaje del usuario en la BD
                message_metadata = {
                    'messenger_event': event.get('message', {}),
                    'timestamp': datetime.now().isoformat(),
                    'is_first_interaction': es_primera_interaccion,
                }
                guardar_mensaje_de_usuario(sender_id, texto_mensaje, message_metadata)

                try:
                    print(f"🔧 Creando crew")
                    # Import dinámico para evitar circular import
                    from ..crew import Integrado

                    integrado_crew = Integrado()
                    crew = integrado_crew.crew()
                    print(f"✅ Crew creado exitosamente")

                    # Obtener conocimiento de la clínica vía RAG (igual que Instagram/WhatsApp)
                    clinic_knowledge = ""
                    try:
                        print(f"📚 Cargando conocimiento de la clínica vía RAG...")
                        rag = RagRetrieverTool()
                        clinic_knowledge = rag._run(texto_mensaje, top_k=3)

                        # Si RAG no pudo devolver piezas relevantes, intentar carga directa de archivo (fallback)
                        if not clinic_knowledge:
                            print(
                                f"⚠️ RAG no retornó resultados, usando fallback a archivos..."
                            )
                            knowledge_dir = os.path.normpath(
                                os.path.join(
                                    os.path.dirname(__file__),
                                    '..',
                                    '..',
                                    '..',
                                    'knowledge',
                                )
                            )
                            combined = []
                            for path in glob.glob(os.path.join(knowledge_dir, '*')):
                                if os.path.isfile(path):
                                    try:
                                        with open(path, 'r', encoding='utf-8') as kf:
                                            combined.append(kf.read())
                                    except Exception:
                                        continue
                            clinic_knowledge = "\n\n".join(combined) if combined else ""

                        # Limitar tamaño para prompts
                        if clinic_knowledge and len(clinic_knowledge) > 6000:
                            clinic_knowledge = (
                                clinic_knowledge[:6000]
                                + "\n\n[... conocimiento truncado ...]"
                            )
                        print(
                            f"✅ Conocimiento cargado: {len(clinic_knowledge)} caracteres"
                        )
                    except Exception as kb_error:
                        print(
                            f"⚠️ Error cargando clinic knowledge via RAG: {str(kb_error)}"
                        )
                        clinic_knowledge = ""

                    # Preparar inputs con contexto de la conversación Y conocimiento de la clínica
                    crew_inputs = {
                        "channel": "messenger",
                        "message": texto_mensaje,
                        "customer_name": conversation_data.get('context', {}).get(
                            'customer_name', 'Cliente de Messenger'
                        ),
                        "sender_id": sender_id,
                        "is_first_interaction": es_primera_interaccion,
                        "conversation_context": conversation_data.get('context', {}),
                        "message_count": conversation_data.get('message_count', 0),
                        "clinic_knowledge": clinic_knowledge,  # 🆕 Agregar conocimiento de la clínica
                    }

                    print(
                        f"🚀 Ejecutando crew con inputs: channel=messenger, message='{texto_mensaje}', first_interaction={es_primera_interaccion}, kb_size={len(clinic_knowledge)}"
                    )
                    resultado = crew.kickoff(inputs=crew_inputs)
                    print(f"✅ Crew ejecutado exitosamente")

                except Exception as e:
                    logger.error(
                        f"❌ Error al crear o ejecutar crew: {str(e)}", exc_info=True
                    )
                    error_response = "Lo siento, ocurrió un error técnico. Por favor intenta de nuevo."
                    messenger_tool._run(
                        recipient_id=sender_id,
                        message=error_response,
                    )
                    # Guardar mensaje de error en la BD
                    guardar_mensaje_de_agente(
                        sender_id,
                        error_response,
                        {'error': True, 'error_message': str(e)},
                    )
                    continue

                print(f"🔄 Procesando respuesta del crew")

                # Extraer respuesta del crew usando el atributo correcto
                respuesta_agente = (
                    getattr(resultado, "raw", None)
                    or getattr(resultado, "output", None)
                    or getattr(resultado, "final_output", None)
                    or "Lo siento, no entendí tu mensaje. ¿Podrías repetirlo?"
                )
                print(f"📤 Respuesta generada: {respuesta_agente}")

                # Guardar respuesta del bot en la BD
                response_metadata = {
                    'crew_result_type': type(resultado).__name__,
                    'timestamp': datetime.now().isoformat(),
                    'crew_success': True,
                }
                guardar_mensaje_de_agente(
                    sender_id, str(respuesta_agente), response_metadata
                )

                # Actualizar contexto del usuario si es necesario
                context_updates = {
                    'last_interaction': datetime.now().isoformat(),
                    'total_messages': conversation_data.get('message_count', 0)
                    + 2,  # +1 user +1 bot
                }

                # Si es primera interacción, marcar al usuario como conocido
                if es_primera_interaccion:
                    context_updates['first_contact_date'] = datetime.now().isoformat()
                    context_updates['customer_status'] = 'active'

                guardar_contexto_de_usuario(sender_id, context_updates)

                messenger_tool._run(recipient_id=sender_id, message=respuesta_agente)
                print(f"✅ Mensaje enviado exitosamente a usuario {sender_id}")

            # SI (El usuario hace click en botón (postback)) ENTONCES
            if "postback" in event:
                payload = event["postback"].get("payload", "")
                print(
                    f"🔘 Postback recibido del usuario {sender_id} con payload: {payload}"
                )

                # Guardar el postback como mensaje del usuario
                postback_metadata = {
                    'type': 'postback',
                    'payload': payload,
                    'messenger_event': event.get('postback', {}),
                    'timestamp': datetime.now().isoformat(),
                }
                guardar_mensaje_de_usuario(
                    sender_id, f"Botón presionado: {payload}", postback_metadata
                )

                # Respuesta al postback
                postback_response = (
                    f"Has hecho click en el botón con payload: {payload}"
                )
                messenger_tool._run(
                    recipient_id=sender_id,
                    message=postback_response,
                )

                # Guardar respuesta del bot
                guardar_mensaje_de_agente(
                    sender_id,
                    postback_response,
                    {'type': 'postback_response', 'original_payload': payload},
                )

                print(f"✅ Respuesta a postback enviada a usuario {sender_id}")

        print(f"✅ Procesamiento completado exitosamente")
        return {"status": "ok"}


def es_primera_interaccion(sender_id: str) -> bool:
    """Verifica si es la primera interacción del usuario.

    Esta función se mantiene por compatibilidad, pero ahora usa la BD.
    """
    try:
        es_primera, _ = obtener_o_crear_conversacion_con_usuario(sender_id)
        return es_primera
    except Exception as e:
        logger.error(
            f"❌ Error al verificar primera interacción para {sender_id}: {str(e)}"
        )
        return False


def marcar_usuario_como_conocido(sender_id: str):
    """Marca al usuario como conocido para futuras interacciones.

    Esta función se mantiene por compatibilidad, pero ahora usa la BD.
    """
    try:
        context_updates = {
            'marked_as_known': datetime.now().isoformat(),
            'customer_status': 'known',
        }
        guardar_contexto_de_usuario(sender_id, context_updates)
        print(f"Usuario {sender_id} marcado como conocido en BD")
    except Exception as e:
        logger.error(
            f"❌ Error al marcar usuario {sender_id} como conocido: {str(e)}",
            exc_info=True,
        )


def obtener_estadisticas_de_usuario(sender_id: str) -> dict:
    """Obtiene estadísticas del usuario desde la base de datos."""
    try:
        stats = conversation_db.get_session_stats(sender_id, "messenger")
        return stats
    except Exception as e:
        logger.error(
            f"❌ Error al obtener estadísticas para {sender_id}: {str(e)}",
            exc_info=True,
        )
        return {}


def obtener_historial_de_usuario(sender_id: str, limit: int = 10) -> list:
    """Obtiene el historial de conversación del usuario."""
    try:
        history = conversation_db.get_conversation_history(
            session_id=sender_id, limit=limit
        )
        return history
    except Exception as e:
        logger.error(
            f"❌ Error al obtener historial para {sender_id}: {str(e)}", exc_info=True
        )
        return []
