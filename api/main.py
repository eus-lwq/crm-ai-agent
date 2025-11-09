"""FastAPI application with endpoints for chat, email, and calendar."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from config import settings
from src.agents.chatagent import initialize_agent, chat
from src.agents.calendar_agent import CalendarAgent
from services.email_monitor import EmailMonitor
from services.email_extractor import EmailExtractorAgent

app = FastAPI(title="CRM AI Agent API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # Vite default port
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents and services (lazy initialization)
_chat_agent = None
_calendar_agent = None
_email_monitor = None
_email_extractor = None

def get_chat_agent():
    """Get or initialize chat agent."""
    global _chat_agent
    if _chat_agent is None:
        try:
            _chat_agent = initialize_agent(
                model_name=settings.vertex_ai_model,
                vertex_location=settings.vertex_ai_location,
                bq_project_id=settings.gcp_project_id,
                bq_dataset_id=settings.bigquery_dataset,
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Failed to initialize chat agent: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise
    return _chat_agent

def get_calendar_agent():
    """Get or initialize calendar agent."""
    global _calendar_agent
    if _calendar_agent is None:
        _calendar_agent = CalendarAgent()
    return _calendar_agent

def get_email_monitor():
    """Get or initialize email monitor."""
    global _email_monitor
    if _email_monitor is None:
        _email_monitor = EmailMonitor()
    return _email_monitor

def get_email_extractor():
    """Get or initialize email extractor."""
    global _email_extractor
    if _email_extractor is None:
        _email_extractor = EmailExtractorAgent()
    return _email_extractor


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class ThinkingStep(BaseModel):
    thought: str
    action: str
    action_input: str
    observation: str

class ChatResponse(BaseModel):
    response: str
    history: List[Dict[str, Any]]
    thinking_steps: Optional[List[ThinkingStep]] = None

class EmailResponse(BaseModel):
    id: str
    subject: str
    from_email: str
    to_email: str
    date: str
    body: str
    extracted_data: Optional[Dict[str, Any]] = None

class CalendarEventResponse(BaseModel):
    id: str
    summary: str
    start: str
    end: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    html_link: Optional[str] = None

class CalendarEventRequest(BaseModel):
    summary: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

class CalendarEventUpdateRequest(BaseModel):
    event_id: str
    summary: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

class InteractionData(BaseModel):
    id: Optional[int] = None
    contact_name: Optional[str] = None
    company: Optional[str] = None
    next_step: Optional[str] = None
    deal_value: Optional[float] = None
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    interaction_medium: Optional[str] = None

class InteractionFrequencyData(BaseModel):
    date: str
    emails: int = 0
    voice_calls: int = 0
    total: int = 0

class InteractionMethodData(BaseModel):
    method: str
    contacts: int
    percentage: float


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "crm-ai-agent"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for CRM agent.
    Allows querying BigQuery tables, checking calendar, editing calendar, and adding events.
    """
    try:
        import traceback
        agent = get_chat_agent()
        
        # Convert conversation history format if provided
        history = None
        if request.conversation_history:
            from langchain_core.messages import HumanMessage, AIMessage
            history = []
            for msg in request.conversation_history:
                if msg.get("role") == "user":
                    history.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    history.append(AIMessage(content=msg.get("content", "")))
        
        # Call chat function - run in thread pool to avoid blocking event loop
        import asyncio
        import functools
        
        # Use run_in_executor with proper error handling
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                functools.partial(chat, request.message, history)
            )
        except Exception as executor_error:
            # Re-raise with more context
            raise Exception(f"Error executing chat in thread pool: {str(executor_error)}") from executor_error
        
        # Convert history to frontend format
        formatted_history = []
        if result and "history" in result:
            for msg in result["history"]:
                if hasattr(msg, "content"):
                    role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                    formatted_history.append({
                        "role": role,
                        "content": msg.content
                    })
        
        response_text = result.get("response", "No response generated") if result else "Error: No result from agent"
        thinking_steps = result.get("thinking_steps", []) if result else []
        
        # Format thinking steps
        formatted_thinking_steps = []
        for step in thinking_steps:
            formatted_thinking_steps.append(ThinkingStep(
                thought=step.get("thought", ""),
                action=step.get("action", ""),
                action_input=step.get("action_input", ""),
                observation=step.get("observation", "")
            ))
        
        return ChatResponse(
            response=response_text,
            history=formatted_history,
            thinking_steps=formatted_thinking_steps if formatted_thinking_steps else None
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e) if str(e) else repr(e)
        error_type = type(e).__name__
        
        print(f"=" * 60)
        print(f"Chat endpoint error: {error_type}: {error_msg}")
        print(f"Traceback:")
        print(error_trace)
        print(f"=" * 60)
        
        # Return more detailed error for debugging
        detail_msg = f"{error_type}: {error_msg}" if error_msg else f"{error_type} occurred"
        raise HTTPException(status_code=500, detail=f"Chat error: {detail_msg}")


