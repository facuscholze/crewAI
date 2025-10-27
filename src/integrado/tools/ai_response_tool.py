"""
Herramienta para guardar respuestas de la AI en el historial
"""

from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from datetime import datetime

from ..database.mongodb_conversation import mongodb_conversation_db

class AIResponseInput(BaseModel):
    """Input schema for saving AI responses."""
    user_id: str = Field(..., description="User ID (phone number)")
    response_content: str = Field(..., description="AI response content")
    channel: str = Field(default="whatsapp", description="Communication channel")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

class AIResponseTool(BaseTool):
    name: str = "AI Response Saver"
    description: str = (
        "Save AI responses to conversation history. Use this after generating a response to store it in the database."
    )
    args_schema: Type[BaseModel] = AIResponseInput

    def _run(self, user_id: str, response_content: str, 
             channel: str = "whatsapp", metadata: dict = None) -> str:
        """Save AI response to conversation history"""
        
        try:
            # Agregar respuesta de AI al historial
            mongodb_conversation_db.add_message(
                session_id=user_id,
                message_type="ai",
                content=response_content,
                additional_kwargs={
                    "timestamp": datetime.utcnow().isoformat(),
                    "channel": channel
                },
                response_metadata=metadata.get('response_metadata', {}) if metadata else {},
                tool_calls=metadata.get('tool_calls', []) if metadata else [],
                invalid_tool_calls=metadata.get('invalid_tool_calls', []) if metadata else []
            )
            
            return f"Respuesta guardada en historial para {user_id}"
            
        except Exception as e:
            return f"Error saving AI response: {str(e)}"
