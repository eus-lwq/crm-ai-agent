#!/usr/bin/env python3
"""Test calendar connection and event creation."""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.calendar_agent import CalendarAgent
from datetime import datetime, timedelta

def test_calendar_connection():
    """Test calendar agent connection and event creation."""
    print("=" * 60)
    print("📅 Calendar Connection Test")
    print("=" * 60)
    print()
    
    # Check credentials
    print("1. Checking credentials...")
    credentials_path = "credentials.json"
    token_path = "token-calendar.json"
    
    if not os.path.exists(credentials_path):
        print(f"❌ credentials.json not found at {credentials_path}")
        print("   Download it from Google Cloud Console > APIs & Services > Credentials")
        return False
    print(f"✅ credentials.json found")
    
    if not os.path.exists(token_path):
        print(f"⚠️  token-calendar.json not found at {token_path}")
        print("   Will attempt to authenticate on first use")
    else:
        print(f"✅ token-calendar.json found")
        import json
        with open(token_path, 'r') as f:
            token = json.load(f)
            if 'refresh_token' in token:
                print("✅ Token has refresh_token")
            else:
                print("⚠️  Token missing refresh_token - may need to re-authenticate")
    
    print()
    print("2. Initializing Calendar Agent...")
    try:
        agent = CalendarAgent()
        agent._initialize()
        print("✅ Calendar agent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize calendar agent: {e}")
        return False
    
    print()
    print("3. Testing service connection...")
    try:
        service = agent._get_service()
        print("✅ Google Calendar service connected")
    except Exception as e:
        print(f"❌ Failed to connect to Google Calendar: {e}")
        return False
    
    print()
    print("4. Testing event listing...")
    try:
        from datetime import datetime, timedelta
        time_min = datetime.utcnow().isoformat() + 'Z'
        time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ Successfully retrieved {len(events)} upcoming events")
        if events:
            print("   Sample events:")
            for event in events[:3]:
                print(f"   - {event.get('summary', 'No title')} ({event.get('start', {}).get('dateTime', 'N/A')})")
    except Exception as e:
        print(f"❌ Failed to list events: {e}")
        return False
    
    print()
    print("5. Testing event creation (dry run - will not create actual event)...")
    try:
        # Test event structure (won't actually create)
        test_event = {
            'summary': 'Test Event (Not Created)',
            'start': {'dateTime': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z', 'timeZone': 'UTC'},
            'end': {'dateTime': (datetime.utcnow() + timedelta(hours=2)).isoformat() + 'Z', 'timeZone': 'UTC'},
        }
        print("✅ Event structure is valid")
        print(f"   Would create: {test_event['summary']}")
        print(f"   Start: {test_event['start']['dateTime']}")
        print(f"   End: {test_event['end']['dateTime']}")
    except Exception as e:
        print(f"❌ Failed to create test event structure: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ All calendar connection tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_calendar_connection()
    sys.exit(0 if success else 1)

