"""Example usage of Gmail Agent using LangChain GmailToolkit."""
import asyncio
from services.gmail_agent import GmailAgent


async def example_send_email():
    """Example: Send an email using Gmail agent."""
    print("=" * 60)
    print("Gmail Agent Example - Send Email")
    print("=" * 60)
    
    # Initialize the agent
    # On first run, this will open a browser for OAuth authorization
    agent = GmailAgent()
    
    # Send an email
    try:
        response = await agent.send_email(
            to="your-email@example.com",  # Change this to your email
            subject="Hello from Gmail Agent",
            body="""
            Hello!
            
            This email was sent using LangChain's GmailToolkit agent.
            
            The agent can:
            - Send emails
            - Search emails
            - Read emails
            - And more!
            
            Best regards,
            CRM AI Agent
            """.strip()
        )
        
        print(f"\n✓ Agent Response:")
        print(f"  {response}")
        print("\n✅ Email sent successfully!")
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nSetup required:")
        print("  1. Download credentials.json from Google Cloud Console")
        print("  2. Save it in the project root")
        print("  3. Make sure your email is added as 'Test User'")
        print("  4. Run again - browser will open for authorization")
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def example_search_emails():
    """Example: Search emails using Gmail agent."""
    print("\n" + "=" * 60)
    print("Gmail Agent Example - Search Emails")
    print("=" * 60)
    
    agent = GmailAgent()
    
    try:
        # Search for unread emails
        response = await agent.search_emails(
            query="is:unread",
            max_results=5
        )
        
        print(f"\n✓ Search Results:")
        print(f"  {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run examples."""
    print("\n" + "=" * 60)
    print("Gmail Agent Examples")
    print("=" * 60)
    print("\nThis uses LangChain's GmailToolkit with an agent executor.")
    print("On first run, a browser will open for OAuth authorization.\n")
    
    await example_send_email()
    # await example_search_emails()  # Uncomment to test email search


if __name__ == "__main__":
    asyncio.run(main())

