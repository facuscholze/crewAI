#!/usr/bin/env python

import os
import sys
import warnings
import threading
from queue import Queue
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# ==================== ENV ====================
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# ==================== FLAGS ====================
IS_CLI = any(cmd in " ".join(sys.argv) for cmd in ["replay", "test"])

# ==================== CREW ====================
integrado_crew = None

def get_crew():
    global integrado_crew
    if integrado_crew is None:
        from integrado.crew import Integrado
        integrado_crew = Integrado()
    return integrado_crew

# ==================== COLA + WORKER ====================
message_queue: Queue = Queue(maxsize=1000)
processing_messages: set[str] = set()


def crew_worker():
    print("🧵 Worker CrewAI iniciado")
    while True:
        item = message_queue.get()
        if item is None:
            break
        key = item["key"]
        try:
            crew = get_crew()
            crew.process_omnicanal_message(
                channel=item["channel"],
                user_id=item["user_id"],
                message=item["message"],
                message_type=item.get("message_type", "text"),
            )
        except Exception as e:
            print(f"❌ Error procesando {key}: {e}")
        finally:
            processing_messages.discard(key)
            message_queue.task_done()

# ==================== WHATSAPP AUDIO ====================
def transcribe_whatsapp_audio_message(message: Dict) -> Optional[str]:
    try:
        token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        if not token:
            return None
        media_id = message.get("audio", {}).get("id")
        if not media_id:
            return None
        meta = requests.get(
            f"https://graph.facebook.com/v18.0/{media_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        ).json()
        media_url = meta.get("url")
        if not media_url:
            return None
        audio = requests.get(
            media_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        ).content
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return None
        resp = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {openai_key}"},
            files={"file": ("audio.ogg", audio, "audio/ogg")},
            data={"model": "whisper-1", "language": "es"},
            timeout=120,
        )
        return resp.json().get("text")
    except Exception:
        return None

# ==================== FASTAPI ====================
if not IS_CLI:
    app = FastAPI(title="Integrado Omnicanal API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==================== MODELS ====================
    class MessageRequest(BaseModel):
        channel: str
        user_id: str
        message: str
        message_type: str = "text"

    class CalendarEventRequest(BaseModel):
        user_id: str
        title: str
        description: str
        start_datetime: str
        end_datetime: str
        attendees: Optional[List[str]] = None
        location: Optional[str] = None
        timezone: str = "UTC"

    # ==================== STARTUP ====================
    @app.on_event("startup")
    async def startup():
        threading.Thread(target=crew_worker, daemon=True).start()

        def instagram_worker():
            try:
                from integrado.run_instagram_poller import run_continuous_loop
                run_continuous_loop(int(os.getenv("INSTAGRAM_POLL_SECONDS", "30")))
            except Exception:
                pass
        threading.Thread(target=instagram_worker, daemon=True).start()

    # ==================== API ====================
    @app.post("/api/message")
    async def process_message(req: MessageRequest):
        key = f"{req.channel}:{req.user_id}:{req.message}"
        if key in processing_messages or message_queue.full():
            return {"status": "ignored"}
        processing_messages.add(key)
        message_queue.put({
            "key": key,
            "channel": req.channel,
            "user_id": req.user_id,
            "message": req.message,
            "message_type": req.message_type,
        })
        return {"status": "queued"}

    @app.post("/api/calendar/schedule")
    async def schedule_event(req: CalendarEventRequest):
        key = f"calendar:{req.user_id}:{req.title}:{req.start_datetime}"
        if key in processing_messages or message_queue.full():
            return {"status": "ignored"}
        processing_messages.add(key)
        message_queue.put({
            "key": key,
            "channel": "calendar",
            "user_id": req.user_id,
            "message": req.dict(),
            "message_type": "calendar",
        })
        return {"status": "queued"}

    # ==================== WEBHOOK VERIFY ====================
    @app.get("/webhook/{channel}")
    async def verify_webhook(
        channel: str,
        hub_mode: str = Query(None, alias="hub.mode"),
        hub_challenge: str = Query(None, alias="hub.challenge"),
        hub_verify_token: str = Query(None, alias="hub.verify_token"),
    ):
        expected = os.getenv(
            f"{channel.upper()}_WEBHOOK_VERIFY_TOKEN",
            os.getenv("WEBHOOK_VERIFY_TOKEN", "43833793"),
        )
        if hub_mode == "subscribe" and hub_verify_token == expected:
            return PlainTextResponse(str(hub_challenge))
        raise HTTPException(status_code=403)

    # ==================== WEBHOOK HANDLER ====================
    @app.post("/webhook/{channel}")
    async def webhook_handler(channel: str, request: Request):
        data = await request.json()

        if channel == "whatsapp":
            messages = (
                data.get("entry", [{}])[0]
                .get("changes", [{}])[0]
                .get("value", {})
                .get("messages", [])
            )
            for msg in messages:
                if "from" not in msg:
                    continue
                user = msg["from"]
                msg_id = msg.get("id", "")
                msg_type = msg.get("type", "text")
                text = msg.get("text", {}).get("body", "")
                if msg_type in ("audio", "voice") or msg.get("audio"):
                    text = transcribe_whatsapp_audio_message(msg) or "[mensaje de voz]"
                    msg_type = "text"
                key = f"wa:{user}:{msg_id}:{text}"
                if key in processing_messages or message_queue.full():
                    continue
                processing_messages.add(key)
                message_queue.put({
                    "key": key,
                    "channel": "whatsapp",
                    "user_id": user,
                    "message": text,
                    "message_type": msg_type,
                })
            return {"status": "queued"}

        raise HTTPException(status_code=400, detail="Unsupported channel")

    # ==================== HEALTH ====================
    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "queue": message_queue.qsize(),
            "time": datetime.now().isoformat(),
        }

# ==================== CLI ====================
def run():
    uvicorn.run(
        "integrado.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "true").lower() == "true",
    )


def replay():
    crew = get_crew()
    crew.crew().replay(task_id=sys.argv[1])


def test():
    crew = get_crew()
    crew.crew().test(
        n_iterations=int(sys.argv[1]),
        eval_llm=sys.argv[2],
        inputs={
            "topic": "Omnicanal Communication",
            "current_year": str(datetime.now().year),
        },
    )

# ==================== MAIN ====================
if __name__ == "__main__":
    if "replay" in sys.argv:
        replay()
    elif "test" in sys.argv:
        test()
    else:
        run()
