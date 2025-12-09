"""
Base agent class for Composable Me Hydra.

Provides common functionality for all agents including:
- Prompt loading
- JSON validation
- Error handling and retry logic
- Truth rules enforcement
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json
from crewai import Agent, Task, Crew, Process, LLM


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
    
    def _load_truth_rules(self) -> str:
        """Load AGENTS.MD truth laws"""
        project_root = self._get_project_root()
        agents_file = project_root / "docs" / "AGENTS.MD"
        
        if agents_file.exists():
            return agents_file.read_text()
        
        # Fallback to root AGENTS.md if docs/ doesn't exist
        agents_file = project_root / "AGENTS.md"
        if agents_file.exists():
            return agents_file.read_text()
        
        return ""
    
    def _load_style_guide(self) -> str:
        """Load STYLE_GUIDE.MD"""
        project_root = self._get_project_root()
        style_file = project_root / "docs" / "STYLE_GUIDE.MD"
        
        if style_file.exists():
            return style_file.read_text()
        
        return ""
    
    def create_agent(self) -> Agent:
        """Create CrewAI agent with prompt and rules"""
        backstory = self._build_backstory()
        
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=backstory,
            llm=self.llm,
            verbose=True,
            allow_delegation=False
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
        style_guide_agents = {
            "Tailoring Agent",
            "Differentiator",
            "Auditor Suite"
        }
        return self.role in style_guide_agents
    
    def create_task(
        self,
        description: str,
        context: Optional[List[Task]] = None
    ) -> Task:
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
            context=context or []
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
        import re
        
        # Strip markdown code fences
        cleaned_output = output.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = re.sub(r'^```json\s*\n?', '', cleaned_output)
            cleaned_output = re.sub(r'\n?```\s*$', '', cleaned_output)
        elif cleaned_output.startswith("```"):
            cleaned_output = re.sub(r'^```\s*\n?', '', cleaned_output)
            cleaned_output = re.sub(r'\n?```\s*$', '', cleaned_output)
        cleaned_output = cleaned_output.strip()
        
        # Try to extract JSON if there's surrounding text
        # Look for first { and last }
        first_brace = cleaned_output.find('{')
        last_brace = cleaned_output.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned_output = cleaned_output[first_brace:last_brace + 1]
        
        # Try to parse JSON
        try:
            parsed = json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            try:
                # Fix trailing commas (common LLM mistake)
                fixed_output = re.sub(r',(\s*[}\]])', r'\1', cleaned_output)
                # Fix single quotes (should be double quotes)
                fixed_output = fixed_output.replace("'", '"')
                parsed = json.loads(fixed_output)
            except json.JSONDecodeError as e2:
                raise ValidationError(f"Invalid JSON output: {e2}\n\nOutput was:\n{cleaned_output[:500]}")
        
        if not isinstance(parsed, dict):
            raise ValidationError("Output must be a JSON object (dictionary)")
        
        # Check if base fields are nested in a top-level key
        if len(parsed) == 1 and "agent" not in parsed:
            nested_key = list(parsed.keys())[0]
            nested_data = parsed[nested_key]
            if isinstance(nested_data, dict) and "agent" in nested_data:
                # Promote base fields to top level
                for field in ["agent", "timestamp", "confidence"]:
                    if field in nested_data:
                        parsed[field] = nested_data[field]
        
        self._validate_schema(parsed)
        return parsed
    
    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """
        Validate output contains required fields.
        
        Subclasses should override to add specific validation.
        
        Args:
            data: Parsed output dictionary
            
        Raises:
            ValidationError: If required fields are missing
        """
        from datetime import datetime
        
        # All agents must include these fields - add defaults if missing
        if "agent" not in data:
            data["agent"] = self.role
        
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat() + "Z"
        
        if "confidence" not in data:
            data["confidence"] = 0.8  # Default confidence
        
        # Validate confidence is a number between 0 and 1
        confidence = data.get("confidence")
        if not isinstance(confidence, (int, float)):
            # Try to convert if it's a string
            try:
                confidence = float(confidence)
                data["confidence"] = confidence
            except (ValueError, TypeError):
                data["confidence"] = 0.8  # Fallback
        
        if not 0.0 <= data["confidence"] <= 1.0:
            data["confidence"] = max(0.0, min(1.0, data["confidence"]))  # Clamp to valid range
    
    def execute_with_retry(
        self,
        task: Task,
        max_retries: int = 1
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
        
        for attempt in range(max_retries + 1):
            try:
                # Execute task via a minimal Crew (Task.execute is not available in newer CrewAI)
                crew = Crew(
                    agents=[task.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False,
                )
                result = crew.kickoff()
                
                # Validate output
                validated = self.validate_output(str(result))
                
                return validated
                
            except (ValidationError, Exception) as e:
                last_error = e
                
                if attempt < max_retries:
                    # Log retry attempt
                    print(f"Retry {attempt + 1}/{max_retries} for {self.role}: {e}")
                    continue
                else:
                    # Max retries reached
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
