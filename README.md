# CRM AI Agent - Parsing Services

A LangGraph-based parsing service for extracting structured CRM data from unstructured interactions (emails, calls, meetings, voice notes).

## Architecture

```
[Gmail / Zoom / WhatsApp audio / Calendar / Webhook sources]
          │
          ▼
   Ingestion Layer (Cloud Run/Functions)
   - email puller (Gmail API / IMAP)
   - audio/transcript webhooks (Zoom, Twilio, WhatsApp via Twilio)
   - calendar events (Google Calendar API)
          │
          ▼
         Pub/Sub  ──────────────▶ Dead-letter topic (retry/failure)
          │
          ▼
   Preprocessing Service (Cloud Run)
   - normalize event {raw_text, audio_uri, metadata}
   - language detect, diarization tags
          │
          ├────────────▶ Speech-to-Text (GCP STT or Whisper on Vertex)*
          │               (*only when audio_uri present)
          ▼
  Extraction Service (Vertex AI: Gemini 1.5 / Gemma)
  - JSON-schema constrained extraction
  - fields: contact, company, deal value, intent, stage, next step, follow-up date, owner, sentiment, risks
          │
          ▼
      BigQuery Storage
```

## Features

- **LangGraph-based Extraction**: Multi-step extraction workflow with validation and enrichment
- **Multi-source Ingestion**: Support for Gmail, Zoom, WhatsApp, Calendar, and webhooks
- **Audio Transcription**: GCP Speech-to-Text or Whisper integration
- **Structured Data Extraction**: JSON-schema constrained extraction using Vertex AI (Gemini 1.5)
- **BigQuery Storage**: Automatic storage of contacts, companies, interactions, and deals
- **FastAPI REST API**: Easy-to-use API for parsing interactions

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crm-ai-agent
```

2. Install `uv` (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies and create virtual environment:
```bash
uv sync
```

This will create a virtual environment and install all dependencies automatically.

4. Activate the environment (if needed):
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

5. Set up environment variables:
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your actual credentials
# Required: GCP_PROJECT_ID
# Optional: Add API keys for Gmail, Zoom, WhatsApp, etc. as needed
```

**Security Note**: The `.env` file is already in `.gitignore` and will not be committed to version control. Never commit API keys or credentials to the repository.

See `env.example` for all available configuration options. At minimum, you need:
- `GCP_PROJECT_ID` - Your Google Cloud Project ID

Optional API credentials (add as needed for each integration):
- **Gmail API**: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`
- **Zoom API**: `ZOOM_API_KEY`, `ZOOM_API_SECRET`, `ZOOM_ACCOUNT_ID`
- **WhatsApp/Twilio**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`
- **Google Calendar**: `GOOGLE_CALENDAR_CREDENTIALS_PATH` (path to credentials JSON)

6. Set up GCP authentication:

**For GCP Services (BigQuery, Vertex AI, Pub/Sub, Speech-to-Text):**

You have two options:

**Option A: Application Default Credentials (Recommended for local development)**
```bash
gcloud auth application-default login
```

**Option B: Service Account (Recommended for production/Cloud Run)**
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set in `.env`:
   ```
   GCP_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
   ```

**Note**: Most GCP services use Service Account credentials or ADC, **not API keys**. API keys are only needed for specific public APIs (Maps, Places, etc.) if you're using them.

7. Create BigQuery dataset (or it will be created automatically):
```bash
bq mk --dataset --location=us-central1 your-project-id:crm_data
```

### Development Dependencies

To install development dependencies:
```bash
uv sync --dev
```

## Usage

### Running the FastAPI Server

Using `uv run` (recommended):
```bash
uv run python main.py
```

Or using uvicorn directly:
```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port 8080
```

Or if you've activated the virtual environment:
```bash
python main.py
# or
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

### API Endpoints

#### POST `/parse`
Main parsing endpoint. Processes an interaction event and returns extracted data.

**Request Body:**
```json
{
  "raw_text": "Had a great call with John Doe from Acme Corp. Discussed a $50k deal. Follow up next week.",
  "audio_uri": null,
  "metadata": {},
  "channel": "email",
  "occurred_at": "2024-01-15T10:00:00Z",
  "source": "gmail"
}
```

**Response:**
```json
{
  "interaction_id": "uuid",
  "extracted_data": {
    "contacts": [
      {
        "full_name": "John Doe",
        "title": null,
        "email": null,
        "company": "Acme Corp"
      }
    ],
    "company": "Acme Corp",
    "deal_value": 50000.0,
    "currency": "USD",
    "next_step": "Follow up next week",
    "follow_up_date": null,
    "sentiment": "positive",
    "risk_flags": [],
    "summary": "Call with John Doe from Acme Corp discussing a $50k deal",
    "action_items": ["Follow up next week"]
  },
  "confidence": 0.85,
  "processing_time_ms": 1234
}
```

#### POST `/preprocess`
Preprocess an event without extraction (for testing).

#### POST `/extract`
Extract data from a processed event (for testing).

#### GET `/health`
Health check endpoint.

### Running Example Scripts

```bash
uv run python example_usage.py
```

### Using the Ingestion Service

```python
from services.ingestion import IngestionService

