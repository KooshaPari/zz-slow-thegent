"""Tests for discovery system wrapper.

Tests cover DiscoverySystem singleton, native extension handling,
fallback behavior, and scan_agents method.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.strategies.discovery import (
    DiscoverySystem,
    get_discovery_system,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before and after each test."""
    DiscoverySystem._instance = None
    DiscoverySystem._interface = None
    yield
    DiscoverySystem._instance = None
    DiscoverySystem._interface = None


class TestDiscoverySystemSingleton:
    """Tests for singleton pattern."""

    def test_singleton_returns_same_instance(self) -> None:
        """Verify singleton returns the same instance."""
        instance1 = DiscoverySystem()
        instance2 = DiscoverySystem()

        assert instance1 is instance2


class TestDiscoverySystemInit:
    """Tests for DiscoverySystem initialization."""

    @patch("thegent.config.ThegentSettings")
    def test_native_disabled_by_default(self, mock_settings: MagicMock) -> None:
        """Verify native discovery is disabled when settings say so."""
        mock_settings.return_value.use_native_discovery = False
        discovery = DiscoverySystem()

        assert discovery.use_native is False
        assert discovery._interface is None

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_but_no_extension(self, mock_settings: MagicMock) -> None:
        """Verify fallback when native extension is not installed (ImportError)."""
        mock_settings.return_value.use_native_discovery = True

        # Ensure the module isn't cached
        original = sys.modules.get("thegent_discovery")
        sys.modules.pop("thegent_discovery", None)

        try:
            discovery = DiscoverySystem()
            assert discovery._interface is None
        finally:
            if original is not None:
                sys.modules["thegent_discovery"] = original

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_with_exception(self, mock_settings: MagicMock) -> None:
        """Verify exception during native init is caught."""
        mock_settings.return_value.use_native_discovery = True

        # Create a mock module that raises an exception when DiscoveryInterface is accessed
        mock_discovery_module = MagicMock()
        mock_discovery_module.DiscoveryInterface.side_effect = RuntimeError("init failed")

        original = sys.modules.get("thegent_discovery")
        try:
            sys.modules["thegent_discovery"] = mock_discovery_module
            discovery = DiscoverySystem()
            assert discovery._interface is None
        finally:
            if original is not None:
                sys.modules["thegent_discovery"] = original
            else:
                sys.modules.pop("thegent_discovery", None)

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_success_path(self, mock_settings: MagicMock) -> None:
        """Verify native discovery is initialized when extension is available."""
        mock_settings.return_value.use_native_discovery = True

        # Create mock module and interface
        mock_interface_instance = MagicMock()
        mock_discovery_module = MagicMock()
        mock_discovery_module.DiscoveryInterface.return_value = mock_interface_instance

        original = sys.modules.get("thegent_discovery")
        try:
            sys.modules["thegent_discovery"] = mock_discovery_module
            discovery = DiscoverySystem()
            mock_discovery_module.DiscoveryInterface.assert_called_once()
            assert discovery._interface is mock_interface_instance
        finally:
            if original is not None:
                sys.modules["thegent_discovery"] = original
            else:
                sys.modules.pop("thegent_discovery", None)


class TestDiscoverySystemIsNativeActive:
    """Tests for is_native_active method."""

    def test_returns_false_when_no_interface(self) -> None:
        """Verify False when interface is None."""
        discovery = DiscoverySystem()
        assert discovery.is_native_active() is False

    def test_returns_true_when_interface_exists(self) -> None:
        """Verify True when interface is set."""
        discovery = DiscoverySystem()
        discovery._interface = MagicMock()

        assert discovery.is_native_active() is True


class TestDiscoverySystemScanAgents:
    """Tests for scan_agents method."""

    def test_returns_empty_list_without_interface(self) -> None:
        """Verify empty list when interface is None."""
        discovery = DiscoverySystem()
        result = discovery.scan_agents()

        assert result == []

    def test_calls_interface_when_available(self) -> None:
        """Verify interface is called when available."""
        discovery = DiscoverySystem()
        mock_interface = MagicMock()
        mock_interface.scan_agents.return_value = [
            {"pid": 1234, "name": "agent-1"},
            {"pid": 5678, "name": "agent-2"},
        ]
        discovery._interface = mock_interface

        result = discovery.scan_agents()

        assert result == [
            {"pid": 1234, "name": "agent-1"},
            {"pid": 5678, "name": "agent-2"},
        ]
        mock_interface.scan_agents.assert_called_once()

    def test_returns_empty_on_interface_exception(self) -> None:
        """Verify empty list when interface raises exception."""
        discovery = DiscoverySystem()
        mock_interface = MagicMock()
        mock_interface.scan_agents.side_effect = RuntimeError("scan failed")
        discovery._interface = mock_interface

        result = discovery.scan_agents()

        assert result == []


class TestGetDiscoverySystem:
    """Tests for get_discovery_system factory function."""

    def test_returns_discovery_instance(self) -> None:
        """Verify factory returns DiscoverySystem instance."""
        result = get_discovery_system()

        assert isinstance(result, DiscoverySystem)

    def test_returns_singleton(self) -> None:
        """Verify factory returns the same singleton instance."""
        result1 = get_discovery_system()
        result2 = get_discovery_system()

        assert result1 is result2
