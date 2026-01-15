# Suggested Commands

## Running the Application

### Main CLI (Recommended)
```bash
# Full workflow with file inputs
./run.sh --jd examples/sample_jd.md \
         --resume examples/sample_resume.md \
         --sources sources/ \
         --out output/

# Or run Python module directly
source .venv/bin/activate
python -m runtime.crewai.cli --jd <job.md> --resume <resume.md> --sources <dir> --out <dir>
```

### Quick Runner (Simplified)
```bash
python runtime/crewai/quick_crew.py --jd job.md --resume resume.md --out output.txt
```

## Environment Setup

### API Keys (priority order)
```bash
export ANTHROPIC_API_KEY='sk-ant-...'       # Primary (Claude models)
export TOGETHER_API_KEY='tgp_v1_...'        # Fallback (Llama models)
export CHUTES_API_KEY='cpk_...'             # Fallback (DeepSeek)
```

### Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Testing

### Unit Tests
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_gap_analyzer.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### E2E Tests (Frontend)
```bash
cd web/frontend
npm run test:e2e           # Headless
npm run test:e2e:headed    # With browser
npm run test:e2e:ui        # Interactive UI
```

## Web Interface

### Start Backend
```bash
cd web/backend
./run.sh
# Or: PYTHONPATH=/Users/admin/git/composable-crew uvicorn app:app --reload
```

### Start Frontend
```bash
cd web/frontend
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
npm run check    # TypeScript check
```

## Development

### Code Quality
```bash
# Husky pre-commit hooks run automatically on git commit
# They check for PII, temporary files, and run linters
```

### Git Operations
```bash
git status
git diff
git log --oneline -10
```

## macOS (Darwin) System Commands
```bash
ls -la              # List files with details
find . -name "*.py" # Find Python files
grep -r "pattern" . # Search in files
cd <directory>      # Change directory
cat <file>          # View file contents
```
