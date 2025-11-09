"""Email monitor service that checks for unread emails, extracts business/deal data, and stores in BigQuery."""
import os
import asyncio
import base64
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

from services.email_extractor import EmailExtractorAgent
from config import settings

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']


def _get_credentials(credentials_path: str = "credentials.json", token_path: str = "token.json") -> Optional[Credentials]:
    """
    Get valid user credentials from storage.
    
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    """
    creds = None
    
    # Load existing token
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Warning: Could not load token from {token_path}: {e}")
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Warning: Could not refresh token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"credentials.json not found at {credentials_path}. "
                    "Download it from Google Cloud Console > APIs & Services > Credentials."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def _parse_email_content(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse email content from Gmail API message.
    
    Returns:
        Dictionary with 'subject', 'from', 'to', 'date', 'body', 'message_id'
    """
    headers = message.get('payload', {}).get('headers', [])
    
    # Extract headers
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
    from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
    to_email = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
    
    # Extract body
    body = ''
    payload = message.get('payload', {})
    
    def extract_body(part):
        """Recursively extract body from email parts."""
        body_text = ''
        if part.get('body', {}).get('data'):
            data = part['body']['data']
            body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        if part.get('parts'):
            for subpart in part['parts']:
                body_text += extract_body(subpart)
        
        return body_text
    
    body = extract_body(payload)
    
    # Clean HTML tags if present
    if '<html' in body.lower() or '<body' in body.lower():
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(body, 'html.parser')
            body = soup.get_text(separator='\n', strip=True)
        except:
            # If BeautifulSoup fails, use regex to remove HTML tags
            body = re.sub(r'<[^>]+>', '', body)
    
    return {
        'subject': subject,
        'from': from_email,
        'to': to_email,
        'date': date,
        'body': body.strip(),
        'message_id': message['id']
    }


def _is_business_related(extracted_data, email_subject: str = "", email_body: str = "") -> bool:
    """
    Determine if an email is business/deal related (software/tech business, not promotions).
    
    An email is considered business-related if it has:
    - A company name AND (deal value OR next step OR follow-up date), OR
    - Notes that contain software/tech business keywords (not promotional keywords)
    
    Filters out promotional/marketing emails.
    """
    # Combine subject and body for keyword checking
    combined_text = f"{email_subject} {email_body}".lower()
    
    # Filter out promotional/marketing emails
    promotional_keywords = [
        'discount', 'sale', 'off', 'promotion', 'coupon', 'deal of the day',
        'limited time', 'special offer', 'buy now', 'shop now', 'order now',
        'free shipping', 'save', 'percent off', '% off', 'clearance',
        'flash sale', 'daily deal', 'groupon', 'retail', 'cosmetics',
        'fashion', 'apparel', 'jewelry', 'furniture', 'home decor',
        'subscription', 'newsletter', 'unsubscribe', 'marketing',
        'advertisement', 'ad', 'promo', 'bargain', 'bogo'
    ]
    
    # If email contains promotional keywords, it's likely not a business deal
    if any(keyword in combined_text for keyword in promotional_keywords):
        return False
    
    # Check for key business indicators (software/tech related)
    # Must have at least company name AND one other indicator
    has_company = bool(extracted_data.company and extracted_data.company.strip())
    has_deal_value = bool(extracted_data.deal_value)
    has_next_step = bool(extracted_data.next_step and extracted_data.next_step.strip())
    has_follow_up = bool(extracted_data.follow_up_date)
    
    # Check notes for software/tech business keywords
    has_business_notes = False
    if extracted_data.notes:
        software_business_keywords = [
            'proposal', 'contract', 'meeting', 'call', 'discussion',
            'project', 'client', 'customer', 'agreement', 'negotiation',
            'partnership', 'collaboration', 'integration', 'api', 'sdk',
            'sla', 'timeline', 'deadline', 'budget', 'quote', 'invoice',
            'software', 'platform', 'service', 'solution', 'implementation',
            'consulting', 'development', 'custom', 'enterprise', 'b2b'
        ]
        notes_lower = extracted_data.notes.lower()
        if any(keyword in notes_lower for keyword in software_business_keywords):
            has_business_notes = True
    
    # Business-related if: (company + deal_value) OR (company + next_step) OR 
    # (company + follow_up) OR (company + business_notes) OR (deal_value + next_step)
    if has_company:
        if has_deal_value or has_next_step or has_follow_up or has_business_notes:
            return True
    
    # Or if it has deal value AND next step (strong indicator of business deal)
    if has_deal_value and has_next_step:
        return True
    
    return False


class EmailMonitor:
    """
    Email monitor service that:
    1. Checks for unread emails in real-time (every 1 second)
    2. Extracts structured data from all unread emails
    3. Stores all emails in BigQuery immediately (no filtering)
    4. Marks processed emails as read
    """
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        """
        Initialize email monitor.
        
        Args:
            credentials_path: Path to credentials.json
            token_path: Path to token.json
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.extractor = EmailExtractorAgent()
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of Gmail service."""
        if self._initialized:
            return
        
        try:
            creds = _get_credentials(self.credentials_path, self.token_path)
            self.service = build('gmail', 'v1', credentials=creds)
            self._initialized = True
        except Exception as e:
            print(f"Warning: Could not initialize Gmail service: {e}")
            self._initialized = True
    
    def _get_unread_emails(self, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Get list of unread email message IDs.
        
        Args:
            max_results: Maximum number of emails to retrieve (default: 3)
            
        Returns:
            List of message dictionaries (limited to first max_results emails)
        """
        if not self.service:
            raise Exception("Gmail service not initialized")
        
        try:
            # Search for unread emails (optimized for real-time sync)
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            # Get full message details (batch processing for efficiency)
            full_messages = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    full_messages.append(message)
                except Exception as e:
                    print(f"Error retrieving message {msg['id']}: {e}")
                    continue
            
            return full_messages
            
        except HttpError as error:
            # Handle rate limiting gracefully
            if error.resp.status == 429:
                print(f"⚠️  Rate limit hit, will retry on next cycle")
            else:
                print(f"An error occurred: {error}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching emails: {e}")
            return []
    
    def _mark_as_read(self, message_id: str) -> bool:
        """
        Mark an email as read by removing the UNREAD label.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error marking message {message_id} as read: {e}")
            return False
    
    async def process_unread_emails(self, max_results: int = 3) -> Dict[str, Any]:
        """
        Process unread emails: extract business data and store in BigQuery.
        
        Args:
            max_results: Maximum number of emails to process in one run (default: 3)
            
        Returns:
            Dictionary with processing results
        """
        self._initialize()
        
        if not self.service:
            return {
                "status": "error",
                "error": "Gmail service not initialized",
                "processed": 0,
                "stored": 0,
                "skipped": 0
            }
        
        # Get unread emails
        unread_messages = self._get_unread_emails(max_results)
        
        if not unread_messages:
            return {
                "status": "success",
                "message": "No unread emails found",
                "processed": 0,
                "stored": 0,
                "skipped": 0
            }
        
        processed = 0
        stored = 0
        skipped = 0
        errors = []
        
        if unread_messages:
            print(f"📧 Found {len(unread_messages)} unread email(s) - processing in real-time...")
        
        for message in unread_messages:
            try:
                # Parse email content
                email_data = _parse_email_content(message)
                message_id = email_data['message_id']
                
                print(f"\nProcessing email: {email_data['subject']}")
                print(f"From: {email_data['from']}")
                
                # Prepare email metadata for extraction
                email_metadata = {
                    "subject": email_data['subject'],
                    "from": email_data['from'],
                    "to": email_data['to'],
                    "date": email_data['date']
                }
                
                # Extract structured data and store in BigQuery (no business-related filtering)
                print("📧 Processing email - extracting structured data and storing in BigQuery...")
                
                # Store in BigQuery immediately (real-time sync)
                result = await self.extractor.extract_and_store(
                    email_data['body'],
                    email_metadata
                )
                
                if result["status"] == "success":
                    stored += 1
                    print(f"✅ Real-time sync: Stored in BigQuery: {result['table_id']}")
                    print(f"   Fields extracted: {sum(1 for v in result['normalized_data'].values() if v is not None)}/{len(result['normalized_data'])}")
                    
                    # Mark as read immediately after successful storage
                    if self._mark_as_read(message_id):
                        print(f"   ✓ Marked email as read")
                    else:
                        print(f"   ⚠️  Could not mark email as read")
                else:
                    skipped += 1
                    errors.append(f"Failed to store email {message_id}: {result.get('error')}")
                    print(f"❌ Failed to store in real-time: {result.get('error')}")
                    # Still mark as read to avoid reprocessing failed emails
                    self._mark_as_read(message_id)
                
                processed += 1
                
            except Exception as e:
                errors.append(f"Error processing email {message.get('id', 'unknown')}: {e}")
                print(f"❌ Error processing email: {e}")
                continue
        
        return {
            "status": "success",
            "processed": processed,
            "stored": stored,
            "skipped": skipped,
            "errors": errors,
            "message": f"Processed {processed} email(s), stored {stored} in BigQuery, {skipped} skipped due to errors"
        }
    
    async def run_continuous(self, interval_minutes: int = 30):
        """
        Run email monitoring continuously, checking every N minutes.
        
        Args:
            interval_minutes: Minutes between checks (default: 30)
        """
        print(f"Starting email monitor (checking every {interval_minutes} minutes)...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                print(f"\n{'='*70}")
                print(f"Checking for unread emails at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*70}")
                
                # Process first 3 unread emails
                result = await self.process_unread_emails(max_results=3)
                
                print(f"\nSummary:")
                print(f"  Processed: {result['processed']}")
                print(f"  Stored in BigQuery: {result['stored']}")
                print(f"  Skipped (not business-related): {result['skipped']}")
                if result.get('errors'):
                    print(f"  Errors: {len(result['errors'])}")
                    for error in result['errors']:
                        print(f"    - {error}")
                
                # Wait for next check
                print(f"\nWaiting {interval_minutes} minutes until next check...")
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n\nStopping email monitor...")
                break
            except Exception as e:
                print(f"\nError in monitoring loop: {e}")
                print(f"Waiting {interval_minutes} minutes before retry...")
                await asyncio.sleep(interval_minutes * 60)

