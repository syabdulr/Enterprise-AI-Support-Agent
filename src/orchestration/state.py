"""
State management for LangGraph workflows.
Defines the state schema for multi-agent incident response workflows.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class IncidentCategory(str, Enum):
    """Incident categories."""
    NETWORK = "Network"
    APPLICATION = "Application"
    DATABASE = "Database"
    SECURITY = "Security"
    INFRASTRUCTURE = "Infrastructure"
    OTHER = "Other"


class IncidentPriority(str, Enum):
    """Incident priority levels."""
    P0 = "P0"  # Critical, immediate action required
    P1 = "P1"  # High, action required within 1 hour
    P2 = "P2"  # Medium, action required within 4 hours
    P3 = "P3"  # Low, action required within 24 hours


class WorkflowState(BaseModel):
    """Complete state for incident response workflow."""
    
    # Incident information
    incident_id: str = Field(description="Unique incident identifier")
    incident_title: str = Field(description="Incident title or summary")
    incident_description: str = Field(description="Detailed incident description")
    
    # Triage information
    severity: Optional[IncidentSeverity] = None
    category: Optional[IncidentCategory] = None
    priority: Optional[IncidentPriority] = None
    impact_assessment: Optional[str] = None
    escalate_immediately: bool = False
    
    # Diagnosis information
    root_causes: List[Dict[str, Any]] = Field(default_factory=list)
    diagnostic_steps: List[str] = Field(default_factory=list)
    components_affected: List[str] = Field(default_factory=list)
    escalation_risk: str = "Medium"
    
    # Resolution information
    resolution_steps: List[str] = Field(default_factory=list)
    verification_steps: List[str] = Field(default_factory=list)
    rollback_procedures: List[str] = Field(default_factory=list)
    estimated_resolution_time: Optional[str] = None
    resolution_status: str = "Not Started"
    
    # RAG retrieved context
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Human review information
    requires_human_review: bool = False
    human_review_notes: Optional[str] = None
    human_review_decision: Optional[str] = None
    human_review_timestamp: Optional[datetime] = None
    
    # Workflow metadata
    current_agent: str = "triage"
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    workflow_status: str = "in_progress"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True
    
    def update_timestamp(self):
        """Update the timestamp."""
        self.updated_at = datetime.utcnow()
    
    def add_error(self, error: str):
        """Add an error to the state."""
        self.errors.append(error)
        self.update_timestamp()
    
    def add_warning(self, warning: str):
        """Add a warning to the state."""
        self.warnings.append(warning)
        self.update_timestamp()
    
    def add_to_conversation(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.update_timestamp()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """Create state from dictionary."""
        return cls(**data)