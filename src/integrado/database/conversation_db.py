"""
Gestor de base de datos para conversaciones
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta

from ..models.conversation import (
    Base,
    ConversationSession,
    ConversationMessage,
    ConversationContext,
)


class ConversationDatabase:
    """Gestor de base de datos para conversaciones"""

    def __init__(self, database_url: Optional[str] = None):
        """Inicializar conexión a base de datos"""
        if not database_url:
            database_url = os.getenv(
                'DATABASE_URL', 'sqlite:///./integrado_conversations.db'
            )

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Crear tablas si no existen
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Obtener sesión de base de datos"""
        return self.SessionLocal()

    def get_or_create_session(
        self, session_id: str, channel: str
    ) -> ConversationSession:
        """Obtener o crear una sesión de conversación"""
        with self.get_session() as db:
            session = (
                db.query(ConversationSession)
                .filter_by(session_id=session_id, is_active=1)
                .first()
            )

            if not session:
                session = ConversationSession(session_id=session_id, channel=channel)
                db.add(session)
                db.commit()
                db.refresh(session)

            return session

    def add_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict] = None,
        channel: str = "whatsapp",
    ) -> ConversationMessage:
        """Agregar mensaje a la conversación"""
        with self.get_session() as db:
            # Obtener o crear sesión
            session = self.get_or_create_session(session_id, channel)

            # Crear mensaje
            message = ConversationMessage(
                session_id=session.id,
                message_type=message_type,
                content=content,
                message_metadata=metadata
                or {},  # Actualizado para usar message_metadata
            )

            db.add(message)
            db.commit()
            db.refresh(message)

            # Actualizar timestamp de la sesión
            session.updated_at = datetime.utcnow()
            db.commit()

            return message

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Obtener historial de conversación"""
        with self.get_session() as db:
            session = (
                db.query(ConversationSession)
                .filter_by(session_id=session_id, is_active=1)
                .first()
            )

            if not session:
                return []

            messages = (
                db.query(ConversationMessage)
                .filter_by(session_id=session.id)
                .order_by(ConversationMessage.created_at.desc())
                .limit(limit)
                .all()
            )

            # Convertir a formato compatible con el ejemplo
            history = []
            for msg in reversed(messages):  # Orden cronológico
                history.append(
                    {
                        "type": msg.message_type,
                        "data": {
                            "content": msg.content,
                            "additional_kwargs": msg.metadata.get(
                                'additional_kwargs', {}
                            ),
                            "response_metadata": msg.metadata.get(
                                'response_metadata', {}
                            ),
                            "tool_calls": msg.metadata.get('tool_calls', []),
                            "invalid_tool_calls": msg.metadata.get(
                                'invalid_tool_calls', []
                            ),
                        },
                    }
                )

            return history

    def set_context(
        self,
        session_id: str,
        context_key: str,
        context_value: str,
        channel: str = "whatsapp",
    ) -> None:
        """Establecer contexto de conversación"""
        with self.get_session() as db:
            session = self.get_or_create_session(session_id, channel)

            # Buscar contexto existente
            context = (
                db.query(ConversationContext)
                .filter_by(session_id=session.id, context_key=context_key)
                .first()
            )

            if context:
                context.context_value = context_value
                context.updated_at = datetime.utcnow()
            else:
                context = ConversationContext(
                    session_id=session.id,
                    context_key=context_key,
                    context_value=context_value,
                )
                db.add(context)

            db.commit()

    def get_context(
        self, session_id: str, context_key: str, channel: str = "whatsapp"
    ) -> Optional[str]:
        """Obtener contexto de conversación"""
        with self.get_session() as db:
            session = (
                db.query(ConversationSession)
                .filter_by(session_id=session_id, is_active=1)
                .first()
            )

            if not session:
                return None

            context = (
                db.query(ConversationContext)
                .filter_by(session_id=session.id, context_key=context_key)
                .first()
            )

            return context.context_value if context else None  # type: ignore

    def get_all_context(
        self, session_id: str, channel: str = "whatsapp"
    ) -> Dict[str, str]:
        """Obtener todo el contexto de una sesión"""
        with self.get_session() as db:
            session = (
                db.query(ConversationSession)
                .filter_by(session_id=session_id, is_active=1)
                .first()
            )

            if not session:
                return {}

            contexts = (
                db.query(ConversationContext).filter_by(session_id=session.id).all()
            )

            return {ctx.context_key: ctx.context_value for ctx in contexts}  # type: ignore

    def close_session(self, session_id: str, channel: str = "whatsapp") -> bool:
        """Cerrar sesión de conversación"""
        with self.get_session() as db:
            session = (
                db.query(ConversationSession)
                .filter_by(session_id=session_id, is_active=1)
                .first()
            )

            if session:
                session.is_active = 0
                session.updated_at = datetime.utcnow()
                db.commit()
                return True

            return False

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Limpiar sesiones antiguas"""
        with self.get_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            old_sessions = (
                db.query(ConversationSession)
                .filter(
                    ConversationSession.updated_at < cutoff_date,
                    ConversationSession.is_active == 0,
                )
                .all()
            )

            count = len(old_sessions)

            for session in old_sessions:
                db.delete(session)

            db.commit()
            return count

    def get_session_stats(
        self, session_id: str, channel: str = "whatsapp"
    ) -> Dict[str, Any]:
        """Obtener estadísticas de una sesión"""
        with self.get_session() as db:
            session = (
                db.query(ConversationSession)
                .filter_by(session_id=session_id, is_active=1)
                .first()
            )

            if not session:
                return {}

            total_messages = (
                db.query(ConversationMessage).filter_by(session_id=session.id).count()
            )

            human_messages = (
                db.query(ConversationMessage)
                .filter_by(session_id=session.id, message_type='human')
                .count()
            )

            ai_messages = (
                db.query(ConversationMessage)
                .filter_by(session_id=session.id, message_type='ai')
                .count()
            )

            return {
                'session_id': session.session_id,
                'channel': session.channel,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'total_messages': total_messages,
                'human_messages': human_messages,
                'ai_messages': ai_messages,
                'is_active': bool(session.is_active),
            }


# Instancia global
conversation_db = ConversationDatabase()
