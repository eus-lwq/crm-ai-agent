"""
CRM Agent with BigQuery Integration using Vertex AI
Built with LangChain and LangGraph from scratch
"""

# ---------------------------------------------- #
from typing import Optional
from datetime import datetime
import asyncio

from google.oauth2 import service_account
from google.cloud import bigquery

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI

import operator
import json
import os

# --- UPDATED: Import tools, Config, and setters explicitly ---
from src.agents.agent_tools import (
    list_tables, get_table_schema, query_bigquery, 
    get_customer_summary, get_current_time,
    Config, get_bigquery_client, set_bigquery_client
)
from src.agents.prompts import SYSTEM_GUIDELINES

# Import email and calendar agents
from src.agents.gmail_agent import GmailAgent
from src.agents.calendar_agent import CalendarAgent

# Create singleton instances for email and calendar agents
_gmail_agent = None
_calendar_agent = None

def get_gmail_agent():
    """Get or create Gmail agent instance."""
    global _gmail_agent
    if _gmail_agent is None:
        _gmail_agent = GmailAgent()
    return _gmail_agent

def get_calendar_agent():
    """Get or create Calendar agent instance."""
    global _calendar_agent
    if _calendar_agent is None:
        _calendar_agent = CalendarAgent()
    return _calendar_agent

# Create email and calendar tools for the chat agent
from langchain_core.tools import tool, StructuredTool
import asyncio

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field

class SendEmailSchema(BaseModel):
    to: str = Field(description="Recipient email address (e.g., 'user@example.com')")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body/content")

def _send_email_func(to: str, subject: str, body: str) -> str:
    """
    Send an email to a recipient.
    
    Args:
        to: Recipient email address (e.g., "user@example.com")
        subject: Email subject line
        body: Email body/content
    
    Returns:
        Confirmation message indicating if the email was sent successfully
    """
    try:
        gmail_agent = get_gmail_agent()
        # Run async method in sync context - use new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new event loop in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, gmail_agent.send_email(to, subject, body))
                    result = future.result(timeout=60)
            else:
                result = loop.run_until_complete(gmail_agent.send_email(to, subject, body))
        except RuntimeError:
            # No event loop, create new one
            result = asyncio.run(gmail_agent.send_email(to, subject, body))
        return result
    except Exception as e:
        return f"Error sending email: {str(e)}"

# Create custom tool class for send_email too
class SendEmailTool(StructuredTool):
    """Custom tool that handles JSON string input from agent executor."""
    
    def _parse_input(self, tool_input):
        """Override _parse_input to handle dict and JSON string inputs."""
        # If tool_input is already a dict with the right keys, validate it directly
        if isinstance(tool_input, dict):
            if 'to' in tool_input or 'subject' in tool_input:
                try:
                    return self.args_schema(**tool_input).dict()
                except Exception:
                    pass
        
        # If tool_input is a JSON string, parse it first
        if isinstance(tool_input, str):
            if tool_input.strip().startswith('{'):
                try:
                    parsed = json.loads(tool_input)
                    if isinstance(parsed, dict):
                        try:
                            return self.args_schema(**parsed).dict()
                        except Exception:
                            pass
                except json.JSONDecodeError:
                    pass
        
        # Fall back to parent's parsing
        return super()._parse_input(tool_input)

send_email = SendEmailTool.from_function(
    func=_send_email_func,
    name="send_email",
    description="Send an email to a recipient. Args: to (recipient email), subject (email subject), body (email content))",
    args_schema=SendEmailSchema
)

class CreateCalendarEventSchema(BaseModel):
    summary: str = Field(description="Event title/summary")
    start_time: str = Field(description="Start time in ISO format (e.g., '2025-11-12T14:00:00') or natural language (e.g., 'tomorrow at 2 PM')")
    end_time: Optional[str] = Field(default=None, description="End time in ISO format (e.g., '2025-11-12T15:00:00') or duration description (e.g., '1 hour'). If not provided, defaults to 1 hour after start_time.")
    attendees: Optional[str] = Field(default=None, description="Comma-separated list of email addresses (optional)")
    description: Optional[str] = Field(default=None, description="Event description (optional)")
    location: Optional[str] = Field(default=None, description="Event location (optional)")

