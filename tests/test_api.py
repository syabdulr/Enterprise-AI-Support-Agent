"""
Unit tests for FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Mock imports since we can't import the actual modules without dependencies
@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = Mock()
    return client

@pytest.fixture
def mock_rag_retriever():
    """Mock RAG retriever."""
    retriever = Mock()
    retriever.retrieve.return_value = [
        {
            "content": "Sample document content",
            "metadata": {"filename": "test.md"},
            "distance": 0.1
        }
    ]
    return retriever

@pytest.fixture
def mock_workflow():
    """Mock incident workflow."""
    workflow = Mock()
    result = Mock()
    result.workflow_status = "completed"
    result.to_dict.return_value = {
        "incident_id": "INC-001",
        "status": "completed",
        "resolution": "Test resolution"
    }
    workflow.run.return_value = result
    return workflow

@pytest.fixture
def app(mock_llm_client, mock_rag_retriever, mock_workflow):
    """Create FastAPI test app."""
    # Patch the components
    with patch('src.api.main.llm_client', mock_llm_client), \
         patch('src.api.main.rag_retriever', mock_rag_retriever), \
         patch('src.api.main.workflow', mock_workflow):
        
        from src.api.main import app
        return app

@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)

class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self, client):
        """Test root endpoint returns correct response."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns correct response."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert data["status"] == "healthy"

class TestIncidentEndpoint:
    """Test incident handling endpoint."""
    
    def test_handle_incident_success(self, client, mock_workflow):
        """Test successful incident handling."""
        incident_data = {
            "incident_id": "INC-001",
            "description": "Test incident"
        }
        
        response = client.post("/incident", json=incident_data)
        assert response.status_code == 200
        data = response.json()
        assert "incident_id" in data
        assert "status" in data
        assert "result" in data
        assert mock_workflow.run.called
    
    def test_handle_incident_missing_description(self, client):
        """Test incident handling fails without description."""
        incident_data = {
            "incident_id": "INC-001"
        }
        
        response = client.post("/incident", json=incident_data)
        assert response.status_code == 400
    
    def test_handle_incident_empty_description(self, client):
        """Test incident handling fails with empty description."""
        incident_data = {
            "incident_id": "INC-001",
            "description": ""
        }
        
        response = client.post("/incident", json=incident_data)
        assert response.status_code == 400

class TestComponentsEndpoint:
    """Test components status endpoint."""
    
    def test_components(self, client):
        """Test components endpoint returns correct response."""
        response = client.get("/components")
        assert response.status_code == 200
        data = response.json()
        assert "llm" in data
        assert "rag" in data
        assert "workflow" in data
        assert "status" in data["llm"]
        assert "status" in data["rag"]
        assert "status" in data["workflow"]

class TestErrorHandling:
    """Test error handling in API."""
    
    def test_workflow_error(self, client, mock_workflow):
        """Test API handles workflow errors gracefully."""
        mock_workflow.run.side_effect = Exception("Test error")
        
        incident_data = {
            "incident_id": "INC-001",
            "description": "Test incident"
        }
        
        response = client.post("/incident", json=incident_data)
        assert response.status_code == 500