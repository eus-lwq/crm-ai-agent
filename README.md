# Zero-Click CRM

**Zero-Click CRM** reimagines relationship management — no typing, no logging, no manual updates.
The system listens to **real communication data** (voice notes, calls, and emails) and automatically extracts, updates, and analyzes CRM records.

Whenever a sales call recording or follow-up email lands in the system, it:

1. **Transcribes** the content (voice → text via Groq Whisper).
2. **Extracts structured CRM fields** using **Gemini 2.0 Flash-Lite** (contact, company, next step, deal value, etc.).
3. **Updates BigQuery** with fresh records, unifying voice and email data.
4. **Engages users** through a **multi-agent chatbot** (Gemini 2.5 Flash) — capable of:

   * Querying BigQuery via natural language
   * Drafting and replying to customer emails
   * Scheduling meetings in Google Calendar
   * Generating insights like:

     > “Show deals with no follow-up in 7 days”
     > “Draft a reply to Acme confirming next week’s demo”

The result: A **self-maintaining, intelligent CRM** that operates across channels — **voice, email, and chat**.

## Architecture
<img width="1148" height="562" alt="Screenshot 2025-11-08 at 11 57 46 PM" src="https://github.com/user-attachments/assets/cb7c19c6-e1c2-46e1-87d4-0bd309df97fb" />


## Features

- **🤖 Intelligent Chat Agent**: Query BigQuery tables, check/edit calendar events, send emails using natural language
- **📧 Email Monitoring**: Automatically monitors Gmail inbox every 1 second, extracts structured CRM data, and stores in BigQuery
- **📅 Calendar Integration**: Create, list, update, and manage Google Calendar events via agent or API
- **📊 Data Extraction**: Uses Vertex AI (Gemini 1.5) to extract structured data from unstructured emails
- **🗄️ BigQuery Storage**: Automatic storage of contacts, companies, deals, and interactions
- **🎤 Voice Processing**: Transcribe audio files and extract CRM data from voice interactions
- **🔄 Real-time Sync**: Frontend syncs with BigQuery every 1 second for real-time updates

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **AI/ML**: 
  - LangChain 0.1.0+ (AgentExecutor, ReAct agents)
  - LangChain Google Vertex AI 0.0.6 (Gemini 1.5 Pro)
  - LangChain Google Community 1.0.4+ (Gmail Toolkit)
- **Database**: Google Cloud BigQuery
- **APIs**: 
  - Gmail API (via `google-api-python-client`)
  - Google Calendar API
  - Google Cloud Speech-to-Text
- **Package Management**: `uv` (Python package manager)
- **Audio Processing**: OpenAI Whisper, Groq API
- **Data Validation**: Pydantic 2.5.0

## Project Structure

```
crm-ai-agent/
├── api/
│   ├── __init__.py
│   └── main.py              # FastAPI application with all endpoints
├── src/
│   └── agents/
│       ├── __init__.py
│       ├── chatagent.py     # Main CRM chat agent (BigQuery, Calendar, Email)
│       ├── calendar_agent.py # Google Calendar agent
│       ├── gmail_agent.py    # Gmail agent (send, search, get emails)
│       ├── agent_tools.py    # BigQuery tools for chat agent
│       └── prompts.py        # System prompts and guidelines
├── services/
│   ├── __init__.py
│   ├── email_extractor.py   # Extract structured CRM data from emails
│   ├── email_monitor.py     # Monitor Gmail, extract, store in BigQuery
│   └── voice_service.py     # Audio transcription and voice data extraction
├── models/
│   ├── __init__.py
│   └── email_schemas.py     # Pydantic schemas for email data
├── tests/
│   └── test_api_endpoints.py # API endpoint tests
├── scripts/
│   ├── start_server.sh      # Start server script
│   ├── kill_port.sh         # Kill process on port
│   ├── test_bigquery_connection.py
│   ├── test_calendar_connection.py
│   └── ...                  # Various utility scripts
├── docs/
│   ├── BIGQUERY_SETUP.md
│   ├── GCP_CREDENTIALS_REFRESH.md
│   └── ...                  # Documentation files
├── config.py                # Application settings (Pydantic)
├── main.py                  # Server entry point
├── pyproject.toml           # Project dependencies (uv)
├── env.example               # Example environment variables
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager ([Installation](https://github.com/astral-sh/uv))
- Google Cloud Project with BigQuery enabled
- Gmail API credentials (for email monitoring)
- Google Calendar API credentials (for calendar features)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd crm-ai-agent
```

2. **Install `uv` (if not already installed):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Install dependencies:**
```bash
uv sync
```

This creates a virtual environment (`.venv`) and installs all dependencies automatically.

4. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your credentials
```

**Required environment variables:**
```env
# GCP Configuration
GCP_PROJECT_ID=your-project-id
BIGQUERY_DATASET=CRM_DATA

# GCP Service Account (for BigQuery, Vertex AI)
GCP_SERVICE_ACCOUNT_PATH=./gcp-service-account.json

# Gmail API (OAuth 2.0)
# Place credentials.json in project root
# token.json will be created on first run

# Google Calendar API
# Place credentials.json in project root
# token-calendar.json will be created on first run
```

5. **Set up GCP authentication:**

**Option A: Application Default Credentials (Recommended for local development)**
```bash
gcloud auth application-default login
```

**Option B: Service Account (Recommended for production)**
- Create a service account in Google Cloud Console
- Download the JSON key file
- Set `GCP_SERVICE_ACCOUNT_PATH` in `.env`

6. **Set up Gmail API:**
- Download `credentials.json` from Google Cloud Console (OAuth 2.0 Client ID)
- Place it in the project root
- On first run, browser will open for authorization
- `token.json` will be created automatically

7. **Set up Google Calendar API:**
- Use the same `credentials.json` or create separate OAuth credentials
- On first run, browser will open for authorization
- `token-calendar.json` will be created automatically

8. **Create BigQuery dataset (if not exists):**
```bash
bq mk --dataset --location=us-central1 your-project-id:CRM_DATA
```

The table `deals` will be created automatically on first email insertion.

### Running the Server

**Using `uv run` (recommended):**
```bash
uv run python main.py
```

**Or using uvicorn directly:**
```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port 8001
```

**Or if virtual environment is activated:**
```bash
source .venv/bin/activate  # macOS/Linux
python main.py
```

The server will start on `http://localhost:8001` (or port specified in `API_PORT` env var).

**Using helper script:**
```bash
./scripts/start_server.sh
```

This script kills any existing processes on port 8001 and starts the server.

## 📡 API Endpoints

### Health Check
```http
GET /health
```
Returns server health status.

### Chat Agent
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Show me all deals over $50,000",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ]
}
```

**Response:**
```json
{
  "response": "Here are the deals over $50,000...",
  "history": [...],
  "thinking_steps": [
    {
      "thought": "I need to query BigQuery for deals...",
      "action": "query_bigquery",
      "action_input": "SELECT * FROM ...",
      "observation": "Found 5 deals..."
    }
  ]
}
```

The chat agent can:
- Query BigQuery tables
- Check and list calendar events
- Create calendar events
- Send emails
- Answer questions about CRM data

### Email Endpoints

**Get Recent Emails:**
```http
GET /api/emails?limit=20
```

**Response:**
```json
[
  {
    "id": "message_id",
    "subject": "Meeting follow-up",
    "from_email": "john@example.com",
    "to_email": "you@example.com",
    "date": "2025-11-10T10:00:00Z",
    "body": "Email body...",
    "extracted_data": {
      "contact_name": "John Doe",
      "company": "Acme Corp",
      "deal_value": 50000.0,
      "follow_up_date": "2025-11-15"
    }
  }
]
```

### Calendar Endpoints

**List Events:**
```http
GET /api/calendar/events?max_results=50
```

**Create Event:**
```http
POST /api/calendar/events
Content-Type: application/json

{
  "summary": "Meeting with John",
  "start_time": "2025-11-15T14:00:00Z",
  "end_time": "2025-11-15T15:00:00Z",
  "description": "Discuss project",
  "attendees": ["john@example.com"]
}
```

**Update Event:**
```http
PUT /api/calendar/events/{event_id}
Content-Type: application/json

{
  "summary": "Updated meeting title",
  "start_time": "2025-11-15T15:00:00Z"
}
```

### BigQuery Interaction Endpoints

**Get Interactions:**
```http
GET /api/interactions?limit=50
```

**Get Interaction Frequency (for charts):**
```http
GET /api/interactions/frequency?days=90
```

**Get Interaction Methods (for Communication Channels):**
```http
GET /api/interactions/methods
```

## 🔧 Services

### Email Monitor Service

The `EmailMonitor` service automatically:
- Checks Gmail inbox every 1 second
- Processes unread emails
- Extracts structured CRM data using `EmailExtractorAgent`
- Stores data in BigQuery (`CRM_DATA.deals` table)
- Marks emails as read

**Schema stored in BigQuery:**
- `contact_name` (STRING)
- `company` (STRING)
- `next_step` (STRING)
- `deal_value` (FLOAT)
- `follow_up_date` (DATE)
- `notes` (STRING)
- `interaction_medium` (STRING) - Always "email"
- `created_at` (TIMESTAMP)

### Email Extractor Agent

Uses Vertex AI (Gemini 1.5 Pro) to extract structured CRM data from email text:

```python
from services.email_extractor import EmailExtractorAgent

