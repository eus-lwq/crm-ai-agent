#!/bin/bash
# Script to set up gcloud CLI and verify GCP credentials

set -e

echo "=========================================="
echo "gcloud CLI Setup and Verification"
echo "=========================================="
echo ""

# Add gcloud to PATH if it exists
if [ -d "$HOME/google-cloud-sdk" ]; then
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    echo "✅ Added gcloud to PATH"
else
    echo "❌ gcloud not found. Please install it first."
    echo "   Run: ./scripts/refresh_gcp_credentials.sh"
    exit 1
fi

# Check gcloud version
echo ""
echo "gcloud version:"
gcloud --version | head -3

# Check authentication
echo ""
echo "=========================================="
echo "Authentication Status"
echo "=========================================="
echo ""
gcloud auth list

# Check project
echo ""
echo "Current project:"
PROJECT=$(gcloud config get-value project 2>/dev/null || echo "Not set")
echo "  $PROJECT"

# Set project if needed
if [ "$PROJECT" != "ai-hackathon-477617" ]; then
    echo ""
    echo "Setting project to ai-hackathon-477617..."
    gcloud config set project ai-hackathon-477617
    echo "✅ Project set"
fi

# Check Application Default Credentials
echo ""
echo "=========================================="
echo "Application Default Credentials"
echo "=========================================="
echo ""
if gcloud auth application-default print-access-token > /dev/null 2>&1; then
    echo "✅ Application Default Credentials are set"
else
    echo "❌ Application Default Credentials not set"
    echo ""
    echo "To set them up, run:"
    echo "  gcloud auth application-default login"
    echo ""
    read -p "Do you want to set them up now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud auth application-default login
    fi
fi

# Test BigQuery access
echo ""
echo "=========================================="
echo "BigQuery Access Test"
echo "=========================================="
echo ""
if gcloud bq datasets list --project=ai-hackathon-477617 2>&1 | grep -q "CRM_DATA\|ERROR"; then
    echo "✅ BigQuery access working"
    echo ""
    echo "Available datasets:"
    gcloud bq datasets list --project=ai-hackathon-477617 --format="table(datasetId)" 2>&1 | head -10
else
    echo "⚠️  BigQuery access test failed"
    echo "   You may need to enable the BigQuery API:"
    echo "   gcloud services enable bigquery.googleapis.com"
fi

# Test Vertex AI access
echo ""
echo "=========================================="
echo "Vertex AI Access Test"
echo "=========================================="
echo ""
if gcloud ai models list --region=us-central1 --project=ai-hackathon-477617 2>&1 | head -5; then
    echo "✅ Vertex AI access working"
else
    echo "⚠️  Vertex AI access test failed (this is normal if no models are deployed)"
    echo "   You may need to enable the Vertex AI API:"
    echo "   gcloud services enable aiplatform.googleapis.com"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To use gcloud in your current shell, run:"
echo "  export PATH=\"\$HOME/google-cloud-sdk/bin:\$PATH\""
echo ""
echo "Or add to your ~/.zshrc or ~/.bashrc:"
echo "  export PATH=\"\$HOME/google-cloud-sdk/bin:\$PATH\""

