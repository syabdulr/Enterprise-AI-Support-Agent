# Configuration Guide

This document provides comprehensive configuration instructions for the Enterprise AI Support Agent.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Azure OpenAI Configuration](#azure-openai-configuration)
- [ChromaDB Configuration](#chromadb-configuration)
- [Redis Configuration](#redis-configuration)
- [API Configuration](#api-configuration)
- [Docker Configuration](#docker-configuration)
- [Monitoring Configuration](#monitoring-configuration)
- [CI/CD Configuration](#cicd-configuration)
- [Troubleshooting](#troubleshooting)

## Environment Setup

### System Requirements

- **Python**: 3.11 or higher
- **Docker**: 24.0 or higher
- **Docker Compose**: 2.20 or higher
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 10GB minimum, 50GB recommended for production

### Virtual Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env
# or
vim .env
```

## Azure OpenAI Configuration

### Azure OpenAI Setup

1. Create Azure OpenAI resource in Azure Portal
2. Create GPT-4 deployment
3. Create text-embedding-ada-002 deployment
4. Get API key and endpoint

### Environment Variables

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_MAX_TOKENS=500
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_TOP_P=0.9
AZURE_OPENAI_FREQUENCY_PENALTY=0.0
AZURE_OPENAI_PRESENCE_PENALTY=0.0
```

### Configuration File

```python
# src/llm/config.py
from pydantic import BaseSettings
from typing import Optional

class AzureOpenAIConfig(BaseSettings):
    """Azure OpenAI configuration."""
    
    api_key: str
    endpoint: str
    api_version: str = "2024-02-15-preview"
    chat_deployment: str = "gpt-4"
    embedding_deployment: str = "text-embedding-ada-002"
    max_tokens: int = 500
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    class Config:
        env_prefix = "AZURE_OPENAI_"
```

### Testing Configuration

```bash
# Test Azure OpenAI connection
curl -X POST "https://your-resource.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" \
  -H "api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

## ChromaDB Configuration

### Local ChromaDB

```env
# ChromaDB Configuration
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
CHROMADB_COLLECTION_NAME=incident_knowledge
CHROMADB_PERSIST_DIRECTORY=data/chromadb
CHROMADB_ANONYMIZED_TELEMETRY=true
```

### Docker ChromaDB

```yaml
# docker-compose.yml
services:
  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    ports:
      - "8001:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - CHROMA_SERVER_AUTH_CREDENTIALS_FILE=/secrets/chroma_credentials
      - ANONYMIZED_TELEMETRY=true
    secrets:
      - chroma_credentials

secrets:
  chroma_credentials:
    file: ./secrets/chroma_credentials.txt

volumes:
  chromadb_data:
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `CHROMADB_HOST` | `localhost` | ChromaDB server host |
| `CHROMADB_PORT` | `8001` | ChromaDB server port |
| `CHROMADB_COLLECTION_NAME` | `incident_knowledge` | Default collection name |
| `CHROMADB_PERSIST_DIRECTORY` | `data/chromadb` | Persistence directory |
| `CHROMADB_MAX_BATCH_SIZE` | `100` | Maximum batch size for inserts |

## Redis Configuration

### Local Redis

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### Docker Redis

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server host |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_PASSWORD` | (empty) | Redis password (if auth enabled) |
| `REDIS_MAX_CONNECTIONS` | `10` | Maximum connection pool size |
| `REDIS_SOCKET_TIMEOUT` | `5` | Socket timeout in seconds |

## API Configuration

### FastAPI Configuration

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_WORKERS=4
API_LOG_LEVEL=info
API_ACCESS_LOG=true
API_CORS_ORIGINS=*
API_CORS_ALLOW_CREDENTIALS=true
API_CORS_ALLOW_METHODS=*
API_CORS_ALLOW_HEADERS=*
```

### API Configuration File

```python
# src/api/config.py
from pydantic import BaseSettings

class APIConfig(BaseSettings):
    """API configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 4
    log_level: str = "info"
    access_log: bool = True
    
    # CORS
    cors_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"
    
    class Config:
        env_prefix = "API_"
```

### Rate Limiting

```env
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

### API Key Authentication

```env
# API Key Authentication
API_KEY_ENABLED=true
API_KEY_HEADER=X-API-Key
API_KEY=your_api_key_here
```

## Docker Configuration

### Dockerfile Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    VERSION=${VERSION}

# Labels
LABEL maintainer="Abdul Syed <syabdulr6@gmail.com>" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        BUILD_DATE: ${BUILD_DATE}
        VCS_REF: ${VCS_REF}
        VERSION: ${VERSION}
    container_name: enterprise-ai-api
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      - API_HOST=${API_HOST:-0.0.0.0}
      - API_PORT=${API_PORT:-8000}
    env_file:
      - .env
    depends_on:
      chromadb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

## Monitoring Configuration

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'enterprise-ai-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

### Grafana Configuration

```json
// grafana/datasources/prometheus.yml
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy",
  "isDefault": true
}
```

### Logging Configuration

```env
# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=logs/app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
LOG_ROTATION=daily
```

### Logging Configuration File

```python
# src/utils/logging_config.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = "logs/app.log"):
    """Configure application logging."""
    
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
```

## CI/CD Configuration

### GitHub Secrets

Configure the following secrets in GitHub repository settings:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `DOCKER_REGISTRY_PASSWORD`
- `ENCRYPTION_KEY`

### GitHub Actions Configuration

```yaml
# .github/workflows/ci-cd.yml
env:
  PYTHON_VERSION: "3.11"
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: enterprise-ai-support-agent
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length', '100']
```

## Troubleshooting

### Azure OpenAI Connection Issues

**Symptom:** Cannot connect to Azure OpenAI

**Solutions:**
1. Verify API key is correct
2. Check endpoint URL is correct
3. Ensure deployment name matches
4. Check Azure subscription limits

```bash
# Test connection
curl -X POST "https://your-resource.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" \
  -H "api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

### ChromaDB Connection Issues

**Symptom:** Cannot connect to ChromaDB

**Solutions:**
1. Check ChromaDB is running
2. Verify host and port configuration
3. Check firewall settings
4. Verify persistence directory permissions

```bash
# Check ChromaDB status
docker-compose ps chromadb

# Check ChromaDB logs
docker-compose logs chromadb
```

### Docker Build Issues

**Symptom:** Docker build fails

**Solutions:**
1. Clear Docker cache: `docker system prune -af`
2. Check Dockerfile syntax
3. Verify base image exists
4. Check build context

```bash
# Build with no cache
docker-compose build --no-cache

# Check Dockerfile syntax
docker build --check -f Dockerfile .
```

### Port Conflicts

**Symptom:** Port already in use

**Solutions:**
1. Check what's using the port
2. Change port configuration
3. Stop conflicting service

```bash
# Check port usage
lsof -i :8000

# Kill process using port
kill -9 $(lsof -t -i:8000)
```

### Memory Issues

**Symptom**: Out of memory errors

**Solutions**:
1. Increase Docker memory limit
2. Optimize ChromaDB batch size
3. Reduce concurrent requests
4. Add swap space

```bash
# Check Docker memory usage
docker stats

# Check system memory
free -h
```

## Configuration Validation

### Validate Environment

```bash
# Validate Python version
python --version  # Should be 3.11+

# Validate Docker version
docker --version

# Validate Docker Compose version
docker-compose --version

# Validate environment variables
python -c "from dotenv import load_dotenv; load_dotenv(); print('Environment loaded')"
```

### Validate Configuration

```python
# validate_config.py
from src.api.config import APIConfig
from src.llm.config import AzureOpenAIConfig

try:
    api_config = APIConfig()
    print("✓ API configuration valid")
except Exception as e:
    print(f"✗ API configuration error: {e}")

try:
    llm_config = AzureOpenAIConfig()
    print("✓ LLM configuration valid")
except Exception as e:
    print(f"✗ LLM configuration error: {e}")
```

---

**Document Version:** 1.0.0  
**Last Updated:** July 24, 2026  
**Maintainer:** Abdul Syed