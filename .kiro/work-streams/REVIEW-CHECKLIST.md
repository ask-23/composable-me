# Stream Completion Review Checklist

This checklist is automatically triggered when a stream creates `completed/DONE.md`.

## Review Process

### 1. Read DONE.md
- [ ] Understand what was built
- [ ] Check claimed deliverables
- [ ] Note any caveats or issues mentioned

### 2. Verify Deliverables Exist
- [ ] Agent implementation file exists
- [ ] Agent prompt file exists
- [ ] Test file exists
- [ ] All files in `completed/` directory

### 3. Run Tests
```bash
.venv/bin/pytest tests/unit/test_{agent_name}.py -v
```
- [ ] All tests pass
- [ ] No test failures
- [ ] Coverage is reasonable

### 4. Code Quality Check
- [ ] Extends `BaseHydraAgent` correctly
- [ ] Implements `execute()` method
- [ ] Implements `_validate_schema()` method
- [ ] Has proper error handling
- [ ] Follows existing patterns

### 5. Interface Compliance
- [ ] Output includes base fields: `agent`, `timestamp`, `confidence`
- [ ] Output matches interface spec from `agent-interfaces.md`
- [ ] YAML format is valid
- [ ] Required fields present

### 6. Requirements Validation
- [ ] Addresses all assigned requirements
- [ ] Implements required functionality
- [ ] Follows truth laws (no fabrication)
- [ ] Handles edge cases

### 7. Decision

**If all checks pass:**
1. Integrate code into main codebase
2. Update stream status to "integrated"
3. Notify dependent streams
4. Mark tasks complete

**If issues found:**
1. Create `stream-X/integration-issues.md` with specific fixes
2. Update stream status to "needs_fixes"
3. Wait for fixes
4. Re-review when updated

## Common Issues to Check

- [ ] Test data missing base fields (`agent`, `timestamp`, `confidence`)
- [ ] Float comparisons using `assertEqual` instead of `assertAlmostEqual`
- [ ] Status.json not updated to `completed`
- [ ] Code not in `completed/` directory
- [ ] DONE.md missing or incomplete
- [ ] Tests not covering edge cases
- [ ] YAML validation not implemented
- [ ] Error handling missing

## Integration Steps (if approved)

1. Copy code from `stream-X/completed/` to main codebase:
   - `completed/agents/{agent}/*.py` → `runtime/crewai/agents/`
   - `completed/tests/*.py` → `tests/unit/`
   - `completed/agents/{agent}/prompt.md` → `agents/{agent}/`

2. Run full test suite:
   ```bash
   .venv/bin/pytest tests/unit/ -v
   ```

3. Commit with message:
   ```
   Integrate Stream X: {Agent Name}
   
   - Implements {requirements}
   - All tests passing
   - Reviewed and approved
   ```

4. Update dependency tracking
5. Notify dependent streams
