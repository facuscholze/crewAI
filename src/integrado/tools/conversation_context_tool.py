"""
Herramienta de contexto de conversación mejorada con base de datos
"""

from crewai.tools import BaseTool
from typing import Type, Optional, Dict, List
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime

from ..database.mongodb_conversation import mongodb_conversation_db
from .runtime_context import current_user_id, current_channel

class ConversationContextInput(BaseModel):
    """Input schema for conversation context management."""
    user_id: str = Field(..., description="Unique identifier for the user (phone number)")
    channel: str = Field(..., description="Communication channel (whatsapp, messenger, instagram, gmail)")
    message: str = Field(default="", description="Current message content")
    message_type: str = Field(default="text", description="Type of message (text, voice, image, etc.)")

class ConversationContextTool(BaseTool):
    name: str = "Conversation Context Manager"
    description: str = (
        "Manage complete conversation history for each user across different communication channels. "
        "Stores and retrieves full conversation history including all messages, context, and session data."
    )
    args_schema: Type[BaseModel] = ConversationContextInput

    def _run(self, user_id: str, channel: str, message: Optional[str] = "", message_type: str = "text") -> str:
        """Manage conversation context and history for a user.

        Enforce the trusted runtime context IDs to avoid phone/channel hallucinations.
        """

        try:
            safe_user_id = current_user_id() or user_id
            safe_channel = current_channel() or channel

            if message:
                mongodb_conversation_db.add_message(
                    session_id=safe_user_id,
                    message_type="human",
                    content=message,
                    additional_kwargs={
                        "message_type": message_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "channel": safe_channel,
                    },
                )

            context_summary = mongodb_conversation_db.get_conversation_context(safe_user_id)

            return context_summary

        except Exception as e:
            return f"Error managing conversation context: {str(e)}"

    def _format_conversation_context(self, user_id: str, channel: str, 
                                   history: List[Dict], context_data: Dict) -> str:
        """Formatear contexto de conversación para el agente"""
        
        context_parts = [
            f"=== CONTEXTO DE CONVERSACIÓN ===",
            f"Usuario: {user_id}",
            f"Canal: {channel}",
            f"Total mensajes: {len(history)}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        # Agregar contexto adicional
        if context_data:
            context_parts.append("\n--- CONTEXTO ADICIONAL ---")
            for key, value in context_data.items():
                context_parts.append(f"{key}: {value}")
        
        # Agregar historial de conversación
        if history:
            context_parts.append("\n--- HISTORIAL DE CONVERSACIÓN ---")
            
            for i, msg in enumerate(history[-6:], 1):  # Últimos 6 mensajes
                msg_type = msg["type"]
                content = msg["data"]["content"]
                
                if msg_type == "human":
                    context_parts.append(f"{i}. 👤 Usuario: {content}")
                elif msg_type == "ai":
                    context_parts.append(f"{i}. 🤖 Recepcionista: {content}")
                else:
                    context_parts.append(f"{i}. 🔧 Sistema: {content}")
        
        # Agregar instrucciones para el agente
        context_parts.extend([
            "\n--- INSTRUCCIONES ---",
            "1. Usa este historial para mantener el hilo de la conversación",
            "2. Haz referencia a mensajes anteriores cuando sea apropiado",
            "3. Mantén un tono conversacional y natural",
            "4. Si es la primera interacción, saluda de manera amigable",
            "5. Si hay contexto previo, continúa la conversación naturalmente"
        ])
        
        return "\n".join(context_parts)

class ConversationContextUpdateInput(BaseModel):
    """Input schema for updating conversation context."""
    user_id: str = Field(..., description="User ID (phone number)")
    context_key: str = Field(..., description="Context key to update")
    context_value: str = Field(..., description="Context value to set")
    channel: str = Field(default="whatsapp", description="Communication channel")

class ConversationContextUpdateTool(BaseTool):
    name: str = "Conversation Context Update"
    description: str = (
        "Update conversation context with new information like user name, preferences, or appointment details."
    )
    args_schema: Type[BaseModel] = ConversationContextUpdateInput

    def _run(self, user_id: str, context_key: str, context_value: str, channel: str = "whatsapp") -> str:
        """Update conversation context"""

        try:
            safe_user_id = current_user_id() or user_id
            safe_channel = current_channel() or channel
            conversation_db.set_context(safe_user_id, context_key, context_value, safe_channel)
            return f"Contexto actualizado: {context_key} = {context_value}"

        except Exception as e:
            return f"Error updating context: {str(e)}"

class ConversationHistoryInput(BaseModel):
    """Input schema for retrieving conversation history."""
    user_id: str = Field(..., description="User ID (phone number)")
    limit: int = Field(default=20, description="Maximum number of messages to retrieve")
    channel: str = Field(default="whatsapp", description="Communication channel")

class ConversationHistoryTool(BaseTool):
    name: str = "Conversation History"
    description: str = (
        "Retrieve complete conversation history for a user."
    )
    args_schema: Type[BaseModel] = ConversationHistoryInput

    def _run(self, user_id: str, limit: int = 20, channel: str = "whatsapp") -> str:
        """Get conversation history"""

        try:
            safe_user_id = current_user_id() or user_id
            history = conversation_db.get_conversation_history(safe_user_id, limit)

            if not history:
                return f"No hay historial de conversación para {safe_user_id}"

            formatted_history = []
            formatted_history.append(f"=== HISTORIAL COMPLETO PARA {safe_user_id} ===")

            for i, msg in enumerate(history, 1):
                msg_type = msg["type"]
                content = msg["data"]["content"]

                if msg_type == "human":
                    formatted_history.append(f"{i}. 👤 Usuario: {content}")
                elif msg_type == "ai":
                    formatted_history.append(f"{i}. 🤖 Recepcionista: {content}")
                else:
                    formatted_history.append(f"{i}. 🔧 Sistema: {content}")

            return "\n".join(formatted_history)

        except Exception as e:
            return f"Error retrieving history: {str(e)}"

class ConversationStatsInput(BaseModel):
    """Input schema for getting conversation statistics."""
    user_id: str = Field(..., description="User ID (phone number)")
    channel: str = Field(default="whatsapp", description="Communication channel")

class ConversationStatsTool(BaseTool):
    name: str = "Conversation Statistics"
    description: str = (
        "Get conversation statistics and session information."
    )
    args_schema: Type[BaseModel] = ConversationStatsInput

    def _run(self, user_id: str, channel: str = "whatsapp") -> str:
        """Get conversation statistics"""

        try:
            safe_user_id = current_user_id() or user_id
            safe_channel = current_channel() or channel
            stats = conversation_db.get_session_stats(safe_user_id, safe_channel)

            if not stats:
                return f"No hay estadísticas para {safe_user_id}"

            formatted_stats = [
                f"=== ESTADÍSTICAS DE CONVERSACIÓN ===",
                f"Usuario: {stats['session_id']}",
                f"Canal: {stats['channel']}",
                f"Creada: {stats['created_at']}",
                f"Última actividad: {stats['updated_at']}",
                f"Total mensajes: {stats['total_messages']}",
                f"Mensajes del usuario: {stats['human_messages']}",
                f"Mensajes de la recepcionista: {stats['ai_messages']}",
                f"Estado: {'Activa' if stats['is_active'] else 'Cerrada'}"
            ]

            return "\n".join(formatted_stats)

        except Exception as e:
            return f"Error retrieving stats: {str(e)}"
