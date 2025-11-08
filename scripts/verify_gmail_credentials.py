"""Verify Gmail credentials are correctly configured."""
import sys
import importlib.util

# Load email_sender directly
spec = importlib.util.spec_from_file_location("email_sender", "services/email_sender.py")
email_sender = importlib.util.module_from_spec(spec)
sys.modules["email_sender"] = email_sender
spec.loader.exec_module(email_sender)

from config import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

print("=" * 60)
print("Gmail Credentials Verification")
print("=" * 60)

# Check config
print("\n1. Checking .env configuration...")
print(f"   GMAIL_CLIENT_ID: {'✓ SET' if settings.gmail_client_id else '✗ NOT SET'}")
print(f"   GMAIL_CLIENT_SECRET: {'✓ SET' if settings.gmail_client_secret else '✗ NOT SET'}")
print(f"   GMAIL_REFRESH_TOKEN: {'✓ SET' if settings.gmail_refresh_token else '✗ NOT SET'}")
print(f"   GMAIL_USER_EMAIL: {'✓ SET' if settings.gmail_user_email else '✗ NOT SET'}")

if not all([settings.gmail_client_id, settings.gmail_client_secret, settings.gmail_refresh_token]):
    print("\n❌ Missing required credentials in .env")
    sys.exit(1)

# Test credential creation
print("\n2. Testing credential creation...")
try:
    creds = Credentials(
        token=None,
        refresh_token=settings.gmail_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        scopes=['https://www.googleapis.com/auth/gmail.send'],
    )
    print("   ✓ Credentials object created")
except Exception as e:
    print(f"   ✗ Error creating credentials: {e}")
    sys.exit(1)

# Test token refresh
print("\n3. Testing token refresh...")
try:
    creds.refresh(Request())
    print("   ✓ Token refreshed successfully!")
    print(f"   ✓ Access token obtained: {bool(creds.token)}")
    print(f"   ✓ Credentials valid: {creds.valid}")
except Exception as e:
    error_msg = str(e)
    print(f"   ✗ Token refresh failed: {error_msg}")
    
    if "unauthorized_client" in error_msg.lower():
        print("\n" + "=" * 60)
        print("❌ ISSUE: Refresh token doesn't match client credentials")
        print("=" * 60)
        print("\nThis usually means:")
        print("  1. The refresh token was obtained using different client ID/secret")
        print("  2. You used OAuth Playground with different credentials")
        print("  3. The client ID/secret in .env don't match the token")
        print("\nSolution:")
        print("  1. Go to OAuth Playground: https://developers.google.com/oauthplayground/")
        print("  2. Click gear icon → Use your own OAuth credentials")
        print(f"  3. Enter EXACTLY these credentials:")
        print(f"     Client ID: {settings.gmail_client_id}")
        print(f"     Client Secret: {settings.gmail_client_secret}")
        print("  4. Get a new refresh token using these credentials")
        print("  5. Update GMAIL_REFRESH_TOKEN in .env with the new token")
    else:
        print(f"\nError details: {e}")
    sys.exit(1)

# Test Gmail API connection
print("\n4. Testing Gmail API connection...")
try:
    from googleapiclient.discovery import build
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    print(f"   ✓ Connected to Gmail!")
    print(f"   ✓ Email: {profile.get('emailAddress')}")
    print(f"   ✓ Messages total: {profile.get('messagesTotal')}")
except Exception as e:
    print(f"   ✗ Gmail API connection failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All credentials verified successfully!")
print("=" * 60)
print("\nYou can now send emails using the EmailSender service.")

