"""Configuration settings for CRM AI Agent."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # GCP Configuration
    gcp_project_id: str = "ai-hackathon-477617"  # Default to user's project
    gcp_region: str = "us-central1"
    bigquery_dataset: str = "CRM_DATA"  # Default to uppercase to match user's example
    
    # Vertex AI Configuration
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-1.5-pro"
    
    # Pub/Sub Configuration
    pubsub_topic: str = "crm-ingestion"
    pubsub_dlq_topic: str = "crm-ingestion-dlq"
    
    # Speech-to-Text Configuration
    use_vertex_stt: bool = True
    stt_model: str = "latest_long"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8001  # Changed to 8001 to avoid port conflicts
    
    # Gmail API Configuration
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_refresh_token: Optional[str] = None
    gmail_user_email: Optional[str] = None
    
    # Google Calendar API Configuration
    google_calendar_credentials_path: Optional[str] = None  # Path to service account JSON or OAuth credentials
    
    # Zoom API Configuration
    zoom_api_key: Optional[str] = None
    zoom_api_secret: Optional[str] = None
    zoom_account_id: Optional[str] = None
    zoom_webhook_secret: Optional[str] = None
    
    # WhatsApp/Twilio Configuration
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None  # WhatsApp number in format: whatsapp:+14155238886
    
    # Webhook Configuration
    webhook_secret: Optional[str] = None  # Secret for validating webhook requests
    
    # GCP Service Account (alternative to application-default credentials)
    gcp_service_account_path: Optional[str] = None  # Path to service account JSON file
    
    # Google API Key (optional - for public APIs like Maps, Places, etc.)
    # Note: Most GCP services (BigQuery, Vertex AI, etc.) use Service Account credentials, not API keys
    google_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

