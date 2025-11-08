# Gmail API Setup Guide

This guide follows [Google's OAuth 2.0 documentation](https://developers.google.com/identity/protocols/oauth2) for server-side applications.

## Overview

The email sending service uses OAuth 2.0 following Google's best practices:
- **Step 1**: Obtain OAuth 2.0 credentials (Client ID & Secret)
- **Step 2**: Obtain access token using refresh token
- **Step 3**: Examine scopes granted
- **Step 4**: Send access token to Gmail API
- **Step 5**: Refresh access token when expired (automatic)

## Fixing "redirect_uri_mismatch" Error

If you're getting a `redirect_uri_mismatch` error, you need to configure the authorized redirect URIs in Google Cloud Console.

### Steps to Fix:

1. **Go to Google Cloud Console**:
   - Navigate to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)

2. **Find Your OAuth 2.0 Client**:
   - Click on your OAuth 2.0 Client ID (the one you're using for Gmail)

3. **Add Authorized Redirect URIs**:
   - Under "Authorized redirect URIs", click "ADD URI"
   - Add these URIs (one at a time):
     - `http://localhost:8080`
     - `http://127.0.0.1:8080`
     - `http://localhost`
     - `urn:ietf:wg:oauth:2.0:oob` (for out-of-band flow)

4. **Save**:
   - Click "SAVE" at the bottom

5. **Try Again**:
   - Run the script again: `uv run python scripts/get_gmail_refresh_token.py`

### Recommended: Use OAuth Playground (Easiest Method)

**This is the recommended method** - it's simpler and avoids redirect URI configuration:

1. Go to [Google OAuth Playground](https://developers.google.com/oauthplayground/)

2. Click the **gear icon (⚙️)** in the top right corner

3. Check **"Use your own OAuth credentials"**

4. Enter:
   - **OAuth Client ID**: Your `GMAIL_CLIENT_ID`
   - **OAuth Client secret**: Your `GMAIL_CLIENT_SECRET`

5. In the left panel, find **"Gmail API v1"** and select:
   - `https://www.googleapis.com/auth/gmail.send`

6. Click **"Authorize APIs"**

7. Sign in and authorize

8. Click **"Exchange authorization code for tokens"**

9. Copy the **"Refresh token"** value

10. Add it to your `.env` file:
    ```
    GMAIL_REFRESH_TOKEN=your-refresh-token-here
    ```

### Verify Your OAuth Client Type

Make sure your OAuth 2.0 client is set up as:
- **Application type**: "Desktop app" or "Web application"
- For Desktop app, redirect URIs should include `http://localhost` variants
- For Web application, you can use `http://localhost:8080`

## Complete Setup Checklist

- [ ] Gmail API enabled in Google Cloud Console
- [ ] OAuth 2.0 credentials created
- [ ] Authorized redirect URIs configured (see above)
- [ ] `GMAIL_CLIENT_ID` set in `.env`
- [ ] `GMAIL_CLIENT_SECRET` set in `.env`
- [ ] `GMAIL_REFRESH_TOKEN` obtained and set in `.env` (NOT commented out)
- [ ] `GMAIL_USER_EMAIL` set in `.env`
- [ ] Test email sending: `uv run python tests/test_email_sender.py`

