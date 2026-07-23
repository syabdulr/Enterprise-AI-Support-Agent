"""
Embedding generation using Azure OpenAI.
Converts text chunks to vector embeddings for similarity search.
"""

from typing import List, Optional
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class EmbeddingGenerator:
    """Generate embeddings using Azure OpenAI."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        deployment_name: str = "text-embedding-ada-002"
    ):
        """Initialize Azure OpenAI client for embeddings."""
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version
        self.deployment_name = deployment_name
        
        if not self.api_key or not self.endpoint:
            raise ValueError(
                "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set "
                "in environment variables or passed to constructor"
            )
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version
        )
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        response = self.client.embeddings.create(
            input=texts,
            model=self.deployment_name
        )
        
        return [item.embedding for item in response.data]
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = self.generate_embeddings([text])
        return embeddings[0]