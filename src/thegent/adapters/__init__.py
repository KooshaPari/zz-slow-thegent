"""thegent.adapters - Hexagonal Architecture Adapters.

This package provides driving (primary) and driven (secondary) adapters
following the hexagonal/ports-and-adapters pattern.

Architecture:
- adapters.ports: Port interfaces (Protocol definitions)
- adapters.driven: Outbound adapters (HTTP, cache, metrics)
- adapters.driving: Inbound adapters (CLI, API handlers)
- adapters.plugin_host_adapter: WASM plugin host integration
"""

# Execution I/O adapters — decomposition seams for the run/bg orchestrators.
# See ``thegent.adapters.execution_io`` for the AUDIT-N+5 hand-off context.
from thegent.adapters.execution_io import (
    LeaseToken,
    ProcessEnvironmentBuilder,
    ProcessSpawner,
    ResourceLockManager,
    ShadowWorkspaceManager,
    SpawnResult,
)

# Plugin Host Adapter - WASM/Extism integration
from thegent.adapters.plugin_host_adapter import (
    LoadedPlugin,
    PluginHostAdapter,
    PluginHostConfig,
    get_plugin_host,
)
from thegent.adapters.ports import (
    # Unified Registry
    AdapterRegistry,
    AuthPort,
    CachePort,
    DriverPlugin,
    GovernancePort,
    # Driven (Outbound) Ports
    HTTPClientPort,
    MetricsPort,
    PluginHost,
    PluginInterface,
    # Driving (Inbound) Ports
    ProviderExecutionPort,
    RouterPlugin,
    RoutingPort,
    register_cache,
    # Registration Decorators
    register_driver,
    register_router,
)

__all__ = [
    # Ports
    "HTTPClientPort",
    "CachePort",
    "MetricsPort",
    "AuthPort",
    "ProviderExecutionPort",
    "RoutingPort",
    "GovernancePort",
    # Registry
    "AdapterRegistry",
    # Plugins
    "PluginInterface",
    "DriverPlugin",
    "RouterPlugin",
    "PluginHost",
    # Plugin Host
    "PluginHostAdapter",
    "PluginHostConfig",
    "LoadedPlugin",
    "get_plugin_host",
    # Execution I/O seams (AUDIT-N+5)
    "LeaseToken",
    "ProcessEnvironmentBuilder",
    "ProcessSpawner",
    "ResourceLockManager",
    "ShadowWorkspaceManager",
    "SpawnResult",
    # Decorators
    "register_driver",
    "register_router",
    "register_cache",
]
