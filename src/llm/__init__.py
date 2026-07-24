"""
LLM (Large Language Model) module.
Provides Azure OpenAI integration, LangChain chains, and prompt templates.
"""

from .azure_openai_client import AzureOpenAIClient
from .chain_builder import ChainBuilder
from .prompts import (
    TRIAGE_SYSTEM_PROMPT,
    DIAGNOSIS_SYSTEM_PROMPT,
    RESOLUTION_SYSTEM_PROMPT,
    ESCALATION_SYSTEM_PROMPT,
    HUMAN_REVIEW_PROMPT,
    TRIAGE_OUTPUT_SCHEMA,
    DIAGNOSIS_OUTPUT_SCHEMA
)

__all__ = [
    'AzureOpenAIClient',
    'ChainBuilder',
    'TRIAGE_SYSTEM_PROMPT',
    'DIAGNOSIS_SYSTEM_PROMPT',
    'RESOLUTION_SYSTEM_PROMPT',
    'ESCALATION_SYSTEM_PROMPT',
    'HUMAN_REVIEW_PROMPT',
    'TRIAGE_OUTPUT_SCHEMA',
    'DIAGNOSIS_OUTPUT_SCHEMA'
]