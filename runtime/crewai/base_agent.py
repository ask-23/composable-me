"""
Base agent class for Composable Me Hydra.

Provides common functionality for all agents including:
- Prompt loading
- JSON validation
- Error handling and retry logic
- Truth rules enforcement
"""

import json
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from crewai import LLM, Agent, Crew, Process, Task

from runtime.crewai.telemetry import record_agent_error, record_agent_result, trace_agent_execution

# Constants
DEFAULT_CONFIDENCE = 0.8
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0
DEFAULT_MAX_RETRIES = 1

# Opt-in flag (default OFF) that routes agent calls straight through LiteLLM instead
# of spinning up a one-task CrewAI Crew per call. See docs/adr/0001-crewai-vs-direct-llm.md.
# Kept off by default: the two paths' prompt assembly is not yet proven equivalent
# against a live model, so this is a scaffold for that migration, not a cutover.
DIRECT_LLM_ENV = "HYDRA_DIRECT_LLM"

DEFAULT_TRUTH_RULES = """\
1. Do not fabricate experience, tools, metrics, or outcomes.
2. Keep chronology consistent with provided sources.
3. If a claim cannot be supported by inputs, omit it or ask for clarification.
""".strip()

DEFAULT_STYLE_GUIDE = """\
- Prefer concrete details over hype.
- Avoid generic corporate phrases and AI clichés.
- Use clear, concise language and varied sentence lengths.
""".strip()


class ValidationError(Exception):
    """Raised when agent output validation fails"""

    pass


