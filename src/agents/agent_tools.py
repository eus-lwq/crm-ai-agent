# ---------------------------------------------- #
from typing import Annotated, TypedDict, Union, Optional
from langchain_core.tools import tool
from datetime import datetime

from google.oauth2 import service_account
from google.cloud import bigquery
import json
import os
# ---------------------------------------------- #

class Config:
    '''
    Configuring CRM Agent and BigQuery Settings
    '''
    # --- NEW: Moved Vertex settings here ---
    VERTEX_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    VERTEX_AI_MODEL= os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash")

    # BigQuery Settings
    BQ_PROJECT_ID = os.getenv("BQ_PROJECT_ID", 'ai-hackathon-477617')
    BQ_DATASET_ID = os.getenv("BQ_DATASET_ID", 'CRM_DATA')
    BQ_CREDENTIALS_PATH = os.getenv("BQ_CREDENTIALS_PATH", None)


def set_bigquery_client(client: bigquery.Client):
    """Sets the global BigQuery client for all tools in this module."""
    global bq_client
    bq_client = client

def get_bigquery_client():
    """Initialize and return BigQuery client"""
    if Config.BQ_CREDENTIALS_PATH and os.path.exists(Config.BQ_CREDENTIALS_PATH):
        credentials = service_account.Credentials.from_service_account_file(
            Config.BQ_CREDENTIALS_PATH
        )
        return bigquery.Client(
            credentials=credentials,
            project=Config.BQ_PROJECT_ID
        )
    else:
        # Note: This will use default credentials if path is not found
        print(f"Initializing BQ client for project: {Config.BQ_PROJECT_ID}")
        return bigquery.Client(project=Config.BQ_PROJECT_ID)

@tool
def list_tables() -> str:
    """
    List all tables available in the CRM BigQuery dataset.
    Use this to discover what data is available.
    
    Returns:
        JSON string with list of tables and their details
    """
    # Note: No change here, but it now relies on the global bq_client
    # being set by set_bigquery_client()
    if bq_client is None:
        return json.dumps({"error": "BigQuery client not initialized."})
    try:
        tables = bq_client.list_tables(f"{Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}")
        
        table_list = []
        for table in tables:
            # Get table details
            table_ref = bq_client.get_table(f"{Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}.{table.table_id}")
            table_list.append({
                "table_name": table.table_id,
                "num_rows": table_ref.num_rows,
                "size_mb": round(table_ref.num_bytes / (1024 * 1024), 2)
            })
        
        return json.dumps({
            "dataset": Config.BQ_DATASET_ID,
            "tables": table_list,
            "count": len(table_list)
        }, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def get_table_schema(table_name: str) -> str:
    """
    Get the schema/structure of a specific BigQuery table.
    Use this to understand what columns and data types are available.
    
    Args:
        table_name: Name of the table to inspect
        
    Returns:
        JSON string with column names, types, and descriptions
    """
    if bq_client is None:
        return json.dumps({"error": "BigQuery client not initialized."})
    try:
        table_ref = f"{Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}.{table_name}"
        table = bq_client.get_table(table_ref)
        
        columns = []
        for field in table.schema:
            columns.append({
                "name": field.name,
                "type": field.field_type,
                "mode": field.mode,
                "description": field.description or "No description"
            })
        
        return json.dumps({
            "table": table_name,
            "num_rows": table.num_rows,
            "columns": columns
        }, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def query_bigquery(sql_query: str) -> str:
    """
    Execute a SQL query against BigQuery to retrieve CRM data.
    Always add LIMIT clause to prevent large result sets.
    
    Args:
        sql_query: SQL query to execute (must be SELECT only)
        
    Returns:
        JSON string with query results
    """
    if bq_client is None:
        return json.dumps({"error": "BigQuery client not initialized."})
    try:
        # Security: Only allow SELECT queries
        if not sql_query.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "Only SELECT queries are allowed"})
        
        # Add automatic LIMIT if not present
        if "LIMIT" not in sql_query.upper():
            sql_query = f"{sql_query.rstrip(';')} LIMIT 100"
        
        # Execute query
        query_job = bq_client.query(sql_query)
        results = query_job.result()
        
        # Convert to list of dicts
        rows = []
        for row in results:
            rows.append(dict(row))
        
        return json.dumps({
            "query": sql_query,
            "row_count": len(rows),
            "data": rows
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "query": sql_query
        })

@tool
def get_customer_summary(customer_id: str = None) -> str:
    """
    Get a summary of customer information. If customer_id is provided,
    returns specific customer details. Otherwise returns overall statistics.
    
    Args:
        customer_id: Optional customer ID to get specific customer info
        
    Returns:
        JSON string with customer summary
    """
    if bq_client is None:
        return json.dumps({"error": "BigQuery client not initialized."})
    try:
        if customer_id:
            # Get specific customer
            query = f"""
                SELECT *
                FROM `{Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}.customers`
                WHERE customer_id = '{customer_id}'
                LIMIT 1
            """
        else:
            # Get overall statistics
            query = f"""
                SELECT 
                    COUNT(*) as total_customers,
                    COUNT(DISTINCT status) as unique_statuses,
                    CURRENT_TIMESTAMP() as query_time
                FROM `{Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}.customers`
            """
        
        results = bq_client.query(query).result()
        rows = [dict(row) for row in results]
        
        return json.dumps({
            "customer_id": customer_id,
            "data": rows[0] if rows else {}
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def get_current_time() -> str:
    """
    Get the current date and time.
    
    Returns:
        Current timestamp as string
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if "__main__" == __name__:
    # For testing purposes
    # --- UPDATED: Set the client for testing ---
    set_bigquery_client(get_bigquery_client())
    
    # You can add test calls here
    print("Testing list_tables:")
    print(list_tables())