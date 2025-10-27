"""
Modelos de base de datos para conversaciones
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class ConversationSession(Base):
    """Modelo para sesiones de conversación"""
    __tablename__ = 'conversation_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(50), unique=True, nullable=False, index=True)  # Número de teléfono
    channel = Column(String(20), nullable=False)  # whatsapp, messenger, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1 = activa, 0 = cerrada
    
    # Relación con mensajes
    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ConversationSession(session_id='{self.session_id}', channel='{self.channel}')>"

class ConversationMessage(Base):
    """Modelo para mensajes individuales en una conversación"""
    __tablename__ = 'conversation_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey('conversation_sessions.id'), nullable=False)
    message_type = Column(String(20), nullable=False)  # human, ai, system
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)  # Para almacenar datos adicionales
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con sesión
    session = relationship("ConversationSession", back_populates="messages")
    
    # Índices para optimizar consultas
    __table_args__ = (
        Index('idx_session_created', 'session_id', 'created_at'),
        Index('idx_message_type', 'message_type'),
    )
    
    def __repr__(self):
        return f"<ConversationMessage(type='{self.message_type}', content='{self.content[:50]}...')>"

class ConversationContext(Base):
    """Modelo para contexto adicional de conversaciones"""
    __tablename__ = 'conversation_contexts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey('conversation_sessions.id'), nullable=False)
    context_key = Column(String(100), nullable=False)  # ej: "user_name", "appointment_type"
    context_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        Index('idx_session_context', 'session_id', 'context_key'),
    )
    
    def __repr__(self):
        return f"<ConversationContext(key='{self.context_key}', value='{self.context_value[:50]}...')>"






