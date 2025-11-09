"""Test email monitor service."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.email_monitor import EmailMonitor


async def test_email_monitor():
    """Test email monitor processing."""
    print("=" * 70)
    print("EMAIL MONITOR TEST")
    print("=" * 70)
    print()
    
    # Check prerequisites
    credentials_path = "credentials.json"
    if not Path(credentials_path).exists():
        print("❌ credentials.json not found")
        print("\nTo set up:")
        print("  1. Go to Google Cloud Console > APIs & Services > Credentials")
        print("  2. Click on your OAuth 2.0 Client ID")
        print("  3. Click 'Download JSON'")
        print("  4. Save it as 'credentials.json' in the project root")
        return False
    
    print("✓ credentials.json found")
    
    # Initialize monitor
    print("\nInitializing Email Monitor...")
    try:
        monitor = EmailMonitor(credentials_path=credentials_path)
        print("✓ Monitor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize monitor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Process unread emails
    print("\n" + "=" * 70)
    print("Processing unread emails...")
    print("=" * 70)
    print()
    
    try:
        result = await monitor.process_unread_emails(max_results=3)
        
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Status: {result['status']}")
        print(f"Processed: {result['processed']}")
        print(f"Stored in BigQuery: {result['stored']}")
        print(f"Skipped (not business-related): {result['skipped']}")
        
        if result.get('errors'):
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['status'] == "success":
            print("\n✅ Test completed successfully!")
            return True
        else:
            print(f"\n⚠️  Test completed with errors: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_email_monitor())
    print("=" * 70)
    if success:
        print("✅ TEST COMPLETED")
    else:
        print("⚠️  TEST INCOMPLETE")
    print("=" * 70)
    print()

