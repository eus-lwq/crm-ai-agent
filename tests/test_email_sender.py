"""Test email sending service."""
import asyncio
from services.email_sender import EmailSender


async def test_send_plain_email():
    """Test sending a plain text email."""
    print("=" * 60)
    print("TEST 1: Send Plain Text Email")
    print("=" * 60)
    
    sender = EmailSender()
    
    # Test email - update with your email address
    test_recipient = "your-email@example.com"  # Change this to your email
    
    try:
        message_id = await sender.send_email(
            to=test_recipient,
            subject="Test Email from CRM AI Agent",
            body="""
Hello!

This is a test email from the CRM AI Agent email sending service.

If you received this email, the Gmail API integration is working correctly!

This follows Google's OAuth 2.0 best practices:
- Uses refresh tokens for long-term access
- Automatically refreshes expired access tokens
- Uses Google's OAuth 2.0 libraries

Best regards,
CRM AI Agent
            """.strip()
        )
        
        print(f"✓ Email sent successfully!")
        print(f"✓ Message ID: {message_id}")
        print(f"✓ Recipient: {test_recipient}")
        print("\n✅ Plain text email test passed!")
        print("   Check your inbox for the test email.\n")
        
    except Exception as e:
        error_msg = str(e)
        if "not configured" in error_msg.lower() or "credentials" in error_msg.lower():
            print(f"⚠️  Email sending test skipped (Gmail not configured)")
            print(f"   Error: {error_msg}")
            print("\n   To enable email sending:")
            print("   1. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET in .env")
            print("   2. Get GMAIL_REFRESH_TOKEN using OAuth Playground:")
            print("      https://developers.google.com/oauthplayground/")
            print("      (See docs/GMAIL_SETUP.md for instructions)")
            print("   3. Add the refresh token to .env as GMAIL_REFRESH_TOKEN=...")
            print("   4. Set GMAIL_USER_EMAIL in .env")
            print("   5. Make sure Gmail API is enabled in your Google Cloud project")
            print("\n   Note: Make sure GMAIL_REFRESH_TOKEN is NOT commented out in .env\n")
        else:
            print(f"❌ Email sending test failed: {error_msg}\n")
            raise


async def test_send_html_email():
    """Test sending an HTML email."""
    print("=" * 60)
    print("TEST 2: Send HTML Email")
    print("=" * 60)
    
    sender = EmailSender()
    
    # Test email - update with your email address
    test_recipient = "your-email@example.com"  # Change this to your email
    
    html_body = """
    <html>
      <body>
        <h2>Test HTML Email from CRM AI Agent</h2>
        <p>This is a <strong>test email</strong> with HTML formatting.</p>
        <ul>
          <li>Feature 1: HTML support</li>
          <li>Feature 2: Rich formatting</li>
          <li>Feature 3: Gmail API integration</li>
          <li>Feature 4: OAuth 2.0 authentication</li>
        </ul>
        <p>If you received this email, the HTML email sending is working!</p>
        <p style="color: blue;">Best regards,<br>CRM AI Agent</p>
      </body>
    </html>
    """
    
    plain_text = """
Test HTML Email from CRM AI Agent

This is a test email with HTML formatting.

Features:
- HTML support
- Rich formatting
- Gmail API integration
- OAuth 2.0 authentication

If you received this email, the HTML email sending is working!

Best regards,
CRM AI Agent
    """
    
    try:
        message_id = await sender.send_html_email(
            to=test_recipient,
            subject="Test HTML Email from CRM AI Agent",
            html_body=html_body,
            plain_text=plain_text
        )
        
        print(f"✓ HTML email sent successfully!")
        print(f"✓ Message ID: {message_id}")
        print(f"✓ Recipient: {test_recipient}")
        print("\n✅ HTML email test passed!")
        print("   Check your inbox for the HTML email.\n")
        
    except Exception as e:
        error_msg = str(e)
        if "not configured" in error_msg.lower() or "credentials" in error_msg.lower():
            print(f"⚠️  HTML email test skipped (Gmail not configured)")
            print(f"   Error: {error_msg}\n")
        else:
            print(f"❌ HTML email test failed: {error_msg}\n")
            raise


async def run_all_tests():
    """Run all email sending tests."""
    print("\n" + "=" * 60)
    print("EMAIL SENDING TESTS")
    print("=" * 60 + "\n")
    
    print("ℹ️  Note: These tests require Gmail API credentials.")
    print("   Update the test_recipient email addresses in the test file.")
    print("   Tests will be skipped if Gmail is not configured.\n")
    
    await test_send_plain_email()
    await test_send_html_email()
    
    print("=" * 60)
    print("✅ ALL EMAIL SENDING TESTS COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

