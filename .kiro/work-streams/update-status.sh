#!/bin/bash
# Helper script to update work stream status
# Usage: ./update-status.sh <stream-name> <status> [current-task]

set -e

STREAM_NAME=$1
STATUS=$2
CURRENT_TASK=${3:-""}

if [ -z "$STREAM_NAME" ] || [ -z "$STATUS" ]; then
    echo "Usage: ./update-status.sh <stream-name> <status> [current-task]"
    echo ""
    echo "Examples:"
    echo "  ./update-status.sh stream-b-codex in_progress 'Reading requirements'"
    echo "  ./update-status.sh stream-b-codex completed"
    echo ""
    echo "Valid statuses: not_started, in_progress, blocked, completed"
    exit 1
fi

STATUS_FILE=".kiro/work-streams/${STREAM_NAME}/status.json"

if [ ! -f "$STATUS_FILE" ]; then
    echo "Error: Status file not found: $STATUS_FILE"
    exit 1
fi

# Get current timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Read current status file
CURRENT_STATUS=$(cat "$STATUS_FILE")

# Update status using jq (if available) or manual sed
if command -v jq &> /dev/null; then
    # Use jq for clean JSON manipulation
    UPDATED=$(echo "$CURRENT_STATUS" | jq \
        --arg status "$STATUS" \
        --arg timestamp "$TIMESTAMP" \
        --arg task "$CURRENT_TASK" \
        '.status = $status | .last_updated = $timestamp | (if $task != "" then .current_task = $task else . end)')
    
    # Add started_at if transitioning to in_progress
    if [ "$STATUS" = "in_progress" ]; then
        UPDATED=$(echo "$UPDATED" | jq \
            --arg timestamp "$TIMESTAMP" \
            'if .started_at == null then .started_at = $timestamp else . end')
    fi
    
    # Add completed_at if transitioning to completed
    if [ "$STATUS" = "completed" ]; then
        UPDATED=$(echo "$UPDATED" | jq \
            --arg timestamp "$TIMESTAMP" \
            '.completed_at = $timestamp | .progress = "100%"')
    fi
    
    echo "$UPDATED" > "$STATUS_FILE"
    echo "✅ Updated $STREAM_NAME status to: $STATUS"
    
else
    echo "⚠️  jq not found. Please update $STATUS_FILE manually."
    echo "Set status to: $STATUS"
    echo "Set last_updated to: $TIMESTAMP"
    exit 1
fi

# Show current status
echo ""
echo "Current status:"
cat "$STATUS_FILE" | jq '.'
