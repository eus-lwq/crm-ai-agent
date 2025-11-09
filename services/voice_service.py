"""Voice pipeline service for transcribing audio and extracting CRM data."""
import os
import re
from typing import Optional, Dict, Any
from google.cloud import bigquery, storage
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import dateparser
import requests

from config import settings

# Set up GCP credentials if service account path is provided
if settings.gcp_service_account_path and os.path.exists(settings.gcp_service_account_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.gcp_service_account_path


class VoiceCRMData(BaseModel):
    """Structured CRM data extracted from voice transcripts."""
    contact_name: Optional[str] = Field(None, description="Name of the contact person")
    company: Optional[str] = Field(None, description="Company name")
    next_step: Optional[str] = Field(None, description="Next step or action")
    deal_value: Optional[str] = Field(None, description="Potential deal value")
    follow_up_date: Optional[str] = Field(None, description="Follow-up date if mentioned")
    notes: Optional[str] = Field(None, description="Additional context or details")
    interaction_medium: str = Field("phone_call", description="Mode of communication (always 'phone_call')")


def normalize_deal_value(value: Optional[str]) -> Optional[float]:
    """Normalize deal value to float."""
    if not value:
        return None
    value_str = str(value).lower().replace(",", "").strip()
    match = re.search(r"([\d\.]+)\s*k?", value_str)
    if match:
        num = float(match.group(1))
        if "k" in value_str:
            num *= 1000
        return num
    return None


def normalize_follow_up_date(value: Optional[str]) -> Optional[str]:
    """Normalize follow-up date to YYYY-MM-DD format."""
    if not value:
        return None
    parsed = dateparser.parse(value)
    if parsed:
        return parsed.date().isoformat()
    return None


def transcribe_audio_groq(local_path: str) -> str:
    """
    Uses Groq's Whisper API to transcribe audio.
    
    Args:
        local_path: Path to local audio file
        
    Returns:
        Transcript text
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    with open(local_path, "rb") as audio_file:
        files = {"file": (local_path, audio_file, "audio/mpeg")}
        data = {"model": "whisper-large-v3"}
        headers = {"Authorization": f"Bearer {api_key}"}

        print("Sending file to Groq Whisper for transcription...")
        response = requests.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()

        result = response.json()
        transcript = result.get("text", "")
        
        return transcript


def extract_crm_fields_from_voice(transcript: str) -> Dict[str, Any]:
    """
    Uses Gemini 2.0 Flash model on Vertex AI to extract structured CRM data
    from a sales conversation transcript.
    
    Args:
        transcript: Audio transcript text
        
    Returns:
        Dictionary with extracted CRM fields
    """
    client = genai.Client(vertexai=True)
    model = "gemini-2.0-flash-lite-001"

    prompt = f"""
    Extract the following CRM fields from this sales conversation:
    - contact name
    - company
    - next step
    - deal value
    - follow-up date
    - notes

    Conversation:
    {transcript}
    """

    response = client.models.generate_content(
        model=model,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VoiceCRMData.model_json_schema(),
        ),
    )

    crm = VoiceCRMData.model_validate_json(response.text)
    crm.interaction_medium = "phone_call"

    print("Parsed CRM data:", crm.dict())
    return crm.dict()


def insert_voice_data_into_bigquery(data: dict):
    """
    Insert voice-extracted CRM data into BigQuery.
    
    Args:
        data: Dictionary with CRM fields
    """
    client = bigquery.Client(project=settings.gcp_project_id)
    dataset_name = settings.bigquery_dataset.upper() if settings.bigquery_dataset else "CRM_DATA"
    table_id = f"{settings.gcp_project_id}.{dataset_name}.deals"

    # Normalize fields
    row = {
        "contact_name": data.get("contact_name"),
        "company": data.get("company"),
        "next_step": data.get("next_step"),
        "deal_value": normalize_deal_value(data.get("deal_value")),
        "follow_up_date": normalize_follow_up_date(data.get("follow_up_date")),
        "notes": data.get("notes"),
        "interaction_medium": data.get("interaction_medium", "phone_call"),
    }

    # Ensure empty strings are None
    for key, value in row.items():
        if value == "" or (isinstance(value, str) and not value.strip()):
            row[key] = None

    errors = client.insert_rows_json(table_id, [row])
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")
    print("Row inserted successfully into BigQuery.")


class VoiceService:
    """
    Voice pipeline service that:
    1. Transcribes audio files
    2. Extracts structured CRM data
    3. Stores data in BigQuery
    """
    
    def __init__(self):
        """Initialize voice service."""
        pass
    
    def process_audio_file(self, local_path: str) -> Dict[str, Any]:
        """
        Process an audio file: transcribe and extract CRM data.
        
        Args:
            local_path: Path to local audio file
            
        Returns:
            Dictionary with transcript and extracted data
        """
        # Step 1: Transcribe
        transcript = transcribe_audio_groq(local_path)
        print(f"Transcript: {transcript[:200]}...")
        
        # Step 2: Extract CRM data
        structured_data = extract_crm_fields_from_voice(transcript)
        
        # Step 3: Insert into BigQuery
        insert_voice_data_into_bigquery(structured_data)
        
        return {
            "transcript": transcript,
            "extracted_data": structured_data,
            "status": "success"
        }
    
    def process_gcs_audio(self, bucket_name: str, file_name: str) -> Dict[str, Any]:
        """
        Process an audio file from Google Cloud Storage.
        
        Args:
            bucket_name: GCS bucket name
            file_name: File path in bucket
            
        Returns:
            Dictionary with transcript and extracted data
        """
        # Download file locally
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        local_path = f"/tmp/{file_name.split('/')[-1]}"
        blob.download_to_filename(local_path)
        print(f"Downloaded {file_name} to {local_path}")
        
        # Process the file
        return self.process_audio_file(local_path)


def on_gcs_file_upload(event, context):
    """
    Cloud Function entry point for processing GCS file uploads.
    
    Args:
        event: GCS event
        context: Cloud Function context
    """
    bucket_name = event['bucket']
    file_name = event['name']

    if not file_name.endswith(('.mp3', '.wav', '.m4a')):
        print(f"Skipping non-audio file: {file_name}")
        return

    print(f"New audio file uploaded: {file_name}")

    service = VoiceService()
    result = service.process_gcs_audio(bucket_name, file_name)
    
    print(f"Data inserted into BigQuery for file: {file_name}")
    return result

