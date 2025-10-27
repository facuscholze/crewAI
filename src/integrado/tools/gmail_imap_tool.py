# crewai_integrado/src/integrado/tools/gmail_imap_tool.py

from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import os
import re
from datetime import datetime, timedelta


class GmailIMAPMessageInput(BaseModel):
    """Input schema for Gmail IMAP message tool."""
    to: str = Field(..., description="Email address of the recipient")
    subject: str = Field(..., description="Subject of the email")
    body: str = Field(..., description="Body content of the email")
    body_type: str = Field(default="text", description="Type of body: text or html")
    reply_to_message_id: Optional[str] = Field(default=None, description="El 'Message-ID' del email original al que se está respondiendo para seguir el hilo.")


class GmailIMAPSearchInput(BaseModel):
    """Input schema for Gmail IMAP search tool."""
    search_criteria: str = Field(default="UNSEEN", description="Search criteria (UNSEEN, ALL, FROM, SUBJECT, etc.)")
    max_messages: int = Field(default=10, description="Maximum number of messages to retrieve")


class GmailIMAPTool(BaseTool):
    name: str = "Gmail IMAP/SMTP Tool"
    description: str = (
        "Send and receive emails through Gmail using IMAP/SMTP protocols. "
        "Supports sending emails, reading inbox, and managing email conversations."
    )
    args_schema: Type[BaseModel] = GmailIMAPMessageInput

    def _run(self, to: str, subject: str, body: str, body_type: str = "text", reply_to_message_id: Optional[str] = None) -> str:
        """Send email through Gmail SMTP."""
        
        try:
            # Get SMTP configuration
            smtp_host = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
            username = os.getenv('EMAIL_USERNAME')
            password = os.getenv('EMAIL_PASSWORD')
            from_email = os.getenv('EMAIL_FROM', username)
            
            if not username or not password:
                return "❌ Error: Gmail credentials not configured (EMAIL_USERNAME, EMAIL_PASSWORD)"
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            # --- MODIFICACIÓN PARA SEGUIMIENTO DE HILO ---
            # Si se provee un reply_to_message_id, lo usamos para seguir el hilo
            if reply_to_message_id:
                msg['In-Reply-To'] = reply_to_message_id
                msg['References'] = reply_to_message_id
            # --- FIN DE LA MODIFICACIÓN ---

            # Add body content
            if body_type == "html":
                html_part = MIMEText(body, 'html', 'utf-8')
                msg.attach(html_part)
            else:
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            if reply_to_message_id:
                return f"✅ Respuesta enviada exitosamente a {to}\n📧 Asunto: {subject}\n🔗 Siguiendo hilo: {reply_to_message_id}"
            else:
                return f"✅ Email enviado exitosamente a {to}\n📧 Asunto: {subject}"
            
        except Exception as e:
            return f"❌ Error enviando email: {str(e)}"

    def _get_imap_connection(self):
        """Get IMAP connection to Gmail."""
        imap_host = os.getenv('EMAIL_IMAP_HOST', 'imap.gmail.com')
        imap_port = int(os.getenv('EMAIL_IMAP_PORT', '993'))
        username = os.getenv('EMAIL_USERNAME')
        password = os.getenv('EMAIL_PASSWORD')
        
        if not username or not password:
            raise Exception("Gmail credentials not configured")
        
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(username, password)
        return mail


