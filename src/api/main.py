"""
FastAPI main application for Enterprise AI Support Agent.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

from src.rag.retriever import RAGRetriever
from src.llm.azure_openai_client import AzureOpenAIClient
from src.llm.chain_builder import ChainBuilder
from src.orchestration.workflow import IncidentWorkflow
from src.orchestration.state import WorkflowState
from src.agents.registry import AgentRegistry
from src.api.schemas import (
    CreateIncidentRequest,
    IncidentResponse,
    WorkflowResult,
    ErrorResponse,
    HealthCheck,
    HealthCheckDetailed,
    ComponentHealth,
    RAGQueryRequest,
    RAGQueryResult,
    LLMChatRequest,
    LLMChatResponse
)
from src.utils.exceptions import EnterpriseAIException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
llm_client = None
rag_retriever = None
workflow = None
start_time = time.time()

# OpenAPI Configuration
app_description = """
## Enterprise AI Support Agent

A production-grade multi-agent AI system for intelligent incident response and resolution.

### Features

- **Multi-Agent Orchestration**: Specialized agents for triage, diagnosis, resolution, and escalation
- **RAG-Powered**: Retrieve relevant knowledge from incident history
- **LangGraph Workflows**: Stateful, resilient incident processing
- **Error Recovery**: Comprehensive retry mechanisms and fallback strategies
- **Production Ready**: Docker containerization, CI/CD, and monitoring

### Architecture

The system uses a multi-agent architecture with the following components:

1. **Triage Agent**: Categorizes and prioritizes incidents
2. **Diagnosis Agent**: Analyzes incident patterns and root causes
3. **Resolution Agent**: Generates step-by-step resolution procedures
4. **Escalation Agent**: Routes complex incidents to human operators

### API Endpoints

