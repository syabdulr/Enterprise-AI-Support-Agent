"""
Tests for LangGraph orchestration and workflow components.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestration.state import WorkflowState, IncidentSeverity, IncidentPriority
from orchestration.agent_coordinator import AgentCoordinator, AgentType
from orchestration.human_review import HumanReviewManager


def test_workflow_state_initialization():
    """Test workflow state initialization."""
    state = WorkflowState(
        incident_id="INC-001",
        incident_title="Test Incident",
        incident_description="Test description"
    )
    
    assert state.incident_id == "INC-001"
    assert state.workflow_status == "in_progress"
    assert state.current_agent == "triage"
    assert len(state.errors) == 0


def test_severity_enum():
    """Test severity enum values."""
    assert IncidentSeverity.CRITICAL.value == "Critical"
    assert IncidentSeverity.HIGH.value == "High"
    assert IncidentSeverity.MEDIUM.value == "Medium"
    assert IncidentSeverity.LOW.value == "Low"


def test_priority_enum():
    """Test priority enum values."""
    assert IncidentPriority.P0.value == "P0"
    assert IncidentPriority.P1.value == "P1"
    assert IncidentPriority.P2.value == "P2"
    assert IncidentPriority.P3.value == "P3"


def test_agent_coordinator_initialization():
    """Test agent coordinator initialization."""
    coordinator = AgentCoordinator()
    assert coordinator is not None
    assert len(coordinator.agent_transitions) == 5


def test_agent_transitions():
    """Test agent transition rules."""
    coordinator = AgentCoordinator()
    
    # Can transition from triage to diagnosis
    assert coordinator.can_transition_to(
        AgentType.TRIAGE,
        AgentType.DIAGNOSIS
    )
    
    # Can transition from triage to escalation
    assert coordinator.can_transition_to(
        AgentType.TRIAGE,
        AgentType.ESCALATION
    )
    
    # Cannot transition from triage to resolution directly
    assert not coordinator.can_transition_to(
        AgentType.TRIAGE,
        AgentType.RESOLUTION
    )


def test_should_escalate():
    """Test escalation decision logic."""
    coordinator = AgentCoordinator()
    
    # Critical severity should escalate
    state = WorkflowState(
        incident_id="INC-001",
        incident_title="Critical Incident",
        incident_description="Critical issue"
    )
    state.severity = IncidentSeverity.CRITICAL
    
    assert coordinator.should_escalate(state) is True
    
    # Medium severity with errors should not escalate
    state.severity = IncidentSeverity.MEDIUM
    state.errors = ["Test error"]
    
    assert coordinator.should_escalate(state) is False
    
    # Low severity with immediate escalation flag should escalate
    state.severity = IncidentSeverity.LOW
    state.escalate_immediately = True
    
    assert coordinator.should_escalate(state) is True


def test_human_review_manager():
    """Test human review manager."""
    manager = HumanReviewManager()
    
    state = WorkflowState(
        incident_id="INC-001",
        incident_title="Test Incident",
        incident_description="Test description"
    )
    
    # Request review
    review_id = manager.request_review(state)
    assert review_id.startswith("review_")
    assert review_id in manager.pending_reviews
    
    # Get review request
    retrieved_state = manager.get_review_request(review_id)
    assert retrieved_state.incident_id == "INC-001"
    
    # Submit review
    reviewed_state = manager.submit_review(review_id, "approve", "Looks good")
    assert reviewed_state.human_review_decision == "approve"
    assert reviewed_state.human_review_notes == "Looks good"
    assert review_id not in manager.pending_reviews


def test_state_add_error():
    """Test adding errors to state."""
    state = WorkflowState(
        incident_id="INC-001",
        incident_title="Test Incident",
        incident_description="Test description"
    )
    
    state.add_error("Test error")
    assert len(state.errors) == 1
    assert state.errors[0] == "Test error"
    assert state.updated_at is not None


def test_state_add_to_conversation():
    """Test adding messages to conversation history."""
    state = WorkflowState(
        incident_id="INC-001",
        incident_title="Test Incident",
        incident_description="Test description"
    )
    
    state.add_to_conversation("user", "Hello")
    state.add_to_conversation("assistant", "Hi there!")
    
    assert len(state.conversation_history) == 2
    assert state.conversation_history[0]["role"] == "user"
    assert state.conversation_history[1]["role"] == "assistant"


def test_generate_review_summary():
    """Test review summary generation."""
    manager = HumanReviewManager()
    
    state = WorkflowState(
        incident_id="INC-001",
        incident_title="Test Incident",
        incident_description="Test description"
    )
    state.severity = IncidentSeverity.HIGH
    state.root_causes = [{"cause": "Test cause"}]
    state.resolution_steps = ["Step 1", "Step 2"]
    
    summary = manager.generate_review_summary(state)
    
    assert "INC-001" in summary
    assert "Test Incident" in summary
    assert "Test cause" in summary
    assert "Step 1" in summary