ingestion = IngestionService()

# Ingest Gmail email
await ingestion.ingest_gmail({
    "subject": "Meeting follow-up",
    "body": "Thanks for the meeting...",
    "from": "john@example.com",
    "to": "you@example.com",
    "date": "2024-01-15T10:00:00Z"
})

# Ingest Zoom transcript
await ingestion.ingest_zoom_transcript({
    "transcript": "Meeting transcript...",
    "meeting_id": "123456",
    "participants": ["John", "Jane"],
    "start_time": "2024-01-15T10:00:00Z"
})
```

### Email Sending

There are two approaches for sending emails:

#### Option 1: Direct Gmail API (EmailSender)

Uses refresh tokens from `.env`:

```python
from services.email_sender import EmailSender

sender = EmailSender()
message_id = await sender.send_email(
    to="recipient@example.com",
    subject="Hello",
    body="Email body"
)
```

See `docs/GMAIL_SETUP.md` for setup instructions.

#### Option 2: Gmail Agent (GmailToolkit)

Uses LangChain's GmailToolkit with agent executor:

```python
from src.agents.gmail_agent import GmailAgent

agent = GmailAgent()  # Uses credentials.json
response = await agent.send_email(
    to="recipient@example.com",
    subject="Hello",
    body="Email body"
)
```

**Setup for Gmail Agent:**
1. Download `credentials.json` from Google Cloud Console (OAuth 2.0 Client ID)
2. Place it in the project root
3. On first run, browser will open for authorization
4. `token.json` will be created automatically

See `docs/GMAIL_AGENT_SETUP.md` for detailed instructions.

## Data Model

### Contacts
- `contact_id` (PK)
- `full_name`, `title`, `email`, `phone`
- `company_id` (FK)
- `tags[]`, `embeddings[]`
- `last_touch_at`

### Companies
- `company_id` (PK)
- `name`, `domain`, `linkedin`
- `size`, `industry`
- `enrichment_json`

### Interactions
- `interaction_id` (PK)
- `contact_id`, `company_id`
- `channel` (email|call|meeting|voice_note)
- `occurred_at`, `raw_text`, `summary`
- `action_items[]`, `next_step`, `follow_up_date`
- `sentiment`, `risk_flags[]`
- `owner`, `confidence`

### Deals
- `deal_id` (PK)
- `company_id`, `contact_id`
- `amount`, `currency`
- `stage`, `next_step`, `close_date`
- `health_score`

## LangGraph Extraction Workflow

The extraction service uses LangGraph to orchestrate a multi-step workflow:

1. **Extract Node**: Uses Vertex AI (Gemini) to extract structured data with JSON schema constraints
2. **Validate Node**: Validates extracted data against Pydantic models
3. **Enrich Node** (conditional): Enriches data if confidence is below threshold

The workflow ensures high-quality extraction with automatic validation and error handling.

## API Credentials Setup

### Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 credentials
3. Add the credentials to your `.env` file:
   ```
   GMAIL_CLIENT_ID=your-client-id
   GMAIL_CLIENT_SECRET=your-client-secret
   GMAIL_REFRESH_TOKEN=your-refresh-token
   GMAIL_USER_EMAIL=your-email@gmail.com
   ```

### Zoom API
1. Go to [Zoom Marketplace](https://marketplace.zoom.us/develop/create)
2. Create a Server-to-Server OAuth app
3. Add credentials to `.env`:
   ```
   ZOOM_API_KEY=your-api-key
   ZOOM_API_SECRET=your-api-secret
   ZOOM_ACCOUNT_ID=your-account-id
   ```

### WhatsApp/Twilio
1. Sign up at [Twilio](https://www.twilio.com/)
2. Get your Account SID and Auth Token from the console
3. Enable WhatsApp Sandbox or get a WhatsApp Business number
4. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=your-account-sid
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```

### Google Calendar
1. Enable Google Calendar API in Google Cloud Console
2. Create service account credentials or OAuth credentials
3. Add path to `.env`:
   ```
   GOOGLE_CALENDAR_CREDENTIALS_PATH=/path/to/credentials.json
   ```

## Deployment

### Cloud Run Deployment

1. Build container:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/crm-parsing-service
```

2. Deploy:
```bash
gcloud run deploy crm-parsing-service \
  --image gcr.io/PROJECT_ID/crm-parsing-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Pub/Sub Handler (Cloud Function)

The `api/pubsub_handler.py` can be deployed as a Cloud Function to process Pub/Sub messages automatically.

## Development

### Project Structure

```
crm-ai-agent/
├── api/
│   ├── main.py              # FastAPI application
│   └── pubsub_handler.py    # Pub/Sub message handler
├── models/
│   ├── schemas.py           # Pydantic models
│   └── bigquery_schema.py   # BigQuery table schemas
├── services/
│   ├── preprocessing.py     # Preprocessing service
│   ├── extraction.py        # LangGraph extraction service
│   ├── bigquery_storage.py  # BigQuery storage service
│   └── ingestion.py         # Ingestion service
├── config.py                # Configuration
├── requirements.txt         # Dependencies
└── README.md
```

## License

MIT
