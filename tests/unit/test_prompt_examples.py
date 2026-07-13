"""Structural checks on agent prompt files.

The Hydra agents are instructed to emit JSON, and the workflow's contract layer
(`runtime/crewai/contracts.py`) parses that JSON. These tests lock two invariants
on every ``agents/**/prompt.md``:

1. Every fenced ``json`` example block is valid JSON (so the prompts never model an
   output shape the parser would reject).
2. No fenced ``yaml`` block sits under a heading whose text contains "Output" — the
   authoritative output-schema examples must be JSON, not YAML.

These are static checks on the prompt text; they do not validate output *quality*.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILES = sorted((REPO_ROOT / "agents").glob("*/prompt.md"))

# Matches a fenced code block, capturing its language tag and body.
_FENCE = re.compile(r"^```(\w+)?\s*$")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$")


def _iter_blocks(text: str):
    """Yield (language, body, heading) for each fenced code block in ``text``.

    ``heading`` is the text of the nearest preceding markdown heading (or "").
    """
    current_heading = ""
    lang = None
    body_lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if in_fence:
            if line.strip() == "```":
                yield lang, "\n".join(body_lines), current_heading
                in_fence = False
                lang = None
                body_lines = []
            else:
                body_lines.append(line)
            continue
        fence = _FENCE.match(line)
        if fence:
            in_fence = True
            lang = (fence.group(1) or "").lower()
            body_lines = []
            continue
        heading = _HEADING.match(line)
        if heading:
            current_heading = heading.group(1).strip()


def test_prompt_files_discovered():
    assert PROMPT_FILES, "no agents/*/prompt.md files found"


def test_json_blocks_parse():
    """Every fenced json block in every agent prompt must be valid JSON."""
    failures = []
    for prompt in PROMPT_FILES:
        text = prompt.read_text()
        for index, (lang, body, _heading) in enumerate(_iter_blocks(text)):
            if lang != "json":
                continue
            try:
                json.loads(body)
            except json.JSONDecodeError as error:
                rel = prompt.relative_to(REPO_ROOT)
                failures.append(f"{rel} json block #{index}: {error}")
    assert not failures, "invalid JSON example blocks:\n" + "\n".join(failures)


def test_no_yaml_under_output_heading():
    """Output-schema blocks must be JSON: no yaml block under an 'Output' heading."""
    offenders = []
    for prompt in PROMPT_FILES:
        text = prompt.read_text()
        for lang, _body, heading in _iter_blocks(text):
            if lang == "yaml" and "output" in heading.lower():
                rel = prompt.relative_to(REPO_ROOT)
                offenders.append(f"{rel}: yaml block under heading '{heading}'")
    assert not offenders, "yaml output schemas must be JSON:\n" + "\n".join(offenders)
