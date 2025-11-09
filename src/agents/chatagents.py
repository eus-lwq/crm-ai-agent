"""
CRM "SQL Chef" Agent with BigQuery Integration using Vertex AI
Built with LangChain and LangGraph from scratch
"""

# ---------------------------------------------- #
from typing import TypedDict, Annotated, Sequence, Union, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.agents import AgentAction, AgentFinish
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import tool, BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
import json
import os

from agent_tools import (
    Config, 
    # BigQueryTools,
    list_tables, 
    get_table_schema,
    query_bigquery,
    get_customer_summary,
    get_bigquery_client,  
    set_bigquery_client,
    delegate_sql_task,
    get_current_time, 
    set_sql_agent
)

from prompts import WAITER_AGENT_PROMPT, SQL_AGENT_PROMPT
# ---------------------------------------------- #
sql_tools = [list_tables, get_table_schema, query_bigquery, get_customer_summary]
# def create_sql_agent(tools_list: List[BaseTool]):
def create_sql_agent():
    """
    Builds and compiles the specialist SQL agent.
    Takes a list of tools as an argument.
    """
    
    llm = ChatVertexAI(
        model_name=Config.VERTEX_AI_MODEL,
        location=Config.VERTEX_LOCATION,
        temperature=0
    )
    
    # Bind the provided SQL tools to this agent
    llm_with_tools = llm.bind_tools(sql_tools)

    def call_model(state):
        messages = state["messages"]
        system_prompt = SystemMessage(content=SQL_AGENT_PROMPT)
        response = llm_with_tools.invoke([system_prompt] + messages)
        return {"messages": [response]}

    def should_continue(state):
        if state["messages"][-1].tool_calls:
            return "tools"
        return END

    # Define the graph for the SQL agent
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(sql_tools)) # Use the provided tools
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "agent")
    
    print("--- [SQL_AGENT] Compiled successfully. ---")
    return workflow.compile()

class AgentState(TypedDict):
    """State of the agent conversation"""
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Add more states if needed for our agent

chat_tools = [get_current_time, delegate_sql_task]
def create_chat_agent():
    """Builds and compiles the main, user-facing agent."""
    
    llm = ChatVertexAI(
        model_name="gemini-2.5-flash", # Note: this is different from Config.VERTEX_AI_MODEL
        location=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
        temperature=0.1
    )
    llm_with_tools = llm.bind_tools(chat_tools)

    def call_model(state):
        messages = state["messages"]
        system_prompt = SystemMessage(content=WAITER_AGENT_PROMPT)
        response = llm_with_tools.invoke([system_prompt] + messages)
        return {"messages": [response]}

    def should_continue(state):
        if state["messages"][-1].tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(chat_tools))
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    print("--- [CHAT_AGENT] Compiled successfully. ---")
    return workflow.compile()

# ================== TEST CALLS =========================
if __name__ == "__main__":
    print("=" * 60)
    print("CRM Hierarchical Agent (ChatAgent + SQLAgent)")
    print("=" * 60)
    
    # --- ADD THIS ENTIRE BLOCK ---
    # 1. INITIALIZE BIGQUERY CLIENT
    print("--- [MAIN] Initializing BigQuery client... ---")
    try:
        # Get the client instance
        bq_client_instance = get_bigquery_client()
        # Inject it into the tools module for all SQL tools to use
        set_bigquery_client(bq_client_instance)
        print("--- [MAIN] BigQuery client initialized successfully. ---")
    except Exception as e:
        print(f"--- [MAIN] FATAL ERROR: Could not initialize BigQuery client: {e} ---")
        print("Please check BQ_PROJECT_ID and authentication.")
        exit() # Exit if we can't connect to BQ
    # --- END OF NEW BLOCK ---
    
    # 2. Create SQL Agent and pass it the tools
    print("--- [MAIN] Compiling SQLAgent... ---")
    sql_agent = create_sql_agent()
    
    # 3. INJECT SQL AGENT (for delegate_sql_task)
    set_sql_agent(sql_agent) 
    
    # 4. Create Chat Agent
    print("--- [MAIN] Compiling ChatAgent... ---")
    chat_agent_app = create_chat_agent()
    
    print("\n--- [MAIN] All agents created. Ready for chat. ---\n")
    conversation_history = []
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        # Add human message to history
        conversation_history.append(HumanMessage(content=user_input))
        
        # Run the agent
        try:
            # We must use the AgentState class for the input
            result = chat_agent_app.invoke({"messages": conversation_history})
            # Add AI response to history
            response_message = result["messages"][-1]
            conversation_history.append(response_message)
            
            print(f"\nAgent: {response_message.content}\n")
            
        except Exception as e:
            print(f"\nError: {str(e)}\n")
            import traceback
            traceback.print_exc()