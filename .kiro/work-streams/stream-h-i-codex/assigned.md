# Stream H+I: CLI & Testing Infrastructure - Assigned to Codex

**Date:** December 6, 2025  
**Agent:** Codex  
**Status:** Ready to start

---

## Overview

This work package combines the remaining tasks needed to make the Composable Me system production-ready:
1. **CLI Interface** - Command-line interface for running the workflow
2. **Integration Tests** - End-to-end testing of the complete pipeline
3. **Testing Infrastructure** - Fixtures and test utilities (optional)

---

## What's Already Complete

✅ **All 6 Agents Implemented:**
- Gap Analyzer
- Interrogator-Prepper
- Differentiator
- Tailoring Agent
- ATS Optimizer
- Auditor Suite

✅ **Workflow Orchestration:**
- HydraWorkflow class with state machine
- Audit retry loop (max 2 retries)
- Error recovery

✅ **117 Tests Passing:**
- 38 infrastructure tests
- 79 agent tests
- 100% pass rate

---

## Your Tasks

### Task 18: CLI Interface (REQUIRED)

**Goal:** Create a command-line interface to run the workflow

**Deliverables:**

1. **`run.sh` script**
   - Check for required environment variables (OPENROUTER_API_KEY)
   - Create virtual environment if needed
   - Install dependencies
   - Execute the workflow
   - Handle errors gracefully

2. **`runtime/crewai/cli.py`** (or similar)
   - Parse command-line arguments:
     - `--jd <path>` - Job description file
     - `--resume <path>` - Resume file
     - `--sources <path>` - Source documents directory
     - `--out <path>` - Output directory
   - Load input files
   - Initialize HydraWorkflow
   - Execute workflow
   - Save outputs (resume, cover letter, audit report)
   - Display results to console

3. **Example usage:**
   ```bash
   ./run.sh --jd examples/sample_jd.md \
            --resume examples/sample_resume.md \
            --sources sources/ \
            --out output/
   ```

**Requirements:**
- Must use existing HydraWorkflow class
- Must handle file I/O errors
- Must display progress to user
- Must save all outputs (resume, cover letter, audit report)

---

### Task 19: Integration Tests (REQUIRED)

**Goal:** Test the complete end-to-end workflow

**Deliverables:**

1. **`tests/integration/test_full_workflow.py`**
   - Test happy path (JD + resume → approved documents)
   - Test audit retry path (fail → fix → pass)
   - Test error recovery (agent failure → graceful degradation)
   - Use real agent execution (not mocked)
   - Verify final outputs are complete

2. **Test scenarios:**
   - ✅ Complete workflow with valid inputs
   - ✅ Workflow with audit failures that get fixed
   - ✅ Workflow with agent errors
   - ✅ Workflow with missing optional data

**Requirements:**
- Must test actual HydraWorkflow execution
- Must verify all 6 agents execute in order
- Must verify audit retry loop works
- Must verify final documents are generated

---

### Task 16: Testing Infrastructure (OPTIONAL)

**Goal:** Create reusable test fixtures and utilities

**Deliverables:**

1. **`tests/fixtures/sample_jds.py`**
   - Collection of diverse job descriptions
   - Different roles, levels, industries
   - Edge cases (vague JDs, missing info)

2. **`tests/fixtures/sample_resumes.py`**
   - Collection of test resumes
   - Different experience levels
   - Different formats

3. **`tests/fixtures/mock_llm.py`**
   - Mock LLM responses for testing
   - Reusable across all tests

**Note:** This is optional - only do if you have time after Tasks 18 & 19.

---

## Implementation Notes

### CLI Design

The CLI should be simple and straightforward:

