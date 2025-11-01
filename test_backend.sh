#!/bin/bash

# Test Backend Server
# Simple script to start backend and test health endpoint

echo "🧪 Testing Backend Server"
echo "========================="
echo ""

# Start backend in background
echo "Starting backend server..."
/Users/robenhai/CoPilot-SE/.venv/bin/python /Users/robenhai/CoPilot-SE/api/server.py > /tmp/copilot_backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for startup
echo "Waiting 5 seconds for startup..."
sleep 5

# Test health endpoint
echo ""
echo "Testing /health endpoint:"
curl -s http://localhost:8000/health | python -m json.tool

echo ""
echo "Testing / endpoint:"
curl -s http://localhost:8000/ | python -m json.tool

echo ""
echo "Testing /docs endpoint:"
echo "Open in browser: http://localhost:8000/docs"

echo ""
echo "========================="
echo "✅ Backend server is running!"
echo "PID: $BACKEND_PID"
echo "Logs: /tmp/copilot_backend.log"
echo ""
echo "To stop: kill $BACKEND_PID"
echo "Or run: pkill -f 'python.*server.py'"
