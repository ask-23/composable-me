#!/bin/bash
# Run the Hydra web backend

# Ensure we're in the project root for imports
cd "$(dirname "$0")/../.." || exit 1

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Source environment variables (API keys)
ENV_FILES=()
if [ -f ".env" ]; then
    ENV_FILES+=(".env")
fi
if [ -f "a.env" ]; then
    ENV_FILES+=("a.env")
fi
if [ ${#ENV_FILES[@]} -gt 0 ]; then
    set -a
    for ENV_FILE in "${ENV_FILES[@]}"; do
        # shellcheck disable=SC1090
        source "$ENV_FILE"
    done
    set +a
fi

# Default Postgres connection for Hydra persistence.
export HYDRA_DATABASE_URL="${HYDRA_DATABASE_URL:-postgresql://hydra:hydra@localhost:5432/hydra}"

# Set PYTHONPATH to include project root
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Install backend dependencies if needed
pip install -q litestar uvicorn pydantic python-multipart sse-starlette python-dotenv "psycopg[binary]" 2>/dev/null

# Run the server
echo "Starting Hydra API server on http://localhost:8000"
echo "API docs: http://localhost:8000/schema"
python -m uvicorn web.backend.app:app --host 0.0.0.0 --port 8000 --reload
