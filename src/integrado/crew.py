from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Import custom tools
from .tools.whatsapp_tool import WhatsAppTool, WhatsAppWebhookTool
from .tools.messenger_tool import MessengerTool, MessengerWebhookTool
try:
    from .tools.instagram_tool import (
        InstagramTool,
        InstagramWebhookTool,
        InstagramGetConversationsTool,
        InstagramGetUnreadConversationsTool,
        InstagramGetParticipantsTool,
        InstagramGetMessagesTool,
    )
except Exception:
    # Fallback to restored implementation if the original module is missing or broken
    from .tools.instagram_tool_restored import (
        InstagramTool,
        InstagramWebhookTool,
        InstagramGetConversationsTool,
        InstagramGetUnreadConversationsTool,
        InstagramGetParticipantsTool,
        InstagramGetMessagesTool,
    )
from .tools.gmail_imap_tool import GmailIMAPTool, GmailIMAPSearchTool, GmailIMAPAutoReplyTool, GmailIMAPWebhookTool
from .tools.calendar_service_account import CalendarTool, CalendarUpdateTool, CalendarSearchTool
try:
    from .tools.elevenlabs_tool import ElevenLabsVoiceTool, ElevenLabsCallTool
except ImportError:
    # Fallback si elevenlabs_tool no existe
    ElevenLabsVoiceTool = None
    ElevenLabsCallTool = None
from .tools.conversation_context_tool import ConversationContextTool, ConversationContextUpdateTool, ConversationHistoryTool, ConversationStatsTool
from .tools.ai_response_tool import AIResponseTool
from .tools.human_escalation_tool import HumanEscalationTool, CheckEscalationStatusTool
from .tools.rag_tool import RagRetrieverTool

