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
    # Vertex AI Settings
    VERTEX_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    VERTEX_AI_MODEL= os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash")

    # BigQuery Settings
    BQ_PROJECT_ID = os.getenv("BQ_PROJECT_ID", 'ai-hackathon-477617')
    # Ensure dataset name is uppercase (BigQuery is case-sensitive)
    _dataset = os.getenv("BQ_DATASET_ID", 'CRM_DATA')
    BQ_DATASET_ID = _dataset.upper() if _dataset else 'CRM_DATA'
    BQ_CREDENTIALS_PATH = os.getenv("BQ_CREDENTIALS_PATH", None)

# Global BigQuery client
bq_client = None

def set_bigquery_client(client: bigquery.Client):
    """Sets the global BigQuery client for all tools in this module."""
    global bq_client
    bq_client = client

def get_bigquery_client():
    """Initialize and return BigQuery client"""
    # Check for service account path in environment or config
    service_account_path = (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or 
        Config.BQ_CREDENTIALS_PATH or
        os.getenv("GCP_SERVICE_ACCOUNT_PATH")
    )
    
    # Also check for service account in current directory
    if not service_account_path and os.path.exists("gcp-service-account.json"):
        service_account_path = os.path.abspath("gcp-service-account.json")
        print(f"📁 Found service account file: {service_account_path}")
    
    if service_account_path and os.path.exists(service_account_path):
        print(f"🔑 Using service account: {service_account_path}")
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path
        )
        return bigquery.Client(
            credentials=credentials,
            project=Config.BQ_PROJECT_ID
        )
    else:
        # Use Application Default Credentials (from gcloud auth application-default login)
        print(f"🔑 Using Application Default Credentials for project: {Config.BQ_PROJECT_ID}")
        print(f"   (Run 'gcloud auth application-default login' if you get authentication errors)")
        return bigquery.Client(project=Config.BQ_PROJECT_ID)

