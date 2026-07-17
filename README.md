# Enterprise AI Support Agent

A production-grade multi-agent incident response system powered by LangChain, LangGraph, and Retrieval-Augmented Generation (RAG).

## 🎯 Overview

The Enterprise AI Support Agent is an intelligent incident response system that:
- Uses multi-agent orchestration to analyze and resolve technical incidents
- Leverages RAG for accurate knowledge retrieval from technical documentation
- Implements policy gates and human-in-the-loop escalation for complex scenarios
- Provides real-time monitoring and metrics for performance tracking
- Offers RESTful API integration with enterprise systems

## 🏗️ Architecture

### Core Components
- **Agent Registry**: Centralized catalog of agent capabilities
- **RAG System**: Knowledge base with vector search
- **Multi-Agent Orchestration**: LangGraph workflows with agent coordination
- **Memory Service**: Conversation and context management
- **Policy Gates**: Rule enforcement and approval workflows
- **Escalation System**: Human-in-the-loop for complex incidents
- **Monitoring & Metrics**: Performance tracking and alerting

### Tech Stack
- **Backend**: Python 3.11+
- **AI Framework**: LangChain + LangGraph
- **LLM**: OpenAI GPT-4
- **Vector Database**: Pinecone/ChromaDB
- **API**: FastAPI
- **Deployment**: Docker + Azure Functions

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key with GPT-4 access
- Pinecone account (free tier) OR use ChromaDB locally
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/syabdulr/enterprise-ai-support-agent.git
cd enterprise-ai-support-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Build knowledge base
python -m src.data.kb_builder

# Run demo
python src/main.py
```

### Configuration

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.7

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=enterprise-ai-kb

# Or use ChromaDB locally
VECTOR_DB_TYPE=chromadb  # pinecone or chromadb

# Application Configuration
LOG_LEVEL=INFO
MAX_AGENTS=10
MEMORY_LIMIT=100
```

## 📚 Features

### Multi-Agent System
- **Triage Agent**: Categorizes incidents by severity and type
- **Diagnostic Agent**: Analyzes root causes using RAG
- **Resolution Agent**: Recommends solutions and remediation steps
- **Memory Management**: Tracks conversation history and context
- **Policy Enforcement**: Validates agent decisions against rules

### RAG Integration
- Knowledge base with technical documentation
- Semantic search for accurate information retrieval
- Context-aware responses
- Continuous learning from resolved incidents

### Human-in-the-Loop
- Automatic escalation for complex incidents
- Approval gates for critical actions
- Interactive API for human intervention
- Workflow pausing and resumption

### Monitoring & Observability
- Agent performance metrics
- Workflow tracing and debugging
- Error handling and retry logic
- Token usage tracking

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

## 📖 API Documentation

### Endpoints

#### Submit Incident
```
POST /api/v1/incidents
Content-Type: application/json

{
  "title": "Database connection timeout",
  "description": "Application unable to connect to database",
  "severity": "high",
  "user_id": "user_123"
}
```

#### Get Incident Status
```
GET /api/v1/incidents/{incident_id}
```

#### Escalate Incident
```
POST /api/v1/incidents/{incident_id}/escalate

{
  "reason": "Requires human expertise",
  "escalate_to": "senior_engineer"
}
```

#### Get Agent Metrics
```
GET /api/v1/metrics/agents
```

## 🐛 Troubleshooting

### Common Issues

**Issue:** OpenAI API key not working
- **Solution:** Verify API key is valid and has GPT-4 access

**Issue:** Vector database connection fails
- **Solution:** Check Pinecone credentials or switch to ChromaDB

**Issue:** Memory service not persisting
- **Solution:** Check database configuration and file permissions

### Debug Mode

```bash
# Run with debug logging
python src/main.py --log-level DEBUG

# Enable LangChain debugging
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langchain_api_key
```

## 📈 Performance Metrics

The system tracks:
- Incident resolution time
- Agent decision accuracy
- RAG retrieval precision
- Token usage and costs
- Escalation rates

## 🤝 Contributing

This is a portfolio project for demonstrating AI/ML engineering capabilities.

## 📄 License

MIT License - Abdul Syed

## 🎓 Learning Resources

- [LangChain Documentation](https://python.langchain.com/docs/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Pinecone Documentation](https://docs.pinecone.io/)

## 📞 Contact

**Developer:** Abdul Syed  
**Email:** syabdulr6@gmail.com  
**GitHub:** https://github.com/syabdulr  
**LinkedIn:** https://linkedin.com/in/abdulsyed1

---

**Project Status:** 🚧 Active Development (2-week sprint)  
**Last Updated:** July 17, 2026  
**Next Milestone:** Multi-agent orchestration (Day 5-6)