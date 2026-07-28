"""
LLM-Powered Self-Critique for agents.
Uses the LLM to generate detailed critiques of agent outputs.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime


class SelfCritiqueEngine:
    """
    LLM-powered self-critique engine.

    Generates detailed critiques of agent outputs using the LLM.
    Parses critique into actionable insights for improvement.
    """

    def __init__(self, llm_client):
        """
        Initialize self-critique engine.

        Args:
            llm_client: LLM client (e.g., AzureOpenAIClient)
        """
        self.llm_client = llm_client
        self.logger = logging.getLogger("self_critique")

    async def generate_critique(
        self,
        agent_name: str,
        agent_capabilities: List[str],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence_score: int
    ) -> Dict[str, Any]:
        """
        Generate detailed critique of agent output.

        Args:
            agent_name: Name of the agent
            agent_capabilities: List of agent capabilities
            input_data: Original input data
            output_data: Agent output data
            confidence_score: Confidence score (0-100)

        Returns:
            Critique results with structured feedback
        """
        # Generate critique prompt
        prompt = self._generate_critique_prompt(
            agent_name,
            agent_capabilities,
            input_data,
            output_data,
            confidence_score
        )

        try:
            # Call LLM
            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Low temperature for consistent critiques
                max_tokens=1000
            )

            # Parse critique
            critique = self._parse_critique(response)

            # Add metadata
            critique['timestamp'] = datetime.now().isoformat()
            critique['agent'] = agent_name
            critique['confidence'] = confidence_score
            critique['input'] = input_data
            critique['output'] = output_data

            self.logger.info(
                f"Generated critique for {agent_name} - "
                f"Strengths: {len(critique.get('strengths', []))}, "
                f"Weaknesses: {len(critique.get('weaknesses', []))}, "
                f"Improvements: {len(critique.get('improvements', []))}"
            )

            return critique

        except Exception as e:
            self.logger.error(f"Failed to generate critique: {e}", exc_info=True)

            # Return fallback critique
            return {
                'timestamp': datetime.now().isoformat(),
                'agent': agent_name,
                'confidence': confidence_score,
                'strengths': ['No critique generated (LLM error)'],
                'weaknesses': ['Unable to analyze'],
                'improvements': [],
                'should_escalate': confidence_score < 70,
                'escalation_reason': f"Low confidence ({confidence_score}%)",
                'error': str(e)
            }

    def _generate_critique_prompt(
        self,
        agent_name: str,
        agent_capabilities: List[str],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence_score: int
    ) -> str:
        """
        Generate critique prompt for LLM.

        Args:
            agent_name: Name of the agent
            agent_capabilities: List of agent capabilities
            input_data: Original input data
            output_data: Agent output data
            confidence_score: Confidence score (0-100)

        Returns:
            Critique prompt string
        """
        prompt = f"""You are a {agent_name} agent reflecting on your own performance.

AGENT CAPABILITIES:
{', '.join(agent_capabilities)}

INPUT:
{self._format_dict(input_data)}

OUTPUT:
{self._format_dict(output_data)}

CONFIDENCE SCORE: {confidence_score}%

Please analyze your output and answer these questions:

1. What did I do well? (2-3 specific strengths)
2. What could I improve? (2-3 specific weaknesses)
3. Did I miss any important information? (yes/no and explain)
4. Are there any errors or inaccuracies? (yes/no and explain)
5. What specific improvements should I make? (3-5 actionable items)
6. Should I escalate to human review? (yes/no)
7. If escalation is recommended, why? (2-3 sentences)

Format your response as JSON:
```json
{{
  "strengths": [
    "Identified the root cause correctly",
    "Provided clear resolution steps",
    "Escalated appropriately for critical issues"
  ],
  "weaknesses": [
    "Missed some edge cases",
    "Could have provided more context",
    "Resolution steps could be more detailed"
  ],
  "missing_information": "Could have gathered more details about the system configuration",
  "has_errors": false,
  "error_details": null,
  "improvements": [
    "Add system configuration checks",
    "Provide more context in resolution steps",
    "Consider edge cases before suggesting resolution"
  ],
  "should_escalate": false,
  "escalation_reason": "Confidence is sufficient, human review not required"
}}
```

