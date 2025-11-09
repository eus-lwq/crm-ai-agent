"""Email extractor agent that extracts structured CRM data from emails and stores in BigQuery."""
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime
from google.cloud import bigquery
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import dateparser

from config import settings
from models.email_schemas import EmailCRMData

# Set up GCP credentials if service account path is provided
if settings.gcp_service_account_path and os.path.exists(settings.gcp_service_account_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.gcp_service_account_path


def normalize_deal_value(value: Optional[str]) -> Optional[float]:
    """
    Normalize deal value to float.
    
    Examples:
        "$75,000" -> 75000.0
        "50k" -> 50000.0
        "$1.5M" -> 1500000.0
    """
    if not value:
        return None
    
    try:
        # Extract numeric part and handle "k", "M", commas
        value_str = str(value).lower().replace(",", "").strip()
        
        # Remove currency symbols
        value_str = re.sub(r'[$€£¥]', '', value_str)
        
        # Handle "k" (thousands) and "M" (millions)
        multiplier = 1
        if value_str.endswith('k'):
            multiplier = 1000
            value_str = value_str[:-1]
        elif value_str.endswith('m'):
            multiplier = 1000000
            value_str = value_str[:-1]
        
        # Extract number
        match = re.search(r'([\d\.]+)', value_str)
        if match:
            num = float(match.group(1))
            return num * multiplier
        
        return None
    except Exception:
        return None


def normalize_follow_up_date(value: Optional[str]) -> Optional[str]:
    """
    Normalize follow-up date to YYYY-MM-DD format.
    
    Examples:
        "2025-11-12" -> "2025-11-12"
        "next week" -> parsed date
        "tomorrow" -> parsed date
    """
    if not value:
        return None
    
    try:
        parsed = dateparser.parse(value)
        if parsed:
            return parsed.date().isoformat()  # YYYY-MM-DD
        return None
    except Exception:
        return None


class EmailExtractorAgent:
    """
    Email extractor agent that extracts structured CRM data from emails
    and stores it in BigQuery.
    """
    
    def __init__(self):
        """Initialize the email extractor agent."""
        self.llm = None
        self.parser = None
        self.bigquery_client = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of LLM and BigQuery client."""
        if self._initialized:
            return
        
        try:
            # Initialize Vertex AI LLM
            self.llm = ChatVertexAI(
                model_name=settings.vertex_ai_model,
                temperature=0,
                location=settings.vertex_ai_location,
                project=settings.gcp_project_id,
            )
            
            # Initialize Pydantic output parser
            self.parser = PydanticOutputParser(pydantic_object=EmailCRMData)
            
            # Initialize BigQuery client (lazy - only when needed)
            self._initialized = True
            
        except Exception as e:
            print(f"Warning: Could not initialize Email Extractor: {e}")
            self._initialized = True
    
    def _get_bigquery_client(self):
        """Get BigQuery client (lazy initialization)."""
        if not self.bigquery_client:
            self.bigquery_client = bigquery.Client(project=settings.gcp_project_id)
        return self.bigquery_client
    
    async def extract_from_email(self, email_text: str, email_metadata: Optional[Dict[str, Any]] = None) -> EmailCRMData:
        """
        Extract structured CRM data from email text.
        
        Args:
            email_text: The email body/text content
            email_metadata: Optional metadata (subject, from, to, date, etc.)
            
        Returns:
            EmailCRMData object with extracted fields
        """
        self._initialize()
        
        if not self.llm:
            raise Exception("Email extractor not available. Check GCP credentials.")
        
        # Build extraction prompt
        prompt_template = PromptTemplate(
            input_variables=["email_text", "email_metadata"],
            template=(
                "Extract the following CRM fields from this email:\n"
                "- contact_name: Name of the contact person mentioned\n"
                "- company: Name of the company mentioned\n"
                "- next_step: Next action item or meeting mentioned\n"
                "- deal_value: Potential deal value (e.g., '$75,000', '50k', '$1.5M')\n"
                "- follow_up_date: Date for follow-up if mentioned (any format)\n"
                "- notes: Additional context, important details, or notes\n\n"
                "IMPORTANT: If a field is not mentioned or cannot be determined from the email, "
                "you MUST set it to null (not an empty string). Always return all fields, even if they are null. "
                "The data will still be stored in the database with null values for missing fields.\n\n"
                "Email Metadata:\n{email_metadata}\n\n"
                "Email Text:\n{email_text}\n\n"
                "Return output that matches this JSON schema:\n{format_instructions}"
            ),
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        
        # Prepare metadata string
        metadata_str = ""
        if email_metadata:
            metadata_str = "\n".join([f"{k}: {v}" for k, v in email_metadata.items()])
        else:
            metadata_str = "None"
        
        # Create chain
        chain = prompt_template | self.llm | self.parser
        
        try:
            result = await chain.ainvoke({
                "email_text": email_text,
                "email_metadata": metadata_str
            })
            return result
        except Exception as e:
            raise Exception(f"Error extracting data from email: {e}")
    
    async def extract_and_store(self, email_text: str, email_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract structured data from email and store in BigQuery.
        
        Args:
            email_text: The email body/text content
            email_metadata: Optional metadata (subject, from, to, date, etc.)
            
        Returns:
            Dictionary with extraction results and BigQuery insertion status
        """
        try:
            # Step 1: Extract structured data
            extracted_data = await self.extract_from_email(email_text, email_metadata)
            
            # Step 2: Normalize and prepare for BigQuery
            # Ensure all fields are set (use None for null values)
            # Convert empty strings, None, and whitespace-only strings to None
            def to_none_if_empty(value):
                """Convert empty/whitespace strings to None."""
                if value is None:
                    return None
                if isinstance(value, str):
                    stripped = value.strip()
                    if not stripped or stripped == "":
                        return None
                    return stripped
                return value
            
            normalized_data = {
                "contact_name": to_none_if_empty(extracted_data.contact_name),
                "company": to_none_if_empty(extracted_data.company),
                "next_step": to_none_if_empty(extracted_data.next_step),
                "deal_value": normalize_deal_value(extracted_data.deal_value),
                "follow_up_date": normalize_follow_up_date(extracted_data.follow_up_date),
                "notes": to_none_if_empty(extracted_data.notes),
                "interaction_medium": "email",  # Always set to "email" for email extractor
                "created_at": datetime.utcnow().isoformat(),  # Add timestamp for tracking
            }
            
            # Final check: ensure no empty strings remain (BigQuery requires None, not empty strings)
            for key, value in normalized_data.items():
                if value == "" or (isinstance(value, str) and not value.strip()):
                    normalized_data[key] = None
            
            # Step 3: Insert into BigQuery
            # Use uppercase dataset name to match user's example (CRM_DATA)
            dataset_name = settings.bigquery_dataset.upper() if settings.bigquery_dataset else "CRM_DATA"
            table_id = f"{settings.gcp_project_id}.{dataset_name}.deals"
            client = self._get_bigquery_client()
            
            # Debug: Print extracted data
            print("\n" + "="*70)
            print("EXTRACTED DATA (before BigQuery insertion):")
            print("="*70)
            for key, value in normalized_data.items():
                print(f"  {key}: {value} (type: {type(value).__name__})")
            print("="*70 + "\n")
            
            # Ensure table exists (create if not)
            try:
                self._ensure_table_exists(client, table_id)
            except Exception as e:
                print(f"⚠️  Warning: Could not ensure table exists: {e}")
                # Try to continue anyway
            
            # Insert row
            try:
                errors = client.insert_rows_json(table_id, [normalized_data])
                if errors:
                    print(f"❌ BigQuery insert errors: {errors}")
                    raise RuntimeError(f"BigQuery insert failed: {errors}")
            except Exception as e:
                error_msg = str(e)
                print(f"❌ BigQuery insertion error: {error_msg}")
                # Check if it's a table not found error
                if "404" in error_msg or "not found" in error_msg.lower() or "truncated" in error_msg.lower():
                    print(f"⚠️  Table might not exist. Attempting to create table: {table_id}")
                    try:
                        self._ensure_table_exists(client, table_id, force_create=True)
                        # Retry insertion
                        errors = client.insert_rows_json(table_id, [normalized_data])
                        if errors:
                            raise RuntimeError(f"BigQuery insert failed after table creation: {errors}")
                        print("✓ Table created and row inserted successfully")
                    except Exception as retry_error:
                        raise RuntimeError(f"Failed to create table and insert: {retry_error}")
                else:
                    raise
            
            return {
                "status": "success",
                "extracted_data": extracted_data.dict(),
                "normalized_data": normalized_data,
                "table_id": table_id,
                "message": "✅ Row inserted successfully into BigQuery."
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "extracted_data": None
            }
    
    def _ensure_table_exists(self, client: bigquery.Client, table_id: str, force_create: bool = False):
        """Ensure the BigQuery table exists, create if not."""
        try:
            table = client.get_table(table_id)
            if force_create:
                print(f"⚠️  Table {table_id} already exists, skipping creation")
            else:
                print(f"✓ Table {table_id} exists")
            return table
        except Exception as e:
            # Table doesn't exist, create it
            print(f"Table {table_id} not found, creating...")
            try:
                # Parse table_id to get dataset and table name
                parts = table_id.split('.')
                if len(parts) != 3:
                    raise ValueError(f"Invalid table_id format: {table_id}. Expected: project.dataset.table")
                
                project_id, dataset_id, table_name = parts
                
                # Ensure dataset exists
                try:
                    dataset = client.get_dataset(dataset_id)
                    print(f"✓ Dataset {dataset_id} exists")
                except Exception:
                    print(f"Creating dataset {dataset_id}...")
                    dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
                    dataset.location = "US"  # Set location
                    dataset = client.create_dataset(dataset, exists_ok=True)
                    print(f"✓ Created dataset {dataset_id}")
                
                # Create table
                schema = [
                    bigquery.SchemaField("contact_name", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("company", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("next_step", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("deal_value", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("follow_up_date", "DATE", mode="NULLABLE"),
                    bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("interaction_medium", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
                ]
                
                table = bigquery.Table(table_id, schema=schema)
                table = client.create_table(table)
                print(f"✓ Created BigQuery table: {table_id}")
                return table
            except Exception as create_error:
                print(f"❌ Error creating table: {create_error}")
                raise

