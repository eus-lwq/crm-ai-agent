"""Full test for Gmail agent - requires GCP credentials for Vertex AI."""
import os
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.gmail_agent import GmailAgent
from config import settings


async def test_gmail_agent_full():
    """Test the full Gmail agent with email sending."""
    print("=" * 70)
    print("GMAIL AGENT FULL TEST")
    print("=" * 70)
    print()
    
    # Check prerequisites
    print("Checking prerequisites...")
    
    # 1. Check credentials.json
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print("❌ credentials.json not found")
        print("\nTo fix:")
        print("  1. Go to Google Cloud Console > APIs & Services > Credentials")
        print("  2. Click on your OAuth 2.0 Client ID")
        print("  3. Click 'Download JSON'")
        print("  4. Save it as 'credentials.json' in the project root")
        return False
    print("✓ credentials.json found")
    
    # 2. Check token.json
    token_path = "token.json"
    if not os.path.exists(token_path):
        print("⚠️  token.json not found (OAuth flow may not have completed)")
        print("   This will be created automatically on first run")
    else:
        print("✓ token.json found")
    
    # 3. Check GCP credentials for Vertex AI
    print("\nChecking GCP credentials for Vertex AI...")
    gcp_configured = False
    
    # Check for service account
    if settings.gcp_service_account_path:
        if os.path.exists(settings.gcp_service_account_path):
            print(f"✓ GCP service account found: {settings.gcp_service_account_path}")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.gcp_service_account_path
            gcp_configured = True
        else:
            print(f"⚠️  GCP service account path set but file not found: {settings.gcp_service_account_path}")
    else:
        print("⚠️  GCP service account not configured in .env")
        print("   Set GCP_SERVICE_ACCOUNT_PATH in .env to use a service account")
    
    # Check for gcloud auth (optional, only if service account not found)
    if not gcp_configured:
        try:
            import subprocess
            result = subprocess.run(
                ["gcloud", "auth", "application-default", "print-access-token"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✓ gcloud application-default credentials found")
                gcp_configured = True
            else:
                print("⚠️  gcloud not configured")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️  gcloud CLI not found or not configured")
    
    if not gcp_configured:
        print("\n" + "=" * 70)
        print("⚠️  GCP CREDENTIALS REQUIRED")
        print("=" * 70)
        print("\nThe Gmail agent uses Vertex AI (Gemini) for the LLM, which requires")
        print("GCP credentials. Choose one of the following options:\n")
        print("Option 1: Use Service Account (Recommended - works without gcloud CLI)")
        print("  1. Create a service account in Google Cloud Console")
        print("  2. Download the JSON key file")
        print("  3. Save it in your project (e.g., gcp-service-account.json)")
        print("  4. Set GCP_SERVICE_ACCOUNT_PATH in .env:")
        print("     GCP_SERVICE_ACCOUNT_PATH=./gcp-service-account.json")
        print("  5. See docs/GCP_SERVICE_ACCOUNT_SETUP.md for detailed instructions\n")
        print("Option 2: Use gcloud CLI (Good for development)")
        print("  1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install")
        print("  2. Run: gcloud auth application-default login")
        print("  3. Select your Google account\n")
        print("Current settings:")
        print(f"  - GCP Project ID: {settings.gcp_project_id}")
        print(f"  - GCP Service Account: {settings.gcp_service_account_path or 'Not set'}")
        print()
        return False
    
    print("\n✓ All prerequisites met!")
    print()
    
    # Test recipient
    test_recipient = settings.gmail_user_email
    if not test_recipient:
        print("⚠️  GMAIL_USER_EMAIL not set in .env")
        print("   Set it to your email address to test email sending")
        return False
    
    print(f"Test recipient: {test_recipient}")
    print()
    
    # Initialize agent
    print("Initializing Gmail agent...")
    try:
        agent = GmailAgent(credentials_path=credentials_path)
        print("✓ Agent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # Test sending email
    print("\n" + "=" * 70)
    print("TEST: Sending Email via Gmail Agent")
    print("=" * 70)
    print()
    
    try:
        print(f"Sending test email to {test_recipient}...")
        print("(This may take a moment as the agent processes the request)\n")
        
        response = await agent.send_email(
            to=test_recipient,
            subject="Test Email from Gmail Agent",
            body="This is a test email sent using LangChain GmailToolkit agent!\n\n"
                 "If you received this, the agent is working correctly."
        )
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"\nAgent response:\n{response}\n")
        print(f"✓ Email sent successfully to {test_recipient}")
        print("  Check your inbox for the test email.\n")
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"\nError: {e}\n")
        
        error_str = str(e).lower()
        if "credentials" in error_str or "authentication" in error_str:
            print("This appears to be an authentication issue.")
            print("\nTroubleshooting:")
            print("  1. For Gmail OAuth:")
            print("     - Make sure credentials.json is valid")
            print("     - Complete OAuth flow (browser should open)")
            print("     - Check that token.json was created")
            print("     - Verify your email is added as 'Test User' in OAuth consent screen")
            print("  2. For Vertex AI:")
            print("     - Make sure GCP credentials are configured (see above)")
            print("     - Verify GCP project ID is correct")
            print("     - Check that Vertex AI API is enabled in your GCP project")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_gmail_agent_full())
    print("=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("⚠️  TEST FAILED - Check setup requirements above")
    print("=" * 70)
    print()