def _create_calendar_event_func(summary: str, start_time: str, end_time: Optional[str] = None,
                         attendees: Optional[str] = None,
                         description: Optional[str] = None,
                         location: Optional[str] = None) -> str:
    """
    Create a calendar event.
    
    Args:
        summary: Event title/summary
        start_time: Start time in ISO format (e.g., "2025-11-12T14:00:00") or natural language (e.g., "tomorrow at 2 PM")
        end_time: End time in ISO format (e.g., "2025-11-12T15:00:00") or duration description (e.g., "1 hour")
        attendees: Comma-separated list of email addresses (optional)
        description: Event description (optional)
        location: Event location (optional)
    
    Returns:
        Confirmation message with event details or link
    """
    try:
        calendar_agent = get_calendar_agent()
        
        # Handle end_time: if not provided or is a duration, calculate end time
        from datetime import timedelta
        import dateparser
        
        # Parse start_time
        parsed_start = dateparser.parse(start_time)
        if not parsed_start:
            return f"Error: Could not parse start_time: {start_time}"
        
        # Determine end_time
        if not end_time:
            # Default to 1 hour after start
            parsed_end = parsed_start + timedelta(hours=1)
        elif "hour" in end_time.lower() or "minute" in end_time.lower():
            # Duration format (e.g., "1 hour", "30 minutes")
            import re
            duration_match = re.search(r'(\d+(?:\.\d+)?)', end_time)
            if duration_match:
                duration_value = float(duration_match.group(1))
                if "hour" in end_time.lower():
                    parsed_end = parsed_start + timedelta(hours=duration_value)
                else:  # minutes
                    parsed_end = parsed_start + timedelta(minutes=duration_value)
            else:
                parsed_end = parsed_start + timedelta(hours=1)
        else:
            # ISO format or other date format
            parsed_end = dateparser.parse(end_time, settings={'RELATIVE_BASE': parsed_start})
            if not parsed_end:
                # If parsing fails, default to 1 hour after start
                parsed_end = parsed_start + timedelta(hours=1)
        
        # Convert to ISO format strings
        start_time_iso = parsed_start.isoformat()
        end_time_iso = parsed_end.isoformat()
        
        attendee_list = None
        if attendees:
            attendee_list = [email.strip() for email in attendees.split(",")]
        
        # Use direct API call instead of agent executor (more reliable)
        # Initialize calendar agent service if needed
        calendar_agent._initialize()
        if not calendar_agent.service:
            # Try to get service
            try:
                service = calendar_agent._get_service()
            except Exception as service_error:
                return f"Error: Calendar service not available. {str(service_error)}"
        else:
            service = calendar_agent.service
        
        # Create event directly using Google Calendar API
        try:
            event = {
                'summary': summary,
                'start': {'dateTime': start_time_iso, 'timeZone': 'UTC'},
                'end': {'dateTime': end_time_iso, 'timeZone': 'UTC'},
            }
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            if attendee_list:
                event['attendees'] = [{'email': email} for email in attendee_list]
            
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            html_link = created_event.get('htmlLink', '')
            return f"✅ Calendar event created successfully! {html_link}"
        except Exception as api_error:
            # If direct API call fails, try agent executor as fallback
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            calendar_agent.create_event(
                                summary, start_time_iso, end_time_iso,
                                attendees=attendee_list,
                                description=description,
                                location=location
                            )
                        )
                        result = future.result(timeout=60)
                else:
                    result = loop.run_until_complete(
                        calendar_agent.create_event(
                            summary, start_time_iso, end_time_iso,
                            attendees=attendee_list,
                            description=description,
                            location=location
                        )
                    )
                return result
            except Exception as agent_error:
                return f"Error creating calendar event: Direct API call failed ({str(api_error)}), Agent executor also failed ({str(agent_error)})"
    except Exception as e:
        return f"Error creating calendar event: {str(e)}"

# Create a custom tool class that handles JSON string parsing
class CreateCalendarEventTool(StructuredTool):
    """Custom tool that handles JSON string input from agent executor."""
    
    def _parse_input(self, tool_input):
        """Override _parse_input to handle dict and JSON string inputs."""
        # If tool_input is already a dict with the right keys, validate it directly
        if isinstance(tool_input, dict):
            # Check if it has the schema fields
            if 'summary' in tool_input or 'start_time' in tool_input:
                # Validate against schema
                try:
                    return self.args_schema(**tool_input).dict()
                except Exception:
                    pass
        
        # If tool_input is a JSON string, parse it first
        if isinstance(tool_input, str):
            if tool_input.strip().startswith('{'):
                try:
                    parsed = json.loads(tool_input)
                    if isinstance(parsed, dict):
                        # Validate against schema
                        try:
                            return self.args_schema(**parsed).dict()
                        except Exception:
                            pass
                except json.JSONDecodeError:
                    pass
        
        # Fall back to parent's parsing
        return super()._parse_input(tool_input)

