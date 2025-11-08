# GCP Service Account Setup for Gmail Agent

The Gmail agent uses Vertex AI (Gemini) for the LLM, which requires GCP credentials. Since `gcloud` CLI is not installed, we'll use a service account instead.

## Step 1: Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `ai-hackathon-477617`
3. Navigate to **IAM & Admin** > **Service Accounts**
4. Click **+ CREATE SERVICE ACCOUNT**
5. Fill in:
   - **Service account name**: `crm-ai-agent` (or any name you prefer)
   - **Service account ID**: (auto-generated)
   - Click **CREATE AND CONTINUE**

## Step 2: Grant Permissions

Add the following roles:
- **Vertex AI User** (for using Gemini)
- **BigQuery User** (if using BigQuery)
- **Pub/Sub Publisher** (if using Pub/Sub)

Click **CONTINUE** and then **DONE**.

## Step 3: Create and Download Key

1. Click on the service account you just created
2. Go to the **KEYS** tab
3. Click **ADD KEY** > **Create new key**
4. Select **JSON** format
5. Click **CREATE**
6. The JSON file will download automatically

## Step 4: Save the Key File

1. Move the downloaded JSON file to your project directory:
   ```bash
   mv ~/Downloads/your-project-*.json /Users/tylerlwq/Downloads/crm-ai-agent/gcp-service-account.json
   ```

2. **Important**: Add this file to `.gitignore` (it's already there, but double-check):
   ```bash
   echo "gcp-service-account.json" >> .gitignore
   ```

## Step 5: Update .env

Add the path to your `.env` file:

```bash
GCP_SERVICE_ACCOUNT_PATH=/Users/tylerlwq/Downloads/crm-ai-agent/gcp-service-account.json
```

Or use a relative path:

```bash
GCP_SERVICE_ACCOUNT_PATH=./gcp-service-account.json
```

## Step 6: Verify Setup

Run the test script:

```bash
uv run python tests/test_gmail_agent_full.py
```

It should now detect the service account and allow the agent to work.

## Security Notes

- **Never commit** the service account JSON file to git
- Keep it secure and don't share it
- If compromised, delete the key in Google Cloud Console and create a new one
- The file is already in `.gitignore` for safety

## Troubleshooting

### "Service account not found"
- Check that the path in `.env` is correct
- Use absolute path if relative path doesn't work
- Verify the file exists: `ls -la gcp-service-account.json`

### "Permission denied"
- Make sure the service account has **Vertex AI User** role
- Check that Vertex AI API is enabled in your project

### "Project not found"
- Verify `GCP_PROJECT_ID=ai-hackathon-477617` in your `.env`
- Make sure the service account belongs to the same project

