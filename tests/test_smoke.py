"""
Smoke tests for critical functionality.
Quick tests to verify core systems are working.
"""

import pytest


@pytest.mark.smoke
@pytest.mark.unit
class TestSmokeTests:
    """Critical smoke tests."""
    
    def test_python_version(self):
        """Test Python version is 3.11 or higher."""
        import sys
        assert sys.version_info >= (3, 11), "Python 3.11+ required"
    
    def test_core_imports(self):
        """Test core modules can be imported."""
        try:
            from rag import ChromaDBStore, DocumentLoader, RAGRetriever
            from llm import AzureOpenAIClient, ChainBuilder
            from orchestration import WorkflowState, AgentCoordinator
            from utils.exceptions import EnterpriseAIException, ErrorCode
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")
    
    def test_exception_hierarchy(self):
        """Test exception hierarchy is correct."""
        from utils.exceptions import (
            EnterpriseAIException,
            RAGException,
            LLMException,
            OrchestrationException
        )
        
        # Test inheritance
        assert issubclass(RAGException, EnterpriseAIException)
        assert issubclass(LLMException, EnterpriseAIException)
        assert issubclass(OrchestrationException, EnterpriseAIException)
        
        # Test instantiation
        exc = RAGException("Test", ErrorCode.RETRIEVAL_ERROR, recoverable=True)
        assert exc.recoverable is True
    
    def test_retry_config(self):
        """Test retry configuration."""
        from utils.retry import RetryConfig
        
        config = RetryConfig(max_attempts=5, base_delay=1.0)
        assert config.max_attempts == 5
        assert config.base_delay == 1.0
        
        # Test delay calculation
        delay = config.calculate_delay(0)
        assert delay == 1.0
    
    def test_workflow_state(self):
        """Test workflow state initialization."""
        from orchestration.state import WorkflowState, IncidentSeverity
        
        state = WorkflowState(
            incident_id="SMOKE-001",
            incident_title="Smoke Test Incident",
            incident_description="Testing workflow state"
        )
        
        assert state.incident_id == "SMOKE-001"
        assert state.workflow_status == "in_progress"
        assert state.current_agent == "triage"
        assert len(state.errors) == 0
    
    def test_document_loader_initialization(self):
        """Test document loader can be initialized."""
        from rag import DocumentLoader
        
        loader = DocumentLoader("data/sample_documents")
        assert loader is not None
    
    def test_chunker_initialization(self):
        """Test chunker can be initialized."""
        from rag import TextChunker
        
        chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 100
    
    def test_logger_configuration(self):
        """Test logging can be configured."""
        import logging
        from utils.logging import get_logger
        
        logger = get_logger("smoke_test")
        assert logger is not None
        assert isinstance(logger, logging.Logger)


@pytest.mark.smoke
@pytest.mark.api
class TestAPISmokeTests:
    """Smoke tests for API endpoints."""
    
    def test_fastapi_import(self):
        """Test FastAPI can be imported."""
        try:
            from fastapi import FastAPI
            assert True
        except ImportError:
            pytest.fail("FastAPI not installed")
    
    def test_api_file_exists(self):
        """Test API main file exists."""
        from pathlib import Path
        
        api_file = Path("src/api/main.py")
        assert api_file.exists(), "API main file not found"


@pytest.mark.smoke
@pytest.mark.docker
class TestDockerSmokeTests:
    """Smoke tests for Docker configuration."""
    
    def test_dockerfile_exists(self):
        """Test Dockerfile exists."""
        from pathlib import Path
        
        dockerfile = Path("Dockerfile")
        assert dockerfile.exists(), "Dockerfile not found"
    
    def test_docker_compose_exists(self):
        """Test docker-compose files exist."""
        from pathlib import Path
        
        compose_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml"
        ]
        
        for compose_file in compose_files:
            path = Path(compose_file)
            assert path.exists(), f"{compose_file} not found"
    
    def test_makefile_exists(self):
        """Test Makefile exists."""
        from pathlib import Path
        
        makefile = Path("Makefile")
        assert makefile.exists(), "Makefile not found"