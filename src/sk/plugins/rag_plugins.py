"""RAG plugin for Semantic Kernel.

Provides knowledge base search as kernel functions for grounding
agent responses in enterprise documentation.
"""

import json
from typing import Any, Dict, List, Optional

from semantic_kernel.functions import kernel_function


class RAGPlugin:
    """SK plugin for retrieval-augmented generation."""

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

    @kernel_function(description="Search the knowledge base for documents relevant to a query")
    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 3,
        filter_category: Optional[str] = None,
    ) -> str:
        """Search the knowledge base for relevant documents."""
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []

        for doc in self._KNOWLEDGE_BASE:
            if filter_category and doc["category"] != filter_category:
                continue

            query_words = set(query_lower.split())
            content_words = set(doc["content"].lower().split())
            overlap = query_words.intersection(content_words)
            score: float = float(len(overlap)) / max(len(query_words), 1)

            if score > 0 or not query_words:
                results.append(
                    {
                        "category": doc["category"],
                        "content": doc["content"],
                        "relevance_score": score,
                    }
                )

        results.sort(key=lambda x: float(x["relevance_score"]), reverse=True)
        results = results[:top_k]

        result: Dict[str, Any] = {
            "query": query,
            "results": results,
            "total_found": len(results),
        }
        return json.dumps(result)

    @kernel_function(description="Get relevant context from the knowledge base for an incident")
    def get_relevant_context(
        self,
        incident_description: str,
        max_chunks: int = 2,
    ) -> str:
        """Get relevant context for an incident from the knowledge base."""
        search_json = self.search_knowledge_base(
            query=incident_description,
            top_k=max_chunks,
        )
        search_result = json.loads(search_json)

        context_chunks = [r["content"] for r in search_result["results"]]

        result: Dict[str, Any] = {
            "incident": incident_description,
            "context": " ".join(context_chunks),
            "sources": [r["category"] for r in search_result["results"]],
            "chunk_count": len(context_chunks),
        }
        return json.dumps(result)
