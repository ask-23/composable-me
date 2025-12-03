# ARCHITECTURE.MD — Composable Me System Design v2.0

## Overview

Composable Me is a multi-agent system for job search optimization.
The system coordinates specialized agents through a central orchestrator
while enforcing strict truth constraints.

## Design Principles

### 1. Single Responsibility
Each agent does one thing well. No agent generates AND verifies.

### 2. Truth as Infrastructure
AGENTS.MD rules are not guidelines—they're enforced at every step.

### 3. Structured Communication
Agents communicate via YAML, not prose. This enables validation.

### 4. Audit Trail
Every decision is logged. Every claim is traceable to source.

### 5. Human in the Loop
No application ships without user greenlight.

---

## System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         COMPOSABLE ME HYDRA                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐                                                    │
│  │   INPUTS    │                                                    │
│  │ ─────────── │                                                    │
│  │ • JD Text   │                                                    │
│  │ • Resume    │                                                    │
│  │ • User Q&A  │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      COMMANDER                               │   │
│  │  (Orchestrator)                                              │   │
│  │                                                              │   │
│  │  • Receives inputs                                           │   │
│  │  • Dispatches agents                                         │   │
│  │  • Enforces workflow                                         │   │
│  │  • Assembles output                                          │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│         ┌───────────────────┼───────────────────┐                   │
│         │                   │                   │                   │
│         ▼                   ▼                   ▼                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  RESEARCH   │    │    GAP      │    │ INTERROGATOR│             │
│  │   AGENT     │    │  ANALYZER   │    │   PREPPER   │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│         │                   │                   │                   │
│         └───────────────────┼───────────────────┘                   │
│                             │                                       │
│                             ▼                                       │
│                   ┌─────────────────┐                               │
│                   │ DIFFERENTIATOR  │                               │
│                   └────────┬────────┘                               │
│                            │                                        │
│                            ▼                                        │
│                   ┌─────────────────┐                               │
│                   │   TAILORING     │                               │
│                   │     AGENT       │                               │
│                   └────────┬────────┘                               │
│                            │                                        │
│                            ▼                                        │
│                   ┌─────────────────┐                               │
│                   │ ATS OPTIMIZER   │                               │
│                   └────────┬────────┘                               │
│                            │                                        │
│                            ▼                                        │
│                   ┌─────────────────┐                               │
│                   │  AUDITOR SUITE  │──────┐                        │
│                   └────────┬────────┘      │                        │
│                            │               │ (retry loop)           │
│                            │◄──────────────┘                        │
│                            │                                        │
│                            ▼                                        │
│                   ┌─────────────────┐                               │
│                   │     OUTPUT      │                               │
│                   │    PACKAGE      │                               │
│                   └─────────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Stage 1: Input Processing

```yaml
input:
  job_description:
    source: "user paste or URL"
    format: "text"
  
  resume:
    source: "Sr. Dev Ops.pdf, resume_merged.md"
    format: "text"
  
  context:
    source: "user preferences"
    format: "yaml"
```

### Stage 2: Research & Analysis

```yaml
research_output:
  company_intel:
    name: "..."
    size: "..."
    tech_stack: [...]
    red_flags: [...]

gap_analysis_output:
  direct_matches: [...]
  adjacent: [...]
  gaps: [...]
  blockers: [...]
  fit_score: "X%"
```

### Stage 3: User Decision Point

```yaml
greenlight_request:
  summary: "..."
  recommendation: "PURSUE / PASS / DISCUSS"
  awaiting: "user confirmation"

user_response:
  decision: "proceed / pass"
  notes: "optional context"
```

### Stage 4: Deep Dive (if proceeding)

```yaml
interview_output:
  themes:
    - theme: "Agentic AI"
      context: "..."
      actions: "..."
      outcomes: "..."
      quotable: "..."

differentiator_output:
  primary: {...}
  secondary: [...]
  narrative_thread: "..."
```

### Stage 5: Generation

```yaml
tailoring_output:
  resume:
    content: "..."
    source_mapping: [...]
  
  cover_letter:
    content: "..."
    source_mapping: [...]
```

### Stage 6: Verification

```yaml
audit_output:
  truth_audit: "PASS/FAIL"
  tone_audit: "PASS/CONDITIONAL/FAIL"
  ats_audit: "PASS/FAIL"
  compliance_audit: "PASS/FAIL"
  
  overall: "APPROVED / REJECTED"
  issues: [...]
  fixes_required: [...]
```

### Stage 7: Output

```yaml
final_package:
  documents:
    resume: "..."
    cover_letter: "..."
    recruiter_reply: "..."  # if applicable
  
  metadata:
    role: "..."
    company: "..."
    fit_score: "..."
    differentiators: [...]
  
  audit_trail:
    sources_referenced: [...]
    decisions_made: [...]
    issues_resolved: [...]
```

---

## State Management

The system maintains state across the workflow:

```yaml
workflow_state:
  id: "uuid"
  created: "timestamp"
  status: "in_progress / awaiting_user / complete / failed"
  
  current_stage: "research / gap_analysis / greenlight / interview / ..."
  
  inputs:
    jd: "..."
    resume: "..."
  
  agent_outputs:
    research: {...}
    gap_analysis: {...}
    interview: {...}
    differentiator: {...}
    tailoring: {...}
    ats: {...}
    audit: {...}
  
  user_interactions:
    - timestamp: "..."
      type: "greenlight"
      decision: "proceed"
    
    - timestamp: "..."
      type: "interview_response"
      content: "..."
  
  errors:
    - stage: "audit"
      issue: "truth violation"
      resolution: "fixed in iteration 2"
```

