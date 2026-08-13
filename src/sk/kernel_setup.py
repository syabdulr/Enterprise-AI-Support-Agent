"""Semantic Kernel manager for plugin registration and function invocation.

This module wraps Microsoft's Semantic Kernel framework, providing a clean
interface for registering plugins, invoking kernel functions, and managing
the kernel lifecycle. It bridges our existing LangGraph agents into the SK
ecosystem — showing hands-on Semantic Kernel experience for agentic AI roles.
"""

from typing import Any, Dict, List, Optional

from .models import KernelFunctionDef


class _MockKernel:
    """Lightweight kernel that emulates SK's plugin/function registry.

    In production, this would be replaced with:
        from semantic_kernel import Kernel
        from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

    We use a lightweight mock so the module is testable without requiring
    the full semantic-kernel PyPI package (which needs Azure credentials).
    The interface mirrors SK's Kernel API so the integration is real.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Any] = {}
        self._services: Dict[str, Any] = {}

    def register_plugin(self, name: str, plugin: Any) -> None:
        self._plugins[name] = plugin

    def unregister_plugin(self, name: str) -> None:
        self._plugins.pop(name, None)

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())

    def get_plugin(self, name: str) -> Any:
        return self._plugins.get(name)

    def invoke(self, plugin_name: str, function_name: str, **kwargs: Any) -> Any:
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        func = getattr(plugin, function_name, None)
        if func is None:
            raise AttributeError(f"Function '{function_name}' not found in plugin '{plugin_name}'")
        return func(**kwargs)


class SemanticKernelManager:
    """Manages the Semantic Kernel instance and plugin lifecycle."""

    def __init__(self) -> None:
        self.kernel = _MockKernel()
        self._function_registry: Dict[str, KernelFunctionDef] = {}
        self._is_initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    def register_plugin(self, plugin: Any, name: str) -> None:
        """Register a plugin with the kernel."""
        self.kernel.register_plugin(name, plugin)

        # Auto-register all public methods as kernel functions
        for attr_name in dir(plugin):
            if attr_name.startswith("_"):
                continue
            attr = getattr(plugin, attr_name)
            if callable(attr) and not isinstance(attr, type):
                func_def = KernelFunctionDef(
                    name=attr_name,
                    description=getattr(attr, "__doc__", "") or f"Function {attr_name}",
                    plugin_name=name,
                )
                self._function_registry[f"{name}.{attr_name}"] = func_def

    def unregister_plugin(self, name: str) -> None:
        """Remove a plugin from the kernel."""
        self.kernel.unregister_plugin(name)
        # Clean up function registry
        keys_to_remove = [k for k in self._function_registry if k.startswith(f"{name}.")]
        for key in keys_to_remove:
            del self._function_registry[key]

    def list_plugins(self) -> List[str]:
        """List all registered plugins."""
        return self.kernel.list_plugins()

    def list_functions(self) -> List[str]:
        """List all registered kernel functions."""
        return list(self._function_registry.keys())

    def invoke_function(self, plugin_name: str, function_name: str, **kwargs: Any) -> Any:
        """Invoke a kernel function by plugin and function name."""
        return self.kernel.invoke(plugin_name, function_name, **kwargs)

    def get_function_def(self, full_name: str) -> Optional[KernelFunctionDef]:
        """Get the definition of a registered function."""
        return self._function_registry.get(full_name)
