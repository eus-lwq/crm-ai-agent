#!/bin/bash
# Script to test API endpoints

PORT=${1:-8001}
BASE_URL="http://localhost:$PORT"

echo "🧪 Testing API endpoints on $BASE_URL"
echo ""

# Test health endpoint
echo "1. Testing /health endpoint..."
curl -s "$BASE_URL/health" | python -m json.tool 2>/dev/null || curl -s "$BASE_URL/health"
echo ""
echo ""

# Test interactions endpoint
echo "2. Testing /api/interactions endpoint..."
curl -s "$BASE_URL/api/interactions?limit=3" | python -m json.tool 2>/dev/null || curl -s "$BASE_URL/api/interactions?limit=3"
echo ""
echo ""

echo "✅ API test complete"