extractor = EmailExtractorAgent()
result = await extractor.extract_and_store(
    email_text="Had a call with John from Acme Corp...",
    email_metadata={"from": "john@example.com", "subject": "Meeting"}
)
```

### Voice Service

Transcribes audio files and extracts CRM data:

```python
from services.voice_service import VoiceService

voice_service = VoiceService()
result = voice_service.process_audio_file("audio.wav")
# Returns: transcript, extracted_data, status
```

## 🤖 Agents

### Chat Agent

The main CRM chat agent (`src/agents/chatagent.py`) uses:
- **LangChain AgentExecutor** with ReAct pattern
- **Vertex AI (Gemini 1.5 Pro)** as the LLM
- **BigQuery tools** for querying data
- **Calendar agent** for managing events
- **Gmail agent** for sending emails

**Capabilities:**
- Natural language queries to BigQuery
- Calendar event management
- Email sending
- Data analysis and insights

### Calendar Agent

Manages Google Calendar events:
- Create events
- List events
- Update events
- Move/reschedule events

### Gmail Agent

Uses LangChain's GmailToolkit:
- Send emails
- Search emails
- Get email details

## 🧪 Testing

Run API endpoint tests:
```bash
uv run pytest tests/test_api_endpoints.py -v
```

Test BigQuery connection:
```bash
uv run python scripts/test_bigquery_connection.py
```

Test calendar connection:
```bash
uv run python scripts/test_calendar_connection.py
```

## 🔐 Authentication Setup

### Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 credentials (Desktop app)
3. Download `credentials.json`
4. Place in project root
5. On first run, browser opens for authorization
6. `token.json` is created automatically

See `scripts/get_gmail_refresh_token.py` for manual token generation.

### Google Calendar API

1. Enable Google Calendar API in Google Cloud Console
2. Use same `credentials.json` or create separate OAuth credentials
3. On first run, browser opens for authorization
4. `token-calendar.json` is created automatically

### BigQuery & Vertex AI

**Option A: Application Default Credentials**
```bash
gcloud auth application-default login
```

**Option B: Service Account**
1. Create service account in Google Cloud Console
2. Grant roles: BigQuery Admin, Vertex AI User
3. Download JSON key
4. Set `GCP_SERVICE_ACCOUNT_PATH` in `.env`

## 📊 BigQuery Schema

The `CRM_DATA.deals` table schema:

```sql
CREATE TABLE `project.CRM_DATA.deals` (
  contact_name STRING,
  company STRING,
  next_step STRING,
  deal_value FLOAT,
  follow_up_date DATE,
  notes STRING,
  interaction_medium STRING,
  created_at TIMESTAMP
)
```

## 🐛 Troubleshooting

### Port Conflicts

If port 8001 is already in use:
```bash
./scripts/kill_port.sh 8001
# Or
./scripts/kill_all_servers.sh
```

### GCP Authentication Errors

Refresh credentials:
```bash
./scripts/refresh_gcp_credentials.sh
# Or
gcloud auth application-default login
```

### Gmail Token Issues

Delete `token.json` and re-authenticate:
```bash
rm token.json
# Restart server - browser will open for auth
```

### Calendar Token Issues

Delete `token-calendar.json` and re-authenticate:
```bash
rm token-calendar.json
# Restart server - browser will open for auth
```

See `docs/TROUBLESHOOTING.md` for more details.

## 📚 Documentation

- `docs/BIGQUERY_SETUP.md` - BigQuery setup and configuration
- `docs/GCP_CREDENTIALS_REFRESH.md` - GCP authentication guide
- `docs/INTEGRATION.md` - Frontend integration guide
- `docs/TROUBLESHOOTING.md` - Common issues and solutions

## 🔄 Development

### Project Dependencies

Managed via `uv` and `pyproject.toml`:
```bash
# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Sync dependencies
uv sync
```

### Code Formatting

```bash
uv run black .
uv run ruff check .
```

### Running Tests

```bash
uv run pytest tests/ -v
```

## 🚢 Deployment

### Environment Variables

Set in production environment:
- `GCP_PROJECT_ID`
- `GCP_SERVICE_ACCOUNT_PATH` (or use ADC)
- `API_PORT` (default: 8001)
- `API_HOST` (default: 0.0.0.0)

### Cloud Run Deployment

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/crm-ai-agent

# Deploy
gcloud run deploy crm-ai-agent \
  --image gcr.io/PROJECT_ID/crm-ai-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project-id
```

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check `docs/TROUBLESHOOTING.md`
- Review `docs/` directory for setup guides
- Check existing GitHub issues
