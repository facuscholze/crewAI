#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

# --- 1. IMPORTA TODO ARRIBA ---
# Importa todo lo que necesitas, sin condicionales
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import json
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
        
        if channel.lower() == "whatsapp":
            expected_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', '43833793')
            print(f"🔑 Token esperado: {expected_token}")
            print(f"🔑 Token recibido: {hub_verify_token}")
            print(f"🔑 Modo: {hub_mode}")
            
            if hub_mode == "subscribe" and hub_verify_token == expected_token:
                print(f"✅ WhatsApp webhook verificado exitosamente!")
                return int(hub_challenge)
            else:
                print(f"❌ Token de verificación incorrecto o modo inválido")
                print(f"   - Modo correcto: {hub_mode == 'subscribe'}")
                print(f"   - Token correcto: {hub_verify_token == expected_token}")
                raise HTTPException(status_code=403, detail="Forbidden")
        
        return {"status": "verified"}


    @app.post("/webhook/{channel}")
    async def webhook_handler(channel: str, request: Request):
        """Maneja webhooks de diferentes canales"""
        # ... (tu código de endpoint)
        try:
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
                                user_id = message.get('from', 'unknown')
                                message_text = message.get('text', {}).get('body', '')
                                message_type = message.get('type', 'text')
                                message_id = message.get('id', '')
                                
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