#!/bin/bash
# Script to kill all Python/uvicorn processes that might be holding ports

echo "🔍 Finding all uvicorn/python server processes..."

# Find all processes
PIDS=$(pgrep -f "uvicorn|main.py|api.main" 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "✅ No server processes found"
    exit 0
fi

echo "Found processes: $PIDS"
for pid in $PIDS; do
    echo "   Killing PID $pid ($(ps -p $pid -o command= 2>/dev/null | head -1))..."
    kill -9 $pid 2>/dev/null
done

sleep 2

# Check ports 8000, 8001, 8080
for port in 8000 8001 8080; do
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "   Killing process $PID on port $port..."
        kill -9 $PID 2>/dev/null
    fi
done

sleep 1
echo "✅ All server processes killed"

