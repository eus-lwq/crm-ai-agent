# GCP Credentials Refresh Guide

If you're getting `401 UNAUTHENTICATED` errors from BigQuery or Vertex AI, your GCP credentials may have expired or are missing.

## Quick Fix

Run the refresh script:
```bash
./scripts/refresh_gcp_credentials.sh
```

## Manual Methods

### Method 1: Application Default Credentials (Recommended)

This is the easiest method and works for both BigQuery and Vertex AI:

```bash
gcloud auth application-default login
```

This will:
- Open a browser for authentication
- Store credentials in `~/.config/gcloud/application_default_credentials.json`
- Work automatically with the code (no env vars needed)

### Method 2: Service Account (For Production)

If you have a service account JSON file:

1. **Set the environment variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-service-account.json"
   ```

2. **Or add to `.env` file:**
   ```bash
   GCP_SERVICE_ACCOUNT_PATH=/path/to/gcp-service-account.json
   ```

3. **Or activate the service account:**
   ```bash
   gcloud auth activate-service-account --key-file=gcp-service-account.json
   ```

### Method 3: User Account Login

```bash
gcloud auth login
gcloud config set project ai-hackathon-477617
```

## Verify Credentials

Test BigQuery access:
```bash
gcloud bq datasets list --project=ai-hackathon-477617
```

Test Vertex AI access:
```bash
gcloud ai models list --region=us-central1 --project=ai-hackathon-477617
```

## Enable Required APIs

If you get API not enabled errors:

```bash
# Enable BigQuery API
gcloud services enable bigquery.googleapis.com

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

## Troubleshooting

### Error: "Request is missing required authentication credential"

1. **Check if credentials are set:**
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

2. **Check active gcloud auth:**
   ```bash
   gcloud auth list
   ```

3. **Refresh application default credentials:**
   ```bash
   gcloud auth application-default login
   ```

### Error: "Service account key file not found"

1. **Check if service account file exists:**
   ```bash
   ls -la gcp-service-account.json
   ```

2. **Update .env file with correct path:**
   ```bash
   GCP_SERVICE_ACCOUNT_PATH=/absolute/path/to/gcp-service-account.json
   ```

### Error: "Permission denied" or "Access denied"

1. **Check service account permissions:**
   - BigQuery Data Viewer
   - BigQuery Job User
   - Vertex AI User

2. **Verify project ID:**
   ```bash
   gcloud config get-value project
   ```

## Environment Variables

The following environment variables control GCP authentication:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON file
- `GCP_SERVICE_ACCOUNT_PATH`: Same as above (used by config.py)
- `GCP_PROJECT_ID`: GCP project ID (default: ai-hackathon-477617)

## Priority Order

The code checks credentials in this order:
1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
2. `GCP_SERVICE_ACCOUNT_PATH` from config.py
3. Application Default Credentials (from `gcloud auth application-default login`)
4. Default credentials from gcloud config

