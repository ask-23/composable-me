# Stream H+I Work Package - CLI & Integration

**Assigned to:** Codex  
**Status:** Ready to start  
**Priority:** HIGH - Required for production

---

## Summary

You're building the final pieces to make Composable Me usable:
1. **CLI interface** - So users can actually run it
2. **Integration tests** - To verify the whole thing works end-to-end

**All the hard work is done** - all 6 agents are built, tested, and integrated. You're just wiring them up!

---

## What's Complete

✅ All 6 agents implemented and tested (117 tests passing)  
✅ HydraWorkflow orchestrator with state machine  
✅ Audit retry loop (max 2 retries)  
✅ Error recovery and logging  

---

## Your Tasks

### 1. CLI Interface (Task 18) - REQUIRED

Create `runtime/crewai/cli.py` and `run.sh` so users can run:

```bash
./run.sh --jd examples/sample_jd.md \
         --resume examples/sample_resume.md \
         --sources sources/ \
         --out output/
```

**What it should do:**
- Parse command-line arguments
- Load input files
- Initialize and execute HydraWorkflow
- Save outputs (resume, cover letter, audit report)
- Display progress to user

### 2. Integration Tests (Task 19) - REQUIRED

Create `tests/integration/test_full_workflow.py` with:
- Happy path test (JD + resume → approved documents)
- Audit retry test (fail → fix → pass)
- Error recovery test (agent failure → graceful handling)

**Important:** Test the REAL workflow, not mocked!

### 3. Test Fixtures (Task 16) - OPTIONAL

Only if you have time:
- `tests/fixtures/sample_jds.py`
- `tests/fixtures/sample_resumes.py`
- `tests/fixtures/mock_llm.py`

---

## Key Files

**Use these:**
- `runtime/crewai/hydra_workflow.py` - The orchestrator (already done!)
- `runtime/crewai/llm_client.py` - LLM initialization
- `runtime/crewai/agents/*.py` - All agents (already done!)

**Reference these:**
- `.kiro/work-streams/stream-h-i-codex/assigned.md` - Detailed instructions
- `.kiro/specs/composable-crew/requirements.md` - Requirements
- `examples/sample_jd.md` - Example input

---

## Don't Do This

❌ Don't reimplement agents  
❌ Don't reimplement HydraWorkflow  
❌ Don't create a new Commander  
❌ Don't mock the workflow in integration tests  

---

## Estimated Time

- CLI: 2-3 hours
- Integration tests: 2-3 hours
- Optional fixtures: 1-2 hours

**Total: 4-8 hours**

---

**See `assigned.md` for detailed implementation guidance!**
