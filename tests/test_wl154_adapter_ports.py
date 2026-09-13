"""WL154 — L15 API surface hardening: adapter ports surface (FR-AGT-002, FR-CTR-006).

Pins the canonical public surface of ``thegent.adapters.ports`` so any
accidental change to the hexagonal port surface is caught before release:

- All ``Protocol`` port interfaces are ``@runtime_checkable`` so
  duck-typed implementations can be validated via ``isinstance`` (this
  is the project-wide convention used in ``core.ports``,
  ``govern.vetter``, ``governance.config_provider``, etc.).
- The ``AdapterRegistry`` / ``PluginHost`` lifecycle is pinned end to
  end (register / lookup / list / unregister / swap / unload).
- The module-level decorators (``register_driver``, ``register_router``,
  ``register_cache``) are pinned to operate against the canonical
  global ``_runtime_registry``.
- The canonical ``__all__`` surface is pinned so private names like
  ``_runtime_registry`` stop leaking through the public API.
"""

from __future__ import annotations

import dataclasses
from typing import ClassVar

import pytest

from thegent.adapters import ports as ports_module
from thegent.adapters.ports import (
    PLUGIN_HOST,
    AdapterRegistry,
    AuthPort,
    CachePort,
    DriverPlugin,
    GovernancePort,
    HTTPClientPort,
    LoadedPlugin,
    MetricsPort,
    PluginHost,
    PluginInterface,
    ProviderExecutionPort,
    RouterPlugin,
    RoutingPort,
    register_cache,
    register_driver,
    register_router,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_fake_plugin(
    name: str = "p",
    version: str = "0.1.0",
    init_log: list[str] | None = None,
    shutdown_log: list[str] | None = None,
) -> PluginInterface:
    """Build a concrete PluginInterface for testing the host lifecycle.

    Captures the function arguments into the inner class via default
    arguments on the methods — this is the safest pattern because
    reading outer-scope names from inside class bodies can be brittle
    under future-annotations + pytest parametrize.
    """
    captured_init = init_log if init_log is not None else []
    captured_shutdown = shutdown_log if shutdown_log is not None else []

    class FakePlugin:
        def __init__(self) -> None:
            self._name = name
            self._version = version
            self._init_log = captured_init
            self._shutdown_log = captured_shutdown

        @property
        def name(self) -> str:
            return self._name

        @property
        def version(self) -> str:
            return self._version

        def initialize(self, config: dict[str, object]) -> None:
            self._init_log.append(f"init:{self._name}")

        def shutdown(self) -> None:
            self._shutdown_log.append(f"shutdown:{self._name}")

    return FakePlugin()


# ---------------------------------------------------------------------------
# Public surface pinning (FR-CTR-006)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAdapterPortsPublicSurface:
    """Pin the canonical public surface of ``thegent.adapters.ports``."""

    def test_canonical_all_is_exact(self) -> None:
        # Every public name must appear in __all__; every __all__ entry
        # must exist on the module. This catches both accidental leaks
        # (private names in __all__) and missing re-exports.
        public_names = {
            "HTTPClientPort",
            "CachePort",
            "MetricsPort",
            "AuthPort",
            "ProviderExecutionPort",
            "RoutingPort",
            "GovernancePort",
            "PluginInterface",
            "LoadedPlugin",
            "DriverPlugin",
            "RouterPlugin",
            "AdapterRegistry",
            "PluginHost",
            "PLUGIN_HOST",
            "register_driver",
            "register_router",
            "register_cache",
        }
        assert set(ports_module.__all__) == public_names

    def test_private_runtime_registry_not_in_all(self) -> None:
        # `_runtime_registry` is a private singleton — it must NOT be
        # part of the public __all__ contract. It is still importable
        # (Python permits this) but it is no longer advertised.
        assert "_runtime_registry" not in ports_module.__all__

    def test_all_names_importable_from_module(self) -> None:
        for name in ports_module.__all__:
            assert hasattr(ports_module, name), f"{name} missing on module"

    def test_ports_module_re_exported_from_adapters_package(self) -> None:
        from thegent import adapters

        # The top-level adapters package must re-export at least the
        # canonical port names so users can import from a stable surface.
        for name in (
            "HTTPClientPort",
            "CachePort",
            "MetricsPort",
            "AuthPort",
            "AdapterRegistry",
            "PluginInterface",
            "PluginHost",
            "PluginHostAdapter",
            "PluginHostConfig",
        ):
            assert name in adapters.__all__, f"{name} missing from adapters.__all__"


# ---------------------------------------------------------------------------
# Protocol runtime_checkability (FR-AGT-002)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProtocolRuntimeCheckable:
    """All Protocol ports must be @runtime_checkable for isinstance checks.

    This is the project-wide convention (see ``core.ports``,
    ``govern.vetter``, ``governance.config_provider``). Without it,
    ``isinstance(obj, HTTPClientPort)`` raises ``TypeError`` and
    duck-typed adapter implementations cannot be validated.
    """

    @pytest.mark.parametrize(
        "protocol_name",
        [
            "HTTPClientPort",
            "CachePort",
            "MetricsPort",
            "AuthPort",
            "ProviderExecutionPort",
            "RoutingPort",
            "GovernancePort",
            "PluginInterface",
        ],
    )
    def test_protocol_is_runtime_checkable(self, protocol_name: str) -> None:
        protocol_cls = getattr(ports_module, protocol_name)
        # runtime_checkable protocols set _is_runtime_protocol = True
        # on the class. Without it, isinstance(obj, Protocol) raises
        # ``TypeError: Instance and class checks can only be used with
        # @runtime_checkable protocols``.
        assert getattr(protocol_cls, "_is_runtime_protocol", False) is True, (
            f"{protocol_name} missing @runtime_checkable decorator"
        )


# ---------------------------------------------------------------------------
# AdapterRegistry CRUD
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAdapterRegistry:
    """Pin the AdapterRegistry CRUD surface."""

    def test_empty_registry_defaults(self) -> None:
        reg = AdapterRegistry()
        assert reg.drivers == {}
        assert reg.routers == {}
        assert reg.cache_backends == {}
        assert reg.list_drivers() == []
        assert reg.list_routers() == []

    def test_register_driver(self) -> None:
        reg = AdapterRegistry()

        class FakeDriver:
            pass

        reg.register_driver("d1", FakeDriver, version="1.0", trust="high")
        assert "d1" in reg.drivers
        entry = reg.get_driver("d1")
        assert isinstance(entry, DriverPlugin)
        assert entry.name == "d1"
        assert entry.driver_class is FakeDriver
        assert entry.metadata == {"version": "1.0", "trust": "high"}

    def test_register_router(self) -> None:
        reg = AdapterRegistry()

        class FakeRouter:
            pass

        reg.register_router("r1", FakeRouter, region="us")
        entry = reg.get_router("r1")
        assert isinstance(entry, RouterPlugin)
        assert entry.router_class is FakeRouter
        assert entry.metadata == {"region": "us"}

    def test_register_cache_backend(self) -> None:
        reg = AdapterRegistry()

        class FakeCache:
            pass

        reg.register_cache_backend("c1", FakeCache)
        assert reg.cache_backends["c1"] is FakeCache

    def test_register_instance_stores_in_drivers_dict(self) -> None:
        # Back-compat: register_instance stores the raw adapter in the
        # drivers dict (this is intentional for legacy callers).
        reg = AdapterRegistry()
        adapter = object()
        reg.register_instance("legacy", adapter)
        assert reg.drivers["legacy"] is adapter
        assert "legacy" in reg.list_drivers()

    def test_register_classmethod_delegates_to_global(self) -> None:
        # AdapterRegistry.register() is a classmethod that delegates to
        # the global _runtime_registry. Pin this contract.
        class _Capture:
            calls: ClassVar[list[tuple[str, object]]] = []

        # We can't directly monkey-patch _runtime_registry because it
        # is module-private. Instead verify behaviour: after calling
        # the classmethod, the global registry has the entry.
        sentinel = object()

        try:
            AdapterRegistry.register("wl154-classmethod", sentinel)
            assert "wl154-classmethod" in ports_module._runtime_registry.drivers
            assert ports_module._runtime_registry.drivers["wl154-classmethod"] is sentinel
        finally:
            ports_module._runtime_registry.drivers.pop(
                "wl154-classmethod",
                None,
            )

    def test_get_driver_missing_returns_none(self) -> None:
        reg = AdapterRegistry()
        assert reg.get_driver("nope") is None

    def test_get_router_missing_returns_none(self) -> None:
        reg = AdapterRegistry()
        assert reg.get_router("nope") is None

    def test_list_drivers_returns_keys(self) -> None:
        reg = AdapterRegistry()
        reg.register_driver("a", type("A", (), {}))
        reg.register_driver("b", type("B", (), {}))
        assert sorted(reg.list_drivers()) == ["a", "b"]

    def test_list_routers_returns_keys(self) -> None:
        reg = AdapterRegistry()
        reg.register_router("x", type("X", (), {}))
        reg.register_router("y", type("Y", (), {}))
        assert sorted(reg.list_routers()) == ["x", "y"]

    def test_loaded_plugin_is_dataclass(self) -> None:
        # Sanity: LoadedPlugin must remain a dataclass so consumers can
        # use dataclasses.replace / fields() etc.
        assert dataclasses.is_dataclass(LoadedPlugin)
        fields = {f.name for f in dataclasses.fields(LoadedPlugin)}
        assert fields == {"name", "version", "instance", "config"}

    def test_driver_plugin_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(DriverPlugin)
        fields = {f.name for f in dataclasses.fields(DriverPlugin)}
        assert fields == {"name", "driver_class", "metadata"}

    def test_router_plugin_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(RouterPlugin)
        fields = {f.name for f in dataclasses.fields(RouterPlugin)}
        assert fields == {"name", "router_class", "metadata"}


# ---------------------------------------------------------------------------
# PluginHost lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPluginHost:
    """Pin the PluginHost lifecycle surface."""

    def test_empty_host(self) -> None:
        host = PluginHost()
        assert host.list_plugins() == []
        assert host.list_loaded() == []
        assert host.get_plugin("missing") is None

    def test_register_plugin(self) -> None:
        host = PluginHost()
        p = make_fake_plugin("p1")
        host.register_plugin(p)
        assert "p1" in host.list_plugins()
        # Sanity: the plugin's own name attribute reads `_name`.
        assert p.name == "p1"

    def test_load_plugin_initializes(self) -> None:
        host = PluginHost()
        log: list[str] = []
        host.register_plugin(make_fake_plugin("p1", init_log=log))
        host.load_plugin("p1", {"k": "v"})
        assert log == ["init:p1"]
        assert "p1" in host.list_loaded()

    def test_load_plugin_without_config(self) -> None:
        host = PluginHost()
        host.register_plugin(make_fake_plugin("p1"))
        host.load_plugin("p1")
        # loaded entry stores empty config
        assert "p1" in host.list_loaded()

    def test_load_plugin_unknown_raises_keyerror(self) -> None:
        host = PluginHost()
        with pytest.raises(KeyError, match="Plugin 'missing' not registered"):
            host.load_plugin("missing")

    def test_unload_plugin_calls_shutdown(self) -> None:
        host = PluginHost()
        log: list[str] = []
        host.register_plugin(make_fake_plugin("p1", shutdown_log=log))
        host.load_plugin("p1")
        host.unload_plugin("p1")
        assert log == ["shutdown:p1"]
        assert "p1" not in host.list_loaded()

    def test_unload_plugin_unknown_is_silent(self) -> None:
        # Unloading a name that's not in _loaded must not raise — the
        # implementation guards via ``if name in self._loaded``.
        host = PluginHost()
        host.unload_plugin("never-loaded")  # no exception

    def test_swap_plugin_replaces_existing(self) -> None:
        host = PluginHost()
        shutdown_log: list[str] = []
        init_log: list[str] = []
        host.register_plugin(make_fake_plugin("p1", shutdown_log=shutdown_log))
        host.load_plugin("p1")

        new_plugin = make_fake_plugin("p1", version="2.0.0", init_log=init_log)
        host.swap_plugin("p1", new_plugin)
        # old plugin shut down, new plugin initialised
        assert shutdown_log == ["shutdown:p1"]
        assert init_log == ["init:p1"]
        assert host.get_plugin("p1") is new_plugin

    def test_swap_plugin_when_not_loaded_just_loads(self) -> None:
        host = PluginHost()
        init_log: list[str] = []
        host.register_plugin(make_fake_plugin("p1", init_log=init_log))
        # not loaded yet — swap should still register + load
        new_plugin = make_fake_plugin("p1", version="3.0.0")
        host.swap_plugin("p1", new_plugin)
        assert host.get_plugin("p1") is new_plugin

    def test_get_plugin_returns_loaded_instance(self) -> None:
        host = PluginHost()
        p = make_fake_plugin("p1")
        host.register_plugin(p)
        host.load_plugin("p1")
        assert host.get_plugin("p1") is p

    def test_get_plugin_not_loaded_returns_none(self) -> None:
        host = PluginHost()
        host.register_plugin(make_fake_plugin("p1"))
        # registered but not loaded
        assert host.get_plugin("p1") is None


# ---------------------------------------------------------------------------
# Module-level decorators
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModuleLevelDecorators:
    """Pin the module-level register_* decorators."""

    def teardown_method(self) -> None:
        # Each test plants a uniquely-named entry on the global
        # _runtime_registry. Clean up to keep tests isolated.
        reg = ports_module._runtime_registry
        for name in list(reg.drivers):
            if name.startswith("wl154-"):
                reg.drivers.pop(name, None)
        for name in list(reg.routers):
            if name.startswith("wl154-"):
                reg.routers.pop(name, None)
        for name in list(reg.cache_backends):
            if name.startswith("wl154-"):
                reg.cache_backends.pop(name, None)

    def test_register_driver_decorator(self) -> None:
        # The current API is a direct call: register_driver(name, cls,
        # **meta). The decorator-form variant is a separate function.
        class MyDriver:
            pass

        register_driver("wl154-driver", MyDriver, version="1.2.3")
        entry = ports_module._runtime_registry.get_driver("wl154-driver")
        assert entry is not None
        assert entry.driver_class is MyDriver
        assert entry.metadata == {"version": "1.2.3"}
        assert entry.driver_class.__name__ == "MyDriver"

    def test_register_router_decorator(self) -> None:
        class MyRouter:
            pass

        register_router("wl154-router", MyRouter, region="eu")
        entry = ports_module._runtime_registry.get_router("wl154-router")
        assert entry is not None
        assert entry.router_class is MyRouter
        assert entry.metadata == {"region": "eu"}

    def test_register_cache_decorator(self) -> None:
        class MyCache:
            pass

        register_cache("wl154-cache", MyCache)
        assert ports_module._runtime_registry.cache_backends["wl154-cache"] is MyCache


# ---------------------------------------------------------------------------
# Global state isolation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGlobalState:
    """Pin global state invariants for PLUGIN_HOST + _runtime_registry."""

    def test_plugin_host_is_singleton_instance(self) -> None:
        assert isinstance(PLUGIN_HOST, PluginHost)
        # Module-level instance must be usable directly.
        assert PLUGIN_HOST.list_plugins() is not None

    def test_runtime_registry_is_singleton_instance(self) -> None:
        assert isinstance(ports_module._runtime_registry, AdapterRegistry)

    def test_runtime_registry_independent_of_new_instance(self) -> None:
        # A freshly constructed AdapterRegistry must NOT share state
        # with the global _runtime_registry.
        fresh = AdapterRegistry()
        fresh.register_driver("fresh-only", type("X", (), {}))
        assert fresh.get_driver("fresh-only") is not None
        assert ports_module._runtime_registry.get_driver("fresh-only") is None


# ---------------------------------------------------------------------------
# Protocol method-signature pinning
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProtocolMethodSignatures:
    """Pin the public method signatures of each port protocol.

    These are the methods every adapter conforming to the port must
    implement. Removing or renaming any of them is a breaking change
    that must be caught at the test layer.
    """

    def _methods(self, cls: type) -> set[str]:
        # Protocol method names live in __dict__ (not __annotations__).
        # We filter out dunder keys, the abstract-method sentinel, and
        # any names starting with underscore (internal Protocol hooks).
        return {name for name in vars(cls) if not name.startswith("_")}

    def test_http_client_port_methods(self) -> None:
        assert self._methods(HTTPClientPort) == {
            "get",
            "post",
            "put",
            "delete",
            "patch",
        }

    def test_cache_port_methods(self) -> None:
        assert self._methods(CachePort) == {"get", "set", "delete", "clear"}

    def test_metrics_port_methods(self) -> None:
        assert self._methods(MetricsPort) == {
            "increment",
            "gauge",
            "histogram",
            "timing",
        }

    def test_auth_port_methods(self) -> None:
        assert self._methods(AuthPort) == {
            "authenticate",
            "validate_token",
            "refresh_token",
        }

    def test_provider_execution_port_methods(self) -> None:
        assert self._methods(ProviderExecutionPort) == {
            "execute",
            "cancel",
            "get_status",
        }

    def test_routing_port_methods(self) -> None:
        assert self._methods(RoutingPort) == {
            "route",
            "get_available_providers",
        }

    def test_governance_port_methods(self) -> None:
        assert self._methods(GovernancePort) == {
            "check_policy",
            "audit_action",
        }

    def test_plugin_interface_methods(self) -> None:
        # Property accessors appear in __annotations__ as well as
        # regular methods, so we expect both `name` and `version`
        # attributes plus `initialize` / `shutdown` methods.
        names = self._methods(PluginInterface)
        assert "initialize" in names
        assert "shutdown" in names
        assert "name" in names
        assert "version" in names
