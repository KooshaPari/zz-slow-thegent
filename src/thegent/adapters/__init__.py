"""thegent.adapters - Hexagonal Architecture Adapters.

This package provides driving (primary) and driven (secondary) adapters
following the hexagonal/ports-and-adapters pattern.

Architecture:
- adapters.ports: Port interfaces (Protocol definitions)
- adapters.driven: Outbound adapters (HTTP, cache, metrics)
- adapters.driving: Inbound adapters (CLI, API handlers)
- adapters.plugin_host_adapter: WASM plugin host integration

All re-exports are lazy to avoid pulling heavy transitive dependencies
(wasm, httpx, cachetools, …) at package-import time.
"""

from __future__ import annotations

import importlib
from typing import Any

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Execution I/O adapters (AUDIT-N+5)
    "LeaseToken": ("thegent.adapters.execution_io", "LeaseToken"),
    "ProcessEnvironmentBuilder": (
        "thegent.adapters.execution_io",
        "ProcessEnvironmentBuilder",
    ),
    "ProcessSpawner": ("thegent.adapters.execution_io", "ProcessSpawner"),
    "ResourceLockManager": ("thegent.adapters.execution_io", "ResourceLockManager"),
    "ShadowWorkspaceManager": (
        "thegent.adapters.execution_io",
        "ShadowWorkspaceManager",
    ),
    "SpawnResult": ("thegent.adapters.execution_io", "SpawnResult"),
    # Plugin Host Adapter
    "LoadedPlugin": ("thegent.adapters.plugin_host_adapter", "LoadedPlugin"),
    "PluginHostAdapter": ("thegent.adapters.plugin_host_adapter", "PluginHostAdapter"),
    "PluginHostConfig": ("thegent.adapters.plugin_host_adapter", "PluginHostConfig"),
    "get_plugin_host": ("thegent.adapters.plugin_host_adapter", "get_plugin_host"),
    # Ports
    "AdapterRegistry": ("thegent.adapters.ports", "AdapterRegistry"),
    "AuthPort": ("thegent.adapters.ports", "AuthPort"),
    "CachePort": ("thegent.adapters.ports", "CachePort"),
    "DriverPlugin": ("thegent.adapters.ports", "DriverPlugin"),
    "GovernancePort": ("thegent.adapters.ports", "GovernancePort"),
    "HTTPClientPort": ("thegent.adapters.ports", "HTTPClientPort"),
    "MetricsPort": ("thegent.adapters.ports", "MetricsPort"),
    "PluginHost": ("thegent.adapters.ports", "PluginHost"),
    "PluginInterface": ("thegent.adapters.ports", "PluginInterface"),
    "ProviderExecutionPort": ("thegent.adapters.ports", "ProviderExecutionPort"),
    "RouterPlugin": ("thegent.adapters.ports", "RouterPlugin"),
    "RoutingPort": ("thegent.adapters.ports", "RoutingPort"),
    "register_cache": ("thegent.adapters.ports", "register_cache"),
    "register_driver": ("thegent.adapters.ports", "register_driver"),
    "register_router": ("thegent.adapters.ports", "register_router"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        mod = importlib.import_module(module_path)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    "HTTPClientPort",
    "CachePort",
    "MetricsPort",
    "AuthPort",
    "ProviderExecutionPort",
    "RoutingPort",
    "GovernancePort",
    "AdapterRegistry",
    "PluginInterface",
    "DriverPlugin",
    "RouterPlugin",
    "PluginHost",
    "PluginHostAdapter",
    "PluginHostConfig",
    "LoadedPlugin",
    "get_plugin_host",
    "LeaseToken",
    "ProcessEnvironmentBuilder",
    "ProcessSpawner",
    "ResourceLockManager",
    "ShadowWorkspaceManager",
    "SpawnResult",
    "register_driver",
    "register_router",
    "register_cache",
]
