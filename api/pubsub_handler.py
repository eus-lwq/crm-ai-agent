"""Pub/Sub message handler for Cloud Run/Functions."""
import json
import base64
from datetime import datetime
from google.cloud import pubsub_v1

from models.schemas import InteractionEvent
from services.preprocessing import PreprocessingService
from services.extraction import ExtractionService
from services.bigquery_storage import BigQueryStorage
from config import settings


# Initialize services
preprocessing_service = PreprocessingService()
extraction_service = ExtractionService()
storage_service = BigQueryStorage()


def process_pubsub_message(event, context):
    """
    Cloud Function entry point for processing Pub/Sub messages.
    
    Args:
        event: Pub/Sub event
        context: Cloud Function context
    """
    try:
        # Decode message
        if "data" in event:
            message_data = base64.b64decode(event["data"]).decode("utf-8")
        else:
            message_data = event.get("message", {}).get("data", "")
            if message_data:
                message_data = base64.b64decode(message_data).decode("utf-8")
        
        # Parse event
        event_dict = json.loads(message_data)
        interaction_event = InteractionEvent(**event_dict)
        
        # Process asynchronously (in production, use async/await)
        import asyncio
        result = asyncio.run(_process_event(interaction_event))
        
        return {"status": "success", "interaction_id": result}
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Publish to DLQ
        _publish_to_dlq(event, str(e))
        raise


async def _process_event(event: InteractionEvent):
    """Process a single interaction event."""
    # Preprocess
    processed_event = await preprocessing_service.process_event(event)
    
    # Extract
    extracted_data, confidence, _ = await extraction_service.extract(processed_event)
    
    # Save
    interaction_id = await storage_service.save_interaction(
        processed_event=processed_event,
        extracted_data=extracted_data,
        confidence=confidence,
    )
    
    return interaction_id


def _publish_to_dlq(event, error_message: str):
    """Publish failed message to dead-letter queue."""
    publisher = pubsub_v1.PublisherClient()
    dlq_topic_path = publisher.topic_path(
        settings.gcp_project_id, settings.pubsub_dlq_topic
    )
    
    dlq_message = {
        "original_event": event,
        "error": error_message,
        "timestamp": datetime.now().isoformat(),
    }
    
    publisher.publish(
        dlq_topic_path,
        json.dumps(dlq_message).encode("utf-8"),
    )

