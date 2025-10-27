# 🚀 Integrado - Sistema Multiagente Omnicanal

**Integrado** es un sistema multiagente avanzado construido con [crewAI](https://crewai.com) que permite la comunicación omnicanal inteligente a través de múltiples plataformas. El sistema coordina agentes especializados para manejar WhatsApp, Messenger, Instagram, Gmail, Google Calendar y llamadas de voz usando ElevenLabs.

## 🎯 Características Principales

### 🤖 Agentes Especializados
- **Coordinador Principal**: Gestiona y distribuye tareas entre agentes especializados
- **Agente WhatsApp**: Maneja mensajes de texto, voz y llamadas
- **Agente Messenger**: Gestiona conversaciones con elementos interactivos
- **Agente Instagram**: Comunicación visual y creativa
- **Agente Gmail**: Emails profesionales estructurados
- **Agente Calendar**: Programación y gestión de eventos
- **Agente Voz**: Llamadas de voz usando ElevenLabs AI

### 📱 Canales Soportados
- **WhatsApp Business API**: Mensajes, audios y llamadas
- **Facebook Messenger**: Conversaciones interactivas
- **Instagram Direct**: Comunicación visual
- **Gmail**: Correos electrónicos profesionales
- **Google Calendar**: Programación de eventos
- **ElevenLabs**: Llamadas de voz con IA

### 🧠 Funcionalidades Inteligentes
- **Contexto por Conversación**: Mantiene historial y preferencias por usuario
- **Coordinación Multiagente**: Proceso jerárquico para distribución de tareas
- **API REST Completa**: Endpoints para integración externa
- **Webhooks**: Recepción automática de mensajes
- **Base de Datos**: Almacenamiento de conversaciones y eventos

## 🛠️ Instalación

### Prerrequisitos
- Python >=3.10 <3.14
- [UV](https://docs.astral.sh/uv/) para gestión de dependencias

### Pasos de Instalación

1. **Instalar UV** (si no está instalado):
```bash
pip install uv
```

2. **Clonar e instalar dependencias**:
```bash
cd integrado
crewai install
```

3. **Configurar variables de entorno**:
```bash
cp env.example .env
# Editar .env con tus credenciales
```

4. **Inicializar base de datos**:
```bash
python -c "from src.integrado.database.database import create_tables; create_tables()"
```

## ⚙️ Configuración

### Variables de Entorno Requeridas

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id

# Google APIs
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GMAIL_CREDENTIALS_PATH=path/to/gmail_credentials.json

# Facebook/Meta APIs
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
FACEBOOK_APP_ID=your_facebook_app_id

# Instagram Basic Display API
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_APP_ID=your_instagram_app_id

# ElevenLabs Voice API
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Database Configuration
DATABASE_URL=sqlite:///./integrado.db
```

### Configuración de Agentes

Los agentes están configurados en `src/integrado/config/agents.yaml`:
- Roles especializados por canal
- Objetivos específicos para cada agente
- Backstories para personalización de comportamiento

### Configuración de Tareas

Las tareas están definidas en `src/integrado/config/tasks.yaml`:
- Tareas de coordinación
- Tareas específicas por canal
- Tareas de gestión de calendario
- Tareas de seguimiento

## 🚀 Uso

### Iniciar el Servidor

```bash
# Usando crewAI CLI
crewai run

# O directamente con Python
python -m integrado.main

# El servidor se iniciará en http://localhost:8000
```

### API Endpoints

#### Procesar Mensaje
```bash
POST /api/message
{
  "channel": "whatsapp",
  "user_id": "1234567890",
  "message": "Hola, necesito ayuda",
  "message_type": "text"
}
```

#### Programar Evento
```bash
POST /api/calendar/schedule
{
  "user_id": "1234567890",
  "title": "Reunión de trabajo",
  "description": "Reunión semanal del equipo",
  "start_datetime": "2024-01-15T10:00:00",
  "end_datetime": "2024-01-15T11:00:00",
  "location": "Oficina principal",
  "timezone": "America/Mexico_City"
}
```

#### Webhooks
```bash
POST /webhook/whatsapp
POST /webhook/messenger
POST /webhook/instagram
POST /webhook/gmail
```

### Ejemplos de Uso Programático

```python
from integrado.crew import Integrado

# Inicializar el crew
crew = Integrado()

# Procesar mensaje de WhatsApp
result = crew.process_omnicanal_message(
    channel="whatsapp",
    user_id="1234567890",
    message="Quiero agendar una cita",
    message_type="text"
)

# Programar evento
event_details = {
    'title': 'Cita médica',
    'description': 'Consulta de rutina',
    'start_datetime': '2024-01-15T14:00:00',
    'end_datetime': '2024-01-15T15:00:00',
    'location': 'Clínica Central'
}

result = crew.schedule_calendar_event(
    user_id="1234567890",
    event_details=event_details
)
```

## 🏗️ Arquitectura

### Estructura del Proyecto
```
integrado/
├── src/integrado/
│   ├── config/
│   │   ├── agents.yaml          # Configuración de agentes
│   │   └── tasks.yaml           # Configuración de tareas
│   ├── tools/
│   │   ├── whatsapp_tool.py     # Herramientas WhatsApp
│   │   ├── messenger_tool.py    # Herramientas Messenger
│   │   ├── instagram_tool.py    # Herramientas Instagram
│   │   ├── gmail_tool.py        # Herramientas Gmail
│   │   ├── calendar_tool.py     # Herramientas Calendar
│   │   ├── elevenlabs_tool.py   # Herramientas ElevenLabs
│   │   └── context_manager.py   # Gestión de contexto
│   ├── database/
│   │   ├── models.py            # Modelos de base de datos
│   │   └── database.py          # Configuración de DB
│   ├── crew.py                  # Crew principal
│   └── main.py                  # API y servidor
├── env.example                  # Ejemplo de variables de entorno
└── README.md                    # Este archivo
```

### Flujo de Comunicación

1. **Recepción**: Mensaje llega via webhook o API
2. **Coordinación**: Coordinador analiza y distribuye tarea
3. **Procesamiento**: Agente especializado procesa el mensaje
4. **Contexto**: Sistema actualiza contexto de conversación
5. **Respuesta**: Agente genera y envía respuesta apropiada
6. **Seguimiento**: Sistema programa seguimientos si es necesario

## 🔧 Desarrollo

### Agregar Nuevo Canal

1. **Crear herramienta** en `src/integrado/tools/`
2. **Agregar agente** en `config/agents.yaml`
3. **Definir tareas** en `config/tasks.yaml`
4. **Actualizar crew** en `crew.py`
5. **Agregar endpoint** en `main.py`

### Testing

```bash
# Test del crew
crewai test 10 gpt-4

# Test específico
python -c "from integrado.crew import Integrado; crew = Integrado(); print('Crew initialized successfully')"
```

## 📚 Documentación

- [CrewAI Documentation](https://docs.crewai.com)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Facebook Messenger API](https://developers.facebook.com/docs/messenger-platform)
- [Instagram Basic Display API](https://developers.facebook.com/docs/instagram-basic-display-api)
- [Gmail API](https://developers.google.com/gmail/api)
- [Google Calendar API](https://developers.google.com/calendar)
- [ElevenLabs API](https://docs.elevenlabs.io)

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

- [Documentación CrewAI](https://docs.crewai.com)
- [GitHub Repository](https://github.com/joaomdmoura/crewai)
- [Discord Community](https://discord.com/invite/X4JWnZnxPb)
- [Chat con Docs](https://chatg.pt/DWjSBZn)

---

**¡Construyamos el futuro de la comunicación omnicanal con la potencia de crewAI!** 🚀
