"""
CRM Agent with BigQuery Integration using Vertex AI
Built with LangChain and LangGraph from scratch
"""

# ---------------------------------------------- #
from typing import Annotated, TypedDict, Sequence
from datetime import datetime

from google.oauth2 import service_account
from google.cloud import bigquery

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.agents import AgentAction, AgentFinish
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import tool

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

import operator
import json
import os

from agent_tools import *
from prompts import SYSTEM_GUIDELINES
# ---------------------------------------------- #
# NOTE: GLOBAL for the momentDefine tools list
tools = [get_table_schema, query_bigquery, list_tables]

class Config:
    """Configuration for the CRM Agent"""
    # Vertex AI Settings
    VERTEX_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    VERTEX_AI_MODEL= os.getenv("VERTEX_AI_MODEL", "ggemini-1.5-flash")
    
    # BigQuery Settings
    # BQ_PROJECT_ID = os.getenv("BQ_PROJECT_ID", "your-project-id")
    # BQ_DATASET_ID = os.getenv("BQ_DATASET_ID", "your-dataset-id")
    # BQ_CREDENTIALS_PATH = os.getenv("BQ_CREDENTIALS_PATH", None)

class AgentState(TypedDict):
    """State of the agent conversation"""
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Add more states if needed for our agent

def create_crm_agent():
    """Create and configure the CRM agent"""
    
    # Initialize Vertex AI LLM
    llm = ChatVertexAI(
        model_name=Config.VERTEX_AI_MODEL,
        location=Config.VERTEX_LOCATION,
        temperature=0,
        max_tokens=2048,
    )
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Create system prompt
    system_prompt = SYSTEM_GUIDELINES
    
    # Define the agent function
    def call_model(state: AgentState):
        """Call the LLM with tools"""
        messages = state["messages"]
        
        # Add system message if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + list(messages)
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Define routing logic
    def should_continue(state: AgentState):
        """Determine if we should continue or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If there are tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, end
        return END
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    
    # After tools, go back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()


def initialize_agent(
    model_name: str = None,
    vertex_location: str = None,
    bq_project_id: str = None,
    bq_dataset_id: str = None,
    bq_credentials_path: str = None
):
    """
    Initialize the CRM agent with custom configuration
    
    Args:
        model_name: Vertex AI model name (default: gemma-2-9b-it)
        vertex_project: GCP project for Vertex AI
        vertex_location: Vertex AI location/region
        bq_project_id: BigQuery project ID
        bq_dataset_id: BigQuery dataset ID
        bq_credentials_path: Path to service account credentials
    """
    global _agent, bq_client
    
    # Update configuration
    if model_name:
        Config.VERTEX_AI_MODEL = model_name
    # if vertex_project:
    #     Config.VERTEX_PROJECT = vertex_project
    if vertex_location:
        Config.VERTEX_LOCATION = vertex_location
    # if bq_project_id:
    #     Config.BQ_PROJECT_ID = bq_project_id
    # if bq_dataset_id:
    #     Config.BQ_DATASET_ID = bq_dataset_id
    # if bq_credentials_path:
    #     Config.BQ_CREDENTIALS_PATH = bq_credentials_path
    
    # Reinitialize BigQuery client if needed
    bq_client = get_bigquery_client()
    
    # Create agent
    _agent = create_crm_agent()
    
    print(f"✓ CRM Agent initialized")
    print(f"  Model: {Config.VERTEX_AI_MODEL}")
    # print(f"  BQ Dataset: {Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}")
    
    return _agent


def chat(message: str, conversation_history: list = None) -> dict:
    """
    Message the CRM Agent and get the response.
    Args:
        message (str): User's message
        conversation_history [Optional](list): List of the previous messages
        
    Returns:
        Dictionary with response and updated history
    """
    global _agent
    
    if _agent is None:
        initialize_agent()
    
    # Prepare messages
    messages = conversation_history or []
    messages.append(HumanMessage(content=message))
    
    # Run agent
    result = _agent.invoke({"messages": messages})
    
    # Extract response
    response_message = result["messages"][-1]
    response_text = response_message.content
    
    return {
        "response": response_text,
        "history": result["messages"]
    }


if __name__ == "__main__":
    print("=" * 60)
    print("CRM Agent with BigQuery & Vertex AI")
    print("=" * 60)
    print()
    
    # Initialize agent
    initialize_agent(
        model_name="gemini-1.5-flash",  # or "gemini-1.5-flash"
        # vertex_project=os.getenv("VERTEX_AI_PROJECT"),
        # bq_project_id=os.getenv("BQ_PROJECT_ID"),
        # bq_dataset_id=os.getenv("BQ_DATASET_ID"),
        # bq_credentials_path=os.getenv("BQ_CREDENTIALS_PATH")
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
    ]
    
    for example in examples:
        print(f"\nQ: {example}")
        result = chat(example)
        print(f"A: {result['response']}")
        print("-" * 60)