"""
Base Agent Class - Foundation for all specialized agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

from ..utils.config import Config
from ..utils.logging import get_logger


class BaseAgent(ABC):
    """Base class for all AI agents in the system."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            version: Agent version
        """
        self.name = name
        self.version = version
        self.logger = get_logger(f"agent.{name}")
        self.config = Config()
        
        # Agent state
        self._state: Dict[str, Any] = {}
        self._status: str = "idle"
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Processing results as dictionary
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        pass
    
    def get_status(self) -> str:
        """Get current agent status."""
        return self._status
    
    def set_status(self, status: str) -> None:
        """Set agent status."""
        self._status = status
        self.logger.info(f"Agent {self.name} status changed to: {status}")
    
    def get_state(self, key: Optional[str] = None) -> Any:
        """Get agent state."""
        if key:
            return self._state.get(key)
        return self._state.copy()
    
    def set_state(self, key: str, value: Any) -> None:
        """Set agent state value."""
        self._state[key] = value
        self.logger.debug(f"Agent {self.name} state updated: {key} = {value}")
    
    def clear_state(self) -> None:
        """Clear agent state."""
        self._state.clear()
        self.logger.debug(f"Agent {self.name} state cleared")
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not input_data:
            self.logger.warning("Empty input data received")
            return False
        
        if not isinstance(input_data, dict):
            self.logger.error(f"Input data must be dict, got {type(input_data)}")
            return False
        
        return True
    
    def log_token_usage(self, 
                       input_tokens: int, 
                       output_tokens: int,
                       model: str = None) -> None:
        """
        Log token usage for monitoring.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name used
        """
        total_tokens = input_tokens + output_tokens
        model = model or self.config.OPENAI_MODEL
        
        self.logger.info(
            f"Token usage - Agent: {self.name}, Model: {model}, "
            f"Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}"
        )
    
    def get_error_response(self, error: Exception) -> Dict[str, Any]:
        """
        Generate standardized error response.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Error response dictionary
        """
        return {
            "error": True,
            "agent": self.name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "suggestion": "Please check logs for more details"
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, version={self.version}, status={self._status})"