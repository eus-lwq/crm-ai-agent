#!/usr/bin/env python3
"""Test script to debug the chat endpoint."""
import sys
import os
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.chatagent import initialize_agent, chat
from config import settings

def test_chat():
    """Test the chat function directly."""
    print("=" * 60)
    print("Testing Chat Endpoint")
    print("=" * 60)
    print()
    
    try:
        # Initialize agent
        print("1. Initializing agent...")
        agent = initialize_agent(
            model_name=settings.vertex_ai_model,
            vertex_location=settings.vertex_ai_location,
            bq_project_id=settings.gcp_project_id,
            bq_dataset_id=settings.bigquery_dataset,
        )
        print("   ✅ Agent initialized")
        print()
        
        # Test simple message
        print("2. Testing simple message...")
        test_message = "Hello, can you help me?"
        print(f"   Message: {test_message}")
        
        result = chat(test_message, None)
        
        print("   ✅ Chat function completed")
        print(f"   Response: {result.get('response', 'No response')[:200]}")
        print(f"   History length: {len(result.get('history', []))}")
        print()
        
        # Test with conversation history
        print("3. Testing with conversation history...")
        history = result.get('history', [])
        result2 = chat("What tables are available?", history)
        print("   ✅ Second message completed")
        print(f"   Response: {result2.get('response', 'No response')[:200]}")
        print()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR OCCURRED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Full traceback:")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    test_chat()

