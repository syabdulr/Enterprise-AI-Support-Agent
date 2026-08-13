"""Semantic Kernel manager using the real semantic-kernel SDK.

Creates a Kernel with AzureChatCompletion service, registers plugins,
and provides async function invocation.
"""

import logging
import os
from typing import Any, List, Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

logger = logging.getLogger(__name__)


class SemanticKernelManager:
    """Manages a real Semantic Kernel instance with Azure OpenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
    ) -> None:
        self.kernel = Kernel()

        self._api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY", "test-key")
        self._endpoint = endpoint or os.getenv(
            "AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com"
        )
        self._deployment_name = deployment_name or os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4"
        )
        self._api_version = api_version

        self._chat_service = AzureChatCompletion(
            service_id="azure_openai_chat",
            api_key=self._api_key,
            deployment_name=self._deployment_name,
            endpoint=self._endpoint,
            api_version=self._api_version,
        )
        self.kernel.add_service(self._chat_service)
        self._is_initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    def register_plugin(self, plugin: Any, name: str) -> None:
        """Register a plugin with the real kernel."""
        self.kernel.add_plugin(plugin, plugin_name=name)

    def unregister_plugin(self, name: str) -> None:
        """Remove a plugin from the kernel."""
        if name in self.kernel.plugins:
            del self.kernel.plugins[name]

    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self.kernel.plugins.keys())

    def list_functions(self) -> List[str]:
        """List all registered kernel functions as plugin.function."""
        result: List[str] = []
        for plugin_name, plugin in self.kernel.plugins.items():
            for func_name in plugin.functions:
                result.append(f"{plugin_name}.{func_name}")
        return result

    async def invoke_function(
        self,
        plugin_name: str,
        function_name: str,
        **kwargs: Any,
    ) -> Any:
        """Invoke a kernel function by plugin and function name."""
        return await self.kernel.invoke(
            function_name=function_name,
            plugin_name=plugin_name,
            **kwargs,
        )
