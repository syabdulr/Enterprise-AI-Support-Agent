"""Incident management plugin for Semantic Kernel.

Provides triage, diagnosis, resolution, and escalation as kernel functions.
Each function returns a string suitable for SK function-chaining.
"""

import json
from typing import Any, Dict, Optional

from semantic_kernel.functions import kernel_function


class IncidentPlugin:
    """SK plugin for incident management."""

    def __init__(self) -> None:
        self.name = "IncidentPlugin"

    @kernel_function(description="Categorize and prioritize an incident based on its description")
    def triage_incident(
        self,
        description: str,
        severity: str = "medium",
    ) -> str:
        """Triage an incident: categorize and assign urgency."""
        desc_lower = description.lower()

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

        result: Dict[str, Any] = {
            "category": category,
            "severity": severity,
            "urgency": urgency,
            "routing": "on_call_engineer" if urgency >= 3 else "queue",
            "assessment": f"Incident categorized as {category} with {severity} severity",
        }
        return json.dumps(result)

    @kernel_function(description="Diagnose probable root causes for an incident")
    def diagnose_incident(
        self,
        description: str,
        category: str = "general",
        context: Optional[str] = None,
    ) -> str:
        """Diagnose the root cause of an incident."""
        context_dict: Dict[str, Any] = {}
        if context:
            try:
                context_dict = json.loads(context)
            except (json.JSONDecodeError, TypeError):
                context_dict = {}

        probable_causes: list = []
        desc_lower = description.lower()

        if category == "database":
            probable_causes.extend(["Connection pool exhaustion", "Long-running query blocking"])
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
            probable_causes.extend(["DNS resolution failure", "Firewall rule blocking traffic"])
        elif category == "application":
            probable_causes.extend(
                [
                    "Unhandled exception in request handler",
                    "Dependency service unavailable",
                ]
            )
        else:
            probable_causes.append("Requires manual investigation")

        if "last_deploy" in context_dict:
            probable_causes.insert(
                0, f"Recent deployment may be related ({context_dict['last_deploy']})"
            )

        result: Dict[str, Any] = {
            "category": category,
            "probable_causes": probable_causes,
            "recommended_actions": [f"Investigate: {c}" for c in probable_causes[:3]],
            "confidence": 0.75 if probable_causes else 0.3,
        }
        return json.dumps(result)

    @kernel_function(description="Generate resolution steps for a diagnosed incident")
    def resolve_incident(
        self,
        description: str,
        diagnosis: str,
        category: str = "general",
    ) -> str:
        """Generate resolution steps for a diagnosed incident."""
        resolution_steps: list = []
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

        result: Dict[str, Any] = {
            "category": category,
            "diagnosis": diagnosis,
            "steps": resolution_steps,
            "estimated_time": "15-30 minutes",
            "requires_restart": "restart" in " ".join(resolution_steps).lower(),
        }
        return json.dumps(result)

    @kernel_function(description="Escalate an incident to human review")
    def escalate_incident(
        self,
        description: str,
        reason: str,
        severity: str = "high",
    ) -> str:
        """Escalate an incident to human review."""
        result: Dict[str, Any] = {
            "escalated": True,
            "reason": reason,
            "severity": severity,
            "action": "human_review_required",
            "notification": f"ONCALL ALERT: {severity} incident requires human review: {reason}",
            "context": description[:200],
        }
        return json.dumps(result)
