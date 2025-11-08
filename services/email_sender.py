"""Email sending service using Gmail API with OAuth 2.0.

Follows Google's OAuth 2.0 best practices:
- Uses refresh tokens for long-term access
- Automatically refreshes expired access tokens
- Uses Google's OAuth 2.0 libraries
"""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings


class EmailSender:
    """Service for sending emails via Gmail API using OAuth 2.0."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self):
        self.service = None
        self.creds = None
        self._service_initialized = False
    
    def _get_credentials(self) -> Optional[Credentials]:
        """
        Get and refresh OAuth 2.0 credentials.
        
        Following Google's OAuth 2.0 best practices:
        - Uses refresh token to obtain new access tokens
        - Automatically refreshes expired tokens
        """
        if not self._service_initialized:
            try:
                if not all([
                    settings.gmail_client_id,
                    settings.gmail_client_secret,
                    settings.gmail_refresh_token,
                ]):
                    raise Exception(
                        "Gmail credentials not configured. "
                        "Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, and GMAIL_REFRESH_TOKEN in .env"
                    )
                
                # Create credentials from refresh token (Step 5: Refresh access token)
                # This follows Google's OAuth 2.0 pattern for server-side applications
                self.creds = Credentials(
                    token=None,  # Will be obtained via refresh
                    refresh_token=settings.gmail_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.gmail_client_id,
                    client_secret=settings.gmail_client_secret,
                    scopes=self.SCOPES,
                )
                
                # Refresh the token if needed (access tokens have limited lifetimes)
                # This is Step 5 from Google's OAuth 2.0 documentation
                if not self.creds.valid:
                    if self.creds.expired and self.creds.refresh_token:
                        try:
                            self.creds.refresh(Request())
                        except Exception as refresh_error:
                            error_msg = str(refresh_error)
                            if "unauthorized_client" in error_msg.lower():
                                raise Exception(
                                    "Refresh token doesn't match client credentials. "
                                    "The refresh token must be obtained using the same "
                                    "GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET that are in your .env file. "
                                    "If you got the token from OAuth Playground, make sure you used "
                                    "the same client ID and secret."
                                )
                            else:
                                    raise Exception(f"Could not refresh token: {refresh_error}")
                    else:
                        raise Exception("Invalid credentials. Refresh token may be expired or revoked.")
                
                self._service_initialized = True
                
            except Exception as e:
                print(f"Warning: Could not initialize Gmail credentials: {e}")
                self.creds = None
                self._service_initialized = True
        
        return self.creds
    
    def _get_service(self):
        """Get Gmail API service instance."""
        creds = self._get_credentials()
        if not creds:
            return None
        
        if not self.service:
            try:
                # Build the Gmail service (Step 4: Send access token to API)
                self.service = build('gmail', 'v1', credentials=creds)
            except Exception as e:
                print(f"Warning: Could not build Gmail service: {e}")
                return None
        
        # Refresh token if expired before making API calls
        if self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
            except Exception as e:
                print(f"Warning: Could not refresh token: {e}")
                return None
        
        return self.service
    
    def _create_message(self, to: str, subject: str, body: str, 
                       from_email: Optional[str] = None,
                       cc: Optional[List[str]] = None,
                       bcc: Optional[List[str]] = None) -> dict:
        """Create a MIME message for an email."""
        message = MIMEMultipart()
        
        from_addr = from_email or settings.gmail_user_email
        if not from_addr:
            raise ValueError("From email not specified and GMAIL_USER_EMAIL not set")
        
        message['to'] = to
        message['from'] = from_addr
        message['subject'] = subject
        
        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)
        
        # Add body
        message.attach(MIMEText(body, 'plain'))
        
        # Encode message (base64url encoding as per Gmail API requirements)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
    
    async def send_email(self, to: str, subject: str, body: str,
                        from_email: Optional[str] = None,
                        cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> str:
        """
        Send an email via Gmail API using OAuth 2.0.
        
        This follows Google's OAuth 2.0 flow:
        - Uses stored refresh token to get access token
        - Sends access token in Authorization header (Step 4)
        - Automatically refreshes token if expired
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email (defaults to GMAIL_USER_EMAIL)
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            Message ID of the sent email
            
        Raises:
            Exception: If Gmail service is not configured or sending fails
        """
        service = self._get_service()
        if not service:
            raise Exception(
                "Gmail service not available. Configure Gmail credentials in .env"
            )
        
        try:
            message = self._create_message(to, subject, body, from_email, cc, bcc)
            
            # Send the message (Step 4: Send access token to API)
            # The access token is automatically included in the Authorization header
            sent_message = service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            return sent_message['id']
            
        except HttpError as error:
            error_content = error.content.decode('utf-8') if error.content else str(error)
            raise Exception(f"Error sending email: {error_content}")
    
    async def send_html_email(self, to: str, subject: str, html_body: str,
                             from_email: Optional[str] = None,
                             plain_text: Optional[str] = None,
                             cc: Optional[List[str]] = None,
                             bcc: Optional[List[str]] = None) -> str:
        """
        Send an HTML email via Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_body: Email body (HTML)
            from_email: Sender email (defaults to GMAIL_USER_EMAIL)
            plain_text: Plain text alternative (optional, recommended)
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            Message ID of the sent email
        """
        service = self._get_service()
        if not service:
            raise Exception(
                "Gmail service not available. Configure Gmail credentials in .env"
            )
        
        try:
            message = MIMEMultipart('alternative')
            
            from_addr = from_email or settings.gmail_user_email
            if not from_addr:
                raise ValueError("From email not specified and GMAIL_USER_EMAIL not set")
            
            message['to'] = to
            message['from'] = from_addr
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            # Add plain text version if provided (best practice for email)
            if plain_text:
                message.attach(MIMEText(plain_text, 'plain'))
            
            # Add HTML version
            message.attach(MIMEText(html_body, 'html'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the message
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return sent_message['id']
            
        except HttpError as error:
            error_content = error.content.decode('utf-8') if error.content else str(error)
            raise Exception(f"Error sending HTML email: {error_content}")

