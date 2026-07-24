"""
Agent coordinator for multi-agent workflows.
Routes incidents to appropriate agents and manages agent transitions.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from .state import WorkflowState, IncidentSeverity, IncidentPriority


class AgentType(str, Enum):
    """Available agent types."""
    TRIAGE = "triage"
    DIAGNOSIS = "diagnosis"
    RESOLUTION = "resolution"
    ESCALATION = "escalation"
    HUMAN_REVIEW = "human_review"


class AgentCoordinator:
    """Coordinates agent selection and workflow transitions."""
    
    def __init__(self):
        """Initialize agent coordinator."""
        self.agent_transitions = {
            AgentType.TRIAGE: [
                AgentType.DIAGNOSIS,
                AgentType.ESCALATION
            ],
            AgentType.DIAGNOSIS: [
                AgentType.RESOLUTION,
                AgentType.ESCALATION,
                AgentType.TRIAGE  # Re-triage if needed
            ],
            AgentType.RESOLUTION: [
                AgentType.TRIAGE,  # Re-triage after resolution
                AgentType.DIAGNOSIS,  # Re-diagnose if resolution fails
                AgentType.ESCALATION
            ],
            AgentType.ESCALATION: [
                AgentType.HUMAN_REVIEW,
                AgentType.TRIAGE
            ],
            AgentType.HUMAN_REVIEW: [
                AgentType.RESOLUTION,  # Proceed with resolution
                AgentType.ESCALATION,  # Continue escalation
                AgentType.TRIAGE  # Start over
            ]
        }
    
    def determine_next_agent(
        self,
        state: WorkflowState
    ) -> AgentType:
        """Determine the next agent based on current state."""
        current_agent = AgentType(state.current_agent)
        
        # If severity is Critical, escalate immediately
        if state.severity == IncidentSeverity.CRITICAL and not state.escalate_immediately:
            return AgentType.ESCALATION
        
        # If human review required, route to human review agent
        if state.requires_human_review and current_agent != AgentType.HUMAN_REVIEW:
            return AgentType.HUMAN_REVIEW
        
        # If triage complete, move to diagnosis
        if current_agent == AgentType.TRIAGE and state.severity and state.category:
            return AgentType.DIAGNOSIS
        
        # If diagnosis complete, move to resolution
        if current_agent == AgentType.DIAGNOSIS and state.root_causes:
            return AgentType.RESOLUTION
        
        # If resolution complete, workflow done
        if current_agent == AgentType.RESOLUTION and state.resolution_status == "Complete":
            state.workflow_status = "completed"
            return current_agent
        
        # Default: escalate if uncertain
        return AgentType.ESCALATION
    
    def can_transition_to(
        self,
        from_agent: AgentType,
        to_agent: AgentType
    ) -> bool:
        """Check if transition from one agent to another is allowed."""
        return to_agent in self.agent_transitions.get(from_agent, [])
    
    def get_agent_description(self, agent_type: AgentType) -> str:
        """Get description of an agent's role."""
        descriptions = {
            AgentType.TRIAGE: "Categorizes incidents, assigns severity, determines priority",
            AgentType.DIAGNOSIS: "Analyzes root causes, identifies affected components, assesses escalation risk",
            AgentType.RESOLUTION: "Generates resolution procedures, provides step-by-step solutions",
            AgentType.ESCALATION: "Prepares escalation packages, coordinates human handoff",
            AgentType.HUMAN_REVIEW: "Facilitates human review of AI recommendations, captures human decisions"
        }
        return descriptions.get(agent_type, "Unknown agent")
    
    def should_escalate(self, state: WorkflowState) -> bool:
        """Determine if incident should be escalated to human review."""
        # Escalate if critical
        if state.severity == IncidentSeverity.CRITICAL:
            return True
        
        # Escalate if high priority with significant errors
        if state.priority == IncidentPriority.P0 and state.errors:
            return True
        
        # Escalate if requested
        if state.escalate_immediately:
            return True
        
        # Escalate if high escalation risk
        if state.escalation_risk == "High":
            return True
        
        return False
    
    def requires_human_verification(self, state: WorkflowState) -> bool:
        """Determine if human verification is required."""
        # Require verification for critical incidents
        if state.severity == IncidentSeverity.CRITICAL:
            return True
        
        # Require verification for security incidents
        if state.category and "security" in state.category.lower():
            return True
        
        # Require verification if there are errors
        if state.errors:
            return True
        
        return False