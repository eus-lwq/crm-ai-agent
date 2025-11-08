"""Simple test for Gmail agent - just test initialization."""
import os
import sys
import importlib.util

# Load gmail_agent directly to avoid import issues
spec = importlib.util.spec_from_file_location("gmail_agent", "services/gmail_agent.py")
gmail_agent = importlib.util.module_from_spec(spec)
sys.modules["gmail_agent"] = gmail_agent
spec.loader.exec_module(gmail_agent)

from services.gmail_agent import GmailAgent


def test_gmail_agent_initialization():
    """Test Gmail agent initialization."""
    print("=" * 60)
    print("TEST: Gmail Agent Initialization")
    print("=" * 60)
    
    credentials_path = "credentials.json"
    
    if not os.path.exists(credentials_path):
        print(f"⚠️  credentials.json not found at {credentials_path}")
        print("\nTo set up:")
        print("  1. Go to Google Cloud Console > APIs & Services > Credentials")
        print("  2. Click on your OAuth 2.0 Client ID")
        print("  3. Click 'Download JSON'")
        print("  4. Save it as 'credentials.json' in the project root")
        return False
    
    print(f"✓ Found credentials.json")
    
    try:
        agent = GmailAgent(credentials_path=credentials_path)
        print("✓ GmailAgent created")
        
        # Try to initialize (this will create toolkit and check for token.json)
        print("\nInitializing agent...")
        agent._initialize()
        
        if agent.toolkit:
            print("✓ GmailToolkit initialized")
            tools = agent.toolkit.get_tools()
            print(f"✓ Found {len(tools)} Gmail tools")
            for tool in tools:
                print(f"  - {tool.name}")
        else:
            print("⚠️  GmailToolkit not initialized")
            return False
        
        if agent.agent_executor:
            print("✓ Agent executor created")
            print("\n✅ Gmail agent initialized successfully!")
            print("\nNext steps:")
            print("  1. Make sure your email is added as 'Test User' in OAuth consent screen")
            print("  2. Run the full test to complete OAuth flow")
            print("  3. After authorization, token.json will be created")
            return True
        else:
            print("⚠️  Agent executor not created")
            print("   This might be due to missing GCP credentials for Vertex AI")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Gmail Agent Simple Test")
    print("=" * 60 + "\n")
    
    success = test_gmail_agent_initialization()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED")
    else:
        print("⚠️  TEST INCOMPLETE - Check setup requirements")
    print("=" * 60 + "\n")

