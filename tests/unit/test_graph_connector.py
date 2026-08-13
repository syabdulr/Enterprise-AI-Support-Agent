"""Tests for Microsoft Graph connector integration."""

from unittest.mock import MagicMock, patch

import pytest

from src.graph.auth import GraphAuthenticator
from src.graph.client import GraphClient
from src.graph.connector import GraphConnector
from src.graph.models import (
    GraphConfig,
    GraphResource,
    GraphResourceType,
    GraphSearchResult,
    PermissionInfo,
)
from src.graph.permission_resolver import PermissionResolver


class TestGraphModels:
    """Tests for Graph connector data models."""

    def test_graph_config(self):
        config = GraphConfig(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
            base_url="https://graph.microsoft.com/v1.0",
        )
        assert config.tenant_id == "tenant-123"
        assert config.client_id == "client-456"
        assert "graph.microsoft.com" in config.base_url

    def test_graph_config_defaults(self):
        config = GraphConfig(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
        assert config.base_url == "https://graph.microsoft.com/v1.0"
        assert config.api_version == "v1.0"

    def test_resource_type_enum(self):
        assert GraphResourceType.SHAREPOINT_LIST.value == "sharepoint_list"
        assert GraphResourceType.SHAREPOINT_FILE.value == "sharepoint_file"
        assert GraphResourceType.USER_PROFILE.value == "user_profile"
        assert GraphResourceType.GROUP.value == "group"
        assert GraphResourceType.TEAMS_MESSAGE.value == "teams_message"

    def test_graph_resource(self):
        resource = GraphResource(
            resource_id="item-001",
            resource_type=GraphResourceType.SHAREPOINT_FILE,
            title="Incident Response Playbook.docx",
            content="Step 1: Verify the issue. Step 2: Contact on-call.",
            web_url="https://contoso.sharepoint.com/docs/playbook.docx",
            source="Engineering SharePoint",
        )
        assert resource.resource_id == "item-001"
        assert resource.resource_type == GraphResourceType.SHAREPOINT_FILE
        assert "playbook" in resource.title.lower()

    def test_graph_resource_with_metadata(self):
        resource = GraphResource(
            resource_id="item-002",
            resource_type=GraphResourceType.SHAREPOINT_LIST,
            title="Incident Log",
            content="INC-001: Database timeout resolved",
            web_url="https://contoso.sharepoint.com/lists/incidents",
            source="IT Operations",
            metadata={"created_by": "admin@contoso.com", "created_at": "2025-01-01"},
        )
        assert resource.metadata["created_by"] == "admin@contoso.com"

    def test_permission_info(self):
        perm = PermissionInfo(
            user_id="user@contoso.com",
            groups=["Engineering", "OnCall"],
            site_permissions={"Engineering": "read", "IT": "write"},
        )
        assert perm.user_id == "user@contoso.com"
        assert "Engineering" in perm.groups
        assert perm.site_permissions["Engineering"] == "read"

    def test_permission_info_has_access(self):
        perm = PermissionInfo(
            user_id="user@contoso.com",
            groups=["Engineering"],
            site_permissions={"Engineering": "read"},
        )
        assert perm.has_access("Engineering", "read") is True
        assert perm.has_access("Engineering", "write") is False
        assert perm.has_access("HR", "read") is False

    def test_graph_search_result(self):
        result = GraphSearchResult(
            query="database timeout",
            resources=[
                GraphResource(
                    resource_id="1",
                    resource_type=GraphResourceType.SHAREPOINT_FILE,
                    title="DB Playbook",
                    content="How to handle DB timeouts",
                    web_url="https://sharepoint.com/1",
                    source="IT",
                ),
            ],
            total_count=1,
        )
        assert result.query == "database timeout"
        assert result.total_count == 1
        assert len(result.resources) == 1


class TestGraphAuthenticator:
    """Tests for Graph API authentication."""

    def test_authenticator_creation(self):
        config = GraphConfig(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
        )
        auth = GraphAuthenticator(config)
        assert auth.config.tenant_id == "tenant-123"

    @patch("src.graph.auth.requests.post")
    def test_get_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock-token-12345",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        config = GraphConfig(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
        )
        auth = GraphAuthenticator(config)
        token = auth.get_token()

        assert token == "mock-token-12345"
        mock_post.assert_called_once()

    @patch("src.graph.auth.requests.post")
    def test_get_token_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_client"}
        mock_post.return_value = mock_response

        config = GraphConfig(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="bad-secret",
        )
        auth = GraphAuthenticator(config)
        with pytest.raises(Exception) as exc_info:
            auth.get_token()
        assert "401" in str(exc_info.value) or "auth" in str(exc_info.value).lower()

    def test_token_caching(self):
        """Test that token is cached and reused."""
        config = GraphConfig(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
        auth = GraphAuthenticator(config)
        auth._cached_token = "cached-token"
        auth._token_expiry = 9999999999  # Far future
        token = auth.get_token()
        assert token == "cached-token"


class TestGraphClient:
    """Tests for Graph API client."""

    def _make_client(self):
        config = GraphConfig(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
        return GraphClient(config)

    @patch("src.graph.client.requests.get")
    @patch("src.graph.auth.requests.post")
    def test_get_sharepoint_lists(self, mock_auth_post, mock_get):
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_auth_post.return_value = mock_auth_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "value": [
                {"id": "list-1", "name": "Incident Log", "displayName": "Incident Log"},
                {"id": "list-2", "name": "Change Requests", "displayName": "Change Requests"},
            ]
        }
        mock_get.return_value = mock_get_response

        client = self._make_client()
        lists = client.get_sharepoint_lists(site_id="contoso.sharepoint.com")

        assert len(lists) == 2
        assert lists[0]["displayName"] == "Incident Log"

    @patch("src.graph.client.requests.get")
    @patch("src.graph.auth.requests.post")
    def test_get_sharepoint_list_items(self, mock_auth_post, mock_get):
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_auth_post.return_value = mock_auth_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "value": [
                {"id": "1", "fields": {"Title": "DB Timeout", "Status": "Resolved"}},
                {"id": "2", "fields": {"Title": "CPU Spike", "Status": "Open"}},
            ]
        }
        mock_get.return_value = mock_get_response

        client = self._make_client()
        items = client.get_sharepoint_list_items(
            site_id="contoso.sharepoint.com",
            list_id="list-1",
        )

        assert len(items) == 2
        assert items[0]["fields"]["Title"] == "DB Timeout"

    @patch("src.graph.client.requests.get")
    @patch("src.graph.auth.requests.post")
    def test_get_user_profile(self, mock_auth_post, mock_get):
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_auth_post.return_value = mock_auth_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "id": "user-123",
            "displayName": "John Doe",
            "mail": "john@contoso.com",
            "department": "Engineering",
        }
        mock_get.return_value = mock_get_response

        client = self._make_client()
        profile = client.get_user_profile("john@contoso.com")

        assert profile["displayName"] == "John Doe"
        assert profile["department"] == "Engineering"

    @patch("requests.post")
    @patch("requests.get")
    def test_search_sharepoint(self, mock_get, mock_post):
        # First call to post = auth token, second = search
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"access_token": "token", "expires_in": 3600}

        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "value": [
                {
                    "hitsContainers": [
                        {
                            "hits": [
                                {
                                    "hitId": "doc-1",
                                    "resource": {
                                        "name": "Incident Playbook.pdf",
                                        "webUrl": "https://contoso.sharepoint.com/docs/playbook.pdf",
                                        "fields": {"Title": "Incident Response Playbook"},
                                    },
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_post.side_effect = [mock_auth_response, mock_search_response]

        client = self._make_client()
        results = client.search_sharepoint(
            site_id="contoso.sharepoint.com",
            query="incident response",
        )

        assert len(results) == 1
        assert "Incident" in results[0]["resource"]["name"]


class TestPermissionResolver:
    """Tests for permission-aware data access."""

    def test_resolver_creation(self):
        resolver = PermissionResolver()
        assert resolver is not None

    def test_get_user_permissions(self):
        resolver = PermissionResolver()
        resolver.set_user_permissions(
            "user@contoso.com",
            PermissionInfo(
                user_id="user@contoso.com",
                groups=["Engineering", "OnCall"],
                site_permissions={"Engineering": "read", "IT": "write"},
            ),
        )
        perm = resolver.get_user_permissions("user@contoso.com")
        assert perm is not None
        assert "Engineering" in perm.groups

    def test_filter_resources_by_permission(self):
        resolver = PermissionResolver()
        resolver.set_user_permissions(
            "user@contoso.com",
            PermissionInfo(
                user_id="user@contoso.com",
                groups=["Engineering"],
                site_permissions={"Engineering": "read", "HR": "read"},
            ),
        )

        resources = [
            GraphResource(
                resource_id="1",
                resource_type=GraphResourceType.SHAREPOINT_FILE,
                title="Eng Doc",
                content="Engineering documentation",
                web_url="https://sharepoint.com/1",
                source="Engineering",
            ),
            GraphResource(
                resource_id="2",
                resource_type=GraphResourceType.SHAREPOINT_FILE,
                title="HR Doc",
                content="HR documentation",
                web_url="https://sharepoint.com/2",
                source="HR",
            ),
            GraphResource(
                resource_id="3",
                resource_type=GraphResourceType.SHAREPOINT_FILE,
                title="Finance Doc",
                content="Finance documentation",
                web_url="https://sharepoint.com/3",
                source="Finance",
            ),
        ]

        filtered = resolver.filter_resources(
            resources,
            user_id="user@contoso.com",
            required_access="read",
        )

        # Should see Engineering and HR docs, but NOT Finance
        sources = [r.source for r in filtered]
        assert "Engineering" in sources
        assert "HR" in sources
        assert "Finance" not in sources

    def test_filter_no_permissions(self):
        """User with no permissions sees nothing."""
        resolver = PermissionResolver()

        resources = [
            GraphResource(
                resource_id="1",
                resource_type=GraphResourceType.SHAREPOINT_FILE,
                title="Doc",
                content="content",
                web_url="https://sharepoint.com/1",
                source="Engineering",
            ),
        ]

        filtered = resolver.filter_resources(
            resources,
            user_id="unknown@contoso.com",
            required_access="read",
        )
        assert len(filtered) == 0


class TestGraphConnector:
    """Tests for the Graph connector that bridges into the RAG pipeline."""

    def _make_connector(self):
        config = GraphConfig(
            tenant_id="t",
            client_id="c",
            client_secret="s",
        )
        return GraphConnector(config)

    def test_connector_creation(self):
        connector = self._make_connector()
        assert connector is not None

    def test_ingest_to_rag_format(self):
        """Test converting Graph resources to RAG-ingestible format."""
        connector = self._make_connector()

        resource = GraphResource(
            resource_id="doc-001",
            resource_type=GraphResourceType.SHAREPOINT_FILE,
            title="Incident Playbook",
            content="Step 1: Verify. Step 2: Escalate.",
            web_url="https://contoso.sharepoint.com/docs/playbook",
            source="Engineering SharePoint",
            metadata={"created_by": "admin", "modified": "2025-01-01"},
        )

        rag_doc = connector.to_rag_document(resource)
        assert rag_doc["id"] == "graph_doc-001"
        assert "content" in rag_doc
        assert "metadata" in rag_doc
        assert rag_doc["metadata"]["source"] == "microsoft_graph"
        assert rag_doc["metadata"]["original_source"] == "Engineering SharePoint"

    def test_ingest_multiple_to_rag(self):
        connector = self._make_connector()

        resources = [
            GraphResource(
                resource_id=f"doc-{i}",
                resource_type=GraphResourceType.SHAREPOINT_LIST,
                title=f"Item {i}",
                content=f"Content {i}",
                web_url=f"https://sharepoint.com/{i}",
                source="IT",
            )
            for i in range(5)
        ]

        rag_docs = connector.to_rag_documents(resources)
        assert len(rag_docs) == 5
        assert all(d["metadata"]["source"] == "microsoft_graph" for d in rag_docs)

    @patch("src.graph.client.requests.get")
    @patch("src.graph.auth.requests.post")
    def test_sync_sharepoint_to_rag(self, mock_auth_post, mock_get):
        """Test full sync: fetch from Graph → convert to RAG format."""
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_auth_post.return_value = mock_auth_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "value": [
                {"id": "1", "fields": {"Title": "DB Runbook", "Content": "Restart the DB service"}},
                {"id": "2", "fields": {"Title": "Network Guide", "Content": "Check DNS settings"}},
            ]
        }
        mock_get.return_value = mock_get_response

        connector = self._make_connector()
        docs = connector.sync_sharepoint_list(
            site_id="contoso.sharepoint.com",
            list_id="runbooks",
        )

        assert len(docs) == 2
        assert docs[0]["metadata"]["source"] == "microsoft_graph"

    def test_permission_aware_sync(self):
        """Test that sync respects user permissions."""
        connector = self._make_connector()
        connector.permission_resolver.set_user_permissions(
            "user@contoso.com",
            PermissionInfo(
                user_id="user@contoso.com",
                groups=["IT"],
                site_permissions={"IT": "read"},
            ),
        )

        resources = [
            GraphResource(
                resource_id="1",
                resource_type=GraphResourceType.SHAREPOINT_FILE,
                title="IT Doc",
                content="IT content",
                web_url="https://sharepoint.com/1",
                source="IT",
            ),
            GraphResource(
                resource_id="2",
                resource_type=GraphResourceType.SHAREPOINT_FILE,
                title="HR Doc",
                content="HR content",
                web_url="https://sharepoint.com/2",
                source="HR",
            ),
        ]

        docs = connector.to_rag_documents(
            resources,
            user_id="user@contoso.com",
        )
        assert len(docs) == 1
        assert docs[0]["metadata"]["original_source"] == "IT"
