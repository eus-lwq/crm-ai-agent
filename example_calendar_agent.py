"""Example usage of Google Calendar Agent."""
import asyncio
from services.calendar_agent import CalendarAgent


async def example_schedule_event():
    """Example: Schedule an event using natural language."""
    print("=" * 60)
    print("Calendar Agent Example - Schedule Event")
    print("=" * 60)
    
    # Initialize the agent
    # On first run, this will open a browser for OAuth authorization
    agent = CalendarAgent()
    
    try:
        # Schedule an event using natural language
        # The agent will use get_current_time to understand "tomorrow"
        response = await agent.schedule_event(
            summary="Discussing LangChain Agents",
            start_time_description="tomorrow at 2 PM",
            duration_hours=1.0,
            attendees=["example-friend@gmail.com"],
            description="A meeting to discuss the implementation of LangChain agents.",
            location="Virtual Meeting"
        )
        
        print(f"\n✓ Agent Response:")
        print(f"  {response}")
        print("\n✅ Event scheduled successfully!")
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nSetup required:")
        print("  1. Download credentials.json from Google Cloud Console")
        print("  2. Save it in the project root")
        print("  3. Make sure your email is added as 'Test User'")
        print("  4. Run again - browser will open for authorization")
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def example_list_events():
    """Example: List upcoming events."""
    print("\n" + "=" * 60)
    print("Calendar Agent Example - List Events")
    print("=" * 60)
    
    agent = CalendarAgent()
    
    try:
        response = await agent.list_events(max_results=5)
        print(f"\n✓ Upcoming events:")
        print(f"  {response}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    print()
    asyncio.run(example_schedule_event())
    # Uncomment to also list events:
    # asyncio.run(example_list_events())
    print()

