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
from .tools.instagram_tool import InstagramTool, InstagramWebhookTool
from .tools.gmail_imap_tool import GmailIMAPTool, GmailIMAPSearchTool, GmailIMAPAutoReplyTool, GmailIMAPWebhookTool
from .tools.calendar_service_account import CalendarTool, CalendarUpdateTool, CalendarSearchTool
from .tools.elevenlabs_tool import ElevenLabsVoiceTool, ElevenLabsCallTool
from .tools.conversation_context_tool import ConversationContextTool, ConversationContextUpdateTool, ConversationHistoryTool, ConversationStatsTool
from .tools.ai_response_tool import AIResponseTool
from .tools.treatment_info_tool import TreatmentInfoTool

@CrewBase
class Integrado():
    """Integrado Omnicanal Crew - Sistema Multiagente para Comunicación Omnicanal"""

    agents: List[BaseAgent]
    tasks: List[Task]

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
                ElevenLabsVoiceTool(),
                ElevenLabsCallTool(),
                TreatmentInfoTool(),
            ],
            verbose=True,
            max_iter=10,  # Limitar iteraciones para forzar uso de herramientas
            max_execution_time=60,  # 1 minuto máximo
            allow_delegation=False,  # No delegar, manejar todo localmente
            reasoning=True,  # Habilitar reasoning para mejor planificación
            max_reasoning_attempts=3,  # Máximo 3 intentos de reasoning
            inject_date=True,  # Inyectar fecha para contexto temporal
            date_format="%Y-%m-%d %H:%M:%S",  # Formato de fecha con hora
            system_template="""
Eres Jennifer, la recepcionista virtual de Houston Aesthetics.

INSTRUCCIONES CRÍTICAS:
1. SIEMPRE que generes una respuesta, DEBES usar WhatsAppTool para ENVIARLA al usuario
2. DESPUÉS de enviar, usa AIResponseTool para guardar la respuesta en el historial
3. NO termines la tarea sin haber enviado el mensaje usando las herramientas
4. Mantén un tono cálido y profesional como recepcionista

PASOS OBLIGATORIOS:
1. Genera tu respuesta como Jennifer
2. USA WhatsAppTool para ENVIAR la respuesta al usuario
3. USA AIResponseTool para guardar la respuesta en el historial
4. Confirma que ambos pasos se completaron

Recuerda: Tu trabajo no está completo hasta que hayas ENVIADO el mensaje usando WhatsAppTool.
"""
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
                ConversationContextTool(),
            ],
            verbose=True
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
        return Agent(
            config=self.agents_config['voice_agent'],
            
            tools=[
                ElevenLabsVoiceTool(),
                ElevenLabsCallTool(),
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
            tools=[WhatsAppTool(), ConversationContextTool()],
        )

    @task
    def whatsapp_voice_call(self) -> Task:
        return Task(
            config=self.tasks_config['whatsapp_voice_call'],
            tools=[ElevenLabsCallTool(), ElevenLabsVoiceTool()],
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
            tools=[InstagramTool(), ConversationContextTool()],
        )

    # Tareas por Canal - Gmail
    @task
    def gmail_message(self) -> Task:
        return Task(
            config=self.tasks_config['gmail_message'],
            tools=[GmailIMAPTool(), GmailIMAPSearchTool(), ConversationContextTool()],
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
        
        print(f"📋 Contexto obtenido: {context_result[:200]}..." if len(context_result) > 200 else f"📋 Contexto: {context_result}")
        
        try:
            # Determinar qué tarea ejecutar basado en el canal
            if channel.lower() == 'whatsapp':
                if message_type == 'voice_call':
                    # Crear crew con tarea específica
                    crew = Crew(
                        agents=[self.voice_agent(), self.whatsapp_agent()],
                        tasks=[self.whatsapp_voice_call()],
                        process=Process.sequential,
                        verbose=True
                    )
                    result = crew.kickoff(inputs=inputs)
                else:
                    # Crear crew con tarea específica
                    crew = Crew(
                        agents=[self.whatsapp_agent(), self.coordinator()],
                        tasks=[self.whatsapp_text_message()],
                        process=Process.sequential,
                        verbose=True
                    )
                    result = crew.kickoff(inputs=inputs)
            elif channel.lower() == 'messenger':
                crew = Crew(
                    agents=[self.messenger_agent(), self.coordinator()],
                    tasks=[self.messenger_message()],
                    process=Process.sequential,
                    verbose=True
                )
                result = crew.kickoff(inputs=inputs)
            elif channel.lower() == 'instagram':
                crew = Crew(
                    agents=[self.instagram_agent(), self.coordinator()],
                    tasks=[self.instagram_message()],
                    process=Process.sequential,
                    verbose=True
                )
                result = crew.kickoff(inputs=inputs)
            elif channel.lower() == 'gmail':
                crew = Crew(
                    agents=[self.gmail_agent(), self.coordinator()],
                    tasks=[self.gmail_message()],
                    process=Process.sequential,
                    verbose=True
                )
                # El kickoff usará el diccionario 'inputs' que ahora contiene el ID
                result = crew.kickoff(inputs=inputs) 
            else:
                # Canal no reconocido, usar coordinador
                crew = Crew(
                    agents=[self.coordinator()],
                    tasks=[self.coordinate_message()],
                    process=Process.sequential,
                    verbose=True
                )
                result = crew.kickoff(inputs=inputs)
            
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