---

## Error Handling

### Retry Logic

```yaml
retry_policy:
  audit_failures:
    max_retries: 2
    action: "route back to responsible agent with specific issues"
    escalation: "after max retries, present to user with options"
  
  agent_errors:
    max_retries: 1
    action: "retry with same inputs"
    escalation: "fail workflow, present error to user"
  
  user_timeouts:
    threshold: "24 hours"
    action: "save state, remind user"
```

### Failure Modes

```yaml
failure_handling:
  truth_violation:
    severity: "blocking"
    action: "reject document, require fix"
  
  ai_pattern_detected:
    severity: "warning"
    action: "flag to user, allow override"
  
  gap_too_large:
    severity: "blocking"
    action: "recommend PASS to user"
  
  external_service_failure:
    severity: "recoverable"
    action: "retry, then proceed without enrichment"
```

---

## Framework Recommendations

Given your background in Go and preference for incremental, testable changes:

### Option 1: Go + LLM API (Recommended)

**Why:** Native to your stack, full control, easy to test.

```go
// Core types
type Agent interface {
    Execute(input AgentInput) (AgentOutput, error)
}

type Workflow struct {
    State    WorkflowState
    Agents   map[string]Agent
    LLM      LLMClient
}

// Each agent is a struct implementing Agent interface
type GapAnalyzer struct {
    llm LLMClient
    sources []SourceDoc
}

func (g *GapAnalyzer) Execute(input AgentInput) (AgentOutput, error) {
    prompt := g.buildPrompt(input)
    response, err := g.llm.Complete(prompt)
    if err != nil {
        return nil, err
    }
    return g.parseResponse(response)
}
```

**Pros:**
- Full control over orchestration
- Easy to unit test each agent
- No framework lock-in
- Familiar tooling

**Cons:**
- More boilerplate
- Build state management yourself

### Option 2: LangGraph (Python)

**Why:** Purpose-built for agent workflows, good state management.

```python
from langgraph.graph import StateGraph

graph = StateGraph(HydraState)
graph.add_node("research", research_agent)
graph.add_node("gap_analysis", gap_analyzer)
# ... etc
```

**Pros:**
- Built-in state management
- Graph visualization
- Interrupts/human-in-loop support

**Cons:**
- Python (not your primary)
- Framework dependency

### Option 3: Claude Artifacts + Prompts

**Why:** Zero infrastructure, immediate iteration.

Run the system as a conversation:
1. User pastes JD
2. Claude runs agents sequentially via structured prompts
3. State managed in conversation context

**Pros:**
- Zero setup
- Immediate feedback
- Easy to iterate prompts

**Cons:**
- Context window limits
- No persistence
- Manual execution

### Recommendation

**Start with Option 3** (Claude Artifacts + Prompts) to validate the agent designs.
Once proven, **port to Option 1** (Go) for production use.

---

## File Structure

```
composable-me/
├── docs/
│   ├── AGENTS.MD              # Truth rules
│   ├── AGENT_ROLES.MD         # Agent specifications
│   ├── ARCHITECTURE.MD        # This file
│   ├── STYLE_GUIDE.MD         # Language rules
│   └── RUNTIME_MANIFEST.md    # Orchestration spec
│
├── agents/
│   ├── commander/
│   │   └── prompt.md
│   ├── interrogator-prepper/
│   │   ├── prompt.md
│   │   └── interview_flows/
│   ├── gap-analyzer/
│   │   └── prompt.md
│   ├── differentiator/
│   │   └── prompt.md
│   ├── tailoring-agent/
│   │   └── prompt.md
│   ├── auditor-suite/
│   │   └── prompt.md
│   └── ats-optimizer/
│       └── prompt.md
│
├── runtime/
│   ├── go/                    # Go implementation
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── agents/
│   │   │   ├── workflow/
│   │   │   └── llm/
│   │   └── go.mod
│   │
│   └── python/                # Python/LangGraph alternative
│       ├── orchestrator.py
│       └── requirements.txt
│
├── sources/                   # User source documents
│   ├── resume.md
│   └── additional/
│
└── output/                    # Generated applications
    └── {company}-{role}-{date}/
```

---

## Testing Strategy

### Unit Tests (Per Agent)

```go
func TestGapAnalyzer_DirectMatch(t *testing.T) {
    input := AgentInput{
        JD: "5+ years AWS experience required",
        Resume: "AWS architect for 6 years...",
    }
    
    output, err := analyzer.Execute(input)
    
    assert.NoError(t, err)
    assert.Contains(t, output.DirectMatches, "AWS")
}
```

### Integration Tests (Workflow)

```go
func TestWorkflow_HappyPath(t *testing.T) {
    wf := NewWorkflow(mockLLM, agents)
    
    result, err := wf.Run(testJD, testResume)
    
    assert.NoError(t, err)
    assert.True(t, result.Audit.Passed)
}
```

### Prompt Tests (Agent Quality)

```python
# Test that prompts produce expected structure
def test_gap_analyzer_output_structure():
    response = llm.complete(gap_analyzer_prompt + test_jd)
    parsed = yaml.safe_load(response)
    
    assert "direct_matches" in parsed
    assert "gaps" in parsed
    assert "fit_score" in parsed
```

---

## Versioning

All agent prompts include version in frontmatter:

```yaml
---
agent: gap-analyzer
version: 1.2.0
updated: 2025-12-02
---
```

AGENTS.MD changes require changelog entry and version bump.
