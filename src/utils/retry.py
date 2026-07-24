"""
Retry logic with exponential backoff.
Provides configurable retry mechanisms for external service calls.
"""

import time
import random
import logging
from typing import Optional, Callable, Type, Any
from functools import wraps
from .exceptions import EnterpriseAIException

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: Optional[tuple[Type[Exception], ...]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            retry_on: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or (Exception,)
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter (0.5x to 1.5x of delay)
            delay = delay * random.uniform(0.5, 1.5)
        
        return delay


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], Any]] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        config: Retry configuration
        on_retry: Optional callback function called on each retry
            Receives (exception, attempt_number) as arguments
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # Last attempt failed, raise the exception
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts"
                        )
                        raise
                    
                    # Calculate delay
                    delay = config.calculate_delay(attempt)
                    
                    # Log retry
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{config.max_attempts}. "
                        f"Retrying in {delay:.2f} seconds. Error: {str(e)}"
                    )
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception if last_exception else Exception("Unknown error")
        
        return wrapper
    return decorator


class RetryManager:
    """Context manager for retry operations."""
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        on_retry: Optional[Callable[[Exception, int], Any]] = None
    ):
        """
        Initialize retry manager.
        
        Args:
            config: Retry configuration
            on_retry: Optional callback function
        """
        self.config = config or RetryConfig()
        self.on_retry = on_retry
        self.attempts = 0
    
    def __enter__(self):
        """Enter context manager."""
        self.attempts = 0
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type is not None and exc_val:
            # An exception occurred
            if not isinstance(exc_val, self.config.retry_on):
                # Not a retryable exception, re-raise
                return False
            
            if self.attempts >= self.config.max_attempts - 1:
                # Max attempts reached, re-raise
                logger.error(f"Retry manager failed after {self.config.max_attempts} attempts")
                return False
            
            # Calculate delay
            delay = self.config.calculate_delay(self.attempts)
            
            # Log retry
            logger.warning(
                f"Retry manager caught exception on attempt {self.attempts + 1}. "
                f"Retrying in {delay:.2f} seconds. Error: {str(exc_val)}"
            )
            
            # Call on_retry callback if provided
            if self.on_retry:
                self.on_retry(exc_val, self.attempts + 1)
            
            # Wait before retry
            time.sleep(delay)
            
            # Increment attempt counter
            self.attempts += 1
            
            # Suppress exception to allow retry
            return True
        
        # No exception occurred
        return False
    
    def attempt(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
        """
        with self:
            while self.attempts < self.config.max_attempts:
                try:
                    return func(*args, **kwargs)
                except self.config.retry_on as e:
                    if self.attempts >= self.config.max_attempts - 1:
                        raise
                    
                    # Calculate delay
                    delay = self.config.calculate_delay(self.attempts)
                    
                    # Log retry
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {self.attempts + 1}/{self.config.max_attempts}. "
                        f"Retrying in {delay:.2f} seconds. Error: {str(e)}"
                    )
                    
                    # Call on_retry callback if provided
                    if self.on_retry:
                        self.on_retry(e, self.attempts + 1)
                    
                    # Wait before retry
                    time.sleep(delay)
                    
                    # Increment attempt counter
                    self.attempts += 1
            
            # Should never reach here
            raise RuntimeError("Retry manager exceeded maximum attempts")