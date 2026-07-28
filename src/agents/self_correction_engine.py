"""
Automated Self-Correction for agents.
Implements retry logic with learning from reflection history.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime


class SelfCorrectionEngine:
    """
    Automated self-correction engine.

    Retries failed actions, learns from reflection history,
    and improves confidence on retry.
    """

    def __init__(self):
        """Initialize self-correction engine."""
        self.logger = logging.getLogger("self_correction")
        self.correction_history: List[Dict[str, Any]] = []

    async def self_correct(
        self,
        agent,
        input_data: Dict[str, Any],
        original_output: Dict[str, Any],
        feedback: Optional[str] = None,
        critique: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Attempt to self-correct based on feedback or critique.

        Args:
            agent: Agent instance
            input_data: Original input data
            original_output: Original output data
            feedback: Optional feedback from human or other agent
            critique: Optional critique from self-critique engine
            max_retries: Maximum number of retry attempts

        Returns:
            Corrected output data
        """
        self.logger.info(f"Starting self-correction (max {max_retries} retries)")

        current_output = original_output
        correction_attempts = 0
        corrections_applied = []

        for attempt in range(max_retries):
            correction_attempts = attempt + 1

            self.logger.info(
                f"Correction attempt {attempt + 1}/{max_retries}"
            )

            # Analyze current output
            improvements = self._identify_improvements(
                input_data,
                current_output,
                critique
            )

            if not improvements:
                self.logger.info("No improvements identified, stopping correction")
                break

            # Apply improvements
            corrected_output = await self._apply_improvements(
                agent,
                input_data,
                current_output,
                improvements
            )

            # Check if correction improved output
            if self._is_improved(original_output, corrected_output):
                self.logger.info("Correction improved output")
                current_output = corrected_output
                corrections_applied.extend(improvements)

                # Check if output is now acceptable
                if self._is_acceptable(corrected_output):
                    self.logger.info("Output is now acceptable")
                    break
            else:
                self.logger.warning("Correction did not improve output")

        # Record correction history
        correction_record = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent.name,
            'input': input_data,
            'original_output': original_output,
            'corrected_output': current_output,
            'correction_attempts': correction_attempts,
            'corrections_applied': corrections_applied,
            'feedback': feedback,
            'critique': critique
        }

        self.correction_history.append(correction_record)

        # Add metadata to output
        current_output['self_corrected'] = True
        current_output['correction_attempts'] = correction_attempts
        current_output['corrections_applied'] = corrections_applied

        self.logger.info(
            f"Self-correction complete - Attempts: {correction_attempts}, "
            f"Improvements: {len(corrections_applied)}"
        )

        return current_output

    def _identify_improvements(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        critique: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Identify potential improvements based on critique or output analysis.

        Args:
            input_data: Original input data
            output_data: Current output data
            critique: Optional critique from self-critique engine

        Returns:
            List of improvement suggestions
        """
        improvements = []

        # Extract improvements from critique
        if critique and critique.get('improvements'):
            improvements.extend(critique['improvements'])

        # Analyze output for common issues
        if not output_data.get('result'):
            improvements.append("Add result field")

        if output_data.get('error'):
            improvements.append("Fix error")

        if output_data.get('warnings'):
            improvements.append("Address warnings")

        # Check for missing context
        if not output_data.get('reasoning'):
            improvements.append("Add reasoning")

        # Check for incomplete information
        if not output_data.get('details'):
            improvements.append("Add details")

        return improvements

    async def _apply_improvements(
        self,
        agent,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        improvements: List[str]
    ) -> Dict[str, Any]:
        """
        Apply improvements to output.

        Args:
            agent: Agent instance
            input_data: Original input data
            output_data: Current output data
            improvements: List of improvement suggestions

        Returns:
            Improved output data
        """
        improved_output = output_data.copy()

        # Re-process with improved prompt
        improved_prompt = self._generate_improved_prompt(
            input_data,
            output_data,
            improvements
        )

        # Create new input with improvements
        improved_input = input_data.copy()
        improved_input['_improvements'] = improvements
        improved_input['_original_output'] = output_data

        # Re-process with agent
        try:
            new_output = await agent.process(improved_input)

            # Merge improvements with original output
            improved_output.update(new_output)
            improved_output['improvements_applied'] = improvements

        except Exception as e:
            self.logger.error(f"Failed to apply improvements: {e}", exc_info=True)
            improved_output['improvement_error'] = str(e)

        return improved_output

    def _generate_improved_prompt(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        improvements: List[str]
    ) -> str:
        """
        Generate improved prompt incorporating improvements.

        Args:
            input_data: Original input data
            output_data: Current output data
            improvements: List of improvement suggestions

        Returns:
            Improved prompt string
        """
        prompt = f"""IMPROVED REQUEST

ORIGINAL INPUT:
{input_data}

ORIGINAL OUTPUT:
{output_data}

IMPROVEMENTS TO APPLY:
{', '.join(improvements)}

Please re-process this input, applying the improvements above.
Focus on:
- Addressing all identified issues
- Providing complete and accurate results
- Including reasoning and context
"""

        return prompt

    def _is_improved(
        self,
        original_output: Dict[str, Any],
        corrected_output: Dict[str, Any]
    ) -> bool:
        """
        Check if corrected output is improved over original.

        Args:
            original_output: Original output data
            corrected_output: Corrected output data

        Returns:
            True if improved, False otherwise
        """
        # Check if errors were fixed
        original_has_error = original_output.get('error', False)
        corrected_has_error = corrected_output.get('error', False)

        if original_has_error and not corrected_has_error:
            return True

        # Check if result was added
        original_has_result = bool(original_output.get('result'))
        corrected_has_result = bool(corrected_output.get('result'))

        if not original_has_result and corrected_has_result:
            return True

        # Check if warnings were reduced
        original_warnings = len(original_output.get('warnings', []))
        corrected_warnings = len(corrected_output.get('warnings', []))

        if corrected_warnings < original_warnings:
            return True

        # Check if confidence improved
        original_confidence = original_output.get('confidence', 0)
        corrected_confidence = corrected_output.get('confidence', 0)

        if corrected_confidence > original_confidence:
            return True

        return False

    def _is_acceptable(self, output_data: Dict[str, Any]) -> bool:
        """
        Check if output is acceptable (no critical issues).

        Args:
            output_data: Output data to check

        Returns:
            True if acceptable, False otherwise
        """
        # Check for critical errors
        if output_data.get('error'):
            return False

        # Check for required fields
        required_fields = ['result']
        for field in required_fields:
            if field not in output_data or not output_data[field]:
                return False

        # Check for confidence threshold
        confidence = output_data.get('confidence', 0)
        if confidence < 70:
            return False

        return True

    def get_correction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get correction history.

        Args:
            limit: Maximum number of corrections to return

        Returns:
            List of correction records
        """
        return self.correction_history[-limit:]

    def get_correction_metrics(self) -> Dict[str, Any]:
        """
        Get aggregate metrics from correction history.

        Returns:
            Dictionary with metrics
        """
        if not self.correction_history:
            return {
                'total_corrections': 0,
                'success_rate': 0,
                'average_attempts': 0,
                'total_improvements': 0
            }

        total = len(self.correction_history)
        successful_corrections = sum(
            1 for c in self.correction_history
            if c['corrected_output'].get('confidence', 0) >= 70
        )

        total_attempts = sum(c['correction_attempts'] for c in self.correction_history)
        total_improvements = sum(
            len(c['corrections_applied']) for c in self.correction_history
        )

        return {
            'total_corrections': total,
            'success_rate': (successful_corrections / total) * 100,
            'average_attempts': total_attempts / total,
            'total_improvements': total_improvements
        }

    def clear_correction_history(self) -> None:
        """Clear correction history."""
        self.correction_history.clear()
        self.logger.info("Correction history cleared")

    async def learn_from_corrections(self) -> Dict[str, Any]:
        """
        Learn from correction history to identify patterns.

        Returns:
            Dictionary with learned patterns
        """
        if not self.correction_history:
            return {'patterns': []}

        # Identify common improvements
        improvement_counts = {}

        for correction in self.correction_history:
            for improvement in correction['corrections_applied']:
                improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1

        # Sort by frequency
        sorted_improvements = sorted(
            improvement_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Identify common failures
        failure_patterns = []

        for correction in self.correction_history:
            if correction['corrected_output'].get('error'):
                failure_patterns.append({
                    'agent': correction['agent'],
                    'error': correction['corrected_output'].get('error_message'),
                    'timestamp': correction['timestamp']
                })

        return {
            'common_improvements': sorted_improvements[:10],
            'failure_patterns': failure_patterns[-5:],  # Last 5 failures
            'total_corrections_analyzed': len(self.correction_history)
        }