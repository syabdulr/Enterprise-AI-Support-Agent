"""
Tests for self-reflection capabilities.
"""

import pytest
from src.agents.base_agent import BaseAgent


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, name="test_agent", **kwargs):
        super().__init__(name=name, **kwargs)

    async def process(self, input_data):
        """Process input (mock)."""
        return {"result": "success"}

    def get_capabilities(self):
        """Get capabilities (mock)."""
        return ["test_capability"]


def test_self_reflection_enabled():
    """Test that self-reflection is enabled by default."""
    agent = MockAgent(name="test_agent")

    assert agent._reflection_enabled is True
    assert agent._confidence_threshold == 70


def test_confidence_calculation_high():
    """Test confidence calculation for high-confidence output."""
    agent = MockAgent(name="test_agent")

    # High confidence: complete result, no errors
    output = {"result": "success", "data": "test data"}
    confidence = agent.calculate_confidence(output)

    assert confidence == 100


def test_confidence_calculation_low():
    """Test confidence calculation for low-confidence output."""
    agent = MockAgent(name="test_agent")

    # Low confidence: errors, warnings, missing fields
    output = {
        "error": True,
        "error_message": "Something went wrong",
        "warnings": ["warning1", "warning2", "warning3"]
    }
    confidence = agent.calculate_confidence(output)

    # Expected: 100 - 30 (error) - 20 (no result) - 15 (3 warnings) - 10 (missing 'result' field) = 25
    assert confidence == 25


def test_should_escalate_low_confidence():
    """Test that low confidence triggers escalation."""
    agent = MockAgent(name="test_agent")
    agent.set_confidence_threshold(70)

    # Low confidence output
    output = {"result": None, "error": True}
    should_escalate = agent.should_escalate(output)

    assert should_escalate is True


def test_should_escalate_high_confidence():
    """Test that high confidence does not trigger escalation."""
    agent = MockAgent(name="test_agent")
    agent.set_confidence_threshold(70)

    # High confidence output
    output = {"result": "success", "data": "test"}
    should_escalate = agent.should_escalate(output)

    assert should_escalate is False


def test_reflection_history():
    """Test that reflections are tracked in history."""
    agent = MockAgent(name="test_agent")

    # Simulate reflection
    import asyncio
    input_data = {"test": "input"}
    output_data = {"result": "success"}

    asyncio.run(agent.reflect_on_output(input_data, output_data))

    # Check history
    history = agent.get_reflection_history()
    assert len(history) == 1
    assert history[0]['agent'] == "test_agent"
    assert 'confidence' in history[0]
    assert 'action' in history[0]


def test_reflection_metrics():
    """Test reflection metrics calculation."""
    agent = MockAgent(name="test_agent")

    # Simulate multiple reflections
    import asyncio

    for i in range(5):
        output = {"result": "success"}
        asyncio.run(agent.reflect_on_output({"test": i}, output))

    metrics = agent.get_reflection_metrics()

    assert metrics['total_reflections'] == 5
    assert metrics['average_confidence'] > 0
    assert 'escalation_rate' in metrics
    assert 'confidence_distribution' in metrics


def test_confidence_threshold_validation():
    """Test that confidence threshold is validated."""
    agent = MockAgent(name="test_agent")

    # Valid threshold
    agent.set_confidence_threshold(80)
    assert agent._confidence_threshold == 80

    # Invalid threshold (too low)
    with pytest.raises(ValueError):
        agent.set_confidence_threshold(-10)

    # Invalid threshold (too high)
    with pytest.raises(ValueError):
        agent.set_confidence_threshold(150)


def test_reflection_report():
    """Test that reflection report is generated correctly."""
    agent = MockAgent(name="test_agent")

    # Simulate reflections
    import asyncio

    for i in range(3):
        output = {"result": "success"}
        asyncio.run(agent.reflect_on_output({"test": i}, output))

    report = agent.get_reflection_report()

    assert "SELF-REFLECTION REPORT" in report
    assert "TEST_AGENT" in report
    assert "Total Reflections: 3" in report
    assert "Average Confidence:" in report


def test_enable_disable_reflection():
    """Test enabling and disabling reflection."""
    agent = MockAgent(name="test_agent")

    # Disable reflection
    agent.enable_reflection(False)
    assert agent._reflection_enabled is False

    # Enable reflection
    agent.enable_reflection(True)
    assert agent._reflection_enabled is True


def test_process_with_reflection():
    """Test processing with automatic reflection."""
    agent = MockAgent(name="test_agent")

    import asyncio
    input_data = {"test": "input"}

    output = asyncio.run(agent.process_with_reflection(input_data))

    # Check that reflection metadata is included
    assert 'confidence' in output
    assert 'reflection' in output
    assert 'should_escalate' in output
    assert 'result' in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])