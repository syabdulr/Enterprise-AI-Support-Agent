"""Bridge from the Triage agent's output into Dataverse incident records."""

import json
from datetime import datetime
from typing import Any, Dict

from .client import DataverseClient
from .models import SEVERITY_VALUES, SiteIncident


class TriageToDataverseConnector:
    """Persists triage output as structured Dataverse incident records."""

    def __init__(self, client: DataverseClient) -> None:
        self.client = client

    def persist_triage(
        self,
        triage_output: str,
        location: str,
        reporter: str,
        description: str,
    ) -> Dict[str, Any]:
        """Parse triage JSON, build a SiteIncident, and create it in Dataverse.

        Args:
            triage_output: JSON string from the Triage agent
                (IncidentPlugin.triage_incident), containing severity and
                category keys at minimum.
            location: Site/location where the incident occurred.
            reporter: Identity of the person reporting the incident.
            description: Free-text description of the incident.

        Returns:
            Dict with the created record's ID and persisted status.
        """
        try:
            triage = json.loads(triage_output)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"triage output is not valid JSON: {exc}") from exc

        severity = str(triage.get("severity", "medium"))
        if severity not in SEVERITY_VALUES:
            severity = "medium"

        incident = SiteIncident(
            location=location,
            severity=severity,
            description=description,
            reporter=reporter,
            timestamp=datetime.now(),
            status="open",
        )

        record_id = self.client.create_incident(incident)
        return {
            "dataverse_record_id": record_id,
            "status": "persisted",
            "severity": severity,
            "category": triage.get("category", "general"),
        }
