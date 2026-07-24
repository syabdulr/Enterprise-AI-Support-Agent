"""
Custom exception classes for the Enterprise AI Support Agent.
Provides structured error handling across all components.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Error codes for categorization."""
    # RAG errors (ERR_RAG_XXX)
    DOCUMENT_LOADING_ERROR = "ERR_RAG_001"
    CHUNKING_ERROR = "ERR_RAG_002"
    EMBEDDING_GENERATION_ERROR = "ERR_RAG_003"
    VECTOR_STORE_ERROR = "ERR_RAG_004"
    RETRIEVAL_ERROR = "ERR_RAG_005"
    
    # LLM errors (ERR_LLM_XXX)
    AZURE_OPENAI_ERROR = "ERR_LLM_001"
    CHAIN_EXECUTION_ERROR = "ERR_LLM_002"
    PROMPT_TEMPLATE_ERROR = "ERR_LLM_003"
    STREAM_ERROR = "ERR_LLM_004"
    
    # Orchestration errors (ERR_ORCH_XXX)
    WORKFLOW_ERROR = "ERR_ORCH_001"
    STATE_ERROR = "ERR_ORCH_002"
    AGENT_COORDINATION_ERROR = "ERR_ORCH_003"
    ROUTING_ERROR = "ERR_ORCH_004"
    
    # Configuration errors (ERR_CONFIG_XXX)
    MISSING_CONFIG = "ERR_CONFIG_001"
    INVALID_CONFIG = "ERR_CONFIG_002"
    ENVIRONMENT_ERROR = "ERR_CONFIG_003"
    
    # Validation errors (ERR_VALID_XXX)
    INVALID_INPUT = "ERR_VALID_001"
    MISSING_REQUIRED_FIELD = "ERR_VALID_002"
    TYPE_ERROR = "ERR_VALID_003"
    
    # API errors (ERR_API_XXX)
    API_ERROR = "ERR_API_001"
    AUTHENTICATION_ERROR = "ERR_API_002"
    RATE_LIMIT_ERROR = "ERR_API_003"


class EnterpriseAIException(Exception):
    """Base exception for all Enterprise AI errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        cause: Optional[Exception] = None
    ):
        """
        Initialize enterprise exception.
        
        Args:
            message: Human-readable error message
            error_code: Categorized error code
            details: Additional error details
            recoverable: Whether the error is recoverable
            cause: Original exception that caused this error
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.recoverable = recoverable
        self.cause = cause
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "cause": str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"[{self.error_code.value}] {self.message}"


class RAGException(EnterpriseAIException):
    """Exceptions related to RAG operations."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, recoverable, cause)


class LLMException(EnterpriseAIException):
    """Exceptions related to LLM operations."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, recoverable, cause)


class OrchestrationException(EnterpriseAIException):
    """Exceptions related to orchestration."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, recoverable, cause)


class ConfigurationException(EnterpriseAIException):
    """Exceptions related to configuration."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, recoverable, cause)


class ValidationException(EnterpriseAIException):
    """Exceptions related to input validation."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, recoverable, cause)


class APIException(EnterpriseAIException):
    """Exceptions related to API operations."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        cause: Optional[Exception] = None
    ):
        self.status_code = status_code
        if status_code:
            details = details or {}
            details["status_code"] = status_code
        super().__init__(message, error_code, details, recoverable, cause)


def wrap_exception(
    exception: Exception,
    error_code: ErrorCode,
    message: Optional[str] = None,
    recoverable: bool = True
) -> EnterpriseAIException:
    """
    Wrap a generic exception in an EnterpriseAIException.
    
    Args:
        exception: The original exception to wrap
        error_code: The error code to use
        message: Optional custom message (uses original message if not provided)
        recoverable: Whether the error is recoverable
        
    Returns:
        An appropriate EnterpriseAIException subclass
    """
    exc_message = message or str(exception)
    exc_details = {
        "original_exception": type(exception).__name__,
        "original_message": str(exception)
    }
    
    # Map error codes to exception classes
    if error_code.value.startswith("ERR_RAG"):
        return RAGException(exc_message, error_code, exc_details, recoverable, exception)
    elif error_code.value.startswith("ERR_LLM"):
        return LLMException(exc_message, error_code, exc_details, recoverable, exception)
    elif error_code.value.startswith("ERR_ORCH"):
        return OrchestrationException(exc_message, error_code, exc_details, recoverable, exception)
    elif error_code.value.startswith("ERR_CONFIG"):
        return ConfigurationException(exc_message, error_code, exc_details, recoverable, exception)
    elif error_code.value.startswith("ERR_VALID"):
        return ValidationException(exc_message, error_code, exc_details, recoverable, exception)
    elif error_code.value.startswith("ERR_API"):
        return APIException(exc_message, error_code, None, exc_details, recoverable, exception)
    else:
        return EnterpriseAIException(exc_message, error_code, exc_details, recoverable, exception)