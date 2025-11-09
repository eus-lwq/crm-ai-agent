#!/bin/bash
# Script to refresh GCP credentials for BigQuery and Vertex AI

set -e

echo "=========================================="
echo "GCP Credentials Refresh Script"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed."
    echo "   Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ gcloud CLI found"
echo ""

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️  No active gcloud authentication found"
    echo ""
    echo "Please authenticate with one of these methods:"
    echo ""
    echo "Option 1: Application Default Credentials (Recommended)"
    echo "  gcloud auth application-default login"
    echo ""
    echo "Option 2: User Account"
    echo "  gcloud auth login"
    echo ""
    echo "Option 3: Service Account (if you have a service account JSON)"
    echo "  gcloud auth activate-service-account --key-file=path/to/service-account.json"
    echo ""
    read -p "Do you want to run 'gcloud auth application-default login' now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud auth application-default login
    else
        echo "Please run one of the authentication commands above and try again."
        exit 1
    fi
else
    echo "✅ Active gcloud authentication found:"
    gcloud auth list --filter=status:ACTIVE --format="table(account,status)"
    echo ""
fi

# Check if using service account
if [ -f "gcp-service-account.json" ]; then
    echo "✅ Service account file found: gcp-service-account.json"
    echo ""
    read -p "Do you want to use this service account? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/gcp-service-account.json"
        echo "✅ Set GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
        echo ""
        echo "To make this permanent, add to your .env file:"
        echo "  GCP_SERVICE_ACCOUNT_PATH=$(pwd)/gcp-service-account.json"
        echo ""
    fi
fi

# Set project
PROJECT_ID="ai-hackathon-477617"
echo "Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Verify BigQuery access
echo ""
echo "Testing BigQuery access..."
if gcloud bq datasets list --project=$PROJECT_ID &> /dev/null; then
    echo "✅ BigQuery access verified"
else
    echo "⚠️  BigQuery access test failed. You may need to enable the BigQuery API:"
    echo "   gcloud services enable bigquery.googleapis.com"
fi

# Verify Vertex AI access
echo ""
echo "Testing Vertex AI access..."
if gcloud ai models list --region=us-central1 --project=$PROJECT_ID &> /dev/null 2>&1; then
    echo "✅ Vertex AI access verified"
else
    echo "⚠️  Vertex AI access test failed. You may need to enable the Vertex AI API:"
    echo "   gcloud services enable aiplatform.googleapis.com"
fi

echo ""
echo "=========================================="
echo "✅ Credentials refresh complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If using service account, add to .env:"
echo "   GCP_SERVICE_ACCOUNT_PATH=$(pwd)/gcp-service-account.json"
echo ""
echo "2. Restart the server:"
echo "   ./scripts/start_server.sh"
echo ""

