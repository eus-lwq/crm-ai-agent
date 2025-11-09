#!/usr/bin/env python3
"""Debug script to test chat agent initialization and execution."""
import sys
import os
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_agent_init():
    """Test agent initialization step by step."""
    print("=" * 60)
    print("Testing Chat Agent Initialization")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Import modules
        print("1. Importing modules...")
        from config import settings
        from src.agents.chatagent import initialize_agent, chat
        print("   ✅ Modules imported")
        print()
        
        # Step 2: Check configuration
        print("2. Checking configuration...")
        print(f"   Vertex AI Model: {settings.vertex_ai_model}")
        print(f"   Vertex AI Location: {settings.vertex_ai_location}")
        print(f"   GCP Project ID: {settings.gcp_project_id}")
        print(f"   BigQuery Dataset: {settings.bigquery_dataset}")
        print()
        
        # Step 3: Initialize agent
        print("3. Initializing agent...")
        try:
            agent = initialize_agent(
                model_name=settings.vertex_ai_model,
                vertex_location=settings.vertex_ai_location,
                bq_project_id=settings.gcp_project_id,
                bq_dataset_id=settings.bigquery_dataset,
            )
            print("   ✅ Agent initialized successfully")
            print()
        except Exception as e:
            print(f"   ❌ Agent initialization failed: {type(e).__name__}: {str(e)}")
            print(f"   Traceback:")
            traceback.print_exc()
            return False
        
        # Step 4: Test simple chat
        print("4. Testing simple chat message...")
        try:
            result = chat("Hello, can you help me?", None)
            print("   ✅ Chat function completed")
            print(f"   Response preview: {result.get('response', 'No response')[:200]}")
            print(f"   History length: {len(result.get('history', []))}")
            print()
            return True
        except Exception as e:
            print(f"   ❌ Chat function failed: {type(e).__name__}: {str(e)}")
            print(f"   Traceback:")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Fatal error: {type(e).__name__}: {str(e)}")
        print(f"Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_init()
    sys.exit(0 if success else 1)

