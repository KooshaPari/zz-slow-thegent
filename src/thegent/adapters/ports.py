"""Ports module for hexagonal architecture adapters.

This module defines the port interfaces (Protocol definitions) for the
driven (outbound) and driving (inbound) adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

from typing_extensions import TypedDict

if TYPE_CHECKING:
    pass


T = TypeVar("T")


# =============================================================================
# Driven (Outbound) Ports
# =============================================================================


@runtime_checkable
class HTTPClientPort(Protocol):
    """Port interface for HTTP clients."""

    async def get(self, url: str, **kwargs: Any) -> Any: ...
    async def post(self, url: str, **kwargs: Any) -> Any: ...
    async def put(self, url: str, **kwargs: Any) -> Any: ...
    async def delete(self, url: str, **kwargs: Any) -> Any: ...
    async def patch(self, url: str, **kwargs: Any) -> Any: ...


@runtime_checkable
class CachePort(Protocol):
    """Port interface for cache backends."""

    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def clear(self) -> None: ...


@runtime_checkable
class MetricsPort(Protocol):
    """Port interface for metrics collection."""

    def increment(self, metric: str, **tags: Any) -> None: ...
    def gauge(self, metric: str, value: float, **tags: Any) -> None: ...
    def histogram(self, metric: str, value: float, **tags: Any) -> None: ...
    def timing(self, metric: str, duration_ms: float, **tags: Any) -> None: ...


@runtime_checkable
class AuthPort(Protocol):
    """Port interface for authentication."""

    async def authenticate(self, credentials: dict[str, Any]) -> dict[str, Any]: ...
    async def validate_token(self, token: str) -> bool: ...
    async def refresh_token(self, refresh_token: str) -> dict[str, Any]: ...


# =============================================================================
# Driving (Inbound) Ports
# =============================================================================


@runtime_checkable
class ProviderExecutionPort(Protocol):
    """Port interface for provider execution."""

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]: ...
    async def cancel(self, task_id: str) -> None: ...
    async def get_status(self, task_id: str) -> dict[str, Any]: ...


@runtime_checkable
class RoutingPort(Protocol):
    """Port interface for LLM routing."""

    async def route(self, request: dict[str, Any]) -> dict[str, Any]: ...
    def get_available_providers(self) -> list[str]: ...


@runtime_checkable
class GovernancePort(Protocol):
    """Port interface for governance checks."""

    async def check_policy(self, action: str, context: dict[str, Any]) -> bool: ...
    async def audit_action(self, action: str, context: dict[str, Any]) -> None: ...


# =============================================================================
# Plugin System
# =============================================================================


@runtime_checkable
class PluginInterface(Protocol):
    """Interface for plugin implementations."""

    @property
    def name(self) -> str: ...
    @property
    def version(self) -> str: ...

    def initialize(self, config: dict[str, Any]) -> None: ...
    def shutdown(self) -> None: ...


@dataclass
class LoadedPlugin:
    """Represents a loaded plugin instance."""

    name: str
    version: str
    instance: Any
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriverPlugin:
    """Plugin that implements a driver (provider) interface."""

    name: str
    driver_class: type
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouterPlugin:
    """Plugin that implements routing logic."""

    name: str
    router_class: type
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Registration System
# =============================================================================


class _RegistryDict(TypedDict):
    drivers: dict[str, DriverPlugin]
    routers: dict[str, RouterPlugin]
    cache_backends: dict[str, type]


@dataclass
class AdapterRegistry:
    """Registry for adapters, drivers, and routers."""

    drivers: dict[str, DriverPlugin] = field(default_factory=dict)
    routers: dict[str, RouterPlugin] = field(default_factory=dict)
    cache_backends: dict[str, type] = field(default_factory=dict)

    def register_driver(self, name: str, driver_class: type, **metadata: Any) -> None:
        """Register a driver plugin."""
        self.drivers[name] = DriverPlugin(
            name=name, driver_class=driver_class, metadata=metadata
        )

    def register_router(self, name: str, router_class: type, **metadata: Any) -> None:
        """Register a router plugin."""
        self.routers[name] = RouterPlugin(
            name=name, router_class=router_class, metadata=metadata
        )

    def register_cache_backend(self, name: str, backend_class: type) -> None:
        """Register a cache backend."""
        self.cache_backends[name] = backend_class

    def register_instance(self, name: str, adapter: Any) -> None:
        """Register an adapter by name (instance method)."""
        # Store adapters in drivers dict for backward compatibility
        self.drivers[name] = adapter

    @classmethod
    def register(cls, name: str, adapter: Any) -> None:
        """Class method to register an adapter (delegates to global registry)."""
        _runtime_registry.register_instance(name, adapter)

    def get_driver(self, name: str) -> DriverPlugin | None:
        """Get a registered driver by name."""
        return self.drivers.get(name)

    def get_router(self, name: str) -> RouterPlugin | None:
        """Get a registered router by name."""
        return self.routers.get(name)

    def list_drivers(self) -> list[str]:
        """List all registered driver names."""
        return list(self.drivers.keys())

    def list_routers(self) -> list[str]:
        """List all registered router names."""
        return list(self.routers.keys())


# Global runtime registry instance
_runtime_registry: AdapterRegistry = AdapterRegistry()


def register_driver(
    name: str,
    driver_class: type | None = None,
    **metadata: Any,
) -> Any:
    """Register a driver plugin.

    Supports two call styles:

    1. Decorator factory::

        @register_driver("name", version="1.0")
        class MyDriver: ...

    2. Direct registration::

        register_driver("name", MyDriver, version="1.0")

    Returns the registered class (direct form) or a decorator that
    registers the class when called (decorator form).
    """
    if driver_class is not None:
        _runtime_registry.register_driver(name, driver_class, **metadata)
        return driver_class

    def decorator(cls: type) -> type:
        _runtime_registry.register_driver(name, cls, **metadata)
        return cls

    return decorator


def register_router(
    name: str,
    router_class: type | None = None,
    **metadata: Any,
) -> Any:
    """Register a router plugin.

    Supports both the decorator factory form
    (``@register_router("name", region="eu")``) and the direct
    registration form (``register_router("name", MyRouter, region="eu")``).
    """
    if router_class is not None:
        _runtime_registry.register_router(name, router_class, **metadata)
        return router_class

    def decorator(cls: type) -> type:
        _runtime_registry.register_router(name, cls, **metadata)
        return cls

    return decorator


def register_cache(name: str, cache_class: type | None = None) -> Any:
    """Register a cache backend.

    Supports both the decorator factory form
    (``@register_cache("name")``) and the direct registration form
    (``register_cache("name", MyCache)``).
    """
    if cache_class is not None:
        _runtime_registry.register_cache_backend(name, cache_class)
        return cache_class

    def decorator(cls: type) -> type:
        _runtime_registry.register_cache_backend(name, cls)
        return cls

    return decorator


# =============================================================================
# Plugin Host Implementation
# =============================================================================


class PluginHost:
    """Host for managing plugin lifecycle."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInterface] = {}
        self._loaded: dict[str, LoadedPlugin] = {}

    def register_plugin(self, plugin: PluginInterface) -> None:
        """Register a plugin instance."""
        self._plugins[plugin.name] = plugin

    def load_plugin(self, name: str, config: dict[str, Any] | None = None) -> None:
        """Load a registered plugin with optional config."""
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not registered")
        plugin = self._plugins[name]
        plugin.initialize(config or {})
        self._loaded[name] = LoadedPlugin(
            name=plugin.name,
            version=plugin.version,
            instance=plugin,
            config=config or {},
        )

    def unload_plugin(self, name: str) -> None:
        """Unload a loaded plugin."""
        if name in self._loaded:
            plugin = self._loaded[name].instance
            plugin.shutdown()
            del self._loaded[name]

    def swap_plugin(self, name: str, new_plugin: PluginInterface) -> None:
        """Replace a loaded plugin with a new one."""
        if name in self._loaded:
            self.unload_plugin(name)
        self._plugins[name] = new_plugin
        self.load_plugin(name)

    def get_plugin(self, name: str) -> PluginInterface | None:
        """Get a loaded plugin instance by name."""
        loaded = self._loaded.get(name)
        return loaded.instance if loaded else None

    def list_plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def list_loaded(self) -> list[str]:
        """List all loaded plugin names."""
        return list(self._loaded.keys())


# Global plugin host instance
PLUGIN_HOST: PluginHost = PluginHost()


__all__ = [
    # Driven (Outbound) Ports
    "HTTPClientPort",
    "CachePort",
    "MetricsPort",
    "AuthPort",
    # Driving (Inbound) Ports
    "ProviderExecutionPort",
    "RoutingPort",
    "GovernancePort",
    # Registry
    "AdapterRegistry",
    # Plugin System
    "PluginInterface",
    "DriverPlugin",
    "RouterPlugin",
    "LoadedPlugin",
    "PluginHost",
    "PLUGIN_HOST",
    # Registration Decorators
    "register_driver",
    "register_router",
    "register_cache",
]
