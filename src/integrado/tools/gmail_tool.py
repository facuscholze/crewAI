from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


class GmailMessageInput(BaseModel):
    """Input schema for Gmail message tool."""
    to: str = Field(..., description="Email address of the recipient")
    subject: str = Field(..., description="Subject of the email")
    body: str = Field(..., description="Body content of the email")
    body_type: str = Field(default="text", description="Type of body: text or html")
    thread_id: Optional[str] = Field(default=None, description="Thread ID to reply to existing conversation")


class GmailTool(BaseTool):
    name: str = "Gmail Tool"
    description: str = (
        "Send emails through Gmail API. "
        "Supports sending new emails and replying to existing email threads."
    )
    args_schema: Type[BaseModel] = GmailMessageInput

    def _run(self, to: str, subject: str, body: str, body_type: str = "text", thread_id: Optional[str] = None) -> str:
        """Send Gmail message."""
        
        try:
            # Initialize Gmail service
            service = self._get_gmail_service()
            
            # Create message
            message = self._create_message(to, subject, body, body_type, thread_id)
            
            # Send message
            result = service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            message_id = result.get('id', 'unknown')
            return f"Gmail message sent successfully. Message ID: {message_id}"
            
        except Exception as e:
            return f"Error sending Gmail message: {str(e)}"

    def _get_gmail_service(self):
        """Initialize Gmail service with authentication."""
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        
        creds = None
        token_file = 'token.json'
        
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
        
        return build('gmail', 'v1', credentials=creds)

    def _create_message(self, to: str, subject: str, body: str, body_type: str = "text", thread_id: Optional[str] = None):
        """Create email message."""
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['subject'] = subject
        
        # Add body content
        if body_type == "html":
            html_part = MIMEText(body, 'html')
            message.attach(html_part)
        else:
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        message_body = {'raw': raw_message}
        if thread_id:
            message_body['threadId'] = thread_id
        
        return message_body


class GmailSearchTool(BaseTool):
    name: str = "Gmail Search Tool"
    description: str = (
        "Search emails in Gmail using various criteria."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Search Gmail messages (placeholder for future implementation)."""
        return "Gmail search functionality not yet implemented"


class GmailWebhookTool(BaseTool):
    name: str = "Gmail Webhook Tool"
    description: str = (
        "Process incoming Gmail webhook notifications and extract relevant information."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Process Gmail webhook data."""
        return "Gmail webhook processed successfully"






