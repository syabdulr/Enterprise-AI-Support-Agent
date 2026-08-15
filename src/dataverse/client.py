"""Client for the Dataverse Web API — CRUD on site safety incident records."""

from typing import Any, Dict, List, Optional, cast

import requests

from .auth import DataverseAuthenticator
from .models import ENTITY_SET_NAME, DataverseConfig, IncidentQuery, SiteIncident


class DataverseClient:
    """CRUD operations against the Dataverse Web API."""

    def __init__(self, config: DataverseConfig) -> None:
        self.config = config
        self.authenticator = DataverseAuthenticator(config)
        self._api_base = f"{self.config.org_url.rstrip('/')}/api/data/{self.config.api_version}"

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = self.authenticator.get_auth_header()
        headers.update(
            {
                "OData-MaxVersion": "4.0",
                "OData-Version": "4.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        if extra:
            headers.update(extra)
        return headers

    def _entity_url(self, incident_id: str = "") -> str:
        if incident_id:
            return f"{self._api_base}/{ENTITY_SET_NAME}({incident_id})"
        return f"{self._api_base}/{ENTITY_SET_NAME}"

    def create_incident(self, incident: SiteIncident) -> str:
        """Create an incident record. Returns the new record's ID."""
        response = requests.post(
            self._entity_url(),
            json=cast(Any, incident.to_dataverse_entity()),
            headers=self._headers({"Prefer": "return=representation"}),
        )
        if response.status_code not in (200, 201, 204):
            raise Exception(
                f"Dataverse create failed: {response.status_code} - {response.text[:200]}"
            )
        entity_id = response.headers.get("OData-EntityId", "")
        if "(" in entity_id and ")" in entity_id:
            return entity_id[entity_id.rfind("(") + 1 : entity_id.rfind(")")]
        payload = response.json() if response.text else {}
        return str(payload.get("abs_incidentid", ""))

    def get_incident(self, incident_id: str) -> SiteIncident:
        """Fetch a single incident record by ID."""
        response = requests.get(self._entity_url(incident_id), headers=self._headers())
        if response.status_code != 200:
            raise Exception(
                f"Dataverse read failed: {response.status_code} - {response.text[:200]}"
            )
        return SiteIncident.from_dataverse_entity(response.json())

    def get_incidents(
        self,
        status: str = "",
        severity: str = "",
        location: str = "",
    ) -> List[SiteIncident]:
        """Query incident records with OData $filter criteria."""
        query = IncidentQuery(status=status, severity=severity, location=location)
        odata_filter = query.to_odata_filter()
        params: Dict[str, str] = {}
        if odata_filter:
            params["$filter"] = odata_filter

        response = requests.get(self._entity_url(), headers=self._headers(), params=params)
        if response.status_code != 200:
            raise Exception(
                f"Dataverse query failed: {response.status_code} - {response.text[:200]}"
            )
        return [
            SiteIncident.from_dataverse_entity(item) for item in response.json().get("value", [])
        ]

    def update_incident_status(self, incident_id: str, status: str) -> None:
        """Update an incident record's status via PATCH."""
        response = requests.patch(
            self._entity_url(incident_id),
            json=cast(Any, {"abs_status": status}),
            headers=self._headers(),
        )
        if response.status_code not in (200, 204):
            raise Exception(
                f"Dataverse update failed: {response.status_code} - {response.text[:200]}"
            )
