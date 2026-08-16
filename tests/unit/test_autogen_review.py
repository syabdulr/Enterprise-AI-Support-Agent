"""Tests for the Autogen severity-review conversation loop.

Real pyautogen ConversableAgents drive the conversation (initiate_chat,
registered reply functions, termination conditions, chat history). The
review policy is deterministic, so no LLM is configured; a test asserts
the OpenAI client is never reached. The Autogen library itself is never
mocked.
"""

import json
from unittest.mock import patch

import autogen
import pytest

from src.autogen_review.reviewer import (
    SEVERITY_ORDER,
    ReviewDecision,
    SeverityReviewOrchestrator,
    build_review_agents,
)


def triage_json(severity: str, category: str) -> str:
    return json.dumps(
        {
            "category": category,
            "severity": severity,
            "urgency": SEVERITY_ORDER.index(severity) + 1,
            "routing": "queue",
            "assessment": f"Incident categorized as {category} with {severity} severity",
        }
    )


class TestBuildReviewAgents:
    def test_creates_two_conversable_agents(self):
        triage, reviewer = build_review_agents()
        assert isinstance(triage, autogen.ConversableAgent)
        assert isinstance(reviewer, autogen.ConversableAgent)

    def test_agents_have_distinct_roles(self):
        triage, reviewer = build_review_agents()
        assert triage.name == "TriageAgent"
        assert reviewer.name == "SeverityReviewerAgent"

    def test_conversation_bounded_to_two_rounds(self):
        triage, reviewer = build_review_agents()
        assert triage.max_consecutive_auto_reply() == 2
        assert reviewer.max_consecutive_auto_reply() == 2


class TestReviewDecision:
    def test_confirmed_decision_fields(self):
        d = ReviewDecision(
            decision="confirmed",
            severity="high",
            reason="Severity meets the category floor",
        )
        assert d.decision == "confirmed"
        assert d.severity == "high"

    def test_invalid_decision_rejected(self):
        with pytest.raises(ValueError):
            ReviewDecision(decision="maybe", severity="high", reason="x")

    def test_invalid_severity_rejected(self):
        with pytest.raises(ValueError):
            ReviewDecision(decision="confirmed", severity="extreme", reason="x")


class TestSeverityReviewOrchestrator:
    def test_security_low_severity_gets_challenged_upward(self):
        decision = SeverityReviewOrchestrator().review(triage_json("low", "security"))
        assert decision.decision == "challenged"
        assert decision.severity == "high"

    def test_severity_meeting_policy_floor_is_confirmed(self):
        decision = SeverityReviewOrchestrator().review(triage_json("high", "security"))
        assert decision.decision == "confirmed"
        assert decision.severity == "high"

    def test_database_medium_is_confirmed(self):
        decision = SeverityReviewOrchestrator().review(triage_json("medium", "database"))
        assert decision.decision == "confirmed"
        assert decision.severity == "medium"

    def test_review_runs_real_message_passing(self):
        orch = SeverityReviewOrchestrator()
        orch.review(triage_json("low", "security"))

        triage, reviewer = orch.triage_agent, orch.reviewer_agent
        history = triage.chat_messages[reviewer]
        roles = [m["role"] for m in history]
        assert roles[0] == "assistant"  # triage's opening message
        assert "user" in roles  # reviewer replied through the real pipeline
        # bounded loop: opening + at most 2 rounds on each side
        assert len(history) <= 5

    def test_final_decision_present_in_chat_history(self):
        orch = SeverityReviewOrchestrator()
        decision = orch.review(triage_json("low", "security"))

        history = orch.triage_agent.chat_messages[orch.reviewer_agent]
        final_messages = [m for m in history if "FINAL_DECISION:" in str(m.get("content", ""))]
        assert final_messages, "expected a FINAL_DECISION message"
        payload = final_messages[-1]["content"].split("FINAL_DECISION:", 1)[1]
        payload = payload.replace(" TERMINATE", "").strip()
        assert json.loads(payload)["decision"] == decision.decision

    def test_invalid_triage_json_raises(self):
        with pytest.raises(ValueError):
            SeverityReviewOrchestrator().review("not json at all")

    def test_llm_client_never_invoked(self):
        """The review policy is deterministic — the OpenAI boundary stays untouched."""
        orch = SeverityReviewOrchestrator()
        with patch("openai.Completion.create") as mock_completion:
            orch.review(triage_json("high", "network"))
        mock_completion.assert_not_called()

    def test_last_chat_result_populated_after_review(self):
        orch = SeverityReviewOrchestrator()
        assert orch.last_chat_result is None
        orch.review(triage_json("high", "network"))
        assert orch.last_chat_result is not None
