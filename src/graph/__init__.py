"""Microsoft Graph connector for enterprise RAG integration.

Fetches SharePoint lists, files, and user profiles via Graph API,
converts them to RAG-ingestible format with permission-aware access.
"""

from .auth import GraphAuthenticator
from .client import GraphClient
from .connector import GraphConnector
from .models import GraphConfig, GraphResource, GraphResourceType, GraphSearchResult, PermissionInfo
from .permission_resolver import PermissionResolver

__all__ = [
    "GraphAuthenticator",
    "GraphClient",
    "GraphConfig",
    "GraphConnector",
    "GraphResource",
    "GraphResourceType",
    "GraphSearchResult",
    "PermissionInfo",
    "PermissionResolver",
]
