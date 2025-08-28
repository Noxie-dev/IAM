#!/bin/bash

# IAM App Development Server Starter
# This script starts both the backend and frontend development servers

echo "🚀 Starting IAM App Development Environment..."
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "📦 Starting Flask backend server..."
cd iam-backend
source venv/bin/activate
python src/main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "⚛️  Starting React frontend server..."
cd iam-frontend
pnpm dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Development servers started!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
