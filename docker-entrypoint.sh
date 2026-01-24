#!/bin/bash
# =============================================================================
# Docker Entrypoint for Hydra Application
# Starts both backend and frontend services
# =============================================================================

set -e

echo "🐉 Starting Hydra Multi-Agent Application..."

# Start the Python backend in the background
echo "Starting backend on http://0.0.0.0:8000..."
cd /app
python -m uvicorn web.backend.app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# Start the Node.js frontend
echo "Starting frontend on http://0.0.0.0:4321..."
cd /app/web/frontend
HOST=0.0.0.0 PORT=4321 node ./dist/server/entry.mjs &
FRONTEND_PID=$!

echo ""
echo "========================================="
echo "🐉 Hydra is running!"
echo "   Frontend: http://localhost:4321"
echo "   Backend:  http://localhost:8000"
echo "========================================="
echo ""

# Handle shutdown gracefully (use numeric signals for better compatibility)
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup 15 2

# Keep the container running by waiting on both processes
wait $BACKEND_PID $FRONTEND_PID
