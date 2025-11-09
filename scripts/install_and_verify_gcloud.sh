#!/bin/bash
# Script to install gcloud CLI and verify GCP credentials

set -e

echo "=========================================="
echo "gcloud CLI Installation and Verification"
echo "=========================================="
echo ""

# Check if already installed
if command -v gcloud &> /dev/null; then
    echo "✅ gcloud is already installed"
    gcloud --version | head -3
    echo ""
elif [ -f "$HOME/google-cloud-sdk/bin/gcloud" ]; then
    echo "✅ gcloud found in ~/google-cloud-sdk"
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    gcloud --version | head -3
    echo ""
else
    echo "📥 Installing gcloud CLI..."
    echo ""
    
    # Check architecture
    ARCH=$(uname -m)
    echo "Detected architecture: $ARCH"
    
    if [ "$ARCH" = "arm64" ]; then
        URL="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz"
        FILE="google-cloud-cli-darwin-arm.tar.gz"
    else
        URL="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-x86_64.tar.gz"
        FILE="google-cloud-cli-darwin-x86_64.tar.gz"
    fi
    
    # Download
    echo "Downloading gcloud CLI for $ARCH..."
    cd ~
    curl -O "$URL" || { echo "❌ Download failed"; exit 1; }
    
    # Extract
    echo "Extracting..."
    tar -xf "$FILE" || { echo "❌ Extraction failed"; exit 1; }
    rm "$FILE"
    
    # Install
    echo "Installing..."
    ./google-cloud-sdk/install.sh --quiet --usage-reporting=false --path-update=true || { echo "❌ Installation failed"; exit 1; }
    
    # Add to PATH for this session
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    
    echo "✅ gcloud installed successfully"
    echo ""
fi

# Ensure gcloud is in PATH
if ! command -v gcloud &> /dev/null && [ -f "$HOME/google-cloud-sdk/bin/gcloud" ]; then
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi

# Verify installation
echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""
gcloud --version | head -3
echo ""

# Check authentication
echo "=========================================="
echo "Authentication Status"
echo "=========================================="
echo ""
gcloud auth list || echo "No active authentication"

# Set project
echo ""
echo "Setting project to ai-hackathon-477617..."
gcloud config set project ai-hackathon-477617 2>&1 || echo "⚠️  Could not set project (may need to authenticate first)"
echo ""

# Check Application Default Credentials
echo "=========================================="
echo "Application Default Credentials"
echo "=========================================="
echo ""
if gcloud auth application-default print-access-token > /dev/null 2>&1; then
    echo "✅ Application Default Credentials are set"
else
    echo "❌ Application Default Credentials not set"
    echo ""
    echo "To fix the 401 error, run:"
    echo "  gcloud auth application-default login"
    echo ""
    read -p "Do you want to set them up now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud auth application-default login
        echo "✅ Application Default Credentials set"
    else
        echo "⚠️  Please run 'gcloud auth application-default login' manually"
    fi
fi

# Test BigQuery
echo ""
echo "=========================================="
echo "BigQuery Access Test"
echo "=========================================="
echo ""
if gcloud bq datasets list --project=ai-hackathon-477617 2>&1 | head -5; then
    echo ""
    echo "✅ BigQuery access working!"
else
    echo "⚠️  BigQuery access test failed"
    echo "   This may be normal if you need to authenticate first"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If Application Default Credentials are not set, run:"
echo "   gcloud auth application-default login"
echo ""
echo "2. Restart your server:"
echo "   ./scripts/start_server.sh"
echo ""

