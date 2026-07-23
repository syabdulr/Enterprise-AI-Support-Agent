"""
ChromaDB vector store wrapper for RAG system.
Handles persistent storage and retrieval of document embeddings.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import os


class ChromaDBStore:
    """Wrapper for ChromaDB vector database operations."""
    
    def __init__(
        self,
        collection_name: str = "incident_knowledge",
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """Initialize ChromaDB client and collection."""
        self.collection_name = collection_name
        
        if persist_directory:
            # Persistent local storage
            self.client = chromadb.PersistentClient(path=persist_directory)
        elif host and port:
            # Remote ChromaDB instance
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        else:
            # In-memory storage (for testing)
            self.client = chromadb.Client()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """Add documents to the collection."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """Query the collection for similar documents."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        return results
    
    def delete(self, ids: List[str]) -> None:
        """Delete documents by IDs."""
        self.collection.delete(ids=ids)
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection."""
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata
        }