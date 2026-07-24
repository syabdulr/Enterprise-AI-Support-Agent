"""
FastAPI main application for Enterprise AI Support Agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from src.rag.retriever import RAGRetriever
from src.llm.azure_openai_client import AzureOpenAIClient
from src.llm.chain_builder import ChainBuilder
from src.orchestration.workflow import IncidentWorkflow
from src.orchestration.state import WorkflowState
from src.agents.registry import AgentRegistry

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
llm_client = None
rag_retriever = None
workflow = None


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


# Create FastAPI app
app = FastAPI(
    title="Enterprise AI Support Agent",
    description="Multi-agent AI system for incident response and resolution",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Enterprise AI Support Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "llm_client": llm_client is not None,
            "rag_retriever": rag_retriever is not None,
            "workflow": workflow is not None
        }
    }


@app.post("/incident")
async def handle_incident(incident: dict):
    """Handle an incident request."""
    try:
        incident_id = incident.get("incident_id", "INC-001")
        description = incident.get("description", "")
        
        if not description:
            raise HTTPException(status_code=400, detail="Description is required")
        
        # Run workflow
        result = workflow.run(incident_id, description)
        
        return {
            "incident_id": incident_id,
            "status": result.workflow_status,
            "result": result.to_dict()
        }
    
    except Exception as e:
        logger.error(f"Error handling incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/components")
async def get_components():
    """Get system components status."""
    return {
        "llm": {
            "status": "ready" if llm_client else "not initialized",
            "type": "Azure OpenAI"
        },
        "rag": {
            "status": "ready" if rag_retriever else "not initialized",
            "type": "ChromaDB"
        },
        "workflow": {
            "status": "ready" if workflow else "not initialized",
            "type": "LangGraph"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)