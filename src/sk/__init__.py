"""Semantic Kernel integration for Enterprise AI Support Agent.

Uses the real semantic-kernel SDK for agentic AI patterns:
planning, tool-use, memory/state, and guardrails.
"""

from .kernel_setup import SemanticKernelManager
from .models import SKAgentRequest, SKAgentResponse
from .orchestrator import SKOrchestrator
from .plugins.guardrail_plugins import GuardrailPlugin
from .plugins.incident_plugins import IncidentPlugin
from .plugins.rag_plugins import RAGPlugin

__all__ = [
    "GuardrailPlugin",
    "IncidentPlugin",
    "RAGPlugin",
    "SKAgentRequest",
    "SKAgentResponse",
    "SKOrchestrator",
    "SemanticKernelManager",
]
