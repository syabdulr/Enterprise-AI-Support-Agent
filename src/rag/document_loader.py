"""
Document loader for RAG system.
Supports loading documents from .md, .txt, and .pdf files.
"""

from typing import List, Dict, Optional
from pathlib import Path
import os


class DocumentLoader:
    """Load and preprocess documents for RAG system."""
    
    def __init__(self, base_directory: str = "data/sample_documents"):
        """Initialize document loader."""
        self.base_directory = Path(base_directory)
    
    def load_directory(self) -> List[Dict]:
        """Load all supported documents from directory."""
        documents = []
        
        if not self.base_directory.exists():
            return documents
        
        for file_path in self.base_directory.rglob("*"):
            if file_path.is_file() and self._is_supported_file(file_path):
                try:
                    doc = self.load_file(file_path)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        return documents
    
    def load_file(self, file_path: Path) -> Optional[Dict]:
        """Load a single document file."""
        content = None
        
        if file_path.suffix == '.md':
            content = self._load_markdown(file_path)
        elif file_path.suffix == '.txt':
            content = self._load_text(file_path)
        elif file_path.suffix == '.pdf':
            content = self._load_pdf(file_path)
        
        if content:
            return {
                "content": content,
                "source": str(file_path),
                "filename": file_path.name,
                "file_type": file_path.suffix
            }
        
        return None
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file type is supported."""
        return file_path.suffix in ['.md', '.txt', '.pdf']
    
    def _load_markdown(self, file_path: Path) -> str:
        """Load markdown file content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_text(self, file_path: Path) -> str:
        """Load text file content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_pdf(self, file_path: Path) -> str:
        """Load PDF file content."""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise Exception("pypdf not installed. Install with: pip install pypdf")
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")