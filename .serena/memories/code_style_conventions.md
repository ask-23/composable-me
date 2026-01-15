# Code Style and Conventions

## Python Style

### General
- Python 3.13 compatible
- Use type hints for function signatures
- Dataclasses for structured data models
- Enums for status/type constants

### Naming Conventions
- Classes: `PascalCase` (e.g., `HydraWorkflow`, `BaseHydraAgent`)
- Functions/methods: `snake_case` (e.g., `execute_with_retry`, `validate_output`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CONFIDENCE`, `MAX_RETRIES`)
- Private methods: `_leading_underscore` (e.g., `_parse_json`, `_log`)

### File Organization
- Agent implementations in `runtime/crewai/agents/`
- Each agent extends `BaseHydraAgent`
- Models/dataclasses in `runtime/crewai/models.py`
- Configuration in `runtime/crewai/config.py`
- LLM client abstraction in `runtime/crewai/llm_client.py`

### Agent Pattern
```python
class MyAgent(BaseHydraAgent):
    def __init__(self, llm_config):
        super().__init__(
            agent_name="my-agent",
            role="Agent Role",
            goal="What it achieves",
            llm_config=llm_config
        )
    
    def create_task(self, context: dict) -> Task:
        # Return CrewAI Task
        pass
    
    def validate_output(self, output: Any) -> dict:
        # Validate and return cleaned output
        pass
```

### Dataclass Pattern
```python
@dataclass
class MyModel:
    field: str
    optional_field: Optional[str] = None
    
    def __post_init__(self):
        # Validation logic
        pass
```

## TypeScript/Frontend Style

### General
- TypeScript strict mode
- Astro 5 for pages
- Svelte 5 for interactive components

### File Organization
- Pages in `web/frontend/src/pages/`
- Components in `web/frontend/src/components/`
- E2E tests in `web/frontend/tests/`

## Documentation Style

### Agent Prompts
- Stored in `agents/<agent-name>/prompt.md`
- Include role, goals, constraints, output format

### Truth Rules
All agents must follow truth rules defined in `docs/AGENTS.MD`:
1. Chronology is sacred — No date changes
2. No fabrication — No invented metrics
3. The Everest Rule — If you didn't do it, don't claim it
4. Source authority — Claims must trace to documents
5. Adjacent framing — Transferable experience framed honestly

## Anti-AI Detection Patterns

See `docs/STYLE_GUIDE.MD` for:
- Forbidden phrases (e.g., "proven track record", "passionate about")
- Required variation in sentence structure
- Human voice patterns
- Specific over generic accomplishments
