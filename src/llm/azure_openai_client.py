"""
Azure OpenAI client wrapper with LangChain integration.
Handles LLM instantiation, chat models, and embeddings.
"""

from typing import Optional, List, Dict, Any
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from openai import AzureOpenAI
import os
import logging
from dotenv import load_dotenv
from ..utils.exceptions import LLMException, ErrorCode, wrap_exception

load_dotenv()
logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Wrapper for Azure OpenAI with LangChain integration."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        chat_deployment: str = "gpt-4",
        embedding_deployment: str = "text-embedding-ada-002"
    ):
        """Initialize Azure OpenAI client."""
        try:
            self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
            self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            self.api_version = api_version
            self.chat_deployment = chat_deployment
            self.embedding_deployment = embedding_deployment
            
            if not self.api_key or not self.endpoint:
                raise LLMException(
                    "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set",
                    ErrorCode.MISSING_CONFIG,
                    recoverable=False
                )
            
            # Initialize LangChain chat model
            self.chat_model = AzureChatOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
                deployment_name=chat_deployment,
                temperature=0.7
            )
            
            # Initialize embeddings (LangChain wrapper)
            self.embeddings = AzureOpenAIEmbeddings(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
                deployment=embedding_deployment
            )
            
            # Initialize raw OpenAI client for advanced operations
            self.client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version
            )
            
            logger.info("Azure OpenAI client initialized successfully")
        
        except LLMException:
            raise
        except Exception as e:
            raise wrap_exception(e, ErrorCode.AZURE_OPENAI_ERROR, "Failed to initialize Azure OpenAI client", recoverable=False)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Send chat messages and get response."""
        try:
            # Convert message dicts to LangChain message objects
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
            
            # Invoke chat model
            if temperature is not None or max_tokens is not None:
                self.chat_model.temperature = temperature or self.chat_model.temperature
                response = self.chat_model.invoke(
                    langchain_messages,
                    max_tokens=max_tokens
                )
            else:
                response = self.chat_model.invoke(langchain_messages)
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise wrap_exception(e, ErrorCode.AZURE_OPENAI_ERROR, "Failed to generate chat response", recoverable=True)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using LangChain wrapper."""
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise wrap_exception(e, ErrorCode.EMBEDDING_GENERATION_ERROR, "Failed to generate embedding", recoverable=True)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise wrap_exception(e, ErrorCode.EMBEDDING_GENERATION_ERROR, "Failed to generate embeddings", recoverable=True)
    
    def get_token_count(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for messages."""
        # Simple estimation (4 chars ≈ 1 token)
        total_chars = sum(len(msg["content"]) for msg in messages)
        return total_chars // 4
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]]
    ) -> Any:
        """Stream chat response for real-time output."""
        try:
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
            
            return self.chat_model.stream(langchain_messages)
        
        except Exception as e:
            logger.error(f"Error in stream_chat: {e}")
            raise wrap_exception(e, ErrorCode.STREAM_ERROR, "Failed to stream chat response", recoverable=True)