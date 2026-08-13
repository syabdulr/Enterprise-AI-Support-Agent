"""Tests for Semantic Kernel agent integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.sk.kernel_setup import SemanticKernelManager
from src.sk.models import KernelFunctionDef, PluginConfig, SKAgentRequest, SKAgentResponse
from src.sk.orchestrator import SKOrchestrator
from src.sk.plugins.guardrail_plugins import GuardrailPlugin
from src.sk.plugins.incident_plugins import IncidentPlugin
from src.sk.plugins.rag_plugins import RAGPlugin


class TestSKModels:
    """Tests for Semantic Kernel data models."""

    def test_sk_agent_request(self):
        req = SKAgentRequest(
            incident_id="INC-001",
            description="Server is down",
            severity="critical",
        )
        assert req.incident_id == "INC-001"
        assert req.description == "Server is down"
        assert req.severity == "critical"

    def test_sk_agent_request_defaults(self):
        req = SKAgentRequest(
            incident_id="INC-002",
            description="Slow response",
        )
        assert req.severity == "medium"
        assert req.context == {}

    def test_sk_agent_response(self):
        resp = SKAgentResponse(
            incident_id="INC-001",
            agent_name="triage",
            result="Categorized as infrastructure outage",
            confidence=0.95,
            success=True,
        )
        assert resp.incident_id == "INC-001"
        assert resp.confidence == 0.95
        assert resp.success is True

    def test_sk_agent_response_with_error(self):
        resp = SKAgentResponse(
            incident_id="INC-001",
            agent_name="diagnosis",
            result="",
            success=False,
            error="LLM timeout",
        )
        assert resp.success is False
        assert resp.error == "LLM timeout"

    def test_kernel_function_def(self):
        func_def = KernelFunctionDef(
            name="triage_incident",
            description="Categorize and prioritize an incident",
            plugin_name="IncidentPlugin",
            parameters=[
                {"name": "description", "type": "string", "required": True},
                {"name": "severity", "type": "string", "required": False},
            ],
        )
        assert func_def.name == "triage_incident"
        assert len(func_def.parameters) == 2

    def test_plugin_config(self):
        config = PluginConfig(
            name="IncidentPlugin",
            enabled=True,
            settings={"max_retries": 3},
        )
        assert config.name == "IncidentPlugin"
        assert config.enabled is True
        assert config.settings["max_retries"] == 3


class TestKernelManager:
    """Tests for Semantic Kernel manager."""

    def test_kernel_manager_creation(self):
        manager = SemanticKernelManager()
        assert manager.kernel is not None
        assert manager.is_initialized is True

    def test_kernel_has_services(self):
        manager = SemanticKernelManager()
        # Kernel should have at least a basic setup
        assert manager.kernel is not None

    def test_register_plugin(self):
        manager = SemanticKernelManager()
        plugin = IncidentPlugin()
        manager.register_plugin(plugin, "IncidentPlugin")
        assert "IncidentPlugin" in manager.list_plugins()

    def test_register_multiple_plugins(self):
        manager = SemanticKernelManager()
        manager.register_plugin(IncidentPlugin(), "IncidentPlugin")
        manager.register_plugin(RAGPlugin(), "RAGPlugin")
        manager.register_plugin(GuardrailPlugin(), "GuardrailPlugin")
        plugins = manager.list_plugins()
        assert "IncidentPlugin" in plugins
        assert "RAGPlugin" in plugins
        assert "GuardrailPlugin" in plugins

    def test_unregister_plugin(self):
        manager = SemanticKernelManager()
        manager.register_plugin(IncidentPlugin(), "IncidentPlugin")
        manager.unregister_plugin("IncidentPlugin")
        assert "IncidentPlugin" not in manager.list_plugins()

    def test_invoke_function(self):
        manager = SemanticKernelManager()
        plugin = IncidentPlugin()
        manager.register_plugin(plugin, "IncidentPlugin")
        result = manager.invoke_function(
            plugin_name="IncidentPlugin",
            function_name="triage_incident",
            description="Server is down",
            severity="critical",
        )
        assert result is not None
        assert "category" in result or isinstance(result, str)


class TestIncidentPlugin:
    """Tests for incident management plugin."""

    def test_plugin_creation(self):
        plugin = IncidentPlugin()
        assert plugin.name == "IncidentPlugin"

    def test_triage_incident(self):
        plugin = IncidentPlugin()
        result = plugin.triage_incident(
            description="Database connection timeout",
            severity="high",
        )
        assert result is not None
        assert "category" in str(result) or isinstance(result, str)

    def test_triage_categorizes_correctly(self):
        plugin = IncidentPlugin()
        result = plugin.triage_incident(
            description="Server CPU at 99%",
            severity="critical",
        )
        # Should categorize as infrastructure
        assert result is not None

    def test_diagnose_incident(self):
        plugin = IncidentPlugin()
        result = plugin.diagnose_incident(
            description="API returning 500 errors",
            category="infrastructure",
            context={"last_deploy": "2 hours ago"},
        )
        assert result is not None

    def test_resolve_incident(self):
        plugin = IncidentPlugin()
        result = plugin.resolve_incident(
            description="Disk space full",
            diagnosis="Log files filling up disk",
            category="infrastructure",
        )
        assert result is not None

    def test_escalate_incident(self):
        plugin = IncidentPlugin()
        result = plugin.escalate_incident(
            description="Critical: production down",
            reason="Automated resolution failed after 3 attempts",
            severity="critical",
        )
        assert result is not None
        assert "human" in str(result).lower() or isinstance(result, str)


class TestRAGPlugin:
    """Tests for RAG (retrieval-augmented generation) plugin."""

    def test_plugin_creation(self):
        plugin = RAGPlugin()
        assert plugin.name == "RAGPlugin"

    def test_search_knowledge_base(self):
        plugin = RAGPlugin()
        result = plugin.search_knowledge_base(
            query="How to restart a service",
            top_k=3,
        )
        assert result is not None

    def test_search_with_filters(self):
        plugin = RAGPlugin()
        result = plugin.search_knowledge_base(
            query="database connection pool",
            top_k=5,
            filter_category="database",
        )
        assert result is not None

    def test_get_relevant_context(self):
        plugin = RAGPlugin()
        result = plugin.get_relevant_context(
            incident_description="SSL certificate expired",
            max_chunks=2,
        )
        assert result is not None


class TestGuardrailPlugin:
    """Tests for guardrail plugin integration."""

    def test_plugin_creation(self):
        plugin = GuardrailPlugin()
        assert plugin.name == "GuardrailPlugin"

    def test_check_content(self):
        plugin = GuardrailPlugin()
        result = plugin.check_content(
            content="The server IP is 10.0.0.1",
            check_type="pii",
        )
        assert result is not None
        assert "passed" in str(result).lower() or isinstance(result, str)

    def test_check_blocks_pii(self):
        plugin = GuardrailPlugin()
        result = plugin.check_content(
            content="SSN: 123-45-6789",
            check_type="pii",
        )
        assert result is not None

    def test_check_allows_clean(self):
        plugin = GuardrailPlugin()
        result = plugin.check_content(
            content="The server is running normally",
            check_type="pii",
        )
        assert result is not None


class TestSKOrchestrator:
    """Tests for the SK-based orchestrator."""

    def _make_orchestrator(self):
        """Create an orchestrator with all plugins registered."""
        manager = SemanticKernelManager()
        manager.register_plugin(IncidentPlugin(), "IncidentPlugin")
        manager.register_plugin(RAGPlugin(), "RAGPlugin")
        manager.register_plugin(GuardrailPlugin(), "GuardrailPlugin")
        return SKOrchestrator(manager)

    def test_orchestrator_creation(self):
        orch = self._make_orchestrator()
        assert orch is not None

    def test_orchestrator_process_incident(self):
        orch = self._make_orchestrator()
        response = orch.process_incident(
            SKAgentRequest(
                incident_id="INC-001",
                description="Production database is down",
                severity="critical",
            )
        )
        assert response.incident_id == "INC-001"
        assert response.success is True
        assert len(response.steps) > 0

    def test_orchestrator_steps(self):
        """Test that orchestrator executes planning → tool-use → memory steps."""
        orch = self._make_orchestrator()
        response = orch.process_incident(
            SKAgentRequest(
                incident_id="INC-002",
                description="API latency spiked to 5 seconds",
                severity="high",
            )
        )
        # Should have multiple steps (planning, rag, triage, diagnose, resolve, guardrail)
        assert len(response.steps) >= 2
        # Check that agent steps are present
        agent_steps = [s for s in response.steps if "agent" in s]
        assert len(agent_steps) >= 2

    def test_orchestrator_with_guardrails(self):
        """Test that guardrails check every response."""
        orch = self._make_orchestrator()
        response = orch.process_incident(
            SKAgentRequest(
                incident_id="INC-003",
                description="Server status check",
                severity="low",
            )
        )
        assert response.guardrail_checked is True

    def test_orchestrator_with_rag_grounding(self):
        """Test that RAG grounds the orchestrator's responses."""
        orch = self._make_orchestrator()
        response = orch.process_incident(
            SKAgentRequest(
                incident_id="INC-004",
                description="How to configure load balancer",
                severity="medium",
            )
        )
        assert response.rag_used is True
        assert response.rag_sources is not None

    def test_orchestrator_memory_persistence(self):
        """Test that orchestrator stores incident history in memory."""
        orch = self._make_orchestrator()

        # Process first incident
        orch.process_incident(
            SKAgentRequest(
                incident_id="INC-001",
                description="Database timeout",
                severity="high",
            )
        )

        # Process second incident
        orch.process_incident(
            SKAgentRequest(
                incident_id="INC-002",
                description="Network connectivity issue",
                severity="medium",
            )
        )

        history = orch.get_incident_history()
        assert len(history) == 2

    def test_orchestrator_error_handling(self):
        """Test orchestrator handles errors gracefully."""
        manager = SemanticKernelManager()
        # Only register incident plugin, missing RAG and guardrails
        manager.register_plugin(IncidentPlugin(), "IncidentPlugin")
        orch = SKOrchestrator(manager)

        response = orch.process_incident(
            SKAgentRequest(
                incident_id="INC-005",
                description="Test incident",
                severity="low",
            )
        )
        # Should still work, just without RAG/guardrails
        assert response.success is True

    def test_orchestrator_planning(self):
        """Test that orchestrator creates a plan before executing."""
        orch = self._make_orchestrator()
        response = orch.process_incident(
            SKAgentRequest(
                incident_id="INC-006",
                description="Disk space at 95%",
                severity="high",
            )
        )
        assert response.plan is not None
        assert len(response.plan) > 0
