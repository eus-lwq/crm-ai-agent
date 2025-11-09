# Codebase Reorganization

This document describes the reorganization of the codebase into clear service and agent layers.

## New Structure

### Services (`services/`)
Services handle data ingestion, processing, and storage:

- **`email_monitor.py`** - Monitors Gmail for unread emails, filters business-related content, stores in BigQuery
- **`email_extractor.py`** - Extracts structured CRM data from emails using Vertex AI
- **`voice_service.py`** - Transcribes audio files and extracts CRM data (merged from `voice-pipeline/`)

### Agents (`src/agents/`)
Agents provide interactive AI capabilities:

- **`chatagent.py`** - CRM chat agent with BigQuery integration
- **`agent_tools.py`** - BigQuery tools for the chat agent
- **`prompts.py`** - System prompts for the chat agent
- **`calendar_agent.py`** - Google Calendar agent (moved from `services/`)
- **`gmail_agent.py`** - Gmail agent (moved from `services/`)

## Migration Guide

### Old Imports → New Imports

```python
# OLD
from services.calendar_agent import CalendarAgent
from services.gmail_agent import GmailAgent

# NEW
from src.agents.calendar_agent import CalendarAgent
from src.agents.gmail_agent import GmailAgent
```

```python
# OLD (voice-pipeline)
from voice_pipeline.src.transcriber import transcribe_audio_groq
from voice_pipeline.src.extractor import extract_crm_fields

# NEW
from services.voice_service import VoiceService, process_audio_file, extract_crm_fields_from_voice
```

### Using Services

```python
# Email monitoring
from services import EmailMonitor
monitor = EmailMonitor()
result = await monitor.process_unread_emails()

# Voice processing
from services import VoiceService
service = VoiceService()
result = service.process_audio_file("audio.mp3")
```

### Using Agents

```python
# Calendar agent
from src.agents import CalendarAgent
agent = CalendarAgent()
events = await agent.list_events()

# Gmail agent
from src.agents import GmailAgent
agent = GmailAgent()
response = await agent.send_email(to="...", subject="...", body="...")

# Chat agent
from src.agents import initialize_agent, chat
agent = initialize_agent()
result = chat("What tables are available?")
```

## What Changed

1. **Voice Pipeline Merged**: `voice-pipeline/src/` → `services/voice_service.py`
2. **Agents Consolidated**: `services/calendar_agent.py` and `services/gmail_agent.py` → `src/agents/`
3. **Clear Separation**: Services handle data processing, Agents handle AI interactions

