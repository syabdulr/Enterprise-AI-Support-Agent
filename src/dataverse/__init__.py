"""Dataverse integration for site safety incident records.

OAuth2 client-credentials auth against Azure AD, CRUD via the Dataverse
Web API, and a connector bridging Triage agent output into structured
incident records.
"""

from .auth import DataverseAuthenticator
from .client import DataverseClient
from .connector import TriageToDataverseConnector
from .models import DataverseConfig, IncidentQuery, SiteIncident

__all__ = [
    "DataverseAuthenticator",
    "DataverseClient",
    "TriageToDataverseConnector",
    "DataverseConfig",
    "IncidentQuery",
    "SiteIncident",
]
