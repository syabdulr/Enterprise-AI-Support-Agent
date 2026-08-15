"""Models for Dataverse-backed site safety incident records."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

# Dataverse custom entity logical name and entity set name.
# The entity set name is the pluralised collection endpoint used by the
# Web API (e.g. POST /api/data/v9.2/abs_siteincidents).
ENTITY_SET_NAME = "abs_siteincidents"

SEVERITY_VALUES = ("low", "medium", "high", "critical")
STATUS_VALUES = ("open", "acknowledged", "escalated", "closed")


def _validate_choice(value: str, allowed: tuple, field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"Invalid {field_name} '{value}'. Allowed values: {', '.join(allowed)}")
    return value


@dataclass
class DataverseConfig:
    """Configuration for Dataverse Web API connection."""

    tenant_id: str
    client_id: str
    client_secret: str
    org_url: str
    api_version: str = "v9.2"


@dataclass
class SiteIncident:
    """A site safety incident stored as a Dataverse record.

    Field mapping uses the 'abs_' publisher prefix convention for
    custom entities in Dataverse.
    """

    location: str
    severity: str
    description: str
    reporter: str
    timestamp: datetime
    status: str = "open"
    incident_id: str = ""

    def __post_init__(self) -> None:
        _validate_choice(self.severity, SEVERITY_VALUES, "severity")
        _validate_choice(self.status, STATUS_VALUES, "status")

    def to_dataverse_entity(self) -> Dict[str, object]:
        """Convert to the JSON body for a Dataverse create/update call."""
        entity: Dict[str, object] = {
            "abs_location": self.location,
            "abs_severity": self.severity,
            "abs_description": self.description,
            "abs_reporter": self.reporter,
            "abs_timestamp": self.timestamp.isoformat(),
            "abs_status": self.status,
        }
        if self.incident_id:
            entity["abs_incidentid"] = self.incident_id
        return entity

    @classmethod
    def from_dataverse_entity(cls, entity: Dict[str, object]) -> "SiteIncident":
        """Build a SiteIncident from a Dataverse record payload."""
        return cls(
            location=str(entity["abs_location"]),
            severity=str(entity["abs_severity"]),
            description=str(entity["abs_description"]),
            reporter=str(entity["abs_reporter"]),
            timestamp=datetime.fromisoformat(str(entity["abs_timestamp"])),
            status=str(entity["abs_status"]),
            incident_id=str(entity.get("abs_incidentid", "")),
        )


@dataclass
class IncidentQuery:
    """Filter parameters for querying incidents from Dataverse."""

    status: str = ""
    severity: str = ""
    location: str = ""

    def to_odata_filter(self) -> str:
        """Build an OData $filter clause from the non-empty criteria."""
        clauses: List[str] = []
        if self.status:
            clauses.append(f"abs_status eq '{self.status}'")
        if self.severity:
            clauses.append(f"abs_severity eq '{self.severity}'")
        if self.location:
            clauses.append(f"abs_location eq '{self.location}'")
        return " and ".join(clauses)
