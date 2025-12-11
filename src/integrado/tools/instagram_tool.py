from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, List, Any
import os
import time
import requests  # Necesario para las excepciones
from .api_client import get_request, post_request


class InstagramMessageInput(BaseModel):
	to: str = Field(..., description="Instagram recipient id")
	message: str = Field(..., description="Message text to send")
	message_type: str = Field(default="text", description="Type of message")


class InstagramTool(BaseTool):
	name: str = "Instagram Message Tool"
	description: str = "Send messages via Instagram (minimal implementation)."
	args_schema: Type[BaseModel] = InstagramMessageInput

	def _run(self, to: str, message: str, message_type: str = "text") -> str:
		access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
		# Respectar modo dry-run para pruebas: si INSTAGRAM_DRY_RUN está activo, no enviar realmente
		dry_run_val = os.getenv('INSTAGRAM_DRY_RUN', os.getenv('DRY_RUN', 'true')).lower()
		dry_run = dry_run_val in ('1', 'true', 'yes')
		if dry_run:
			print("\n📝 [MODO DRY-RUN ACTIVO]")
			print(f"👤 Destinatario: {to}")
			print(f"💬 Mensaje: {message[:200]}")
			print("✅ Simulación completada")
			return f"[DRY-RUN] Mensaje simulado a {to}"
		if not access_token:
			return "Error: INSTAGRAM_ACCESS_TOKEN/ FACEBOOK_ACCESS_TOKEN no configurado"

		# Enviar mensaje directamente usando el ID recibido (PSID)
		url = "https://graph.facebook.com/v24.0/me/messages"
		headers = {
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/json"
		}

		payload = {
			"recipient": {"id": to},
			"message": {"text": message}
		}

		try:
			print(f"\n📤 Enviando mensaje a Instagram...")
			print(f"🔗 URL: {url}")
			print(f"👤 Destinatario ID: {to}")
			print(f"💬 Mensaje: {message[:100]}...")

			resp = post_request(url, json=payload, headers=headers)
			print(f"📊 Status Code: {resp.status_code}")

			if resp.status_code == 200:
				print("✅ Mensaje enviado exitosamente")
				return f"Mensaje enviado a {to}"
			else:
				error_text = resp.text[:500] if resp.text else "Sin detalles"
				print(f"❌ Error: {resp.status_code}")
				print(f"📄 Response: {error_text}")
				return f"Error enviando mensaje: {resp.status_code} - {error_text}"
		except requests.RequestException as e:
			print(f"❌ Error de conexión: {str(e)}")
			return f"Error de conexión al enviar mensaje: {e}"
		except Exception as e:
			error_text = str(e)
			print(f"❌ Error al enviar mensaje: {error_text}")
			return f"Error al enviar mensaje: {error_text}"


class InstagramWebhookTool(BaseTool):
	name: str = "Instagram Webhook Tool"
	description: str = "Process incoming Instagram webhook (placeholder)."
	args_schema: Type[BaseModel] = BaseModel

	def _run(self) -> str:
		return "Instagram webhook processed"


class InstagramGetConversationsTool(BaseTool):
	name: str = "Instagram Get Conversations"
	description: str = "Return a list of recent conversations from Instagram."
	args_schema: Type[BaseModel] = BaseModel

	def _run(self, limit: int = 1) -> List[Any]:
		access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
		if not access_token:
			return []

		url = "https://graph.facebook.com/v24.0/me/conversations"
		params = {"platform": "instagram", "limit": limit, "access_token": access_token}
		try:
			resp = get_request(url, params=params)
			if resp.status_code == 200:
				return resp.json().get('data', [])
		except requests.RequestException:
			pass
		return []


