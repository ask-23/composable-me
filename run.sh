#!/bin/bash
# Composable Me Hydra — Run Script
#
# Usage:
#   ./run.sh examples/sample_jd.md examples/sample_resume.md
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
if [ $# -lt 2 ]; then
    echo "Usage: $0 <job_description.md> <resume.md> [interview_notes.md]"
    echo ""
    echo "Example:"
    echo "  $0 examples/sample_jd.md examples/sample_resume.md"
    exit 1
fi

JD="$1"
RESUME="$2"
NOTES="${3:-}"

# Check files exist
if [ ! -f "$JD" ]; then
    echo "ERROR: Job description not found: $JD"
    exit 1
fi

if [ ! -f "$RESUME" ]; then
    echo "ERROR: Resume not found: $RESUME"
    exit 1
fi

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

# Run the crew
echo ""
echo "============================================================"
echo "COMPOSABLE ME HYDRA — Starting CrewAI Pipeline"
echo "============================================================"
echo "JD: $JD"
echo "Resume: $RESUME"
echo "Notes: ${NOTES:-none}"
echo "Model: ${OPENROUTER_MODEL:-anthropic/claude-3.5-sonnet}"
echo "============================================================"
echo ""

if [ -n "$NOTES" ] && [ -f "$NOTES" ]; then
    python runtime/crewai/quick_crew.py --jd "$JD" --resume "$RESUME" --notes "$NOTES"
else
    python runtime/crewai/quick_crew.py --jd "$JD" --resume "$RESUME"
fi
