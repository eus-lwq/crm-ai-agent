"""BigQuery table schemas for CRM data."""
from google.cloud import bigquery
from typing import List


def get_contacts_schema() -> List[bigquery.SchemaField]:
    """Get BigQuery schema for contacts table."""
    return [
        bigquery.SchemaField("contact_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("full_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("phone", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("company_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
        bigquery.SchemaField("embeddings", "FLOAT", mode="REPEATED"),
        bigquery.SchemaField("last_touch_at", "TIMESTAMP", mode="NULLABLE"),
    ]


def get_companies_schema() -> List[bigquery.SchemaField]:
    """Get BigQuery schema for companies table."""
    return [
        bigquery.SchemaField("company_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("domain", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("linkedin", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("size", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("industry", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("enrichment_json", "JSON", mode="NULLABLE"),
    ]


def get_interactions_schema() -> List[bigquery.SchemaField]:
    """Get BigQuery schema for interactions table."""
    return [
        bigquery.SchemaField("interaction_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("contact_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("company_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("channel", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("occurred_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("raw_text", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("summary", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("action_items", "STRING", mode="REPEATED"),
        bigquery.SchemaField("next_step", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("follow_up_date", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("sentiment", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("risk_flags", "STRING", mode="REPEATED"),
        bigquery.SchemaField("owner", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("confidence", "FLOAT", mode="NULLABLE"),
    ]


def get_deals_schema() -> List[bigquery.SchemaField]:
    """Get BigQuery schema for deals table."""
    return [
        bigquery.SchemaField("deal_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("company_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("contact_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("amount", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("currency", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("stage", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("next_step", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("close_date", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("health_score", "FLOAT", mode="NULLABLE"),
    ]

