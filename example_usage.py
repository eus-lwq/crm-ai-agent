"""Example usage of the CRM parsing services."""
import asyncio
from datetime import datetime
from models.schemas import InteractionEvent, Channel
from services.preprocessing import PreprocessingService
from services.extraction import ExtractionService
from services.bigquery_storage import BigQueryStorage


async def example_parse_email():
    """Example: Parse an email interaction."""
    print("Example: Parsing email interaction...")
    
    # Create sample email event
    event = InteractionEvent(
        raw_text="""
        Hi Sarah,
        
        Great meeting today! I wanted to follow up on our discussion about the $75,000 
        enterprise package for Acme Corporation. 
        
        Next steps:
        1. Send proposal by Friday
        2. Schedule demo with the technical team
        3. Follow up with John Doe (john.doe@acme.com) next week
        
        Looking forward to working together!
        
        Best,
        Mike
        """,
        metadata={
            "subject": "Follow-up: Enterprise Package Discussion",
            "from": "mike@example.com",
            "to": "sarah@example.com",
        },
        channel=Channel.EMAIL,
        occurred_at=datetime.now(),
        source="gmail",
    )
    
    # Initialize services
    preprocessing = PreprocessingService()
    extraction = ExtractionService()
    storage = BigQueryStorage()
    
    # Process
    print("1. Preprocessing...")
    processed = await preprocessing.process_event(event)
    print(f"   Language detected: {processed.language}")
    
    print("2. Extracting structured data...")
    extracted_data, confidence, processing_time = await extraction.extract(processed)
    print(f"   Confidence: {confidence:.2f}")
    print(f"   Processing time: {processing_time}ms")
    
    print("3. Extracted data:")
    print(f"   Summary: {extracted_data.summary}")
    print(f"   Contacts: {[c.full_name for c in extracted_data.contacts]}")
    print(f"   Company: {extracted_data.company}")
    print(f"   Deal value: ${extracted_data.deal_value:,.0f}" if extracted_data.deal_value else "   Deal value: None")
    print(f"   Action items: {extracted_data.action_items}")
    print(f"   Sentiment: {extracted_data.sentiment}")
    
    # Save to BigQuery (uncomment to actually save)
    # print("4. Saving to BigQuery...")
    # interaction_id = await storage.save_interaction(processed, extracted_data, confidence)
    # print(f"   Saved with interaction_id: {interaction_id}")


async def example_parse_call():
    """Example: Parse a call transcript."""
    print("\nExample: Parsing call transcript...")
    
    event = InteractionEvent(
        raw_text="""
        Call transcript:
        
        Agent: Hi, this is Sarah from Sales. How can I help you today?
        Customer: Hi, I'm John from TechCorp. We're interested in your enterprise solution.
        Agent: Great! What's your company size?
        Customer: We have about 200 employees. We're looking at a $100k annual contract.
        Agent: Perfect! I'll send you a proposal. Can we schedule a demo next Tuesday?
        Customer: Yes, that works. My email is john@techcorp.com.
        Agent: Excellent. I'll send the calendar invite.
        """,
        metadata={
            "call_duration": 300,
            "participants": ["Sarah", "John"],
        },
        channel=Channel.CALL,
        occurred_at=datetime.now(),
        source="zoom",
    )
    
    preprocessing = PreprocessingService()
    extraction = ExtractionService()
    
    processed = await preprocessing.process_event(event)
    extracted_data, confidence, _ = await extraction.extract(processed)
    
    print(f"   Summary: {extracted_data.summary}")
    print(f"   Company: {extracted_data.company}")
    print(f"   Deal value: ${extracted_data.deal_value:,.0f}" if extracted_data.deal_value else "   Deal value: None")
    print(f"   Next step: {extracted_data.next_step}")


if __name__ == "__main__":
    print("CRM AI Agent - Example Usage\n")
    print("=" * 50)
    
    # Run examples
    asyncio.run(example_parse_email())
    asyncio.run(example_parse_call())
    
    print("\n" + "=" * 50)
    print("Examples completed!")

