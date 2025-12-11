#!/usr/bin/env python3
"""
Script de automatización para responder mensajes no leídos de Instagram
Ejemplo de cómo usar las herramientas de Instagram para crear un bot automatizado
"""

import os
import time
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.integrado.tools.instagram_tool import (
        InstagramGetUnreadConversationsTool,
        InstagramGetMessagesTool,
        InstagramGetParticipantsTool,
        InstagramTool,
    )
except Exception:
    # Fallback to restored module if original is broken/empty
    from src.integrado.tools.instagram_tool_restored import (
        InstagramGetUnreadConversationsTool,
        InstagramGetMessagesTool,
        InstagramGetParticipantsTool,
        InstagramTool,
    )

# Cargar variables de entorno
load_dotenv()


def get_current_user_id():
    """Obtener el ID del usuario actual (dueño de la cuenta)"""
    import requests
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    
    url = "https://graph.facebook.com/v24.0/me"
    params = {
        'fields': 'id',
        'access_token': access_token
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            return result.get('id')
    except:
        pass
    
    return None


def get_other_participant(conversation_id, current_user_id=None):
    """Obtener el ID del otro participante (no el bot)"""
    import requests
    
    # Obtener participantes directamente desde la API
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    if not access_token:
        return None
    
    url = f"https://graph.facebook.com/v24.0/{conversation_id}"
    params = {
        'fields': 'participants',
        'access_token': access_token
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            participants = result.get('participants', {}).get('data', [])
            
            if not participants or len(participants) < 2:
                return None
            
            # Estrategia 1: Si tenemos current_user_id, buscar el que NO es el bot
            if current_user_id:
                current_user_id_str = str(current_user_id)
                for p in participants:
                    participant_id = str(p.get('id', ''))
                    if participant_id != current_user_id_str:
                        return participant_id
            
            # Estrategia 2: Intentar identificar el bot desde los mensajes
            try:
                messages_url = f"https://graph.facebook.com/v24.0/{conversation_id}/messages"
                messages_params = {
                    'fields': 'from',
                    'limit': 10,
                    'access_token': access_token
                }
                messages_response = requests.get(messages_url, params=messages_params)
                if messages_response.status_code == 200:
                    messages_result = messages_response.json()
                    messages = messages_result.get('data', [])
                    if messages:
                        # Contar mensajes por remitente
                        from_ids = {}
                        for msg in messages:
                            from_id = msg.get('from', {}).get('id')
                            if from_id:
                                from_ids[from_id] = from_ids.get(from_id, 0) + 1
                        
                        if from_ids:
                            bot_id = max(from_ids, key=from_ids.get)
                            bot_id_str = str(bot_id)
                            # Retornar el participante que NO es el bot
                            for p in participants:
                                participant_id = str(p.get('id', ''))
                                if participant_id != bot_id_str:
                                    return participant_id
            except:
                pass
            
            # Estrategia 3: En Instagram, generalmente el primer participante es el dueño (bot)
            # Entonces retornamos el segundo
            return str(participants[1].get('id', ''))
            
    except Exception as e:
        print(f"Error obteniendo participantes: {str(e)}")
        return None


def get_unread_conversations():
    """Obtener todas las conversaciones no leídas"""
    tool = InstagramGetUnreadConversationsTool()
    result = tool._run(limit=50)
    return result


def process_unread_conversations():
    """Procesar todas las conversaciones no leídas y responder automáticamente"""
    
    print("🤖 Bot de Instagram - Procesando mensajes no leídos")
    print("=" * 60)
    
    # Obtener conversaciones no leídas (limitado a 1 en desarrollo)
    tool = InstagramGetUnreadConversationsTool()
    result = tool._run()
    
    print(f"\n📋 Resultado:\n{result}\n")
    
    if not result:
        print("✅ No se encontraron conversaciones no leídas.")
        return

    # Obtener el id del bot para usar en heurísticas y enviar mensajes
    bot_id = get_current_user_id()

    for conv in result:
        try:
            conv_id = conv.get('id')
            print(f"➡️ Procesando conversation_id: {conv_id}")

            # Obtener destinatario (otro participante)
            recipient = get_other_participant(conv_id, current_user_id=bot_id)
            if not recipient:
                print(f"⚠️ No se pudo determinar el destinatario para {conv_id}, saltando.")
                continue

            # Obtener últimos mensajes para contexto
            messages_tool = InstagramGetMessagesTool()
            msgs = messages_tool._run(conversation_id=conv_id, limit=5)
            last_text = ''
            if msgs and isinstance(msgs, list) and len(msgs) > 0:
                last_text = msgs[0].get('message', '')

            # Obtener el historial completo de mensajes para contexto
            messages_tool = InstagramGetMessagesTool()
            all_msgs = messages_tool._run(conversation_id=conv_id, limit=50)
            
            # Construir el historial formateado para el contexto
            conversation_history = []
            if all_msgs and isinstance(all_msgs, list):
                for msg in reversed(all_msgs):  # Más antiguos primero
                    msg_text = msg.get('message', '')
                    msg_from = msg.get('from', {}).get('id', '')
                    is_bot = str(msg_from) == str(bot_id)
                    conversation_history.append(
                        f"{'🤖 Bot' if is_bot else '👤 Usuario'}: {msg_text}"
                    )
            
            # Obtener la respuesta usando el sistema Integrado con todo el contexto
            reply = None
            try:
                from integrado.crew import Integrado
                crew = Integrado()
                
                print(f"🚀 Procesando mensaje omnicanal: instagram - {recipient} - {last_text[:50]}...")
                
                # Llamada al procesamiento con contexto completo
                try:
                    # Llamada al procesamiento (Integrado obtendrá su propio contexto internamente)
                    response = crew.process_omnicanal_message(
                        channel='instagram',
                        user_id=recipient,
                        message=last_text,
                        message_type='text',
                        original_message_id=conv.get('id')
                    )
                    reply = str(response)
                except Exception as e:
                    print(f"⚠️ Error procesando con crew: {str(e)}")
                    reply = None
            except ImportError:
                print("⚠️ Módulo crew no disponible")
                reply = None
            except Exception as e:
                print(f"⚠️ Error inesperado: {str(e)}")
                reply = None

            if not reply:
                print("⚠️ No se pudo generar respuesta, usando respuesta por defecto")
                reply = f"Gracias por tu mensaje: {last_text[:240]}"

            # Enviar usando InstagramTool (respeta INSTAGRAM_DRY_RUN)
            sender_tool = InstagramTool()
            send_result = sender_tool._run(to=recipient, message=reply, message_type='text')
            print(f"📤 Envío: {send_result}")

            # Pequeña espera para respetar rate limits
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Error procesando conversación {conv}: {e}")
            continue
    
    print("✅ Procesamiento de conversaciones completado.")


def run_continuous_loop(interval_seconds=30):
    """Ejecutar en loop continuo verificando mensajes cada X segundos"""
    
    print(f"🔄 Iniciando loop continuo (verificando cada {interval_seconds} segundos)")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        while True:
            print(f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} - Verificando mensajes...")
            process_unread_conversations()
            print(f"\n💤 Esperando {interval_seconds} segundos hasta la próxima verificación...")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n\n✅ Bot detenido por el usuario")


def main():
    """Función principal"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Bot automatizado de Instagram')
    parser.add_argument(
        '--loop',
        action='store_true',
        help='Ejecutar en loop continuo'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Intervalo en segundos entre verificaciones (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Verificar token
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    if not access_token:
        print("❌ Error: Token de acceso no configurado")
        print("   Configura INSTAGRAM_ACCESS_TOKEN o FACEBOOK_ACCESS_TOKEN en .env")
        return
    
    if args.loop:
        run_continuous_loop(args.interval)
    else:
        process_unread_conversations()


if __name__ == "__main__":
    main()
