#!/bin/bash
# Script to start the FastAPI server, killing any existing process first

PORT=${1:-8001}

echo "🚀 Starting CRM AI Agent server on port $PORT..."

# Kill any uvicorn/python processes that might be using the port
echo "🔍 Checking for existing processes..."
PIDS=$(pgrep -f "uvicorn|main.py|api.main" 2>/dev/null)
if [ ! -z "$PIDS" ]; then
    echo "⚠️  Found Python processes: $PIDS"
    for pid in $PIDS; do
        # Kill the process and all its children
        echo "   Killing PID $pid and children..."
        pkill -9 -P $pid 2>/dev/null  # Kill children first
        kill -9 $pid 2>/dev/null      # Then kill parent
    done
    sleep 3
fi

# Kill any process on the specific port
PID=$(lsof -ti:$PORT 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "⚠️  Found process $PID on port $PORT, killing it..."
    kill -9 $PID 2>/dev/null
    sleep 2
fi

# Double check port is free
if lsof -ti:$PORT 2>/dev/null; then
    echo "❌ Port $PORT is still in use. Force killing..."
    lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null
    sleep 3
fi

# Final check
if lsof -ti:$PORT 2>/dev/null; then
    echo "❌ ERROR: Port $PORT is still in use after cleanup attempts"
    echo "   Please manually kill the process:"
    echo "   lsof -i:$PORT"
    echo "   kill -9 \$(lsof -ti:$PORT)"
    exit 1
fi

# Start the server
echo "✅ Port $PORT is free. Starting server..."
cd "$(dirname "$0")/.."
uv run python main.py

