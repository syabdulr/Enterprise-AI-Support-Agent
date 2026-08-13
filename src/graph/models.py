"""Models for Microsoft Graph connector integration."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class GraphResourceType(Enum):
    """Types of resources accessible via Microsoft Graph."""

    SHAREPOINT_LIST = "sharepoint_list"
    SHAREPOINT_FILE = "sharepoint_file"
    USER_PROFILE = "user_profile"
    GROUP = "group"
    TEAMS_MESSAGE = "teams_message"


@dataclass
class GraphConfig:
    """Configuration for Microsoft Graph API connection."""

    tenant_id: str
    client_id: str
    client_secret: str
    base_url: str = "https://graph.microsoft.com/v1.0"
    api_version: str = "v1.0"


@dataclass
class GraphResource:
    """A resource retrieved from Microsoft Graph."""

    resource_id: str
    resource_type: GraphResourceType
    title: str
    content: str
    web_url: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "title": self.title,
            "content": self.content,
            "web_url": self.web_url,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class PermissionInfo:
    """Permission information for a user accessing Graph resources."""

    user_id: str
    groups: List[str] = field(default_factory=list)
    site_permissions: Dict[str, str] = field(default_factory=dict)

    def has_access(self, source: str, required_access: str) -> bool:
        """Check if user has the required access level for a source."""
        access_levels = {"read": 1, "write": 2, "admin": 3}
        user_level = access_levels.get(self.site_permissions.get(source, ""), 0)
        required_level = access_levels.get(required_access, 1)
        return user_level >= required_level


@dataclass
class GraphSearchResult:
    """Result of a Graph API search query."""

    query: str
    resources: List[GraphResource] = field(default_factory=list)
    total_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "resources": [r.to_dict() for r in self.resources],
            "total_count": self.total_count,
        }
