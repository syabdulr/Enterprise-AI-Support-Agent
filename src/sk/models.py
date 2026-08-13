"""Models for Semantic Kernel integration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SKAgentRequest:
    """Request for SK-based agent processing."""

    incident_id: str
    description: str
    severity: str = "medium"
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "description": self.description,
            "severity": self.severity,
            "context": self.context,
        }


@dataclass
class SKAgentResponse:
    """Response from SK-based agent processing."""

    incident_id: str
    agent_name: str
    result: str
    confidence: float = 0.0
    success: bool = True
    error: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    guardrail_checked: bool = False
    rag_used: bool = False
    rag_sources: Optional[List[str]] = None
    plan: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "agent_name": self.agent_name,
            "result": self.result,
            "confidence": self.confidence,
            "success": self.success,
            "error": self.error,
            "steps": self.steps,
            "guardrail_checked": self.guardrail_checked,
            "rag_used": self.rag_used,
            "rag_sources": self.rag_sources,
            "plan": self.plan,
        }


@dataclass
class KernelFunctionDef:
    """Definition of a Semantic Kernel function."""

    name: str
    description: str
    plugin_name: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "plugin_name": self.plugin_name,
            "parameters": self.parameters,
        }


@dataclass
class PluginConfig:
    """Configuration for an SK plugin."""

    name: str
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "settings": self.settings,
        }
