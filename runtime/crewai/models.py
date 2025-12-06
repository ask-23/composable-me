"""
Data models for Composable Me Hydra.

These dataclasses represent the core data structures used throughout the system.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class WorkflowStatus(Enum):
    """Workflow execution status"""
    INITIALIZED = "initialized"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    AWAITING_GREENLIGHT = "awaiting_greenlight"
    INTERVIEWING = "interviewing"
    DIFFERENTIATING = "differentiating"
    GENERATING = "generating"
    OPTIMIZING = "optimizing"
    AUDITING = "auditing"
    RETRYING = "retrying"
    COMPLETE = "complete"
    FAILED = "failed"
    ARCHIVED = "archived"


class ClassificationType(Enum):
    """Requirement classification types"""
    DIRECT_MATCH = "direct_match"
    ADJACENT = "adjacent"
    GAP = "gap"
    BLOCKER = "blocker"


class IssueSeverity(Enum):
    """Audit issue severity levels"""
    BLOCKING = "blocking"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"


class RequirementType(Enum):
    """Types of job requirements"""
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    CULTURAL = "cultural"


class RequirementPriority(Enum):
    """Priority levels for requirements"""
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"


# ============================================================================
# Core Data Models
# ============================================================================

@dataclass
class Employment:
    """Employment history entry"""
    company: str
    title: str
    start_date: str
    end_date: Optional[str]
    achievements: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate employment data"""
        if not self.company or not self.title or not self.start_date:
            raise ValueError("Employment must have company, title, and start_date")


@dataclass
class Resume:
    """Resume data structure"""
    text: str
    format: str = "markdown"  # markdown, pdf, text
    employment_history: List[Employment] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate resume data"""
        if not self.text:
            raise ValueError("Resume text cannot be empty")


@dataclass
class JobDescription:
    """Job description data structure"""
    text: str
    company: Optional[str] = None
    role: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate job description data"""
        if not self.text:
            raise ValueError("Job description text cannot be empty")


@dataclass
class Requirement:
    """A single job requirement"""
    text: str
    type: RequirementType
    priority: RequirementPriority
    keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate requirement data"""
        if not self.text:
            raise ValueError("Requirement text cannot be empty")


@dataclass
class Classification:
    """Classification of a requirement against candidate experience"""
    requirement: Requirement
    category: ClassificationType
    evidence: Optional[str] = None
    confidence: float = 0.0
    framing: Optional[str] = None
    
    def __post_init__(self):
        """Validate classification data"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class Differentiator:
    """A unique value proposition for the candidate"""
    hook: str
    evidence: str
    resonance: str
    relevance_score: float = 0.0
    
    def __post_init__(self):
        """Validate differentiator data"""
        if not self.hook or not self.evidence or not self.resonance:
            raise ValueError("Differentiator must have hook, evidence, and resonance")
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0")


@dataclass
class AuditIssue:
    """An issue found during audit"""
    type: str  # truth, tone, ats, compliance
    severity: IssueSeverity
    location: str
    description: str
    fix: str
    
    def __post_init__(self):
        """Validate audit issue data"""
        valid_types = {"truth", "tone", "ats", "compliance"}
        if self.type not in valid_types:
            raise ValueError(f"Issue type must be one of {valid_types}")


@dataclass
class AgentExecution:
    """Record of an agent execution"""
    agent_name: str
    timestamp: datetime
    inputs: Dict[str, Any]
    output: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class WorkflowState:
    """State machine for workflow execution"""
    id: str
    status: WorkflowStatus
    current_stage: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    user_interactions: List[Dict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    audit_trail: List[AgentExecution] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def transition(self, new_status: WorkflowStatus) -> None:
        """Transition to a new workflow status"""
        # Validate state transitions
        valid_transitions = {
            WorkflowStatus.INITIALIZED: {
                WorkflowStatus.RESEARCHING,
                WorkflowStatus.ANALYZING
            },
            WorkflowStatus.RESEARCHING: {
                WorkflowStatus.ANALYZING
            },
            WorkflowStatus.ANALYZING: {
                WorkflowStatus.AWAITING_GREENLIGHT
            },
            WorkflowStatus.AWAITING_GREENLIGHT: {
                WorkflowStatus.INTERVIEWING,
                WorkflowStatus.ARCHIVED
            },
            WorkflowStatus.INTERVIEWING: {
                WorkflowStatus.DIFFERENTIATING
            },
            WorkflowStatus.DIFFERENTIATING: {
                WorkflowStatus.GENERATING
            },
            WorkflowStatus.GENERATING: {
                WorkflowStatus.OPTIMIZING
            },
            WorkflowStatus.OPTIMIZING: {
                WorkflowStatus.AUDITING
            },
            WorkflowStatus.AUDITING: {
                WorkflowStatus.COMPLETE,
                WorkflowStatus.RETRYING,
                WorkflowStatus.FAILED
            },
            WorkflowStatus.RETRYING: {
                WorkflowStatus.GENERATING
            },
        }
        
        if new_status not in valid_transitions.get(self.status, set()):
            raise ValueError(
                f"Invalid transition from {self.status.value} to {new_status.value}"
            )
        
        self.status = new_status
        self.updated_at = datetime.now()
    
    def log_agent_execution(
        self,
        agent_name: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Log an agent execution to the audit trail"""
        execution = AgentExecution(
            agent_name=agent_name,
            timestamp=datetime.now(),
            inputs=inputs,
            output=output,
            success=success,
            error=error,
            retry_count=self.retry_counts.get(agent_name, 0)
        )
        self.audit_trail.append(execution)
        self.agent_outputs[agent_name] = output
        self.updated_at = datetime.now()
    
    def log_error(self, error: Exception) -> None:
        """Log an error"""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "type": type(error).__name__
        })
        self.updated_at = datetime.now()
    
    def get_retry_count(self, agent_name: str) -> int:
        """Get retry count for an agent"""
        return self.retry_counts.get(agent_name, 0)
    
    def increment_retry(self, agent_name: str) -> None:
        """Increment retry count for an agent"""
        self.retry_counts[agent_name] = self.retry_counts.get(agent_name, 0) + 1
        self.updated_at = datetime.now()
    
    def log_user_interaction(self, interaction_type: str, data: Dict[str, Any]) -> None:
        """Log a user interaction"""
        self.user_interactions.append({
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "data": data
        })
        self.updated_at = datetime.now()