class InstagramGetUnreadConversationsTool(BaseTool):
	name: str = "Instagram Get Unread Conversations"
	description: str = "Return conversations whose last message was not sent by the bot."
	args_schema: Type[BaseModel] = BaseModel

	def _get_current_user_id(self) -> Optional[str]:
		access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
		if not access_token:
			return None
		# Try accounts -> instagram_business_account
		try:
			url = "https://graph.facebook.com/v24.0/me/accounts"
			params = {"fields": "instagram_business_account", "access_token": access_token}
			# Usar proxy HTTPS público para mejorar conectividad
			proxies = {
				'https': 'https://proxy.scrapeops.io/v1/?api_key=YOUR_API_KEY_HERE&url=https://graph.facebook.com',
			}
			r = requests.get(url, params=params, timeout=30, proxies=proxies)
			if r.status_code == 200:
				data = r.json().get('data', [])
				for acc in data:
					ig = acc.get('instagram_business_account')
					if ig and ig.get('id'):
						return str(ig.get('id'))
		except requests.RequestException:
			pass

		# Fallback: infer from conversations
		try:
			url = "https://graph.facebook.com/v24.0/me/conversations"
			params = {"platform": "instagram", "limit": 1, "fields": "participants", "access_token": access_token}
			r = get_request(url, params=params)
			if r.status_code == 200:
				convs = r.json().get('data', [])
				if convs:
					parts = convs[0].get('participants', {}).get('data', [])
					if len(parts) >= 1:
						return str(parts[0].get('id'))
		except requests.RequestException:
			pass

		# Last fallback: /me id
		try:
			url = "https://graph.facebook.com/v24.0/me"
			params = {"fields": "id", "access_token": access_token}
			r = requests.get(url, params=params, timeout=30)
			if r.status_code == 200:
				return str(r.json().get('id'))
		except requests.RequestException:
			pass

		return None

	def _run(self) -> List[dict]:
		"""Obtener solo conversaciones no leídas usando la misma lógica que test_instagram.py"""
		access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
		if not access_token:
			print("❌ Error: Token de acceso de Instagram no configurado")
			return []

		url = "https://graph.facebook.com/v24.0/me/conversations"
        
		# Obtener el ID del bot
		current_user_id = self._get_current_user_id()
		if not current_user_id:
			print("❌ Error: No se pudo obtener el ID del bot")
			return []
		current_user_id_str = str(current_user_id)
        
		# Obtener conversaciones recientes
		params = {
			'platform': 'instagram',
			'limit': 1,
			'access_token': access_token,
			'fields': 'id,updated_time'
		}
        
		print(f"\n📤 Obteniendo conversaciones NO LEÍDAS de Instagram...")
		print(f"🔗 URL: {url}")
		print(f"📋 Estrategia: Último mensaje del bot = Leída | Último mensaje de otro = No leída")
		print(f"🔑 Bot ID: {current_user_id_str}")
        
		try:
			response = get_request(url, params=params)
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
			all_conversations.sort(key=lambda x: x.get('updated_time', ''), reverse=True)
            
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
					messages_response = get_request(messages_url, params=messages_params)
                    
					if messages_response.status_code == 200:
						messages_result = messages_response.json()
						messages = messages_result.get('data', [])
                        
						if messages:
							last_message = messages[0]
							last_message_from = last_message.get('from', {}).get('id')
							last_message_from_str = str(last_message_from) if last_message_from else None
                            
							print(f"   - Conversación {conv_id[:30]}...")
							print(f"     Último mensaje de: {last_message_from_str}")
							print(f"     Bot ID: {current_user_id_str}")
                            
                # LÓGICA SIMPLE: Si el último mensaje NO es del bot → No leída
							if last_message_from_str and last_message_from_str != current_user_id_str:
								# El último mensaje es de otro usuario → No leída
								print(f"     ✅ No leída: último mensaje de otro usuario")
								unread_conversations.append({
									**conv,
									'last_message_from': last_message_from_str,
									'last_message_time': last_message.get('created_time', 'unknown'),
									'last_message_text': last_message.get('message', '')[:50],
									'user_id': last_message_from_str,  # Agregar user_id
									'message': last_message.get('message', ''),  # Mensaje completo sin truncar
									'message_type': 'text'  # Por defecto es mensaje de texto
								})
							else:
								print(f"     ❌ Leída: último mensaje del bot")
				except Exception as e:
					print(f"     ⚠️ Error procesando conversación: {str(e)}")
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
						participants_response = get_request(participants_url, params=participants_params)
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


class InstagramGetParticipantsTool(BaseTool):
	name: str = "Instagram Get Participants"
	description: str = "Return participants for a conversation."
	args_schema: Type[BaseModel] = BaseModel

	def _run(self, conversation_id: Optional[str] = None) -> List[dict]:
		if not conversation_id:
			return []
		access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
		if not access_token:
			return []
		url = f"https://graph.facebook.com/v24.0/{conversation_id}"
		params = {"fields": "participants", "access_token": access_token}
		try:
			r = requests.get(url, params=params, timeout=30)
			if r.status_code == 200:
				return r.json().get('participants', {}).get('data', [])
		except requests.RequestException:
			pass
		return []


class InstagramGetMessagesTool(BaseTool):
	name: str = "Instagram Get Messages"
	description: str = "Return messages for a conversation."
	args_schema: Type[BaseModel] = BaseModel

	def _run(self, conversation_id: Optional[str] = None, limit: int = 1) -> List[dict]:
		if not conversation_id:
			return []
		access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', os.getenv('FACEBOOK_ACCESS_TOKEN'))
		if not access_token:
			return []
		url = f"https://graph.facebook.com/v24.0/{conversation_id}/messages"
		params = {"fields": "message,from,created_time", "limit": limit, "access_token": access_token}
		try:
			r = requests.get(url, params=params, timeout=30)
			if r.status_code == 200:
				return r.json().get('data', [])
		except requests.RequestException:
			pass
		return []

