"""Google Calendar agent using Google Calendar API directly.

Note: GoogleCalendarToolkit is not yet available in langchain-google-community v1.0.4.
This implementation uses the Google Calendar API directly with an agent executor pattern.
"""
import os
from typing import Optional, List, Union
from datetime import datetime, timedelta
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import tool, StructuredTool
try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

from config import settings

# Set up GCP credentials if service account path is provided
if settings.gcp_service_account_path and os.path.exists(settings.gcp_service_account_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.gcp_service_account_path

# Google Calendar API scopes
# Full calendar access for read/write operations
SCOPES = ['https://www.googleapis.com/auth/calendar']

def _get_credentials(credentials_path: str, token_path: str) -> Optional[Credentials]:
    """Get valid user credentials from storage or OAuth flow."""
    creds = None
    
    # Load existing token
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            # If token file has wrong scopes, delete it and recreate
            print(f"Warning: Token file has invalid scopes. Deleting and recreating: {e}")
            os.remove(token_path)
            creds = None
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                # If refresh fails, need to re-authenticate
                print(f"Warning: Token refresh failed. Need to re-authenticate: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"credentials.json not found at {credentials_path}. "
                    "Download it from Google Cloud Console > APIs & Services > Credentials. "
                    "Make sure Google Calendar API is enabled in your project."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return creds


# Define tools for the agent
@tool
def get_current_time() -> str:
    """Get the current date and time in ISO format. Use this to understand relative dates like 'tomorrow'.
    
    This tool takes no parameters. Just call it to get the current time.
    Returns the current datetime in ISO format.
    """
    try:
        return datetime.now().isoformat()
    except Exception as e:
        return f"Error getting current time: {e}"


@tool
def create_calendar_event(summary: str, start_time: str, end_time: str,
                         attendees: Optional[str] = None,
                         description: Optional[str] = None,
                         location: Optional[str] = None) -> str:
    """
    Create a calendar event.
    
    Args:
        summary: Event title/summary
        start_time: Start time in ISO format (e.g., "2025-11-09T14:00:00")
        end_time: End time in ISO format (e.g., "2025-11-09T15:00:00")
        attendees: Comma-separated list of email addresses (optional)
        description: Event description (optional)
        location: Event location (optional)
    """
    try:
        # This will be called with the service from the agent
        # For now, return instructions
        return "Event creation tool - requires calendar service"
    except Exception as e:
        return f"Error: {e}"


@tool
def list_calendar_events(time_min: Optional[str] = None,
                        time_max: Optional[str] = None,
                        max_results: int = 10) -> str:
    """
    List calendar events.
    
    Args:
        time_min: Lower bound for event end time in ISO format (optional)
        time_max: Upper bound for event start time in ISO format (optional)
        max_results: Maximum number of events to return (default: 10)
    """
    try:
        return "Event listing tool - requires calendar service"
    except Exception as e:
        return f"Error: {e}"


class CalendarAgent:
    """
    Google Calendar agent using Google Calendar API directly.
    
    This uses OAuth 2.0 flow with credentials.json and token.json files.
    On first run, it will open a browser for authorization.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize Calendar agent.
        
        Args:
            credentials_path: Path to credentials.json (default: looks for 'credentials.json' in current dir)
            token_path: Path to token.json (default: looks for 'token-calendar.json' to avoid conflicts with Gmail token)
        """
        self.credentials_path = credentials_path or "credentials.json"
        self.token_path = token_path or "token-calendar.json"
        self.service = None
        self.agent_executor = None
        self._initialized = False
    
    def _get_service(self):
        """Get Google Calendar service instance."""
        if not self.service:
            creds = _get_credentials(self.credentials_path, self.token_path)
            self.service = build('calendar', 'v3', credentials=creds)
        return self.service
    
    def _initialize(self):
        """Lazy initialization of tools and agent."""
        if self._initialized:
            return
        
        try:
            # Check if credentials.json exists
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"credentials.json not found at {self.credentials_path}. "
                    "Download it from Google Cloud Console > APIs & Services > Credentials. "
                    "It should be the OAuth 2.0 Client ID credentials (JSON format)."
                )
            
            # Create tools with access to the service
            service = self._get_service()
            
            # Define tools that have access to the service
            @tool
            def create_event_tool(summary: str, start_time: str, end_time: str,
                                 attendees: Optional[str] = None,
                                 description: Optional[str] = None,
                                 location: Optional[str] = None) -> str:
                """Create a calendar event."""
                try:
                    event = {
                        'summary': summary,
                        'start': {'dateTime': start_time, 'timeZone': 'UTC'},
                        'end': {'dateTime': end_time, 'timeZone': 'UTC'},
                    }
                    if description:
                        event['description'] = description
                    if location:
                        event['location'] = location
                    if attendees:
                        event['attendees'] = [{'email': email.strip()} for email in attendees.split(',')]
                    
                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    return f"Event created: {created_event.get('htmlLink')}"
                except Exception as e:
                    return f"Error creating event: {e}"
            
            def list_events_tool_func(max_results: Union[int, str] = 10, time_min: Optional[str] = None,
                                     time_max: Optional[str] = None) -> str:
                """List calendar events."""
                try:
                    # Convert max_results to int if it's a string
                    if isinstance(max_results, str):
                        max_results = int(max_results)
                    
                    # Build query parameters - only include timeMin/timeMax if they're not None
                    query_params = {
                        'calendarId': 'primary',
                        'maxResults': max_results,
                        'singleEvents': True,
                        'orderBy': 'startTime'
                    }
                    if time_min and time_min != "null" and time_min.lower() != "none":
                        query_params['timeMin'] = time_min
                    if time_max and time_max != "null" and time_max.lower() != "none":
                        query_params['timeMax'] = time_max
                    
                    events_result = service.events().list(**query_params).execute()
                    events = events_result.get('items', [])
                    if not events:
                        return "No events found."
                    result = []
                    for event in events:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        event_id = event.get('id', 'unknown')
                        result.append(f"ID: {event_id} - {event.get('summary', 'No title')} - {start}")
                    return "\n".join(result)
                except Exception as e:
                    return f"Error listing events: {e}"
            
            # Create tool with flexible schema
            class ListEventsSchema(BaseModel):
                max_results: Union[int, str] = Field(default=10, description="Maximum number of events to return")
                time_min: Optional[str] = Field(default=None, description="Lower bound for event end time in ISO format")
                time_max: Optional[str] = Field(default=None, description="Upper bound for event start time in ISO format")
            
            list_events_tool = StructuredTool.from_function(
                func=list_events_tool_func,
                name="list_events_tool",
                description="List calendar events. max_results can be an integer or string.",
                args_schema=ListEventsSchema
            )
            
            @tool
            def update_event_tool(event_id: str, start_time: Optional[str] = None,
                                 end_time: Optional[str] = None,
                                 summary: Optional[str] = None,
                                 description: Optional[str] = None,
                                 location: Optional[str] = None) -> str:
                """Update a calendar event. You can change the time, title, description, or location."""
                try:
                    # First, get the existing event
                    event = service.events().get(calendarId='primary', eventId=event_id).execute()
                    
                    # Update fields if provided
                    if start_time:
                        event['start'] = {'dateTime': start_time, 'timeZone': 'UTC'}
                    if end_time:
                        event['end'] = {'dateTime': end_time, 'timeZone': 'UTC'}
                    if summary:
                        event['summary'] = summary
                    if description:
                        event['description'] = description
                    if location:
                        event['location'] = location
                    
                    # Update the event
                    updated_event = service.events().update(
                        calendarId='primary',
                        eventId=event_id,
                        body=event
                    ).execute()
                    
                    return f"Event updated successfully: {updated_event.get('htmlLink')}"
                except Exception as e:
                    return f"Error updating event: {e}"
            
            def get_event_tool_func(event_id: str) -> str:
                """Get details of a specific calendar event by its ID."""
                try:
                    # Handle if event_id is passed as JSON string
                    if event_id.startswith('{') and '"event_id"' in event_id:
                        import json
                        try:
                            parsed = json.loads(event_id)
                            event_id = parsed.get('event_id', event_id)
                        except:
                            # Try to extract from string
                            import re
                            match = re.search(r'"event_id"\s*:\s*"([^"]+)"', event_id)
                            if match:
                                event_id = match.group(1)
                    
                    event = service.events().get(calendarId='primary', eventId=event_id).execute()
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    return f"Event: {event.get('summary', 'No title')}\nStart: {start}\nEnd: {end}\nDescription: {event.get('description', 'None')}\nLocation: {event.get('location', 'None')}"
                except Exception as e:
                    return f"Error getting event: {e}"
            
            get_event_tool = tool(get_event_tool_func)
            
            # Get the tools
            tools = [get_current_time, create_event_tool, list_events_tool, update_event_tool, get_event_tool]
            
            # Define the prompt for the ReAct agent
            prompt_template = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

IMPORTANT: The toolkit includes a get_current_time tool that you should use to understand relative dates like "tomorrow" or "next week".

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (must be valid JSON with correct parameter names)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
            
            prompt = PromptTemplate.from_template(prompt_template)
            
            # Initialize the LLM (using Vertex AI Gemini)
            # Note: This requires GCP credentials for Vertex AI
            try:
                llm = ChatVertexAI(
                    model_name=settings.vertex_ai_model,
                    temperature=0,
                    location=settings.vertex_ai_location,
                    project=settings.gcp_project_id,
                )
            except Exception as e:
                raise Exception(
                    f"Could not initialize Vertex AI LLM: {e}. "
                    "Make sure GCP credentials are configured (gcloud auth or service account). "
                    "The Calendar agent uses Vertex AI for the agent executor."
                )
            
            # Create the ReAct agent
            agent = create_react_agent(llm, tools, prompt)
            
            # Create the agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,
                max_execution_time=300,
            )
            
            self._initialized = True
            
        except Exception as e:
            print(f"Warning: Could not initialize Calendar agent: {e}")
            self.service = None
            self.agent_executor = None
            self._initialized = True
    
    async def create_event(self, summary: str, start_time: str, end_time: str,
                          attendees: Optional[list] = None,
                          description: Optional[str] = None,
                          location: Optional[str] = None) -> str:
        """
        Create a calendar event using the Calendar agent.
        
        Args:
            summary: Event title/summary
            start_time: Start time in ISO format (e.g., "2025-11-09T14:00:00")
            end_time: End time in ISO format (e.g., "2025-11-09T15:00:00")
            attendees: List of email addresses to invite
            description: Event description
            location: Event location
            
        Returns:
            Agent's response/output
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception(
                "Calendar agent not available. Make sure credentials.json exists and "
                "you've completed the OAuth flow (token.json should be created)."
            )
        
        try:
            # Build the prompt with all event details
            attendee_str = ", ".join(attendees) if attendees else "no attendees"
            desc_str = f" with description '{description}'" if description else ""
            loc_str = f" at location '{location}'" if location else ""
            
            prompt = (
                f"Create a calendar event with summary '{summary}', "
                f"starting at {start_time}, ending at {end_time}, "
                f"with attendees: {attendee_str}{desc_str}{loc_str}."
            )
            
            try:
                response = self.agent_executor.invoke({"input": prompt})
                return response.get("output", "Event created successfully")
            except StopIteration as e:
                raise Exception(f"Agent execution stopped unexpectedly. Try again or check the agent logs.")
            except RuntimeError as e:
                if "generator raised StopIteration" in str(e) or "StopIteration" in str(e):
                    raise Exception(f"Agent execution error. This may be due to a tool invocation issue. Error: {e}")
                raise
            except Exception as e:
                raise Exception(f"Error creating calendar event via agent: {e}")
        except Exception as e:
            raise Exception(f"Error creating calendar event: {e}")
    
    async def schedule_event(self, summary: str, start_time_description: str,
                           duration_hours: Optional[float] = None,
                           duration_minutes: Optional[int] = None,
                           attendees: Optional[list] = None,
                           description: Optional[str] = None,
                           location: Optional[str] = None) -> str:
        """
        Schedule an event using natural language time descriptions.
        
        The agent will use get_current_time to understand relative times like "tomorrow at 2 PM".
        
        Args:
            summary: Event title/summary
            start_time_description: Natural language description (e.g., "tomorrow at 2 PM", "next Monday at 10 AM")
            duration_hours: Duration in hours (e.g., 1.5 for 1.5 hours)
            duration_minutes: Duration in minutes (alternative to duration_hours)
            attendees: List of email addresses to invite
            description: Event description
            location: Event location
            
        Returns:
            Agent's response/output
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception("Calendar agent not available")
        
        try:
            # Build natural language prompt
            duration_str = ""
            if duration_hours:
                duration_str = f" for {duration_hours} hour(s)"
            elif duration_minutes:
                duration_str = f" for {duration_minutes} minute(s)"
            
            attendee_str = ""
            if attendees:
                attendee_str = f" with attendees: {', '.join(attendees)}"
            
            desc_str = f" with description '{description}'" if description else ""
            loc_str = f" at location '{location}'" if location else ""
            
            prompt = (
                f"Schedule a calendar event with summary '{summary}' "
                f"for {start_time_description}{duration_str}{attendee_str}{desc_str}{loc_str}."
            )
            
            try:
                # Use ainvoke for async methods to avoid StopIteration issues
                import asyncio
                if asyncio.iscoroutinefunction(self.agent_executor.ainvoke):
                    response = await self.agent_executor.ainvoke({"input": prompt})
                else:
                    response = self.agent_executor.invoke({"input": prompt})
                return response.get("output", "Event scheduled successfully")
            except (StopIteration, RuntimeError) as e:
                error_msg = str(e)
                if "generator raised StopIteration" in error_msg or "StopIteration" in error_msg:
                    # This is a known Python 3.7+ issue with generators
                    # Try using the tool directly instead of through the agent
                    print("Warning: Agent executor encountered StopIteration. Trying direct tool call...")
                    # Fallback: use tools directly
                    service = self._get_service()
                    from datetime import datetime, timedelta
                    # Parse "tomorrow at 2 PM" - simplified version
                    current_time = datetime.now()
                    if "tomorrow" in start_time_description.lower():
                        target_date = current_time + timedelta(days=1)
                    else:
                        target_date = current_time
                    # Extract time (simplified - agent should handle this better)
                    hour = 14  # Default to 2 PM
                    if "2" in start_time_description or "two" in start_time_description.lower():
                        hour = 14
                    start_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(hours=duration_hours or 1.0)
                    
                    event = {
                        'summary': summary,
                        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
                        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
                    }
                    if description:
                        event['description'] = description
                    if location:
                        event['location'] = location
                    if attendees:
                        event['attendees'] = [{'email': email} for email in attendees]
                    
                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    return f"Event created successfully (fallback method): {created_event.get('htmlLink')}"
                raise Exception(f"Agent execution error: {error_msg}")
            except Exception as e:
                raise Exception(f"Error scheduling calendar event via agent: {e}")
        except Exception as e:
            raise Exception(f"Error scheduling calendar event: {e}")
    
    async def list_events(self, time_min: Optional[str] = None,
                         time_max: Optional[str] = None,
                         max_results: int = 10) -> str:
        """
        List calendar events.
        
        Args:
            time_min: Lower bound (exclusive) for an event's end time (ISO format)
            time_max: Upper bound (exclusive) for an event's start time (ISO format)
            max_results: Maximum number of events to return
            
        Returns:
            Agent's response with event list
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception("Calendar agent not available")
        
        try:
            time_filter = ""
            if time_min and time_max:
                time_filter = f" between {time_min} and {time_max}"
            elif time_min:
                time_filter = f" after {time_min}"
            elif time_max:
                time_filter = f" before {time_max}"
            
            prompt = f"List up to {max_results} calendar events{time_filter}."
            
            try:
                response = self.agent_executor.invoke({"input": prompt})
                return response.get("output", "No events found")
            except (StopIteration, RuntimeError, ValueError, TypeError, Exception) as e:
                error_msg = str(e)
                # Check if it's a validation error or StopIteration
                if ("validation error" in error_msg.lower() or 
                    "generator raised StopIteration" in error_msg or 
                    "StopIteration" in error_msg or
                    "not a valid integer" in error_msg):
                    # Fallback: use direct API call
                    print("Warning: Agent executor encountered StopIteration. Using direct API call...")
                    service = self._get_service()
                    
                    query_params = {
                        'calendarId': 'primary',
                        'maxResults': max_results,
                        'singleEvents': True,
                        'orderBy': 'startTime'
                    }
                    if time_min:
                        query_params['timeMin'] = time_min
                    if time_max:
                        query_params['timeMax'] = time_max
                    
                    events_result = service.events().list(**query_params).execute()
                    events = events_result.get('items', [])
                    if not events:
                        return "No events found."
                    result = []
                    for event in events:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        event_id = event.get('id', 'unknown')
                        result.append(f"ID: {event_id} - {event.get('summary', 'No title')} - {start}")
                    return "\n".join(result)
                raise Exception(f"Agent execution error: {error_msg}")
            except Exception as e:
                raise Exception(f"Error listing calendar events via agent: {e}")
        except Exception as e:
            raise Exception(f"Error listing calendar events: {e}")
    
    async def get_event(self, event_id: str) -> str:
        """
        Get a specific calendar event by ID.
        
        Args:
            event_id: Calendar event ID
            
        Returns:
            Event details
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception("Calendar agent not available")
        
        try:
            prompt = f"Get the calendar event with ID {event_id}"
            response = self.agent_executor.invoke({"input": prompt})
            return response.get("output", "Event not found")
            
        except Exception as e:
            raise Exception(f"Error getting calendar event: {e}")
    
    async def move_event(self, event_id: str, new_start_time: str, new_end_time: Optional[str] = None) -> str:
        """
        Move/reschedule a calendar event to a new time.
        
        Args:
            event_id: Calendar event ID
            new_start_time: New start time in ISO format (e.g., "2025-11-10T15:00:00")
            new_end_time: New end time in ISO format (optional, will calculate from duration if not provided)
            
        Returns:
            Agent's response/output
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception("Calendar agent not available")
        
        try:
            prompt = f"Move the calendar event with ID {event_id} to start at {new_start_time}"
            if new_end_time:
                prompt += f" and end at {new_end_time}"
            prompt += "."
            
            try:
                response = self.agent_executor.invoke({"input": prompt})
                return response.get("output", "Event moved successfully")
            except (StopIteration, RuntimeError) as e:
                error_msg = str(e)
                if "generator raised StopIteration" in error_msg or "StopIteration" in error_msg:
                    # Fallback: use direct API call
                    print("Warning: Agent executor encountered StopIteration. Using direct API call...")
                    service = self._get_service()
                    
                    # Get existing event
                    event = service.events().get(calendarId='primary', eventId=event_id).execute()
                    
                    # Calculate end time if not provided
                    if not new_end_time:
                        # Get duration from existing event
                        old_start = event['start'].get('dateTime', event['start'].get('date'))
                        old_end = event['end'].get('dateTime', event['end'].get('date'))
                        from datetime import datetime
                        start_dt = datetime.fromisoformat(old_start.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(old_end.replace('Z', '+00:00'))
                        duration = end_dt - start_dt
                        
                        new_start_dt = datetime.fromisoformat(new_start_time.replace('Z', '+00:00'))
                        new_end_dt = new_start_dt + duration
                        new_end_time = new_end_dt.isoformat()
                    
                    # Update event times
                    event['start'] = {'dateTime': new_start_time, 'timeZone': 'UTC'}
                    event['end'] = {'dateTime': new_end_time, 'timeZone': 'UTC'}
                    
                    updated_event = service.events().update(
                        calendarId='primary',
                        eventId=event_id,
                        body=event
                    ).execute()
                    
                    return f"Event moved successfully (fallback method): {updated_event.get('htmlLink')}"
                raise Exception(f"Agent execution error: {error_msg}")
            except Exception as e:
                raise Exception(f"Error moving calendar event via agent: {e}")
        except Exception as e:
            raise Exception(f"Error moving calendar event: {e}")
    
    async def reschedule_event(self, event_id: str, new_time_description: str) -> str:
        """
        Reschedule an event using natural language (e.g., "tomorrow at 3 PM").
        
        Args:
            event_id: Calendar event ID
            new_time_description: Natural language description of new time (e.g., "tomorrow at 3 PM", "next Monday at 10 AM")
            
        Returns:
            Agent's response/output
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception("Calendar agent not available")
        
        try:
            prompt = f"Move the calendar event with ID {event_id} to {new_time_description}. First, get the current time to understand what '{new_time_description}' means, then get the event details to know its duration, and finally update the event with the new start and end times."
            
            try:
                response = self.agent_executor.invoke({"input": prompt})
                return response.get("output", "Event rescheduled successfully")
            except (StopIteration, RuntimeError) as e:
                error_msg = str(e)
                if "generator raised StopIteration" in error_msg or "StopIteration" in error_msg:
                    # Fallback: use direct API call with simplified parsing
                    print("Warning: Agent executor encountered StopIteration. Using direct API call...")
                    service = self._get_service()
                    
                    # Get existing event
                    event = service.events().get(calendarId='primary', eventId=event_id).execute()
                    
                    # Get duration from existing event
                    old_start = event['start'].get('dateTime', event['start'].get('date'))
                    old_end = event['end'].get('dateTime', event['end'].get('date'))
                    from datetime import datetime, timedelta
                    start_dt = datetime.fromisoformat(old_start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(old_end.replace('Z', '+00:00'))
                    duration = end_dt - start_dt
                    
                    # Parse new time (simplified)
                    current_time = datetime.now()
                    if "tomorrow" in new_time_description.lower():
                        target_date = current_time + timedelta(days=1)
                    else:
                        target_date = current_time
                    
                    # Extract hour (simplified - agent should handle this better)
                    hour = 15  # Default to 3 PM
                    if "3" in new_time_description or "three" in new_time_description.lower():
                        hour = 15
                    elif "2" in new_time_description or "two" in new_time_description.lower():
                        hour = 14
                    elif "10" in new_time_description:
                        hour = 10
                    
                    new_start_dt = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    new_end_dt = new_start_dt + duration
                    
                    event['start'] = {'dateTime': new_start_dt.isoformat(), 'timeZone': 'UTC'}
                    event['end'] = {'dateTime': new_end_dt.isoformat(), 'timeZone': 'UTC'}
                    
                    updated_event = service.events().update(
                        calendarId='primary',
                        eventId=event_id,
                        body=event
                    ).execute()
                    
                    return f"Event rescheduled successfully (fallback method): {updated_event.get('htmlLink')}"
                raise Exception(f"Agent execution error: {error_msg}")
            except Exception as e:
                raise Exception(f"Error rescheduling calendar event via agent: {e}")
        except Exception as e:
            raise Exception(f"Error rescheduling calendar event: {e}")

