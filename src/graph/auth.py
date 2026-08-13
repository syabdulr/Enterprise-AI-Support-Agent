"""Authentication for Microsoft Graph API using Azure AD client credentials flow."""

import time
from typing import Any, Dict

import requests

from .models import GraphConfig


class GraphAuthenticator:
    """Handles OAuth2 client credentials authentication for Graph API."""

    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    SCOPE = "https://graph.microsoft.com/.default"

    def __init__(self, config: GraphConfig) -> None:
        self.config = config
        self._cached_token: str = ""
        self._token_expiry: float = 0

    def get_token(self) -> str:
        """Get an access token, using cache if still valid."""
        if self._cached_token and time.time() < self._token_expiry:
            return self._cached_token

        token_url = self.TOKEN_URL_TEMPLATE.format(tenant_id=self.config.tenant_id)

        data: Dict[str, Any] = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": self.SCOPE,
            "grant_type": "client_credentials",
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            raise Exception(
                f"Graph API authentication failed: {response.status_code} - "
                f"{response.json().get('error', 'unknown error')}"
            )

        token_data = response.json()
        self._cached_token = token_data["access_token"]
        self._token_expiry = time.time() + token_data.get("expires_in", 3600) - 300  # 5min buffer

        return self._cached_token

    def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header for Graph API requests."""
        return {"Authorization": f"Bearer {self.get_token()}"}
