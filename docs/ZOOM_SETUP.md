# Zoom API Setup Guide

## Finding Your Zoom Account ID

The Zoom Account ID can be found in several places:

### Method 1: Zoom Admin Portal (Easiest)
1. Log in to [Zoom Admin Portal](https://admin.zoom.us/)
2. Navigate to **Account Management** → **Account Profile**
3. The **Account ID** is displayed in the account information section
4. It's usually 8-10 characters long (e.g., `abc123xyz`)

### Method 2: From JWT Token
1. When you create a Server-to-Server OAuth app in Zoom Marketplace
2. The Account ID is included in the JWT token as the "iss" (issuer) field
3. It's the value after `zoom.us/` in the token

### Method 3: API Response
1. Make an API call to Zoom using your credentials
2. The Account ID may be returned in the response headers or body

## Complete Zoom Setup

1. **Create Server-to-Server OAuth App**:
   - Go to [Zoom Marketplace](https://marketplace.zoom.us/develop/create)
   - Click "Create" → "Server-to-Server OAuth"
   - Fill in app details
   - Note your **Account ID**, **Client ID** (API Key), and **Client Secret**

2. **Add to `.env`**:
   ```
   ZOOM_API_KEY=your-client-id-here
   ZOOM_API_SECRET=your-client-secret-here
   ZOOM_ACCOUNT_ID=your-account-id-here
   ZOOM_WEBHOOK_SECRET=your-webhook-secret (if using webhooks)
   ```

## Testing Without Zoom

You can test all other features without Zoom credentials:
- The `ingest_zoom_transcript()` function will still work if you provide transcript data directly
- Simply comment out or omit Zoom credentials in your `.env` file
- The parsing service works independently of Zoom

## Troubleshooting

**Can't find Account ID?**
- Make sure you're logged in as a Zoom account administrator
- The Account ID is different from your Zoom user ID
- Contact Zoom support if you still can't find it

