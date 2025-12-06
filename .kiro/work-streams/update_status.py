#!/usr/bin/env python3
"""
Helper script to update work stream status.json files.

Usage:
    python update_status.py <stream-name> <status> [--task "current task"] [--add-completed "task"]
    
Examples:
    python update_status.py stream-b-codex in_progress --task "Reading requirements"
    python update_status.py stream-b-codex in_progress --add-completed "Created agent class"
    python update_status.py stream-b-codex completed
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def update_status(
    stream_name: str,
    status: str,
    current_task: Optional[str] = None,
    add_completed_task: Optional[str] = None,
    progress: Optional[str] = None
) -> None:
    """
    Update the status.json file for a work stream.
    
    Args:
        stream_name: Name of the stream (e.g., "stream-b-codex")
        status: New status (not_started, in_progress, blocked, completed)
        current_task: Optional current task description
        add_completed_task: Optional task to add to completed_tasks
        progress: Optional progress percentage (e.g., "45%")
    """
    valid_statuses = ["not_started", "in_progress", "blocked", "completed"]
    if status not in valid_statuses:
        print(f"❌ Error: Invalid status '{status}'")
        print(f"Valid statuses: {', '.join(valid_statuses)}")
        sys.exit(1)
    
    status_file = Path(f".kiro/work-streams/{stream_name}/status.json")
    
    if not status_file.exists():
        print(f"❌ Error: Status file not found: {status_file}")
        sys.exit(1)
    
    # Read current status
    with open(status_file, 'r') as f:
        data = json.load(f)
    
    # Update fields
    timestamp = get_timestamp()
    data["status"] = status
    data["last_updated"] = timestamp
    
    # Set started_at if transitioning to in_progress
    if status == "in_progress" and data.get("started_at") is None:
        data["started_at"] = timestamp
    
    # Set completed_at if transitioning to completed
    if status == "completed":
        data["completed_at"] = timestamp
        data["progress"] = "100%"
        data["current_task"] = "Work complete"
    
    # Update current task if provided
    if current_task:
        data["current_task"] = current_task
    
    # Add completed task if provided
    if add_completed_task:
        if "completed_tasks" not in data:
            data["completed_tasks"] = []
        if add_completed_task not in data["completed_tasks"]:
            data["completed_tasks"].append(add_completed_task)
    
    # Update progress if provided
    if progress:
        data["progress"] = progress
    
    # Write updated status
    with open(status_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Updated {stream_name} status to: {status}")
    
    if current_task:
        print(f"   Current task: {current_task}")
    
    if add_completed_task:
        print(f"   Added completed task: {add_completed_task}")
    
    print(f"\nCurrent status:")
    print(json.dumps(data, indent=2))


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    stream_name = sys.argv[1]
    status = sys.argv[2]
    
    # Parse optional arguments
    current_task = None
    add_completed_task = None
    progress = None
    
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--task" and i + 1 < len(sys.argv):
            current_task = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--add-completed" and i + 1 < len(sys.argv):
            add_completed_task = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--progress" and i + 1 < len(sys.argv):
            progress = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    update_status(stream_name, status, current_task, add_completed_task, progress)


if __name__ == "__main__":
    main()