@CrewBase
class Integrado(object):
    """Integrado Omnicanal Crew - Sistema Multiagente para Comunicación Omnicanal"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def _load_full_knowledge(self) -> str:
        """Load complete knowledge base content to inject into agent prompts."""
        import glob
        module_dir = os.path.dirname(os.path.abspath(__file__))
        knowledge_dir = os.path.normpath(os.path.join(module_dir, '..', '..', 'knowledge'))
        chunks = []
        if os.path.exists(knowledge_dir):
            for path in glob.glob(os.path.join(knowledge_dir, '*')):
                if os.path.isfile(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            chunks.append(f.read())
                    except Exception:
                        continue
        return "\n\n".join(chunks) if chunks else "(No knowledge available)"

    # Coordinador Principal
    @agent
    def coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config['coordinator'],
            
            tools=[
                ConversationContextTool(),
                ConversationContextUpdateTool(),
                ConversationHistoryTool(),
                ConversationStatsTool(),
            ],
            verbose=True,
            allow_delegation=True
        )

    # Agentes Especializados por Canal
    @agent
    def whatsapp_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['whatsapp_agent'],
            
            tools=[
                WhatsAppTool(),
                WhatsAppWebhookTool(),
                ConversationContextTool(),
                ConversationContextUpdateTool(),
                ConversationHistoryTool(),
                ConversationStatsTool(),
                AIResponseTool(),
                RagRetrieverTool(),
                *([ElevenLabsVoiceTool(), ElevenLabsCallTool()] if ElevenLabsVoiceTool and ElevenLabsCallTool else []),
                HumanEscalationTool(),
                CheckEscalationStatusTool(),
            ],
            verbose=True,
            max_iter=8,
            max_execution_time=45,
            allow_delegation=False,
            reasoning=False,
            max_reasoning_attempts=0,
            inject_date=True,
            date_format="%Y-%m-%d %H:%M:%S",
        )

    @agent
    def messenger_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['messenger_agent'],
            
            tools=[
                MessengerTool(),
                MessengerWebhookTool(),
                ConversationContextTool(),
            ],
            verbose=True
        )

    @agent
    def instagram_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['instagram_agent'],
            
            tools=[
                InstagramTool(),
                InstagramWebhookTool(),
                InstagramGetConversationsTool(),
                InstagramGetUnreadConversationsTool(),
                InstagramGetParticipantsTool(),
                InstagramGetMessagesTool(),
                ConversationContextTool(),
                ConversationContextUpdateTool(),
                ConversationHistoryTool(),
                AIResponseTool(),
                RagRetrieverTool(),
            ],
            verbose=True,
            max_iter=10,
            max_execution_time=60,
            allow_delegation=False,
            reasoning=False,
            max_reasoning_attempts=0,
            inject_date=True,
            date_format="%Y-%m-%d %H:%M:%S",
        )

    @agent
    def gmail_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['gmail_agent'],
            
            tools=[
                GmailIMAPTool(),
                GmailIMAPSearchTool(),
                GmailIMAPAutoReplyTool(),
                GmailIMAPWebhookTool(),
                ConversationContextTool(),
            ],
            verbose=True
        )

    @agent
    def calendar_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['calendar_agent'],
            
            tools=[
                CalendarTool(),
                CalendarUpdateTool(),
                CalendarSearchTool(),
                ConversationContextTool(),
            ],
            verbose=True
        )

    @agent
    def voice_agent(self) -> Agent:
        voice_tools = []
        if ElevenLabsVoiceTool and ElevenLabsCallTool:
            voice_tools = [ElevenLabsVoiceTool(), ElevenLabsCallTool()]
        return Agent(
            config=self.agents_config['voice_agent'],
            
            tools=[
                *voice_tools,
                ConversationContextTool(),
            ],
            verbose=True
        )

    # Tareas de Coordinación
    @task
    def coordinate_message(self) -> Task:
        return Task(
            config=self.tasks_config['coordinate_message'],
            tools=[ConversationContextTool(), ConversationContextUpdateTool(), ConversationHistoryTool()],
        )

    # Teras por Canal - WhatsApp
    @task
    def whatsapp_text_message(self) -> Task:
        return Task(
            config=self.tasks_config['whatsapp_text_message'],
            tools=[
                WhatsAppTool(), 
                ConversationContextTool(),
                HumanEscalationTool(),
                CheckEscalationStatusTool(),
                AIResponseTool(),
                RagRetrieverTool(),
            ],
        )

    @task
    def whatsapp_voice_call(self) -> Task:
        voice_tools = []
        if ElevenLabsCallTool and ElevenLabsVoiceTool:
            voice_tools = [ElevenLabsCallTool(), ElevenLabsVoiceTool()]
        return Task(
            config=self.tasks_config['whatsapp_voice_call'],
            tools=voice_tools,
        )

    # Tareas por Canal - Messenger
    @task
    def messenger_message(self) -> Task:
        return Task(
            config=self.tasks_config['messenger_message'],
            tools=[MessengerTool(), ConversationContextTool()],
        )

    # Tareas por Canal - Instagram
    @task
    def instagram_message(self) -> Task:
        return Task(
            config=self.tasks_config['instagram_message'],
            tools=[
                InstagramTool(),
                ConversationContextTool(),
                AIResponseTool(),
                RagRetrieverTool(),
            ],
        )

    # Tareas por Canal - Gmail
    @task
    def gmail_message(self) -> Task:
        return Task(
            config=self.tasks_config['gmail_message'],
            tools=[GmailIMAPTool(), GmailIMAPSearchTool(), GmailIMAPAutoReplyTool(), ConversationContextTool()],
        )

    # Tareas de Calendar
    @task
    def schedule_event(self) -> Task:
        return Task(
            config=self.tasks_config['schedule_event'],
            tools=[CalendarTool(), CalendarSearchTool(), ConversationContextTool()],
        )

    @task
    def update_calendar(self) -> Task:
        return Task(
            config=self.tasks_config['update_calendar'],
            tools=[CalendarUpdateTool(), ConversationContextTool()],
        )

    # Tarea de Seguimiento
    @task
    def follow_up_task(self) -> Task:
        return Task(
            config=self.tasks_config['follow_up_task'],
            tools=[ConversationContextTool()],
        )

    @crew
    def crew(self) -> Crew:
        """Crea el Crew Omnicanal de Integrado"""
        
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm="gpt-4o-mini",
            verbose=True,
            # Configuración simplificada sin memory/planning para evitar problemas
            max_rpm=100,
            max_execution_time=300,  # 5 minutos máximo por ejecución
        )

    # --- INICIO DE LA MODIFICACIÓN ---
    # Añadimos 'original_message_id=None' a la definición de la función
    def process_omnicanal_message(self, channel: str, user_id: str, message: str, message_type: str = "text", original_message_id: str = None):
        """Procesa mensajes entrantes de cualquier canal omnicanal"""
        
        print(f"🚀 Procesando mensaje omnicanal: {channel} - {user_id} - {message[:50]}...")
        
        # Obtener contexto de conversación existente
        context_manager = ConversationContextTool()
        context_result = context_manager._run(user_id, channel, message, message_type)
        
        inputs = {
            'channel': channel,
            'user_id': user_id,
            'message': message,
            'message_type': message_type,
            'timestamp': str(datetime.now().isoformat()),
            'conversation_context': context_result,
            'original_message_id': original_message_id  # <-- AÑADIMOS EL ID A LOS INPUTS
        }

        # Obtener conocimiento de la clínica vía RAG y adjuntarlo al inputs (fallback a archivos si RAG no devuelve nada)
        try:
            rag = RagRetrieverTool()
            clinic_knowledge = rag._run(message, top_k=3)
            # Si RAG no pudo devolver piezas relevantes, intentar carga directa de archivo (compatibilidad)
            if not clinic_knowledge:
                import glob
                knowledge_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge'))
                combined = []
                for path in glob.glob(os.path.join(knowledge_dir, '*')):
                    if os.path.isfile(path):
                        try:
                            with open(path, 'r', encoding='utf-8') as kf:
                                combined.append(kf.read())
                        except Exception:
                            continue
                clinic_knowledge = "\n\n".join(combined) if combined else None
            # Limitar tamaño para prompts
            if clinic_knowledge and len(clinic_knowledge) > 6000:
                clinic_knowledge = clinic_knowledge[:6000] + "\n\n[... conocimiento truncado ...]"
            inputs['clinic_knowledge'] = clinic_knowledge
        except Exception as e:
            print(f"⚠️ Error cargando clinic knowledge via RAG: {str(e)}")
            # Asegurar que el template tenga la variable aunque esté vacía
            inputs['clinic_knowledge'] = ""

        print(f"📋 Contexto obtenido: {context_result[:200]}..." if len(context_result) > 200 else f"📋 Contexto: {context_result}")
        
        try:
            # Determinar qué tarea ejecutar basado en el canal
            if channel.lower() == 'whatsapp':
                if message_type == 'voice_call':
                    crew = Crew(
                        agents=[self.voice_agent(), self.whatsapp_agent()],
                        tasks=[self.whatsapp_voice_call()],
                        process=Process.sequential,
                        verbose=True,
                        max_execution_time=120,
                    )
                else:
                    crew = Crew(
                        agents=[self.whatsapp_agent(), self.coordinator()],
                        tasks=[self.whatsapp_text_message()],
                        process=Process.sequential,
                        verbose=True,
                        max_execution_time=120,
                    )
                result = self._kickoff_with_retry(crew, inputs)
            elif channel.lower() == 'messenger':
                crew = Crew(
                    agents=[self.messenger_agent(), self.coordinator()],
                    tasks=[self.messenger_message()],
                    process=Process.sequential,
                    verbose=True,
                    max_execution_time=120,
                )
                result = self._kickoff_with_retry(crew, inputs)
            elif channel.lower() == 'instagram':
                # Sanitizar y limitar conocimiento clínico para evitar caracteres de control en prompts
                if inputs.get('clinic_knowledge'):
                    try:
                        raw_ck = inputs['clinic_knowledge']
                        # Remover caracteres de control excepto tab y salto de línea, y truncar para prompts
                        clean_ck = ''.join(ch for ch in raw_ck if ch == '\n' or ch == '\t' or ord(ch) >= 32)
                        inputs['clinic_knowledge'] = clean_ck[:6000]
                    except Exception:
                        # Si algo falla, eliminar knowledge para evitar bloqueos
                        inputs['clinic_knowledge'] = None
                crew = Crew(
                    agents=[self.instagram_agent(), self.coordinator()],
                    tasks=[self.instagram_message()],
                    process=Process.sequential,
                    verbose=True,
                    max_execution_time=120,
                )
                result = self._kickoff_with_retry(crew, inputs)
            elif channel.lower() == 'gmail':
                crew = Crew(
                    agents=[self.gmail_agent(), self.coordinator()],
                    tasks=[self.gmail_message()],
                    process=Process.sequential,
                    verbose=True,
                    max_execution_time=180,
                )
                result = self._kickoff_with_retry(crew, inputs)
            else:
                # Canal no reconocido, usar coordinador
                crew = Crew(
                    agents=[self.coordinator()],
                    tasks=[self.coordinate_message()],
                    process=Process.sequential,
                    verbose=True,
                    max_execution_time=60,
                )
                result = self._kickoff_with_retry(crew, inputs)
            
            return result
            
        except Exception as e:
            return f"Error processing omnicanal message: {str(e)}"
    # --- FIN DE LA MODIFICACIÓN ---

    def schedule_calendar_event(self, user_id: str, event_details: dict):
        """Programa un evento en el calendario"""
        
        inputs = {
            'user_id': user_id,
            'title': event_details.get('title', ''),
            'description': event_details.get('description', ''),
            'start_datetime': event_details.get('start_datetime', ''),
            'end_datetime': event_details.get('end_datetime', ''),
            'attendees': event_details.get('attendees', []),
            'location': event_details.get('location', ''),
            'timezone': event_details.get('timezone', 'UTC')
        }
        
        try:
            crew = Crew(
                agents=[self.calendar_agent(), self.coordinator()],
                tasks=[self.schedule_event()],
                process=Process.sequential,
                verbose=True
            )
            result = crew.kickoff(inputs=inputs)
            return result
        except Exception as e:
            return f"Error scheduling calendar event: {str(e)}"

    def _kickoff_with_retry(self, crew: Crew, inputs: dict, retries: int = 1):
        """Ejecuta un crew con reintentos básicos ante timeouts u errores transitorios."""
        for attempt in range(retries + 1):
            try:
                result = crew.kickoff(inputs=inputs)
            except Exception as exc:
                error_text = str(exc)
                print(f"⚠️ Crew execution error (attempt {attempt + 1}/{retries + 1}): {error_text}")
                
                # Si es rate limit, esperar un poco más antes de reintentar
                if "rate limit" in error_text.lower() or "tpm" in error_text.lower():
                    import time
                    wait_time = 30  # Esperar 30 segundos para rate limits
                    print(f"⏳ Rate limit detectado. Esperando {wait_time} segundos antes de reintentar...")
                    time.sleep(wait_time)
                
                if attempt < retries:
                    print("🔁 Reintentando ejecución del crew...")
                    continue
                # Si falla definitivamente, devolver mensaje amigable pero continuar
                return f"Lo siento, hubo un problema técnico. Por favor intenta de nuevo en un momento."

            if isinstance(result, str) and ("execution timed out" in result.lower() or "timed out" in result.lower()):
                print(f"⚠️ Crew timeout detected (attempt {attempt + 1}/{retries + 1}).")
                if attempt < retries:
                    print("🔁 Reintentando ejecución del crew tras timeout...")
                    continue
            return result

        return "Lo siento, hubo un problema técnico. Por favor intenta de nuevo en un momento."