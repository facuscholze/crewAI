# TODO: unused? This entire module (context_manager.py) is NOT imported anywhere in the project.
# The active conversation-context tools live in conversation_context_tool.py (backed by MongoDB/SQLite).
# This file uses Redis and has a different internal implementation. Keep for reference but do not enable
# without verifying Redis connectivity and removing the conflict with conversation_context_tool.py.
from crewai.tools import BaseTool
from typing import Type, Optional, Dict, List
from pydantic import BaseModel, Field
import redis
import json
import os
from datetime import datetime, timedelta


class ConversationContextInput(BaseModel):
    """Input schema for conversation context management."""
    user_id: str = Field(..., description="Unique identifier for the user")
    channel: str = Field(..., description="Communication channel (whatsapp, messenger, instagram, gmail)")
    message: str = Field(..., description="Current message content")
    message_type: str = Field(default="text", description="Type of message (text, voice, image, etc.)")


class ContextUpdateInput(BaseModel):
    """Input schema for updating conversation context."""
    user_id: str = Field(..., description="Unique identifier for the user")
    channel: str = Field(..., description="Communication channel")
    context_data: Dict = Field(..., description="Context data to store")
    ttl: int = Field(default=86400, description="Time to live in seconds (default: 24 hours)")


class ConversationContextTool(BaseTool):
    name: str = "Conversation Context Manager"
    description: str = (
        "Manage conversation context for each user across different communication channels. "
        "Stores conversation history, user preferences, and current state for personalized interactions."
    )
    args_schema: Type[BaseModel] = ConversationContextInput

    def _run(self, user_id: str, channel: str, message: str, message_type: str = "text") -> str:
        """Manage conversation context for a user."""
        
        try:
            # Initialize Redis connection
            redis_client = self._get_redis_client()
            
            # Generate context key
            context_key = f"conversation:{user_id}:{channel}"
            
            # Get existing context
            existing_context = self._get_context(redis_client, context_key)
            
            # Update context with new message
            updated_context = self._update_context(existing_context, message, message_type, channel)
            
            # Store updated context
            self._store_context(redis_client, context_key, updated_context)
            
            # Return context summary
            return self._format_context_summary(updated_context)
            
        except Exception as e:
            return f"Error managing conversation context: {str(e)}"

    def _get_redis_client(self):
        """Initialize Redis client."""
        redis_url = os.getenv('REDIS_URL')
        redis_password = os.getenv('REDIS_PASSWORD')
        
        # Si no hay configuración de Redis, usar memoria local
        if not redis_url:
            return None
            
        try:
            client = redis.from_url(redis_url, password=redis_password, decode_responses=True)
            client.ping()  # Test connection
            return client
        except Exception:
            # Fallback to in-memory storage if Redis is not available
            print("⚠️ Redis no disponible, usando almacenamiento en memoria")
            return None

    def _get_context(self, redis_client, context_key: str) -> Dict:
        """Get existing conversation context."""
        if redis_client:
            try:
                context_data = redis_client.get(context_key)
                if context_data:
                    return json.loads(context_data)
            except Exception:
                pass
        
        # Return default context structure
        return {
            "user_id": context_key.split(":")[1],
            "channel": context_key.split(":")[2],
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "messages": [],
            "user_preferences": {},
            "current_state": "active",
            "pending_tasks": [],
            "scheduled_events": []
        }

    def _update_context(self, context: Dict, message: str, message_type: str, channel: str) -> Dict:
        """Update context with new message."""
        
        # Add new message to history
        new_message = {
            "content": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "channel": channel
        }
        
        context["messages"].append(new_message)
        context["message_count"] += 1
        context["last_activity"] = datetime.now().isoformat()
        
        # Keep only last 50 messages to prevent memory issues
        if len(context["messages"]) > 50:
            context["messages"] = context["messages"][-50:]
        
        # Update user preferences based on message patterns
        self._update_user_preferences(context, message, message_type)
        
        # Detect intent and update state
        self._update_conversation_state(context, message)
        
        return context

    def _update_user_preferences(self, context: Dict, message: str, message_type: str):
        """Update user preferences based on interaction patterns."""
        preferences = context.get("user_preferences", {})
        
        # Track preferred communication style
        if message_type not in preferences:
            preferences["message_types"] = {}
        
        if message_type in preferences["message_types"]:
            preferences["message_types"][message_type] += 1
        else:
            preferences["message_types"][message_type] = 1
        
        # Track response time preferences (based on message frequency)
        current_time = datetime.now()
        if "last_message_time" in preferences:
            last_time = datetime.fromisoformat(preferences["last_message_time"])
            time_diff = (current_time - last_time).total_seconds()
            
            if "avg_response_time" not in preferences:
                preferences["avg_response_time"] = time_diff
            else:
                # Update running average
                preferences["avg_response_time"] = (
                    preferences["avg_response_time"] + time_diff
                ) / 2
        
        preferences["last_message_time"] = current_time.isoformat()
        context["user_preferences"] = preferences

    def _update_conversation_state(self, context: Dict, message: str):
        """Update conversation state based on message content."""
        message_lower = message.lower()
        
        # Detect common intents
        if any(keyword in message_lower for keyword in ["agendar", "cita", "meeting", "evento"]):
            context["current_state"] = "scheduling"
        elif any(keyword in message_lower for keyword in ["problema", "ayuda", "soporte", "error"]):
            context["current_state"] = "support"
        elif any(keyword in message_lower for keyword in ["gracias", "bye", "adiós", "chau"]):
            context["current_state"] = "closing"
        else:
            context["current_state"] = "active"

    def _store_context(self, redis_client, context_key: str, context: Dict):
        """Store updated context."""
        if redis_client:
            try:
                # Store with 24-hour TTL
                redis_client.setex(
                    context_key, 
                    86400,  # 24 hours
                    json.dumps(context, default=str)
                )
            except Exception:
                pass

    def _format_context_summary(self, context: Dict) -> str:
        """Format context summary for agent use."""
        summary = f"""
Context Summary:
- User: {context['user_id']}
- Channel: {context['channel']}
- Messages: {context['message_count']}
- State: {context['current_state']}
- Last Activity: {context['last_activity']}
- Preferred Message Types: {context.get('user_preferences', {}).get('message_types', {})}
- Recent Messages: {len(context['messages'])} messages
"""
        
        # Include recent message context
        recent_messages = context['messages'][-3:]  # Last 3 messages
        if recent_messages:
            summary += "\nRecent Messages:\n"
            for msg in recent_messages:
                summary += f"- {msg['timestamp']}: {msg['content'][:100]}...\n"
        
        return summary


