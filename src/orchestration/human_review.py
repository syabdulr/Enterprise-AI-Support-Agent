"""
Human-in-the-loop integration for incident workflows.
Manages human review processes and decisions.
"""

from typing import Dict, Optional, Any
from datetime import datetime
from .state import WorkflowState


class HumanReviewManager:
    """Manages human review processes for incident workflows."""
    
    def __init__(self):
        """Initialize human review manager."""
        self.pending_reviews: Dict[str, WorkflowState] = {}
    
    def request_review(self, state: WorkflowState) -> str:
        """Request human review for an incident."""
        review_id = f"review_{state.incident_id}_{datetime.utcnow().timestamp()}"
        self.pending_reviews[review_id] = state
        state.requires_human_review = True
        state.update_timestamp()
        return review_id
    
    def submit_review(
        self,
        review_id: str,
        decision: str,
        notes: Optional[str] = None
    ) -> WorkflowState:
        """Submit human review decision."""
        if review_id not in self.pending_reviews:
            raise ValueError(f"Review {review_id} not found")
        
        state = self.pending_reviews[review_id]
        state.human_review_decision = decision
        state.human_review_notes = notes
        state.human_review_timestamp = datetime.utcnow()
        state.update_timestamp()
        
        # Remove from pending
        del self.pending_reviews[review_id]
        
        return state
    
    def get_review_request(self, review_id: str) -> Optional[WorkflowState]:
        """Get a pending review request."""
        return self.pending_reviews.get(review_id)
    
    def list_pending_reviews(self) -> list:
        """List all pending review requests."""
        return list(self.pending_reviews.keys())
    
    def generate_review_summary(self, state: WorkflowState) -> str:
        """Generate a summary for human review."""
        summary = f"""
# Human Review Request

## Incident Information
- **Incident ID:** {state.incident_id}
- **Title:** {state.incident_title}
- **Severity:** {state.severity}
- **Category:** {state.category}
- **Priority:** {state.priority}

## Incident Description
{state.incident_description}

## AI Analysis

### Root Causes
"""
        for i, cause in enumerate(state.root_causes, 1):
            summary += f"\n{i}. {cause.get('cause', 'Unknown')}"
        
        summary += f"""

### Proposed Resolution
"""
        for i, step in enumerate(state.resolution_steps, 1):
            summary += f"\n{i}. {step}"
        
        summary += f"""

### Retrieved Context
"""
        for doc in state.retrieved_context[:3]:
            summary += f"\n- {doc['metadata'].get('filename', 'Unknown')}: {doc['content'][:200]}..."
        
        summary += f"""

## Review Required
Please review the AI-generated analysis and resolution above.
Consider:
- Are the root causes accurate?
- Is the resolution procedure appropriate?
- Are there any safety concerns?
- Should this be escalated to higher-level support?

## Options
1. **Approve** - Proceed with the proposed resolution
2. **Reject** - Reject the proposal and escalate
3. **Modify** - Provide modified resolution steps

**Decision:** [Approve/Reject/Modify]
**Notes:** [Your notes here]
"""
        return summary