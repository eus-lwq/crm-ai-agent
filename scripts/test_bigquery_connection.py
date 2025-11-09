"""Test script to verify BigQuery connection and table access."""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from src.agents.agent_tools import get_bigquery_client
from google.cloud import bigquery

def test_bigquery_connection():
    """Test connection to BigQuery and verify table exists."""
    print("=" * 70)
    print("Testing BigQuery Connection")
    print("=" * 70)
    
    # Get configuration
    project_id = settings.gcp_project_id or "ai-hackathon-477617"
    dataset_name = settings.bigquery_dataset.upper() if settings.bigquery_dataset else "CRM_DATA"
    table_id = f"{project_id}.{dataset_name}.deals"
    
    print(f"\n📊 Configuration:")
    print(f"  Project ID: {project_id}")
    print(f"  Dataset: {dataset_name}")
    print(f"  Table: {table_id}")
    print(f"  Full path: {table_id}")
    
    try:
        # Get BigQuery client
        print("\n🔌 Connecting to BigQuery...")
        client = get_bigquery_client()
        print("✅ BigQuery client created successfully")
        
        # Check if dataset exists
        print(f"\n📁 Checking dataset: {dataset_name}...")
        dataset_ref = client.dataset(dataset_name, project=project_id)
        try:
            dataset = client.get_dataset(dataset_ref)
            print(f"✅ Dataset '{dataset_name}' exists")
        except Exception as e:
            print(f"❌ Dataset '{dataset_name}' not found: {e}")
            return False
        
        # Check if table exists
        print(f"\n📋 Checking table: deals...")
        table_ref = dataset_ref.table("deals")
        try:
            table = client.get_table(table_ref)
            print(f"✅ Table 'deals' exists")
            print(f"   Rows: {table.num_rows}")
            print(f"   Size: {table.num_bytes} bytes")
            print(f"   Schema fields: {len(table.schema)}")
        except Exception as e:
            print(f"❌ Table 'deals' not found: {e}")
            return False
        
        # Test query
        print(f"\n🔍 Testing query...")
        query = f"""
        SELECT 
            contact_name,
            company,
            next_step,
            deal_value,
            follow_up_date,
            notes,
            interaction_medium
        FROM `{table_id}`
        LIMIT 5
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        print(f"✅ Query executed successfully")
        print(f"\n📊 Sample data (first 5 rows):")
        print("-" * 70)
        
        count = 0
        for row in results:
            count += 1
            print(f"\nRow {count}:")
            print(f"  Contact: {row.contact_name}")
            print(f"  Company: {row.company}")
            print(f"  Next Step: {row.next_step}")
            print(f"  Deal Value: ${row.deal_value}" if row.deal_value else "  Deal Value: None")
            print(f"  Follow-up: {row.follow_up_date}")
            print(f"  Medium: {row.interaction_medium}")
        
        if count == 0:
            print("  (No data found in table)")
        
        print("\n" + "=" * 70)
        print("✅ BigQuery connection test PASSED")
        print("=" * 70)
        return True
        
    except Exception as e:
        import traceback
        print("\n" + "=" * 70)
        print("❌ BigQuery connection test FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print("\nTraceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_bigquery_connection()
    sys.exit(0 if success else 1)

