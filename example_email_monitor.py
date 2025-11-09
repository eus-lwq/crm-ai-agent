"""Example: Run email monitor to process unread emails."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.email_monitor import EmailMonitor


async def example_process_once():
    """Example: Process unread emails once."""
    print("=" * 70)
    print("EMAIL MONITOR - PROCESS ONCE")
    print("=" * 70)
    print()
    
    monitor = EmailMonitor()
    
    print("Processing unread emails (first 3)...")
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


async def example_run_continuous():
    """Example: Run email monitor continuously (every 30 minutes)."""
    print("=" * 70)
    print("EMAIL MONITOR - CONTINUOUS MODE")
    print("=" * 70)
    print()
    
    monitor = EmailMonitor()
    
    # Run continuously, checking every 30 minutes
    await monitor.run_continuous(interval_minutes=30)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        # Run continuously
        asyncio.run(example_run_continuous())
    else:
        # Process once
        asyncio.run(example_process_once())

