"""Preprocessing service for normalizing events and handling audio transcription."""
from datetime import datetime
from typing import Optional
from google.cloud import speech
from google.cloud.speech import RecognitionConfig, RecognitionAudio
from langdetect import detect
import whisper

from models.schemas import InteractionEvent, ProcessedEvent, Channel
from config import settings


class PreprocessingService:
    """Service for preprocessing interaction events."""
    
    def __init__(self):
        self.stt_client = None
        self.whisper_model = None
        
        if settings.use_vertex_stt:
            self.stt_client = speech.SpeechClient()
        else:
            # Load Whisper model for local transcription
            self.whisper_model = whisper.load_model("base")
    
    async def process_event(self, event: InteractionEvent) -> ProcessedEvent:
        """
        Process an interaction event:
        - Normalize the event
        - Detect language
        - Transcribe audio if present
        - Add diarization tags if available
        """
        processed = ProcessedEvent(
            raw_text=event.raw_text,
            audio_uri=event.audio_uri,
            metadata=event.metadata,
            channel=event.channel,
            occurred_at=event.occurred_at or datetime.now(),
            source=event.source,
        )
        
        # Detect language from raw_text
        if event.raw_text:
            try:
                processed.language = detect(event.raw_text)
            except:
                processed.language = "en"  # Default to English
        
        # Transcribe audio if audio_uri is present
        if event.audio_uri:
            transcript = await self._transcribe_audio(event.audio_uri)
            if transcript:
                processed.transcript = transcript
                # Combine raw_text with transcript
                if processed.raw_text:
                    processed.raw_text = f"{processed.raw_text}\n\n{transcript}"
                else:
                    processed.raw_text = transcript
        
        # Extract diarization tags from metadata if available
        if "diarization" in event.metadata:
            processed.diarization_tags = event.metadata["diarization"]
        
        return processed
    
    async def _transcribe_audio(self, audio_uri: str) -> Optional[str]:
        """Transcribe audio using GCP Speech-to-Text or Whisper."""
        if settings.use_vertex_stt and self.stt_client:
            return await self._transcribe_with_gcp(audio_uri)
        else:
            return await self._transcribe_with_whisper(audio_uri)
    
    async def _transcribe_with_gcp(self, audio_uri: str) -> Optional[str]:
        """Transcribe audio using Google Cloud Speech-to-Text."""
        try:
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_automatic_punctuation=True,
                model=settings.stt_model,
            )
            
            # Handle both GCS URIs and local files
            if audio_uri.startswith("gs://"):
                audio = RecognitionAudio(uri=audio_uri)
            else:
                with open(audio_uri, "rb") as audio_file:
                    content = audio_file.read()
                audio = RecognitionAudio(content=content)
            
            response = self.stt_client.recognize(config=config, audio=audio)
            
            # Combine all transcripts
            transcripts = []
            for result in response.results:
                transcripts.append(result.alternatives[0].transcript)
            
            return " ".join(transcripts) if transcripts else None
            
        except Exception as e:
            print(f"Error transcribing with GCP: {e}")
            return None
    
    async def _transcribe_with_whisper(self, audio_uri: str) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper."""
        try:
            if not self.whisper_model:
                self.whisper_model = whisper.load_model("base")
            
            result = self.whisper_model.transcribe(audio_uri)
            return result["text"]
        except Exception as e:
            print(f"Error transcribing with Whisper: {e}")
            return None

