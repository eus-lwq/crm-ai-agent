#!/bin/bash
# Script to kill process on a specific port

PORT=${1:-8000}

echo "Checking for processes on port $PORT..."

PID=$(lsof -ti:$PORT)

if [ -z "$PID" ]; then
    echo "No process found on port $PORT"
    exit 0
fi

echo "Found process $PID on port $PORT"
echo "Killing process..."
kill -9 $PID
echo "✅ Process killed"

