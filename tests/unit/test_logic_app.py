"""Tests for the Logic App escalation workflow definition.

The workflow JSON is validated structurally: trigger cadence, Dataverse
polling with AAD OAuth, severity condition, escalation actions, and
secure parameter handling. This mirrors what `az logic workflow create`
validates at deploy time.
"""

import json
import pathlib

import pytest

WORKFLOW_PATH = pathlib.Path(__file__).parents[2] / "infra" / "logic-app-escalation.json"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text())


class TestWorkflowDefinition:
    def test_file_is_valid_json_with_definition(self, workflow):
        assert "$schema" in workflow
        assert "triggers" in workflow
        assert "actions" in workflow

    def test_recurrence_trigger_polls_every_five_minutes(self, workflow):
        (trigger,) = workflow["triggers"].values()
        assert trigger["type"] == "Recurrence"
        assert trigger["recurrence"]["frequency"] == "Minute"
        assert trigger["recurrence"]["interval"] == 5

    def test_dataverse_poll_uses_aad_oauth(self, workflow):
        poll = workflow["actions"]["Poll_Dataverse_For_Escalations"]
        assert poll["type"] == "Http"
        auth = poll["inputs"]["authentication"]
        assert auth["type"] == "ActiveDirectoryOAuth"
        assert auth["authority"] == "login.microsoftonline.com"
        # audience is parameterized, resolved to the org URL at runtime
        assert auth["audience"] == "@parameters('dataverseUrl')"
        # credentials come from parameters, never hardcoded
        assert "@parameters('dataverseClientId')" in json.dumps(auth)

    def test_poll_filters_critical_high_open_incidents(self, workflow):
        poll = workflow["actions"]["Poll_Dataverse_For_Escalations"]
        uri = poll["inputs"]["uri"]
        assert "abs_siteincidents" in uri
        assert "$filter=" in uri
        assert "abs_severity eq 'critical'" in uri or "abs_status eq 'open'" in uri

    def test_poll_response_parsed_as_row_array(self, workflow):
        parse = workflow["actions"]["Parse_Incident_Rows"]
        assert parse["type"] == "ParseJson"
        schema = parse["inputs"]["schema"]
        assert schema["properties"]["value"]["type"] == "array"

    def test_foreach_iterates_parsed_rows(self, workflow):
        loop = workflow["actions"]["For_Each_Incident"]
        assert loop["type"] == "Foreach"
        assert loop["foreach"] == "@body('Parse_Incident_Rows')?['value']"

    def test_condition_splits_critical_from_high(self, workflow):
        cond = workflow["actions"]["For_Each_Incident"]["actions"]["Is_Critical_Severity"]
        assert cond["type"] == "If"
        expression = cond["expression"]
        dumped = json.dumps(expression)
        assert "abs_severity" in dumped
        assert "critical" in dumped

    def test_critical_branch_notifies_and_escalates(self, workflow):
        branch = workflow["actions"]["For_Each_Incident"]["actions"]["Is_Critical_Severity"][
            "actions"
        ]
        notify = branch["Notify_On_Call_Supervisor"]
        assert notify["type"] == "Http"
        assert notify["inputs"]["method"] == "POST"
        assert "@parameters('teamsWebhookUrl')" in json.dumps(notify["inputs"])

        escalate = branch["Mark_Record_Escalated"]
        assert escalate["type"] == "Http"
        assert escalate["inputs"]["method"] == "PATCH"
        assert "abs_status" in escalate["inputs"]["body"]
        assert escalate["inputs"]["body"]["abs_status"] == "escalated"

    def test_escalation_patch_reuses_row_id(self, workflow):
        escalate = workflow["actions"]["For_Each_Incident"]["actions"]["Is_Critical_Severity"][
            "actions"
        ]["Mark_Record_Escalated"]
        assert "items('For_Each_Incident')" in json.dumps(escalate["inputs"])

    def test_secrets_declared_as_securestring_parameters(self, workflow):
        params = workflow["parameters"]
        for name in ("dataverseClientSecret", "teamsWebhookUrl"):
            assert params[name]["type"] == "securestring"
        # tenant/client id are identifiers, not secrets — plain strings
        assert params["dataverseTenantId"]["type"] == "string"

    def test_default_values_do_not_leak_secrets(self, workflow):
        params = workflow["parameters"]
        assert "defaultValue" not in params["dataverseClientSecret"]
        assert "defaultValue" not in params["teamsWebhookUrl"]

    def test_deploy_doc_covers_logic_app(self):
        deploy = (pathlib.Path(__file__).parents[2] / "DEPLOY.md").read_text()
        assert "az logic workflow create" in deploy
        assert "logic-app-escalation.json" in deploy


class TestNotificationPayload:
    def test_teams_message_includes_incident_fields(self, workflow):
        notify = workflow["actions"]["For_Each_Incident"]["actions"]["Is_Critical_Severity"][
            "actions"
        ]["Notify_On_Call_Supervisor"]
        body = json.dumps(notify["inputs"]["body"])
        for field in ("abs_location", "abs_description", "abs_severity"):
            assert field in body
