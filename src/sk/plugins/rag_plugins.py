"""RAG plugin for Semantic Kernel integration.

Wraps our existing ChromaDB-based RAG pipeline as SK kernel functions,
demonstrating how SK agents can ground their responses in enterprise
knowledge bases.
"""

from typing import Any, Dict, List, Optional


class RAGPlugin:
    """SK plugin for retrieval-augmented generation."""

    # Simulated knowledge base (in production, this calls ChromaDB)
    _KNOWLEDGE_BASE: List[Dict[str, str]] = [
        {
            "category": "infrastructure",
            "content": "To restart a service: sudo systemctl restart <service-name>. "
            "Verify with: sudo systemctl status <service-name>.",
        },
        {
            "category": "database",
            "content": "Database connection pool exhaustion: increase max_connections "
            "or reduce idle timeout. Monitor with: SHOW STATUS LIKE 'Threads_connected'.",
        },
        {
            "category": "network",
            "content": "DNS issues: check /etc/resolv.conf, run nslookup, verify "
            "firewall rules on port 53.",
        },
        {
            "category": "security",
            "content": "SSL certificate renewal: use certbot or Azure Key Vault. "
            "Rotate before expiry to avoid service disruption.",
        },
        {
            "category": "infrastructure",
            "content": "Disk space cleanup: rotate logs with logrotate, clear /tmp, "
            "archive old data. Monitor with: df -h.",
        },
        {
            "category": "application",
            "content": "API 500 errors: check application logs, verify dependencies "
            "are healthy, review recent deployments for regressions.",
        },
    ]

    def __init__(self) -> None:
        self.name = "RAGPlugin"

    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 3,
        filter_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search the knowledge base for relevant documents.

        Implements the memory pattern: SK agents can retrieve context
        from enterprise knowledge bases.
        """
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []

        for doc in self._KNOWLEDGE_BASE:
            if filter_category and doc["category"] != filter_category:
                continue

            # Simple keyword-based relevance scoring
            query_words = set(query_lower.split())
            content_words = set(doc["content"].lower().split())
            overlap = query_words.intersection(content_words)
            score: float = len(overlap) / max(len(query_words), 1)

            if score > 0 or not query_words:
                results.append(
                    {
                        "category": doc["category"],
                        "content": doc["content"],
                        "relevance_score": score,
                    }
                )

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = results[:top_k]

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
        }

    def get_relevant_context(
        self,
        incident_description: str,
        max_chunks: int = 2,
    ) -> Dict[str, Any]:
        """
        Get relevant context for an incident from the knowledge base.

        Used by SK agents to ground their diagnosis and resolution
        in enterprise documentation.
        """
        search_result = self.search_knowledge_base(
            query=incident_description,
            top_k=max_chunks,
        )

        # Combine top chunks into a context string
        context_chunks = [r["content"] for r in search_result["results"]]

        return {
            "incident": incident_description,
            "context": " ".join(context_chunks),
            "sources": [r["category"] for r in search_result["results"]],
            "chunk_count": len(context_chunks),
        }
