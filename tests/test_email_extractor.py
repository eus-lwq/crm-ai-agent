"""Test email extractor agent."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.email_extractor import EmailExtractorAgent


async def test_email_extraction():
    """Test extracting structured data from email."""
    print("=" * 70)
    print("EMAIL EXTRACTOR AGENT TEST")
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
    try:
        extractor = EmailExtractorAgent()
        print("✓ Extractor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        return False
    
    # Extract data
    print("\n" + "=" * 70)
    print("STEP 1: Extract structured data from email")
    print("=" * 70)
    print()
    
    try:
        print("Extracting CRM data using Vertex AI (Gemini)...")
        extracted_data = await extractor.extract_from_email(email_text, email_metadata)
        
        print("\n✓ Extraction successful!")
        print("\nExtracted data:")
        print("-" * 70)
        print(f"Contact Name: {extracted_data.contact_name}")
        print(f"Company: {extracted_data.company}")
        print(f"Next Step: {extracted_data.next_step}")
        print(f"Deal Value: {extracted_data.deal_value}")
        print(f"Follow-up Date: {extracted_data.follow_up_date}")
        print(f"Notes: {extracted_data.notes}")
        print("-" * 70)
        print()
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Extract and store in BigQuery
    print("=" * 70)
    print("STEP 2: Store extracted data in BigQuery")
    print("=" * 70)
    print()
    
    try:
        print("Extracting and storing in BigQuery...")
        result = await extractor.extract_and_store(email_text, email_metadata)
        
        if result["status"] == "success":
            print("\n" + "=" * 70)
            print("✅ SUCCESS!")
            print("=" * 70)
            print(f"\n{result['message']}")
            print(f"Table: {result['table_id']}")
            print("\nNormalized data inserted:")
            print("-" * 70)
            for key, value in result["normalized_data"].items():
                print(f"{key}: {value}")
            print("-" * 70)
            print()
            return True
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_email_extraction())
    print("=" * 70)
    if success:
        print("✅ TEST COMPLETED")
    else:
        print("⚠️  TEST INCOMPLETE")
    print("=" * 70)
    print()

