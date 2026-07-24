# Architecture Diagrams

This document contains detailed architecture diagrams for the Enterprise AI Support Agent system.

## Table of Contents

- [System Architecture](#system-architecture)
- [Component Architecture](#component-architecture)
- [Data Flow Diagrams](#data-flow-diagrams)
- [Deployment Architecture](#deployment-architecture)
- [Sequence Diagrams](#sequence-diagrams)

## System Architecture

### High-Level System View

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Application]
        API_CLIENT[API Client]
        MOBILE[Mobile App]
    end
    
    subgraph "API Gateway"
        NGINX[Nginx Reverse Proxy]
        FASTAPI[FastAPI Application]
    end
    
    subgraph "Application Layer"
        COORD[Agent Coordinator]
        WORKFLOW[LangGraph Workflow]
        STATE[State Manager]
    end
    
    subgraph "Agent Layer"
        TRIAGE[Triage Agent]
        DIAG[Diagnosis Agent]
        RESOL[Resolution Agent]
        ESCAL[Escalation Agent]
    end
    
    subgraph "AI Layer"
        RAG[RAG System]
        LLM[Azure OpenAI Client]
        CHROMA[ChromaDB]
        EMBED[Embedding Generator]
    end
    
    subgraph "Infrastructure Layer"
        REDIS[Redis Cache]
        LOGS[Centralized Logging]
        METRICS[Prometheus]
        ALERTS[AlertManager]
    end
    
    subgraph "External Services"
        AZURE[Azure OpenAI]
        INCIDENT[Incident Management]
        NOTIFICATION[Notification Service]
    end
    
    WEB --> NGINX
    API_CLIENT --> NGINX
    MOBILE --> NGINX
    
    NGINX --> FASTAPI
    
    FASTAPI --> COORD
    FASTAPI --> RAG
    FASTAPI --> LLM
    
    COORD --> WORKFLOW
    WORKFLOW --> STATE
    
    WORKFLOW --> TRIAGE
    WORKFLOW --> DIAG
    WORKFLOW --> RESOL
    WORKFLOW --> ESCAL
    
    RAG --> CHROMA
    RAG --> EMBED
    
    LLM --> AZURE
    RAG --> AZURE
    
    COORD --> REDIS
    WORKFLOW --> REDIS
    FASTAPI --> REDIS
    
    FASTAPI --> LOGS
    COORD --> LOGS
    WORKFLOW --> LOGS
    
    FASTAPI --> METRICS
    COORD --> METRICS
    WORKFLOW --> METRICS
    
    METRICS --> ALERTS
    ALERTS --> NOTIFICATION
    
    ESCAL --> INCIDENT
```

## Component Architecture

### API Layer Components

```mermaid
graph LR
    subgraph "API Layer"
        API[FastAPI App]
        SCHEMAS[Pydantic Schemas]
        MIDDLEWARE[CORS/Logging]
        ROUTES[Route Handlers]
        VALIDATION[Request Validation]
    end
    
    API --> SCHEMAS
    API --> MIDDLEWARE
    API --> ROUTES
    ROUTES --> VALIDATION
    VALIDATION --> SCHEMAS
```

### Orchestration Layer Components

```mermaid
graph TB
    subgraph "Orchestration Layer"
        COORD[Agent Coordinator]
        REGISTRY[Agent Registry]
        ROUTER[Conditional Router]
        GRAPH[LangGraph Workflow]
        STATE[Workflow State]
        POLICY[Policy Gates]
    end
    
    COORD --> REGISTRY
    COORD --> ROUTER
    ROUTER --> GRAPH
    GRAPH --> STATE
    GRAPH --> POLICY
    
    REGISTRY -.-> AGENT1[Agent 1]
    REGISTRY -.-> AGENT2[Agent 2]
    REGISTRY -.-> AGENT3[Agent 3]
```

### RAG System Components

```mermaid
graph LR
    subgraph "RAG System"
        RETRIEVER[RAG Retriever]
        LOADER[Document Loader]
        CHUNKER[Text Chunker]
        EMBED[Embedding Generator]
        STORE[ChromaDB Store]
    end
    
    RETRIEVER --> STORE
    RETRIEVER --> EMBED
    STORE <-- CHUNKER
    CHUNKER <-- LOADER
    EMBED --> CHUNKER
```

### LLM Layer Components

```mermaid
graph TB
    subgraph "LLM Layer"
        CLIENT[Azure OpenAI Client]
        CHAINS[Chain Builder]
        PROMPTS[Prompt Templates]
        STREAM[Streaming Handler]
        CACHE[Response Cache]
    end
    
    CLIENT --> CHAINS
    CHAINS --> PROMPTS
    CLIENT --> STREAM
    CLIENT --> CACHE
    PROMPTS --> CHAINS
```

## Data Flow Diagrams

### Incident Processing Flow

```mermaid
sequenceDiagram
    participant User as User
    participant API as FastAPI
    participant Coord as Coordinator
    participant Triage as Triage Agent
    participant Diag as Diagnosis Agent
    participant RAG as RAG System
    participant LLM as LLM Engine
    participant Resol as Resolution Agent
    participant DB as ChromaDB
    
    User->>API: POST /incident
    API->>API: Validate Request
    API->>Coord: Submit Incident
    Coord->>Coord: Initialize State
    
    Coord->>Triage: Classify Incident
    Triage->>LLM: Generate Classification
    LLM->>Triage: Severity & Category
    Triage->>Coord: Return Triage Result
    Coord->>Coord: Update State
    
    Coord->>Diag: Analyze Root Cause
    Diag->>RAG: Query Knowledge Base
    RAG->>DB: Vector Search
    DB->>RAG: Relevant Documents
    RAG->>Diag: Return Context
    Diag->>LLM: Analyze with Context
    LLM->>Diag: Diagnosis Result
    Diag->>Coord: Return Diagnosis
    Coord->>Coord: Update State
    
    Coord->>Resol: Generate Resolution
    Resol->>RAG: Query Solutions
    RAG->>Resol: Return Solutions
    Resol->>LLM: Generate Steps
    LLM->>Resol: Resolution Plan
    Resol->>Coord: Return Resolution
    Coord->>Coord: Update State
    
    Coord->>API: Return Complete Result
    API->>User: HTTP 200 Response
```

### RAG Query Flow

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant RAG as RAG Retriever
    participant Embed as Embedding Gen
    participant Chroma as ChromaDB
    participant LLM as LLM Engine
    
    Agent->>RAG: Query Knowledge Base
    RAG->>Embed: Generate Query Embedding
    Embed->>LLM: Text to Embedding
    LLM->>Embed: Vector Representation
    Embed->>RAG: Return Query Vector
    
    RAG->>Chroma: Vector Similarity Search
    Chroma->>Chroma: Query Index
    Chroma->>Chroma: Rank Results
    Chroma->>RAG: Return Top Documents
    
    RAG->>RAG: Format Results
    RAG->>Agent: Return Context
```

### LLM Generation Flow

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant Chain as LangChain Chain
    participant Prompt as Prompt Template
    participant RAG as RAG System
    participant LLM as Azure OpenAI
    participant Stream as Stream Handler
    
    Agent->>Chain: Invoke Chain
    Chain->>RAG: Retrieve Context
    RAG->>Chain: Return Documents
    
    Chain->>Prompt: Format Prompt
    Prompt->>Prompt: Add Context
    Prompt->>Prompt: Add System Message
    Prompt->>Chain: Return Formatted Prompt
    
    Chain->>LLM: Generate Response
    LLM->>Stream: Stream Tokens
    Stream->>Chain: Accumulate Tokens
    
    Stream->>Stream: All Tokens Received
    Stream->>LLM: Complete
    LLM->>Chain: Return Response
    Chain->>Agent: Return Result
```

## Deployment Architecture

### Development Environment

```mermaid
graph TB
    subgraph "Development Environment"
        DEV[Developer Machine]
        COMPOSE[Docker Compose]
        
        subgraph "Containers"
            API[API Container]
            CHROMA[ChromaDB Container]
            REDIS[Redis Container]
            NGINX[Nginx Container]
        end
    end
    
    DEV --> COMPOSE
    COMPOSE --> API
    COMPOSE --> CHROMA
    COMPOSE --> REDIS
    COMPOSE --> NGINX
    
    API -.-> CHROMA
    API -.-> REDIS
    NGINX -.-> API
```

### Production Environment

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Kubernetes Cluster"
            subgraph "Ingress"
                INGRESS[Nginx Ingress]
            end
            
            subgraph "API Deployment"
                API1[API Pod 1]
                API2[API Pod 2]
                API3[API Pod 3]
            end
            
            subgraph "Stateful Services"
                CHROMA[ChromaDB StatefulSet]
                REDIS[Redis Cluster]
            end
            
            subgraph "Monitoring"
                PROM[Prometheus]
                GRAF[Grafana]
            end
        end
        
        subgraph "External"
            AZURE[Azure OpenAI]
            NOTIF[Notification Service]
        end
    end
    
    INGRESS --> API1
    INGRESS --> API2
    INGRESS --> API3
    
    API1 -.-> CHROMA
    API2 -.-> CHROMA
    API3 -.-> CHROMA
    
    API1 -.-> REDIS
    API2 -.-> REDIS
    API3 -.-> REDIS
    
    API1 --> PROM
    API2 --> PROM
    API3 --> PROM
    
    PROM --> GRAF
    
    API1 --> AZURE
    API2 --> AZURE
    API3 --> AZURE
    
    PROM --> NOTIF
```

## Sequence Diagrams

### Multi-Agent Workflow

```mermaid
sequenceDiagram
    participant API as API
    participant Coord as Coordinator
    participant State as State Manager
    participant Triage as Triage
    participant Diag as Diagnosis
    participant Resol as Resolution
    participant Escal as Escalation
    
    API->>Coord: Submit Incident
    Coord->>State: Initialize State
    State-->>Coord: State Created
    
    Coord->>Triage: Analyze Incident
    Triage-->>Coord: Triage Result
    Coord->>State: Update State
    
    State-->>Coord: State Updated
    Coord->>Diag: Diagnose Issue
    Diag-->>Coord: Diagnosis Result
    Coord->>State: Update State
    
    State-->>Coord: State Updated
    Coord->>Resol: Generate Resolution
    Resol-->>Coord: Resolution Plan
    Coord->>State: Update State
    
    State-->>Coord: State Updated
    Coord->>API: Return Result
    API-->>User: Response
```

### Error Recovery Flow

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant Retry as Retry Manager
    participant LLM as LLM Client
    participant Fallback as Fallback Strategy
    participant State as State Manager
    participant User as User
    
    Agent->>LLM: Request
    LLM-->>Agent: Error
    
    Agent->>Retry: Handle Error
    Retry->>Retry: Check Retry Config
    Retry->>LLM: Retry Request (Attempt 1)
    LLM-->>Retry: Error Again
    
    Retry->>Retry: Check Retry Count
    Retry->>LLM: Retry Request (Attempt 2)
    LLM-->>Retry: Error Again
    
    Retry->>Fallback: Max Retries Exceeded
    Fallback->>Fallback: Select Fallback
    Fallback-->>Retry: Fallback Response
    
    Retry->>State: Record Error
    State-->>Retry: State Updated
    Retry-->>Agent: Fallback Result
    Agent-->>User: Response with Warning
```

### Human-in-the-Loop Flow

```mermaid
sequenceDiagram
    participant User as System
    participant Workflow as Workflow
    participant Agent as Escalation Agent
    participant Human as Human Operator
    participant State as State Manager
    
    User->>Workflow: Submit Complex Incident
    Workflow->>Agent: Process Incident
    
    Agent->>Agent: Evaluate Complexity
    Agent->>Workflow: Requires Escalation
    
    Workflow->>State: Pause Workflow
    State-->>Workflow: Workflow Paused
    
    Workflow->>Human: Notify Human
    Human->>Human: Review Incident
    Human->>Human: Provide Input
    
    Human->>Workflow: Submit Decision
    Workflow->>State: Resume Workflow
    State-->>Workflow: Workflow Resumed
    
    Workflow->>Agent: Continue with Human Input
    Agent-->>Workflow: Final Result
    Workflow-->>User: Complete Response
```

---

**Document Version:** 1.0.0  
**Last Updated:** July 24, 2026  
**Maintainer:** Abdul Syed