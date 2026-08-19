"""Tests for the incident_write Azure Function.

The function logic is tested directly with real azure.functions
HttpRequest/HttpResponse objects. The Dataverse HTTP layer is mocked at
the network boundary (requests.post/requests.get), the same pattern as
tests/unit/test_dataverse.py. The azure.functions SDK itself is never
mocked.
"""

import json
from unittest.mock import MagicMock, patch

import azure.functions as func
import pytest

pytest.importorskip(
    "semantic_kernel",
    exc_type=ImportError,
    reason=(
        "functions.incident_write imports src.sk.plugins.incident_plugins, "
        "which needs semantic_kernel -- see tests/unit/test_semantic_kernel.py "
        "for why that fails to import on this interpreter (Python 3.14 / "
        "pydantic incompatibility). Run under Python <=3.13 to exercise "
        "these tests."
    ),
)

from functions.incident_write import main as incident_write_main
from src.dataverse.models import DataverseConfig


def make_auth_response(token: str = "fake-token-123", expires_in: int = 3600) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": token, "expires_in": expires_in}
    return resp


def make_api_response(status: int = 204, payload: dict = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload or {}
    return resp


def make_request(body: dict, method: str = "POST") -> func.HttpRequest:
    return func.HttpRequest(
        method=method,
        url="/api/incident_write",
        body=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def make_created_response(record_id: str) -> MagicMock:
    created = make_api_response(status=204)
    created.headers = {
        "OData-EntityId": (
            f"https://testorg.crm.dynamics.com/api/data/v9.2/" f"abs_siteincidents({record_id})"
        )
    }
    return created


VALID_BODY = {
    "location": "Site A - North Tower",
    "description": "Database connection timeout on the site reporting server",
    "reporter": "jsmith@aecon.com",
    "severity": "high",
}


class TestIncidentWriteFunction:
    def test_valid_incident_writes_to_dataverse_and_returns_201(self):
        req = make_request(VALID_BODY)
        created = make_created_response("guid-100")

        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            from src.dataverse.client import DataverseClient
            from src.dataverse.connector import TriageToDataverseConnector

            client = DataverseClient(
                DataverseConfig(
                    tenant_id="t",
                    client_id="c",
                    client_secret="s",
                    org_url="https://testorg.crm.dynamics.com",
                )
            )
            client.authenticator.get_token()
            connector = TriageToDataverseConnector(client)

        with patch("src.dataverse.client.requests.post", return_value=created) as mock_post:
            resp = incident_write_main(req, connector=connector)

        assert resp.status_code == 201
        body = json.loads(resp.get_body())
        assert body["dataverse_record_id"] == "guid-100"
        sent = mock_post.call_args.kwargs["json"]
        assert sent["abs_severity"] == "high"
        assert sent["abs_location"] == "Site A - North Tower"

    def test_classification_runs_before_write(self):
        """The function must classify via IncidentPlugin.triage before persisting."""
        req = make_request(VALID_BODY)
        created = make_created_response("guid-101")

        with patch("src.dataverse.auth.requests.post", return_value=make_auth_response()):
            from src.dataverse.client import DataverseClient
            from src.dataverse.connector import TriageToDataverseConnector

            client = DataverseClient(
                DataverseConfig(
                    tenant_id="t",
                    client_id="c",
                    client_secret="s",
                    org_url="https://testorg.crm.dynamics.com",
                )
            )
            client.authenticator.get_token()
            connector = TriageToDataverseConnector(client)

        with patch("src.dataverse.client.requests.post", return_value=created):
            resp = incident_write_main(req, connector=connector)

        assert resp.status_code == 201
        body = json.loads(resp.get_body())
        # classification must have run: category derived from description keywords
        assert body["category"] == "database"
        assert body["severity"] == "high"

    def test_missing_required_field_returns_400(self):
        body = {"location": "Site A"}  # no description/reporter
        req = make_request(body)
        resp = incident_write_main(req)
        assert resp.status_code == 400
        payload = json.loads(resp.get_body())
        assert "description" in str(payload["error"]) or "reporter" in str(payload["error"])

    def test_malformed_json_returns_400(self):
        req = func.HttpRequest(
            method="POST",
            url="/api/incident_write",
            body=b"{not valid json",
            headers={"Content-Type": "application/json"},
        )
        resp = incident_write_main(req)
        assert resp.status_code == 400
        assert "error" in json.loads(resp.get_body())

    # Test the default connector construction path (env-var driven).
    # The HTTP layer is still mocked at the network boundary.
    def test_default_connector_from_env(self):
        import os
        from unittest.mock import patch as mock_patch

        env = {
            "DATAVERSE_URL": "https://envorg.crm.dynamics.com",
            "DATAVERSE_TENANT_ID": "env-tenant",
            "DATAVERSE_CLIENT_ID": "env-client",
            "DATAVERSE_CLIENT_SECRET": "env-secret",
        }

        def fake_post(url, data=None, json=None, headers=None, **kwargs):
            if "login.microsoftonline.com" in url:
                return make_auth_response()
            return make_created_response("guid-102")

        with mock_patch.dict(os.environ, env):
            with patch("src.dataverse.client.requests.post", side_effect=fake_post):
                req = make_request(VALID_BODY)
                resp = incident_write_main(req)
        assert resp.status_code == 201
        body = json.loads(resp.get_body())
        assert body["dataverse_record_id"] == "guid-102"

    def test_invalid_severity_returns_400(self):
        body = dict(VALID_BODY, severity="catastrophic")
        req = make_request(body)
        resp = incident_write_main(req)
        assert resp.status_code == 400
        assert "severity" in json.loads(resp.get_body())["error"]


# ---------------------------------------------------------------------------
# Bicep infra validation
# ---------------------------------------------------------------------------


class TestBicepFiles:
    def test_function_app_bicep_exists_and_declares_function_app(self):
        import pathlib

        p = pathlib.Path(__file__).parents[2] / "infra" / "function-app.bicep"
        content = p.read_text()
        assert "Microsoft.Web/sites" in content
        assert "functionapp" in content
        assert "consumption" in content.lower() or "serverFarm" in content

    def test_apim_bicep_exists_and_declares_apim_with_policy(self):
        import pathlib

        p = pathlib.Path(__file__).parent.parent.parent / "infra" / "apim.bicep"
        content = p.read_text()
        assert "Microsoft.ApiManagement/service" in content
        assert "rate-limit" in content or "rate-limit-by-key" in content
        assert "subscriptionRequired" in content

    def test_deploy_doc_exists(self):
        import pathlib

        p = pathlib.Path(__file__).parents[2] / "DEPLOY.md"
        content = p.read_text()
        assert "az deployment group create" in content
        assert "func azure functionapp publish" in content
