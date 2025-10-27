"""
Gestor de conversaciones compatible con MongoDB usando formato exacto
"""

import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from bson import ObjectId
import sqlite3

class MongoDBConversationDB:
    """Gestor de conversaciones que simula el formato MongoDB exacto"""
    
    def __init__(self, db_path: str = None):
        """Inicializar base de datos SQLite que simula MongoDB"""
        if not db_path:
            db_path = os.getenv('CONVERSATION_DB_PATH', './integrado_conversations.db')
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear tabla de conversaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                _id TEXT PRIMARY KEY,
                sessionId TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear índice en sessionId
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessionId ON conversations(sessionId)
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_object_id(self) -> str:
        """Generar ObjectId compatible con MongoDB"""
        return str(ObjectId())
    
    def _format_mongodb_message(self, message_type: str, content: str, 
                               additional_kwargs: Dict = None, 
                               response_metadata: Dict = None,
                               tool_calls: List = None,
                               invalid_tool_calls: List = None) -> Dict:
        """Formatear mensaje en el formato exacto de MongoDB"""
        
        message_data = {
            "content": content,
            "additional_kwargs": additional_kwargs or {},
            "response_metadata": response_metadata or {}
        }
        
        # Agregar campos específicos para AI
        if message_type == "ai":
            message_data["tool_calls"] = tool_calls or []
            message_data["invalid_tool_calls"] = invalid_tool_calls or []
        
        return {
            "type": message_type,
            "data": message_data
        }
    
    def get_or_create_conversation(self, session_id: str) -> Dict:
        """Obtener o crear conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar conversación existente
        cursor.execute('SELECT _id, messages FROM conversations WHERE sessionId = ?', (session_id,))
        result = cursor.fetchone()
        
        if result:
            _id, messages_json = result
            messages = json.loads(messages_json)
        else:
            # Crear nueva conversación
            _id = self._generate_object_id()
            messages = []
            
            cursor.execute('''
                INSERT INTO conversations (_id, sessionId, messages) 
                VALUES (?, ?, ?)
            ''', (_id, session_id, json.dumps(messages)))
        
        conn.commit()
        conn.close()
        
        return {
            "_id": {"$oid": _id},
            "sessionId": session_id,
            "messages": messages
        }
    
    def add_message(self, session_id: str, message_type: str, content: str,
                   additional_kwargs: Dict = None, response_metadata: Dict = None,
                   tool_calls: List = None, invalid_tool_calls: List = None) -> Dict:
        """Agregar mensaje a la conversación"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener conversación existente
        cursor.execute('SELECT _id, messages FROM conversations WHERE sessionId = ?', (session_id,))
        result = cursor.fetchone()
        
        if not result:
            # Crear nueva conversación si no existe
            _id = self._generate_object_id()
            messages = []
        else:
            _id, messages_json = result
            messages = json.loads(messages_json)
        
        # Crear nuevo mensaje
        new_message = self._format_mongodb_message(
            message_type, content, additional_kwargs, 
            response_metadata, tool_calls, invalid_tool_calls
        )
        
        # Agregar mensaje al array
        messages.append(new_message)
        
        # Actualizar base de datos
        if not result:
            cursor.execute('''
                INSERT INTO conversations (_id, sessionId, messages) 
                VALUES (?, ?, ?)
            ''', (_id, session_id, json.dumps(messages)))
        else:
            cursor.execute('''
                UPDATE conversations 
                SET messages = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE sessionId = ?
            ''', (json.dumps(messages), session_id))
        
        conn.commit()
        conn.close()
        
        return {
            "_id": {"$oid": _id},
            "sessionId": session_id,
            "messages": messages
        }
    
    def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Obtener conversación completa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT _id, messages FROM conversations WHERE sessionId = ?', (session_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            _id, messages_json = result
            messages = json.loads(messages_json)
            
            return {
                "_id": {"$oid": _id},
                "sessionId": session_id,
                "messages": messages
            }
        
        return None
    
    def get_conversation_history(self, session_id: str, limit: int = None) -> List[Dict]:
        """Obtener historial de conversación"""
        conversation = self.get_conversation(session_id)
        
        if not conversation:
            return []
        
        messages = conversation["messages"]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_conversation_context(self, session_id: str) -> str:
        """Obtener contexto formateado para el agente"""
        conversation = self.get_conversation(session_id)
        
        if not conversation or not conversation["messages"]:
            return f"=== NUEVA CONVERSACIÓN ===\nUsuario: {session_id}\nNo hay mensajes previos."
        
        messages = conversation["messages"]
        context_parts = [
            f"=== CONTEXTO DE CONVERSACIÓN ===",
            f"Usuario: {session_id}",
            f"Total mensajes: {len(messages)}",
            f"Conversación ID: {conversation['_id']['$oid']}"
        ]
        
        # Agregar últimos mensajes
        context_parts.append("\n--- HISTORIAL RECIENTE ---")
        recent_messages = messages[-10:]  # Últimos 10 mensajes
        
        for i, msg in enumerate(recent_messages, 1):
            msg_type = msg["type"]
            content = msg["data"]["content"]
            
            if msg_type == "human":
                context_parts.append(f"{i}. 👤 Usuario: {content}")
            elif msg_type == "ai":
                context_parts.append(f"{i}. 🤖 Recepcionista: {content}")
            else:
                context_parts.append(f"{i}. 🔧 Sistema: {content}")
        
        # Extraer información del contexto
        context_info = self._extract_context_info(messages)
        if context_info:
            context_parts.append("\n--- INFORMACIÓN DEL CONTEXTO ---")
            for key, value in context_info.items():
                context_parts.append(f"{key}: {value}")
        
        context_parts.extend([
            "\n--- INSTRUCCIONES CRÍTICAS ---",
            "1. LEE TODO EL HISTORIAL antes de responder",
            "2. NO saludes de nuevo si ya hay conversación en curso",
            "3. Si el usuario menciona múltiples temas (cuello + rodillas), responde a AMBOS",
            "4. Continúa la conversación naturalmente, no la reinicies",
            "5. Haz referencia específica a lo que el usuario dijo anteriormente",
            "6. Mantén el contexto: si habla de tratamientos, continúa con eso",
            "7. NO uses 'Hola' si ya hay conversación activa"
        ])
        
        return "\n".join(context_parts)
    
    def _extract_context_info(self, messages: List[Dict]) -> Dict[str, str]:
        """Extraer información del contexto de los mensajes"""
        context = {}
        
        for msg in messages:
            if msg["type"] == "human":
                content = msg["data"]["content"].lower()
                
                # Detectar nombre
                if "me llamo" in content or "soy" in content:
                    words = msg["data"]["content"].split()
                    for i, word in enumerate(words):
                        if word.lower() in ["me", "llamo", "soy"] and i + 1 < len(words):
                            context["nombre"] = words[i + 1].title()
                            break
                
                # Detectar email
                if "@" in msg["data"]["content"]:
                    import re
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', msg["data"]["content"])
                    if email_match:
                        context["email"] = email_match.group()
                
                # Detectar teléfono
                if any(char.isdigit() for char in msg["data"]["content"]) and len(msg["data"]["content"].replace(" ", "")) >= 8:
                    context["telefono"] = msg["data"]["content"].strip()
                
                # Detectar tratamientos
                treatments = ["botox", "relleno", "lifting", "depilación", "limpieza", "facial"]
                for treatment in treatments:
                    if treatment in content:
                        context["tratamiento_interes"] = treatment.title()
                        break
                
                # Detectar horarios
                if any(word in content for word in ["mañana", "tarde", "noche"]):
                    if "mañana" in content:
                        context["horario_preferido"] = "Mañana"
                    elif "tarde" in content:
                        context["horario_preferido"] = "Tarde"
                    elif "noche" in content:
                        context["horario_preferido"] = "Noche"
                
                # Detectar días
                days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                for day in days:
                    if day in content:
                        context["dia_preferido"] = day.title()
                        break
        
        return context
    
    def delete_conversation(self, session_id: str) -> bool:
        """Eliminar conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM conversations WHERE sessionId = ?', (session_id,))
        affected_rows = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected_rows > 0
    
    def list_conversations(self) -> List[Dict]:
        """Listar todas las conversaciones"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT sessionId, created_at, updated_at FROM conversations ORDER BY updated_at DESC')
        results = cursor.fetchall()
        
        conn.close()
        
        conversations = []
        for result in results:
            conversations.append({
                "sessionId": result[0],
                "created_at": result[1],
                "updated_at": result[2]
            })
        
        return conversations

# Instancia global
mongodb_conversation_db = MongoDBConversationDB()


