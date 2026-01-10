# Integration Framework Design

## Overview

The integration framework is the glue that connects all agents, validates inputs/outputs, handles errors, and maintains the audit trail.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Workflow Runner                       │
│  (Main entry point - orchestrates everything)            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Agent Coordinator                       │
│  - Validates inputs/outputs                              │
│  - Handles agent invocation                              │
│  - Manages context passing                               │
│  - Implements retry logic                                │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │ Agent A │       │ Agent B │       │ Agent C │
   └─────────┘       └─────────┘       └─────────┘
```

## Components

### 1. Workflow Runner
**Location:** `runtime/crewai/workflow_runner.py`

Main entry point that:
- Accepts job description and resume
- Initializes the workflow
- Calls Commander to orchestrate
- Returns final application package

```python
class WorkflowRunner:
    def run(self, job_description: str, resume: str) -> dict:
        """Execute the full workflow"""
        pass
```

### 2. Agent Coordinator
**Location:** `runtime/crewai/agent_coordinator.py`

Handles agent lifecycle:
- Load agent configurations
- Validate inputs before calling
- Invoke agents via CrewAI
- Validate outputs after receiving
- Handle errors and retries
- Maintain context between agents

```python
class AgentCoordinator:
    def invoke_agent(self, agent_name: str, inputs: dict) -> dict:
        """Invoke an agent with validation"""
        pass
    
    def validate_input(self, agent_name: str, inputs: dict) -> bool:
        """Validate inputs against schema"""
        pass
    
    def validate_output(self, agent_name: str, output: dict) -> bool:
        """Validate outputs against schema"""
        pass
```

### 3. Schema Validator
**Location:** `runtime/crewai/schema_validator.py`

Validates YAML against interface specifications:
- Load schemas from agent-interfaces.md
- Validate structure
- Validate data types
- Validate required fields

```python
class SchemaValidator:
    def validate(self, schema_name: str, data: dict) -> tuple[bool, list[str]]:
        """Validate data against schema, return (valid, errors)"""
        pass
```

### 4. Context Manager
**Location:** `runtime/crewai/context_manager.py`

Manages workflow state:
- Store agent outputs
- Pass context between agents
- Maintain audit trail
- Track workflow progress

```python
class ContextManager:
    def store_output(self, agent_name: str, output: dict):
        """Store agent output"""
        pass
    
    def get_context_for_agent(self, agent_name: str) -> dict:
        """Get all context needed for this agent"""
        pass
    
    def get_audit_trail(self) -> list[dict]:
        """Get full audit trail"""
        pass
```

### 5. Error Handler
**Location:** `runtime/crewai/error_handler.py`

Handles errors gracefully:
- Retry logic (max 2 attempts)
- Determine if workflow can continue
- Escalate to user when needed
- Log all errors

```python
class ErrorHandler:
    def handle_error(self, agent_name: str, error: Exception, attempt: int) -> str:
        """Handle error, return action: 'retry', 'continue', 'escalate'"""
        pass
```

## Workflow Sequence

```
1. User provides JD + Resume
2. Workflow Runner initializes
3. Commander invoked (via Agent Coordinator)
   ├─ Research Agent (optional)
   └─ Gap Analyzer
4. Commander requests greenlight
5. User approves
6. Commander continues:
   ├─ Interrogator-Prepper
   ├─ Differentiator
   ├─ Tailoring Agent
   ├─ ATS Optimizer
   └─ Auditor Suite
7. If audit fails:
   ├─ Route back to responsible agent
   ├─ Regenerate
   └─ Re-audit (max 2 loops)
8. Commander assembles final package
9. Return to user
```

## Data Flow

```
JD + Resume
    │
    ▼
Commander ──────► Research Agent ──┐
    │                               │
    ▼                               ▼
Gap Analyzer ◄──────────────────────┘
    │
    ▼
[Greenlight Gate]
    │
    ▼
Interrogator-Prepper
    │
    ▼
Differentiator
    │
    ▼
Tailoring Agent
    │
    ▼
ATS Optimizer
    │
    ▼
Auditor Suite ──► [If fails] ──► Route back ──► Regenerate
    │
    ▼
Final Package
```

## Error Handling Strategy

### Retry Logic
1. First failure: Retry immediately with same inputs
2. Second failure: Check if workflow can continue without this agent
3. If can continue: Log warning, proceed with degraded functionality
4. If cannot continue: Escalate to user with options (retry, skip, abort)

### Audit Failures
1. Categorize issues (blocking vs warning)
2. Generate specific revision instructions
3. Route back to responsible agent
4. Max 2 retry loops
5. After 2 loops: Escalate to user

## Configuration

**Location:** `runtime/crewai/config.yaml`

```yaml
agents:
  commander:
    enabled: true
    timeout: 60
    max_retries: 2
  gap_analyzer:
    enabled: true
    timeout: 30
    max_retries: 2
  # ... etc

workflow:
  require_greenlight: true
  max_audit_retries: 2
  enable_research_agent: false  # optional

llm:
  provider: "openrouter"
  model: "anthropic/claude-3.5-sonnet"
  api_key_env: "OPENROUTER_API_KEY"
```

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock agent responses
- Validate error handling

### Integration Tests
- Test agent-to-agent communication
- Test full workflow with sample data
- Test error scenarios

### End-to-End Tests
- Test with real job descriptions
- Validate final output quality
- Test greenlight process

## Implementation Priority

1. **Phase 1:** Basic structure
   - Workflow Runner skeleton
   - Agent Coordinator skeleton
   - Schema Validator

2. **Phase 2:** Agent integration
   - Integrate Commander (Stream B)
   - Integrate Gap Analyzer (Stream C)
   - Test basic workflow

3. **Phase 3:** Full workflow
   - Integrate remaining agents
   - Implement retry logic
   - Implement audit loop

4. **Phase 4:** Polish
   - Error handling refinement
   - Logging and monitoring
   - Performance optimization

## Next Steps

1. Create skeleton implementations
2. Wait for Stream B (Commander) to complete
3. Integrate and test
4. Iterate with other streams as they complete