IMPORTANT: Return ONLY the JSON, no other text.
"""
        return prompt

    def _parse_critique(self, critique_text: str) -> Dict[str, Any]:
        """
        Parse critique text from LLM response.

        Args:
            critique_text: Raw text from LLM

        Returns:
            Parsed critique dictionary
        """
        try:
            # Extract JSON from text
            json_start = critique_text.find('{')
            json_end = critique_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in critique")

            json_str = critique_text[json_start:json_end]
            critique = json.loads(json_str)

            # Validate required fields
            required_fields = [
                'strengths', 'weaknesses', 'improvements', 'should_escalate'
            ]

            for field in required_fields:
                if field not in critique:
                    critique[field] = [] if field != 'should_escalate' else False

            return critique

        except Exception as e:
            self.logger.warning(f"Failed to parse critique JSON: {e}")

            # Return fallback structure
            return {
                'strengths': [],
                'weaknesses': ['Unable to parse critique'],
                'missing_information': None,
                'has_errors': True,
                'error_details': str(e),
                'improvements': [],
                'should_escalate': True,
                'escalation_reason': 'Unable to parse critique, escalating to be safe'
            }

    def _format_dict(self, data: Dict[str, Any], indent: int = 2) -> str:
        """
        Format dictionary as readable string.

        Args:
            data: Dictionary to format
            indent: Indentation level

        Returns:
            Formatted string
        """
        return json.dumps(data, indent=indent, default=str)

    async def generate_cross_agent_critique(
        self,
        reviewer_agent_name: str,
        reviewee_agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate cross-agent critique (one agent critiques another).

        Args:
            reviewer_agent_name: Name of the reviewing agent
            reviewee_agent_name: Name of the agent being reviewed
            input_data: Original input data
            output_data: Agent output data to critique

        Returns:
            Cross-agent critique results
        """
        prompt = f"""You are {reviewer_agent_name} critiquing {reviewee_agent_name}'s output.

INPUT:
{self._format_dict(input_data)}

OUTPUT BY {reviewee_agent_name}:
{self._format_dict(output_data)}

Please provide constructive feedback:

1. What did {reviewee_agent_name} do well? (2-3 strengths)
2. What could {reviewee_agent_name} improve? (2-3 weaknesses)
3. Are there any errors or missed information? (yes/no and explain)
4. What specific improvements should {reviewee_agent_name} make? (3-5 actionable items)
5. Should this output be escalated to human review? (yes/no)
6. If escalation is recommended, why? (2-3 sentences)

Format your response as JSON:
```json
{{
  "strengths": [
    "Good analysis of root cause",
    "Clear resolution steps"
  ],
  "weaknesses": [
    "Missed some edge cases",
    "Could have provided more context"
  ],
  "has_errors": false,
  "error_details": null,
  "improvements": [
    "Consider edge cases",
    "Provide more context"
  ],
  "should_escalate": false,
  "escalation_reason": "Output is sufficient, no escalation needed"
}}
```

IMPORTANT: Return ONLY the JSON, no other text.
"""

        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000
            )

            critique = self._parse_critique(response)
            critique['timestamp'] = datetime.now().isoformat()
            critique['reviewer_agent'] = reviewer_agent_name
            critique['reviewee_agent'] = reviewee_agent_name
            critique['cross_agent'] = True

            return critique

        except Exception as e:
            self.logger.error(f"Failed to generate cross-agent critique: {e}", exc_info=True)

            return {
                'timestamp': datetime.now().isoformat(),
                'reviewer_agent': reviewer_agent_name,
                'reviewee_agent': reviewee_agent_name,
                'cross_agent': True,
                'strengths': [],
                'weaknesses': ['Unable to generate cross-agent critique'],
                'has_errors': True,
                'error_details': str(e),
                'improvements': [],
                'should_escalate': True,
                'escalation_reason': 'Unable to critique, escalating to be safe'
            }