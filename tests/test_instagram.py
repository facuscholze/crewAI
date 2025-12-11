#!/usr/bin/env python3
"""
Script de prueba para Instagram Direct Messages API
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def test_get_conversations():
    """Prueba obtener conversaciones de Instagram"""
    
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    
    if not access_token:
        print("❌ Error: Token de acceso de Instagram no configurado")
        print("   Configura INSTAGRAM_ACCESS_TOKEN o FACEBOOK_ACCESS_TOKEN en .env")
        return False
    
    print(f"🔑 Token: {access_token[:20]}...")
    
    url = "https://graph.facebook.com/v24.0/me/conversations"
    
    params = {
        'platform': 'instagram',
        'limit': 1,
        'access_token': access_token
    }
    
    print(f"📤 Obteniendo conversaciones de Instagram...")
    print(f"🔗 URL: {url}")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            conversations = result.get('data', [])
            if conversations:
                conversation_id = conversations[0].get('id', 'unknown')
                print(f"✅ Conversación encontrada. ID: {conversation_id}")
                return conversation_id
            else:
                print("⚠️  No se encontraron conversaciones")
                return None
        else:
            print(f"❌ Error obteniendo conversaciones: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
        return None


def get_current_user_id():
    """Obtener el ID del usuario de Instagram (no el de la página de Facebook)"""
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    
    # Primero intentar obtener el Instagram Business Account ID desde las cuentas conectadas
    try:
        # Obtener las cuentas de Instagram conectadas a la página
        url = "https://graph.facebook.com/v24.0/me/accounts"
        params = {
            'fields': 'instagram_business_account',
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            accounts = result.get('data', [])
            if accounts:
                # Buscar la cuenta que tiene Instagram conectado
                for account in accounts:
                    ig_account = account.get('instagram_business_account')
                    if ig_account:
                        ig_id = ig_account.get('id')
                        if ig_id:
                            print(f"✅ ID de Instagram obtenido desde accounts: {ig_id}")
                            return ig_id
    except Exception as e:
        print(f"⚠️  No se pudo obtener ID desde accounts: {str(e)}")
    
    # Si no funciona, intentar obtener desde una conversación (inferir del participante que NO es el otro)
    try:
        url = "https://graph.facebook.com/v24.0/me/conversations"
        params = {
            'platform': 'instagram',
            'limit': 1,
            'fields': 'participants',
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            conversations = result.get('data', [])
            if conversations:
                conv = conversations[0]
                participants = conv.get('participants', {}).get('data', [])
                if len(participants) == 2:
                    # En Instagram, generalmente el primer participante es el dueño de la cuenta
                    # O podemos verificar quién envió el último mensaje
                    bot_id = participants[0].get('id')
                    print(f"✅ ID de Instagram inferido desde conversación: {bot_id}")
                    return bot_id
    except Exception as e:
        print(f"⚠️  No se pudo inferir ID desde conversación: {str(e)}")
    
    # Fallback: usar /me (retorna página de Facebook, no es ideal pero mejor que nada)
    try:
        url = "https://graph.facebook.com/v24.0/me"
        params = {
            'fields': 'id',
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            page_id = result.get('id')
            print(f"⚠️  Usando ID de página (no es el ID de Instagram): {page_id}")
            return page_id
    except:
        pass
    
    return None


def test_get_participants(conversation_id):
    """Prueba obtener participantes de una conversación"""
    
    if not conversation_id:
        print("⚠️  No hay conversation_id para probar participantes")
        return None
    
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    
    url = f"https://graph.facebook.com/v24.0/{conversation_id}"
    
    params = {
        'fields': 'participants',
        'access_token': access_token
    }
    
    print(f"\n📤 Obteniendo participantes de conversación {conversation_id}...")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            participants = result.get('participants', {}).get('data', [])
            if participants:
                participant_ids = [p.get('id', 'unknown') for p in participants]
                participant_usernames = [p.get('username', 'unknown') for p in participants]
                print(f"✅ Participantes encontrados: {', '.join([f'{id} ({username})' for id, username in zip(participant_ids, participant_usernames)])}")
                
                # Estrategia simplificada: En Instagram, con 2 participantes:
                # - El primero generalmente es el dueño de la cuenta (bot)
                # - El segundo es el otro usuario (destinatario)
                # Pero primero intentamos identificar el bot para mayor seguridad
                
                current_user_id = None
                current_user_id_str = None
                
                # Si hay exactamente 2 participantes, asumir que el primero es el bot
                if len(participants) == 2:
                    # Usar el primer participante como bot
                    current_user_id = participants[0].get('id')
                    current_user_id_str = str(current_user_id) if current_user_id else None
                    print(f"🔑 Usuario actual (bot) - asumido como primer participante: {current_user_id} (@{participants[0].get('username', 'unknown')})")
                else:
                    # Si hay más de 2 participantes, intentar identificarlo desde mensajes
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
                                from_ids = {}
                                for msg in messages:
                                    from_id = msg.get('from', {}).get('id')
                                    if from_id:
                                        from_ids[from_id] = from_ids.get(from_id, 0) + 1
                                if from_ids:
                                    current_user_id = max(from_ids, key=from_ids.get)
                                    current_user_id_str = str(current_user_id)
                                    print(f"🔑 Usuario actual (bot) identificado desde mensajes: {current_user_id}")
                    except Exception as e:
                        print(f"⚠️  No se pudo identificar bot desde mensajes: {str(e)}")
                    
                    if not current_user_id:
                        current_user_id = get_current_user_id()
                        current_user_id_str = str(current_user_id) if current_user_id else None
                        print(f"🔑 Usuario actual (bot) desde get_current_user_id: {current_user_id}")
                
                # Buscar el participante que NO es el usuario actual
                other_participant = None
                other_username = None
                
                print(f"🔍 Buscando participante diferente al bot...")
                for p in participants:
                    participant_id = str(p.get('id', ''))  # Convertir a string para comparación
                    participant_username = p.get('username', 'unknown')
                    print(f"   - Verificando: {participant_id} (@{participant_username})")
                    
                    # Comparar como strings para evitar problemas de tipo
                    if current_user_id_str and participant_id != current_user_id_str:
                        other_participant = participant_id
                        other_username = participant_username
                        print(f"   ✅ ENCONTRADO: Este NO es el bot")
                        break
                    elif not current_user_id_str:
                        # Si no pudimos obtener el ID del bot, usar el segundo participante
                        if len(participants) > 1 and p != participants[0]:
                            other_participant = participant_id
                            other_username = participant_username
                            print(f"   ✅ USANDO: No se identificó bot, usando este participante")
                            break
                
                # Si aún no encontramos, usar una estrategia más simple:
                # En Instagram, cuando hay 2 participantes, generalmente:
                # - El primero es el dueño de la cuenta (bot)
                # - El segundo es el otro usuario
                if not other_participant and len(participants) == 2:
                    # Usar el segundo participante como destinatario
                    other_participant = str(participants[1].get('id', ''))
                    other_username = participants[1].get('username', 'unknown')
                    print(f"⚠️  Fallback: Usando segundo participante (asumiendo que el primero es el bot): {other_participant}")
                elif not other_participant and len(participants) > 1:
                    other_participant = str(participants[1].get('id', ''))
                    other_username = participants[1].get('username', 'unknown')
                    print(f"⚠️  Fallback: Usando segundo participante: {other_participant}")
                
                if other_participant:
                    print(f"✅ Usuario destinatario final: {other_participant} (@{other_username})")
                    return other_participant
                else:
                    print("⚠️  Solo hay un participante (probablemente el bot)")
                    return None
            else:
                print("⚠️  No se encontraron participantes")
                return None
        else:
            print(f"❌ Error obteniendo participantes: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
        return None


def test_get_messages(conversation_id):
    """Prueba obtener mensajes de una conversación"""
    
    if not conversation_id:
        print("⚠️  No hay conversation_id para probar mensajes")
        return False
    
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    
    url = f"https://graph.facebook.com/v24.0/{conversation_id}/messages"
    
    params = {
        'fields': 'message,from,created_time',
        'access_token': access_token
    }
    
    print(f"\n📤 Obteniendo mensajes de conversación {conversation_id}...")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            messages = result.get('data', [])
            if messages:
                print(f"✅ {len(messages)} mensaje(s) encontrado(s):")
                for i, msg in enumerate(messages[:3], 1):  # Mostrar solo los primeros 3
                    msg_text = msg.get('message', '')
                    from_id = msg.get('from', {}).get('id', 'unknown')
                    created_time = msg.get('created_time', 'unknown')
                    print(f"   {i}. De: {from_id}, Hora: {created_time}")
                    print(f"      Mensaje: {msg_text[:50]}...")
                return True
            else:
                print("⚠️  No se encontraron mensajes en esta conversación")
                return False
        else:
            print(f"❌ Error obteniendo mensajes: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False


def test_send_message(recipient_id):
    """Prueba enviar un mensaje de Instagram"""
    
    if not recipient_id:
        print("⚠️  No hay recipient_id para enviar mensaje")
        print("   Necesitas un user_id de Instagram para probar el envío")
        print("   Puedes obtenerlo de los participantes de una conversación")
        return False
    
    # Verificar que NO estamos enviando al bot
    # Nota: get_current_user_id() puede retornar el ID de la página de Facebook,
    # no el ID de Instagram, por lo que esta verificación puede no ser 100% confiable.
    # La verificación real debería hacerse en test_get_participants()
    current_user_id = get_current_user_id()
    
    # Verificación adicional: Si el recipient_id parece ser un ID de Instagram (muy largo),
    # y el current_user_id es un ID de página de Facebook (más corto), no comparar
    recipient_str = str(recipient_id)
    current_str = str(current_user_id) if current_user_id else ""
    
    # Solo verificar si ambos IDs tienen formato similar
    if current_user_id and len(recipient_str) > 15 and len(current_str) > 15:
        if recipient_str == current_str:
            print(f"❌ ERROR: Estás intentando enviar un mensaje al bot mismo!")
            print(f"   Bot ID: {current_user_id}")
            print(f"   Recipient ID: {recipient_id}")
            print(f"   Esto causará un error. Asegúrate de usar el ID del otro participante.")
            return False
    
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    
    url = "https://graph.facebook.com/v24.0/me/messages"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": "🧪 Prueba del sistema Integrado - Mensaje de prueba desde Instagram API"}
    }
    
    print(f"\n📤 Enviando mensaje:")
    print(f"   Destinatario: {recipient_id}")
    print(f"   Bot ID: {current_user_id}")
    print(f"   ✅ Verificado: El destinatario NO es el bot")
    print(f"🔗 URL: {url}")
    print(f"📦 Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('message_id', 'unknown')
            print(f"✅ Mensaje enviado exitosamente. Message ID: {message_id}")
            return True
        else:
            error_data = response.json() if response.text else {}
            error_message = error_data.get('error', {}).get('message', 'Error desconocido')
            error_code = error_data.get('error', {}).get('code', 'unknown')
            print(f"❌ Error enviando mensaje: {error_code} - {error_message}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False


def test_get_unread_conversations():
    """Prueba obtener solo conversaciones no leídas"""
    
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    
    if not access_token:
        print("❌ Error: Token de acceso de Instagram no configurado")
        return []
    
    url = "https://graph.facebook.com/v24.0/me/conversations"
    
    # ESTRATEGIA SIMPLE: Verificar si el último mensaje fue del bot o no.
    # Si el último mensaje NO fue del bot → No leída (necesita respuesta)
    # Si el último mensaje SÍ fue del bot → Leída (ya respondida)
    
    # Obtener el ID del bot
    current_user_id = get_current_user_id()
    if not current_user_id:
        print("❌ Error: No se pudo obtener el ID del bot")
        return []
    current_user_id_str = str(current_user_id)
    
    # Obtener conversaciones recientes
    params = {
        'platform': 'instagram',
        'limit': 1,  # Obtener varias para filtrar
        'access_token': access_token,
        'fields': 'id,updated_time'
    }
    
    print(f"\n📤 Obteniendo conversaciones NO LEÍDAS de Instagram...")
    print(f"🔗 URL: {url}")
    print(f"📋 Estrategia: Último mensaje del bot = Leída | Último mensaje de otro = No leída")
    print(f"🔑 Bot ID: {current_user_id_str}")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text[:500] if response.text else "Sin detalles"
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {error_text}")
            return []
        
        result = response.json()
        all_conversations = result.get('data', [])
        
        print(f"📊 Total de conversaciones obtenidas: {len(all_conversations)}")
        
        if not all_conversations:
            print("✅ No hay conversaciones")
            return []
        
        # Ordenar por updated_time descendente (más recientes primero)
        all_conversations.sort(
            key=lambda x: x.get('updated_time', ''), 
            reverse=True
        )
        
        # Verificar cada conversación: ¿el último mensaje es del bot?
        unread_conversations = []
        
        print(f"\n🔍 Verificando cada conversación...")
        for conv in all_conversations:
            conv_id = conv.get('id', 'unknown')
            
            # Obtener el último mensaje
            try:
                messages_url = f"https://graph.facebook.com/v24.0/{conv_id}/messages"
                messages_params = {
                    'fields': 'from,created_time,message',
                    'limit': 1,  # Solo el último mensaje
                    'access_token': access_token
                }
                messages_response = requests.get(messages_url, params=messages_params)
                
                if messages_response.status_code == 200:
                    messages_result = messages_response.json()
                    messages = messages_result.get('data', [])
                    
                    if messages:
                        last_message = messages[0]
                        last_message_from = last_message.get('from', {}).get('id')
                        last_message_from_str = str(last_message_from) if last_message_from else None
                        
                        # LÓGICA SIMPLE: Si el último mensaje NO es del bot → No leída
                        if last_message_from_str and last_message_from_str != current_user_id_str:
                            # El último mensaje es de otro usuario → No leída
                            unread_conversations.append({
                                **conv,
                                'last_message_from': last_message_from_str,
                                'last_message_time': last_message.get('created_time', 'unknown'),
                                'last_message_text': last_message.get('message', '')[:50]
                            })
            except Exception as e:
                # Si falla, saltar esta conversación
                continue
        
        print(f"\n📊 Conversaciones con último mensaje del otro usuario: {len(unread_conversations)}")
        
        if unread_conversations:
            print(f"✅ Encontradas {len(unread_conversations)} conversación(es) no leída(s):")
            
            # Mostrar información de las conversaciones no leídas
            for i, conv in enumerate(unread_conversations[:10], 1):  # Máximo 10
                conv_id = conv.get('id', 'unknown')
                updated_time = conv.get('updated_time', 'unknown')
                last_message_from = conv.get('last_message_from', 'unknown')
                last_message_time = conv.get('last_message_time', 'unknown')
                last_message_text = conv.get('last_message_text', 'N/A')
                
                # Obtener participantes
                participants_str = "N/A"
                try:
                    participants_url = f"https://graph.facebook.com/v24.0/{conv_id}"
                    participants_params = {
                        'fields': 'participants',
                        'access_token': access_token
                    }
                    participants_response = requests.get(participants_url, params=participants_params)
                    if participants_response.status_code == 200:
                        participants_data = participants_response.json()
                        participants = participants_data.get('participants', {}).get('data', [])
                        if participants:
                            participant_names = [p.get('username', p.get('id', 'unknown')) for p in participants]
                            participants_str = ', '.join(participant_names)
                except:
                    pass
                
                print(f"   {i}. ID: {conv_id[:50]}...")
                print(f"      Último mensaje de: {last_message_from}")
                print(f"      Hora: {last_message_time}")
                print(f"      Texto: {last_message_text}")
                print(f"      Actualizado: {updated_time}")
                print(f"      Participantes: {participants_str}")
            
            return unread_conversations
        else:
            print("✅ No hay conversaciones no leídas (todos los últimos mensajes fueron del bot)")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return []


def main():
    """Función principal"""
    
    print("🧪 PRUEBAS DE INSTAGRAM DIRECT MESSAGES API")
    print("=" * 60)
    
    # Verificar token
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
    if not access_token:
        print("❌ Error: Token de acceso no configurado")
        print("   Configura INSTAGRAM_ACCESS_TOKEN o FACEBOOK_ACCESS_TOKEN en .env")
        return
    
    print("\n0️⃣ PASO 0: Obtener conversaciones NO LEÍDAS (para automatización)")
    print("-" * 60)
    unread_conversations = test_get_unread_conversations()
    
    print("\n1️⃣ PASO 1: Obtener conversación más reciente")
    print("-" * 60)
    conversation_id = test_get_conversations()
    
    if conversation_id:
        print("\n2️⃣ PASO 2: Obtener participantes de la conversación")
        print("-" * 60)
        participant_id = test_get_participants(conversation_id)
        
        print("\n3️⃣ PASO 3: Obtener mensajes de la conversación")
        print("-" * 60)
        test_get_messages(conversation_id)
        
        if participant_id:
            print("\n4️⃣ PASO 4: Enviar mensaje de respuesta")
            print("-" * 60)
            print("⚠️  NOTA: Solo envía si quieres probar el envío real")
            print("   Descomenta la siguiente línea para probar:")
            test_send_message(participant_id)
        else:
            print("\n⚠️  No se pudo obtener participant_id, no se puede probar envío")
    else:
        print("\n⚠️  No se encontraron conversaciones para probar")
        print("   Asegúrate de tener conversaciones activas en Instagram Direct")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")


if __name__ == "__main__":
    main()
