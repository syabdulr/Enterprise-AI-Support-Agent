"""
LangGraph workflow for multi-agent incident response.
Defines the complete workflow using LangGraph state machines.
"""

from typing import Dict, Optional
from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .agent_coordinator import AgentCoordinator, AgentType
from ..llm.chain_builder import ChainBuilder
from ..rag.retriever import RAGRetriever
from ..agents.registry import AgentRegistry
import logging

logger = logging.getLogger(__name__)


class IncidentWorkflow:
    """LangGraph workflow for multi-agent incident response."""
    
    def __init__(
        self,
        llm_client,
        rag_retriever: RAGRetriever,
        agent_registry: AgentRegistry
    ):
        """Initialize incident workflow."""
        self.llm_client = llm_client
        self.rag_retriever = rag_retriever
        self.agent_registry = agent_registry
        self.coordinator = AgentCoordinator()
        self.chain_builder = ChainBuilder(llm_client)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Define nodes (agents)
        workflow.add_node("triage_agent", self._triage_step)
        workflow.add_node("diagnosis_agent", self._diagnosis_step)
        workflow.add_node("resolution_agent", self._resolution_step)
        workflow.add_node("escalation_agent", self._escalation_step)
        workflow.add_node("human_review_agent", self._human_review_step)
        
        # Define edges (transitions)
        workflow.set_entry_point("triage_agent")
        
        workflow.add_conditional_edges(
            "triage_agent",
            self._triage_router,
            {
                "diagnosis": "diagnosis_agent",
                "escalation": "escalation_agent"
            }
        )
        
        workflow.add_conditional_edges(
            "diagnosis_agent",
            self._diagnosis_router,
            {
                "resolution": "resolution_agent",
                "escalation": "escalation_agent",
                "triage": "triage_agent"
            }
        )
        
        workflow.add_conditional_edges(
            "resolution_agent",
            self._resolution_router,
            {
                "complete": END,
                "retry": "diagnosis_agent",
                "escalate": "escalation_agent"
            }
        )
        
        workflow.add_conditional_edges(
            "escalation_agent",
            self._escalation_router,
            {
                "human_review": "human_review_agent",
                "complete": END
            }
        )
        
        workflow.add_conditional_edges(
            "human_review_agent",
            self._human_review_router,
            {
                "proceed": "resolution_agent",
                "escalate": "escalation_agent",
                "complete": END
            }
        )
        
        return workflow.compile()
    
    def _triage_step(self, state: WorkflowState) -> WorkflowState:
        """Execute triage agent step."""
        logger.info(f"Executing triage for incident {state.incident_id}")
        
        try:
            # Retrieve relevant context using RAG
            context = self.rag_retriever.retrieve(
                state.incident_description,
                n_results=3
            )
            state.retrieved_context = context
            
            # Build triage chain
            triage_chain = self.chain_builder.build_triage_chain()
            
            # Execute triage
            messages = [
                {"role": "system", "content": "Analyze this incident and provide triage information."},
                {"role": "user", "content": state.incident_description}
            ]
            
            response = triage_chain.invoke({"input": messages[-1]["content"], "chat_history": state.conversation_history})
            
            # Parse response and update state
            state.add_to_conversation("assistant", response)
            state.current_agent = "triage"
            
            # Note: In production, you'd parse structured output
            # For now, we'll update based on response content
            state.update_timestamp()
            
            logger.info(f"Triage complete for incident {state.incident_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error in triage step: {e}")
            state.add_error(f"Triage error: {str(e)}")
            state.escalate_immediately = True
            return state
    
    def _diagnosis_step(self, state: WorkflowState) -> WorkflowState:
        """Execute diagnosis agent step."""
        logger.info(f"Executing diagnosis for incident {state.incident_id}")
        
        try:
            # Build diagnosis chain
            diagnosis_chain = self.chain_builder.build_diagnosis_chain()
            
            # Execute diagnosis with retrieved context
            context_text = "\n".join([
                doc["content"] for doc in state.retrieved_context
            ])
            
            messages = [
                {"role": "system", "content": f"Diagnose this incident. Context: {context_text}"},
                {"role": "user", "content": state.incident_description}
            ]
            
            response = diagnosis_chain.invoke({"input": messages[-1]["content"], "chat_history": state.conversation_history})
            
            # Update state
            state.add_to_conversation("assistant", response)
            state.current_agent = "diagnosis"
            state.update_timestamp()
            
            logger.info(f"Diagnosis complete for incident {state.incident_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error in diagnosis step: {e}")
            state.add_error(f"Diagnosis error: {str(e)}")
            return state
    
    def _resolution_step(self, state: WorkflowState) -> WorkflowState:
        """Execute resolution agent step."""
        logger.info(f"Executing resolution for incident {state.incident_id}")
        
        try:
            # Build resolution chain
            resolution_chain = self.chain_builder.build_resolution_chain()
            
            # Execute resolution
            messages = [
                {"role": "system", "content": "Generate resolution procedures for this incident."},
                {"role": "user", "content": f"Incident: {state.incident_description}\n\nDiagnosis: {state.root_causes}"}
            ]
            
            response = resolution_chain.invoke({"input": messages[-1]["content"], "chat_history": state.conversation_history})
            
            # Update state
            state.add_to_conversation("assistant", response)
            state.current_agent = "resolution"
            state.resolution_status = "Proposed"
            state.update_timestamp()
            
            logger.info(f"Resolution complete for incident {state.incident_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error in resolution step: {e}")
            state.add_error(f"Resolution error: {str(e)}")
            state.resolution_status = "Failed"
            return state
    
    def _escalation_step(self, state: WorkflowState) -> WorkflowState:
        """Execute escalation agent step."""
        logger.info(f"Executing escalation for incident {state.incident_id}")
        
        try:
            # Build escalation chain
            escalation_chain = self.chain_builder.build_escalation_chain()
            
            # Execute escalation
            messages = [
                {"role": "system", "content": "Prepare escalation package for this incident."},
                {"role": "user", "content": state.incident_description}
            ]
            
            response = escalation_chain.invoke({"input": messages[-1]["content"], "chat_history": state.conversation_history})
            
            # Update state
            state.add_to_conversation("assistant", response)
            state.current_agent = "escalation"
            state.requires_human_review = True
            state.update_timestamp()
            
            logger.info(f"Escalation complete for incident {state.incident_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error in escalation step: {e}")
            state.add_error(f"Escalation error: {str(e)}")
            return state
    
    def _human_review_step(self, state: WorkflowState) -> WorkflowState:
        """Execute human review agent step."""
        logger.info(f"Executing human review for incident {state.incident_id}")
        
        # This step waits for human input
        # In a real implementation, this would be a blocking operation
        state.current_agent = "human_review"
        state.update_timestamp()
        
        logger.info(f"Human review requested for incident {state.incident_id}")
        return state
    
    def _triage_router(self, state: WorkflowState) -> str:
        """Route after triage step."""
        if state.escalate_immediately:
            return "escalation"
        return "diagnosis"
    
    def _diagnosis_router(self, state: WorkflowState) -> str:
        """Route after diagnosis step."""
        if self.coordinator.should_escalate(state):
            return "escalation"
        if not state.root_causes:
            return "triage"
        return "resolution"
    
    def _resolution_router(self, state: WorkflowState) -> str:
        """Route after resolution step."""
        if state.resolution_status == "Complete":
            return "complete"
        if state.errors:
            return "escalate"
        return "retry"
    
    def _escalation_router(self, state: WorkflowState) -> str:
        """Route after escalation step."""
        if self.coordinator.requires_human_verification(state):
            return "human_review"
        return "complete"
    
    def _human_review_router(self, state: WorkflowState) -> str:
        """Route after human review step."""
        if state.human_review_decision == "approve":
            return "proceed"
        elif state.human_review_decision == "reject":
            return "escalate"
        return "complete"
    
    def run(self, incident_id: str, incident_description: str) -> WorkflowState:
        """Run the incident workflow."""
        # Initialize state
        state = WorkflowState(
            incident_id=incident_id,
            incident_title=f"Incident {incident_id}",
            incident_description=incident_description
        )
        
        logger.info(f"Starting workflow for incident {incident_id}")
        
        # Run the workflow
        final_state = self.workflow.invoke(state)
        
        logger.info(f"Workflow complete for incident {incident_id}")
        
        return final_state