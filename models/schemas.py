"""Data models and schemas for CRM parsing."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class Sentiment(str, Enum):
    """Sentiment enumeration."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Channel(str, Enum):
    """Interaction channel enumeration."""
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    VOICE_NOTE = "voice_note"
    WEBHOOK = "webhook"


class Contact(BaseModel):
    """Contact information."""
    full_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None


class ExtractedData(BaseModel):
    """Extracted structured data from unstructured text."""
    contacts: List[Contact] = Field(default_factory=list)
    company: Optional[str] = None
    deal_value: Optional[float] = None
    currency: Optional[str] = Field(default="USD")
    next_step: Optional[str] = None
    follow_up_date: Optional[str] = None
    sentiment: Optional[Sentiment] = None
    risk_flags: List[str] = Field(default_factory=list)
    summary: str = Field(..., description="Summary of the interaction")
    action_items: List[str] = Field(default_factory=list)
    
    @field_validator('follow_up_date')
    @classmethod
    def validate_date(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("follow_up_date must be in YYYY-MM-DD format")
        return v


class InteractionEvent(BaseModel):
    """Raw interaction event from ingestion layer."""
    raw_text: str
    audio_uri: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    channel: Channel
    occurred_at: Optional[datetime] = None
    source: str  # gmail, zoom, whatsapp, calendar, webhook


class ProcessedEvent(BaseModel):
    """Processed event after preprocessing."""
    raw_text: str
    audio_uri: Optional[str] = None
    metadata: dict
    channel: Channel
    occurred_at: datetime
    source: str
    language: Optional[str] = None
    diarization_tags: Optional[dict] = None
    transcript: Optional[str] = None  # If audio was transcribed


class ParsingResponse(BaseModel):
    """Response from parsing service."""
    interaction_id: Optional[str] = None
    extracted_data: ExtractedData
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time_ms: int

