"""BigQuery storage service for CRM data."""
import uuid
from datetime import datetime
from typing import Optional, List
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from models.schemas import ExtractedData, ProcessedEvent, Channel
from models.bigquery_schema import (
    get_contacts_schema,
    get_companies_schema,
    get_interactions_schema,
    get_deals_schema,
)
from config import settings


class BigQueryStorage:
    """Service for storing CRM data in BigQuery."""
    
    def __init__(self):
        self.client = bigquery.Client(project=settings.gcp_project_id)
        self.dataset_id = settings.bigquery_dataset
        self._ensure_dataset_and_tables()
    
    def _ensure_dataset_and_tables(self):
        """Ensure dataset and tables exist."""
        dataset_ref = self.client.dataset(self.dataset_id)
        
        try:
            self.client.get_dataset(dataset_ref)
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = settings.gcp_region
            self.client.create_dataset(dataset, exists_ok=True)
        
        # Create tables if they don't exist
        tables = {
            "contacts": get_contacts_schema(),
            "companies": get_companies_schema(),
            "interactions": get_interactions_schema(),
            "deals": get_deals_schema(),
        }
        
        for table_name, schema in tables.items():
            table_ref = dataset_ref.table(table_name)
            try:
                self.client.get_table(table_ref)
            except NotFound:
                table = bigquery.Table(table_ref, schema=schema)
                self.client.create_table(table)
    
    async def save_interaction(
        self,
        processed_event: ProcessedEvent,
        extracted_data: ExtractedData,
        confidence: float,
    ) -> str:
        """
        Save interaction and related data to BigQuery.
        
        Returns:
            interaction_id: Generated interaction ID
        """
        interaction_id = str(uuid.uuid4())
        
        # Upsert contacts
        contact_ids = []
        for contact in extracted_data.contacts:
            if contact.full_name or contact.email:
                contact_id = await self._upsert_contact(contact)
                contact_ids.append(contact_id)
        
        # Upsert company
        company_id = None
        if extracted_data.company:
            company_id = await self._upsert_company(extracted_data.company)
        
        # Use first contact_id if available
        contact_id = contact_ids[0] if contact_ids else None
        
        # Convert occurred_at to datetime if needed
        occurred_at = processed_event.occurred_at
        if not isinstance(occurred_at, datetime):
            if isinstance(occurred_at, str):
                occurred_at = datetime.fromisoformat(occurred_at.replace('Z', '+00:00'))
            else:
                occurred_at = datetime.now()
        
        # Save interaction
        interaction_data = {
            "interaction_id": interaction_id,
            "contact_id": contact_id,
            "company_id": company_id,
            "channel": processed_event.channel.value,
            "occurred_at": occurred_at.isoformat(),
            "raw_text": processed_event.raw_text,
            "summary": extracted_data.summary,
            "action_items": extracted_data.action_items,
            "next_step": extracted_data.next_step,
            "follow_up_date": extracted_data.follow_up_date,
            "sentiment": extracted_data.sentiment.value if extracted_data.sentiment else None,
            "risk_flags": extracted_data.risk_flags,
            "owner": None,  # Can be set from metadata if available
            "confidence": confidence,
        }
        
        table_ref = self.client.dataset(self.dataset_id).table("interactions")
        errors = self.client.insert_rows_json(table_ref, [interaction_data])
        
        if errors:
            raise Exception(f"Error inserting interaction: {errors}")
        
        # Save deal if deal_value is present
        if extracted_data.deal_value and extracted_data.deal_value > 0:
            await self._save_deal(
                interaction_id=interaction_id,
                company_id=company_id,
                contact_id=contact_id,
                extracted_data=extracted_data,
            )
        
        return interaction_id
    
    async def _upsert_contact(self, contact) -> str:
        """Upsert contact and return contact_id."""
        # Generate contact_id from email or name
        contact_id = str(uuid.uuid4())
        
        # Check if contact exists (by email)
        if contact.email:
            query = f"""
            SELECT contact_id FROM `{settings.gcp_project_id}.{self.dataset_id}.contacts`
            WHERE email = @email
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", contact.email)
                ]
            )
            results = self.client.query(query, job_config=job_config)
            row = list(results)
            if row:
                contact_id = row[0].contact_id
                # Update existing contact
                update_query = f"""
                UPDATE `{settings.gcp_project_id}.{self.dataset_id}.contacts`
                SET full_name = COALESCE(@full_name, full_name),
                    title = COALESCE(@title, title),
                    phone = COALESCE(@phone, phone),
                    last_touch_at = CURRENT_TIMESTAMP()
                WHERE contact_id = @contact_id
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("contact_id", "STRING", contact_id),
                        bigquery.ScalarQueryParameter("full_name", "STRING", contact.full_name),
                        bigquery.ScalarQueryParameter("title", "STRING", contact.title),
                        bigquery.ScalarQueryParameter("phone", "STRING", contact.phone),
                    ]
                )
                self.client.query(update_query, job_config=job_config).result()
                return contact_id
        
        # Insert new contact
        contact_data = {
            "contact_id": contact_id,
            "full_name": contact.full_name,
            "title": contact.title,
            "email": contact.email,
            "phone": contact.phone,
            "company_id": None,  # Will be linked if company is found
            "tags": [],
            "embeddings": [],
            "last_touch_at": datetime.now().isoformat(),
        }
        
        table_ref = self.client.dataset(self.dataset_id).table("contacts")
        errors = self.client.insert_rows_json(table_ref, [contact_data], skip_invalid_rows=True)
        
        if errors:
            print(f"Warning: Error inserting contact: {errors}")
        
        return contact_id
    
    async def _upsert_company(self, company_name: str) -> str:
        """Upsert company and return company_id."""
        company_id = str(uuid.uuid4())
        
        # Check if company exists
        query = f"""
        SELECT company_id FROM `{settings.gcp_project_id}.{self.dataset_id}.companies`
        WHERE LOWER(name) = LOWER(@name)
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("name", "STRING", company_name)
            ]
        )
        results = self.client.query(query, job_config=job_config)
        row = list(results)
        if row:
            return row[0].company_id
        
        # Insert new company
        company_data = {
            "company_id": company_id,
            "name": company_name,
            "domain": None,
            "linkedin": None,
            "size": None,
            "industry": None,
            "enrichment_json": None,
        }
        
        table_ref = self.client.dataset(self.dataset_id).table("companies")
        errors = self.client.insert_rows_json(table_ref, [company_data], skip_invalid_rows=True)
        
        if errors:
            print(f"Warning: Error inserting company: {errors}")
        
        return company_id
    
    async def _save_deal(
        self,
        interaction_id: str,
        company_id: Optional[str],
        contact_id: Optional[str],
        extracted_data: ExtractedData,
    ):
        """Save deal information."""
        deal_id = str(uuid.uuid4())
        
        deal_data = {
            "deal_id": deal_id,
            "company_id": company_id,
            "contact_id": contact_id,
            "amount": extracted_data.deal_value,
            "currency": extracted_data.currency or "USD",
            "stage": None,  # Can be extracted or inferred
            "next_step": extracted_data.next_step,
            "close_date": None,
            "health_score": None,
        }
        
        table_ref = self.client.dataset(self.dataset_id).table("deals")
        errors = self.client.insert_rows_json(table_ref, [deal_data], skip_invalid_rows=True)
        
        if errors:
            print(f"Warning: Error inserting deal: {errors}")