@app.get("/api/emails", response_model=List[EmailResponse])
async def get_emails(limit: int = 10):
    """
    Get recent emails from Gmail.
    Syncs with Google email and returns recent emails.
    """
    try:
        monitor = get_email_monitor()
        monitor._initialize()
        
        if not monitor.service:
            raise HTTPException(status_code=500, detail="Gmail service not initialized")
        
        service = monitor.service
        
        # Get recent emails from inbox
        try:
            messages_result = service.users().messages().list(
                userId='me',
                maxResults=limit,
                q='in:inbox'
            ).execute()
            
            messages = messages_result.get('messages', [])
            emails = []
            
            for msg in messages[:limit]:
                try:
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Parse email content
                    from services.email_monitor import _parse_email_content
                    email_data = _parse_email_content(message)
                    
                    # Try to extract structured data (optional, don't fail if it doesn't work)
                    extracted_data = None
                    try:
                        extractor = get_email_extractor()
                        email_metadata = {
                            "subject": email_data['subject'],
                            "from": email_data['from'],
                            "to": email_data['to'],
                            "date": email_data['date']
                        }
                        extracted = await extractor.extract_from_email(
                            email_data['body'],
                            email_metadata
                        )
                        extracted_data = extracted.dict()
                    except Exception as extract_error:
                        # Extraction failed, but we still return the email
                        print(f"Warning: Could not extract data from email: {extract_error}")
                    
                    emails.append(EmailResponse(
                        id=email_data['message_id'],
                        subject=email_data['subject'],
                        from_email=email_data['from'],
                        to_email=email_data['to'],
                        date=email_data['date'],
                        body=email_data['body'][:1000],  # Limit body length for frontend
                        extracted_data=extracted_data
                    ))
                except Exception as e:
                    print(f"Error processing email {msg.get('id')}: {e}")
                    continue
            
            return emails
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sync error: {str(e)}")


@app.get("/api/calendar/events", response_model=List[CalendarEventResponse])
async def get_calendar_events(max_results: int = 20):
    """
    Get calendar events from Google Calendar.
    Syncs with Google Calendar and returns upcoming events.
    """
    try:
        agent = get_calendar_agent()
        
        # Get events using direct API call (more reliable than agent)
        # Initialize calendar agent service if needed
        if not hasattr(agent, 'service') or agent.service is None:
            agent._initialize()
        service = agent.service
        
        from datetime import datetime, timedelta
        time_min = datetime.utcnow().isoformat() + 'Z'
        time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            attendees = [a.get('email') for a in event.get('attendees', [])]
            
            formatted_events.append(CalendarEventResponse(
                id=event['id'],
                summary=event.get('summary', 'No title'),
                start=start,
                end=end,
                description=event.get('description'),
                location=event.get('location'),
                attendees=attendees if attendees else None,
                html_link=event.get('htmlLink')
            ))
        
        return formatted_events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calendar sync error: {str(e)}")


@app.post("/api/calendar/events", response_model=CalendarEventResponse)
async def create_calendar_event(request: CalendarEventRequest):
    """
    Create a new calendar event.
    Can be called directly or via chat agent.
    """
    try:
        agent = get_calendar_agent()
        
        result = await agent.create_event(
            summary=request.summary,
            start_time=request.start_time,
            end_time=request.end_time,
            description=request.description,
            location=request.location,
            attendees=request.attendees
        )
        
        # Extract event ID from result if possible
        # Otherwise, get the most recent event
        if not hasattr(agent, 'service') or agent.service is None:
            agent._initialize()
        service = agent.service
        events_result = service.events().list(
            calendarId='primary',
            maxResults=1,
            singleEvents=True,
            orderBy='updated'
        ).execute()
        
        if events_result.get('items'):
            event = events_result['items'][0]
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            attendees = [a.get('email') for a in event.get('attendees', [])]
            
            return CalendarEventResponse(
                id=event['id'],
                summary=event.get('summary', 'No title'),
                start=start,
                end=end,
                description=event.get('description'),
                location=event.get('location'),
                attendees=attendees if attendees else None,
                html_link=event.get('htmlLink')
            )
        else:
            raise HTTPException(status_code=500, detail="Event created but could not retrieve details")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating calendar event: {str(e)}")


