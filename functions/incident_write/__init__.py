"""HTTP-triggered Azure Function: write a site safety incident to Dataverse.

Validates the request, runs severity/category classification via the
existing IncidentPlugin triage logic, and persists a SiteIncident record
through the Dataverse Web API.
"""

import json
import logging
import os
from typing import Optional

import azure.functions as func

from src.dataverse.client import DataverseClient
from src.dataverse.connector import TriageToDataverseConnector
from src.dataverse.models import SEVERITY_VALUES, DataverseConfig
from src.sk.plugins.incident_plugins import IncidentPlugin

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ("location", "description", "reporter")


def _build_connector() -> TriageToDataverseConnector:
    """Build the Dataverse connector from environment configuration."""
    config = DataverseConfig(
        tenant_id=os.environ["DATAVERSE_TENANT_ID"],
        client_id=os.environ["DATAVERSE_CLIENT_ID"],
        client_secret=os.environ["DATAVERSE_CLIENT_SECRET"],
        org_url=os.environ["DATAVERSE_URL"],
    )
    return TriageToDataverseConnector(DataverseClient(config))


def main(
    req: func.HttpRequest,
    connector: Optional[TriageToDataverseConnector] = None,
) -> func.HttpResponse:
    """Handle POST /api/incident_write."""
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "request body must be valid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    missing = [f for f in REQUIRED_FIELDS if not body.get(f)]
    if missing:
        return func.HttpResponse(
            body=json.dumps({"error": f"missing required fields: {', '.join(missing)}"}),
            status_code=400,
            mimetype="application/json",
        )

    severity = str(body.get("severity", "medium")).lower()
    if severity not in SEVERITY_VALUES:
        return func.HttpResponse(
            body=json.dumps(
                {
                    "error": (
                        f"invalid severity '{severity}'. " f"Allowed: {', '.join(SEVERITY_VALUES)}"
                    )
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    description = str(body["description"])
    location = str(body["location"])
    reporter = str(body["reporter"])

    triage_output = IncidentPlugin().triage_incident(description, severity=severity)

    try:
        if connector is None:
            connector = _build_connector()
        result = connector.persist_triage(
            triage_output=triage_output,
            location=location,
            reporter=reporter,
            description=description,
        )
    except KeyError as exc:
        return func.HttpResponse(
            body=json.dumps({"error": f"missing environment variable: {exc}"}),
            status_code=500,
            mimetype="application/json",
        )
    except Exception as exc:  # Dataverse write failures
        logger.exception("Dataverse write failed")
        return func.HttpResponse(
            body=json.dumps({"error": f"failed to persist incident: {exc}"}),
            status_code=502,
            mimetype="application/json",
        )

    return func.HttpResponse(
        body=json.dumps(result),
        status_code=201,
        mimetype="application/json",
    )
