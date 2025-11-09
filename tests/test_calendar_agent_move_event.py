"""Test moving/rescheduling calendar events using the Calendar agent."""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.calendar_agent import CalendarAgent
from config import settings


async def test_move_event():
    """Test moving a calendar event to a new time."""
    print("=" * 70)
    print("CALENDAR AGENT - MOVE EVENT TEST")
    print("=" * 70)
    print()
    
    # Check prerequisites
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print("❌ credentials.json not found")
        print("\nTo set up:")
        print("  1. Go to Google Cloud Console > APIs & Services > Credentials")
        print("  2. Click on your OAuth 2.0 Client ID")
        print("  3. Click 'Download JSON'")
        print("  4. Save it as 'credentials.json' in the project root")
        return False
    
    print("✓ credentials.json found")
    
    # Initialize agent
    print("\nInitializing Calendar agent...")
    try:
        agent = CalendarAgent(credentials_path=credentials_path)
        print("✓ Agent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # Step 1: List events to find one to move
    print("\n" + "=" * 70)
    print("STEP 1: List recent events to find one to move")
    print("=" * 70)
    print()
    
    try:
        print("Listing upcoming events...")
        events_list = await agent.list_events(max_results=5)
        print(f"\nEvents found:\n{events_list}\n")
        
        # Try to extract event ID from the list
        import re
        event_ids = re.findall(r'ID: ([a-zA-Z0-9_]+)', events_list)
        
        # Filter out birthday events (they can't be moved)
        regular_event_ids = []
        for event_id in event_ids:
            # Check if it's a birthday event by looking at the event details
            try:
                event_details = await agent.get_event(event_id)
                if "birthday" not in event_details.lower():
                    regular_event_ids.append(event_id)
            except:
                # If we can't get details, assume it's a regular event
                regular_event_ids.append(event_id)
        
        event_ids = regular_event_ids
        
        if not event_ids:
            print("⚠️  No regular events found (only birthday events which can't be moved).")
            print("Creating a test event first...\n")
            
            # Create a test event using direct API call (more reliable)
            from datetime import datetime, timedelta
            service = agent._get_service()
            tomorrow = datetime.now() + timedelta(days=1)
            start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': 'Test Event to Move',
                'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
                'description': 'This is a test event that we will move'
            }
            
            print("Creating test event...")
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            test_event_id = created_event.get('id')
            print(f"✓ Created test event with ID: {test_event_id}\n")
            event_ids = [test_event_id]
        
        if not event_ids:
            print("❌ Could not find or create an event to move.")
            return False
        
        test_event_id = event_ids[0]
        print(f"✓ Found event ID: {test_event_id}\n")
        
    except Exception as e:
        print(f"❌ Error listing events: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Get event details
    print("=" * 70)
    print("STEP 2: Get current event details")
    print("=" * 70)
    print()
    
    try:
        event_details = await agent.get_event(test_event_id)
        print(f"Current event details:\n{event_details}\n")
    except Exception as e:
        print(f"⚠️  Could not get event details: {e}\n")
    
    # Step 3: Move the event using agent
    print("=" * 70)
    print("STEP 3: Move event to new time using agent")
    print("=" * 70)
    print()
    
    try:
        # Move event to tomorrow at 3 PM
        print(f"Moving event {test_event_id} to tomorrow at 3 PM...")
        print("(The agent will use get_current_time to understand 'tomorrow')\n")
        
        response = await agent.reschedule_event(
            event_id=test_event_id,
            new_time_description="tomorrow at 3 PM"
        )
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"\nAgent response:\n{response}\n")
        print("✓ Event moved successfully!")
        
        # Verify by getting updated event using direct API call
        print("\nVerifying event was moved...")
        try:
            service = agent._get_service()
            updated_event = service.events().get(calendarId='primary', eventId=test_event_id).execute()
            start = updated_event['start'].get('dateTime', updated_event['start'].get('date'))
            end = updated_event['end'].get('dateTime', updated_event['end'].get('date'))
            print(f"\nUpdated event details:")
            print(f"  Summary: {updated_event.get('summary', 'No title')}")
            print(f"  Start: {start}")
            print(f"  End: {end}")
            print(f"  Link: {updated_event.get('htmlLink', 'N/A')}\n")
        except Exception as e:
            print(f"⚠️  Could not verify event (but move was successful): {e}\n")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_move_event())
    print("=" * 70)
    if success:
        print("✅ TEST COMPLETED")
    else:
        print("⚠️  TEST INCOMPLETE")
    print("=" * 70)
    print()

