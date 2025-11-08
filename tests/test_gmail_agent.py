"""Test Gmail agent using LangChain GmailToolkit."""
import asyncio
import os
from services.gmail_agent import GmailAgent


async def test_gmail_agent_send_email():
    """Test sending email using Gmail agent."""
    print("=" * 60)
    print("TEST: Gmail Agent - Send Email")
    print("=" * 60)
    
    # Check if credentials.json exists
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print(f"⚠️  credentials.json not found at {credentials_path}")
        print("\nTo set up:")
        print("  1. Go to Google Cloud Console > APIs & Services > Credentials")
        print("  2. Click on your OAuth 2.0 Client ID")
        print("  3. Click 'Download JSON'")
        print("  4. Save it as 'credentials.json' in the project root")
        print("  5. Make sure your email is added as a 'Test User' in OAuth consent screen")
        print("\nOn first run, a browser will open for authorization.")
        print("This will create 'token.json' for future runs.\n")
        return
    
    print(f"✓ Found credentials.json")
    
    agent = GmailAgent(credentials_path=credentials_path)
    
    # Test email - update with your email address
    # Use the email from config if available, otherwise prompt
    from config import settings
    test_recipient = settings.gmail_user_email or "your-email@example.com"
    
    if test_recipient == "your-email@example.com":
        print("⚠️  Update test_recipient in the test file or set GMAIL_USER_EMAIL in .env")
        print("   Skipping email send test\n")
        return
    
    try:
        print(f"\nSending test email to {test_recipient}...")
        print("(This may open a browser for authorization on first run)\n")
        
        response = await agent.send_email(
            to=test_recipient,
            subject="Test Email from Gmail Agent",
            body="This is a test email sent using LangChain GmailToolkit agent!"
        )
        
        print(f"\n✓ Agent response:")
        print(f"  {response}")
        print("\n✅ Email sent successfully via Gmail agent!")
        print("   Check your inbox for the test email.\n")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        
        if "credentials" in error_msg.lower() or "token" in error_msg.lower():
            print("\nTroubleshooting:")
            print("  1. Make sure credentials.json exists and is valid")
            print("  2. On first run, complete the OAuth flow in the browser")
            print("  3. Check that token.json was created after authorization")
            print("  4. Make sure your email is added as 'Test User' in OAuth consent screen")
        print()


async def test_gmail_agent_search():
    """Test searching emails using Gmail agent."""
    print("=" * 60)
    print("TEST: Gmail Agent - Search Emails")
    print("=" * 60)
    
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print("⚠️  credentials.json not found. Skipping test.\n")
        return
    
    agent = GmailAgent(credentials_path=credentials_path)
    
    try:
        print("\nSearching for recent emails...")
        response = await agent.search_emails(
            query="is:unread",
            max_results=5
        )
        
        print(f"\n✓ Search results:")
        print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")
        print("\n✅ Email search test passed!\n")
        
    except Exception as e:
        print(f"⚠️  Search test failed: {e}\n")


async def run_all_tests():
    """Run all Gmail agent tests."""
    print("\n" + "=" * 60)
    print("GMAIL AGENT TESTS (LangChain GmailToolkit)")
    print("=" * 60 + "\n")
    
    print("ℹ️  Note: This uses a different approach than the direct Gmail API.")
    print("   It requires:")
    print("   - credentials.json (OAuth 2.0 Client ID JSON from Google Cloud)")
    print("   - token.json (created automatically after first authorization)")
    print("   - Your email added as 'Test User' in OAuth consent screen\n")
    
    await test_gmail_agent_send_email()
    await test_gmail_agent_search()
    
    print("=" * 60)
    print("✅ ALL GMAIL AGENT TESTS COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

