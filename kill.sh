#!/bin/bash

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
