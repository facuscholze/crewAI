from crewai.tools import BaseTool
from typing import Type, Optional, List
from pydantic import BaseModel, Field
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from datetime import datetime, timedelta


class CalendarEventInput(BaseModel):
    """Input schema for Google Calendar event tool."""
    title: str = Field(..., description="Title of the event")
    description: str = Field(..., description="Description of the event")
    start_datetime: str = Field(..., description="Start date and time (ISO format: YYYY-MM-DDTHH:MM:SS)")
    end_datetime: str = Field(..., description="End date and time (ISO format: YYYY-MM-DDTHH:MM:SS)")
    attendees: Optional[List[str]] = Field(default=None, description="List of email addresses to invite")
    location: Optional[str] = Field(default=None, description="Location of the event")
    timezone: str = Field(default="America/Argentina/Buenos_Aires", description="Timezone for the event")


class CalendarUpdateEventInput(BaseModel):
    """Input schema for updating Google Calendar event."""
    event_id: str = Field(..., description="ID of the event to update")
    title: Optional[str] = Field(default=None, description="New title of the event")
    description: Optional[str] = Field(default=None, description="New description of the event")
    start_datetime: Optional[str] = Field(default=None, description="New start date and time (ISO format)")
    end_datetime: Optional[str] = Field(default=None, description="New end date and time (ISO format)")
    attendees: Optional[List[str]] = Field(default=None, description="New list of email addresses")
    location: Optional[str] = Field(default=None, description="New location of the event")


class CalendarTool(BaseTool):
    name: str = "Google Calendar Tool"
    description: str = (
        "Create, update, and manage Google Calendar events using Service Account. "
        "Supports scheduling meetings, setting reminders, and managing attendees."
    )
    args_schema: Type[BaseModel] = CalendarEventInput

    def _run(self, title: str, description: str, start_datetime: str, end_datetime: str, 
             attendees: Optional[List[str]] = None, location: Optional[str] = None, 
             timezone: str = "America/Argentina/Buenos_Aires") -> str:
        """Create Google Calendar event."""
        
        try:
            # Initialize Calendar service
            service = self._get_calendar_service()
            
            # Get calendar ID from environment
            calendar_id = os.getenv('CALENDAR_ID', 'primary')
            
            # Create event
            event = self._create_event_dict(title, description, start_datetime, end_datetime, 
                                          attendees, location, timezone)
            
            # Insert event
            result = service.events().insert(calendarId=calendar_id, body=event).execute()
            
            event_id = result.get('id', 'unknown')
            event_link = result.get('htmlLink', '')
            
            return f"✅ Evento creado exitosamente en Google Calendar:\n📅 Título: {title}\n🆔 ID: {event_id}\n🔗 Enlace: {event_link}\n📅 Fecha: {start_datetime} - {end_datetime}"
            
        except Exception as e:
            return f"❌ Error creando evento en Google Calendar: {str(e)}"

    def _get_calendar_service(self):
        """Initialize Calendar service with Service Account authentication."""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        # Get service account file path
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', './credenciales.json')
        
        if not os.path.exists(service_account_file):
            raise Exception(f"Service account file not found: {service_account_file}")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=SCOPES)
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            raise Exception(f"Error initializing Calendar service: {str(e)}")

    def _create_event_dict(self, title: str, description: str, start_datetime: str, end_datetime: str,
                          attendees: Optional[List[str]] = None, location: Optional[str] = None,
                          timezone: str = "America/Argentina/Buenos_Aires"):
        """Create event dictionary for Google Calendar API."""
        
        # Convert datetime strings to datetime objects
        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': timezone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 30},       # 30 minutes before
                ],
            },
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        if location:
            event['location'] = location
        
        return event


class CalendarUpdateTool(BaseTool):
    name: str = "Google Calendar Update Tool"
    description: str = (
        "Update existing Google Calendar events with new information using Service Account."
    )
    args_schema: Type[BaseModel] = CalendarUpdateEventInput

    def _run(self, event_id: str, title: Optional[str] = None, description: Optional[str] = None,
             start_datetime: Optional[str] = None, end_datetime: Optional[str] = None,
             attendees: Optional[List[str]] = None, location: Optional[str] = None) -> str:
        """Update Google Calendar event."""
        
        try:
            # Initialize Calendar service
            service = self._get_calendar_service()
            
            # Get calendar ID from environment
            calendar_id = os.getenv('CALENDAR_ID', 'primary')
            
            # Get existing event
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            
            # Update fields if provided
            if title:
                event['summary'] = title
            if description:
                event['description'] = description
            if start_datetime:
                start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                event['start']['dateTime'] = start_dt.isoformat()
            if end_datetime:
                end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
                event['end']['dateTime'] = end_dt.isoformat()
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            if location:
                event['location'] = location
            
            # Update event
            updated_event = service.events().update(
                calendarId=calendar_id, 
                eventId=event_id, 
                body=event
            ).execute()
            
            return f"✅ Evento actualizado exitosamente en Google Calendar:\n🆔 ID: {event_id}\n📅 Nuevo título: {updated_event.get('summary', 'N/A')}"
            
        except Exception as e:
            return f"❌ Error actualizando evento en Google Calendar: {str(e)}"

    def _get_calendar_service(self):
        """Initialize Calendar service with Service Account authentication."""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        # Get service account file path
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', './credenciales.json')
        
        if not os.path.exists(service_account_file):
            raise Exception(f"Service account file not found: {service_account_file}")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=SCOPES)
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            raise Exception(f"Error initializing Calendar service: {str(e)}")


class CalendarSearchTool(BaseTool):
    name: str = "Google Calendar Search Tool"
    description: str = (
        "Search and retrieve Google Calendar events based on various criteria using Service Account."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Search calendar events."""
        try:
            service = self._get_calendar_service()
            calendar_id = os.getenv('CALENDAR_ID', 'primary')
            
            # Get upcoming events
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return "📅 No hay eventos próximos en el calendario."
            
            result = "📅 **Próximos eventos:**\n\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                title = event.get('summary', 'Sin título')
                result += f"• **{title}** - {start}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error buscando eventos: {str(e)}"

    def _get_calendar_service(self):
        """Initialize Calendar service with Service Account authentication."""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', './credenciales.json')
        
        if not os.path.exists(service_account_file):
            raise Exception(f"Service account file not found: {service_account_file}")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=SCOPES)
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            raise Exception(f"Error initializing Calendar service: {str(e)}")






