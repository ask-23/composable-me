#!/bin/bash
# Composable Me Hydra — Run Script
#
# Usage:
#   ./run.sh --jd examples/sample_jd.md \
#            --resume examples/sample_resume.md \
#            --sources sources/ \
#            --out output/
#
# Environment (set at least one API key):
#   TOGETHER_API_KEY: Recommended (Together AI)
#   CHUTES_API_KEY: Alternative (Chutes.ai)
#   OPENROUTER_API_KEY: Alternative (OpenRouter)
# Optional model overrides:
#   TOGETHER_MODEL / CHUTES_MODEL / OPENROUTER_MODEL

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .env or a.env if present
ENV_FILES=()
if [ -f "$SCRIPT_DIR/.env" ]; then
    ENV_FILES+=("$SCRIPT_DIR/.env")
fi
if [ -f "$SCRIPT_DIR/a.env" ]; then
    ENV_FILES+=("$SCRIPT_DIR/a.env")
fi
if [ ${#ENV_FILES[@]} -gt 0 ]; then
    set -a
    for ENV_FILE in "${ENV_FILES[@]}"; do
        # shellcheck disable=SC1090
        source "$ENV_FILE"
    done
    set +a
fi

# Choose provider + model based on available keys (matches runtime/crewai/llm_client.py)
if [ -n "$TOGETHER_API_KEY" ]; then
    PROVIDER="Together AI"
    MODEL="${TOGETHER_MODEL:-${OPENROUTER_MODEL:-meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8}}"
elif [ -n "$CHUTES_API_KEY" ]; then
    PROVIDER="Chutes.ai"
    MODEL="${CHUTES_MODEL:-${OPENROUTER_MODEL:-deepseek-ai/DeepSeek-V3.1}}"
elif [ -n "$OPENROUTER_API_KEY" ]; then
    PROVIDER="OpenRouter"
    MODEL="${OPENROUTER_MODEL:-anthropic/claude-sonnet-4.5}"
else
    echo "ERROR: No LLM API key found."
    echo ""
    echo "Set one of:"
    echo "  export TOGETHER_API_KEY='tgp_v1_...'"
    echo "  export CHUTES_API_KEY='your-key'"
    echo "  export OPENROUTER_API_KEY='sk-or-...'"
    exit 1
fi

# Check args
# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install deps if needed
if ! python -c "import crewai" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "============================================================"
echo "COMPOSABLE ME HYDRA — Starting CLI"
echo "============================================================"
echo "Provider: ${PROVIDER}"
echo "Model: ${MODEL}"
echo "============================================================"
echo ""

python -m runtime.crewai.cli "$@"
