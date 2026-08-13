"""Incident management plugin for Semantic Kernel.

This plugin wraps our existing agent capabilities (triage, diagnosis,
resolution, escalation) as SK kernel functions. In production, these
would call the LangGraph workflow; here they provide deterministic
rule-based logic so the system is testable without LLM credentials.
"""

import re
from typing import Any, Dict, Optional


class IncidentPlugin:
    """SK plugin for incident management agentic patterns."""

    def __init__(self) -> None:
        self.name = "IncidentPlugin"

    def triage_incident(self, description: str, severity: str = "medium") -> Dict[str, Any]:
        """
        Categorize and prioritize an incident.

        Implements the planning agentic pattern: analyzes the incident
        description to determine category, urgency, and routing.
        """
        desc_lower = description.lower()

        # Categorization rules
        if any(kw in desc_lower for kw in ["database", "db", "sql", "query"]):
            category = "database"
        elif any(kw in desc_lower for kw in ["server", "cpu", "memory", "disk", "infrastructure"]):
            category = "infrastructure"
        elif any(kw in desc_lower for kw in ["network", "latency", "timeout", "connection"]):
            category = "network"
        elif any(kw in desc_lower for kw in ["api", "endpoint", "500", "error"]):
            category = "application"
        elif any(kw in desc_lower for kw in ["ssl", "certificate", "auth", "security"]):
            category = "security"
        else:
            category = "general"

        severity_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        urgency = severity_scores.get(severity, 2)

        return {
            "category": category,
            "severity": severity,
            "urgency": urgency,
            "routing": "on_call_engineer" if urgency >= 3 else "queue",
            "assessment": f"Incident categorized as {category} with {severity} severity",
        }

    def diagnose_incident(
        self,
        description: str,
        category: str = "general",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Diagnose the root cause of an incident.

        Implements the tool-use pattern: uses context signals to
        narrow down probable root causes.
        """
        context = context or {}
        probable_causes = []

        desc_lower = description.lower()

        if category == "database":
            probable_causes.append("Connection pool exhaustion")
            probable_causes.append("Long-running query blocking")
        elif category == "infrastructure":
            if "cpu" in desc_lower:
                probable_causes.append("CPU spike from runaway process")
            if "disk" in desc_lower or "space" in desc_lower:
                probable_causes.append("Disk space exhaustion from logs")
            if "memory" in desc_lower:
                probable_causes.append("Memory leak in application process")
            if not probable_causes:
                probable_causes.append("Resource saturation")
        elif category == "network":
            probable_causes.append("DNS resolution failure")
            probable_causes.append("Firewall rule blocking traffic")
        elif category == "application":
            probable_causes.append("Unhandled exception in request handler")
            probable_causes.append("Dependency service unavailable")
        else:
            probable_causes.append("Requires manual investigation")

        # Use context clues
        if "last_deploy" in context:
            probable_causes.insert(
                0, f"Recent deployment may be related ({context['last_deploy']})"
            )

        return {
            "category": category,
            "probable_causes": probable_causes,
            "recommended_actions": [f"Investigate: {cause}" for cause in probable_causes[:3]],
            "confidence": 0.75 if probable_causes else 0.3,
        }

    def resolve_incident(
        self,
        description: str,
        diagnosis: str,
        category: str = "general",
    ) -> Dict[str, Any]:
        """
        Generate resolution steps for a diagnosed incident.

        Implements the planning pattern: creates step-by-step resolution.
        """
        resolution_steps = []
        desc_lower = description.lower()

        if "disk" in desc_lower or "space" in desc_lower:
            resolution_steps = [
                "1. Identify large files: du -sh /var/log/*",
                "2. Rotate or archive old logs",
                "3. Clear temp directories",
                "4. Monitor disk usage after cleanup",
            ]
        elif "database" in desc_lower or "timeout" in desc_lower:
            resolution_steps = [
                "1. Check active connections: SHOW PROCESSLIST",
                "2. Identify long-running queries",
                "3. Kill blocking queries if safe",
                "4. Review connection pool settings",
            ]
        elif "cpu" in desc_lower:
            resolution_steps = [
                "1. Identify top processes: top -o %CPU",
                "2. Check for runaway processes",
                "3. Restart service if necessary",
                "4. Review scaling policies",
            ]
        else:
            resolution_steps = [
                "1. Verify current system state",
                "2. Check recent changes and deployments",
                "3. Review monitoring dashboards",
                "4. Escalate if no resolution found",
            ]

        return {
            "category": category,
            "diagnosis": diagnosis,
            "steps": resolution_steps,
            "estimated_time": "15-30 minutes",
            "requires_restart": "restart" in " ".join(resolution_steps).lower(),
        }

    def escalate_incident(
        self,
        description: str,
        reason: str,
        severity: str = "high",
    ) -> Dict[str, Any]:
        """
        Escalate an incident to human review.

        Implements the guardrail pattern: ensures critical incidents
        get human oversight when automated resolution fails.
        """
        return {
            "escalated": True,
            "reason": reason,
            "severity": severity,
            "action": "human_review_required",
            "notification": f"ONCALL ALERT: {severity} incident requires human review: {reason}",
            "context": description[:200],
        }
