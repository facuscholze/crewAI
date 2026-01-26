from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Conversation(Base):
    """Modelo para almacenar conversaciones"""

    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String(50), default='active')
    message_metadata = Column(JSON)  # Cambiado de 'metadata' a 'message_metadata'


class Message(Base):
    """Modelo para almacenar mensajes individuales"""

    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, nullable=False)
    user_id = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)
    message_type = Column(String(50), default='text')
    content = Column(Text, nullable=False)
    direction = Column(String(10), nullable=False)  # 'inbound' or 'outbound'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_metadata = Column(JSON)  # Cambiado de 'metadata' a 'message_metadata'


class ScheduledEvent(Base):
    """Modelo para eventos programados"""

    __tablename__ = 'scheduled_events'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    event_id = Column(String(255))  # Google Calendar event ID
    title = Column(String(500), nullable=False)
    description = Column(Text)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(500))
    attendees = Column(JSON)
    status = Column(String(50), default='scheduled')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserPreferences(Base):
    """Modelo para preferencias de usuario"""

    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, unique=True)
    preferred_channels = Column(JSON)
    communication_style = Column(String(50))
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='es')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    preferences = Column(JSON)


class AgentLog(Base):
    """Modelo para logs de agentes"""

    __tablename__ = 'agent_logs'

    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100), nullable=False)
    task_name = Column(String(100), nullable=False)
    user_id = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time = Column(Integer)  # in seconds
    status = Column(String(50), nullable=False)  # 'success', 'error', 'pending'
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
