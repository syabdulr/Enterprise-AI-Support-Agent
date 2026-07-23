"""
Text chunker for RAG system.
Splits documents into chunks with overlap for better retrieval.
"""

from typing import List
import tiktoken


class TextChunker:
    """Split text into chunks with token-based overlap."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"  # GPT-4 encoding
    ):
        """Initialize text chunker."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
    
    def chunk_text(self, text: str, metadata: dict = None) -> List[Dict]:
        """Split text into chunks with overlap."""
        chunks = []
        
        # Encode text to tokens
        tokens = self.encoding.encode(text)
        
        # Calculate chunk size in tokens
        chunk_size_tokens = self.chunk_size
        overlap_tokens = self.chunk_overlap
        
        # Create chunks with overlap
        start = 0
        chunk_index = 0
        
        while start < len(tokens):
            end = min(start + chunk_size_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Create chunk metadata
            chunk_metadata = {
                "chunk_index": chunk_index,
                "chunk_size": len(chunk_tokens),
                "start_token": start,
                "end_token": end
            }
            
            # Add original metadata if provided
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_metadata
            })
            
            # Move start position with overlap
            start += (chunk_size_tokens - overlap_tokens)
            chunk_index += 1
        
        return chunks
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Chunk multiple documents."""
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_text(
                doc["content"],
                metadata={
                    "source": doc["source"],
                    "filename": doc["filename"],
                    "file_type": doc["file_type"]
                }
            )
            all_chunks.extend(chunks)
        
        return all_chunks