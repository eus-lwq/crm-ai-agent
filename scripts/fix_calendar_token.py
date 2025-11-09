"""Helper script to fix calendar token scope issues."""
import os
import sys

def fix_calendar_token():
    """Delete token.json if it exists to force re-authentication with Calendar scopes."""
    token_path = "token.json"
    
    if os.path.exists(token_path):
        print(f"Found {token_path}")
        response = input("This token was created for Gmail. Delete it to re-authenticate with Calendar scopes? (y/n): ")
        if response.lower() == 'y':
            os.remove(token_path)
            print(f"✓ Deleted {token_path}")
            print("\nNext steps:")
            print("1. Make sure Google Calendar API is enabled in your Google Cloud project")
            print("2. Run: uv run python example_calendar_agent.py")
            print("3. A browser will open for you to authorize Calendar access")
            print("4. A new token.json will be created with the correct scopes")
        else:
            print("Keeping existing token.json")
            print("\nNote: You may need to delete it manually if you get 'invalid_scope' errors")
    else:
        print(f"{token_path} not found. You can run the calendar agent directly - it will create a new token.")

if __name__ == "__main__":
    fix_calendar_token()