class ContextRetrievalTool(BaseTool):
    name: str = "Context Retrieval Tool"
    description: str = (
        "Retrieve conversation context and history for personalized responses."
    )
    args_schema: Type[BaseModel] = ConversationContextInput

    def _run(self, user_id: str, channel: str, message: str = "", message_type: str = "text") -> str:
        """Retrieve conversation context."""
        
        try:
            redis_client = self._get_redis_client()
            context_key = f"conversation:{user_id}:{channel}"
            
            context = self._get_context(redis_client, context_key)
            return self._format_context_summary(context)
            
        except Exception as e:
            return f"Error retrieving context: {str(e)}"

    def _get_redis_client(self):
        """Initialize Redis client."""
        redis_url = os.getenv('REDIS_URL')
        redis_password = os.getenv('REDIS_PASSWORD')
        
        # Si no hay configuración de Redis, usar memoria local
        if not redis_url:
            return None
            
        try:
            client = redis.from_url(redis_url, password=redis_password, decode_responses=True)
            client.ping()
            return client
        except Exception:
            print("⚠️ Redis no disponible, usando almacenamiento en memoria")
            return None

    def _get_context(self, redis_client, context_key: str) -> Dict:
        """Get existing conversation context."""
        if redis_client:
            try:
                context_data = redis_client.get(context_key)
                if context_data:
                    return json.loads(context_data)
            except Exception:
                pass
        
        return {
            "user_id": context_key.split(":")[1],
            "channel": context_key.split(":")[2],
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "messages": [],
            "user_preferences": {},
            "current_state": "active",
            "pending_tasks": [],
            "scheduled_events": []
        }

    def _format_context_summary(self, context: Dict) -> str:
        """Format context summary for agent use."""
        summary = f"""
Context Summary:
- User: {context['user_id']}
- Channel: {context['channel']}
- Messages: {context['message_count']}
- State: {context['current_state']}
- Last Activity: {context['last_activity']}
- Recent Messages: {len(context['messages'])} messages
"""
        
        recent_messages = context['messages'][-3:]
        if recent_messages:
            summary += "\nRecent Messages:\n"
            for msg in recent_messages:
                summary += f"- {msg['timestamp']}: {msg['content'][:100]}...\n"
        
        return summary
