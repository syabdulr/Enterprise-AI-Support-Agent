"""
Unit tests for error handling and recovery components.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.exceptions import (
    EnterpriseAIException,
    RAGException,
    LLMException,
    OrchestrationException,
    ConfigurationException,
    ValidationException,
    APIException,
    ErrorCode,
    wrap_exception
)
from utils.retry import RetryConfig, retry_with_backoff, RetryManager


def test_exception_initialization():
    """Test exception initialization."""
    exc = EnterpriseAIException(
        message="Test error",
        error_code=ErrorCode.AZURE_OPENAI_ERROR,
        details={"key": "value"},
        recoverable=True
    )
    
    assert exc.message == "Test error"
    assert exc.error_code == ErrorCode.AZURE_OPENAI_ERROR
    assert exc.details == {"key": "value"}
    assert exc.recoverable is True


def test_exception_to_dict():
    """Test exception to_dict conversion."""
    exc = EnterpriseAIException(
        message="Test error",
        error_code=ErrorCode.AZURE_OPENAI_ERROR,
        recoverable=True
    )
    
    exc_dict = exc.to_dict()
    
    assert exc_dict["error_code"] == ErrorCode.AZURE_OPENAI_ERROR.value
    assert exc_dict["message"] == "Test error"
    assert exc_dict["recoverable"] is True


def test_rag_exception():
    """Test RAG exception."""
    exc = RAGException(
        message="RAG error",
        error_code=ErrorCode.RETRIEVAL_ERROR,
        recoverable=True
    )
    
    assert isinstance(exc, EnterpriseAIException)
    assert exc.error_code == ErrorCode.RETRIEVAL_ERROR


def test_llm_exception():
    """Test LLM exception."""
    exc = LLMException(
        message="LLM error",
        error_code=ErrorCode.AZURE_OPENAI_ERROR,
        recoverable=True
    )
    
    assert isinstance(exc, EnterpriseAIException)
    assert exc.error_code == ErrorCode.AZURE_OPENAI_ERROR


def test_api_exception_with_status_code():
    """Test API exception with status code."""
    exc = APIException(
        message="API error",
        error_code=ErrorCode.API_ERROR,
        status_code=500,
        recoverable=True
    )
    
    assert exc.status_code == 500
    assert exc.details["status_code"] == 500


def test_wrap_exception():
    """Test wrap_exception function."""
    original_error = Exception("Original error")
    
    wrapped = wrap_exception(
        original_error,
        ErrorCode.AZURE_OPENAI_ERROR,
        "Wrapped error message",
        recoverable=True
    )
    
    assert isinstance(wrapped, LLMException)
    assert wrapped.message == "Wrapped error message"
    assert wrapped.cause == original_error


def test_retry_config_initialization():
    """Test retry config initialization."""
    config = RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=30.0
    )
    
    assert config.max_attempts == 5
    assert config.base_delay == 2.0
    assert config.max_delay == 30.0


def test_retry_config_calculate_delay():
    """Test retry delay calculation."""
    config = RetryConfig(
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=False
    )
    
    # First retry: 1.0 * 2^0 = 1.0
    delay = config.calculate_delay(0)
    assert delay == 1.0
    
    # Second retry: 1.0 * 2^1 = 2.0
    delay = config.calculate_delay(1)
    assert delay == 2.0
    
    # Third retry: 1.0 * 2^2 = 4.0
    delay = config.calculate_delay(2)
    assert delay == 4.0
    
    # Should not exceed max_delay
    delay = config.calculate_delay(10)
    assert delay <= 60.0


def test_retry_with_backoff_decorator():
    """Test retry decorator."""
    call_count = 0
    
    @retry_with_backoff(config=RetryConfig(max_attempts=3, base_delay=0.1))
    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "Success"
    
    result = failing_function()
    
    assert result == "Success"
    assert call_count == 3


def test_retry_manager_context():
    """Test retry manager context manager."""
    attempt_count = 0
    
    def risky_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ValueError("First attempt fails")
        return "Result"
    
    config = RetryConfig(max_attempts=3, base_delay=0.1)
    manager = RetryManager(config)
    
    with manager:
        while manager.attempts < config.max_attempts:
            try:
                return risky_operation()
            except Exception as e:
                if manager.attempts >= config.max_attempts - 1:
                    raise
                raise


def test_error_codes_enum():
    """Test error code enum values."""
    assert ErrorCode.AZURE_OPENAI_ERROR.value == "ERR_LLM_001"
    assert ErrorCode.VECTOR_STORE_ERROR.value == "ERR_RAG_004"
    assert ErrorCode.WORKFLOW_ERROR.value == "ERR_ORCH_001"
    assert ErrorCode.MISSING_CONFIG.value == "ERR_CONFIG_001"
    assert ErrorCode.API_ERROR.value == "ERR_API_001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])