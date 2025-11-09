# Frontend-Backend Integration Guide

This document describes how the frontend (langgraph-crm-insight) and backend (crm-ai-agent) are connected.

## Architecture

```
Frontend (React + Vite)          Backend (FastAPI)
Port: 8080                      Port: 8000
┌─────────────────┐             ┌─────────────────┐
│  React App      │             │  FastAPI        │
│  - Index.tsx    │────────────▶│  - api/main.py  │
│  - AIAssistant  │   HTTP      │                 │
│  - API Client   │             │  Agents:        │
│                 │             │  - Chat Agent   │
│                 │             │  - Calendar     │
│                 │             │  - Email Monitor│
│                 │             │  - Email Extract│
└─────────────────┘             └─────────────────┘
                                        │
                                        ▼
                                ┌─────────────────┐
                                │  Services       │
                                │  - BigQuery     │
                                │  - Gmail API    │
                                │  - Calendar API │
                                └─────────────────┘
```

## API Endpoints

### 1. Chat Endpoint
- **URL**: `POST /api/chat`
- **Purpose**: Chat with CRM agent to query tables, check calendar, edit calendar, add events
- **Request**:
  ```json
  {
    "message": "What are my upcoming meetings?",
    "conversation_history": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi! How can I help?"}
    ]
  }
  ```
- **Response**:
  ```json
  {
    "response": "You have 3 upcoming meetings...",
    "history": [...]
  }
  ```

### 2. Get Emails
- **URL**: `GET /api/emails?limit=10`
- **Purpose**: Get recent emails from Gmail
- **Response**: Array of email objects with extracted CRM data

### 3. Get Calendar Events
- **URL**: `GET /api/calendar/events?max_results=20`
- **Purpose**: Get upcoming calendar events
- **Response**: Array of calendar event objects

### 4. Create Calendar Event
- **URL**: `POST /api/calendar/events`
- **Purpose**: Create a new calendar event
- **Request**:
  ```json
  {
    "summary": "Meeting with client",
    "start_time": "2025-11-15T14:00:00",
    "end_time": "2025-11-15T15:00:00",
    "description": "Discuss project",
    "location": "Office",
    "attendees": ["client@example.com"]
  }
  ```

### 5. Update Calendar Event
- **URL**: `PUT /api/calendar/events/{event_id}`
- **Purpose**: Update an existing calendar event

### 6. Get Interactions
- **URL**: `GET /api/interactions?limit=50`
- **Purpose**: Get interaction data from BigQuery
- **Response**: Array of interaction objects (deals, contacts, etc.)

## Frontend Configuration

The frontend API client is configured in `langgraph-crm-insight/src/lib/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";
```
```

To change the backend URL, set the environment variable:
```bash
VITE_API_URL=http://your-backend-url:8001
```

## Backend Configuration

The backend runs on port 8001 by default (configured in `config.py`):

```python
api_port: int = 8001  # Changed to 8001 to avoid port conflicts
```

## Email Sync

The backend automatically syncs emails every 30 minutes:
- Checks for unread emails
- Filters business-related emails
- Extracts structured CRM data
- Stores in BigQuery
- Marks emails as read

This runs as a background task when the FastAPI server starts.

## Running the System

### Backend
```bash
cd crm-ai-agent
uv run python main.py
# Server runs on http://localhost:8001
```

### Frontend
```bash
cd langgraph-crm-insight
npm run dev
# App runs on http://localhost:8080
```

## Testing

Run the API endpoint tests:
```bash
cd crm-ai-agent
uv run pytest tests/test_api_endpoints.py -v
```

## CORS Configuration

The backend is configured to allow requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (alternative)
- `http://127.0.0.1:5173`

To add more origins, edit `api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://your-frontend-url"],
    ...
)
```

## Data Flow

1. **Interactions Data**: Frontend fetches from `/api/interactions` → BigQuery → Displayed in dashboard
2. **Chat**: User sends message → `/api/chat` → Chat Agent → BigQuery/Calendar → Response
3. **Emails**: Frontend can fetch from `/api/emails` → Gmail API → Displayed
4. **Calendar**: Frontend fetches from `/api/calendar/events` → Google Calendar API → Displayed

## Environment Variables

### Backend (.env)
- `GCP_PROJECT_ID`: Your GCP project ID
- `BIGQUERY_DATASET`: Dataset name (default: CRM_DATA)
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`: Gmail API credentials
- `GCP_SERVICE_ACCOUNT_PATH`: Path to service account JSON (for Vertex AI)

### Frontend
- `VITE_API_URL`: Backend API URL (optional, defaults to localhost:8001)

