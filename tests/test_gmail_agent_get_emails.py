"""Test retrieving email content using Gmail agent."""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.gmail_agent import GmailAgent
from config import settings


async def test_get_emails():
    """Test retrieving email content."""
    print("=" * 70)
    print("GMAIL AGENT - GET EMAIL CONTENT TEST")
    print("=" * 70)
    print()
    
    # Check prerequisites
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print("❌ credentials.json not found")
        return False
    
    print("✓ credentials.json found")
    
    # Initialize agent
    print("\nInitializing Gmail agent...")
    try:
        agent = GmailAgent(credentials_path=credentials_path)
        print("✓ Agent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # First, search for recent emails to get message IDs
    print("\n" + "=" * 70)
    print("STEP 1: Search for recent emails")
    print("=" * 70)
    print()
    
    try:
        print("Searching for recent emails...")
        search_result = await agent.search_emails(query="is:inbox", max_results=5)
        print(f"\nSearch result:\n{search_result}\n")
        
        # Try to extract message IDs from the search result
        # The agent might return message IDs in the response
        print("Note: The search result above may contain message IDs.")
        print("We'll now try to get email content using the get_email method.")
        print()
        
    except Exception as e:
        print(f"⚠️  Search failed: {e}")
        print("Continuing with direct message ID retrieval...\n")
    
    # Alternative: Use the tool directly to search and get message IDs
    print("=" * 70)
    print("STEP 2: Get email content directly")
    print("=" * 70)
    print()
    
    try:
        tools = agent.toolkit.get_tools()
        search_tool = [t for t in tools if 'search' in t.name.lower()][0]
        get_tool = [t for t in tools if 'get' in t.name.lower() and 'message' in t.name.lower()][0]
        
        print("Using search_gmail tool to find recent emails...")
        # Search for recent emails
        search_result = search_tool.invoke({"query": "is:inbox", "max_results": 5})
        
        print(f"Search result type: {type(search_result)}")
        print(f"Search result: {search_result}\n")
        
        # Parse the result to get message IDs
        # The result might be a string or a dict
        message_ids = []
        
        if isinstance(search_result, str):
            # Try to extract message IDs from string
            import re
            # Gmail message IDs are typically long alphanumeric strings
            potential_ids = re.findall(r'[a-zA-Z0-9]{16,}', search_result)
            if potential_ids:
                message_ids = potential_ids[:2]  # Get first 2
        elif isinstance(search_result, dict):
            # Check if it has message IDs
            if 'messages' in search_result:
                message_ids = [msg.get('id') for msg in search_result['messages'][:2]]
            elif 'message_ids' in search_result:
                message_ids = search_result['message_ids'][:2]
        
        if not message_ids:
            print("⚠️  Could not extract message IDs from search result.")
            print("Trying alternative approach: using direct Gmail API search...\n")
            
            # Try using the search tool with error handling
            try:
                # Use a simpler query that's less likely to hit encoding issues
                search_result = search_tool.invoke({"query": "is:inbox", "max_results": 2})
                
                # Try to parse the result
                if isinstance(search_result, list):
                    message_ids = [msg.get('id') for msg in search_result[:2] if isinstance(msg, dict) and 'id' in msg]
                elif isinstance(search_result, str):
                    import re
                    potential_ids = re.findall(r'[a-zA-Z0-9]{16,}', search_result)
                    if potential_ids:
                        message_ids = potential_ids[:2]
            except UnicodeDecodeError as e:
                print(f"⚠️  Encoding error in search result: {e}")
                print("This can happen with emails that use non-UTF-8 encoding.")
                print("Trying to get message IDs from a different approach...\n")
                
                # Try using the agent with a simpler prompt
                try:
                    agent_prompt = "Find 2 recent emails in my inbox. Just return their message IDs, nothing else."
                    response = agent.agent_executor.invoke({"input": agent_prompt})
                    print(f"Agent response: {response.get('output', 'No output')[:200]}...\n")
                    
                    # Try to extract IDs from agent response
                    import re
                    potential_ids = re.findall(r'[a-zA-Z0-9]{16,}', str(response.get('output', '')))
                    if potential_ids:
                        message_ids = potential_ids[:2]
                except Exception as agent_error:
                    print(f"⚠️  Agent also failed: {agent_error}\n")
        
        if not message_ids:
            print("❌ Could not find message IDs. Cannot retrieve email content.")
            print("\nTo test manually:")
            print("  1. Open Gmail and find an email")
            print("  2. The message ID is in the URL or you can use the search tool")
            print("  3. Call agent.get_email(message_id) with a valid message ID")
            return False
        
        print(f"✓ Found {len(message_ids)} message ID(s): {message_ids[:2]}\n")
        
        # Get content for up to 2 emails
        print("=" * 70)
        print("STEP 3: Retrieve email content")
        print("=" * 70)
        print()
        
        emails_retrieved = 0
        for i, msg_id in enumerate(message_ids[:2], 1):
            try:
                print(f"Retrieving email {i} (ID: {msg_id[:20]}...):")
                
                # Use the tool directly with error handling
                try:
                    email_content = get_tool.invoke({"message_id": msg_id})
                except UnicodeDecodeError as decode_error:
                    print(f"⚠️  Encoding error when retrieving email {i}: {decode_error}")
                    print("   This email may have non-UTF-8 encoding. Skipping...\n")
                    continue
                
                print(f"✓ Email {i} retrieved successfully")
                print(f"\nEmail {i} content:")
                print("-" * 70)
                
                if isinstance(email_content, dict):
                    # Pretty print the email content
                    for key, value in email_content.items():
                        if key == 'body' and isinstance(value, str):
                            # Truncate long bodies and handle encoding
                            try:
                                display_value = value[:200] + "..." if len(value) > 200 else value
                                print(f"{key}: {display_value}")
                            except UnicodeEncodeError:
                                print(f"{key}: [Content contains non-printable characters]")
                        elif isinstance(value, str) and len(value) > 100:
                            print(f"{key}: {value[:100]}...")
                        else:
                            print(f"{key}: {value}")
                else:
                    try:
                        content_str = str(email_content)[:500]
                        print(content_str)
                    except UnicodeEncodeError:
                        print("[Content contains non-printable characters]")
                
                print("-" * 70)
                print()
                emails_retrieved += 1
                
            except Exception as e:
                print(f"⚠️  Failed to retrieve email {i}: {e}\n")
                import traceback
                if "UnicodeDecodeError" in str(type(e)):
                    print("   This is an encoding issue. The email may use a non-UTF-8 encoding.")
                continue
        
        if emails_retrieved > 0:
            print("=" * 70)
            print(f"✅ SUCCESS - Retrieved {emails_retrieved} email(s)")
            print("=" * 70)
            return True
        else:
            print("=" * 70)
            print("❌ FAILED - Could not retrieve any emails")
            print("=" * 70)
            return False
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_get_emails())
    print("=" * 70)
    if success:
        print("✅ TEST COMPLETED")
    else:
        print("⚠️  TEST INCOMPLETE")
    print("=" * 70)
    print()

