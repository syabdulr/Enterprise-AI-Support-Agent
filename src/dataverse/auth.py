"""Authentication for Dataverse Web API using Azure AD client credentials flow."""

import time
from typing import Any, Dict

import requests

from .models import DataverseConfig


class DataverseAuthenticator:
    """Handles OAuth2 client credentials authentication for Dataverse."""

    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    def __init__(self, config: DataverseConfig) -> None:
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
            "scope": f"{self.config.org_url}/.default",
            "grant_type": "client_credentials",
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            raise Exception(
                f"Dataverse authentication failed: {response.status_code} - "
                f"{response.json().get('error', 'unknown error')}"
            )

        token_data = response.json()
        self._cached_token = token_data["access_token"]
        self._token_expiry = time.time() + token_data.get("expires_in", 3600) - 300  # 5min buffer

        return self._cached_token

    def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header for Dataverse Web API requests."""
        return {"Authorization": f"Bearer {self.get_token()}"}