create_calendar_event = CreateCalendarEventTool.from_function(
    func=_create_calendar_event_func,
    name="create_calendar_event",
    description="Create a calendar event. Args: summary (event title), start_time (ISO format or natural language), end_time (ISO format or duration, optional - defaults to 1 hour), attendees (optional comma-separated emails), description (optional), location (optional)",
    args_schema=CreateCalendarEventSchema
)

class ListCalendarEventsSchema(BaseModel):
    max_results: int = Field(default=10, description="Maximum number of events to return")
    time_min: Optional[str] = Field(default=None, description="Lower bound for event end time in ISO format")
    time_max: Optional[str] = Field(default=None, description="Upper bound for event start time in ISO format")

def _list_calendar_events_func(max_results: int = 10, time_min: Optional[str] = None,
                        time_max: Optional[str] = None) -> str:
    """
    List calendar events.
    
    Args:
        max_results: Maximum number of events to return (default: 10)
        time_min: Lower bound for event end time in ISO format (optional)
        time_max: Upper bound for event start time in ISO format (optional)
    
    Returns:
        List of calendar events with their details
    """
    try:
        calendar_agent = get_calendar_agent()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        calendar_agent.list_events(time_min=time_min, time_max=time_max, max_results=max_results)
                    )
                    result = future.result(timeout=60)
            else:
                result = loop.run_until_complete(
                    calendar_agent.list_events(time_min=time_min, time_max=time_max, max_results=max_results)
                )
        except RuntimeError:
            result = asyncio.run(
                calendar_agent.list_events(time_min=time_min, time_max=time_max, max_results=max_results)
            )
        return result
    except Exception as e:
        return f"Error listing calendar events: {str(e)}"

# Create custom tool class for list_calendar_events too
class ListCalendarEventsTool(StructuredTool):
    """Custom tool that handles JSON string input from agent executor."""
    
    def _parse_input(self, tool_input):
        """Override _parse_input to handle dict and JSON string inputs."""
        # If tool_input is empty dict, set defaults
        if isinstance(tool_input, dict):
            if not tool_input:
                tool_input = {"max_results": 10}
            # If it has schema fields, validate it directly
            if 'max_results' in tool_input or 'time_min' in tool_input or 'time_max' in tool_input:
                try:
                    return self.args_schema(**tool_input).dict()
                except Exception:
                    pass
        
        # If tool_input is a JSON string, parse it first
        if isinstance(tool_input, str):
            if tool_input.strip().startswith('{'):
                try:
                    parsed = json.loads(tool_input)
                    if isinstance(parsed, dict):
                        # Handle empty dict
                        if not parsed:
                            parsed = {"max_results": 10}
                        try:
                            return self.args_schema(**parsed).dict()
                        except Exception:
                            pass
                except json.JSONDecodeError:
                    pass
        
        # Fall back to parent's parsing
        return super()._parse_input(tool_input)

list_calendar_events = ListCalendarEventsTool.from_function(
    func=_list_calendar_events_func,
    name="list_calendar_events",
    description="List calendar events. Args: max_results (default 10), time_min (optional ISO format), time_max (optional ISO format)",
    args_schema=ListCalendarEventsSchema
)

# ---------------------------------------------- #
tools = [
    get_table_schema, 
    query_bigquery, 
    list_tables,
    get_customer_summary,
    get_current_time,
    send_email,
    create_calendar_event,
    list_calendar_events
]

# AgentState is no longer needed with AgentExecutor approach