class GmailIMAPSearchTool(BaseTool):
    name: str = "Gmail IMAP Search Tool"
    description: str = (
        "Search and retrieve emails from Gmail inbox using IMAP protocol."
    )
    args_schema: Type[BaseModel] = GmailIMAPSearchInput

    def _run(self, search_criteria: str = "UNSEEN", max_messages: int = 10) -> str:
        """Search emails in Gmail inbox."""
        
        try:
            gmail_tool = GmailIMAPTool()
            mail = gmail_tool._get_imap_connection()
            
            # Select inbox
            mail.select('INBOX')
            
            # Search emails
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                return "❌ Error buscando emails"
            
            email_ids = messages[0].split()
            
            if not email_ids:
                return f"📧 No se encontraron emails con criterio: {search_criteria}"
            
            # Get latest messages
            email_ids = email_ids[-max_messages:] if len(email_ids) > max_messages else email_ids
            
            emails_info = []
            
            for email_id in email_ids:
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Decode subject
                        subject = self._decode_header(email_message['Subject'])
                        
                        # Decode sender
                        sender = self._decode_header(email_message['From'])
                        
                        # Get date
                        date = email_message['Date']
                        
                        # --- MODIFICACIÓN PARA OBTENER MESSAGE-ID ---
                        # Extraer el Message-ID para poder responder
                        message_id = email_message['Message-ID']
                        if message_id:
                            # Limpiar el Message-ID (a veces vienen con < >)
                            message_id = message_id.strip('<>')
                        # --- FIN DE LA MODIFICACIÓN ---

                        emails_info.append({
                            'id': email_id.decode(),
                            'message_id': message_id, # <-- Añadido
                            'subject': subject,
                            'from': sender,
                            'date': date
                        })
                        
                except Exception as e:
                    continue
            
            mail.close()
            mail.logout()
            
            if not emails_info:
                return "📧 No se pudieron procesar los emails"
            
            result = f"📧 **{len(emails_info)} emails encontrados:**\n\n"
            for email_info in emails_info:
                result += f"• **{email_info['subject']}**\n"
                result += f"  👤 De: {email_info['from']}\n"
                result += f"  📅 Fecha: {email_info['date']}\n"
                result += f"  🆔 Message-ID: {email_info['message_id']}\n\n" # <-- Añadido
            
            return result
            
        except Exception as e:
            return f"❌ Error buscando emails: {str(e)}"

    def _decode_header(self, header_value):
        """Decode email header."""
        if header_value is None:
            return "Sin asunto"
        
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string


class GmailIMAPAutoReplyTool(BaseTool):
    name: str = "Gmail IMAP Auto Reply Tool"
    description: str = (
        "Automatically reply to unread emails in Gmail inbox."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Auto-reply to unread emails."""
        
        try:
            gmail_tool = GmailIMAPTool()
            mail = gmail_tool._get_imap_connection()
            
            # Select inbox
            mail.select('INBOX')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                return "❌ Error buscando emails no leídos"
            
            email_ids = messages[0].split()
            
            if not email_ids:
                return "📧 No hay emails no leídos para responder"
            
            replied_count = 0
            
            for email_id in email_ids:
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Get sender
                        sender = self._decode_header(email_message['From'])
                        subject = self._decode_header(email_message['Subject'])
                        
                        # --- MODIFICACIÓN PARA SEGUIMIENTO DE HILO ---
                        # Extraer el Message-ID para responder
                        original_message_id = email_message['Message-ID']
                        if original_message_id:
                            original_message_id = original_message_id.strip('<>')
                        # --- FIN DE LA MODIFICACIÓN ---

                        # Extract email address from sender
                        email_match = re.search(r'<(.+?)>', sender)
                        if email_match:
                            sender_email = email_match.group(1)
                        else:
                            # Try to extract email from the string
                            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', sender)
                            sender_email = email_match.group(1) if email_match else sender
                        
                        # Create auto-reply
                        reply_subject = f"Re: {subject}" if not subject.startswith('Re:') else subject
                        reply_body = f"""Hola,

Gracias por contactarnos. Hemos recibido tu mensaje y te responderemos lo antes posible.

Tu mensaje original:
{subject}

Saludos cordiales,
Sistema Integrado Omnicanal
"""
                        
                        # Send reply
                        result = gmail_tool._run(
                            to=sender_email,
                            subject=reply_subject,
                            body=reply_body,
                            body_type="text",
                            reply_to_message_id=original_message_id # <-- Añadido
                        )
                        
                        if "✅" in result:
                            replied_count += 1
                            # Mark original email as read
                            mail.store(email_id, '+FLAGS', '\\Seen')
                        
                except Exception as e:
                    continue
            
            mail.close()
            mail.logout()
            
            return f"✅ Auto-respuesta enviada a {replied_count} emails"
            
        except Exception as e:
            return f"❌ Error en auto-respuesta: {str(e)}"

    def _decode_header(self, header_value):
        """Decode email header."""
        if header_value is None:
            return "Sin asunto"
        
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string


class GmailIMAPWebhookTool(BaseTool):
    name: str = "Gmail IMAP Webhook Tool"
    description: str = (
        "Process incoming Gmail notifications and trigger appropriate responses."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Process Gmail webhook notifications."""
        
        # Check if auto-reply is enabled
        auto_reply = os.getenv('EMAIL_AUTO_REPLY', 'false').lower() == 'true'
        
        if auto_reply:
            auto_reply_tool = GmailIMAPAutoReplyTool()
            return auto_reply_tool._run()
        else:
            return "📧 Auto-respuesta deshabilitada. Revisa EMAIL_AUTO_REPLY en configuración."