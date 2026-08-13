"""SK-based orchestrator for multi-agent incident response.

This orchestrator demonstrates the four agentic patterns the Aecon JD requires:
- Planning: creates a step plan before executing
- Tool-use: invokes kernel functions (triage, diagnose, resolve)
- Memory/state: stores incident history across requests
- Guardrails: checks every response via GuardrailPlugin

It wraps the Semantic Kernel manager and coordinates plugins to handle
incidents end-to-end, showing how Semantic Kernel can orchestrate agents
for enterprise incident response workflows.
"""

from typing import Any, Dict, List, Optional

from .kernel_setup import SemanticKernelManager
from .models import SKAgentRequest, SKAgentResponse


class SKOrchestrator:
    """Orchestrates incident response using Semantic Kernel plugins."""

    def __init__(self, kernel_manager: SemanticKernelManager) -> None:
        self.kernel = kernel_manager
        self._incident_history: List[Dict[str, Any]] = []

    def process_incident(self, request: SKAgentRequest) -> SKAgentResponse:
        """
        Process an incident through the full SK pipeline.

        Steps:
        1. Plan: Determine execution plan based on severity
        2. RAG: Ground the response in knowledge base
        3. Triage: Categorize the incident
        4. Diagnose: Identify probable causes
        5. Resolve: Generate resolution steps
        6. Guardrail: Check final output
        """
        steps: List[Dict[str, Any]] = []
        rag_sources: Optional[List[str]] = None
        rag_used = False
        guardrail_checked = False

        # Step 1: Create execution plan (planning pattern)
        plan = self._create_plan(request)
        steps.append({"step": "planning", "plan": plan})

        # Step 2: RAG grounding (memory pattern)
        rag_result = None
        if "RAGPlugin" in self.kernel.list_plugins():
            rag_result = self.kernel.invoke_function(
                "RAGPlugin",
                "get_relevant_context",
                incident_description=request.description,
                max_chunks=2,
            )
            rag_used = True
            rag_sources = rag_result.get("sources", []) if rag_result else None
            steps.append({"step": "rag_grounding", "result": rag_result})

        # Step 3: Triage (tool-use pattern)
        triage_result = None
        if "IncidentPlugin" in self.kernel.list_plugins():
            triage_result = self.kernel.invoke_function(
                "IncidentPlugin",
                "triage_incident",
                description=request.description,
                severity=request.severity,
            )
            steps.append({"step": "triage", "agent": "triage", "result": triage_result})

        # Step 4: Diagnose
        category = triage_result.get("category", "general") if triage_result else "general"
        diagnosis_result = None
        if "IncidentPlugin" in self.kernel.list_plugins():
            diagnosis_result = self.kernel.invoke_function(
                "IncidentPlugin",
                "diagnose_incident",
                description=request.description,
                category=category,
                context=request.context,
            )
            steps.append({"step": "diagnosis", "agent": "diagnosis", "result": diagnosis_result})

        # Step 5: Resolve
        diagnosis_str = ""
        if diagnosis_result and diagnosis_result.get("probable_causes"):
            diagnosis_str = diagnosis_result["probable_causes"][0]

        resolution_result = None
        if "IncidentPlugin" in self.kernel.list_plugins():
            resolution_result = self.kernel.invoke_function(
                "IncidentPlugin",
                "resolve_incident",
                description=request.description,
                diagnosis=diagnosis_str,
                category=category,
            )
            steps.append({"step": "resolution", "agent": "resolution", "result": resolution_result})

        # Step 6: Guardrail check (guardrail pattern)
        final_output = ""
        if resolution_result:
            final_output = " ".join(resolution_result.get("steps", []))

        if "GuardrailPlugin" in self.kernel.list_plugins():
            guardrail_result = self.kernel.invoke_function(
                "GuardrailPlugin",
                "check_content",
                content=final_output,
                check_type="all",
            )
            guardrail_checked = True
            steps.append({"step": "guardrail_check", "result": guardrail_result})

            if not guardrail_result.get("passed", True):
                final_output = guardrail_result.get("sanitized", final_output)

        # Build confidence score
        confidence = 0.85 if triage_result and diagnosis_result else 0.5

        # Store in memory
        self._incident_history.append(
            {
                "incident_id": request.incident_id,
                "description": request.description,
                "severity": request.severity,
                "category": category,
                "steps": len(steps),
                "confidence": confidence,
            }
        )

        return SKAgentResponse(
            incident_id=request.incident_id,
            agent_name="sk_orchestrator",
            result=final_output,
            confidence=confidence,
            success=True,
            steps=steps,
            guardrail_checked=guardrail_checked,
            rag_used=rag_used,
            rag_sources=rag_sources,
            plan=plan,
        )

    def _create_plan(self, request: SKAgentRequest) -> List[str]:
        """Create an execution plan based on incident severity."""
        plan = [
            "1. Retrieve relevant context from knowledge base",
            "2. Triage: categorize incident",
            "3. Diagnose: identify probable causes",
            "4. Resolve: generate resolution steps",
            "5. Guardrail check on final output",
        ]

        if request.severity in ("critical", "high"):
            plan.insert(0, "0. Alert on-call engineer (high severity)")
            plan.append("6. Escalate if resolution confidence < 0.7")

        return plan

    def get_incident_history(self) -> List[Dict[str, Any]]:
        """Get history of all processed incidents (memory/state pattern)."""
        return list(self._incident_history)
