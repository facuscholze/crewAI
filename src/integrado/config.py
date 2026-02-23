"""
Centralized configuration module.
Reads all environment variables in one place so the rest of the codebase
can import settings from here instead of scattering os.getenv() calls.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── WhatsApp ─────────────────────────────────────────────────────────────────
WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "43833793")

# ── Instagram / Facebook ─────────────────────────────────────────────────────
INSTAGRAM_ACCESS_TOKEN: str = os.getenv(
    "INSTAGRAM_ACCESS_TOKEN", os.getenv("FACEBOOK_ACCESS_TOKEN", "")
)
INSTAGRAM_DRY_RUN: bool = os.getenv(
    "INSTAGRAM_DRY_RUN", os.getenv("DRY_RUN", "true")
).lower() in ("1", "true", "yes")
INSTAGRAM_POLL_SECONDS: int = int(os.getenv("INSTAGRAM_POLL_SECONDS", "30"))
FB_ACCESS_TOKEN: str = os.getenv("FB_ACCESS_TOKEN", "")
FB_VERIFY_TOKEN: str = os.getenv("FB_VERIFY_TOKEN", "profisio_verify_2025")

# ── Gmail ────────────────────────────────────────────────────────────────────
EMAIL_IMAP_HOST: str = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
EMAIL_IMAP_PORT: int = int(os.getenv("EMAIL_IMAP_PORT", "993"))
EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

# ── Google Calendar ──────────────────────────────────────────────────────────
GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "./credenciales.json"
)
CALENDAR_ID: str = os.getenv("CALENDAR_ID", "primary")

# ── ElevenLabs ───────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")

# ── OpenAI ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "sqlite:///./integrado_conversations.db"
)
CONVERSATION_DB_PATH: str = os.getenv(
    "CONVERSATION_DB_PATH", "./integrado_conversations.db"
)

# ── Escalation ───────────────────────────────────────────────────────────────
HUMAN_ESCALATION_NUMBER: str = os.getenv(
    "HUMAN_ESCALATION_NUMBER", "+543755629953"
)

# ── Server ───────────────────────────────────────────────────────────────────
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

# ── Webhook ──────────────────────────────────────────────────────────────────
WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "43833793")