@app.put("/api/calendar/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(event_id: str, request: CalendarEventUpdateRequest):
    """
    Update a calendar event.
    Can be called directly or via chat agent.
    """
    try:
        agent = get_calendar_agent()
        
        # Use move_event or direct API call
        if request.start_time:
            await agent.move_event(
                event_id=event_id,
                new_start_time=request.start_time,
                new_end_time=request.end_time
            )
        
        # Get updated event
        if not hasattr(agent, 'service') or agent.service is None:
            agent._initialize()
        service = agent.service
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        attendees = [a.get('email') for a in event.get('attendees', [])]
        
        return CalendarEventResponse(
            id=event['id'],
            summary=event.get('summary', 'No title'),
            start=start,
            end=end,
            description=event.get('description'),
            location=event.get('location'),
            attendees=attendees if attendees else None,
            html_link=event.get('htmlLink')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating calendar event: {str(e)}")


@app.get("/api/interactions", response_model=List[InteractionData])
async def get_interactions(limit: int = 50):
    """
    Get interaction data from BigQuery.
    Returns deals/interactions stored in BigQuery.
    Table: ai-hackathon-477617.CRM_DATA.deals
    """
    try:
        from google.cloud import bigquery
        from src.agents.agent_tools import get_bigquery_client
        
        client = get_bigquery_client()
        
        # Use the exact table path: ai-hackathon-477617.CRM_DATA.deals
        # Construct from settings, but ensure it matches the exact path
        project_id = settings.gcp_project_id or "ai-hackathon-477617"
        dataset_name = (settings.bigquery_dataset.upper() if settings.bigquery_dataset else "CRM_DATA")
        table_id = f"{project_id}.{dataset_name}.deals"
        
        print(f"🔍 Querying BigQuery table: {table_id}")
        
        query = f"""
        SELECT 
            contact_name,
            company,
            next_step,
            deal_value,
            follow_up_date,
            notes,
            interaction_medium,
            created_at
        FROM `{table_id}`
        ORDER BY follow_up_date DESC NULLS LAST, created_at DESC
        LIMIT {limit}
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        interactions = []
        for idx, row in enumerate(results, 1):
            interactions.append(InteractionData(
                id=idx,
                contact_name=row.contact_name if hasattr(row, 'contact_name') else None,
                company=row.company if hasattr(row, 'company') else None,
                next_step=row.next_step if hasattr(row, 'next_step') else None,
                deal_value=float(row.deal_value) if hasattr(row, 'deal_value') and row.deal_value is not None else None,
                follow_up_date=str(row.follow_up_date) if hasattr(row, 'follow_up_date') and row.follow_up_date else None,
                notes=row.notes if hasattr(row, 'notes') else None,
                interaction_medium=row.interaction_medium if hasattr(row, 'interaction_medium') else None
            ))
        
        print(f"✅ Retrieved {len(interactions)} interactions from BigQuery")
        return interactions
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error fetching interactions from BigQuery: {e}")
        print(f"Error details: {error_details}")
        # Use table_id from the try block scope
        project_id = settings.gcp_project_id or "ai-hackathon-477617"
        dataset_name = (settings.bigquery_dataset.upper() if settings.bigquery_dataset else "CRM_DATA")
        table_id = f"{project_id}.{dataset_name}.deals"
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching interactions from BigQuery table {table_id}: {str(e)}"
        )


@app.get("/api/interactions/frequency", response_model=List[InteractionFrequencyData])
async def get_interaction_frequency(days: int = 30):
    """
    Get interaction frequency data grouped by follow_up_date and interaction_medium.
    Returns data for the Recent Interaction Frequency chart.
    Groups interactions by their follow_up_date to show scheduled follow-ups over time.
    """
    try:
        from google.cloud import bigquery
        from src.agents.agent_tools import get_bigquery_client
        from datetime import datetime, timedelta
        
        client = get_bigquery_client()
        
        project_id = settings.gcp_project_id or "ai-hackathon-477617"
        dataset_name = (settings.bigquery_dataset.upper() if settings.bigquery_dataset else "CRM_DATA")
        table_id = f"{project_id}.{dataset_name}.deals"
        
        # Calculate date range - extend to future dates to include all follow_up_dates
        end_date = datetime.utcnow() + timedelta(days=365)  # Include future dates up to 1 year
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query to get frequency data grouped by follow_up_date
        # Uses follow_up_date when available, otherwise uses created_at as fallback
        # Includes all records with follow_up_date in the extended range
        query = f"""
        SELECT 
            DATE(COALESCE(
                follow_up_date,
                CAST(created_at AS DATE),
                CURRENT_DATE()
            )) as date,
            interaction_medium,
            COUNT(*) as count
        FROM `{table_id}`
        WHERE (
            -- Include records with follow_up_date in range (past or future)
            (follow_up_date >= '{start_date.date().isoformat()}' AND follow_up_date <= '{end_date.date().isoformat()}')
            OR
            -- Include records without follow_up_date but with created_at in past range
            (follow_up_date IS NULL AND created_at IS NOT NULL AND (
                CAST(created_at AS DATE) >= '{start_date.date().isoformat()}' 
                AND CAST(created_at AS DATE) <= '{datetime.utcnow().date().isoformat()}'
            ))
            OR
            -- Include records with neither (use current date)
            (follow_up_date IS NULL AND created_at IS NULL)
        )
        GROUP BY date, interaction_medium
        ORDER BY date ASC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        # Group by date
        date_data: dict[str, dict[str, int]] = {}
        for row in results:
            date_str = str(row.date) if hasattr(row, 'date') and row.date else None
            medium = row.interaction_medium if hasattr(row, 'interaction_medium') else None
            count = row.count if hasattr(row, 'count') else 0
            
            if not date_str:
                continue
            
            if date_str not in date_data:
                date_data[date_str] = {'emails': 0, 'voice_calls': 0, 'total': 0}
            
            # Normalize interaction_medium values
            medium_lower = (medium or '').lower()
            if 'email' in medium_lower:
                date_data[date_str]['emails'] += count
            elif 'voice' in medium_lower or 'call' in medium_lower:
                date_data[date_str]['voice_calls'] += count
            
            date_data[date_str]['total'] += count
        
        # Convert to list format
        frequency_data = []
        for date_str in sorted(date_data.keys()):
            data = date_data[date_str]
            frequency_data.append(InteractionFrequencyData(
                date=date_str,
                emails=data['emails'],
                voice_calls=data['voice_calls'],
                total=data['total']
            ))
        
        return frequency_data
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error fetching interaction frequency: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching interaction frequency: {str(e)}"
        )


@app.get("/api/interactions/methods", response_model=List[InteractionMethodData])
async def get_interaction_methods():
    """
    Get interaction method distribution.
    Returns data for the Interaction Method component.
    """
    try:
        from google.cloud import bigquery
        from src.agents.agent_tools import get_bigquery_client
        
        client = get_bigquery_client()
        
        project_id = settings.gcp_project_id or "ai-hackathon-477617"
        dataset_name = (settings.bigquery_dataset.upper() if settings.bigquery_dataset else "CRM_DATA")
        table_id = f"{project_id}.{dataset_name}.deals"
        
        query = f"""
        SELECT 
            interaction_medium,
            COUNT(DISTINCT contact_name) as contacts,
            COUNT(*) as total
        FROM `{table_id}`
        WHERE interaction_medium IS NOT NULL
        GROUP BY interaction_medium
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        # Calculate total contacts for percentage
        total_contacts = 0
        method_data = []
        for row in results:
            medium = row.interaction_medium if hasattr(row, 'interaction_medium') else None
            contacts = row.contacts if hasattr(row, 'contacts') else 0
            total_contacts += contacts
            
            # Normalize method names
            medium_lower = (medium or '').lower()
            if 'email' in medium_lower:
                method_name = "Email"
            elif 'voice' in medium_lower or 'call' in medium_lower:
                method_name = "Voice Call"
            else:
                method_name = medium or "Other"
            
            method_data.append({
                'method': method_name,
                'contacts': contacts,
                'raw_medium': medium
            })
        
        # Calculate percentages
        methods = []
        for data in method_data:
            percentage = (data['contacts'] / total_contacts * 100) if total_contacts > 0 else 0
            methods.append(InteractionMethodData(
                method=data['method'],
                contacts=data['contacts'],
                percentage=round(percentage, 1)
            ))
        
        # Sort by contact count (descending) to ensure stable order
        methods.sort(key=lambda x: x.contacts, reverse=True)
        
        return methods
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error fetching interaction methods: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching interaction methods: {str(e)}"
        )


# Background task for email sync (real-time: every 1 second)
@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    async def email_sync_loop():
        """Sync emails in real-time (every 1 second)."""
        print("🚀 Starting real-time email sync (checking every 1 second)...")
        while True:
            try:
                monitor = get_email_monitor()
                await monitor.process_unread_emails(max_results=3)
                # Wait 1 second before next check
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error in email sync loop: {e}")
                # On error, wait 1 second before retry
                await asyncio.sleep(1)
    
    # Start background task
    asyncio.create_task(email_sync_loop())
    print("✅ Real-time email sync background task started (checking every 1 second)")

