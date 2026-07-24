"""
RAG retriever for document similarity search.
Combines ChromaDB storage with embedding generation.
"""

from typing import List, Dict, Optional
import logging
from ..utils.exceptions import RAGException, ErrorCode, wrap_exception
from .chromadb_store import ChromaDBStore
from .embeddings import EmbeddingGenerator
from .document_loader import DocumentLoader
from .chunker import TextChunker

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieve relevant documents using RAG approach."""
    
    def __init__(
        self,
        collection_name: str = "incident_knowledge",
        persist_directory: Optional[str] = "data/chromadb",
        azure_api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None
    ):
        """Initialize RAG retriever."""
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize components
        self.vector_store = ChromaDBStore(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        
        self.embeddings = EmbeddingGenerator(
            api_key=azure_api_key,
            endpoint=azure_endpoint
        )
        
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
    
    def index_documents(
        self,
        documents: Optional[List[Dict]] = None,
        directory: str = "data/sample_documents"
    ) -> int:
        """Load, chunk, and index documents."""
        try:
            # Load documents
            if documents is None:
                self.loader.base_directory = directory
                documents = self.loader.load_directory()
            
            if not documents:
                logger.info("No documents found to index.")
                return 0
            
            # Chunk documents
            chunks = self.chunker.chunk_documents(documents)
            
            # Generate embeddings
            texts = [chunk["content"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            
            # Add to vector store
            self.vector_store.add_documents(texts, metadatas, ids)
            
            logger.info(f"Indexed {len(chunks)} chunks from {len(documents)} documents.")
            return len(chunks)
        
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            raise wrap_exception(e, ErrorCode.VECTOR_STORE_ERROR, "Failed to index documents", recoverable=True)
    
    def retrieve(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """Retrieve relevant documents for a query."""
        try:
            results = self.vector_store.query(query, n_results=n_results)
            
            retrieved_docs = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    retrieved_docs.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            return retrieved_docs
        
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            raise wrap_exception(e, ErrorCode.RETRIEVAL_ERROR, "Failed to retrieve documents", recoverable=True)
    
    def get_collection_info(self) -> Dict:
        """Get information about the indexed collection."""
        try:
            return self.vector_store.get_collection_info()
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            raise wrap_exception(e, ErrorCode.VECTOR_STORE_ERROR, "Failed to get collection info", recoverable=True)