"""
Shared pytest fixtures and configuration.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Create and cleanup test data directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="enterprise_ai_test_"))
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    This is a sample document for testing the RAG system.
    It contains information about network issues, database problems,
    and common troubleshooting steps.
    
    Network timeouts can occur due to firewall rules or connectivity issues.
    Database connection strings must be correctly configured.
    Always check logs for error messages and stack traces.
    """


@pytest.fixture
def sample_incident():
    """Sample incident data."""
    return {
        "incident_id": "TEST-001",
        "description": "Network timeout when connecting to database",
        "severity": "High",
        "category": "Network",
        "priority": "P1"
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    import os
    original_env = os.environ.copy()
    
    os.environ["AZURE_OPENAI_API_KEY"] = "test_key"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com"
    os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"] = "gpt-4"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB for unit tests."""
    from unittest.mock import Mock
    
    mock_store = Mock()
    mock_store.add_documents.return_value = None
    mock_store.query.return_value = {
        "documents": [["Sample document content"]],
        "metadatas": [[{"filename": "test.md"}]],
        "distances": [[0.1]]
    }
    mock_store.get_collection_info.return_value = {
        "name": "test_collection",
        "count": 10
    }
    
    return mock_store


@pytest.fixture
def mock_azure_openai():
    """Mock Azure OpenAI client for unit tests."""
    from unittest.mock import Mock
    
    mock_client = Mock()
    mock_client.chat.return_value = "Test response"
    mock_client.generate_embedding.return_value = [0.1] * 1536
    mock_client.get_token_count.return_value = 100
    
    return mock_client


# Pytest hooks

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require external services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full system tests)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests (skip by default)"
    )
    config.addinivalue_line(
        "markers", "rag: RAG-related tests"
    )
    config.addinivalue_line(
        "markers", "llm: LLM-related tests"
    )
    config.addinivalue_line(
        "markers", "orchestration: Orchestration-related tests"
    )
    config.addinivalue_line(
        "markers", "api: API-related tests"
    )
    config.addinivalue_line(
        "markers", "docker: Docker-related tests"
    )
    config.addinivalue_line(
        "markers", "smoke: Smoke tests (critical functionality)"
    )
    config.addinivalue_line(
        "markers", "regression: Regression tests"
    )