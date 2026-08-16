"""Autogen-based severity review loop for triage classifications.

Two pyautogen ConversableAgents — one holding the original Triage
classification, one acting as severity reviewer — exchange messages in a
bounded two-round conversation before escalation proceeds. The reviewer
applies a deterministic category-floor policy, so the loop runs without
an LLM; with one configured, the same reply-resolution pipeline applies.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.sk.plugins.incident_plugins import IncidentPlugin  # noqa: F401

try:
    import autogen
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pyautogen is required for the severity review loop: " "pip install pyautogen"
    ) from exc

SEVERITY_ORDER = ["low", "medium", "high", "critical"]

# Minimum severity the reviewer will accept for each triage category.
CATEGORY_FLOORS = {
    "security": "high",
    "infrastructure": "medium",
    "database": "medium",
    "network": "medium",
    "application": "low",
    "general": "low",
}

MAX_REVIEW_ROUNDS = 2


@dataclass
class ReviewDecision:
    """Outcome of the severity review conversation."""

    decision: str
    severity: str
    reason: str

    def __post_init__(self) -> None:
        if self.decision not in ("confirmed", "challenged"):
            raise ValueError(
                f"decision must be 'confirmed' or 'challenged', " f"got {self.decision!r}"
            )
        if self.severity not in SEVERITY_ORDER:
            raise ValueError(f"severity must be one of {SEVERITY_ORDER}, got {self.severity!r}")


def _severity_at_least(actual: str, floor: str) -> bool:
    return SEVERITY_ORDER.index(actual) >= SEVERITY_ORDER.index(floor)


def _terminate_on_final(message: Dict[str, Any]) -> bool:
    return "TERMINATE" in str(message.get("content", ""))


def build_review_agents() -> Tuple[autogen.ConversableAgent, autogen.ConversableAgent]:
    """Create the two conversation participants with bounded auto-reply."""
    triage_agent = autogen.ConversableAgent(
        name="TriageAgent",
        system_message=(
            "Holds the original triage classification and presents it " "for severity review."
        ),
        llm_config=False,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=MAX_REVIEW_ROUNDS,
        is_termination_msg=_terminate_on_final,
    )
    reviewer_agent = autogen.ConversableAgent(
        name="SeverityReviewerAgent",
        system_message=(
            "Reviews triage classifications against category severity "
            "floors and confirms or challenges them."
        ),
        llm_config=False,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=MAX_REVIEW_ROUNDS,
        is_termination_msg=_terminate_on_final,
    )
    return triage_agent, reviewer_agent


class SeverityReviewOrchestrator:
    """Runs the bounded two-round severity review conversation."""

    def __init__(self) -> None:
        self.last_chat_result: Optional[Any] = None
        self.triage_agent, self.reviewer_agent = build_review_agents()
        self._register_replies()

    def _register_replies(self) -> None:
        self.reviewer_agent.register_reply(autogen.ConversableAgent, self._reviewer_reply)
        self.triage_agent.register_reply(autogen.ConversableAgent, self._triage_reply)

    def _reviewer_reply(
        self,
        recipient: autogen.ConversableAgent,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional[Any] = None,
        config: Optional[Any] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Reply policy: check the presented severity against the floor."""
        msgs = messages or []
        content = str(msgs[-1]["content"]) if msgs else ""
        try:
            triage = json.loads(content)
        except json.JSONDecodeError:
            # not a triage classification (e.g. final-decision echo) —
            # defer to the built-in handlers so termination applies
            return False, None
        category = triage.get("category", "general")
        severity = triage.get("severity", "low")
        floor = CATEGORY_FLOORS.get(category, "low")

        if _severity_at_least(severity, floor):
            verdict = {
                "decision": "confirmed",
                "proposed_severity": severity,
                "floor": floor,
                "reason": f"{severity} meets the {category} floor of {floor}",
            }
            return True, f"REVIEW_VERDICT: {json.dumps(verdict)} TERMINATE"

        verdict = {
            "decision": "challenged",
            "proposed_severity": floor,
            "floor": floor,
            "reason": f"{severity} is below the {category} floor of {floor}",
        }
        return True, f"REVIEW_VERDICT: {json.dumps(verdict)}"

    def _triage_reply(
        self,
        recipient: autogen.ConversableAgent,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional[Any] = None,
        config: Optional[Any] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Reply policy: accept a reviewer challenge and issue the final call."""
        msgs = messages or []
        content = str(msgs[-1]["content"]) if msgs else ""
        if "REVIEW_VERDICT:" not in content:
            return False, None
        payload = content.split("REVIEW_VERDICT:", 1)[1]
        payload = payload.replace(" TERMINATE", "").strip()
        verdict = json.loads(payload)

        final = {
            "decision": verdict["decision"],
            "severity": verdict["proposed_severity"],
            "reason": verdict["reason"],
        }
        return True, f"FINAL_DECISION: {json.dumps(final)} TERMINATE"

    @staticmethod
    def _extract_verdict(message_content: str) -> Dict[str, Any]:
        payload = message_content.split("REVIEW_VERDICT:", 1)[1]
        payload = payload.replace(" TERMINATE", "").strip()
        verdict: Dict[str, Any] = json.loads(payload)
        return verdict

    def review(self, triage_output: str) -> ReviewDecision:
        """Run the review conversation over a triage classification."""
        try:
            triage = json.loads(triage_output)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"triage_output is not valid JSON: {exc}") from exc

        # fresh agents per review so chat history never leaks between runs
        self.triage_agent, self.reviewer_agent = build_review_agents()
        self._register_replies()

        self.last_chat_result = self.triage_agent.initiate_chat(
            self.reviewer_agent,
            message=triage_output,
            silent=True,
        )

        history = self.triage_agent.chat_messages[self.reviewer_agent]
        final_messages = [m for m in history if "FINAL_DECISION:" in str(m.get("content", ""))]
        if final_messages:
            payload = final_messages[-1]["content"].split("FINAL_DECISION:", 1)[1]
            payload = payload.replace(" TERMINATE", "").strip()
            final = json.loads(payload)
            return ReviewDecision(
                decision=final["decision"],
                severity=final["severity"],
                reason=final["reason"],
            )

        # no challenge occurred — the reviewer confirmed and terminated
        verdict_messages = [m for m in history if "REVIEW_VERDICT:" in str(m.get("content", ""))]
        verdict = self._extract_verdict(verdict_messages[-1]["content"])
        return ReviewDecision(
            decision=verdict["decision"],
            severity=triage["severity"],
            reason=verdict["reason"],
        )