def create_crm_agent():
    """Create and configure the CRM agent using ReAct pattern (compatible with Vertex AI)"""
    
    # Initialize Vertex AI LLM
    try:
        llm = ChatVertexAI(
            # --- UPDATED: Reads from the imported Config ---
            model_name=Config.VERTEX_AI_MODEL,
            location=Config.VERTEX_LOCATION,
            temperature=0,
            max_tokens=2048,
            project=Config.BQ_PROJECT_ID,
        )
    except Exception as e:
        raise Exception(f"Failed to initialize Vertex AI LLM: {str(e)}. Check GCP credentials and project configuration.")
    
    # Create system prompt with tool descriptions
    system_prompt = SYSTEM_GUIDELINES
    
    # Create ReAct prompt template (compatible with Vertex AI)
    from langchain_core.prompts import PromptTemplate
    
    prompt_template = f"""{system_prompt}

You have access to the following tools:

{{tools}}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{{tool_names}}]
Action Input: the input to the action (must be valid JSON with correct parameter names)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {{input}}
Thought:{{agent_scratchpad}}"""
    
    prompt = PromptTemplate.from_template(prompt_template)
    
    # Use create_react_agent (works with Vertex AI, unlike bind_tools)
    from langchain.agents import create_react_agent, AgentExecutor
    
    agent = create_react_agent(llm, tools, prompt)
    
    # Create agent executor with better error handling
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=lambda e: f"Error parsing tool input: {e}. Please try again with correct format.",
        max_iterations=10,
        return_intermediate_steps=True,  # Enable intermediate steps for thinking process
    )
    
    return agent_executor


def initialize_agent(
    model_name: str = None,
    # vertex_project: str = None, # This was commented out, correct
    vertex_location: str = None,
    bq_project_id: str = None,
    bq_dataset_id: str = None,
    bq_credentials_path: str = None
):
    """
    Initialize the CRM agent with custom configuration
    
    Args:
        model_name: Vertex AI model name
        vertex_location: Vertex AI location/region
        bq_project_id: BigQuery project ID
        bq_dataset_id: BigQuery dataset ID
        bq_credentials_path: Path to service account credentials
    """
    global _agent
    
    # --- UPDATED: Update the *shared* Config object ---
    if model_name:
        Config.VERTEX_AI_MODEL = model_name
    if vertex_location:
        Config.VERTEX_LOCATION = vertex_location
    if bq_project_id:
        Config.BQ_PROJECT_ID = bq_project_id
    if bq_dataset_id:
        # Ensure dataset name is uppercase (BigQuery is case-sensitive)
        Config.BQ_DATASET_ID = bq_dataset_id.upper()
    # if bq_credentials_path:
    #     Config.BQ_CREDENTIALS_PATH = bq_credentials_path
    
    # --- UPDATED: Create and INJECT the client into agent_tools ---
    bq_client = get_bigquery_client()
    set_bigquery_client(bq_client)
    
    # Create agent
    _agent = create_crm_agent()
    
    print(f"✓ CRM Agent initialized")
    print(f"  Model: {Config.VERTEX_AI_MODEL}")
    # --- UPDATED: Reads from the shared Config ---
    print(f"  BQ Dataset: {Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}")
    
    return _agent