@tool
def list_tables(dummy: str = "") -> str:
    """
    List all tables available in the CRM BigQuery dataset.
    Use this to discover what data is available.
    
    Args:
        dummy: Optional parameter (ignored, can be empty string)
    
    Returns:
        JSON string with list of tables and their details
    """
    if bq_client is None:
        return json.dumps({"error": "BigQuery client not initialized."})
    try:
        # Since INFORMATION_SCHEMA requires special permissions, just return the known table
        # The frontend successfully queries the deals table, so we know it exists
        project_id = Config.BQ_PROJECT_ID
        dataset_id = Config.BQ_DATASET_ID
        
        # Return the known table (frontend confirms it exists and is accessible)
        table_list = [{"table_name": "deals", "num_rows": 0, "size_mb": 0}]
        
        # Try to get actual row count by querying (if we have permission)
        try:
            count_query = f"SELECT COUNT(*) as row_count FROM `{project_id}.{dataset_id}.deals`"
            count_job = bq_client.query(count_query)
            count_result = count_job.result()
            for row in count_result:
                if hasattr(row, 'row_count'):
                    table_list[0]["num_rows"] = row.row_count
                break
        except Exception:
            # If count query fails, just return 0 (table still exists)
            pass
        
        return json.dumps({
            "dataset": dataset_id,
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
        table_name: Name of the table to inspect (e.g., "deals")
        
    Returns:
        JSON string with column names, types, and descriptions
    """
    if bq_client is None:
        return json.dumps({"error": "BigQuery client not initialized."})
    try:
        # Normalize table name (remove quotes, handle JSON strings)
        if isinstance(table_name, str):
            # Remove JSON wrapper if present
            table_name = table_name.strip().strip('"').strip("'")
            # Handle if it's a JSON string like '{"table_name": "deals"}'
            if table_name.startswith('{') and 'table_name' in table_name:
                import re
                match = re.search(r'"table_name"\s*:\s*"([^"]+)"', table_name)
                if match:
                    table_name = match.group(1)
        
        # Use the same approach as frontend - construct full table ID
        project_id = Config.BQ_PROJECT_ID
        dataset_id = Config.BQ_DATASET_ID
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        
        # Get table schema using the same method as frontend
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
            "table_id": table_ref,
            "num_rows": table.num_rows if hasattr(table, 'num_rows') else 0,
            "columns": columns
        }, indent=2)
    
    except Exception as e:
        error_msg = str(e)
        # Provide helpful error message
        if "not found" in error_msg.lower() or "404" in error_msg:
            return json.dumps({
                "error": f"Table '{table_name}' not found in {Config.BQ_PROJECT_ID}.{Config.BQ_DATASET_ID}",
                "suggestion": "Use list_tables to see available tables"
            })
        return json.dumps({"error": error_msg})

@tool
def query_bigquery(sql_query: str) -> str:
    """
    Execute a SQL query against BigQuery to retrieve CRM data.
    Always add LIMIT clause to prevent large result sets.
    Use the same table path format as the frontend: ai-hackathon-477617.CRM_DATA.deals
    
    Args:
        sql_query: SQL query to execute (must be SELECT only)
                  Example: "SELECT * FROM `ai-hackathon-477617.CRM_DATA.deals` LIMIT 10"
                  Can also be a JSON string like '{"sql_query": "SELECT ..."}'
        
    Returns:
        JSON string with query results
    """
    if bq_client is None:
        return json.dumps({"error": "BigQuery client not initialized."})
    try:
        # Debug: log the input type and first 200 chars
        input_type = type(sql_query).__name__
        input_preview = str(sql_query)[:200] if isinstance(sql_query, str) else str(sql_query)[:200]
        
        # Handle different input formats from agent executor
        # LangChain tools can receive input as dict or string
        if isinstance(sql_query, dict):
            # Direct dict input (from StructuredTool)
            sql_query = sql_query.get('sql_query', '')
        elif isinstance(sql_query, str):
            sql_query = sql_query.strip()
            # Handle JSON string format: '{"sql_query": "SELECT ..."}'
            if sql_query.startswith('{') and 'sql_query' in sql_query:
                try:
                    import json as json_lib
                    parsed = json_lib.loads(sql_query)
                    if isinstance(parsed, dict) and 'sql_query' in parsed:
                        sql_query = parsed['sql_query']
                except (json_lib.JSONDecodeError, ValueError):
                    # If JSON parsing fails, try simple regex extraction
                    import re
                    # Extract SQL from: "sql_query": "SELECT ..."
                    # Handle escaped quotes and backticks
                    match = re.search(r'"sql_query"\s*:\s*"((?:[^"\\]|\\.)*)"', sql_query, re.DOTALL)
                    if not match:
                        # Try with single quotes
                        match = re.search(r"'sql_query'\s*:\s*'((?:[^'\\]|\\.)*)'", sql_query, re.DOTALL)
                    if match:
                        sql_query = match.group(1).replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n').replace('\\\\', '\\')
        
        # Ensure we have a string
        if not isinstance(sql_query, str):
            sql_query = str(sql_query)
        
        # Security: Only allow SELECT queries
        sql_query_clean = sql_query.strip()
        sql_query_upper = sql_query_clean.upper()
        
        # Check if it's a SELECT query (allow SELECT with any case)
        if not sql_query_upper.startswith("SELECT"):
            return json.dumps({
                "error": "Only SELECT queries are allowed",
                "received_type": input_type,
                "received_preview": input_preview,
                "extracted_query": sql_query_clean[:100] if sql_query_clean else "empty"
            })
        
        # Ensure table references use the correct format
        project_id = Config.BQ_PROJECT_ID
        dataset_id = Config.BQ_DATASET_ID
        
        # If query doesn't specify full table path, help construct it
        if f"{project_id}.{dataset_id}" not in sql_query_clean:
            # Try to find table name and construct full path
            import re
            # Look for FROM clause (case insensitive)
            from_match = re.search(r'FROM\s+[`"]?(\w+)[`"]?', sql_query_upper)
            if from_match:
                table_name = from_match.group(1).lower()
                # Replace with full path (preserve original case in FROM)
                sql_query_clean = re.sub(
                    r'FROM\s+[`"]?\w+[`"]?',
                    f'FROM `{project_id}.{dataset_id}.{table_name}`',
                    sql_query_clean,
                    flags=re.IGNORECASE
                )
        
        # Add automatic LIMIT if not present
        if "LIMIT" not in sql_query_upper:
            sql_query_clean = f"{sql_query_clean.rstrip(';')} LIMIT 100"
        
        # Execute query using the same method as frontend
        query_job = bq_client.query(sql_query_clean)
        results = query_job.result()
        
        # Convert to list of dicts (same format as frontend)
        rows = []
        for row in results:
            row_dict = {}
            for key, value in row.items():
                # Handle different data types
                if value is None:
                    row_dict[key] = None
                elif hasattr(value, 'isoformat'):  # datetime/date objects
                    row_dict[key] = value.isoformat()
                else:
                    row_dict[key] = value
            rows.append(row_dict)
        
        return json.dumps({
            "query": sql_query_clean,
            "row_count": len(rows),
            "data": rows
        }, indent=2, default=str)
    
    except Exception as e:
        error_msg = str(e)
        return json.dumps({
            "error": error_msg,
            "query": sql_query[:200] if isinstance(sql_query, str) else str(sql_query)[:200],
            "suggestion": "Make sure table names use format: project.dataset.table (e.g., ai-hackathon-477617.CRM_DATA.deals)"
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
def get_current_time(dummy: str = "") -> str:
    """
    Get the current date and time.
    
    Args:
        dummy: Optional parameter (ignored, can be empty string)
    
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