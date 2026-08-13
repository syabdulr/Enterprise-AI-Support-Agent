"""Graph API client for querying SharePoint, user profiles, and search."""

from typing import Any, Dict, List, Optional, cast

import requests

from .auth import GraphAuthenticator
from .models import GraphConfig


class GraphClient:
    """Client for Microsoft Graph API operations."""

    def __init__(self, config: GraphConfig) -> None:
        self.config = config
        self.authenticator = GraphAuthenticator(config)

    def _get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated GET request to Graph API."""
        url = f"{self.config.base_url}{endpoint}"
        headers = self.authenticator.get_auth_header()
        response = requests.get(url, headers=headers, params=params or {})

        if response.status_code != 200:
            raise Exception(
                f"Graph API request failed: {response.status_code} - {response.text[:200]}"
            )

        return cast(Dict[str, Any], response.json())

    def get_sharepoint_lists(self, site_id: str) -> List[Dict[str, Any]]:
        """Get all SharePoint lists for a site."""
        endpoint = f"/sites/{site_id}/lists"
        result = self._get(endpoint)
        return cast(List[Dict[str, Any]], result.get("value", []))

    def get_sharepoint_list_items(
        self, site_id: str, list_id: str, top: int = 50
    ) -> List[Dict[str, Any]]:
        """Get items from a SharePoint list."""
        endpoint = f"/sites/{site_id}/lists/{list_id}/items"
        params = {"$top": top, "$expand": "fields($select=Title,Status,Content)"}
        result = self._get(endpoint, params)
        return cast(List[Dict[str, Any]], result.get("value", []))

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get a user's profile information."""
        endpoint = f"/users/{user_id}"
        return self._get(endpoint)

    def search_sharepoint(
        self, site_id: str, query: str, top: int = 10
    ) -> List[Dict[str, Any]]:
        """Search SharePoint content using the Graph search API."""
        endpoint = "/search/query"
        url = f"{self.config.base_url}{endpoint}"
        headers = self.authenticator.get_auth_header()
        headers["Content-Type"] = "application/json"

        body: Dict[str, Any] = {
            "requests": [
                {
                    "entityTypes": ["listItem"],
                    "query": {"queryString": query},
                    "from": 0,
                    "size": top,
                    "fields": ["Title", "name", "webUrl", "content"],
                }
            ]
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code != 200:
            raise Exception(
                f"Graph search failed: {response.status_code} - {response.text[:200]}"
            )

        data = response.json()
        value = data.get("value", [{}])
        if not value:
            return []
        hits_containers = value[0].get("hitsContainers", [{}])
        if not hits_containers:
            return []
        return cast(List[Dict[str, Any]], hits_containers[0].get("hits", []))

    def get_drive_files(
        self, site_id: str, drive_id: str, top: int = 50
    ) -> List[Dict[str, Any]]:
        """Get files from a SharePoint document library."""
        endpoint = f"/sites/{site_id}/drives/{drive_id}/root/children"
        params = {"$top": top}
        result = self._get(endpoint, params)
        return cast(List[Dict[str, Any]], result.get("value", []))

    def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """Get group memberships for a user."""
        endpoint = f"/users/{user_id}/memberOf"
        result = self._get(endpoint)
        return cast(List[Dict[str, Any]], result.get("value", []))
