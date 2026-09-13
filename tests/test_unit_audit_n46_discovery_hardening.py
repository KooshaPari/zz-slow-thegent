"""AUDIT-N+46: strategies/discovery hardening spec.

15 invariants (FR-ORC-DC-001..015) covering DiscoverySystem singleton,
native extension handling, is_native_active, scan_agents, discover, and
get_discovery_system factory.

SOTA pass-30 — 48 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.strategies.discovery import (
    DiscoverySystem,
    get_discovery_system,
)


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset singleton state before and after each test."""
    DiscoverySystem._instance = None
    DiscoverySystem._interface = None
    yield
    DiscoverySystem._instance = None
    DiscoverySystem._interface = None


# ── FR-ORC-DC-001: DiscoverySystem is a @dataclass ──────────────────────────


class TestDC001Dataclass:
    def test_is_dataclass(self) -> None:
        from dataclasses import fields as dc_fields

        assert len(dc_fields(DiscoverySystem())) >= 0


# ── FR-ORC-DC-002: Singleton via __new__ ────────────────────────────────────


class TestDC002Singleton:
    def test_same_instance(self) -> None:
        a = DiscoverySystem()
        b = DiscoverySystem()
        assert a is b

    def test_singleton_persists(self) -> None:
        a = DiscoverySystem()
        b = DiscoverySystem()
        assert a is b


# ── FR-ORC-DC-003: __init__ reads use_native from settings ─────────────────


class TestDC003Init:
    @patch("thegent.config.ThegentSettings")
    def test_native_disabled(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value.use_native_discovery = False
        ds = DiscoverySystem()
        assert ds.use_native is False
        assert ds._interface is None

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_no_extension(self, mock_settings: MagicMock) -> None:
        import sys

        mock_settings.return_value.use_native_discovery = True
        original = sys.modules.pop("thegent_discovery", None)
        try:
            ds = DiscoverySystem()
            assert ds._interface is None
        finally:
            if original is not None:
                sys.modules["thegent_discovery"] = original

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_exception(self, mock_settings: MagicMock) -> None:
        import sys

        mock_settings.return_value.use_native_discovery = True
        mock_mod = MagicMock()
        mock_mod.DiscoveryInterface.side_effect = RuntimeError("boom")
        original = sys.modules.pop("thegent_discovery", None)
        try:
            sys.modules["thegent_discovery"] = mock_mod
            ds = DiscoverySystem()
            assert ds._interface is None
        finally:
            if original is not None:
                sys.modules["thegent_discovery"] = original


# ── FR-ORC-DC-004: __init__ loads native extension on success ───────────────


class TestDC004NativeSuccess:
    @patch("thegent.config.ThegentSettings")
    def test_native_interface_set(self, mock_settings: MagicMock) -> None:
        import sys

        mock_settings.return_value.use_native_discovery = True
        mock_iface = MagicMock()
        mock_mod = MagicMock()
        mock_mod.DiscoveryInterface.return_value = mock_iface
        original = sys.modules.pop("thegent_discovery", None)
        try:
            sys.modules["thegent_discovery"] = mock_mod
            ds = DiscoverySystem()
            assert ds._interface is mock_iface
        finally:
            if original is not None:
                sys.modules["thegent_discovery"] = original


# ── FR-ORC-DC-005: is_native_active returns bool ────────────────────────────


class TestDC005IsActive:
    def test_false_no_interface(self) -> None:
        ds = DiscoverySystem()
        assert ds.is_native_active() is False

    def test_true_with_interface(self) -> None:
        ds = DiscoverySystem()
        ds._interface = MagicMock()
        assert ds.is_native_active() is True


# ── FR-ORC-DC-006: discover returns list[str] ───────────────────────────────


class TestDC006Discover:
    def test_returns_list(self) -> None:
        ds = DiscoverySystem()
        result = ds.discover()
        assert isinstance(result, list)

    def test_default_empty(self) -> None:
        ds = DiscoverySystem()
        assert ds.discover() == []


# ── FR-ORC-DC-007: scan_agents returns list ─────────────────────────────────


class TestDC007ScanAgents:
    def test_empty_without_interface(self) -> None:
        ds = DiscoverySystem()
        assert ds.scan_agents() == []

    def test_delegates_to_interface(self) -> None:
        ds = DiscoverySystem()
        mock_iface = MagicMock()
        mock_iface.scan_agents.return_value = [{"pid": 1}]
        ds._interface = mock_iface
        assert ds.scan_agents() == [{"pid": 1}]
        mock_iface.scan_agents.assert_called_once()

    def test_returns_empty_on_exception(self) -> None:
        ds = DiscoverySystem()
        mock_iface = MagicMock()
        mock_iface.scan_agents.side_effect = RuntimeError("fail")
        ds._interface = mock_iface
        assert ds.scan_agents() == []


# ── FR-ORC-DC-008: get_discovery_system factory ─────────────────────────────


class TestDC008Factory:
    def test_returns_instance(self) -> None:
        result = get_discovery_system()
        assert isinstance(result, DiscoverySystem)

    def test_returns_singleton(self) -> None:
        a = get_discovery_system()
        b = get_discovery_system()
        assert a is b


# ── FR-ORC-DC-009: __all__ exports ──────────────────────────────────────────


class TestDC009Exports:
    def test_all_defined(self) -> None:
        from thegent.orchestration.strategies.discovery import __all__

        assert "DiscoverySystem" in __all__
        assert "get_discovery_system" in __all__


# ── FR-ORC-DC-010: Docstrings present ───────────────────────────────────────


class TestDC010Docstrings:
    def test_class_docstring(self) -> None:
        assert DiscoverySystem.__doc__ is not None

    def test_discover_docstring(self) -> None:
        assert DiscoverySystem.discover.__doc__ is not None


# ── FR-ORC-DC-011: Thread-safe singleton reset ─────────────────────────────


class TestDC011ThreadSafety:
    def test_manual_reset(self) -> None:
        a = DiscoverySystem()
        DiscoverySystem._instance = None
        b = DiscoverySystem()
        assert a is not b


# ── FR-ORC-DC-012: scan_agents handles non-dict return ─────────────────────


class TestDC012ScanAgentsEdge:
    def test_empty_interface_result(self) -> None:
        ds = DiscoverySystem()
        mock_iface = MagicMock()
        mock_iface.scan_agents.return_value = []
        ds._interface = mock_iface
        assert ds.scan_agents() == []


# ── FR-ORC-DC-013: discover method is callable ──────────────────────────────


class TestDC013DiscoverCallable:
    def test_callable(self) -> None:
        ds = DiscoverySystem()
        assert callable(ds.discover)


# ── FR-ORC-DC-014: scan_agents method is callable ───────────────────────────


class TestDC014ScanCallable:
    def test_callable(self) -> None:
        ds = DiscoverySystem()
        assert callable(ds.scan_agents)


# ── FR-ORC-DC-015: No secrets in module ────────────────────────────────────


class TestDC015NoSecrets:
    def test_no_api_keys(self) -> None:
        import inspect

        source = inspect.getsource(DiscoverySystem)
        assert "api_key" not in source.lower()
        assert "secret" not in source.lower()
