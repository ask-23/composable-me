#!/usr/bin/env python3
"""
Hydra Feed Sync - pCloud Job Feed Synchronization Utility

Downloads job feed JSON files from a pCloud public folder and places them
where Hydra can consume them. Tracks processed files to avoid duplicates.

Usage:
    python hydra-feed-sync.py sync      # Download new files
    python hydra-feed-sync.py check     # Check for new files without downloading
    python hydra-feed-sync.py status    # Show sync status
    python hydra-feed-sync.py reset     # Reset state (re-download everything)
"""

import argparse
import hashlib
import json
import logging
import re
import ssl
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# SSL context for HTTPS requests (handles macOS certificate issues)
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    # Fallback: create unverified context (less secure but works)
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# =============================================================================
# Configuration
# =============================================================================

# pCloud public link code (from the share URL)
PCLOUD_CODE = "kZDIsaZG6KHH3wKDc7e7mtzQovQTHLwCe9y"

# pCloud API base URL (EU datacenter based on 'e' prefix in link)
PCLOUD_API_BASE = "https://eapi.pcloud.com"

# Where to save downloaded files
OUTPUT_DIR = Path(__file__).parent.parent.parent / "inputs" / "hydra_job_feed"

# State file to track processed files
STATE_DIR = Path.home() / ".hydra-feed-sync"
STATE_FILE = STATE_DIR / "state.json"

# Logging
LOG_FILE = STATE_DIR / "sync.log"
LOG_LEVEL = logging.INFO

# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging() -> logging.Logger:
    """Configure logging to both file and console."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("hydra-feed-sync")
    logger.setLevel(LOG_LEVEL)
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(LOG_LEVEL)
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)
    
    return logger

log = setup_logging()

# =============================================================================
# pCloud API Functions
# =============================================================================

def api_call(endpoint: str, **params) -> dict[str, Any]:
    """Make a pCloud API call and return JSON response."""
    url = f"{PCLOUD_API_BASE}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    
    log.debug(f"API call: {url}")
    
    try:
        req = Request(url, headers={"User-Agent": "HydraFeedSync/1.0"})
        with urlopen(req, timeout=30, context=SSL_CONTEXT) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        if data.get("result") != 0:
            error_msg = data.get("error", "Unknown error")
            raise RuntimeError(f"pCloud API error: {error_msg}")
            
        return data
    except HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def list_folder(code: str) -> dict[str, Any]:
    """List contents of a pCloud public folder."""
    return api_call("showpublink", code=code)


def get_download_url(code: str, fileid: int) -> str:
    """Get direct download URL for a file in a public folder."""
    data = api_call("getpublinkdownload", code=code, fileid=fileid)
    
    host = data["hosts"][0]
    path = data["path"]
    
    return f"https://{host}{path}"


def download_file(url: str, destination: Path) -> None:
    """Download a file from URL to destination path."""
    log.debug(f"Downloading: {url}")
    
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    req = Request(url, headers={"User-Agent": "HydraFeedSync/1.0"})
    with urlopen(req, timeout=60, context=SSL_CONTEXT) as response:
        content = response.read()
        
    # Validate JSON before saving
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Downloaded file is not valid JSON: {e}")
    
    destination.write_bytes(content)
    log.debug(f"Saved to: {destination}")

# =============================================================================
# File Discovery
# =============================================================================

def find_json_files(metadata: dict[str, Any], parent_folder: str = "") -> list[dict[str, Any]]:
    """Recursively find all .json files in folder metadata."""
    files = []
    
    contents = metadata.get("contents", [])
    for item in contents:
        if item.get("isfolder"):
            # Recurse into subfolder
            folder_name = item.get("name", "")
            files.extend(find_json_files(item, folder_name))
        else:
            # Check if it's a JSON file
            name = item.get("name", "")
            if name.lower().endswith(".json"):
                files.append({
                    "name": name,
                    "fileid": item.get("fileid"),
                    "hash": item.get("hash"),
                    "size": item.get("size"),
                    "modified": item.get("modified"),
                    "parent_folder": parent_folder,
                })
    
    return files


def parse_date_from_folder(folder_name: str) -> str:
    """Extract date from folder name like '1 file from hydra feed from agent on Jan 26, 2026'."""
    # Pattern: "... on Month DD, YYYY"
    pattern = r"on\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})"
    match = re.search(pattern, folder_name)
    
    if match:
        month_str, day, year = match.groups()
        try:
            dt = datetime.strptime(f"{month_str} {day} {year}", "%b %d %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Fallback: use today's date
    return datetime.now().strftime("%Y-%m-%d")

# =============================================================================
# State Management
# =============================================================================

def load_state() -> dict[str, Any]:
    """Load sync state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            log.warning("Corrupted state file, starting fresh")
    
    return {
        "processed_hashes": [],
        "last_run": None,
        "files_downloaded": 0,
    }