```python
# runtime/crewai/cli.py
import argparse
from pathlib import Path
from runtime.crewai.hydra_workflow import HydraWorkflow
from runtime.crewai.llm_client import get_llm_client

def main():
    parser = argparse.ArgumentParser(description='Composable Me - Job Application Generator')
    parser.add_argument('--jd', required=True, help='Path to job description file')
    parser.add_argument('--resume', required=True, help='Path to resume file')
    parser.add_argument('--sources', required=True, help='Path to source documents directory')
    parser.add_argument('--out', default='output/', help='Output directory')
    
    args = parser.parse_args()
    
    # Load inputs
    jd = Path(args.jd).read_text()
    resume = Path(args.resume).read_text()
    sources = Path(args.sources).read_text()  # Or load multiple files
    
    # Initialize workflow
    llm = get_llm_client()
    workflow = HydraWorkflow(llm)
    
    # Execute
    print("Starting workflow...")
    result = workflow.execute({
        'job_description': jd,
        'resume': resume,
        'source_documents': sources,
        'target_role': 'Senior Platform Engineer'  # Extract from JD
    })
    
    # Save outputs
    if result.success:
        output_dir = Path(args.out)
        output_dir.mkdir(exist_ok=True)
        
        (output_dir / 'resume.md').write_text(result.final_documents['resume'])
        (output_dir / 'cover_letter.md').write_text(result.final_documents['cover_letter'])
        (output_dir / 'audit_report.yaml').write_text(str(result.audit_report))
        
        print(f"✅ Success! Documents saved to {output_dir}")
    else:
        print(f"❌ Failed: {result.error_message}")

if __name__ == '__main__':
    main()
```

### Integration Test Pattern

```python
# tests/integration/test_full_workflow.py
import pytest
from runtime.crewai.hydra_workflow import HydraWorkflow
from runtime.crewai.llm_client import get_llm_client

def test_full_workflow_happy_path():
    """Test complete workflow from JD + resume to approved documents"""
    # Setup
    llm = get_llm_client()
    workflow = HydraWorkflow(llm)
    
    context = {
        'job_description': load_test_jd(),
        'resume': load_test_resume(),
        'source_documents': load_test_sources(),
        'target_role': 'Senior Platform Engineer'
    }
    
    # Execute
    result = workflow.execute(context)
    
    # Verify
    assert result.success
    assert result.final_documents is not None
    assert 'resume' in result.final_documents
    assert 'cover_letter' in result.final_documents
    assert result.audit_report['final_status'] == 'APPROVED'
```

---

## Success Criteria

### Task 18 (CLI) Complete When:
- [ ] `run.sh` script works end-to-end
- [ ] CLI accepts all required arguments
- [ ] Workflow executes successfully
- [ ] Outputs are saved to files
- [ ] Errors are handled gracefully
- [ ] User sees progress updates

### Task 19 (Integration Tests) Complete When:
- [ ] Happy path test passes
- [ ] Audit retry test passes
- [ ] Error recovery test passes
- [ ] All tests use real workflow execution
- [ ] Tests verify complete outputs

### Task 16 (Optional) Complete When:
- [ ] Test fixtures created
- [ ] Fixtures are reusable
- [ ] Mock LLM utilities available

---

## Files to Reference

### Existing Code
- `runtime/crewai/hydra_workflow.py` - Workflow orchestrator (use this!)
- `runtime/crewai/llm_client.py` - LLM client initialization
- `runtime/crewai/agents/*.py` - All agent implementations
- `tests/unit/*.py` - Unit test patterns

### Documentation
- `.kiro/specs/composable-crew/requirements.md` - Full requirements
- `.kiro/specs/composable-crew/design.md` - System design
- `docs/AGENTS.MD` - Truth laws
- `docs/STYLE_GUIDE.MD` - Language rules

### Examples
- `examples/sample_jd.md` - Example job description
- `examples/sample_resume.md` - Example resume

---

## What NOT to Do

❌ **Don't reimplement agents** - They're all done
❌ **Don't reimplement HydraWorkflow** - It's done
❌ **Don't create a new Commander** - It exists in Stream B
❌ **Don't mock the workflow in integration tests** - Test the real thing

---

## Questions?

If you need clarification:
- **Workflow execution:** See `runtime/crewai/hydra_workflow.py`
- **Agent usage:** See existing unit tests in `tests/unit/`
- **Requirements:** See `.kiro/specs/composable-crew/requirements.md`

---

## Estimated Effort

- **Task 18 (CLI):** 2-3 hours
- **Task 19 (Integration Tests):** 2-3 hours
- **Task 16 (Optional):** 1-2 hours

**Total:** 4-8 hours depending on whether you do optional Task 16

---

**Ready to start! All the hard work is done - you're just wiring it up and testing it end-to-end.** 🚀
