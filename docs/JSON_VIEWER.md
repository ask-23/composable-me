# Composable Crew JSON Viewer

A minimal, single-file utility for viewing JSON outputs from the Composable Crew agent pipeline in a human-readable format.

## Features

- **Drag & Drop**: Simply drag JSON files onto the page to view them
- **Collapsible Tree**: Navigate complex nested JSON structures easily
- **Syntax Highlighting**: Color-coded keys, strings, numbers, and booleans
- **Markdown Preview**: Toggle markdown rendering for long text fields (like resumes)
- **Zero Dependencies**: Pure HTML/CSS/JS, no build process required

## Usage

### Option 1: Open Directly

Simply open `json-viewer.html` in your web browser.

### Option 2: Serve Locally

For a better experience (and to avoid some browser file restrictions), use the included server script:

```bash
python3 serve_viewer.py
```

This will start a local server at `http://localhost:8000` and automatically open your default browser.

## Supported Outputs

The viewer is optimized for JSON outputs from all Composable Crew agents, including:

- **Gap Analyzer**: Requirements analysis and fit scoring
- **Tailoring Agent**: Generated resumes and cover letters
- **Auditor Suite**: Audit reports and compliance checks
- **Commander**: Workflow decisions and orchestration logs

## Development

The viewer is contained entirely within `json-viewer.html`. It follows the project's architectural principles:
1. **Embrace and extend**: Uses native browser JSON parsing and DOM manipulation
2. **Avoid addition**: No external libraries or frameworks
3. **Reuse, don't invent**: Leverages standard HTML5 Drag and Drop API