"""
Error recovery strategies for incident workflows.
Provides mechanisms to recover from various error conditions.
"""

import time
import logging
from typing import Optional, Callable, Dict, Any
from .exceptions import EnterpriseAIException, ErrorCode

logger = logging.getLogger(__name__)


class RecoveryStrategy:
    """Base class for recovery strategies."""
    
    def can_recover(self, error: EnterpriseAIException) -> bool:
        """
        Determine if this strategy can recover from the error.
        
        Args:
            error: The error to attempt recovery from
            
        Returns:
            True if recovery is possible, False otherwise
        """
        raise NotImplementedError
    
    def recover(self, error: EnterpriseAIException, context: Dict[str, Any]) -> bool:
        """
        Attempt to recover from the error.
        
        Args:
            error: The error to recover from
            context: Additional context for recovery
            
        Returns:
            True if recovery was successful, False otherwise
        """
        raise NotImplementedError


class RetryRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy that retries the operation."""
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize retry recovery strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
    
    def can_recover(self, error: EnterpriseAIException) -> bool:
        """Retry recovery works for recoverable errors."""
        return error.recoverable and error.error_code in [
            ErrorCode.AZURE_OPENAI_ERROR,
            ErrorCode.VECTOR_STORE_ERROR,
            ErrorCode.API_ERROR,
            ErrorCode.RATE_LIMIT_ERROR
        ]
    
    def recover(self, error: EnterpriseAIException, context: Dict[str, Any]) -> bool:
        """Attempt to recover by retrying."""
        retry_count = context.get("retry_count", 0)
        
        if retry_count >= self.max_retries:
            logger.warning(f"Max retries ({self.max_retries}) exceeded for {error.error_code}")
            return False
        
        context["retry_count"] = retry_count + 1
        logger.info(f"Retry recovery attempt {retry_count + 1}/{self.max_retries} for {error.error_code}")
        return True


class FallbackRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy that falls back to a secondary method."""
    
    def __init__(self, fallback_method: Optional[Callable] = None):
        """
        Initialize fallback recovery strategy.
        
        Args:
            fallback_method: Method to call as fallback
        """
        self.fallback_method = fallback_method
    
    def can_recover(self, error: EnterpriseAIException) -> bool:
        """Fallback recovery works for most errors."""
        return error.recoverable and self.fallback_method is not None
    
    def recover(self, error: EnterpriseAIException, context: Dict[str, Any]) -> bool:
        """Attempt to recover by calling fallback method."""
        if not self.fallback_method:
            return False
        
        try:
            logger.info(f"Attempting fallback recovery for {error.error_code}")
            result = self.fallback_method(**context)
            logger.info("Fallback recovery successful")
            return True
        except Exception as e:
            logger.error(f"Fallback recovery failed: {e}")
            return False


class DegradationRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy that degrades service gracefully."""
    
    def __init__(self, degraded_method: Optional[Callable] = None):
        """
        Initialize degradation recovery strategy.
        
        Args:
            degraded_method: Method to call with degraded functionality
        """
        self.degraded_method = degraded_method
    
    def can_recover(self, error: EnterpriseAIException) -> bool:
        """Degradation recovery works for service-level errors."""
        return error.recoverable and self.degraded_method is not None and error.error_code in [
            ErrorCode.AZURE_OPENAI_ERROR,
            ErrorCode.EMBEDDING_GENERATION_ERROR,
            ErrorCode.CHAIN_EXECUTION_ERROR
        ]
    
    def recover(self, error: EnterpriseAIException, context: Dict[str, Any]) -> bool:
        """Attempt to recover by degrading service."""
        if not self.degraded_method:
            return False
        
        try:
            logger.warning(f"Service degradation activated for {error.error_code}")
            result = self.degraded_method(**context)
            logger.info("Degradation recovery successful")
            return True
        except Exception as e:
            logger.error(f"Degradation recovery failed: {e}")
            return False


class ErrorRecoveryManager:
    """Manages error recovery strategies."""
    
    def __init__(self):
        """Initialize error recovery manager."""
        self.strategies: list[RecoveryStrategy] = []
        self._default_strategies()
    
    def _default_strategies(self):
        """Set up default recovery strategies."""
        # Retry strategy for recoverable errors
        self.strategies.append(RetryRecoveryStrategy(max_retries=3))
    
    def add_strategy(self, strategy: RecoveryStrategy):
        """
        Add a recovery strategy.
        
        Args:
            strategy: Recovery strategy to add
        """
        self.strategies.append(strategy)
    
    def attempt_recovery(
        self,
        error: EnterpriseAIException,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Attempt to recover from an error using available strategies.
        
        Args:
            error: The error to recover from
            context: Additional context for recovery
            
        Returns:
            True if recovery was successful, False otherwise
        """
        if context is None:
            context = {}
        
        logger.info(f"Attempting recovery for error: {error.error_code}")
        
        for strategy in self.strategies:
            if strategy.can_recover(error):
                logger.info(f"Trying recovery strategy: {type(strategy).__name__}")
                
                if strategy.recover(error, context):
                    logger.info("Recovery successful")
                    return True
                else:
                    logger.warning(f"Recovery strategy {type(strategy).__name__} failed")
        
        logger.error("All recovery strategies failed")
        return False
    
    def create_recovery_context(self, **kwargs) -> Dict[str, Any]:
        """
        Create a recovery context with standard fields.
        
        Returns:
            Dictionary with standard recovery context fields
        """
        context = {
            "timestamp": time.time(),
            "retry_count": 0,
            **kwargs
        }
        return context