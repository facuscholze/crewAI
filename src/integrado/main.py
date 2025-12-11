#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

# --- 1. IMPORTA TODO ARRIBA ---
# Importa todo lo que necesitas, sin condicionales
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import json
import threading
import requests
import importlib.util
from pathlib import Path
from integrado.crew import Integrado  # Asumo que tu crew está en crew.py

# --- 2. DEFINE TU BANDERA DE ENTRENAMIENTO ---
IS_TRAINING = any(cmd in " ".join(sys.argv) for cmd in ["train", "replay", "test"])

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# --- 3. INICIALIZA TU CREW ---
# Esto se necesita tanto para entrenar como para la API
integrado_crew = Integrado()

# --- 4. BLOQUE CONDICIONAL SOLO PARA FASTAPI ---
# Todo lo relacionado con la API va DENTRO de este 'if'
if not IS_TRAINING:
    
    # Mueve la inicialización de 'app' aquí dentro
    app = FastAPI(
        title="Integrado Omnicanal API",
        description="API para el sistema multiagente omnicanal con CrewAI",
        version="1.0.0"
    )

    # Mueve el middleware aquí dentro
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mueve tus Pydantic models aquí dentro
    class MessageRequest(BaseModel):
        channel: str
        user_id: str
        message: str
        message_type: str = "text"
        metadata: Optional[Dict] = None

    class CalendarEventRequest(BaseModel):
        user_id: str
        title: str
        description: str
        start_datetime: str
        end_datetime: str
        attendees: Optional[List[str]] = None
        location: Optional[str] = None
        timezone: str = "UTC"

    class WebhookRequest(BaseModel):
        channel: str
        data: Dict

    # Cache para duplicados (solo necesario para el servidor)
    processed_messages = set()

    # --- Mueve todos tus Endpoints (@app.post / @app.get) aquí dentro ---
    
    @app.post("/api/message")
    async def process_message(request: MessageRequest):
        """Procesa mensajes entrantes de cualquier canal omnicanal"""
        try:
            result = integrado_crew.process_omnicanal_message(
                channel=request.channel,
                user_id=request.user_id,
                message=request.message,
                message_type=request.message_type
            )
            return {"success": True, "result": str(result)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/calendar/schedule")
    async def schedule_event(request: CalendarEventRequest):
        """Programa un evento en Google Calendar"""
        # ... (tu código de endpoint)
        try:
            event_details = {
                'title': request.title,
                'description': request.description,
                'start_datetime': request.start_datetime,
                'end_datetime': request.end_datetime,
                'attendees': request.attendees or [],
                'location': request.location,
                'timezone': request.timezone
            }
            
            result = integrado_crew.schedule_calendar_event(
                user_id=request.user_id,
                event_details=event_details
            )
            return {"success": True, "result": str(result)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @app.get("/webhook/{channel}")
    async def webhook_verification(
        channel: str,
        hub_mode: str = Query(None, alias="hub.mode"),
        hub_challenge: str = Query(None, alias="hub.challenge"),
        hub_verify_token: str = Query(None, alias="hub.verify_token")
    ):
        """Maneja la verificación de webhooks (GET request)"""
        # ... (tu código de endpoint)
        print(f"🔍 Verificación webhook - Canal: {channel}, Mode: {hub_mode}, Token: {hub_verify_token}, Challenge: {hub_challenge}")
        # Use a channel-specific verify token if available, otherwise fall back to a generic one
        env_token_key = f"{channel.upper()}_WEBHOOK_VERIFY_TOKEN"
        expected_token = os.getenv(env_token_key, os.getenv('WEBHOOK_VERIFY_TOKEN', os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', '43833793')))

        print(f"🔑 Token esperado (from {env_token_key} or fallback): {expected_token}")
        print(f"🔑 Token recibido: {hub_verify_token}")
        print(f"🔑 Modo: {hub_mode}")

        # Facebook/Instagram expects the exact hub.challenge value as plain text when verifying
        if hub_mode == "subscribe":
            if hub_verify_token == expected_token:
                print(f"✅ Webhook verificado exitosamente para canal {channel}!")
                # Return plain text body with the challenge
                return PlainTextResponse(str(hub_challenge), status_code=200)
            else:
                print(f"❌ Token de verificación incorrecto o modo inválido")
                print(f"   - Modo correcto: {hub_mode == 'subscribe'}")
                print(f"   - Token correcto: {hub_verify_token == expected_token}")
                raise HTTPException(status_code=403, detail="Forbidden")

        # Default response for non-verification requests
        return {"status": "verified"}


    @app.post("/webhook/{channel}")
    async def webhook_handler(channel: str, request: Request):
        """Maneja webhooks de diferentes canales"""
        # ... (tu código de endpoint)
        try:
            def transcribe_whatsapp_audio_message(message: Dict) -> Optional[str]:
                """Descarga el audio de WhatsApp y lo transcribe con OpenAI Whisper si está configurado."""
                try:
                    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
                    if not access_token:
                        print("⚠️ No hay WHATSAPP_ACCESS_TOKEN para descargar media.")
                        return None
                    audio_info = message.get('audio') or {}
                    media_id = audio_info.get('id')
                    if not media_id:
                        print("⚠️ Mensaje de audio sin media_id.")
                        return None
                    # 1) Obtener URL del media
                    media_meta_url = f"https://graph.facebook.com/v18.0/{media_id}"
                    meta_resp = requests.get(
                        media_meta_url,
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=30,
                    )
                    if meta_resp.status_code != 200:
                        print(f"⚠️ Error obteniendo metadatos de media: {meta_resp.status_code} {meta_resp.text[:200]}")
                        return None
                    media_url = meta_resp.json().get('url')
                    if not media_url:
                        print("⚠️ No se obtuvo URL del media.")
                        return None
                    # 2) Descargar binario del audio
                    media_resp = requests.get(
                        media_url,
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=60,
                    )
                    if media_resp.status_code != 200:
                        print(f"⚠️ Error descargando media: {media_resp.status_code}")
                        return None
                    audio_bytes = media_resp.content
                    # 3) Transcribir con OpenAI Whisper (si hay API key)
                    openai_key = os.getenv('OPENAI_API_KEY')
                    if not openai_key:
                        print("⚠️ No hay OPENAI_API_KEY; no se puede transcribir. Se usará placeholder.")
                        return None
                    files = {
                        "file": ("audio.ogg", audio_bytes, "audio/ogg"),
                    }
                    data = {
                        "model": "whisper-1",
                        "response_format": "json",
                        "language": "es",
                    }
                    headers = {
                        "Authorization": f"Bearer {openai_key}",
                    }
                    whisper_resp = requests.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=120,
                    )
                    if whisper_resp.status_code != 200:
                        print(f"⚠️ Error en Whisper: {whisper_resp.status_code} {whisper_resp.text[:200]}")
                        return None
                    tr_json = whisper_resp.json()
                    text = tr_json.get("text")
                    if text:
                        print(f"📝 Transcripción Whisper: {text[:120]}...")
                    return text
                except Exception as e:
                    print(f"⚠️ Error transcribiendo audio: {e}")
                    return None

            if channel.lower() == "whatsapp":
                data = await request.json()
                print(f"📱 WhatsApp webhook recibido: {data}")
                
                if 'entry' in data and len(data['entry']) > 0:
                    entry = data['entry'][0]
                    if 'changes' in entry and len(entry['changes']) > 0:
                        change = entry['changes'][0]
                        if 'value' in change and 'messages' in change['value']:
                            messages = change['value']['messages']
                            for message in messages:
                                # Solo procesar mensajes entrantes (no status updates)
                                if 'from' not in message:
                                    continue  # Saltar status updates
                                    
                                user_id = message.get('from', 'unknown')
                                message_text = message.get('text', {}).get('body', '')
                                message_type = message.get('type', 'text')
                                message_id = message.get('id', '')
                                
                                # Solo procesar mensajes de texto o audio (no status)
                                if message_type not in ('text', 'audio', 'voice'):
                                    continue
                                # Si es audio/voice, intentamos transcribir
                                if message_type in ('audio', 'voice') or message.get('audio'):
                                    transcribed = transcribe_whatsapp_audio_message(message)
                                    if transcribed:
                                        message_text = transcribed
                                        # Tratarlo como texto normal para mantener un solo hilo
                                        message_type = 'text'
                                    else:
                                        # Placeholder para que el flujo continúe
                                        message_text = message_text or "[mensaje de voz]"
                                
                                message_key = f"{user_id}:{message_id}:{message_text}"
                                print(f"📱 Mensaje de WhatsApp: {user_id} -> {message_text}")
                                print(f"🔑 Clave del mensaje: {message_key}")
                                
                                if message_key in processed_messages:
                                    print(f"⚠️ Mensaje duplicado detectado, ignorando: {message_key}")
                                    continue
                                
                                processed_messages.add(message_key)
                                
                                if len(processed_messages) > 100:
                                    processed_messages.clear()
                                
                                print(f"✅ Procesando mensaje nuevo: {message_key}")
                                
                                result = integrado_crew.process_omnicanal_message(
                                    channel=channel,
                                    user_id=user_id,
                                    message=message_text,
                                    message_type=message_type
                                )
                                print(f"✅ Respuesta generada: {result}")
                
                return {"status": "received"}
            
            # ... (tus otros 'elif' para messenger, instagram, etc.)
            elif channel.lower() == "instagram":
                data = await request.json()
                print(f"📸 Instagram webhook recibido: {data}")

                # Intentar extraer mensajes de varios formatos posibles
                try:
                    entries = data.get('entry', []) if isinstance(data, dict) else []
                    for entry in entries:
                        changes = entry.get('changes', [])
                        for change in changes:
                            value = change.get('value', {})
                            # Mensajes pueden venir en 'messages' o 'messages' dentro de 'value'
                            messages = value.get('messages') or value.get('messages', [])
                            if not messages and isinstance(value, dict) and 'message' in value:
                                messages = [value.get('message')]

                            # En algunos payloads los mensajes están directamente en value['messages']
                            if messages:
                                for message in messages:
                                    # Diferentes estructuras posibles, intentar extraer sender y texto
                                    sender_id = None
                                    text = ''
                                    msg_id = ''
                                    if isinstance(message, dict):
                                        sender_id = message.get('from') or message.get('sender') or message.get('from_id')
                                        text = message.get('text') or (message.get('message') or {}).get('text') or message.get('body') or ''
                                        msg_id = message.get('id') or message.get('message_id') or ''

                                    if not sender_id:
                                        # intentar obtener desde value->participants o metadata
                                        participants = value.get('participants', {}).get('data', []) if isinstance(value.get('participants'), dict) else value.get('participants')
                                        if participants and isinstance(participants, list):
                                            # tomar el que no sea el bot si es posible
                                            sender_id = participants[0].get('id') if isinstance(participants[0], dict) else str(participants[0])

                                    if not sender_id:
                                        sender_id = 'unknown'

                                    message_key = f"instagram:{sender_id}:{msg_id}:{text}"
                                    if message_key in processed_messages:
                                        print(f"⚠️ Mensaje duplicado Instagram detectado, ignorando: {message_key}")
                                        continue
                                    processed_messages.add(message_key)
                                    if len(processed_messages) > 100:
                                        processed_messages.clear()

                                    print(f"✅ Procesando mensaje Instagram: {sender_id} -> {text}")
                                    result = integrado_crew.process_omnicanal_message(
                                        channel='instagram',
                                        user_id=sender_id,
                                        message=text,
                                        message_type='text',
                                        original_message_id=msg_id or None
                                    )
                                    print(f"✅ Respuesta Instagram generada: {result}")

                except Exception as e:
                    print(f"❌ Error procesando webhook Instagram: {e}")

                return {"status": "received"}

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported channel: {channel}")
        
        except Exception as e:
            print(f"❌ Error en webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.get("/")
    async def root():
        """Root endpoint"""
        # ... (tu código de endpoint)
        return {
            "message": "Integrado Omnicanal API",
            "version": "1.0.0",
            "endpoints": {
                "message": "/api/message",
                "calendar": "/api/calendar/schedule",
                "webhooks": "/webhook/{channel}",
                "health": "/health"
            }
        }

    @app.on_event("startup")
    async def startup_pollers():
        """Arranca pollers en segundo plano después de que FastAPI haya inicializado.

        Cargamos el script de polling de manera perezosa desde `scripts/instagram_bot_automation.py`
        para evitar problemas de orden de importación/circular imports durante la carga del módulo.
        """
        def instagram_worker():
            try:
                # Ruta relativa al root del repo: ../../.. desde src/integrado
                module_path = Path(__file__).resolve().parents[2] / "scripts" / "instagram_bot_automation.py"
                if not module_path.exists():
                    print(f"⚠️ No se encontró el módulo de automatización de Instagram en {module_path}")
                    return
                spec = importlib.util.spec_from_file_location("instagram_bot_automation", str(module_path))
                instagram_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(instagram_mod)
                run_continuous_loop = getattr(instagram_mod, 'run_continuous_loop', None)
                if run_continuous_loop is None:
                    print("⚠️ El script de Instagram no expone 'run_continuous_loop'. No se inicia poller.")
                    return
                # Iniciar poller de Instagram
                from integrado.run_instagram_poller import run_continuous_loop
                interval = int(os.getenv('INSTAGRAM_POLL_INTERVAL', os.getenv('INSTAGRAM_POLL_SECONDS', '30')))
                dry = os.getenv('INSTAGRAM_DRY_RUN', os.getenv('DRY_RUN', 'true')).lower() in ('1', 'true', 'yes')
                print(f"🔁 Startup: iniciando Instagram poller (interval={interval}s, dry_run={dry})")
                run_continuous_loop(interval_seconds=interval)
            except Exception as e:
                print(f"⚠️ Error al iniciar Instagram poller en startup: {e}")

        threading.Thread(target=instagram_worker, daemon=True).start()
# --- FIN DEL BLOQUE 'if not IS_TRAINING' ---


# --- 5. FUNCIONES CLI (FUERA DEL 'IF') ---
# Estas funciones deben estar disponibles para que 'crewai train' las llame
def run():
    """
    Run the crew (legacy function for crewAI CLI compatibility).
    """
    print("Starting Integrado Omnicanal Server...")
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # uvicorn.run necesita que 'app' exista cuando se importa
    # "integrado.main:app" le dice a uvicorn que cargue este archivo
    # y busque la variable 'app'.
    # Cuando uvicorn carga el archivo, IS_TRAINING será False,
    # por lo que 'app' se creará correctamente.
    uvicorn.run("integrado.main:app", host=host, port=port, reload=debug)

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "Omnicanal Communication",
        'current_year': str(datetime.now().year),
        
        # --- Variables que ya habías añadido ---
        'channel': 'whatsapp',  
        'user_id': 'user_123_entrenamiento', 
        'message': 'Hola, me gustaría agendar una cita para mañana.',
        
        # --- AÑADE LA NUEVA VARIABLE QUE FALTA AQUÍ ---
        'conversation_context': "El usuario acaba de iniciar la conversación." # O simplemente ""
    }
    try:
        integrado_crew.crew().train(
            n_iterations=int(sys.argv[1]), 
            filename=sys.argv[2], 
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        integrado_crew.crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "Omnicanal Communication",
        "current_year": str(datetime.now().year)
    }
    
    try:
        integrado_crew.crew().test(
            n_iterations=int(sys.argv[1]), 
            eval_llm=sys.argv[2], 
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_server():
    """
    Run the FastAPI server.
    """
    run()

# --- 6. BLOQUE MAIN (FUERA DEL 'IF') ---
if __name__ == "__main__":
    # Esto se ejecuta si corres 'python integrado/main.py'
    # En este caso, IS_TRAINING será False.
    run()