from google.cloud import bigquery
import dateparser
import re

def normalize_deal_value(value):
    if not value:
        return None
    # Extract numeric part and handle "k" or commas
    value_str = str(value).lower().replace(",", "").strip()
    match = re.search(r"([\d\.]+)\s*k?", value_str)
    if match:
        num = float(match.group(1))
        if "k" in value_str:
            num *= 1000
        return num
    return None

def normalize_follow_up_date(value):
    if not value:
        return None
    parsed = dateparser.parse(value)
    if parsed:
        return parsed.date().isoformat()  # YYYY-MM-DD
    return None

def insert_into_bigquery(data: dict):
    client = bigquery.Client()
    table_id = "ai-hackathon-477617.CRM_DATA.deals"

    # Normalize fields
    row = {
        "contact_name": data.get("contact_name"),
        "company": data.get("company"),
        "next_step": data.get("next_step"),
        "deal_value": normalize_deal_value(data.get("deal_value")),
        "follow_up_date": normalize_follow_up_date(data.get("follow_up_date")),
        "notes": data.get("notes"),
    }

    errors = client.insert_rows_json(table_id, [row])
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")
    print("✅ Row inserted successfully into BigQuery.")
