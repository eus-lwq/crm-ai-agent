#!/usr/bin/env python3
"""
Fix Gmail token by regenerating it with correct scopes.
This script will delete the old token and create a new one with proper Gmail scopes.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Gmail API scopes required for GmailToolkit
# These scopes allow reading, sending, and modifying emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

def fix_gmail_token(credentials_path: str = "credentials.json", token_path: str = "token.json"):
    """
    Regenerate Gmail token with correct scopes.
    
    Args:
        credentials_path: Path to credentials.json
        token_path: Path to token.json (will be overwritten)
    """
    print("=" * 60)
    print("Gmail Token Fix Script")
    print("=" * 60)
    print()
    
    # Check if credentials.json exists
    if not os.path.exists(credentials_path):
        print(f"❌ Error: {credentials_path} not found!")
        print()
        print("Please download credentials.json from:")
        print("  Google Cloud Console > APIs & Services > Credentials")
        print("  Create OAuth 2.0 Client ID credentials (Desktop app)")
        print()
        return False
    
    # Backup old token if it exists
    if os.path.exists(token_path):
        backup_path = f"{token_path}.backup"
        print(f"📦 Backing up old token to {backup_path}")
        os.rename(token_path, backup_path)
    
    print(f"🔑 Using credentials from: {credentials_path}")
    print(f"💾 Token will be saved to: {token_path}")
    print()
    print("Required scopes:")
    for scope in SCOPES:
        print(f"  • {scope}")
    print()
    
    try:
        # Check if we have an existing token to check scopes
        creds = None
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                print("✅ Existing token found, checking validity...")
            except Exception as e:
                print(f"⚠️  Existing token has invalid scopes: {e}")
                print("   Will create new token...")
                creds = None
        
        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Token expired, attempting refresh...")
                try:
                    creds.refresh(Request())
                    print("✅ Token refreshed successfully!")
                except Exception as e:
                    print(f"⚠️  Token refresh failed: {e}")
                    print("   Starting new OAuth flow...")
                    creds = None
            
            if not creds:
                print("🚀 Starting OAuth flow...")
                print("   A browser window will open for authentication.")
                print()
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ Authentication successful!")
        
        # Save the credentials
        print()
        print(f"💾 Saving token to {token_path}...")
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        
        print()
        print("=" * 60)
        print("✅ Gmail token fixed successfully!")
        print("=" * 60)
        print()
        print(f"Token saved to: {token_path}")
        print(f"Scopes: {', '.join(creds.scopes)}")
        print()
        print("You can now use the Gmail agent to send emails.")
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Error fixing Gmail token")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure credentials.json is valid")
        print("  2. Make sure Gmail API is enabled in Google Cloud Console")
        print("  3. Make sure your email is added as a test user in OAuth consent screen")
        print("  4. Check that the OAuth consent screen is configured correctly")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix Gmail token with correct scopes")
    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Path to credentials.json (default: credentials.json)"
    )
    parser.add_argument(
        "--token",
        default="token.json",
        help="Path to token.json (default: token.json)"
    )
    
    args = parser.parse_args()
    
    success = fix_gmail_token(args.credentials, args.token)
    sys.exit(0 if success else 1)

