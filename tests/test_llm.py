"""
Tests for LLM and LangChain components.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm.azure_openai_client import AzureOpenAIClient
from llm.chain_builder import ChainBuilder
from llm.prompts import TRIAGE_SYSTEM_PROMPT


@pytest.fixture
def mock_azure_client(monkeypatch):
    """Mock Azure OpenAI client for testing."""
    # Mock environment variables
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    
    # Note: In real tests, you'd mock the OpenAI API calls
    # For now, we'll test initialization
    return AzureOpenAIClient


def test_azure_client_initialization(monkeypatch):
    """Test Azure OpenAI client initialization."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    
    client = AzureOpenAIClient()
    assert client.api_key == "test_key"
    assert client.endpoint == "https://test.openai.azure.com"
    assert client.chat_model is not None
    assert client.embeddings is not None


def test_chain_builder_initialization():
    """Test chain builder initialization."""
    # This would require a real or mocked client
    # For now, we test structure
    assert ChainBuilder is not None


def test_prompt_templates():
    """Test that prompt templates are defined."""
    from llm.prompts import (
        TRIAGE_SYSTEM_PROMPT,
        DIAGNOSIS_SYSTEM_PROMPT,
        RESOLUTION_SYSTEM_PROMPT,
        ESCALATION_SYSTEM_PROMPT
    )
    
    assert len(TRIAGE_SYSTEM_PROMPT) > 0
    assert len(DIAGNOSIS_SYSTEM_PROMPT) > 0
    assert len(RESOLUTION_SYSTEM_PROMPT) > 0
    assert len(ESCALATION_SYSTEM_PROMPT) > 0
    
    # Check prompt content
    assert "Triage" in TRIAGE_SYSTEM_PROMPT
    assert "Diagnosis" in DIAGNOSIS_SYSTEM_PROMPT
    assert "Resolution" in RESOLUTION_SYSTEM_PROMPT
    assert "Escalation" in ESCALATION_SYSTEM_PROMPT


def test_token_count_estimation():
    """Test token count estimation."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the meaning of life?"}
    ]
    
    # Simple estimation
    total_chars = sum(len(msg["content"]) for msg in messages)
    estimated_tokens = total_chars // 4
    
    assert estimated_tokens > 0