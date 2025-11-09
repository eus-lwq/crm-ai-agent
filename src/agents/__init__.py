"""Agents package - CRM chat agent, calendar agent, and gmail agent."""
# Use relative imports to avoid path issues
try:
    from .chatagent import create_crm_agent, initialize_agent, chat
except ImportError:
    # Fallback for when langgraph is not available
    create_crm_agent = None
    initialize_agent = None
    chat = None

from .calendar_agent import CalendarAgent
from .gmail_agent import GmailAgent

__all__ = [
    "create_crm_agent",
    "initialize_agent", 
    "chat",
    "CalendarAgent",
    "GmailAgent"
]

