#!/bin/bash
# Script to fix port configuration

echo "🔧 Fixing port configuration..."

if [ -f .env ]; then
    # Check current port setting
    CURRENT_PORT=$(grep "^API_PORT=" .env | cut -d'=' -f2)
    
    if [ "$CURRENT_PORT" = "8080" ]; then
        # Update to 8001
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' 's/^API_PORT=8080$/API_PORT=8001/' .env
        else
            # Linux
            sed -i 's/^API_PORT=8080$/API_PORT=8001/' .env
        fi
        echo "✅ Updated .env: Changed API_PORT from 8080 to 8001"
    elif [ -z "$CURRENT_PORT" ]; then
        # Add API_PORT if not present
        echo "API_PORT=8001" >> .env
        echo "✅ Added API_PORT=8001 to .env"
    else
        echo "⚠️  API_PORT is already set to $CURRENT_PORT in .env"
        echo "   To change it, edit .env manually"
    fi
else
    echo "📝 No .env file found. Creating one with API_PORT=8001..."
    echo "API_PORT=8001" > .env
    echo "✅ Created .env with API_PORT=8001"
fi

echo ""
echo "Current configuration:"
if [ -f .env ]; then
    grep "^API_PORT=" .env || echo "  API_PORT not in .env (will use config.py default: 8001)"
fi

