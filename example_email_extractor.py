"""Example usage of the Email Extractor Agent."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.email_extractor import EmailExtractorAgent


async def example_extract_email():
    """Example: Extract structured data from an email and store in BigQuery."""
    print("=" * 70)
    print("EMAIL EXTRACTOR AGENT - EXAMPLE")
    print("=" * 70)
    print()
    
    # Sample email from user
    email_text = """Hi team, thanks for the overview today (phone call). Next step from our side: please send the proposal with API integration details and supported data formats. We're looking at something around $75,000 for year one depending on SLAs. Follow-up date I suggested internally is 2025-11-12 to agree on the integration timeline. Quick notes: DataFlow Systems cares a lot about webhook latency and retry semantics — they were enthusiastic about the REST API demo. — Michael"""
    
    email_metadata = {
        "subject": "Proposal next steps / API questions",
        "from": "Sayam Khatri <1999sanyam@gmail.com>",
        "to": "me",
        "date": "5:54 PM (1 hour ago)"
    }
    
    print("Email to extract from:")
    print("-" * 70)
    print(f"Subject: {email_metadata['subject']}")
    print(f"From: {email_metadata['from']}")
    print(f"\nBody:\n{email_text}\n")
    print("-" * 70)
    print()
    
    # Initialize extractor
    print("Initializing Email Extractor Agent...")
    extractor = EmailExtractorAgent()
    print("✓ Extractor initialized\n")
    
    # Extract and store
    print("Extracting structured data and storing in BigQuery...")
    print()
    
    result = await extractor.extract_and_store(email_text, email_metadata)
    
    if result["status"] == "success":
        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"\n{result['message']}")
        print(f"Table: {result['table_id']}")
        print("\nExtracted Data:")
        print("-" * 70)
        for key, value in result["extracted_data"].items():
            print(f"  {key}: {value}")
        print("\nNormalized Data (inserted into BigQuery):")
        print("-" * 70)
        for key, value in result["normalized_data"].items():
            print(f"  {key}: {value}")
        print("-" * 70)
    else:
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"\nError: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(example_extract_email())

