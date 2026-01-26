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

    def __init__(self, db_path: str = None):  # type: ignore
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
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS conversations (
                _id TEXT PRIMARY KEY,
                sessionId TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        )

        # Crear índice en sessionId
        cursor.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_sessionId ON conversations(sessionId)
        '''
        )

        conn.commit()
        conn.close()

    def _generate_object_id(self) -> str:
        """Generar ObjectId compatible con MongoDB"""
        return str(ObjectId())

    def _format_mongodb_message(
        self,
        message_type: str,
        content: str,
        additional_kwargs: Dict = None,  # type: ignore
        response_metadata: Dict = None,  # type: ignore
        tool_calls: List = None,  # type: ignore
        invalid_tool_calls: List = None,  # type: ignore
    ) -> Dict:
        """Formatear mensaje en el formato exacto de MongoDB"""

        message_data = {
            "content": content,
            "additional_kwargs": additional_kwargs or {},
            "response_metadata": response_metadata or {},
        }

        # Agregar campos específicos para AI
        if message_type == "ai":
            message_data["tool_calls"] = tool_calls or []
            message_data["invalid_tool_calls"] = invalid_tool_calls or []

        return {"type": message_type, "data": message_data}

    def get_or_create_conversation(self, session_id: str) -> Dict:
        """Obtener o crear conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Buscar conversación existente
        cursor.execute(
            'SELECT _id, messages FROM conversations WHERE sessionId = ?', (session_id,)
        )
        result = cursor.fetchone()

        if result:
            _id, messages_json = result
            messages = json.loads(messages_json)
        else:
            # Crear nueva conversación
            _id = self._generate_object_id()
            messages = []

            cursor.execute(
                '''
                INSERT INTO conversations (_id, sessionId, messages) 
                VALUES (?, ?, ?)
            ''',
                (_id, session_id, json.dumps(messages)),
            )

        conn.commit()
        conn.close()

        return {"_id": {"$oid": _id}, "sessionId": session_id, "messages": messages}

    def add_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        additional_kwargs: Dict = None,  # type: ignore
        response_metadata: Dict = None,  # type: ignore
        tool_calls: List = None,  # type: ignore
        invalid_tool_calls: List = None,  # pyright: ignore[reportArgumentType]
    ) -> Dict:
        """Agregar mensaje a la conversación"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener conversación existente
        cursor.execute(
            'SELECT _id, messages FROM conversations WHERE sessionId = ?', (session_id,)
        )
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
            message_type,
            content,
            additional_kwargs,
            response_metadata,
            tool_calls,
            invalid_tool_calls,
        )

        # Agregar mensaje al array
        messages.append(new_message)

        # Actualizar base de datos
        if not result:
            cursor.execute(
                '''
                INSERT INTO conversations (_id, sessionId, messages) 
                VALUES (?, ?, ?)
            ''',
                (_id, session_id, json.dumps(messages)),
            )
        else:
            cursor.execute(
                '''
                UPDATE conversations 
                SET messages = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE sessionId = ?
            ''',
                (json.dumps(messages), session_id),
            )

        conn.commit()
        conn.close()

        return {"_id": {"$oid": _id}, "sessionId": session_id, "messages": messages}

    def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Obtener conversación completa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT _id, messages FROM conversations WHERE sessionId = ?', (session_id,)
        )
        result = cursor.fetchone()

        conn.close()

        if result:
            _id, messages_json = result
            messages = json.loads(messages_json)

            return {"_id": {"$oid": _id}, "sessionId": session_id, "messages": messages}

        return None

    def get_conversation_history(
        self, session_id: str, limit: int = None  # type: ignore
    ) -> List[Dict]:
        """Obtener historial de conversación"""
        conversation = self.get_conversation(session_id)

        if not conversation:
            return []

        messages = conversation["messages"]

        if limit:
            messages = messages[-limit:]

        return messages

    def _is_greeting(self, message: str) -> bool:
        """Detectar si un mensaje es un saludo (inicio de nueva conversación)"""
        message_lower = message.lower().strip()

        # Lista de saludos comunes
        greetings = [
            "hola",
            "holi",
            "holis",
            "hola!",
            "hola 😊",
            "hola 😀",
            "buenos días",
            "buen día",
            "buenos dias",
            "buen dia",
            "buenas tardes",
            "buena tarde",
            "buenas noches",
            "buena noche",
            "hi",
            "hello",
            "hey",
            "hey!",
            "hi!",
            "hello!",
            "buenas",
            "buenas!",
            "saludos",
            "saludos!",
            "qué tal",
            "que tal",
            "qué tal?",
            "que tal?",
            "cómo estás",
            "como estas",
            "cómo estás?",
            "como estas?",
            "buen día",
            "buendia",
        ]

        # Verificar si el mensaje es solo un saludo (sin contenido adicional)
        # Si el mensaje tiene más de 3 palabras, probablemente no es solo un saludo
        words = message_lower.split()
        if len(words) > 3:
            return False

        # Verificar si coincide con algún saludo
        for greeting in greetings:
            if greeting in message_lower:
                return True

        return False

    def get_conversation_context(self, session_id: str) -> str:
        """Obtener contexto formateado para el agente"""
        conversation = self.get_conversation(session_id)

        if not conversation or not conversation["messages"]:
            return f"=== NUEVA CONVERSACIÓN ===\nUsuario: {session_id}\nNo hay mensajes previos."

        messages = conversation["messages"]

        # Detectar si el último mensaje del usuario es un saludo
        # Si es un saludo, tratar como nueva conversación (ignorar información antigua)
        is_new_conversation = False
        last_human_message = None

        # Buscar el último mensaje del usuario
        for msg in reversed(messages):
            if msg.get("type") == "human":
                last_human_message = msg.get("data", {}).get("content", "")
                if last_human_message and self._is_greeting(last_human_message):
                    is_new_conversation = True
                break

        context_parts = [
            f"=== CONTEXTO DE CONVERSACIÓN ===",
            f"Usuario: {session_id}",
            f"Total mensajes: {len(messages)}",
            f"Conversación ID: {conversation['_id']['$oid']}",
        ]

        # Si es un saludo, marcar como nueva conversación
        if is_new_conversation:
            context_parts.append(
                "\n🆕 NUEVA CONSULTA: El usuario saludó, iniciando conversación desde cero"
            )
            context_parts.append(f"Último mensaje: {last_human_message}")
        else:
            # Agregar últimos mensajes (limitar a 8 para evitar rate limits)
            context_parts.append("\n--- HISTORIAL RECIENTE ---")
            recent_messages = messages[
                -8:
            ]  # Últimos 8 mensajes (reducido para evitar rate limits)

            for i, msg in enumerate(recent_messages, 1):
                msg_type = msg["type"]
                content = msg["data"]["content"]

                if msg_type == "human":
                    context_parts.append(f"{i}. 👤 Usuario: {content}")
                elif msg_type == "ai":
                    context_parts.append(f"{i}. 🤖 Recepcionista: {content}")
                else:
                    context_parts.append(f"{i}. 🔧 Sistema: {content}")

        # Solo extraer información del contexto si NO es un saludo (nueva conversación)
        if not is_new_conversation:
            # Extraer información del contexto SOLO de los mensajes recientes (últimos 5)
            # Esto evita que aparezca información antigua de conversaciones pasadas
            recent_messages_for_context = (
                messages[-5:] if len(messages) >= 5 else messages
            )
            context_info = self._extract_context_info(recent_messages_for_context)

            # Solo incluir información del contexto si hay suficientes mensajes recientes (al menos 2)
            # Esto evita mostrar información de conversaciones muy antiguas o nuevas
            if context_info and len(recent_messages_for_context) >= 2:
                context_parts.append("\n--- INFORMACIÓN DEL CONTEXTO ---")
                for key, value in context_info.items():
                    # Validar que el valor no sea un mensaje completo (evitar mostrar mensajes como teléfono)
                    if key == "telefono" and len(value) > 30:
                        continue  # Saltar si parece un mensaje completo, no un teléfono
                    context_parts.append(f"{key}: {value}")

        # Instrucciones según si es nueva conversación o no
        if is_new_conversation:
            context_parts.extend(
                [
                    "\n--- INSTRUCCIONES CRÍTICAS ---",
                    "1. El usuario saludó, esto es una NUEVA CONSULTA - trata como conversación nueva",
                    "2. NO hagas referencia a conversaciones anteriores o información antigua",
                    "3. Saluda de manera cálida y profesional como Camila",
                    "4. NO menciones tratamientos, precios o información de conversaciones pasadas",
                    "5. Espera a que el usuario te diga qué necesita en esta nueva consulta",
                    "6. Mantén un tono amigable y profesional",
                ]
            )
        else:
            context_parts.extend(
                [
                    "\n--- INSTRUCCIONES CRÍTICAS ---",
                    "1. LEE TODO EL HISTORIAL antes de responder",
                    "2. NO saludes de nuevo si ya hay conversación en curso",
                    "3. Si el usuario menciona múltiples temas (cuello + rodillas), responde a AMBOS",
                    "4. Continúa la conversación naturalmente, no la reinicies",
                    "5. Haz referencia específica a lo que el usuario dijo anteriormente",
                    "6. Mantén el contexto: si habla de tratamientos, continúa con eso",
                    "7. NO uses 'Hola' si ya hay conversación activa",
                ]
            )

        return "\n".join(context_parts)

    def _extract_context_info(self, messages: List[Dict]) -> Dict[str, str]:
        """Extraer información del contexto SOLO de los mensajes recientes proporcionados"""
        context = {}

        for msg in messages:
            if msg["type"] == "human":
                content_lower = msg["data"]["content"].lower()
                content_original = msg["data"]["content"]

                # Detectar nombre (solo si es una frase corta de presentación)
                if ("me llamo" in content_lower or "soy" in content_lower) and len(
                    content_original.split()
                ) <= 5:
                    words = content_original.split()
                    for i, word in enumerate(words):
                        if word.lower() in ["me", "llamo", "soy"] and i + 1 < len(
                            words
                        ):
                            context["nombre"] = words[i + 1].title()
                            break

                # Detectar email
                if "@" in content_original:
                    import re

                    email_match = re.search(
                        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                        content_original,
                    )
                    if email_match:
                        context["email"] = email_match.group()

                # Detectar teléfono (solo si parece un número de teléfono, no un mensaje completo)
                # Validar que tenga dígitos, sea corto (< 20 caracteres) y no contenga palabras comunes de mensajes
                if (
                    any(char.isdigit() for char in content_original)
                    and len(content_original.replace(" ", "")) >= 8
                    and len(content_original) < 20
                    and not any(
                        word in content_lower
                        for word in [
                            "masajes",
                            "tratamiento",
                            "precio",
                            "cita",
                            "agendar",
                            "quiero",
                            "me gustaría",
                        ]
                    )
                ):
                    context["telefono"] = content_original.strip()

                # Detectar tratamientos (solo si no hay uno ya detectado, para evitar sobrescribir con información más antigua)
                if not context.get("tratamiento_interes"):
                    treatments = [
                        "botox",
                        "relleno",
                        "lifting",
                        "depilación",
                        "limpieza",
                        "facial",
                        "masaje",
                        "acupuntura",
                    ]
                    for treatment in treatments:
                        if treatment in content_lower:
                            context["tratamiento_interes"] = treatment.title()
                            break

                # Detectar horarios (solo si no hay uno ya detectado)
                if not context.get("horario_preferido"):
                    if any(
                        word in content_lower for word in ["mañana", "tarde", "noche"]
                    ):
                        if "mañana" in content_lower:
                            context["horario_preferido"] = "Mañana"
                        elif "tarde" in content_lower:
                            context["horario_preferido"] = "Tarde"
                        elif "noche" in content_lower:
                            context["horario_preferido"] = "Noche"

                # Detectar días (solo si no hay uno ya detectado)
                if not context.get("dia_preferido"):
                    days = [
                        "lunes",
                        "martes",
                        "miércoles",
                        "jueves",
                        "viernes",
                        "sábado",
                        "domingo",
                    ]
                    for day in days:
                        if day in content_lower:
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

    def delete_all(self) -> int:
        """Eliminar TODAS las conversaciones y reiniciar la base."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM conversations')
            affected_rows = cursor.rowcount if cursor.rowcount is not None else 0
            conn.commit()
        finally:
            conn.close()
        return affected_rows

    def list_conversations(self) -> List[Dict]:
        """Listar todas las conversaciones"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT sessionId, created_at, updated_at FROM conversations ORDER BY updated_at DESC'
        )
        results = cursor.fetchall()

        conn.close()

        conversations = []
        for result in results:
            conversations.append(
                {
                    "sessionId": result[0],
                    "created_at": result[1],
                    "updated_at": result[2],
                }
            )

        return conversations


# Instancia global
mongodb_conversation_db = MongoDBConversationDB()
