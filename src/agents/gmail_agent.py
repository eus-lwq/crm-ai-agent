"""Gmail agent using LangChain GmailToolkit and agent executor."""
import os
from typing import Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_community import GmailToolkit
from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import settings

# Set up GCP credentials if service account path is provided
if settings.gcp_service_account_path and os.path.exists(settings.gcp_service_account_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.gcp_service_account_path


class GmailAgent:
    """
    Gmail agent using LangChain's GmailToolkit.
    
    This uses OAuth 2.0 flow with credentials.json and token.json files.
    On first run, it will open a browser for authorization.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize Gmail agent.
        
        Args:
            credentials_path: Path to credentials.json (default: looks for 'credentials.json' in current dir)
            token_path: Path to token.json (default: looks for 'token.json' in current dir)
        """
        self.credentials_path = credentials_path or "credentials.json"
        self.token_path = token_path or "token.json"
        self.toolkit = None
        self.agent_executor = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of toolkit and agent."""
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
            
            # Check if token exists and validate it
            if os.path.exists(self.token_path):
                try:
                    from google.oauth2.credentials import Credentials
                    from google.auth.transport.requests import Request
                    import json
                    
                    # Try to load and validate the token
                    with open(self.token_path, 'r') as f:
                        token_data = json.load(f)
                    
                    # Check if token is expired
                    from datetime import datetime, timezone
                    if 'expiry' in token_data:
                        expiry = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                        if expiry < datetime.now(timezone.utc):
                            print(f"⚠️  Token expired on {expiry}. Deleting to force re-authentication...")
                            os.remove(self.token_path)
                        else:
                            # Try to refresh if needed
                            try:
                                creds = Credentials.from_authorized_user_file(self.token_path)
                                if creds.expired and creds.refresh_token:
                                    print("🔄 Refreshing expired token...")
                                    creds.refresh(Request())
                                    # Save refreshed token
                                    with open(self.token_path, 'w') as token:
                                        token.write(creds.to_json())
                                    print("✅ Token refreshed successfully!")
                            except Exception as refresh_error:
                                print(f"⚠️  Could not refresh token: {refresh_error}")
                                print("   Deleting token to force re-authentication...")
                                os.remove(self.token_path)
                except Exception as token_error:
                    print(f"⚠️  Error validating token: {token_error}")
                    print("   Deleting token to force re-authentication...")
                    if os.path.exists(self.token_path):
                        os.remove(self.token_path)
            
            # Initialize the Gmail Toolkit
            # It will look for 'credentials.json' in the specified path
            # On first run, it will open a browser for you to authorize
            # This will create a 'token.json' file for future runs
            self.toolkit = GmailToolkit(credentials_path=self.credentials_path)
            
            # Get the tools from the toolkit
            tools = self.toolkit.get_tools()
            
            # Define the prompt for the ReAct agent
            prompt_template = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

IMPORTANT: When using send_gmail_message tool, use these exact parameter names:
- "to": recipient email address (string or list of strings)
- "subject": email subject (string)
- "message": email body text (string)
- "cc": optional CC recipients (string or list of strings)
- "bcc": optional BCC recipients (string or list of strings)

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
                    "The Gmail agent uses Vertex AI for the agent executor."
                )
            
            # Create the ReAct agent
            agent = create_react_agent(llm, tools, prompt)
            
            # Create the agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
            )
            
            self._initialized = True
            
        except Exception as e:
            print(f"Warning: Could not initialize Gmail agent: {e}")
            self.toolkit = None
            self.agent_executor = None
            self._initialized = True
    
    async def send_email(self, to: str, subject: str, body: str) -> str:
        """
        Send an email using the Gmail agent.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            Agent's response/output
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception(
                "Gmail agent not available. Make sure credentials.json exists and "
                "you've completed the OAuth flow (token.json should be created)."
            )
        
        try:
            # Try calling the tool directly first (more reliable)
            tools = self.toolkit.get_tools()
            send_tool = [t for t in tools if 'send' in t.name.lower()][0]
            
            # Call the tool directly with proper format
            try:
                result = send_tool.invoke({
                    "to": to,
                    "subject": subject,
                    "message": body
                })
                return f"Email sent successfully. {result}"
            except Exception as direct_error:
                # Fall back to agent if direct call fails
                print(f"Direct tool call failed, trying agent: {direct_error}")
                prompt = f"Send an email to {to} with the subject '{subject}' and the body '{body}'. Use the send_gmail_message tool with to='{to}', subject='{subject}', message='{body}'."
                
                response = self.agent_executor.invoke({"input": prompt})
                return response.get("output", "Email sent successfully")
            
        except Exception as e:
            raise Exception(f"Error sending email via agent: {e}")
    
    async def search_emails(self, query: str, max_results: int = 10) -> str:
        """
        Search emails using the Gmail agent.
        
        Args:
            query: Search query (e.g., "from:example@gmail.com", "subject:meeting")
            max_results: Maximum number of results
            
        Returns:
            Agent's response with email search results
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception("Gmail agent not available")
        
        try:
            prompt = f"Search for emails matching '{query}' and return up to {max_results} results"
            response = self.agent_executor.invoke({"input": prompt})
            return response.get("output", "No results found")
            
        except Exception as e:
            raise Exception(f"Error searching emails: {e}")
    
    async def get_email(self, message_id: str) -> str:
        """
        Get a specific email by message ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Email content
        """
        self._initialize()
        
        if not self.agent_executor:
            raise Exception("Gmail agent not available")
        
        try:
            # Try using the tool directly first (more reliable and handles encoding better)
            tools = self.toolkit.get_tools()
            get_tool = [t for t in tools if 'get' in t.name.lower() and 'message' in t.name.lower()][0]
            
            try:
                result = get_tool.invoke({"message_id": message_id})
                return str(result)
            except UnicodeDecodeError as decode_error:
                # If encoding error, try with agent as fallback
                print(f"Warning: Encoding error when retrieving email directly: {decode_error}")
                print("Falling back to agent executor...")
                prompt = f"Get the email with message ID {message_id}"
                response = self.agent_executor.invoke({"input": prompt})
                return response.get("output", "Email not found")
            
        except Exception as e:
            raise Exception(f"Error getting email: {e}")

