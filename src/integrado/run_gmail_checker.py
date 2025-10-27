# C:\Users\Facu\Desktop\todo integrado\integrado\src\integrado\run_gmail_checker.py

import time
import os
import imaplib
import email
import re
from email.header import decode_header
from dotenv import load_dotenv

# Importa la clase principal de tu Crew y la herramienta de conexión
from integrado.crew import Integrado
from integrado.tools.gmail_imap_tool import GmailIMAPTool

# Cargar las variables de entorno (.env)
load_dotenv()

def decode_header_simple(header_value):
    """Función simple para decodificar encabezados de email."""
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
    """Extrae el cuerpo de texto plano o HTML del email."""
    if email_message.is_multipart():
        for part in email_message.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    return part.get_payload(decode=True).decode('latin-1', errors='ignore')
        # Si no se encuentra texto plano, tomar el HTML
        for part in email_message.walk():
            if part.get_content_type() == 'text/html' and 'attachment' not in cdispo:
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        return "" # No se encontró cuerpo legible
    else:
        # No es multipart, tomar el payload principal
        return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

def get_sender_email(sender_header):
    """Extrae la dirección de email limpia del encabezado 'From'."""
    email_match = re.search(r'<(.+?)>', sender_header)
    if email_match:
        return email_match.group(1)
    else:
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', sender_header)
        return email_match.group(1) if email_match else sender_header

def mark_all_as_read(tool_for_connection):
    """Marca todos los emails "UNSEEN" como "Seen" al inicio."""
    print("Iniciando limpieza: Marcando todos los emails existentes como leídos...")
    try:
        mail = tool_for_connection._get_imap_connection()
        mail.select('INBOX')
        status, messages = mail.search(None, 'UNSEEN')
        if status == 'OK':
            email_ids = messages[0].split()
            if email_ids:
                print(f"Se encontraron {len(email_ids)} emails no leídos. Marcándolos como leídos...")
                for email_id in email_ids:
                    mail.store(email_id, '+FLAGS', '\\Seen')
                print(f"Limpieza completada. {len(email_ids)} emails antiguos han sido marcados.")
            else:
                print("No se encontraron emails no leídos. ¡La bandeja ya estaba limpia!")
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"❌ Error durante la limpieza de emails: {str(e)}")

def process_new_emails(integrado_crew, tool_for_connection):
    """Busca nuevos emails y los pasa al CrewAI para que los procese."""
    print(f"[{time.ctime()}] Buscando emails NUEVOS...")
    try:
        mail = tool_for_connection._get_imap_connection()
        mail.select('INBOX')
        
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            print("Error buscando emails.")
            mail.close()
            mail.logout()
            return

        email_ids = messages[0].split()
        if not email_ids:
            print(f"[{time.ctime()}] Resultado: No hay emails nuevos.")
            mail.close()
            mail.logout()
            return
        
        print(f"[{time.ctime()}] ¡Se encontraron {len(email_ids)} email(s) nuevo(s)!")

        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extraer información clave
                    sender_header = decode_header_simple(email_message['From'])
                    sender_email = get_sender_email(sender_header)
                    
                    body_text = get_email_body(email_message)
                    
                    original_message_id = email_message['Message-ID']
                    if original_message_id:
                        original_message_id = original_message_id.strip('<>')
                    
                    print(f"  -> Procesando email de: {sender_email} (ID: {original_message_id})")
                    
                    # --- ¡AQUÍ OCURRE LA MAGIA! ---
                    # Llamamos al CrewAI principal para que maneje la respuesta
                    result = integrado_crew.process_omnicanal_message(
                        channel='gmail',
                        user_id=sender_email,
                        message=body_text,
                        message_type="text",
                        original_message_id=original_message_id
                    )
                    
                    print(f"  -> CrewAI finalizó. Resultado: {result}")
                    
                    # Marcamos como leído DESPUÉS de procesarlo
                    mail.store(email_id, '+FLAGS', '\\Seen')
                    print(f"  -> Email (ID: {email_id}) marcado como leído.")

            except Exception as e:
                print(f"❌ Error procesando email ID {email_id}: {e}")
                # Marcar como leído igualmente para evitar bucles de error
                mail.store(email_id, '+FLAGS', '\\Seen')
        
        mail.close()
        mail.logout()

    except Exception as e:
        print(f"❌ Error en el bucle principal de revisión: {str(e)}")


if __name__ == "__main__":
    
    print("--- Servicio de Gmail con CrewAI iniciado ---")
    
    # Instanciamos la herramienta solo para usar su método de conexión
    tool = GmailIMAPTool()
    
    # 1. Limpiamos la bandeja de entrada ANTES de empezar
    mark_all_as_read(tool)
    
    # 2. Instanciamos el Crew principal UNA SOLA VEZ
    print("Iniciando instancia de Integrado Crew...")
    try:
        integrado_crew = Integrado()
        print("✅ CrewAI listo.")
    except Exception as e:
        print(f"❌ ERROR FATAL: No se pudo instanciar Integrado Crew: {e}")
        print("El script no puede continuar. Revisa la configuración de tu crew.")
        exit(1)

    # 3. Iniciamos el bucle para esperar emails nuevos
    print(f"[{time.ctime()}] Iniciando bucle de espera de nuevos emails...")
    print("Presiona Ctrl+C para detener.")
    
    while True:
        try:
            process_new_emails(integrado_crew, tool)
        except Exception as e:
            print(f"❌ Un error inesperado ocurrió en el bucle 'while True': {e}")
            
        sleep_duration = 5 # Espera 60 segundos
        time.sleep(sleep_duration)