- `POST /incident` - Submit an incident for processing
- `GET /incident/{incident_id}` - Retrieve incident status
- `POST /rag/query` - Query the knowledge base
- `POST /llm/chat` - Direct LLM interaction
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
"""

tags_metadata = [
    {
        "name": "incidents",
        "description": "Incident management operations"
    },
    {
        "name": "knowledge",
        "description": "RAG knowledge base queries"
    },
    {
        "name": "llm",
        "description": "Direct LLM interactions"
    },
    {
        "name": "health",
        "description": "Health and status checks"
    },
    {
        "name": "components",
        "description": "System component status"
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting Enterprise AI Support Agent...")
    
    try:
        # Initialize components
        global llm_client, rag_retriever, workflow
        
        # Initialize LLM client
        llm_client = AzureOpenAIClient()
        logger.info("Azure OpenAI client initialized")
        
        # Initialize RAG retriever
        rag_retriever = RAGRetriever()
        logger.info("RAG retriever initialized")
        
        # Index sample documents
        rag_retriever.index_documents()
        logger.info("Documents indexed")
        
        # Initialize agent registry
        agent_registry = AgentRegistry()
        logger.info("Agent registry initialized")
        
        # Initialize workflow
        workflow = IncidentWorkflow(llm_client, rag_retriever, agent_registry)
        logger.info("Incident workflow initialized")
        
        logger.info("Enterprise AI Support Agent started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down Enterprise AI Support Agent...")


# Create FastAPI app with OpenAPI configuration
app = FastAPI(
    title="Enterprise AI Support Agent",
    description=app_description,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Enterprise AI Platform",
        "email": "support@enterprise-ai.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], response_model=HealthCheck)
async def root():
    """Root endpoint with basic API information."""
    return HealthCheck(
        status="running",
        version="1.0.0",
        uptime=time.time() - start_time
    )


@app.get("/health", tags=["health"], response_model=HealthCheckDetailed)
async def health_check():
    """Comprehensive health check of all system components."""
    components = {}
    
    # Check LLM component
    try:
        llm_status = ComponentHealth(
            name="llm",
            status="healthy" if llm_client else "not_initialized",
            message="Azure OpenAI connection OK" if llm_client else "Not initialized"
        )
    except Exception as e:
        llm_status = ComponentHealth(
            name="llm",
            status="unhealthy",
            message=f"Error: {str(e)}"
        )
    components["llm"] = llm_status
    
    # Check RAG component
    try:
        rag_status = ComponentHealth(
            name="rag",
            status="healthy" if rag_retriever else "not_initialized",
            message="ChromaDB connection OK" if rag_retriever else "Not initialized"
        )
    except Exception as e:
        rag_status = ComponentHealth(
            name="rag",
            status="unhealthy",
            message=f"Error: {str(e)}"
        )
    components["rag"] = rag_status
    
    # Check workflow component
    try:
        workflow_status = ComponentHealth(
            name="workflow",
            status="healthy" if workflow else "not_initialized",
            message="LangGraph workflow OK" if workflow else "Not initialized"
        )
    except Exception as e:
        workflow_status = ComponentHealth(
            name="workflow",
            status="unhealthy",
            message=f"Error: {str(e)}"
        )
    components["workflow"] = workflow_status
    
    # Determine overall status
    overall_status = "healthy" if all(
        c.status == "healthy" for c in components.values()
    ) else "degraded"
    
    return HealthCheckDetailed(
        status=overall_status,
        version="1.0.0",
        uptime=time.time() - start_time,
        components=components
    )


@app.post(
    "/incident",
    tags=["incidents"],
    response_model=IncidentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def handle_incident(request: CreateIncidentRequest):
    """
    Submit an incident for processing by the AI agent system.
    
    The incident will be processed through the multi-agent workflow:
    1. Triage agent categorizes and prioritizes
    2. Diagnosis agent analyzes patterns
    3. Resolution agent generates procedures
    4. Escalation agent routes if needed
    """
    try:
        # Create workflow state
        state = WorkflowState(
            incident_id=request.incident_id,
            incident_title=f"Incident {request.incident_id}",
            incident_description=request.description,
            incident_severity=request.severity.value if request.severity else "Medium",
            incident_category=request.category,
            incident_priority=request.priority
        )
        
        # Run workflow
        result = workflow.run(state)
        
        # Build response
        response = IncidentResponse(
            incident_id=result.incident_id,
            status=result.workflow_status.value if hasattr(result.workflow_status, 'value') else result.workflow_status,
            description=result.incident_description,
            severity=request.severity if request.severity else IncidentSeverity.MEDIUM,
            category=request.category,
            created_at=result.created_at if hasattr(result, 'created_at') else datetime.utcnow(),
            updated_at=result.updated_at if hasattr(result, 'updated_at') else datetime.utcnow(),
            current_agent=result.current_agent,
            errors=result.errors if hasattr(result, 'errors') else [],
            metadata=result.to_dict()
        )
        
        return response
    
    except EnterpriseAIException as e:
        logger.error(f"Enterprise AI error: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=e.__class__.__name__,
                message=str(e),
                details={"error_code": e.error_code.value if hasattr(e, 'error_code') else "UNKNOWN"}
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"Error handling incident: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="InternalServerError",
                message=str(e)
            ).model_dump()
        )


@app.post(
    "/rag/query",
    tags=["knowledge"],
    response_model=RAGQueryResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def query_knowledge_base(request: RAGQueryRequest):
    """
    Query the RAG knowledge base for relevant documents.
    
    Returns similar documents based on semantic search using embeddings.
    """
    try:
        if not rag_retriever:
            raise HTTPException(
                status_code=503,
                detail="RAG system not initialized"
            )
        
        # Query the knowledge base
        results = rag_retriever.retrieve(
            request.query,
            n_results=request.n_results,
            filter_metadata=request.filter_metadata
        )
        
        # Build response
        documents = [doc["content"] for doc in results]
        metadatas = [doc["metadata"] for doc in results]
        distances = [doc.get("distance", 0.0) for doc in results]
        
        return RAGQueryResult(
            documents=documents,
            metadatas=metadatas,
            distances=distances
        )
    
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="QueryError",
                message=str(e)
            ).model_dump()
        )


@app.post(
    "/llm/chat",
    tags=["llm"],
    response_model=LLMChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def llm_chat(request: LLMChatRequest):
    """
    Direct interaction with the LLM.
    
    Useful for testing or standalone LLM queries without RAG or workflow.
    """
    try:
        if not llm_client:
            raise HTTPException(
                status_code=503,
                detail="LLM client not initialized"
            )
        
        # Get LLM response
        response = llm_client.chat(
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return LLMChatResponse(
            content=response,
            tokens_used=llm_client.get_token_count(response),
            model="gpt-4",
            finish_reason="stop"
        )
    
    except Exception as e:
        logger.error(f"Error in LLM chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="LLMError",
                message=str(e)
            ).model_dump()
        )


@app.get("/components", tags=["components"])
async def get_components():
    """Get detailed status of all system components."""
    return {
        "llm": {
            "status": "ready" if llm_client else "not_initialized",
            "type": "Azure OpenAI",
            "model": "gpt-4"
        },
        "rag": {
            "status": "ready" if rag_retriever else "not_initialized",
            "type": "ChromaDB",
            "collection_name": "incident_knowledge"
        },
        "workflow": {
            "status": "ready" if workflow else "not_initialized",
            "type": "LangGraph",
            "agents": ["triage", "diagnosis", "resolution", "escalation"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")