def chat(message: str, conversation_history: list = None) -> dict:
    """
    Message the CRM Agent and get the response.
    Args:
        message (str): User's message
        conversation_history [Optional](list): List of the previous messages (HumanMessage/AIMessage)
        
    Returns:
        Dictionary with response and updated history
    """
    global _agent
    
    if _agent is None:
        # --- UPDATED: Pass runtime env vars to init ---
        # This ensures env vars are read if provided
        initialize_agent(
            model_name=os.getenv("VERTEX_AI_MODEL", Config.VERTEX_AI_MODEL),
            vertex_location=os.getenv("VERTEX_AI_LOCATION", Config.VERTEX_LOCATION),
            bq_project_id=os.getenv("BQ_PROJECT_ID"),
            bq_dataset_id=os.getenv("BQ_DATASET_ID"),
            bq_credentials_path=os.getenv("BQ_CREDENTIALS_PATH")
        )
    
    # AgentExecutor uses a different interface - it takes {"input": message}
    # We need to incorporate conversation history into the input
    input_text = message
    
    # If there's conversation history, prepend it to provide context
    if conversation_history:
        history_text = ""
        for msg in conversation_history:
            if hasattr(msg, "content"):
                role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                history_text += f"{role}: {msg.content}\n"
        input_text = f"{history_text}\nUser: {message}"
    
    # Run agent executor with better error handling
    # Capture intermediate steps for thinking process
    thinking_steps = []
    
    try:
        # Use stream_events or capture intermediate steps
        # AgentExecutor returns {"output": "...", "intermediate_steps": [...]}
        result = _agent.invoke({"input": input_text}, return_only_outputs=False)
    except RuntimeError as e:
        # Handle StopIteration errors (common with LangChain agents)
        if "StopIteration" in str(e) or "generator raised StopIteration" in str(e):
            # Try to extract useful error info
            error_msg = str(e)
            if "StopIteration" in error_msg:
                raise Exception(
                    "Agent encountered an error while processing your request. "
                    "This may be due to a tool parsing issue. Please try rephrasing your request."
                )
        raise Exception(f"Agent invoke failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Agent invoke failed: {str(e)}")
    
    # Extract response - AgentExecutor returns {"output": "...", "intermediate_steps": [...]}
    if not result:
        raise Exception("Agent returned empty result")
    
    response_text = result.get("output", "No response generated")
    intermediate_steps = result.get("intermediate_steps", [])
    
    # Parse intermediate steps to extract thinking process
    from langchain_core.agents import AgentAction, AgentFinish
    
    for step in intermediate_steps:
        if isinstance(step, tuple) and len(step) >= 2:
            agent_action = step[0]
            observation = step[1]
            
            # Extract tool name and input from agent_action
            if isinstance(agent_action, AgentAction):
                tool_name = agent_action.tool if hasattr(agent_action, "tool") else "Unknown"
                tool_input = agent_action.tool_input if hasattr(agent_action, "tool_input") else {}
                log = agent_action.log if hasattr(agent_action, "log") else ""
            else:
                # Fallback for other types
                tool_name = getattr(agent_action, "tool", "Unknown")
                tool_input = getattr(agent_action, "tool_input", {})
                log = getattr(agent_action, "log", "")
            
            # Format tool input as JSON string
            import json
            try:
                tool_input_str = json.dumps(tool_input, indent=2) if tool_input else ""
            except:
                tool_input_str = str(tool_input) if tool_input else ""
            
            # Extract observation
            observation_str = str(observation) if observation else ""
            
            # Extract thought from log or construct from context
            thought = log if log else f"Using {tool_name} to process the request"
            
            # Clean up thought - remove redundant prefixes
            if thought.startswith("Action:"):
                thought = thought.replace("Action:", "").strip()
            
            thinking_steps.append({
                "thought": thought[:500],  # Limit thought length
                "action": tool_name,
                "action_input": tool_input_str[:1000],  # Limit input length
                "observation": observation_str[:1000]  # Limit observation length
            })
    
    # Build history for return (convert to message format)
    history = conversation_history or []
    history.append(HumanMessage(content=message))
    history.append(AIMessage(content=response_text))
    
    return {
        "response": response_text,
        "history": history,
        "thinking_steps": thinking_steps
    }


if __name__ == "__main__":
    print("=" * 60)
    print("CRM Agent with BigQuery & Vertex AI")
    print("=" * 60)
    print()
    
    # Initialize agent
    initialize_agent(
        model_name="gemini-2.5-flash", # Note: your file had gemini-2.5-flash, but Config default is 1.5. Make sure this is what you want.
        vertex_location=os.getenv("VERTEX_AI_LOCATION"), # Added this
        bq_project_id=os.getenv("BQ_PROJECT_ID"),
        bq_dataset_id=os.getenv("BQ_DATASET_ID"),
    )
    
    print()
    print("=" * 60)
    print("Interactive Chat (type 'quit' to exit)")
    print("=" * 60)
    print()
    
    conversation_history = []
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            # --- UPDATED: No history needed, chat function handles it ---
            result = chat(user_input, conversation_history)
            conversation_history = result["history"]
            
            print(f"\nAgent: {result['response']}\n")
            
        except Exception as e:
            print(f"\nError: {str(e)}\n")
            import traceback
            traceback.print_exc()

    # Example programmatic usage
    print("\n" + "=" * 60)
    print("Example Queries:")
    print("=" * 60)
    
    examples = [
        "What time is it now?",
        "What tables are available?",
        "Show me the schema of the customers table",
        "How many customers do we have?",
        "Show me the first 5 customers"
    ]
    
    for example in examples:
        print(f"\nQ: {example}")
        result = chat(example)
        print(f"A: {result['response']}")
        print("-" * 60)