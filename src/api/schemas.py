"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class IncidentStatus(str, Enum):
    """Incident status values."""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class CreateIncidentRequest(BaseModel):
    """Request model for creating an incident."""
    incident_id: str = Field(..., description="Unique incident identifier")
    description: str = Field(..., min_length=10, description="Incident description")
    severity: Optional[IncidentSeverity] = Field(IncidentSeverity.MEDIUM, description="Incident severity")
    category: Optional[str] = Field(None, description="Incident category")
    priority: Optional[str] = Field(None, description="Incident priority")
    additional_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "INC-2024-001",
                "description": "Network timeout when connecting to database server",
                "severity": "High",
                "category": "Network",
                "priority": "P1"
            }
        }


class Resolution(BaseModel):
    """Resolution information."""
    resolution: str = Field(..., description="Resolution description")
    steps_taken: List[str] = Field(default_factory=list, description="Steps taken to resolve")
    resolved_by: str = Field(..., description="Who resolved the incident")
    resolved_at: datetime = Field(default_factory=datetime.utcnow, description="Resolution timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resolution": "Updated database connection string and increased timeout",
                "steps_taken": [
                    "Reviewed database logs",
                    "Updated connection string",
                    "Increased timeout to 30s"
                ],
                "resolved_by": "AI Agent"
            }
        }


class IncidentResponse(BaseModel):
    """Response model for incident operations."""
    incident_id: str = Field(..., description="Incident identifier")
    status: IncidentStatus = Field(..., description="Incident status")
    description: str = Field(..., description="Incident description")
    severity: IncidentSeverity = Field(..., description="Incident severity")
    category: Optional[str] = Field(None, description="Incident category")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    current_agent: str = Field(..., description="Currently processing agent")
    resolution: Optional[Resolution] = Field(None, description="Resolution if resolved")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "INC-2024-001",
                "status": "resolved",
                "description": "Network timeout when connecting to database server",
                "severity": "High",
                "category": "Network",
                "current_agent": "resolution",
                "resolution": {
                    "resolution": "Updated database connection string",
                    "steps_taken": ["Reviewed logs", "Updated config"],
                    "resolved_by": "AI Agent"
                },
                "errors": []
            }
        }


class AgentOutput(BaseModel):
    """Output from an individual agent."""
    agent_name: str = Field(..., description="Name of the agent")
    status: str = Field(..., description="Agent execution status")
    output: str = Field(..., description="Agent output/recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "triage",
                "status": "completed",
                "output": "Incident classified as network issue",
                "confidence": 0.95,
                "processing_time": 1.23
            }
        }


class WorkflowResult(BaseModel):
    """Result from the complete workflow."""
    incident_id: str = Field(..., description="Incident identifier")
    workflow_status: str = Field(..., description="Overall workflow status")
    final_status: IncidentStatus = Field(..., description="Final incident status")
    agents_executed: List[str] = Field(..., description="List of agents executed")
    total_processing_time: float = Field(..., description="Total processing time")
    result: str = Field(..., description="Final result/diagnosis")
    resolution: Optional[str] = Field(None, description="Resolution if available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "INC-2024-001",
                "workflow_status": "completed",
                "final_status": "resolved",
                "agents_executed": ["triage", "diagnosis", "resolution"],
                "total_processing_time": 3.45,
                "result": "Network timeout due to firewall rule",
                "resolution": "Updated firewall rule to allow database traffic"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid incident ID format",
                "details": {"field": "incident_id", "expected": "INC-XXXX-XXX"}
            }
        }


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5
            }
        }


class ComponentHealth(BaseModel):
    """Individual component health."""
    name: str = Field(..., description="Component name")
    status: str = Field(..., description="Component status")
    message: Optional[str] = Field(None, description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "llm",
                "status": "healthy",
                "message": "Azure OpenAI connection OK"
            }
        }


class HealthCheckDetailed(HealthCheck):
    """Detailed health check with components."""
    components: Dict[str, ComponentHealth] = Field(..., description="Individual component statuses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5,
                "components": {
                    "llm": {"name": "llm", "status": "healthy", "message": "Connection OK"},
                    "rag": {"name": "rag", "status": "healthy", "message": "ChromaDB OK"}
                }
            }
        }


class RAGQueryRequest(BaseModel):
    """Request for RAG query."""
    query: str = Field(..., min_length=1, description="Query text")
    n_results: int = Field(5, ge=1, le=20, description="Number of results to return")
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "database connection timeout",
                "n_results": 5
            }
        }


class RAGQueryResult(BaseModel):
    """Result from RAG query."""
    documents: List[str] = Field(..., description="Retrieved documents")
    metadatas: List[Dict[str, Any]] = Field(..., description="Document metadata")
    distances: List[float] = Field(..., description="Distance scores")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": ["Database timeout documentation..."],
                "metadatas": [{"filename": "db_guide.md"}],
                "distances": [0.123]
            }
        }


class LLMChatRequest(BaseModel):
    """Request for LLM chat completion."""
    messages: List[Dict[str, str]] = Field(..., min_items=1, description="Chat messages")
    max_tokens: Optional[int] = Field(500, ge=1, le=2000, description="Max tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Temperature for sampling")
    stream: Optional[bool] = Field(False, description="Enable streaming")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What causes database timeouts?"}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
        }


class LLMChatResponse(BaseModel):
    """Response from LLM chat."""
    content: str = Field(..., description="Generated content")
    tokens_used: int = Field(..., description="Tokens used")
    model: str = Field(..., description="Model used")
    finish_reason: str = Field(..., description="Reason for completion")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Database timeouts can occur due to...",
                "tokens_used": 150,
                "model": "gpt-4",
                "finish_reason": "stop"
            }
        }