"""Semantic Kernel integration for Enterprise AI Support Agent.

This module demonstrates Microsoft Semantic Kernel integration for
agentic AI patterns: planning, tool-use, memory/state, and guardrails.
"""

from .kernel_setup import SemanticKernelManager
from .models import KernelFunctionDef, PluginConfig, SKAgentRequest, SKAgentResponse
from .orchestrator import SKOrchestrator
from .plugins.guardrail_plugins import GuardrailPlugin
from .plugins.incident_plugins import IncidentPlugin
from .plugins.rag_plugins import RAGPlugin

__all__ = [
    "GuardrailPlugin",
    "IncidentPlugin",
    "KernelFunctionDef",
    "PluginConfig",
    "RAGPlugin",
    "SKAgentRequest",
    "SKAgentResponse",
    "SKOrchestrator",
    "SemanticKernelManager",
]
