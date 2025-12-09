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
        Validate and parse agent output with robust error handling for open-source models.
        
        Args:
            output: Raw output string from agent
            
        Returns:
            Parsed and validated output dictionary
            
        Raises:
            ValidationError: If output is invalid after all cleanup attempts
        """
        import re
        
        # Strip markdown code fences
        cleaned_output = output.strip()
        if cleaned_output.startswith("```yaml") or cleaned_output.startswith("```yml"):
            cleaned_output = re.sub(r'^```ya?ml\s*\n?', '', cleaned_output)
            cleaned_output = re.sub(r'\n?```\s*$', '', cleaned_output)
        elif cleaned_output.startswith("```"):
            cleaned_output = re.sub(r'^```\s*\n?', '', cleaned_output)
            cleaned_output = re.sub(r'\n?```\s*$', '', cleaned_output)
        cleaned_output = cleaned_output.strip()
        
        # Aggressive YAML cleaning for open-source models
        lines = cleaned_output.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines at start
            if not cleaned_lines and not line.strip():
                continue
            
            # Remove inline comments in list items: - "value" (comment)
            line = re.sub(r'^(\s*-\s*"[^"]+")(\s*\([^)]+\).*)?$', r'\1', line)
            line = re.sub(r'^(\s*-\s+[^\s(#]+)(\s*\([^)]+\).*)?$', r'\1', line)
            
            # Remove trailing comments after values
            line = re.sub(r'(\s*:\s*[^#]+?)\s*#.*$', r'\1', line)
            
            # Fix common quoting issues - unquoted colons in values
            if ':' in line and not line.strip().startswith('-'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key_part = parts[0]
                    value_part = parts[1].strip()
                    # If value has unquoted special chars, try to quote it
                    if value_part and not (value_part.startswith('"') or value_part.startswith("'") or 
                                          value_part.startswith('[') or value_part.startswith('{')):
                        # Check if it looks like it needs quoting
                        if ':' in value_part or '@' in value_part or '|' in value_part:
                            value_part = f'"{value_part}"'
                            line = f"{key_part}: {value_part}"
            
            # Replace tabs with spaces
            line = line.replace('\t', '  ')
            
            # Remove any weird unicode characters that break YAML
            line = line.encode('ascii', 'ignore').decode('ascii')
            
            cleaned_lines.append(line)
        
        cleaned_output = '\n'.join(cleaned_lines)
        
        # Try multiple parsing strategies
        parsed = None
        last_error = None
        
        # Strategy 1: Direct parse
        try:
            parsed = yaml.safe_load(cleaned_output)
        except yaml.YAMLError as e:
            last_error = e
            
            # Strategy 2: Fix indentation issues
            try:
                # Normalize indentation to 2 spaces
                fixed_lines = []
                for line in cleaned_lines:
                    if line.strip():
                        # Count leading spaces
                        leading = len(line) - len(line.lstrip())
                        # Normalize to multiples of 2
                        normalized_leading = (leading // 2) * 2
                        fixed_lines.append(' ' * normalized_leading + line.lstrip())
                    else:
                        fixed_lines.append(line)
                
                cleaned_output = '\n'.join(fixed_lines)
                parsed = yaml.safe_load(cleaned_output)
            except yaml.YAMLError as e2:
                last_error = e2
                
                # Strategy 3: Try to extract just the YAML block if there's extra text
                try:
                    # Look for the first line that looks like YAML (key: value)
                    yaml_start = 0
                    for i, line in enumerate(fixed_lines):
                        if ':' in line and not line.strip().startswith('#'):
                            yaml_start = i
                            break
                    
                    # Look for the last line that looks like YAML
                    yaml_end = len(fixed_lines)
                    for i in range(len(fixed_lines) - 1, -1, -1):
                        line = fixed_lines[i].strip()
                        if line and not line.startswith('#'):
                            yaml_end = i + 1
                            break
                    
                    yaml_block = '\n'.join(fixed_lines[yaml_start:yaml_end])
                    parsed = yaml.safe_load(yaml_block)
                except yaml.YAMLError as e3:
                    last_error = e3
                    
                    # Strategy 4: Fix nested list indentation issues
                    # Llama often creates lists with wrong indentation
                    try:
                        ultra_fixed_lines = []
                        prev_indent = 0
                        in_list = False
                        
                        for line in fixed_lines[yaml_start:yaml_end]:
                            stripped = line.lstrip()
                            if not stripped:
                                ultra_fixed_lines.append(line)
                                continue
                            
                            current_indent = len(line) - len(stripped)
                            
                            # If this is a list item
                            if stripped.startswith('- '):
                                if in_list and current_indent <= prev_indent:
                                    # Same level or outdented list item - keep as is
                                    ultra_fixed_lines.append(line)
                                elif in_list and current_indent > prev_indent + 2:
                                    # Over-indented list item - fix it
                                    ultra_fixed_lines.append(' ' * (prev_indent + 2) + stripped)
                                else:
                                    ultra_fixed_lines.append(line)
                                in_list = True
                                prev_indent = len(ultra_fixed_lines[-1]) - len(ultra_fixed_lines[-1].lstrip())
                            # If this is a key: value line
                            elif ':' in stripped and not stripped.startswith('#'):
                                in_list = False
                                ultra_fixed_lines.append(line)
                                prev_indent = current_indent
                            else:
                                # Regular content line
                                ultra_fixed_lines.append(line)
                        
                        yaml_block = '\n'.join(ultra_fixed_lines)
                        parsed = yaml.safe_load(yaml_block)
                    except yaml.YAMLError as e4:
                        last_error = e4
        
        if parsed is None:
            raise ValidationError(f"Invalid YAML output after all cleanup attempts: {last_error}")
        
        if not isinstance(parsed, dict):
            raise ValidationError("Output must be a YAML dictionary")
        
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
