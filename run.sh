#!/bin/bash

# Start all services for ReviewGuide.ai
# Backend (FastAPI), Frontend (Next.js), and Redis
# Usage:
#   ./run.sh        - Start all services
#   ./run.sh clear  - Clear terminal before starting services
#   ./run.sh kill   - Kill all backend and frontend processes

# Check if "kill" argument is provided
if [ "$1" = "kill" ]; then
    echo "Killing all backend and frontend processes..."

    # Kill backend processes
    echo "Killing backend (uvicorn)..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true

    # Kill frontend processes
    echo "Killing frontend (Next.js)..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3001 | xargs kill -9 2>/dev/null || true
    lsof -ti:3002 | xargs kill -9 2>/dev/null || true
    lsof -ti:3003 | xargs kill -9 2>/dev/null || true
    lsof -ti:3004 | xargs kill -9 2>/dev/null || true
    pkill -9 -f "next dev" 2>/dev/null || true
    pkill -9 node 2>/dev/null || true

    # Kill Redis
    echo "Killing Redis..."
    pkill -9 redis-server 2>/dev/null || true

    echo "All processes killed."
    exit 0
fi

# Check if "clear" argument is provided
if [ "$1" = "clear" ]; then
    clear
fi

echo "Starting ReviewGuide.ai services..."

# Load port from .env file (default to 8000)
BACKEND_PORT=$(grep -E '^APP_PORT=' backend/.env 2>/dev/null | cut -d '=' -f2 || echo "8000")

# Kill any process running on backend port
echo "Checking for processes on port $BACKEND_PORT..."
lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:3000,3001,3002,3003,3004 | xargs kill -9 2>/dev/null || true
pkill -9 -f "next dev" 2>/dev/null || true
pkill -9 redis-server 2>/dev/null || true

# Check if redis-server is already running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server &
    REDIS_PID=$!
    sleep 2
else
    echo "Redis is already running"
    REDIS_PID=""
fi

# Start backend
echo "Starting Backend (FastAPI) on port $BACKEND_PORT..."
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting Frontend (Next.js)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================"
echo "All services started!"
echo "================================"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:$BACKEND_PORT"
echo "Redis:    localhost:6379"
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================"

# Trap Ctrl+C and stop all services
trap "echo 'Stopping all services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; [ -n '$REDIS_PID' ] && kill $REDIS_PID 2>/dev/null; exit" INT

# Wait for all background processes
wait
