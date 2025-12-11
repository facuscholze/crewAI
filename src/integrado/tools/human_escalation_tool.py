"""
Herramienta para escalamiento humano en conversaciones
"""
from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict
from pydantic import BaseModel, Field
import os
import requests
from datetime import datetime, timedelta
from .whatsapp_tool import WhatsAppTool

# Cache simple para evitar escalamientos duplicados (últimos 5 minutos)
_escalation_cache = {}  # {user_id: timestamp}


class HumanEscalationInput(BaseModel):
    """Input schema for human escalation."""
    user_id: str = Field(..., description="Phone number of the user requesting human assistance")
    user_message: str = Field(..., description="The message that triggered the escalation request")
    conversation_summary: str = Field(default="", description="Brief summary of the conversation context")
    reason: str = Field(default="user_requested", description="Reason for escalation")


class HumanEscalationTool(BaseTool):
    name: str = "Human Escalation Tool"
    description: str = (
        "Escalate conversation to a human agent when the user explicitly requests it or when the bot cannot handle the request. "
        "This tool sends a notification message to the clinic's WhatsApp number (543755585557) with customer information and conversation context. "
        "Use this when user says ANY of these phrases: 'hablar con un humano', 'hablar con una persona', 'derivarme con una persona', "
        "'derivar con alguien', 'escalar', 'no me sirve', 'quiero que me atienda una persona', 'necesito hablar con alguien', "
        "'pueden derivarme', 'derivarme', 'hablar con alguien real', or any variation asking to speak with a human/person. "
        "After escalation, the bot should continue responding normally to the user."
    )
    args_schema: Type[BaseModel] = HumanEscalationInput

    def _run(
        self, 
        user_id: str, 
        user_message: str, 
        conversation_summary: str = "", 
        reason: str = "user_requested"
    ) -> str:
        """Escalate conversation to human agent."""
        
        # Verificar si ya se escaló recientemente (últimos 5 minutos)
        now = datetime.now()
        if user_id in _escalation_cache:
            last_escalation = _escalation_cache[user_id]
            if (now - last_escalation).total_seconds() < 300:  # 5 minutos
                print(f"⚠️ Escalamiento reciente detectado para {user_id}, evitando duplicado")
                return f"✅ Ya se escaló esta conversación recientemente. El bot continuará respondiendo al cliente."
        
        print(f"🚨 ESCALAMIENTO A HUMANO DETECTADO")
        print(f"   Usuario: {user_id}")
        print(f"   Mensaje: {user_message}")
        
        # Registrar escalamiento
        _escalation_cache[user_id] = now
        
        # Limpiar cache antiguo (más de 10 minutos)
        _escalation_cache.clear() if len(_escalation_cache) > 100 else None
        
        # Número de la clínica para notificaciones
        clinic_number = os.getenv('HUMAN_ESCALATION_NUMBER', '54375515585557')
        print(f"   Enviando notificación a: {clinic_number}")
        
        # Inicializar variables para contexto reciente
        recent_messages = []
        user_info = {}
        recent_context_lines = []
        
        # Obtener información adicional del contexto RECIENTE (últimos mensajes)
        try:
            from ..database.mongodb_conversation import mongodb_conversation_db
            
            # Obtener solo los últimos mensajes (últimos 5 para contexto reciente)
            recent_messages = mongodb_conversation_db.get_conversation_history(user_id, limit=5)
            
            # Extraer información relevante SOLO de los últimos mensajes
            for msg in recent_messages:
                if msg.get("type") == "human":
                    content = msg.get("data", {}).get("content", "")
                    if content:
                        recent_context_lines.append(f"👤 Usuario: {content[:100]}")
                        
                        # Extraer información válida solo si parece ser un dato estructurado
                        content_lower = content.lower()
                        
                        # Detectar teléfono (solo si parece un número de teléfono, no un mensaje completo)
                        if any(char.isdigit() for char in content) and len(content.replace(" ", "")) >= 8 and len(content) < 20:
                            # Validar que no sea un mensaje completo
                            if not any(word in content_lower for word in ["masajes", "tratamiento", "precio", "cita", "agendar"]):
                                user_info['telefono'] = content.strip()
                        
                        # Detectar tratamientos SOLO en los últimos mensajes
                        treatments = ["botox", "relleno", "lifting", "depilación", "limpieza", "facial", "masaje", "acupuntura"]
                        for treatment in treatments:
                            if treatment in content_lower and not user_info.get('tratamiento'):
                                # Solo si el tratamiento se menciona en contexto reciente
                                user_info['tratamiento'] = treatment.title()
                                break
                        
                        # Detectar días preferidos
                        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                        for day in days:
                            if day in content_lower:
                                user_info['dia'] = day.title()
                                break
                
                elif msg.get("type") == "ai":
                    content = msg.get("data", {}).get("content", "")
                    if content:
                        recent_context_lines.append(f"🤖 Bot: {content[:100]}")
            
            # Si no hay mensajes recientes o muy pocos, no incluir información antigua
            if len(recent_messages) < 2:
                user_info = {}  # Limpiar si hay muy pocos mensajes recientes
            
        except Exception as e:
            print(f"⚠️ Error obteniendo contexto reciente: {e}")
            recent_context_lines = []
            user_info = {}
        
        # Generar resumen explicativo del contexto y razón del escalamiento
        context_summary = self._generate_escalation_summary(recent_messages, user_message, user_info, recent_context_lines)
        
        # Construir mensaje de notificación para la clínica
        notification_message = f"""🚨 *ESCALAMIENTO A HUMANO*

*Cliente solicitando atención humana:*

📱 *Número del cliente:* {user_id}
💬 *Último mensaje:* {user_message[:200]}

"""
        
        # Agregar resumen explicativo del contexto
        if context_summary:
            notification_message += f"*📋 Resumen del contexto y ayuda necesaria:*\n{context_summary}\n\n"
        
        # Agregar información del contexto RECIENTE solo si es relevante
        if user_info and len(recent_messages) >= 2:
            notification_message += "*Información reciente del cliente:*\n"
            # Solo incluir teléfono si parece válido (no un mensaje completo)
            if user_info.get('telefono') and len(user_info['telefono']) < 20:
                notification_message += f"📞 Teléfono: {user_info['telefono']}\n"
            # Solo incluir tratamiento si se mencionó en los últimos mensajes
            if user_info.get('tratamiento'):
                notification_message += f"💉 Tratamiento mencionado: {user_info['tratamiento']}\n"
            if user_info.get('dia'):
                notification_message += f"📅 Día preferido: {user_info['dia']}\n"
            notification_message += "\n"
        
        # El resumen explicativo ya contiene toda la información necesaria, no necesitamos el historial de mensajes
        
        notification_message += f"⏰ *Hora de escalamiento:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        notification_message += f"🔗 *Razón:* {reason}\n\n"
        notification_message += "💡 *Acción requerida:* Iniciar conversación con el cliente en WhatsApp."
        
        # Enviar mensaje usando WhatsAppTool
        try:
            whatsapp_tool = WhatsAppTool()
            result = whatsapp_tool._run(
                to=clinic_number,
                message=notification_message,
                message_type="text"
            )
            
            print(f"   Resultado del envío: {result}")
            
            if "successfully" in result.lower() or "queued" in result.lower():
                print(f"✅ ESCALAMIENTO EXITOSO - Notificación enviada a {clinic_number}")
                return f"✅ Escalamiento exitoso. Notificación enviada a {clinic_number}. El bot continuará respondiendo al cliente."
            else:
                print(f"⚠️ PROBLEMA AL ENVIAR NOTIFICACIÓN: {result}")
                return f"⚠️ Escalamiento iniciado pero hubo un problema al enviar notificación: {result}. El bot continuará respondiendo."
                
        except Exception as e:
            print(f"❌ ERROR EN ESCALAMIENTO: {str(e)}")
            return f"⚠️ Error al enviar notificación de escalamiento: {str(e)}. El bot continuará respondiendo al cliente normalmente."


    def _generate_escalation_summary(self, recent_messages: List, user_message: str, user_info: Dict, recent_context_lines: List) -> str:
        """Generar un resumen narrativo completo y detallado del contexto de la conversación"""
        
        if not recent_messages or len(recent_messages) < 2:
            return f"El cliente solicitó hablar con un agente humano. Último mensaje: '{user_message}'"
        
        # Analizar todos los mensajes para construir un resumen completo
        treatments_mentioned = []
        topics_discussed = []
        specific_questions = []
        bot_responses_summary = []
        
        # Diccionario completo de tratamientos
        treatments_dict = {
            "botox": "Botox",
            "relleno": "Rellenos faciales",
            "lifting": "Lifting facial",
            "depilación": "Depilación",
            "limpieza": "Limpieza facial",
            "facial": "Tratamiento facial",
            "masaje": "Masajes terapéuticos",
            "masajes": "Masajes terapéuticos",
            "acupuntura": "Acupuntura",
            "estrés": "Tratamientos para el estrés",
            "relajación": "Tratamientos de relajación",
            "cuello": "Tratamientos para cuello",
            "rodillas": "Tratamientos para rodillas"
        }
        
        # Analizar mensajes del usuario y del bot
        for msg in recent_messages:
            msg_type = msg.get("type")
            content = msg.get("data", {}).get("content", "")
            content_lower = content.lower()
            
            if msg_type == "human":
                # Detectar tratamientos mencionados por el usuario
                for key, value in treatments_dict.items():
                    if key in content_lower and value not in treatments_mentioned:
                        treatments_mentioned.append(value)
                
                # Detectar preguntas o consultas específicas
                if any(word in content_lower for word in ["precio", "costo", "cuánto", "cuanto", "vale"]):
                    specific_questions.append("Consultó sobre precios")
                elif any(word in content_lower for word in ["cita", "agendar", "turno", "disponibilidad", "horario"]):
                    specific_questions.append("Consultó sobre disponibilidad para agendar")
                elif any(word in content_lower for word in ["información", "info", "detalles", "más", "saber"]):
                    specific_questions.append("Solicitó más información")
                elif any(word in content_lower for word in ["efectos", "secundarios", "riesgos", "dolor"]):
                    specific_questions.append("Consultó sobre efectos secundarios o riesgos")
                elif any(word in content_lower for word in ["dura", "tiempo", "sesiones", "cuántas"]):
                    specific_questions.append("Consultó sobre duración o cantidad de sesiones")
                
                # Capturar temas generales de la conversación
                if len(content) > 10:  # Solo mensajes con contenido sustancial
                    topics_discussed.append(content[:150])
            
            elif msg_type == "ai":
                # Resumir respuestas del bot para entender qué información se proporcionó
                if any(word in content_lower for word in ["precio", "costo", "$", "pesos"]):
                    bot_responses_summary.append("Se proporcionó información sobre precios")
                elif any(word in content_lower for word in ["masaje", "acupuntura", "botox", "tratamiento"]):
                    # Extraer el tratamiento mencionado en la respuesta del bot
                    for key, value in treatments_dict.items():
                        if key in content_lower and value not in treatments_mentioned:
                            treatments_mentioned.append(value)
        
        # Construir resumen narrativo completo
        summary_parts = []
        
        # Introducción
        summary_parts.append("El cliente ha estado consultando sobre nuestros servicios y ahora solicita hablar con un agente humano para obtener más información o resolver su consulta de manera personalizada.")
        
        # Tratamientos mencionados
        if treatments_mentioned:
            if len(treatments_mentioned) == 1:
                summary_parts.append(f"Durante la conversación, el cliente mostró interés en: {treatments_mentioned[0]}.")
            else:
                treatments_str = ", ".join(treatments_mentioned[:-1]) + f" y {treatments_mentioned[-1]}"
                summary_parts.append(f"Durante la conversación, el cliente mostró interés en los siguientes tratamientos: {treatments_str}.")
        
        # Consultas específicas
        if specific_questions:
            unique_questions = list(set(specific_questions))
            if len(unique_questions) == 1:
                summary_parts.append(f"El cliente {unique_questions[0].lower()}.")
            else:
                questions_str = ", ".join(unique_questions[:-1]) + f" y {unique_questions[-1].lower()}"
                summary_parts.append(f"Durante la conversación, el cliente {questions_str}.")
        
        # Información adicional del contexto
        if user_info.get('tratamiento'):
            treatment = user_info['tratamiento']
            if treatment not in [t.split()[-1] if ' ' in t else t for t in treatments_mentioned]:
                summary_parts.append(f"El cliente mencionó específicamente interés en: {treatment}.")
        
        # Razón del escalamiento basada en el mensaje
        user_msg_lower = user_message.lower()
        if any(word in user_msg_lower for word in ["profundidad", "profundo", "detallado", "específico", "más información", "más en profundidad"]):
            summary_parts.append("El cliente necesita una consulta más detallada y personalizada que requiere la atención de un agente humano.")
        elif any(word in user_msg_lower for word in ["no me sirve", "no funciona", "no entiendo", "no me ayuda"]):
            summary_parts.append("El cliente tiene dificultades o no está completamente satisfecho con las respuestas del bot y necesita atención personalizada.")
        else:
            summary_parts.append("El cliente prefiere hablar directamente con un agente humano para continuar con su consulta.")
        
        # Si no hay suficiente información, usar el mensaje del usuario
        if len(summary_parts) == 1:  # Solo la introducción
            summary_parts.append(f"Último mensaje del cliente: '{user_message}'")
        
        return " ".join(summary_parts)


class CheckEscalationStatusInput(BaseModel):
    """Input schema for checking escalation status."""
    user_id: str = Field(..., description="Phone number of the user")


class CheckEscalationStatusTool(BaseTool):
    name: str = "Check Escalation Status"
    description: str = (
        "Check if a conversation has been escalated to a human agent."
    )
    args_schema: Type[BaseModel] = CheckEscalationStatusInput

    def _run(self, user_id: str) -> str:
        """Check escalation status."""
        # Por ahora, simplemente retornamos que no hay escalamiento activo
        # En el futuro, esto podría consultar una base de datos de escalamientos
        return f"No hay escalamiento activo registrado para {user_id}"

