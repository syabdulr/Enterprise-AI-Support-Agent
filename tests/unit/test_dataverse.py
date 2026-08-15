"""Tests for Dataverse integration — site safety incident records.

Network boundary mocking only (requests.post / requests.get), the same
pattern used in tests/unit/test_graph_connector.py. The client, auth,
and connector code under test is real.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.dataverse.auth import DataverseAuthenticator
from src.dataverse.client import DataverseClient
from src.dataverse.connector import TriageToDataverseConnector
from src.dataverse.models import SiteIncident


def make_auth_response(token: str = "fake-token-123", expires_in: int = 3600) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": token, "expires_in": expires_in}
    return resp


def make_api_response(status: int = 200, payload: dict = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload or {}
    return resp


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestSiteIncidentModel:
    def test_model_accepts_valid_severity(self):
        inc = SiteIncident(
            location="Site A - North Tower",
            severity="high",
            description="Worker reported unstable scaffolding on level 3",
            reporter="jsmith@aecon.com",
            timestamp=datetime(2026, 8, 13, 10, 30, 0),
            status="open",
        )
        assert inc.severity == "high"
        assert inc.status == "open"

    def test_model_rejects_invalid_severity(self):
        with pytest.raises(Exception):
            SiteIncident(
                location="Site A",
                severity="catastrophic",
                description="test",
                reporter="x@y.com",
                timestamp=datetime.now(),
                status="open",
            )

    def test_model_rejects_invalid_status(self):
        with pytest.raises(Exception):
            SiteIncident(
                location="Site A",
                severity="high",
                description="test",
                reporter="x@y.com",
                timestamp=datetime.now(),
                status="maybe",
            )

    def test_to_dataverse_entity_maps_fields(self):
        inc = SiteIncident(
            location="Site B",
            severity="critical",
            description="Crane load dropped near crew",
            reporter="amore@aecon.com",
            timestamp=datetime(2026, 8, 13, 14, 0, 0),
            status="open",
        )
        entity = inc.to_dataverse_entity()
        assert entity["abs_location"] == "Site B"
        assert entity["abs_severity"] == "critical"
        assert entity["abs_description"] == "Crane load dropped near crew"
        assert entity["abs_reporter"] == "amore@aecon.com"

    def test_to_dataverse_entity_uses_iso_format_timestamp(self):
        inc = SiteIncident(
            location="Site B",
            severity="low",
            description="Minor spill contained",
            reporter="x@y.com",
            timestamp=datetime(2026, 8, 13, 9, 15, 30),
            status="closed",
        )
        entity = inc.to_dataverse_entity()
        assert entity["abs_timestamp"] == "2026-08-13T09:15:30"

    def test_from_dataverse_entity_round_trip(self):
        inc = SiteIncident(
            location="Site C",
            severity="medium",
            description="PPE missing at gate 2",
            reporter="z@y.com",
            timestamp=datetime(2026, 8, 13, 8, 0, 0),
            status="acknowledged",
        )
        entity = inc.to_dataverse_entity()
        entity["abs_incidentid"] = "guid-1234"
        restored = SiteIncident.from_dataverse_entity(entity)
        assert restored.location == "Site C"
        assert restored.severity == "medium"
        assert restored.status == "acknowledged"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TestDataverseAuthenticator:
    def _auth(self) -> DataverseAuthenticator:
        from src.dataverse.models import DataverseConfig

        return DataverseAuthenticator(
            DataverseConfig(
                tenant_id="tenant-abc",
                client_id="client-123",
                client_secret="secret-xyz",
                org_url="https://testorg.crm.dynamics.com",
            )
        )

    def test_get_token_posts_to_tenant_token_endpoint(self):
        auth = self._auth()
        with patch(
            "src.dataverse.auth.requests.post", return_value=make_auth_response()
        ) as mock_post:
            token = auth.get_token()
        assert token == "fake-token-123"
        args, kwargs = mock_post.call_args
        assert "tenant-abc" in args[0]
        assert "oauth2/v2.0/token" in args[0]
        assert kwargs["data"]["client_id"] == "client-123"
        assert kwargs["data"]["grant_type"] == "client_credentials"
        assert kwargs["data"]["scope"] == "https://testorg.crm.dynamics.com/.default"

    def test_get_token_raises_on_failure(self):
        auth = self._auth()
        bad = make_auth_response()
        bad.status_code = 401
        bad.json.return_value = {"error": "invalid_client"}
        with patch("src.dataverse.auth.requests.post", return_value=bad):
            with pytest.raises(Exception, match="Dataverse authentication failed"):
                auth.get_token()

    def test_token_cached_until_expiry(self):
        auth = self._auth()
        with patch(
            "src.dataverse.auth.requests.post", return_value=make_auth_response()
        ) as mock_post:
            auth.get_token()
            auth.get_token()
            auth.get_token()
        assert mock_post.call_count == 1

    def test_token_refetched_after_expiry(self):
        auth = self._auth()
        expired = make_auth_response(token="old", expires_in=-10)
        fresh = make_auth_response(token="new")
        with patch("src.dataverse.auth.requests.post", side_effect=[expired, fresh]) as mock_post:
            first = auth.get_token()
            second = auth.get_token()
        assert first == "old"
        assert second == "new"
        assert mock_post.call_count == 2

    def test_auth_header_contains_bearer_token(self):
        auth = self._auth()
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            header = auth.get_auth_header()
        assert header == {"Authorization": "Bearer fake-token-123"}


# ---------------------------------------------------------------------------
# Client — CRUD against the Web API
# ---------------------------------------------------------------------------


class TestDataverseClient:
    def _client(self) -> DataverseClient:
        from src.dataverse.models import DataverseConfig

        return DataverseClient(
            DataverseConfig(
                tenant_id="t",
                client_id="c",
                client_secret="s",
                org_url="https://testorg.crm.dynamics.com",
            )
        )

    def test_create_incident_posts_to_entity_set(self):
        client = self._client()
        inc = SiteIncident(
            location="Site A",
            severity="high",
            description="Scaffold concern",
            reporter="r@aecon.com",
            timestamp=datetime(2026, 8, 13, 12, 0, 0),
            status="open",
        )
        created = make_api_response(status=204)
        created.headers = {
            "OData-EntityId": (
                "https://testorg.crm.dynamics.com/api/data/v9.2/" "abs_siteincidents(guid-1)"
            )
        }
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            client.authenticator.get_token()
        with patch("src.dataverse.client.requests.post", return_value=created) as mock_post:
            record_id = client.create_incident(inc)
        assert record_id == "guid-1"
        args, kwargs = mock_post.call_args
        assert args[0] == "https://testorg.crm.dynamics.com/api/data/v9.2/abs_siteincidents"
        assert kwargs["json"]["abs_location"] == "Site A"
        assert kwargs["headers"]["OData-MaxVersion"] == "4.0"

    def test_create_incident_raises_on_error(self):
        client = self._client()
        inc = SiteIncident(
            location="Site A",
            severity="high",
            description="x",
            reporter="r@aecon.com",
            timestamp=datetime.now(),
            status="open",
        )
        failed = make_api_response(status=400, payload={"error": {"message": "bad request"}})
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            client.authenticator.get_token()
        with patch("src.dataverse.client.requests.post", return_value=failed):
            with pytest.raises(Exception, match="Dataverse create failed"):
                client.create_incident(inc)

    def test_get_incidents_filters_by_status(self):
        client = self._client()
        payload = {
            "value": [
                {
                    "abs_incidentid": "guid-1",
                    "abs_location": "Site A",
                    "abs_severity": "high",
                    "abs_description": "d1",
                    "abs_reporter": "r@aecon.com",
                    "abs_timestamp": "2026-08-13T10:00:00",
                    "abs_status": "open",
                }
            ]
        }
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            with patch(
                "src.dataverse.client.requests.get", return_value=make_api_response(payload=payload)
            ) as mock_get:
                incidents = client.get_incidents(status="open")
        assert len(incidents) == 1
        assert incidents[0].severity == "high"
        args, kwargs = mock_get.call_args
        assert "$filter" in kwargs["params"]
        assert "abs_status eq 'open'" in kwargs["params"]["$filter"]

    def test_get_incidents_filters_by_severity_and_site(self):
        client = self._client()
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            with patch(
                "src.dataverse.client.requests.get",
                return_value=make_api_response(payload={"value": []}),
            ) as mock_get:
                client.get_incidents(severity="critical", location="Site B")
        _, kwargs = mock_get.call_args
        filt = kwargs["params"]["$filter"]
        assert "abs_severity eq 'critical'" in filt
        assert "abs_location eq 'Site B'" in filt

    def test_get_incident_by_id(self):
        client = self._client()
        payload = {
            "abs_incidentid": "guid-9",
            "abs_location": "Site Z",
            "abs_severity": "low",
            "abs_description": "d",
            "abs_reporter": "r@aecon.com",
            "abs_timestamp": "2026-08-13T10:00:00",
            "abs_status": "closed",
        }
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            with patch(
                "src.dataverse.client.requests.get", return_value=make_api_response(payload=payload)
            ):
                inc = client.get_incident("guid-9")
        assert inc.location == "Site Z"

    def test_update_incident_status_sends_patch(self):
        client = self._client()
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            with patch(
                "src.dataverse.client.requests.patch", return_value=make_api_response(status=204)
            ) as mock_patch_req:
                client.update_incident_status("guid-9", "escalated")
        args, kwargs = mock_patch_req.call_args
        assert args[0].endswith("/abs_siteincidents(guid-9)")
        assert kwargs["json"] == {"abs_status": "escalated"}


# ---------------------------------------------------------------------------
# Connector — Triage output → SiteIncident
# ---------------------------------------------------------------------------


class TestTriageToDataverseConnector:
    def _connector(self, client=None) -> TriageToDataverseConnector:
        from src.dataverse.models import DataverseConfig

        if client is None:
            client = DataverseClient(
                DataverseConfig(
                    tenant_id="t",
                    client_id="c",
                    client_secret="s",
                    org_url="https://testorg.crm.dynamics.com",
                )
            )
        return TriageToDataverseConnector(client)

    def test_persists_triage_output_as_site_incident(self):
        connector = self._connector()
        triage_output = json.dumps(
            {
                "category": "infrastructure",
                "severity": "high",
                "urgency": 3,
                "routing": "on_call_engineer",
                "assessment": "Scaffold instability reported",
            }
        )
        created = make_api_response(status=204)
        created.headers = {"OData-EntityId": "...(guid-77)"}
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            connector.client.authenticator.get_token()
        with patch("src.dataverse.client.requests.post", return_value=created) as mock_post:
            result = connector.persist_triage(
                triage_output=triage_output,
                location="Site A - Tower 2",
                reporter="jsmith@aecon.com",
                description="Unstable scaffolding on level 3",
            )
        assert result["dataverse_record_id"] == "guid-77"
        assert result["status"] == "persisted"
        sent = mock_post.call_args.kwargs["json"]
        assert sent["abs_severity"] == "high"
        assert sent["abs_location"] == "Site A - Tower 2"

    def test_invalid_triage_json_raises(self):
        connector = self._connector()
        with pytest.raises(ValueError, match="triage output"):
            connector.persist_triage(
                triage_output="not json at all {{{",
                location="Site A",
                reporter="x@y.com",
                description="d",
            )

    def test_severity_defaults_to_medium_when_missing(self):
        connector = self._connector()
        created = make_api_response(status=204)
        created.headers = {"OData-EntityId": "...(guid-5)"}
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            connector.client.authenticator.get_token()
        with patch("src.dataverse.client.requests.post", return_value=created) as mock_post:
            connector.persist_triage(
                triage_output=json.dumps({"category": "general"}),
                location="Site A",
                reporter="x@y.com",
                description="d",
            )
        assert mock_post.call_args.kwargs["json"]["abs_severity"] == "medium"

    def test_unknown_severity_falls_back_to_medium(self):
        connector = self._connector()
        created = make_api_response(status=204)
        created.headers = {"OData-EntityId": "...(guid-6)"}
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            connector.client.authenticator.get_token()
        with patch("src.dataverse.client.requests.post", return_value=created) as mock_post:
            connector.persist_triage(
                triage_output=json.dumps({"severity": "ultra"}),
                location="Site A",
                reporter="x@y.com",
                description="d",
            )
        assert mock_post.call_args.kwargs["json"]["abs_severity"] == "medium"

    def test_round_trip_create_then_read(self):
        """The create-then-read round trip, mocked at the HTTP boundary."""
        connector = self._connector()
        created = make_api_response(status=204)
        created.headers = {"OData-EntityId": "...(guid-42)"}
        read_payload = {
            "value": [
                {
                    "abs_incidentid": "guid-42",
                    "abs_location": "Site A - Tower 2",
                    "abs_severity": "high",
                    "abs_description": "Unstable scaffolding on level 3",
                    "abs_reporter": "jsmith@aecon.com",
                    "abs_timestamp": "2026-08-13T10:00:00",
                    "abs_status": "open",
                }
            ]
        }
        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            connector.client.authenticator.get_token()
        with patch("src.dataverse.client.requests.post", return_value=created):
            with patch(
                "src.dataverse.client.requests.get",
                return_value=make_api_response(payload=read_payload),
            ):
                result = connector.persist_triage(
                    triage_output=json.dumps({"severity": "high", "category": "infrastructure"}),
                    location="Site A - Tower 2",
                    reporter="jsmith@aecon.com",
                    description="Unstable scaffolding on level 3",
                )
                incidents = connector.client.get_incidents(status="open")
        assert result["dataverse_record_id"] == "guid-42"
        assert incidents[0].severity == "high"
        assert incidents[0].status == "open"
