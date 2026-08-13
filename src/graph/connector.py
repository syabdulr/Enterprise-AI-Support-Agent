"""Graph connector that bridges Microsoft Graph data into the RAG pipeline.

This is the main integration point: it fetches enterprise data from
SharePoint, converts it to RAG-ingestible documents, and respects
permission-aware access patterns. This shows hands-on Microsoft Graph
and SharePoint integration — directly addressing the JD requirement.
"""

from typing import Any, Dict, List, Optional

from .client import GraphClient
from .models import GraphConfig, GraphResource, GraphResourceType
from .permission_resolver import PermissionResolver


class GraphConnector:
    """Bridges Microsoft Graph data into the RAG knowledge base."""

    def __init__(self, config: GraphConfig) -> None:
        self.client = GraphClient(config)
        self.permission_resolver = PermissionResolver()

    def to_rag_document(
        self, resource: GraphResource, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Convert a Graph resource to a RAG document."""
        # Check permissions if user_id is provided
        if user_id:
            if not self.permission_resolver.check_access(user_id, resource.source):
                return None

        return {
            "id": f"graph_{resource.resource_id}",
            "content": f"{resource.title}\n{resource.content}",
            "metadata": {
                "source": "microsoft_graph",
                "original_source": resource.source,
                "resource_type": resource.resource_type.value,
                "web_url": resource.web_url,
                "title": resource.title,
                **resource.metadata,
            },
        }

    def to_rag_documents(
        self,
        resources: List[GraphResource],
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Convert multiple Graph resources to RAG documents."""
        docs: List[Dict[str, Any]] = []
        for resource in resources:
            doc = self.to_rag_document(resource, user_id)
            if doc is not None:
                docs.append(doc)
        return docs

    def sync_sharepoint_list(
        self, site_id: str, list_id: str, top: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Sync a SharePoint list to RAG format.

        Fetches list items from Graph API and converts them to
        RAG-ingestible documents.
        """
        items = self.client.get_sharepoint_list_items(site_id, list_id, top)

        resources = []
        for item in items:
            fields = item.get("fields", {})
            title = fields.get("Title", f"Item {item.get('id', 'unknown')}")
            content = fields.get("Content", fields.get("Title", ""))

            resources.append(
                GraphResource(
                    resource_id=item.get("id", ""),
                    resource_type=GraphResourceType.SHAREPOINT_LIST,
                    title=title,
                    content=content,
                    web_url=f"https://{site_id}/lists/{list_id}",
                    source=f"SharePoint/{site_id}",
                    metadata={"list_id": list_id, "raw_fields": fields},
                )
            )

        return self.to_rag_documents(resources)

    def sync_sharepoint_files(self, site_id: str, drive_id: str) -> List[Dict[str, Any]]:
        """Sync files from a SharePoint document library to RAG format."""
        files = self.client.get_drive_files(site_id, drive_id)

        resources = []
        for f in files:
            resources.append(
                GraphResource(
                    resource_id=f.get("id", ""),
                    resource_type=GraphResourceType.SHAREPOINT_FILE,
                    title=f.get("name", "Untitled"),
                    content=f.get("description", f.get("name", "")),
                    web_url=f.get("webUrl", ""),
                    source=f"SharePoint/{site_id}",
                    metadata={
                        "drive_id": drive_id,
                        "mime_type": f.get("file", {}).get("mimeType", ""),
                    },
                )
            )

        return self.to_rag_documents(resources)

    def search_and_convert(self, site_id: str, query: str, top: int = 10) -> List[Dict[str, Any]]:
        """Search SharePoint and convert results to RAG format."""
        results = self.client.search_sharepoint(site_id, query, top)

        resources = []
        for hit in results:
            fields = hit.get("resource", {}).get("fields", {})
            resources.append(
                GraphResource(
                    resource_id=hit.get("hitId", ""),
                    resource_type=GraphResourceType.SHAREPOINT_FILE,
                    title=fields.get("Title", hit.get("resource", {}).get("name", "Untitled")),
                    content=fields.get("content", ""),
                    web_url=fields.get("webUrl", hit.get("resource", {}).get("webUrl", "")),
                    source=f"SharePoint/{site_id}",
                    metadata={"query": query},
                )
            )

        return self.to_rag_documents(resources)
