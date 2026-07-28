"""
Self-Reflection Mixin - Enables agents to critique and improve their own decisions.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime


class SelfReflectionMixin:
    """
    Mixin class that adds self-reflection capabilities to agents.

    Agents using this mixin can:
    - Score their own confidence (0-100)
    - Critique their own decisions
    - Identify mistakes and improvements
    - Auto-escalate for low-confidence decisions
    - Log reflections for learning
    """

    def __init__(self, *args, **kwargs):
        """Initialize self-reflection capabilities."""
        super().__init__(*args, **kwargs)

        # Reflection state
        self._reflection_enabled: bool = True
        self._confidence_threshold: int = 70  # Escalate if confidence < 70
        self._reflection_history: List[Dict[str, Any]] = []

        # Get logger from parent class
        if hasattr(self, 'logger'):
            self.logger = self.logger
        else:
            self.logger = logging.getLogger(f"agent.{self.__class__.__name__}")

    def enable_reflection(self, enabled: bool = True) -> None:
        """
        Enable or disable self-reflection.

        Args:
            enabled: True to enable, False to disable
        """
        self._reflection_enabled = enabled
        self.logger.info(f"Self-reflection {'enabled' if enabled else 'disabled'}")

    def set_confidence_threshold(self, threshold: int) -> None:
        """
        Set confidence threshold for auto-escalation.

        Args:
            threshold: Confidence score (0-100). Below this, escalate.
        """
        if threshold < 0 or threshold > 100:
            raise ValueError("Confidence threshold must be between 0 and 100")

        self._confidence_threshold = threshold
        self.logger.info(f"Confidence threshold set to: {threshold}%")

    def calculate_confidence(self, output_data: Dict[str, Any]) -> int:
        """
        Calculate confidence score for agent output (0-100).

        This is a base implementation that can be overridden by specific agents.
        Default logic:
        - High confidence: Complete output, no errors, clear reasoning
        - Medium confidence: Partial output, minor errors
        - Low confidence: Incomplete output, errors, unclear reasoning

        Args:
            output_data: Output data from agent processing

        Returns:
            Confidence score (0-100)
        """
        score = 100

        # Check for errors
        if output_data.get('error'):
            score -= 30

        # Check for completeness
        if not output_data.get('result'):
            score -= 20

        # Check for warnings
        if output_data.get('warnings'):
            warning_count = len(output_data['warnings'])
            score -= min(warning_count * 5, 20)

        # Check for missing fields
        required_fields = self.get_required_fields()
        missing_fields = [
            field for field in required_fields
            if field not in output_data or not output_data[field]
        ]

        if missing_fields:
            score -= len(missing_fields) * 10

        # Ensure score is within bounds
        return max(0, min(100, score))

    def get_required_fields(self) -> List[str]:
        """
        Get list of required fields for agent output.
        Override this in agent subclasses.

        Returns:
            List of required field names
        """
        return ['result']

    async def reflect_on_output(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reflect on agent output and identify improvements.

        This method uses the LLM to generate a self-critique.

        Args:
            input_data: Original input data
            output_data: Agent output data

        Returns:
            Reflection results including critique and improvements
        """
        if not self._reflection_enabled:
            return {'reflection': 'disabled'}

        # Calculate confidence
        confidence = self.calculate_confidence(output_data)

        # Log reflection
        self.logger.info(f"Starting self-reflection (confidence: {confidence}%)")

        # Store reflection
        reflection = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.name,
            'input': input_data,
            'output': output_data,
            'confidence': confidence,
            'critique': None,  # Will be filled by LLM
            'improvements': [],  # Will be filled by LLM
            'action': None  # 'continue', 'escalate', 'retry'
        }

        # Determine action based on confidence
        if confidence >= self._confidence_threshold:
            reflection['action'] = 'continue'
        else:
            reflection['action'] = 'escalate'

        # Store reflection in history
        self._reflection_history.append(reflection)

        self.logger.info(
            f"Self-reflection complete - Confidence: {confidence}%, "
            f"Action: {reflection['action']}"
        )

        return reflection

    def should_escalate(self, output_data: Dict[str, Any]) -> bool:
        """
        Determine if agent should escalate based on confidence.

        Args:
            output_data: Agent output data

        Returns:
            True if should escalate, False otherwise
        """
        if not self._reflection_enabled:
            return False

        confidence = self.calculate_confidence(output_data)
        return confidence < self._confidence_threshold

    def get_reflection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get reflection history.

        Args:
            limit: Maximum number of reflections to return

        Returns:
            List of reflection dictionaries
        """
        return self._reflection_history[-limit:]

    def get_reflection_metrics(self) -> Dict[str, Any]:
        """
        Get aggregate metrics from reflection history.

        Returns:
            Dictionary with metrics (avg confidence, escalation rate, etc.)
        """
        if not self._reflection_history:
            return {
                'total_reflections': 0,
                'average_confidence': 0,
                'escalation_rate': 0,
                'total_escalations': 0
            }

        total = len(self._reflection_history)
        total_confidence = sum(r['confidence'] for r in self._reflection_history)
        escalations = sum(1 for r in self._reflection_history if r['action'] == 'escalate')

        return {
            'total_reflections': total,
            'average_confidence': total_confidence / total,
            'escalation_rate': escalations / total * 100,
            'total_escalations': escalations,
            'confidence_distribution': {
                'high': sum(1 for r in self._reflection_history if r['confidence'] >= 80),
                'medium': sum(1 for r in self._reflection_history if 60 <= r['confidence'] < 80),
                'low': sum(1 for r in self._reflection_history if r['confidence'] < 60)
            }
        }

    def clear_reflection_history(self) -> None:
        """Clear reflection history."""
        self._reflection_history.clear()
        self.logger.info("Reflection history cleared")

    def get_reflection_report(self) -> str:
        """
        Generate a human-readable reflection report.

        Returns:
            Formatted report string
        """
        metrics = self.get_reflection_metrics()

        report = f"""
=== SELF-REFLECTION REPORT FOR {self.name.upper()} ===

Total Reflections: {metrics['total_reflections']}
Average Confidence: {metrics['average_confidence']:.1f}%
Escalation Rate: {metrics['escalation_rate']:.1f}%
Total Escalations: {metrics['total_escalations']}

Confidence Distribution:
  High (80%+): {metrics['confidence_distribution']['high']}
  Medium (60-79%): {metrics['confidence_distribution']['medium']}
  Low (<60%): {metrics['confidence_distribution']['low']}

Recent Reflections (Last 5):
"""
        recent_reflections = self.get_reflection_history(limit=5)
        for i, reflection in enumerate(recent_reflections, 1):
            report += f"""
{i}. {reflection['timestamp']}
   Confidence: {reflection['confidence']}%
   Action: {reflection['action']}
"""

        return report