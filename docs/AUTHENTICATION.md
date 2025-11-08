# Authentication Guide

This document explains the different authentication methods used in the CRM AI Agent.

## Overview

Different Google APIs require different authentication methods:

| API/Service | Authentication Method | Required Credentials |
|------------|----------------------|---------------------|
| **Gmail API** | OAuth 2.0 | Client ID, Client Secret, Refresh Token |
| **Google Calendar API** | OAuth 2.0 or Service Account | OAuth credentials OR Service Account JSON |
| **BigQuery** | Service Account or ADC | Service Account JSON OR `gcloud auth` |
| **Vertex AI** | Service Account or ADC | Service Account JSON OR `gcloud auth` |
| **Speech-to-Text** | Service Account or ADC | Service Account JSON OR `gcloud auth` |
| **Pub/Sub** | Service Account or ADC | Service Account JSON OR `gcloud auth` |
| **Maps/Places API** | API Key | Google API Key |

## Gmail API - OAuth 2.0 (Required)

**You CANNOT use an API key for Gmail API.** Gmail API requires OAuth 2.0 because it accesses user's personal email data.

### Setup Steps:

1. **Enable Gmail API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/library)
   - Search for "Gmail API" and enable it

2. **Create OAuth 2.0 Credentials**:
   - Go to [Credentials page](https://console.cloud.google.com/apis/credentials)
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" or "Web application"
   - Download the credentials JSON (contains client_id and client_secret)

3. **Get Refresh Token**:
   - Complete the OAuth flow once to get a refresh token
   - The refresh token allows the app to access Gmail without user interaction
   - You can use a script or tool to generate the refresh token

4. **Add to `.env`**:
   ```
   GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=your-client-secret
   GMAIL_REFRESH_TOKEN=your-refresh-token
   GMAIL_USER_EMAIL=your-email@gmail.com
   ```

## Google Calendar API

Similar to Gmail, Calendar API can use:
- **OAuth 2.0** (for user calendars)
- **Service Account** (for shared calendars)

Set `GOOGLE_CALENDAR_CREDENTIALS_PATH` to the path of your credentials file.

## GCP Services (BigQuery, Vertex AI, etc.)

These services use **Service Account credentials** or **Application Default Credentials (ADC)**, NOT API keys.

### Option 1: Application Default Credentials (Local Development)
```bash
gcloud auth application-default login
```

### Option 2: Service Account (Production)
1. Create a service account in Google Cloud Console
2. Grant necessary permissions (BigQuery Admin, Vertex AI User, etc.)
3. Download the JSON key file
4. Set in `.env`:
   ```
   GCP_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
   ```

## Google API Key

**When to use**: Only for public APIs like:
- Google Maps API
- Places API
- YouTube Data API (for public data)
- Other public-facing APIs

**When NOT to use**: 
- ❌ Gmail API (requires OAuth)
- ❌ BigQuery (requires Service Account)
- ❌ Vertex AI (requires Service Account)
- ❌ Any API that accesses user data

## Summary

- **Gmail API**: Must use OAuth 2.0 (Client ID + Secret + Refresh Token)
- **GCP Services**: Use Service Account or ADC (NOT API keys)
- **Public APIs**: Can use API keys (optional, only if needed)

**You do NOT need a Google API key for Gmail API** - it won't work. You must use OAuth credentials.

