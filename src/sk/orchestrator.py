"""SK-based orchestrator for multi-agent incident response.

Coordinates plugins through the real Semantic Kernel to process incidents
end-to-end: planning, RAG grounding, triage, diagnosis, resolution, and
guardrail checking.
"""

import json
from typing import Any, Dict, List, Optional

from .kernel_setup import SemanticKernelManager
from .models import SKAgentRequest, SKAgentResponse


class SKOrchestrator:
    """Orchestrates incident response using Semantic Kernel plugins."""

    def __init__(self, kernel_manager: SemanticKernelManager) -> None:
        self.kernel = kernel_manager
        self._incident_history: List[Dict[str, Any]] = []

    async def process_incident(self, request: SKAgentRequest) -> SKAgentResponse:
        """Process an incident through the full SK pipeline.

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

        # Step 1: Create execution plan
        plan = self._create_plan(request)
        steps.append({"step": "planning", "plan": plan})

        # Step 2: RAG grounding
        if "RAGPlugin" in self.kernel.list_plugins():
            rag_result = await self.kernel.invoke_function(
                "RAGPlugin",
                "get_relevant_context",
                incident_description=request.description,
                max_chunks=2,
            )
            rag_used = True
            rag_data = json.loads(str(rag_result))
            rag_sources = rag_data.get("sources", [])
            steps.append({"step": "rag_grounding", "result": rag_data})

        # Step 3: Triage
        triage_data = None
        category = "general"
        if "IncidentPlugin" in self.kernel.list_plugins():
            triage_result = await self.kernel.invoke_function(
                "IncidentPlugin",
                "triage_incident",
                description=request.description,
                severity=request.severity,
            )
            triage_data = json.loads(str(triage_result))
            category = triage_data.get("category", "general")
            steps.append({"step": "triage", "agent": "triage", "result": triage_data})

        # Step 4: Diagnose
        diagnosis_data = None
        if "IncidentPlugin" in self.kernel.list_plugins():
            context_str = json.dumps(request.context) if request.context else None
            diagnosis_result = await self.kernel.invoke_function(
                "IncidentPlugin",
                "diagnose_incident",
                description=request.description,
                category=category,
                context=context_str,
            )
            diagnosis_data = json.loads(str(diagnosis_result))
            steps.append({"step": "diagnosis", "agent": "diagnosis", "result": diagnosis_data})

        # Step 5: Resolve
        resolution_data = None
        diagnosis_str = ""
        if diagnosis_data and diagnosis_data.get("probable_causes"):
            diagnosis_str = diagnosis_data["probable_causes"][0]

        if "IncidentPlugin" in self.kernel.list_plugins():
            resolution_result = await self.kernel.invoke_function(
                "IncidentPlugin",
                "resolve_incident",
                description=request.description,
                diagnosis=diagnosis_str,
                category=category,
            )
            resolution_data = json.loads(str(resolution_result))
            steps.append({"step": "resolution", "agent": "resolution", "result": resolution_data})

        # Step 6: Guardrail check
        final_output = ""
        if resolution_data:
            final_output = " ".join(resolution_data.get("steps", []))

        if "GuardrailPlugin" in self.kernel.list_plugins():
            guardrail_result = await self.kernel.invoke_function(
                "GuardrailPlugin",
                "check_content",
                content=final_output,
                check_type="all",
            )
            guardrail_checked = True
            guardrail_data = json.loads(str(guardrail_result))
            steps.append({"step": "guardrail_check", "result": guardrail_data})

            if not guardrail_data.get("passed", True):
                final_output = guardrail_data.get("sanitized", final_output)

        # Build confidence score
        confidence = 0.85 if triage_data and diagnosis_data else 0.5

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
        """Get history of all processed incidents."""
        return list(self._incident_history)