class BaseHydraAgent(ABC):
    """Base class for all Hydra agents"""

    # Subclasses must define these
    role: str = ""
    goal: str = ""
    expected_output: str = ""

    def __init__(self, llm: LLM, prompt_path: Optional[str] = None, use_json_mode: bool = True):
        """
        Initialize base agent.

        Args:
            llm: The LLM instance to use
            prompt_path: Path to agent prompt file (relative to project root)
            use_json_mode: Whether to request JSON mode from LLM (if supported)
        """
        self.llm = llm
        self.prompt_path = prompt_path
        self.prompt = self._load_prompt() if prompt_path else ""
        self.truth_rules = self._load_truth_rules()
        self.style_guide = self._load_style_guide()
        self.use_json_mode = use_json_mode

    def _get_project_root(self) -> Path:
        """Get project root directory"""
        # Navigate up from runtime/crewai/ to project root
        return Path(__file__).parent.parent.parent

    def _load_prompt(self) -> str:
        """Load agent prompt from file"""
        if not self.prompt_path:
            return ""

        project_root = self._get_project_root()
        prompt_file = project_root / self.prompt_path

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        return prompt_file.read_text()

    def _load_first(self, candidates: List[str], default: str) -> str:
        """Return the contents of the first existing candidate path, else default.

        Filenames are matched case-insensitively so the canonical docs load on both
        case-sensitive (Linux/CI) and case-insensitive (macOS) filesystems.
        """
        project_root = self._get_project_root()
        for candidate in candidates:
            path = project_root / candidate
            if path.exists():
                return path.read_text()
            # Case-insensitive fallback within the candidate's directory.
            parent = path.parent
            if parent.exists():
                for entry in parent.iterdir():
                    if entry.is_file() and entry.name.lower() == path.name.lower():
                        return entry.read_text()
        return default

    def _load_truth_rules(self) -> str:
        """Load the canonical truth rules (docs/AGENTS.MD), else a built-in default."""
        return self._load_first(["docs/AGENTS.MD", "AGENTS.md"], DEFAULT_TRUTH_RULES)

    def _load_style_guide(self) -> str:
        """Load the canonical style guide (docs/STYLE_GUIDE.MD), else a built-in default."""
        return self._load_first(["docs/STYLE_GUIDE.MD", "STYLE_GUIDE.md"], DEFAULT_STYLE_GUIDE)

    def create_agent(self) -> Agent:
        """Create CrewAI agent with prompt and rules"""
        backstory = self._build_backstory()

        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=backstory,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _build_backstory(self) -> str:
        """Build agent backstory with prompt and rules"""
        parts = []

        if self.prompt:
            parts.append(self.prompt)

        if self.truth_rules:
            parts.append("\n\nTRUTH RULES (INVIOLABLE):")
            parts.append(self.truth_rules)

        if self.style_guide and self._needs_style_guide():
            parts.append("\n\nSTYLE GUIDE:")
            parts.append(self.style_guide)

        return "\n".join(parts)

    def _needs_style_guide(self) -> bool:
        """Check if this agent needs the style guide"""
        # Only agents that generate user-facing content need style guide
        style_guide_agents = {"Tailoring Agent", "Differentiator", "Auditor Suite"}
        return self.role in style_guide_agents

    def create_task(self, description: str, context: Optional[List[Task]] = None) -> Task:
        """Create CrewAI task for this agent"""
        # Add required base fields to task description
        enhanced_description = f"""{description}

IMPORTANT: Your output MUST be valid JSON and include these required fields at the top level:
- "agent": "{self.role}"
- "timestamp": Current ISO-8601 timestamp (e.g., "2025-12-08T12:00:00Z")
- "confidence": A number between 0.0 and 1.0 indicating your confidence in the analysis

Return ONLY valid JSON. Do not include any text before or after the JSON object.
"""

        return Task(
            description=enhanced_description,
            expected_output=self.expected_output,
            agent=self.create_agent(),
            context=context or [],
        )

    def validate_output(self, output: str) -> Dict[str, Any]:
        """
        Validate and parse agent output as JSON.

        Args:
            output: Raw output string from agent

        Returns:
            Parsed and validated output dictionary

        Raises:
            ValidationError: If output is invalid JSON
        """
        cleaned_output = self._clean_output(output)
        parsed = self._parse_json(cleaned_output)
        self._promote_nested_base_fields(parsed)
        self._validate_schema(parsed)
        return parsed

    def _clean_output(self, output: str) -> str:
        """Clean and extract JSON from raw output."""
        cleaned = output.strip()

        # Remove markdown code fences
        if cleaned.startswith("```json"):
            cleaned = re.sub(r"^```json\s*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        elif cleaned.startswith("```"):
            cleaned = re.sub(r"^```\s*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)

        cleaned = cleaned.strip()

        # Extract JSON from surrounding text
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace : last_brace + 1]

        return cleaned

    def _parse_json(self, json_str: str) -> Dict[str, Any]:
        """Parse JSON string with limited, safe error recovery.

        The only automatic repair is stripping trailing commas — a common,
        unambiguous LLM mistake. We deliberately do NOT blanket-replace single
        quotes with double quotes: that corrupts legitimate apostrophes inside
        string values (e.g. "the candidate's experience").
        """
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            try:
                # Remove trailing commas before a closing } or ].
                fixed = re.sub(r",(\s*[}\]])", r"\1", json_str)
                parsed = json.loads(fixed)
            except json.JSONDecodeError as e2:
                raise ValidationError(
                    f"Invalid JSON output: {e2}\n\nOutput was:\n{json_str[:500]}"
                ) from e2

        # Validate that result is a dictionary
        if not isinstance(parsed, dict):
            raise ValidationError("Output must be a JSON object (dictionary)")

        return parsed

    def _promote_nested_base_fields(self, parsed: Dict[str, Any]) -> None:
        """Promote base fields from nested structure if needed."""
        # Check if base fields are nested in a single top-level key
        if len(parsed) == 1 and "agent" not in parsed:
            nested_key = list(parsed.keys())[0]
            nested_data = parsed[nested_key]
            if isinstance(nested_data, dict) and "agent" in nested_data:
                # Promote base fields to top level
                for field in ["agent", "timestamp", "confidence"]:
                    if field in nested_data:
                        parsed[field] = nested_data[field]

    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """
        Validate output contains required fields.

        Subclasses should override to add specific validation.

        Args:
            data: Parsed output dictionary

        Raises:
            ValidationError: If required fields are missing
        """
        # All agents must include these fields - add defaults if missing
        if "agent" not in data:
            data["agent"] = self.role

        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat() + "Z"

        if "confidence" not in data:
            data["confidence"] = DEFAULT_CONFIDENCE

        # Validate and normalize confidence
        data["confidence"] = self._normalize_confidence(data["confidence"])

    def _normalize_confidence(self, confidence: Any) -> float:
        """Normalize confidence value to valid range [0.0, 1.0]."""
        if not isinstance(confidence, (int, float)):
            # Try to convert if it's a string
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                return DEFAULT_CONFIDENCE

        # Clamp to valid range
        return max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, float(confidence)))

    def _build_messages(self, task: Task) -> List[Dict[str, str]]:
        """Assemble system+user messages for a direct LiteLLM call.

        Built from the same pieces the CrewAI path uses: the agent backstory
        (role + goal + prompt + injected truth/style rules) as the system message,
        and the task description (which already carries the JSON-output instruction)
        plus the expected-output contract as the user message.
        """
        system = f"You are {self.role}. {self.goal}\n\n{self._build_backstory()}".strip()
        user = task.description
        if self.expected_output:
            user = f"{user}\n\nExpected output: {self.expected_output}"
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _execute_direct(self, task: Task) -> str:
        """Run one agent call directly through LiteLLM, bypassing CrewAI.

        Opt-in via HYDRA_DIRECT_LLM. Reuses the model/credentials from the CrewAI
        LLM object so provider routing is unchanged.
        """
        import litellm

        llm = self.llm
        response = litellm.completion(
            model=getattr(llm, "model", None),
            messages=self._build_messages(task),
            temperature=getattr(llm, "temperature", None),
            api_key=getattr(llm, "api_key", None),
            base_url=getattr(llm, "base_url", None),
        )
        return response["choices"][0]["message"]["content"]

    def execute_with_retry(
        self, task: Task, max_retries: int = DEFAULT_MAX_RETRIES
    ) -> Dict[str, Any]:
        """
        Execute task with retry logic.

        Args:
            task: The task to execute
            max_retries: Maximum number of retries on failure

        Returns:
            Validated output dictionary

        Raises:
            ValidationError: If all retries fail
        """
        last_error = None

        with trace_agent_execution(self.role, {"max_retries": max_retries}) as span:
            for attempt in range(max_retries + 1):
                try:
                    span.set_attribute("agent.attempt", attempt + 1)

                    # Default: execute via a minimal one-task Crew. Opt-in: call
                    # LiteLLM directly (no Crew) when HYDRA_DIRECT_LLM is set.
                    if os.environ.get(DIRECT_LLM_ENV):
                        result = self._execute_direct(task)
                    else:
                        # Task.execute is not available in newer CrewAI, so wrap in a Crew.
                        crew = Crew(
                            agents=[task.agent],
                            tasks=[task],
                            process=Process.sequential,
                            verbose=False,
                        )
                        result = crew.kickoff()

                    # Validate output
                    validated = self.validate_output(str(result))

                    # Record success
                    record_agent_result(span, validated, self.role)
                    span.set_attribute("agent.retries_used", attempt)

                    return validated

                except Exception as e:
                    last_error = e
                    span.add_event(f"retry.{attempt + 1}", {"error": str(e)})

                    if attempt < max_retries:
                        # Log retry attempt
                        print(f"Retry {attempt + 1}/{max_retries} for {self.role}: {e}")
                        continue
                    else:
                        # Max retries reached - record error
                        record_agent_error(span, e, self.role)
                        break

            # All retries failed
            raise ValidationError(
                f"Agent {self.role} failed after {max_retries + 1} attempts: {last_error}"
            )

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with given context.

        Subclasses must implement this method.

        Args:
            context: Input context for the agent

        Returns:
            Agent output dictionary
        """
        pass
