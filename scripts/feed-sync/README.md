# Hydra Feed Sync

A standalone utility to sync job feed JSON files from pCloud to the local Hydra inputs directory.

## Overview

This utility polls a pCloud public folder, detects new job feed files, downloads them, and places them where Hydra can consume them. It tracks processed files using pCloud's content hash to avoid duplicates.

## Quick Start

```bash
# Check for new files (dry run)
python scripts/feed-sync/hydra-feed-sync.py check

# Download new files
python scripts/feed-sync/hydra-feed-sync.py sync

# Show status
python scripts/feed-sync/hydra-feed-sync.py status
```

## Commands

| Command | Description |
|---------|-------------|
| `sync` | Download new files from pCloud |
| `sync --dry-run` | Check what would be downloaded |
| `check` | Alias for `sync --dry-run` |
| `status` | Show sync status and recent files |
| `reset` | Clear state to re-download all files |

## How It Works

1. **List**: Calls pCloud API to list folder contents
2. **Detect**: Compares file hashes against processed files
3. **Download**: Fetches new files via direct download URL
4. **Save**: Stores files with date-based names in `inputs/hydra_job_feed/`
5. **Track**: Updates state file to prevent re-downloading

## File Locations

| File | Path |
|------|------|
| Downloaded feeds | `inputs/hydra_job_feed/*.json` |
| State file | `~/.hydra-feed-sync/state.json` |
| Log file | `~/.hydra-feed-sync/sync.log` |

## Scheduling

### macOS (launchd)

Create `~/Library/LaunchAgents/com.hydra.feedsync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hydra.feedsync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/admin/git/composable-crew/scripts/feed-sync/hydra-feed-sync.py</string>
        <string>sync</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/admin/.hydra-feed-sync/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/admin/.hydra-feed-sync/launchd.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.hydra.feedsync.plist
```

### Linux (cron)

```bash
# Edit crontab
crontab -e

# Add daily sync at 8 AM
0 8 * * * /usr/bin/python3 /path/to/composable-crew/scripts/feed-sync/hydra-feed-sync.py sync
```

## Configuration

Edit the constants at the top of `hydra-feed-sync.py`:

```python
PCLOUD_CODE = "kZDIsaZG6KHH3wKDc7e7mtzQovQTHLwCe9y"  # pCloud share code
OUTPUT_DIR = Path("...") / "inputs" / "hydra_job_feed"  # Where to save files
```

## Integration with Hydra

After syncing, the files appear in `inputs/hydra_job_feed/`. You can:

1. **Manual**: Upload via Hydra web UI file picker
2. **CLI**: Process directly with `./run.sh --jd inputs/hydra_job_feed/2026-01-26.json ...`

## Troubleshooting

**"All files already processed"**  
This is normal - the sync only downloads new files. Run `reset` if you want to re-download.

**Network errors**  
Check your internet connection. The script will retry on the next run.

**Invalid JSON errors**  
The source file may be corrupted. Check the pCloud folder.
