"""Permission resolver for Graph resources.

Implements permission-aware data access patterns, ensuring users only
see Graph resources (SharePoint files, lists) they have access to.
This is critical for enterprise RAG — agents must not surface documents
from sites the user doesn't have permission to view.
"""

from typing import Dict, List, Optional

from .models import GraphResource, PermissionInfo


class PermissionResolver:
    """Resolves permissions for Graph resources per user."""

    def __init__(self) -> None:
        self._user_permissions: Dict[str, PermissionInfo] = {}

    def set_user_permissions(self, user_id: str, permissions: PermissionInfo) -> None:
        """Set permission info for a user."""
        self._user_permissions[user_id] = permissions

    def get_user_permissions(self, user_id: str) -> Optional[PermissionInfo]:
        """Get permission info for a user."""
        return self._user_permissions.get(user_id)

    def filter_resources(
        self,
        resources: List[GraphResource],
        user_id: str,
        required_access: str = "read",
    ) -> List[GraphResource]:
        """
        Filter resources based on user permissions.

        Only returns resources from sources the user has access to.
        """
        perm = self._user_permissions.get(user_id)
        if perm is None:
            return []

        return [r for r in resources if perm.has_access(r.source, required_access)]

    def check_access(self, user_id: str, source: str, required_access: str = "read") -> bool:
        """Check if a user has access to a specific source."""
        perm = self._user_permissions.get(user_id)
        if perm is None:
            return False
        return perm.has_access(source, required_access)
