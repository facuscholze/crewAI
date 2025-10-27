#!/usr/bin/env python3
"""
Script unificado para iniciar Integrado Omnicanal con ngrok y servicio de Gmail.
"""

import os
import sys
import time
import subprocess
import requests
import threading
from pathlib import Path
from dotenv import load_dotenv

# ============================================
# 🔹 FUNCIONES NGROK + SERVIDOR FASTAPI
# ============================================

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 INTEGRADO OMNICANAL - INICIO AUTOMÁTICO                ║
║                                                              ║
║    Sistema Multiagente Omnicanal + Servicio Gmail IMAP       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def start_ngrok(port=8000):
    print(f"🌐 Iniciando ngrok en puerto {port}...")
    try:
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(5)
        response = requests.get('http://localhost:4040/api/tunnels', timeout=10)
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            if tunnels:
                public_url = tunnels[0]['public_url']
                print(f"✅ ngrok iniciado: {public_url}")
                return ngrok_process, public_url
        print("⚠️ No se pudo obtener URL automáticamente.")
        return ngrok_process, None
    except Exception as e:
        print(f"❌ Error iniciando ngrok: {e}")
        return None, None

def update_env_with_ngrok_url(public_url):
    if not public_url:
        return
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            updated_content = content.replace(
                'WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io',
                f'WEBHOOK_BASE_URL={public_url}'
            )
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Archivo .env actualizado con: {public_url}")
        except Exception as e:
            print(f"⚠️ Error actualizando .env: {e}")

def show_webhook_info(public_url):
    """Muestra las URLs de los distintos webhooks"""
    if public_url:
        print(f"\n🔗 URLs de Webhooks disponibles:")
        print(f"📱 WhatsApp:   {public_url}/webhook/whatsapp")
        print(f"💬 Messenger:  {public_url}/webhook/messenger")
        print(f"📸 Instagram:  {public_url}/webhook/instagram")
        print(f"📧 Gmail:      {public_url}/webhook/gmail")
        print(f"\n🌐 API:        {public_url}")
        print(f"📚 Docs:       {public_url}/docs\n")

def start_server():
    print("🚀 Iniciando servidor Integrado Omnicanal...")
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))
    try:
        from integrado.main import app
        import uvicorn
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '8000'))
        debug = os.getenv('DEBUG', 'True').lower() == 'true'
        print(f"🌐 Servidor iniciado en: http://{host}:{port}")
        print(f"📚 Documentación local:  http://{host}:{port}/docs")
        uvicorn.run("integrado.main:app", host=host, port=port, reload=debug)
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")

# ============================================
# 🔹 SERVICIO GMAIL (SIN PRINTS)
# ============================================

def gmail_service():
    """Servicio de verificación Gmail que corre en segundo plano."""
    import imaplib
    import email
    import re
    from email.header import decode_header
    from integrado.crew import Integrado
    from integrado.tools.gmail_imap_tool import GmailIMAPTool

    def decode_header_simple(header_value):
        if header_value is None:
            return ""
        decoded_string = ""
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string

    def get_email_body(email_message):
        if email_message.is_multipart():
            for part in email_message.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    try:
                        return part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        return part.get_payload(decode=True).decode('latin-1', errors='ignore')
            for part in email_message.walk():
                if part.get_content_type() == 'text/html' and 'attachment' not in cdispo:
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
            return ""
        else:
            return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

    def get_sender_email(sender_header):
        email_match = re.search(r'<(.+?)>', sender_header)
        if email_match:
            return email_match.group(1)
        else:
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', sender_header)
            return email_match.group(1) if email_match else sender_header

    load_dotenv()
    tool = GmailIMAPTool()
    integrado_crew = Integrado()

    while True:
        try:
            mail = tool._get_imap_connection()
            mail.select('INBOX')
            status, messages = mail.search(None, 'UNSEEN')
            if status == 'OK':
                email_ids = messages[0].split()
                for email_id in email_ids:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        sender_header = decode_header_simple(email_message['From'])
                        sender_email = get_sender_email(sender_header)
                        body_text = get_email_body(email_message)
                        original_message_id = email_message['Message-ID']
                        if original_message_id:
                            original_message_id = original_message_id.strip('<>')
                        integrado_crew.process_omnicanal_message(
                            channel='gmail',
                            user_id=sender_email,
                            message=body_text,
                            message_type="text",
                            original_message_id=original_message_id
                        )
                        mail.store(email_id, '+FLAGS', '\\Seen')
            mail.close()
            mail.logout()
        except:
            pass
        time.sleep(5)

# ============================================
# 🔹 FUNCIÓN PRINCIPAL
# ============================================

def main():
    print_banner()

    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    if not env_file.exists():
        env_example = project_root.parent / "env.example"
        if env_example.exists():
            import shutil
            shutil.copy2(env_example, env_file)
            print("✅ Archivo .env creado desde env.example")
        else:
            print("❌ Archivo env.example no encontrado")
            return

    port = 8000
    try:
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('PORT='):
                    port = int(line.split('=')[1].strip())
                    break
    except:
        pass

    ngrok_process, public_url = start_ngrok(port)
    if ngrok_process:
        update_env_with_ngrok_url(public_url)
        show_webhook_info(public_url)

    # Iniciar servicio Gmail en hilo aparte
    threading.Thread(target=gmail_service, daemon=True).start()

    # Iniciar servidor principal
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        if ngrok_process:
            ngrok_process.terminate()
        print("✅ Sistema detenido")

if __name__ == "__main__":
    main()
