"""
Agent Registry - Centralized catalog of agent capabilities.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(Enum):
    """Agent operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"


class AgentCapability(Enum):
    """Agent capability categories."""
    TRIAGE = "triage"
    DIAGNOSTIC = "diagnostic"
    RESOLUTION = "resolution"
    MONITORING = "monitoring"
    ESCALATION = "escalation"
    MEMORY = "memory"
    POLICY = "policy"


@dataclass
class AgentDefinition:
    """Definition of an agent's capabilities and configuration."""
    name: str
    description: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.ACTIVE
    version: str = "1.0.0"
    author: str = "Abdul Syed"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def can_perform(self, capability: AgentCapability) -> bool:
        """Check if agent can perform a specific capability."""
        return capability in self.capabilities


class AgentRegistry:
    """Centralized registry for managing agent definitions."""
    
    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._initialize_default_agents()
    
    def _initialize_default_agents(self) -> None:
        """Initialize the default agent catalog."""
        default_agents = [
            AgentDefinition(
                name="triage_agent",
                description="Categorizes incidents by severity and type using AI analysis",
                capabilities=[AgentCapability.TRIAGE],
                tags=["analysis", "classification", "urgency"],
                dependencies=["openai", "langchain"]
            ),
            AgentDefinition(
                name="diagnostic_agent",
                description="Analyzes root causes using RAG and technical documentation",
                capabilities=[AgentCapability.DIAGNOSTIC],
                tags=["analysis", "rag", "troubleshooting"],
                dependencies=["rag_system", "vector_db"]
            ),
            AgentDefinition(
                name="resolution_agent",
                description="Recommends solutions and remediation steps for incidents",
                capabilities=[AgentCapability.RESOLUTION],
                tags=["solutions", "remediation", "automation"],
                dependencies=["diagnostic_agent", "knowledge_base"]
            ),
            AgentDefinition(
                name="memory_agent",
                description="Manages conversation history and context for all agents",
                capabilities=[AgentCapability.MEMORY],
                tags=["context", "conversation", "persistence"],
                dependencies=[]
            ),
            AgentDefinition(
                name="policy_agent",
                description="Enforces governance rules and approval gates",
                capabilities=[AgentCapability.POLICY],
                tags=["governance", "compliance", "security"],
                dependencies=[]
            ),
            AgentDefinition(
                name="escalation_agent",
                description="Handles human-in-the-loop escalation workflows",
                capabilities=[AgentCapability.ESCALATION],
                tags=["escalation", "human-approval", "workflow"],
                dependencies=["policy_agent"]
            )
        ]
        
        for agent in default_agents:
            self.register_agent(agent)
    
    def register_agent(self, agent: AgentDefinition) -> None:
        """Register a new agent in the registry."""
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' already registered")
        
        self._agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """Get an agent definition by name."""
        return self._agents.get(name)
    
    def list_agents(self, 
                   capability: Optional[AgentCapability] = None,
                   status: Optional[AgentStatus] = None) -> List[AgentDefinition]:
        """List agents, optionally filtered by capability and status."""
        agents = list(self._agents.values())
        
        if capability:
            agents = [agent for agent in agents if capability in agent.capabilities]
        
        if status:
            agents = [agent for agent in agents if agent.status == status]
        
        return agents
    
    def update_agent_status(self, name: str, status: AgentStatus) -> bool:
        """Update agent status."""
        if name not in self._agents:
            return False
        
        self._agents[name].status = status
        return True
    
    def get_agent_count(self) -> int:
        """Get total number of registered agents."""
        return len(self._agents)
    
    def get_active_agents(self) -> List[AgentDefinition]:
        """Get all active agents."""
        return self.list_agents(status=AgentStatus.ACTIVE)
    
    def get_agent_by_capability(self, capability: AgentCapability) -> Optional[AgentDefinition]:
        """Get first available agent with specified capability."""
        agents = self.list_agents(capability=capability, status=AgentStatus.ACTIVE)
        return agents[0] if agents else None


# Global registry instance
registry = AgentRegistry()