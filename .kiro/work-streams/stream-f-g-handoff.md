# Stream F & G Handoff to Augment

**Date:** December 6, 2025  
**From:** Kiro (Spec Agent)  
**To:** Augment  
**Status:** Ready to start

---

## What's Complete

### Phase 1 (100% Complete)
- ✅ **Stream A:** Core Infrastructure
- ✅ **Stream B:** Commander Agent (13/13 tests passing)
- ✅ **Stream C:** Gap Analyzer Agent (7/7 tests passing)
- ✅ **Stream D:** Interrogator-Prepper Agent (5/5 tests passing)
- ✅ **Stream E:** Differentiator & Tailoring Agents (13/13 tests passing)

**Total:** 38/38 tests passing

---

## Your Assignment

### Stream F: ATS Optimizer & Auditor Suite

**Tasks:**
- **Task 9:** Implement ATS Optimizer Agent
  - 9.1: Create ATS Optimizer prompt ✅ (already exists at `agents/ats-optimizer/prompt.md`)
  - 9.2-9.5: Property tests and unit tests (optional, marked with *)
  
- **Task 11:** Implement Auditor Suite Agent
  - 11.1: Create Auditor Suite prompt ✅ (already exists at `agents/auditor-suite/prompt.md`)
  - 11.2-11.7: Property tests and unit tests (optional, marked with *)

**What You Need to Build:**
1. `runtime/crewai/agents/ats_optimizer.py` - ATS Optimizer implementation
2. `runtime/crewai/agents/auditor.py` - Auditor Suite implementation
3. Unit tests for both agents (following the pattern from completed agents)

### Stream G: Workflow Orchestration

**Tasks:**
- **Task 13:** Implement Commander Agent (workflow orchestration version)
- **Task 14:** Implement HydraWorkflow orchestrator
  - Full workflow coordination
  - State machine transitions
  - Audit retry loop
  - Error recovery

---

## Key Files to Reference

### Requirements & Design
- `.kiro/specs/composable-crew/requirements.md` - Full requirements
- `.kiro/specs/composable-crew/design.md` - Complete design document
- `.kiro/specs/composable-crew/tasks.md` - Task list (updated with correct stream labels)

### Prompts (Already Created)
- `agents/ats-optimizer/prompt.md` - ATS Optimizer prompt
- `agents/auditor-suite/prompt.md` - Auditor Suite prompt

### Style & Rules
- `docs/STYLE_GUIDE.MD` - AI pattern detection rules (critical for Auditor Suite)
- `AGENTS.md` - Truth laws and compliance rules (critical for Auditor Suite)

### Completed Examples (Follow These Patterns)
- `runtime/crewai/agents/commander.py` - Commander implementation
- `runtime/crewai/agents/gap_analyzer.py` - Gap Analyzer implementation
- `runtime/crewai/agents/interrogator_prepper.py` - Interrogator implementation
- `runtime/crewai/agents/differentiator.py` - Differentiator implementation
- `runtime/crewai/agents/tailoring_agent.py` - Tailoring Agent implementation

### Test Examples
- `tests/unit/test_commander.py` - 13 tests
- `tests/unit/test_gap_analyzer.py` - 7 tests
- `tests/unit/test_interrogator_prepper.py` - 5 tests
- `tests/unit/test_differentiator.py` - 7 tests
- `tests/unit/test_tailoring_agent.py` - 6 tests

---

## Implementation Pattern

All agents follow this pattern:

```python
from runtime.crewai.base_agent import BaseHydraAgent

class YourAgent(BaseHydraAgent):
    """Agent description"""
    
    def __init__(self, llm_client):
        super().__init__(
            agent_name="YourAgent",
            prompt_path="agents/your-agent/prompt.md",
            llm_client=llm_client
        )
    
    def _validate_context(self, context: dict) -> None:
        """Validate required context parameters"""
        required = ["param1", "param2"]
        for param in required:
            if param not in context:
                raise ValueError(f"Missing required context: {param}")
    
    def _validate_schema(self, output: dict) -> None:
        """Validate agent-specific output schema"""
        super()._validate_schema(output)  # Validates base fields
        
        # Add your specific validations
        required_fields = ["field1", "field2"]
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
```

---

## Testing Requirements

### Unit Tests (Required)
- Test initialization and configuration
- Test required context parameters
- Test schema validation
- Test error handling
- Follow the pattern from completed agents

### Property Tests (Optional - marked with *)
- These are marked as optional in the task list
- You can skip them to focus on core functionality
- If you implement them, use Hypothesis library

---

## Key Requirements for Auditor Suite

The Auditor Suite is the most complex agent. It must:

1. **Truth Audit:** Verify all claims against source documents
   - Check employment dates unchanged
   - Verify all technologies mentioned exist in sources
   - Ensure no fabricated metrics

2. **Tone Audit:** Detect AI patterns from STYLE_GUIDE.MD
   - Check for forbidden phrases (see `docs/STYLE_GUIDE.MD`)
   - Verify sentence length variation
   - Ensure human voice patterns

3. **ATS Audit:** Verify keyword coverage
   - Extract keywords from JD
   - Check presence in resume
   - Identify missing but claimable keywords

4. **Compliance Audit:** Check AGENTS.MD rules
   - Verify chronology preservation
   - Check for fabrication
   - Validate adjacent experience framing

5. **Issue Categorization:** blocking, warning, recommendation
   - Blocking issues prevent approval
   - Warnings should be fixed but can proceed
   - Recommendations are optional improvements

---

## Key Requirements for ATS Optimizer

The ATS Optimizer must:

1. **Keyword Extraction:** Extract keywords from JD
2. **Coverage Checking:** Verify keywords in resume
3. **Truthful Suggestions:** Only suggest keywords that are claimable
4. **Format Validation:** Ensure ATS-compatible structure
5. **No Fabrication:** Never add keywords that aren't truthful

---

## Success Criteria

### Stream F Complete When:
- [ ] ATS Optimizer agent implemented
- [ ] Auditor Suite agent implemented
- [ ] Unit tests written and passing for both
- [ ] Agents follow BaseHydraAgent pattern
- [ ] Schema validation working correctly

### Stream G Complete When:
- [ ] HydraWorkflow orchestrator implemented
- [ ] State machine transitions working
- [ ] Audit retry loop functional (max 2 retries)
- [ ] Error recovery implemented
- [ ] Full workflow can execute end-to-end

---

## Notes

1. **Stream labels fixed:** I corrected the confusing duplicate "Stream D" labeling in tasks.md
2. **Prompts exist:** Both ATS Optimizer and Auditor Suite prompts are already written
3. **Pattern established:** All 5 completed agents follow the same pattern - use them as reference
4. **Tests passing:** All 38 tests from Phase 1 are passing - maintain this standard
5. **Optional tests:** Tasks marked with `*` are optional - focus on core functionality first

---

## Questions?

If you need clarification on:
- Requirements: See `.kiro/specs/composable-crew/requirements.md`
- Design decisions: See `.kiro/specs/composable-crew/design.md`
- Implementation patterns: Look at completed agents in `runtime/crewai/agents/`
- Testing patterns: Look at completed tests in `tests/unit/`

---

## Good Luck!

You're building on a solid foundation. Phase 1 is complete with 100% test pass rate. Keep that standard going! 🚀