def save_state(state: dict[str, Any]) -> None:
    """Save sync state to file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))

# =============================================================================
# Main Commands
# =============================================================================

def cmd_sync(dry_run: bool = False) -> int:
    """Sync new files from pCloud."""
    log.info("🔄 Checking pCloud for new job feeds...")
    
    try:
        # List folder contents
        data = list_folder(PCLOUD_CODE)
        metadata = data.get("metadata", {})
        json_files = find_json_files(metadata)
        
        if not json_files:
            log.info("📭 No JSON files found in pCloud folder")
            return 0
        
        log.info(f"📁 Found {len(json_files)} JSON file(s) in pCloud")
        
        # Load state
        state = load_state()
        processed = set(state.get("processed_hashes", []))
        
        # Find new files
        new_files = [f for f in json_files if f["hash"] not in processed]
        
        if not new_files:
            log.info("✅ All files already processed - nothing new to download")
            return 0
        
        log.info(f"🆕 {len(new_files)} new file(s) to download")
        
        if dry_run:
            for f in new_files:
                log.info(f"  Would download: {f['parent_folder']}/{f['name']}")
            return 0
        
        # Download new files
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        downloaded = 0
        
        for f in new_files:
            try:
                # Generate output filename from folder date
                date_str = parse_date_from_folder(f["parent_folder"])
                output_path = OUTPUT_DIR / f"{date_str}.json"
                
                # Handle duplicates (append counter if file exists)
                if output_path.exists():
                    counter = 1
                    while output_path.exists():
                        output_path = OUTPUT_DIR / f"{date_str}_{counter}.json"
                        counter += 1
                
                log.info(f"⬇️  Downloading: {f['parent_folder']}/{f['name']}")
                
                url = get_download_url(PCLOUD_CODE, f["fileid"])
                download_file(url, output_path)
                
                # Update state
                state["processed_hashes"].append(f["hash"])
                downloaded += 1
                
                log.info(f"   ✓ Saved to: {output_path.name}")
                
            except Exception as e:
                log.error(f"   ✗ Failed: {e}")
        
        # Save state
        state["files_downloaded"] = state.get("files_downloaded", 0) + downloaded
        save_state(state)
        
        log.info(f"✅ Sync complete: {downloaded} file(s) downloaded")
        return 0
        
    except Exception as e:
        log.error(f"❌ Sync failed: {e}")
        return 1


def cmd_check() -> int:
    """Check for new files without downloading."""
    return cmd_sync(dry_run=True)


def cmd_status() -> int:
    """Show current sync status."""
    state = load_state()
    
    log.info("📊 Hydra Feed Sync Status")
    log.info(f"   State file: {STATE_FILE}")
    log.info(f"   Output dir: {OUTPUT_DIR}")
    log.info(f"   Last run: {state.get('last_run', 'Never')}")
    log.info(f"   Files processed: {len(state.get('processed_hashes', []))}")
    log.info(f"   Total downloaded: {state.get('files_downloaded', 0)}")
    
    # List downloaded files
    if OUTPUT_DIR.exists():
        files = list(OUTPUT_DIR.glob("*.json"))
        log.info(f"   Local files: {len(files)}")
        for f in sorted(files)[-5:]:  # Show last 5
            log.info(f"      {f.name}")
    
    return 0


def cmd_reset() -> int:
    """Reset sync state."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        log.info("🗑️  State reset - next sync will re-download all files")
    else:
        log.info("ℹ️  No state file to reset")
    return 0

# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync job feed files from pCloud to Hydra",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # sync command
    sync_parser = subparsers.add_parser("sync", help="Download new files from pCloud")
    sync_parser.add_argument("--dry-run", action="store_true", help="Check only, don't download")
    
    # check command
    subparsers.add_parser("check", help="Check for new files without downloading")
    
    # status command
    subparsers.add_parser("status", help="Show sync status")
    
    # reset command
    subparsers.add_parser("reset", help="Reset state (re-download all files)")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        return cmd_sync(dry_run=args.dry_run)
    elif args.command == "check":
        return cmd_check()
    elif args.command == "status":
        return cmd_status()
    elif args.command == "reset":
        return cmd_reset()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
