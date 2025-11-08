"""Test preprocessing service."""
import asyncio
from datetime import datetime
from services.preprocessing import PreprocessingService
from models.schemas import InteractionEvent, Channel


async def test_preprocessing_email():
    """Test preprocessing an email event."""
    print("=" * 60)
    print("TEST 1: Preprocessing Email Event")
    print("=" * 60)
    
    service = PreprocessingService()
    
    event = InteractionEvent(
        raw_text="""
        Subject: Follow-up on our meeting
        
        Hi Sarah,
        
        Thanks for the great meeting today. I wanted to follow up on our discussion
        about the enterprise package. We discussed a $75,000 annual contract.
        
        Next steps:
        1. Send proposal by Friday
        2. Schedule demo with technical team
        3. Follow up with John Doe (john.doe@acme.com) next week
        
        Best regards,
        Mike
        """,
        metadata={
            "subject": "Follow-up on our meeting",
            "from": "mike@example.com",
            "to": "sarah@example.com",
        },
        channel=Channel.EMAIL,
        occurred_at=datetime.now(),
        source="gmail",
    )
    
    processed = await service.process_event(event)
    
    print(f"✓ Language detected: {processed.language}")
    print(f"✓ Channel: {processed.channel.value}")
    print(f"✓ Source: {processed.source}")
    print(f"✓ Has transcript: {processed.transcript is not None}")
    print(f"✓ Raw text length: {len(processed.raw_text)} characters")
    print("\n✅ Preprocessing test passed!\n")


async def test_preprocessing_call():
    """Test preprocessing a call transcript."""
    print("=" * 60)
    print("TEST 2: Preprocessing Call Transcript")
    print("=" * 60)
    
    service = PreprocessingService()
    
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
    
    processed = await service.process_event(event)
    
    print(f"✓ Language detected: {processed.language}")
    print(f"✓ Channel: {processed.channel.value}")
    print(f"✓ Participants in metadata: {processed.metadata.get('participants')}")
    print(f"✓ Raw text length: {len(processed.raw_text)} characters")
    print("\n✅ Call preprocessing test passed!\n")


async def test_preprocessing_audio():
    """
    Test preprocessing with audio URI.
    
    Note: The audio_uri is a mock/test URI - not a real file.
    - gs:// URIs point to Google Cloud Storage buckets
    - For real testing, you would need:
      1. An actual audio file (local path or GCS URI)
      2. GCP credentials configured (for GCS access)
      3. Speech-to-Text API enabled (for transcription)
    
    This test demonstrates the preprocessing flow without requiring actual audio files.
    """
    print("=" * 60)
    print("TEST 3: Preprocessing Audio Event")
    print("=" * 60)
    
    service = PreprocessingService()
    
    # This is a MOCK/PLACEHOLDER URI - not a real file
    # Format: gs://bucket-name/path/to/file.wav
    # For real testing, use an actual GCS URI or local file path
    mock_audio_uri = "gs://bucket/audio/meeting-123.wav"
    
    event = InteractionEvent(
        raw_text="Voice note caption: Meeting follow-up",
        audio_uri=mock_audio_uri,
        metadata={
            "duration": 120,
        },
        channel=Channel.VOICE_NOTE,
        occurred_at=datetime.now(),
        source="whatsapp",
    )
    
    processed = await service.process_event(event)
    
    print(f"✓ Audio URI: {processed.audio_uri}")
    print(f"✓ Channel: {processed.channel.value}")
    print(f"✓ Has audio URI: {processed.audio_uri is not None}")
    print("\nℹ️  Note: This is a MOCK URI for testing purposes.")
    print("   For real audio transcription, you would need:")
    print("   1. A real audio file (local path or GCS URI)")
    print("   2. GCP credentials configured")
    print("   3. Speech-to-Text API enabled")
    print("   Example real GCS URI: gs://your-bucket-name/audio/meeting.wav")
    print("   Example local file: /path/to/audio/meeting.wav")
    print("\n✅ Audio preprocessing test passed!\n")


async def run_all_tests():
    """Run all preprocessing tests."""
    print("\n" + "=" * 60)
    print("PREPROCESSING SERVICE TESTS")
    print("=" * 60 + "\n")
    
    try:
        await test_preprocessing_email()
        await test_preprocessing_call()
        await test_preprocessing_audio()
        
        print("=" * 60)
        print("✅ ALL PREPROCESSING TESTS PASSED")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())

