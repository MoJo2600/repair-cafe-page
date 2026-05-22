#!/bin/bash

# Development Startup Script for Repair Cafe
# This script starts both the Vue frontend and Flask backend

echo "🚀 Starting Repair Cafe Development Environment..."
echo ""

# Check if node_modules exists in frontend folder
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 node_modules not found. Installing dependencies..."
    cd frontend && pnpm install && cd ..
    echo ""
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $VITE_PID $FLASK_PID 2>/dev/null
    exit 0
}

# Trap CTRL+C and call cleanup
trap cleanup INT TERM

echo "🎨 Starting Vite dev server (Vue frontend)..."
cd frontend && pnpm dev &
VITE_PID=$!
cd ..

# Wait a bit for Vite to start
sleep 3

echo "🐍 Starting Flask server (backend)..."
cd app && python run.py &
FLASK_PID=$!

echo ""
echo "✅ Development servers started!"
echo ""
echo "📱 Frontend (Vue): http://localhost:5173"
echo "🔧 Backend (Flask): http://localhost:8088 (or 5000)"
echo "🔗 Vue App via Flask: http://localhost:8088/vue (after adding route)"
echo ""
echo "Press CTRL+C to stop all servers"
echo ""

# Wait for background processes
wait
