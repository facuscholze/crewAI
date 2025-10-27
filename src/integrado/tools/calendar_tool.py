from crewai.tools import BaseTool
from typing import Type, Optional, List
from pydantic import BaseModel, Field
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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
    timezone: str = Field(default="UTC", description="Timezone for the event")


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
        "Create, update, and manage Google Calendar events. "
        "Supports scheduling meetings, setting reminders, and managing attendees."
    )
    args_schema: Type[BaseModel] = CalendarEventInput

    def _run(self, title: str, description: str, start_datetime: str, end_datetime: str, 
             attendees: Optional[List[str]] = None, location: Optional[str] = None, 
             timezone: str = "UTC") -> str:
        """Create Google Calendar event."""
        
        try:
            # Initialize Calendar service
            service = self._get_calendar_service()
            
            # Create event
            event = self._create_event_dict(title, description, start_datetime, end_datetime, 
                                          attendees, location, timezone)
            
            # Insert event
            result = service.events().insert(calendarId='primary', body=event).execute()
            
            event_id = result.get('id', 'unknown')
            event_link = result.get('htmlLink', '')
            
            return f"Calendar event created successfully. Event ID: {event_id}. Link: {event_link}"
            
        except Exception as e:
            return f"Error creating calendar event: {str(e)}"

    def _get_calendar_service(self):
        """Initialize Calendar service with authentication."""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        creds = None
        token_file = 'calendar_token.json'
        
        # Load existing credentials
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json'), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)

    def _create_event_dict(self, title: str, description: str, start_datetime: str, end_datetime: str,
                          attendees: Optional[List[str]] = None, location: Optional[str] = None,
                          timezone: str = "UTC"):
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
        "Update existing Google Calendar events with new information."
    )
    args_schema: Type[BaseModel] = CalendarUpdateEventInput

    def _run(self, event_id: str, title: Optional[str] = None, description: Optional[str] = None,
             start_datetime: Optional[str] = None, end_datetime: Optional[str] = None,
             attendees: Optional[List[str]] = None, location: Optional[str] = None) -> str:
        """Update Google Calendar event."""
        
        try:
            # Initialize Calendar service
            service = self._get_calendar_service()
            
            # Get existing event
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
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
                calendarId='primary', 
                eventId=event_id, 
                body=event
            ).execute()
            
            return f"Calendar event updated successfully. Event ID: {event_id}"
            
        except Exception as e:
            return f"Error updating calendar event: {str(e)}"

    def _get_calendar_service(self):
        """Initialize Calendar service with authentication."""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        creds = None
        token_file = 'calendar_token.json'
        
        # Load existing credentials
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json'), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)


class CalendarSearchTool(BaseTool):
    name: str = "Google Calendar Search Tool"
    description: str = (
        "Search and retrieve Google Calendar events based on various criteria."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Search calendar events (placeholder for future implementation)."""
        return "Calendar search functionality not yet implemented"
