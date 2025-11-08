"""Ingestion layer interfaces for different sources."""
from typing import Optional
from datetime import datetime
from google.cloud import pubsub_v1

from models.schemas import InteractionEvent, Channel
from config import settings


class IngestionService:
    """Service for ingesting events from various sources."""
    
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(
            settings.gcp_project_id, settings.pubsub_topic
        )
    
    async def ingest_gmail(self, email_data: dict) -> str:
        """Ingest email from Gmail."""
        event = InteractionEvent(
            raw_text=email_data.get("body", ""),
            metadata={
                "subject": email_data.get("subject"),
                "from": email_data.get("from"),
                "to": email_data.get("to"),
                "thread_id": email_data.get("thread_id"),
            },
            channel=Channel.EMAIL,
            occurred_at=datetime.fromisoformat(email_data.get("date", datetime.now().isoformat())),
            source="gmail",
        )
        return await self._publish_event(event)
    
    async def ingest_zoom_transcript(self, transcript_data: dict) -> str:
        """Ingest Zoom meeting transcript."""
        event = InteractionEvent(
            raw_text=transcript_data.get("transcript", ""),
            audio_uri=transcript_data.get("audio_uri"),
            metadata={
                "meeting_id": transcript_data.get("meeting_id"),
                "participants": transcript_data.get("participants", []),
                "duration": transcript_data.get("duration"),
                "diarization": transcript_data.get("diarization"),
            },
            channel=Channel.MEETING,
            occurred_at=datetime.fromisoformat(
                transcript_data.get("start_time", datetime.now().isoformat())
            ),
            source="zoom",
        )
        return await self._publish_event(event)
    
    async def ingest_whatsapp_audio(self, audio_data: dict) -> str:
        """Ingest WhatsApp audio message."""
        event = InteractionEvent(
            raw_text=audio_data.get("caption", ""),
            audio_uri=audio_data.get("audio_uri"),
            metadata={
                "message_id": audio_data.get("message_id"),
                "from_number": audio_data.get("from_number"),
                "to_number": audio_data.get("to_number"),
            },
            channel=Channel.VOICE_NOTE,
            occurred_at=datetime.fromisoformat(
                audio_data.get("timestamp", datetime.now().isoformat())
            ),
            source="whatsapp",
        )
        return await self._publish_event(event)
    
    async def ingest_calendar_event(self, calendar_data: dict) -> str:
        """Ingest calendar event."""
        event = InteractionEvent(
            raw_text=calendar_data.get("description", ""),
            metadata={
                "event_id": calendar_data.get("event_id"),
                "title": calendar_data.get("title"),
                "start_time": calendar_data.get("start_time"),
                "end_time": calendar_data.get("end_time"),
                "attendees": calendar_data.get("attendees", []),
            },
            channel=Channel.MEETING,
            occurred_at=datetime.fromisoformat(
                calendar_data.get("start_time", datetime.now().isoformat())
            ),
            source="calendar",
        )
        return await self._publish_event(event)
    
    async def ingest_webhook(self, webhook_data: dict) -> str:
        """Ingest generic webhook event."""
        event = InteractionEvent(
            raw_text=webhook_data.get("text", ""),
            audio_uri=webhook_data.get("audio_uri"),
            metadata=webhook_data.get("metadata", {}),
            channel=Channel.WEBHOOK,
            occurred_at=datetime.fromisoformat(
                webhook_data.get("timestamp", datetime.now().isoformat())
            ),
            source=webhook_data.get("source", "webhook"),
        )
        return await self._publish_event(event)
    
    async def _publish_event(self, event: InteractionEvent) -> str:
        """Publish event to Pub/Sub."""
        message_data = event.model_dump_json()
        future = self.publisher.publish(
            self.topic_path,
            message_data.encode("utf-8"),
        )
        return future.result()  # Returns message_id

