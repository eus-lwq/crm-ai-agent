# Gmail Agent Setup (LangChain GmailToolkit)

This guide explains how to set up the Gmail agent using `langchain_google_community.GmailToolkit`.

## Overview

The Gmail agent uses LangChain's GmailToolkit which provides:
- Email sending
- Email searching
- Email reading
- And more Gmail operations via an agent executor

## Setup Steps

### 1. Get credentials.json

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click on your **OAuth 2.0 Client ID** (the one you're using for Gmail)
3. Click **"Download JSON"** (or "DOWNLOAD CLIENT CONFIGURATION")
4. Save the file as `credentials.json` in your project root directory

**Important**: This is different from the service account JSON. This should be the OAuth 2.0 Client ID credentials.

### 2. Add Test User

1. Go to [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
2. Scroll down to **"Test users"** section
3. Click **"ADD USERS"**
4. Add your Gmail address (the one you want to use)
5. Click **"SAVE"**

**Critical**: If your email is not in the Test users list, Google will block the login attempt.

### 3. First Run (Authorization)

When you first run the Gmail agent:

```python
from services.gmail_agent import GmailAgent

agent = GmailAgent()
await agent.send_email(to="...", subject="...", body="...")
```

1. A browser window will automatically open
2. Sign in with the Google account you added as a Test User
3. Grant permission to the application
4. A `token.json` file will be created in your project directory
5. You won't need to authorize again (token.json stores the authorization)

### 4. Add to .gitignore

**IMPORTANT**: Add these files to `.gitignore`:

```
credentials.json
token.json
```

These files contain sensitive credentials and should never be committed.

## Usage

### Basic Email Sending

```python
from services.gmail_agent import GmailAgent

agent = GmailAgent()

# Send an email
response = await agent.send_email(
    to="recipient@example.com",
    subject="Hello",
    body="This is a test email"
)
print(response)
```

### Email Search

```python
# Search for unread emails
results = await agent.search_emails(
    query="is:unread",
    max_results=10
)
```

### Get Specific Email

```python
# Get email by message ID
email = await agent.get_email(message_id="...")
```

## Files

- **credentials.json**: OAuth 2.0 Client ID credentials (from Google Cloud Console)
- **token.json**: Created automatically after first authorization (stores your permission)

## Differences from Direct Gmail API

| Feature | Direct Gmail API | GmailToolkit Agent |
|---------|-----------------|-------------------|
| Setup | Refresh token in .env | credentials.json + token.json |
| First Run | Manual OAuth flow | Automatic browser flow |
| Flexibility | Direct API calls | Agent-based (can reason about actions) |
| Use Case | Simple email sending | Complex email operations with reasoning |

## Troubleshooting

### "credentials.json not found"
- Download the OAuth 2.0 Client ID JSON from Google Cloud Console
- Save it as `credentials.json` in the project root

### "Access blocked" or "User not authorized"
- Make sure your email is added as a "Test User" in OAuth consent screen
- Check that you're using the same Google account

### "token.json not created"
- Complete the OAuth flow in the browser
- Grant all requested permissions
- Check that the browser didn't block popups

### Browser doesn't open
- Make sure you're running the script in an environment with browser access
- For headless servers, use the direct Gmail API approach instead

## Testing

Run the test script:

```bash
uv run python tests/test_gmail_agent.py
```

Make sure to:
1. Have `credentials.json` in the project root
2. Update the test recipient email in the test file
3. Complete the OAuth flow on first run

