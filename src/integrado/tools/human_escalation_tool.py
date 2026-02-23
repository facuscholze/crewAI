"""
Herramienta para escalamiento humano en conversaciones (Omnicanal Segura)
"""
import logging
from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict
from pydantic import BaseModel, Field
import os
import re  # Agregamos Regex para detectar teléfonos mejor
from datetime import datetime
from openai import OpenAI
from .whatsapp_tool import WhatsAppTool
from .runtime_context import current_user_id, current_channel

logger = logging.getLogger(__name__)

# Cache simple para evitar escalamientos duplicados (últimos 5 minutos)
_escalation_cache = {}

class HumanEscalationInput(BaseModel):
    """Input schema for human escalation."""
    user_id: str = Field(..., description="Phone number or ID of the user")
    user_message: str = Field(..., description="The message that triggered the escalation request")
    reason: str = Field(default="user_requested", description="Reason for escalation")

class HumanEscalationTool(BaseTool):
    name: str = "Human Escalation Tool"
    description: str = (
        "Escalate conversation to a human agent. "
        "CRITICAL: If the conversation is NOT on WhatsApp (e.g. Instagram/Web), this tool will check "
        "if a phone number has been provided. If not, it will return an instruction for you to ask for it."
    )
    args_schema: Type[BaseModel] = HumanEscalationInput

    def _run(self, user_id: str, user_message: str, reason: str = "user_requested") -> str:
        """Escalate conversation to human agent."""
        
        # 1. Obtener contexto y canal
        safe_user_id = current_user_id() or user_id
        channel = current_channel() or "whatsapp"
        
        logger.info(f"Procesando escalamiento - Canal: {channel} | User: {safe_user_id}")

        # 2. Variables iniciales
        recent_messages = []
        user_info = {}
        recent_context_lines = []
        
        # Regex para buscar teléfonos (Argentina, Uruguay y general)
        # Busca números de 8-15 dígitos, opcionalmente con prefijos +54, 54, 0, +598, 598
        phone_pattern = r'\b(?:\+?(?:54|598)|0)?[\s.-]?\d[\d\s.-]{6,14}\d\b'
        
        def extract_phone(text):
            if not text: return None
            matches = re.findall(phone_pattern, text)
            # Filtra números que parecen precios (ej 15.000) y valida longitud
            valid_phones = []
            for match in matches:
                # Limpiar el número de espacios y caracteres
                clean = re.sub(r'[\s.-]', '', match)
                # Debe tener entre 8 y 15 dígitos sin caracteres especiales
                if 8 <= len(clean) <= 15 and not '.' in match:
                    valid_phones.append(match.strip())
            return valid_phones[0] if valid_phones else None

        # 3. Importación DIFERIDA de la DB (Para evitar el error de 'Integrado')
        try:
            # ---> AQUÍ ESTÁ EL TRUCO: Importamos dentro de la función <---
            from ..database.mongodb_conversation import mongodb_conversation_db
            from datetime import timedelta
            
            # Obtener más historial para filtrar
            all_messages = mongodb_conversation_db.get_conversation_history(safe_user_id, limit=50)
            
            # FILTRAR SOLO MENSAJES DE LA SESIÓN ACTUAL (últimas 2 horas)
            cutoff_time = datetime.now() - timedelta(hours=2)
            recent_messages = []
            
            for msg in all_messages:
                msg_timestamp = msg.get("timestamp")
                # Si el mensaje tiene timestamp y es reciente, incluirlo
                if msg_timestamp:
                    try:
                        if isinstance(msg_timestamp, str):
                            msg_time = datetime.fromisoformat(msg_timestamp.replace('Z', '+00:00'))
                        else:
                            msg_time = msg_timestamp
                        
                        if msg_time > cutoff_time:
                            recent_messages.append(msg)
                    except:
                        # Si hay error parseando timestamp, incluir últimos mensajes
                        pass
            
            # Si no hay mensajes recientes o el filtro no funcionó, tomar últimos 5
            if not recent_messages and all_messages:
                recent_messages = all_messages[-5:]
            
            # Iterar por mensajes de la SESIÓN ACTUAL (no mezclar con conversaciones viejas)
            for msg in recent_messages[-10:]:  # Solo últimos 10 de la sesión actual
                role = "Cliente" if msg.get("type") == "human" else "Bot"
                content = msg.get("data", {}).get("content", "") or msg.get("content", "")
                
                if content:
                    recent_context_lines.append(f"{role}: {content[:100]}")
                
                # Buscar datos en el historial
                if msg.get("type") == "human":
                    content_lower = content.lower()
                    
                    # Buscar teléfono en mensajes anteriores
                    if not user_info.get('telefono'):
                        found = extract_phone(content)
                        if found: user_info['telefono'] = found
                    
                    # Buscar Tratamientos (Tu lógica original)
                    treatments = ["botox", "relleno", "lifting", "depilación", "limpieza", "facial", "masaje", "acupuntura"]
                    for t in treatments:
                        if t in content_lower and not user_info.get('tratamiento'):
                            user_info['tratamiento'] = t.title()
                            break

        except ImportError:
            logger.warning("No se pudo importar la DB (ImportError). Usando solo mensaje actual.")
        except Exception as e:
            logger.warning(f"Error obteniendo contexto reciente: {e}")

        # 4. Buscar teléfono en el mensaje ACTUAL (Prioridad)
        current_msg_phone = extract_phone(user_message)
        if current_msg_phone:
            user_info['telefono'] = current_msg_phone

        # 5. Si aún no hay teléfono, buscar en los metadatos de la conversación
        if not user_info.get('telefono'):
            try:
                from ..database.mongodb_conversation import mongodb_conversation_db
                conversation_meta = mongodb_conversation_db.get_conversation_metadata(safe_user_id)
                if conversation_meta and conversation_meta.get('metadata', {}).get('telefono'):
                    user_info['telefono'] = conversation_meta['metadata']['telefono']
                    logger.info(f"Teléfono recuperado de metadata: {user_info['telefono']}")
            except Exception as e:
                logger.warning(f"No se pudieron obtener metadatos: {e}")

        # ==============================================================================
        # 6. BLOQUEO DE SEGURIDAD (LA LÓGICA DE INSTAGRAM QUE PEDISTE)
        # ==============================================================================
        if channel != "whatsapp" and not user_info.get('telefono'):
            logger.info(f"Bloqueo: Canal {channel} sin teléfono. Solicitando al agente que pregunte.")
            return (
                f"⚠️ NO SE PUEDE ESCALAR AÚN. Estás hablando por {channel.upper()} y no tenemos un número de contacto.\n"
                "👉 ACCIÓN REQUERIDA: Responde al cliente amablemente pidiéndole su número de WhatsApp "
                "para que el especialista pueda contactarlo. NO inventes que ya escalaste."
            )
        # ==============================================================================

        # 7. Verificar Cache (Anti-spam)
        now = datetime.now()
        if safe_user_id in _escalation_cache:
            last = _escalation_cache[safe_user_id]
            if (now - last).total_seconds() < 45:
                logger.info(f"Escalamiento reciente para {safe_user_id}, evitando duplicado")
                return f"✅ Ya se escaló recientemente. Sigue hablando con el cliente."
        
       

        # 8. Generar Resumen con IA
        # Mantenemos tu firma de función original para que no rompa nada
        context_summary = self._generate_escalation_summary(recent_messages, user_message, user_info, recent_context_lines)

        # 9. Construir Notificación
        clinic_number = os.getenv('HUMAN_ESCALATION_NUMBER', '543755629953')
        
        contact_display = safe_user_id
        if channel != "whatsapp":
            contact_display = f"{user_info.get('telefono')} (vía {channel})"

        notification_message = f"""🚨 *ESCALAMIENTO A HUMANO*

👤 *Cliente:* {contact_display}
🔗 *Canal:* {channel.upper()}
💬 *Último mensaje:* {user_message[:200]}

"""
        if context_summary:
            notification_message += f"*📋 Resumen IA:*\n{context_summary}\n\n"
        
        notification_message += f"⏰ *Hora:* {datetime.now().strftime('%H:%M')}\n"
        notification_message += "💡 *Acción:* Contactar al cliente vía WhatsApp."

        # 10. Enviar WhatsApp a la clínica
        try:
            whatsapp_tool = WhatsAppTool()
            result = whatsapp_tool._run(to=clinic_number, message=notification_message, message_type="text")
            
            if "successfully" in result.lower() or "queued" in result.lower():
                 # Registrar y limpiar cache
                _escalation_cache[safe_user_id] = now
                if len(_escalation_cache) > 100: _escalation_cache.clear()
                
                # Formatear número de la clínica para mostrarlo al cliente
                formatted_clinic = clinic_number
                if clinic_number.startswith('54') and len(clinic_number) >= 10:
                    formatted_clinic = f"+{clinic_number[:2]} {clinic_number[2:5]} {clinic_number[5:]}"
                
                logger.info(f"Escalamiento exitoso a {clinic_number}")
                return f"✅ Escalamiento exitoso. Te van a contactar al número que nos diste desde el {formatted_clinic}."
            else:
                return f"⚠️ Problema enviando notificación: {result}. Sigue atendiendo."
        except Exception as e:
            logger.error(f"Error en escalamiento: {str(e)}")
            return f"⚠️ Error técnico al notificar ({str(e)}). Sigue atendiendo."

    def _generate_escalation_summary(self, recent_messages: List, user_message: str, user_info: Dict, recent_context_lines: List) -> str:
        """Genera resumen usando OpenAI (Tu implementación mejorada)"""
        try:
            # Tomar solo los últimos mensajes de la CONVERSACIÓN ACTUAL (no mezclar con historiales viejos)
            chat_history_text = "\n".join(recent_context_lines[-8:])
            
            system_prompt = """
            Eres supervisor de una clínica estética. Resume SOLO la conversación ACTUAL (no menciones temas de conversaciones pasadas).
            Resumen en 1 párrafo fluido (máx 40 palabras):
            1. INTENCIÓN: ¿Qué busca en ESTA conversación?
            2. DOLOR/MOTIVO: ¿Qué dolor o consulta específica tiene HOY?
            3. ESTADO: ¿Qué información se le dio?
            
            IMPORTANTE: NO incluyas temas de conversaciones anteriores. Solo resume lo que se habló EN ESTA SESIÓN.
            """
            
            user_prompt = f"""
            --- CONVERSACIÓN ACTUAL (últimos mensajes) ---
            {chat_history_text}
            --- FIN DE CONVERSACIÓN ACTUAL ---
            
            Último mensaje del cliente: "{user_message}"
            
            Resume SOLO lo que se habló en esta conversación. No menciones temas antiguos.
            """

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key: return f"Cliente pide humano. Msg: '{user_message}'"

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.3, max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error LLM al generar resumen de escalamiento: {e}")
            return f"El cliente solicita atención humana. Mensaje: '{user_message}'"

class CheckEscalationStatusInput(BaseModel):
    user_id: str = Field(..., description="User ID")

class CheckEscalationStatusTool(BaseTool):
    name: str = "Check Escalation Status"
    description: str = "Check if a conversation has been escalated."
    args_schema: Type[BaseModel] = CheckEscalationStatusInput

    def _run(self, user_id: str) -> str:
        safe_user_id = current_user_id() or user_id
        if safe_user_id in _escalation_cache:
            elapsed = (datetime.now() - _escalation_cache[safe_user_id]).total_seconds()
            if elapsed < 300:
                return f"Escalación activa hace {int(elapsed)}s."
        return "No hay escalamiento activo."