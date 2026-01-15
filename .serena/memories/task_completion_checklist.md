# Task Completion Checklist

## Before Committing Code

### 1. Run Tests
```bash
# Unit tests with coverage
pytest

# Check for failures
pytest --tb=short
```

### 2. Type Checking (Frontend)
```bash
cd web/frontend
npm run check
```

### 3. Pre-commit Hooks
The Husky pre-commit hook automatically runs on `git commit` and checks:
- PII patterns (email addresses)
- Console.log with potential PII
- Temporary/scratch files
- Linter (if configured)
- Formatter (if configured)

Note: Hooks warn but don't block commits.

## After Modifying Agents

1. Ensure agent extends `BaseHydraAgent`
2. Implement required methods: `create_task()`, `validate_output()`
3. Update agent prompt if behavior changed: `agents/<name>/prompt.md`
4. Run relevant test: `pytest tests/test_<agent>.py`

## After Modifying Models

1. Update dataclass in `runtime/crewai/models.py`
2. Add `__post_init__` validation if needed
3. Update any agents that use the model
4. Run tests: `pytest`

## After Modifying Web Interface

### Backend
```bash
cd web/backend
# Run backend to verify
./run.sh
```

### Frontend
```bash
cd web/frontend
npm run check           # TypeScript
npm run test:e2e        # E2E tests
npm run build           # Verify build
```

## Code Quality Standards

- No hardcoded API keys (use environment variables)
- All agent outputs must be validated
- Follow truth rules in `docs/AGENTS.MD`
- Follow style guide in `docs/STYLE_GUIDE.MD`
- Confidence scores must be 0.0-1.0

## Common Test Markers
```bash
pytest -m unit         # Unit tests only
pytest -m integration  # Integration tests only
pytest -m slow         # Slow tests
pytest -m property     # Property-based tests
```
