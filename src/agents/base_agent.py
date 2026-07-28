"""
Base Agent Class - Foundation for all specialized agents.
Updated with self-reflection capabilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

from ..utils.config import Config
from ..utils.logging import get_logger
from .self_reflection_mixin import SelfReflectionMixin


class BaseAgent(ABC, SelfReflectionMixin):
    """Base class for all AI agents in the system with self-reflection capabilities."""

    def __init__(self, name: str, version: str = "1.0.0", enable_reflection: bool = True):
        """
        Initialize base agent.

        Args:
            name: Agent name
            version: Agent version
            enable_reflection: Enable self-reflection capabilities (default: True)
        """
        # Initialize SelfReflectionMixin
        SelfReflectionMixin.__init__(self)

        self.name = name
        self.version = version
        self.logger = get_logger(f"agent.{name}")
        self.config = Config()

        # Agent state
        self._state: Dict[str, Any] = {}
        self._status: str = "idle"

        # Enable/disable reflection
        if enable_reflection:
            self.enable_reflection(True)
        else:
            self.enable_reflection(False)

        self.logger.info(
            f"Agent {self.name} v{self.version} initialized "
            f"(self-reflection: {'enabled' if enable_reflection else 'disabled'})"
        )

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

    def log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> None:
        """
        Log token usage for monitoring.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name used
        """
        total_tokens = input_tokens + output_tokens
        model = model or getattr(self.config, 'OPENAI_MODEL', 'unknown')

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

    async def process_with_reflection(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process input with automatic self-reflection.

        This method wraps the standard process() method with reflection:
        1. Process input
        2. Reflect on output
        3. Determine if escalation needed
        4. Return output with reflection metadata

        Args:
            input_data: Input data for processing

        Returns:
            Dictionary with:
            - 'result': Processing result
            - 'confidence': Confidence score (0-100)
            - 'reflection': Reflection metadata
            - 'should_escalate': Whether to escalate
        """
        # Validate input
        if not await self.validate_input(input_data):
            return self.get_error_response(ValueError("Invalid input data"))

        # Set status
        self.set_status("processing")

        try:
            # Process input
            output_data = await self.process(input_data)

            # Reflect on output
            reflection = await self.reflect_on_output(input_data, output_data)

            # Determine if escalation needed
            should_escalate = self.should_escalate(output_data)

            # Add reflection metadata to output
            output_data['confidence'] = reflection['confidence']
            output_data['reflection'] = reflection
            output_data['should_escalate'] = should_escalate

            # Set status
            self.set_status("idle")

            return output_data

        except Exception as e:
            self.logger.error(f"Error during processing: {e}", exc_info=True)
            self.set_status("error")
            return self.get_error_response(e)

    def get_required_fields(self) -> List[str]:
        """
        Get list of required fields for agent output.
        Override this in agent subclasses.

        Returns:
            List of required field names
        """
        return ['result']

    def __repr__(self) -> str:
        reflection_status = "enabled" if self._reflection_enabled else "disabled"
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"version={self.version}, "
            f"status={self._status}, "
            f"reflection={reflection_status}"
            f")"
        )