#!/bin/bash
# Composable Me Hydra — Run Script
#
# Usage:
#   ./run.sh --jd examples/sample_jd.md \
#            --resume examples/sample_resume.md \
#            --sources sources/ \
#            --out output/
#
# Environment:
#   OPENROUTER_API_KEY: Required
#   OPENROUTER_MODEL: Optional (default: anthropic/claude-3.5-sonnet)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY not set"
    echo ""
    echo "Get a key from https://openrouter.ai/keys"
    echo "Then run:"
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
echo "Model: ${OPENROUTER_MODEL:-anthropic/claude-3.5-sonnet}"
echo "============================================================"
echo ""

python runtime/crewai/cli.py "$@"
