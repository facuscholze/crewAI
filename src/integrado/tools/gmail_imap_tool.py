from __future__ import annotations

import os
import re
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from typing import Optional, Type

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


load_dotenv()


def _normalize_reply_subject(subject: str | None) -> str:
    if not subject:
        return "Re:"
    # Remove any number of repeated Re:/RE:/re: prefixes
    cleaned = re.sub(r"^(?:(?:re|fw|fwd)\s*:\s*)+", "", subject, flags=re.IGNORECASE).strip()
    return f"Re: {cleaned}" if cleaned else "Re:"


class GmailConnectionMixin:
    def _get_imap_connection(self) -> imaplib.IMAP4_SSL:
        host = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
        port = int(os.getenv("EMAIL_IMAP_PORT", "993"))
        username = os.getenv("EMAIL_USERNAME")
        password = os.getenv("EMAIL_PASSWORD")
        if not username or not password:
            raise RuntimeError("EMAIL_USERNAME/EMAIL_PASSWORD no configurados")
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(username, password)
        return mail

    def _get_smtp_connection(self) -> smtplib.SMTP:
        host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        username = os.getenv("EMAIL_USERNAME")
        password = os.getenv("EMAIL_PASSWORD")
        if not username or not password:
            raise RuntimeError("EMAIL_USERNAME/EMAIL_PASSWORD no configurados")
        server = smtplib.SMTP(host, port)
        server.ehlo()
        server.starttls()
        server.login(username, password)
        return server

    def _find_email_by_message_id(self, message_id: str) -> Optional[email.message.Message]:
        if not message_id:
            return None
        conn = self._get_imap_connection()
        try:
            conn.select("INBOX")
            status, data = conn.search(None, f'HEADER Message-ID "<{message_id}>"')
            if status != "OK" or not data or not data[0]:
                return None
            ids = data[0].split()
            if not ids:
                return None
            status, msg_data = conn.fetch(ids[-1], "(RFC822)")
            if status != "OK":
                return None
            raw = msg_data[0][1]
            return email.message_from_bytes(raw)
        finally:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass


# =============== SEND REPLY TOOL ===============
class GmailSendReplyInput(BaseModel):
    to: str = Field(..., description="Email del destinatario")
    body: str = Field(..., description="Cuerpo del email en texto plano")
    subject: Optional[str] = Field(None, description="Asunto. Si no se da, se usa 'Re: <asunto original>'")
    reply_to_message_id: Optional[str] = Field(None, description="Message-ID del email original, sin <>")
    cc: Optional[str] = Field(None, description="Lista CC separada por comas")
    bcc: Optional[str] = Field(None, description="Lista BCC separada por comas")


class GmailIMAPAutoReplyTool(BaseTool, GmailConnectionMixin):
    name: str = "Gmail IMAP/SMTP Tool"
    description: str = (
        "Envía una respuesta por email en el mismo hilo usando In-Reply-To/References. "
        "Normaliza el asunto para evitar 'Re: Re:'."
    )
    args_schema: Type[BaseModel] = GmailSendReplyInput

    def _run(
        self,
        to: str,
        body: str,
        subject: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> str:
        from_addr = os.getenv("EMAIL_FROM") or os.getenv("EMAIL_USERNAME")
        if not from_addr:
            return "Error: EMAIL_FROM/EMAIL_USERNAME no configurados"

        original_subject = None
        if reply_to_message_id:
            original_msg = self._find_email_by_message_id(reply_to_message_id)
            if original_msg is not None:
                original_subject = original_msg.get("Subject")

        final_subject = _normalize_reply_subject(subject or original_subject or "")

        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = final_subject

        # Threading headers
        references_vals = []
        if reply_to_message_id:
            msg["In-Reply-To"] = f"<{reply_to_message_id}>"
            references_vals.append(f"<{reply_to_message_id}>")
            # Include older References if available
            if original_msg is not None:
                prev_refs = original_msg.get_all("References", [])
                for ref in prev_refs:
                    references_vals.append(ref)
        if references_vals:
            # Deduplicate while preserving order
            seen = set()
            deduped = []
            for ref in references_vals:
                if ref not in seen:
                    seen.add(ref)
                    deduped.append(ref)
            msg["References"] = " ".join(deduped)

        msg_id = make_msgid()
        msg["Message-ID"] = msg_id

        msg.attach(MIMEText(body, "plain", _charset="utf-8"))

        recipients = [to]
        if cc:
            recipients += [r.strip() for r in cc.split(",") if r.strip()]
        if bcc:
            recipients += [r.strip() for r in bcc.split(",") if r.strip()]

        try:
            server = self._get_smtp_connection()
            try:
                server.sendmail(from_addr, recipients, msg.as_string())
            finally:
                server.quit()
            return f"Email enviado a {to} con asunto '{final_subject}'."
        except Exception as e:
            return f"Error enviando email: {e}"


# =============== BASIC IMAP TOOL (connection + noop) ===============
class GmailIMAPTool(BaseTool, GmailConnectionMixin):
    name: str = "Gmail IMAP Tool"
    description: str = "Provee conexión IMAP y utilidades básicas."
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        try:
            conn = self._get_imap_connection()
            try:
                status, _ = conn.select("INBOX")
                return "Conexión IMAP OK" if status == "OK" else "Error abriendo INBOX"
            finally:
                conn.close()
                conn.logout()
        except Exception as e:
            return f"Error IMAP: {e}"


# =============== SEARCH TOOL (minimal) ===============
class GmailSearchInput(BaseModel):
    query: str = Field(..., description="Cadena de búsqueda IMAP, p.ej. 'UNSEEN' o 'FROM \"user@dominio\"'")


class GmailIMAPSearchTool(BaseTool, GmailConnectionMixin):
    name: str = "Gmail IMAP Search Tool"
    description: str = "Busca emails por un criterio IMAP y devuelve IDs encontrados."
    args_schema: Type[BaseModel] = GmailSearchInput

    def _run(self, query: str) -> str:
        try:
            conn = self._get_imap_connection()
            try:
                conn.select("INBOX")
                status, data = conn.search(None, query)
                if status != "OK":
                    return "Error en búsqueda IMAP"
                ids = data[0].decode("utf-8") if data and data[0] else ""
                return ids
            finally:
                conn.close()
                conn.logout()
        except Exception as e:
            return f"Error en búsqueda IMAP: {e}"


# =============== WEBHOOK PLACEHOLDER ===============
class GmailIMAPWebhookTool(BaseTool):
    name: str = "Gmail IMAP Webhook Tool"
    description: str = "Placeholder para procesamiento de webhooks/notificaciones push."
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        return "Webhook Gmail procesado"


