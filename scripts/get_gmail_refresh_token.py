"""Helper script to get Gmail refresh token via OAuth flow."""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_refresh_token():
    """
    Get Gmail refresh token via OAuth flow.
    
    This will open a browser window for you to authorize the app.
    After authorization, the refresh token will be printed.
    """
    creds = None
    
    # Check if we have credentials from a previous run
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Get client ID and secret from environment or user input
            client_id = os.getenv('GMAIL_CLIENT_ID') or input("Enter GMAIL_CLIENT_ID: ")
            client_secret = os.getenv('GMAIL_CLIENT_SECRET') or input("Enter GMAIL_CLIENT_SECRET: ")
            
            if not client_id or not client_secret:
                print("Error: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET are required")
                return
            
            # Create OAuth flow with proper redirect URIs
            # IMPORTANT: These redirect URIs must be added to your OAuth client in Google Cloud Console
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [
                            "http://localhost:8080",
                            "http://127.0.0.1:8080",
                            "http://localhost",
                            "urn:ietf:wg:oauth:2.0:oob"  # Out-of-band flow
                        ]
                    }
                },
                SCOPES
            )
            
            # Run the OAuth flow with a fixed port
            # Use port 8080 to match common redirect URI configurations
            try:
                creds = flow.run_local_server(port=8080, open_browser=True)
            except Exception as e:
                print(f"\n❌ OAuth flow failed: {e}")
                print("\nIf you got 'redirect_uri_mismatch' error:")
                print("1. Go to Google Cloud Console > APIs & Services > Credentials")
                print("2. Click on your OAuth 2.0 Client ID")
                print("3. Under 'Authorized redirect URIs', add:")
                print("   - http://localhost:8080")
                print("   - http://127.0.0.1:8080")
                print("   - http://localhost")
                print("4. Save and try again")
                print("\nOr use OAuth Playground instead (see docs/GMAIL_SETUP.md)")
                return
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
    
    # Print the refresh token
    if creds and creds.refresh_token:
        print("\n" + "=" * 60)
        print("SUCCESS! Your Gmail Refresh Token:")
        print("=" * 60)
        print(creds.refresh_token)
        print("=" * 60)
        print("\nAdd this to your .env file (make sure it's NOT commented out):")
        print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
        print("\n✅ Refresh token obtained successfully!")
    else:
        print("❌ Could not obtain refresh token")
        print("   Make sure you completed the OAuth flow and authorized the app")
    
    # Test the connection
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"\n✓ Connected to Gmail account: {profile.get('emailAddress')}")
    except Exception as e:
        print(f"\n⚠️  Could not verify connection: {e}")

if __name__ == "__main__":
    print("Gmail Refresh Token Generator")
    print("=" * 60)
    print("\nThis script will help you get a Gmail refresh token.")
    print("You'll need:")
    print("  1. GMAIL_CLIENT_ID")
    print("  2. GMAIL_CLIENT_SECRET")
    print("\n⚠️  IMPORTANT: If you get 'redirect_uri_mismatch' error:")
    print("   See docs/GMAIL_SETUP.md for detailed instructions")
    print("   Or use Google OAuth Playground (easier):")
    print("   https://developers.google.com/oauthplayground/")
    print("\nA browser window will open for you to authorize the app.\n")
    
    get_refresh_token()

