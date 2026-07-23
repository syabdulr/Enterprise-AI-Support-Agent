"""
Tests for RAG system components.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag.document_loader import DocumentLoader
from rag.chunker import TextChunker


def test_document_loader(tmp_path):
    """Test document loading."""
    # Create test files
    test_dir = tmp_path / "documents"
    test_dir.mkdir()
    
    (test_dir / "test.txt").write_text("Test content")
    (test_dir / "test.md").write_text("# Test\n\nContent")
    
    loader = DocumentLoader(str(test_dir))
    docs = loader.load_directory()
    
    assert len(docs) == 2
    assert docs[0]["filename"] == "test.txt"
    assert docs[1]["filename"] == "test.md"


def test_text_chunker():
    """Test text chunking."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    text = " ".join(["word"] * 200)
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 1
    assert all("content" in chunk for chunk in chunks)
    assert chunks[0]["metadata"]["chunk_index"] == 0


def test_chunker_with_metadata():
    """Test chunking with metadata preservation."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    text = " ".join(["word"] * 200)
    chunks = chunker.chunk_text(
        text,
        metadata={"source": "test.txt", "filename": "test.txt"}
    )
    
    assert chunks[0]["metadata"]["source"] == "test.txt"
    assert chunks[0]["metadata"]["filename"] == "test.txt"