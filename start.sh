#!/bin/bash

# Co-Pilot SE - Startup Script
# Starts both backend API server and frontend development server

set -e

echo "========================================"
echo "🚀 Co-Pilot SE - Starting Application"
echo "========================================"
echo ""

# Check if Python virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found (.venv)"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed"
    echo "Please run: cd frontend && npm install"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "Please create .env file from .env.example and add your API keys"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start backend API server in background
echo "📡 Starting Backend API Server..."
.venv/bin/python api/server.py > api_server.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Backend URL: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Logs: api_server.log"

# Wait for backend to start
echo "   Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Start frontend development server
echo "🎨 Starting Frontend Development Server..."
(cd frontend && npm run dev) > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
echo "   Frontend URL: http://localhost:5173"
echo "   Logs: frontend.log"

echo ""
echo "========================================"
echo "✅ Application Started Successfully!"
echo "========================================"
echo ""
echo "🌐 Web Portal: http://localhost:5173"
echo "📡 API Server: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for both processes
wait
