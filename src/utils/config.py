"""
Configuration management for Enterprise AI Support Agent.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration settings."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chromadb")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "enterprise-ai-kb")
    
    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_AGENTS: int = int(os.getenv("MAX_AGENTS", "10"))
    MEMORY_LIMIT: int = int(os.getenv("MEMORY_LIMIT", "100"))
    MAX_CONVERSATION_TURNS: int = int(os.getenv("MAX_CONVERSATION_TURNS", "20"))
    
    # Policy Configuration
    MAX_URGENCY_THRESHOLD: str = os.getenv("MAX_URGENCY_THRESHOLD", "critical")
    ESCALATION_TIMEOUT: int = int(os.getenv("ESCALATION_TIMEOUT", "300"))  # seconds
    APPROVAL_REQUIRED_FOR_CRITICAL: bool = os.getenv("APPROVAL_REQUIRED_FOR_CRITICAL", "true").lower() == "true"
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration settings."""
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
        ]
        
        if cls.VECTOR_DB_TYPE == "pinecone":
            required_vars.extend([
                ("PINECONE_API_KEY", cls.PINECONE_API_KEY),
                ("PINECONE_ENVIRONMENT", cls.PINECONE_ENVIRONMENT),
            ])
        
        missing = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def get_config_dict(cls) -> dict:
        """Get configuration as dictionary."""
        return {
            "openai": {
                "api_key": cls.OPENAI_API_KEY,
                "model": cls.OPENAI_MODEL,
                "temperature": cls.OPENAI_TEMPERATURE,
                "max_tokens": cls.OPENAI_MAX_TOKENS,
            },
            "vector_db": {
                "type": cls.VECTOR_DB_TYPE,
                "pinecone_api_key": cls.PINECONE_API_KEY,
                "pinecone_environment": cls.PINECONE_ENVIRONMENT,
                "pinecone_index_name": cls.PINECONE_INDEX_NAME,
            },
            "application": {
                "log_level": cls.LOG_LEVEL,
                "max_agents": cls.MAX_AGENTS,
                "memory_limit": cls.MEMORY_LIMIT,
                "max_conversation_turns": cls.MAX_CONVERSATION_TURNS,
            },
            "policy": {
                "max_urgency_threshold": cls.MAX_URGENCY_THRESHOLD,
                "escalation_timeout": cls.ESCALATION_TIMEOUT,
                "approval_required_for_critical": cls.APPROVAL_REQUIRED_FOR_CRITICAL,
            },
            "api": {
                "host": cls.API_HOST,
                "port": cls.API_PORT,
                "workers": cls.API_WORKERS,
            }
        }