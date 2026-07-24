"""
Integration tests for RAG system.
Tests the complete RAG pipeline with real components.
"""

import pytest
from pathlib import Path
import shutil

from rag import ChromaDBStore, DocumentLoader, TextChunker, RAGRetriever


@pytest.fixture
def test_collection_name():
    """Test collection name."""
    return "test_integration_collection"


@pytest.fixture
def test_persist_directory():
    """Test persist directory."""
    dir_path = Path("data/chromadb_test")
    yield dir_path
    # Cleanup
    if dir_path.exists():
        shutil.rmtree(dir_path)


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    docs = [
        {
            "filename": "test1.md",
            "content": "This is a test document about network errors. Network timeouts are common.",
            "metadata": {"type": "network", "priority": "high"}
        },
        {
            "filename": "test2.txt",
            "content": "Database connection issues can occur. Check connection strings.",
            "metadata": {"type": "database", "priority": "medium"}
        }
    ]
    return docs


@pytest.mark.integration
class TestRAGIntegration:
    """Integration tests for complete RAG pipeline."""
    
    def test_document_to_retrieval_pipeline(
        self,
        test_collection_name,
        test_persist_directory,
        sample_documents
    ):
        """Test complete pipeline from documents to retrieval."""
        # Initialize components
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        vector_store = ChromaDBStore(
            collection_name=test_collection_name,
            persist_directory=str(test_persist_directory)
        )
        
        # Chunk documents
        chunks = chunker.chunk_documents(sample_documents)
        assert len(chunks) > 0
        
        # Index chunks
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [f"test_{i}" for i in range(len(chunks))]
        
        vector_store.add_documents(texts, metadatas, ids)
        
        # Verify documents are indexed
        info = vector_store.get_collection_info()
        assert info["count"] == len(chunks)
        
        # Query documents
        query = "network timeout issues"
        results = vector_store.query(query, n_results=2)
        
        assert "documents" in results
        assert results["documents"]
        assert len(results["documents"][0]) > 0
    
    def test_retriever_with_real_documents(
        self,
        test_collection_name,
        test_persist_directory
    ):
        """Test RAGRetriever with actual document loading."""
        retriever = RAGRetriever(
            collection_name=test_collection_name,
            persist_directory=str(test_persist_directory)
        )
        
        # Index sample documents
        num_chunks = retriever.index_documents(
            directory="data/sample_documents"
        )
        
        assert num_chunks > 0
        
        # Test retrieval
        query = "database connection timeout"
        results = retriever.retrieve(query, n_results=3)
        
        assert len(results) > 0
        assert all("content" in doc for doc in results)
        assert all("metadata" in doc for doc in results)
    
    def test_persistent_storage(
        self,
        test_collection_name,
        test_persist_directory
    ):
        """Test that documents persist across sessions."""
        # First session: add documents
        vector_store1 = ChromaDBStore(
            collection_name=test_collection_name,
            persist_directory=str(test_persist_directory)
        )
        
        vector_store1.add_documents(
            texts=["Test document"],
            metadatas=[{"source": "test"}],
            ids=["test_id"]
        )
        
        # Second session: retrieve documents
        vector_store2 = ChromaDBStore(
            collection_name=test_collection_name,
            persist_directory=str(test_persist_directory)
        )
        
        info = vector_store2.get_collection_info()
        assert info["count"] == 1