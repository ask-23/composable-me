#!/bin/bash
# Run the Hydra web application (backend + frontend)
# Usage: ./web/run.sh [backend|frontend|both]

cd "$(dirname "$0")/.." || exit 1

MODE="${1:-both}"

run_backend() {
    echo "Starting Litestar backend on http://localhost:8000..."
    source .venv/bin/activate 2>/dev/null || true
    # Source .env file if it exists to load API keys
    if [ -f .env ]; then
        set -a
        source .env
        set +a
        echo "Loaded environment from .env"
    fi
    export PYTHONPATH="${PWD}:${PYTHONPATH}"
    pip install -q litestar uvicorn pydantic python-multipart sse-starlette python-dotenv 2>/dev/null
    python -m uvicorn web.backend.app:app --host 0.0.0.0 --port 8000 --reload
}

run_frontend() {
    echo "Starting Astro frontend on http://localhost:4321..."
    cd web/frontend || exit 1
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev
}

case "$MODE" in
    backend)
        run_backend
        ;;
    frontend)
        run_frontend
        ;;
    both)
        echo "Starting both backend and frontend..."
        echo "Backend: http://localhost:8000"
        echo "Frontend: http://localhost:4321"
        echo ""
        echo "Press Ctrl+C to stop both."
        echo ""

        # Run backend in background
        run_backend &
        BACKEND_PID=$!

        # Wait for backend to start
        sleep 2

        # Run frontend (foreground)
        run_frontend

        # Clean up backend on exit
        kill $BACKEND_PID 2>/dev/null
        ;;
    *)
        echo "Usage: $0 [backend|frontend|both]"
        exit 1
        ;;
esac
