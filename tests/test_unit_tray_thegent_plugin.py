"""Tests for thegent tray plugin."""

import pytest

pytest.importorskip("PySide6")

from unittest.mock import MagicMock

from thegent.tray.core.plugin_system import TrayPlugin
from thegent.tray.plugins.thegent.api_client import ThegentAPIClient


class TestThegentPlugin:
    """Test suite for ThegentPlugin class."""

    def test_plugin_name_is_thegent(self):
        """Test that the plugin name is 'thegent'."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))
        assert plugin.name == "thegent"

    def test_sidebar_items_returns_six_items(self):
        """Test that sidebar_items returns exactly 6 items."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))
        items = plugin.sidebar_items

        assert len(items) == 6

    def test_sidebar_items_has_correct_ids(self):
        """Test that sidebar items have the correct IDs."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))
        items = plugin.sidebar_items

        expected_ids = [
            "thegent-projects",
            "thegent-agents",
            "thegent-runs",
            "thegent-gardener",
            "thegent-costs",
            "thegent-gamification",
        ]

        actual_ids = [item.id for item in items]
        assert actual_ids == expected_ids

    def test_sidebar_items_have_correct_section(self):
        """Test that all sidebar items have section 'thegent'."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))
        items = plugin.sidebar_items

        for item in items:
            assert item.section == "thegent"

    def test_get_tab_returns_none_initially(self):
        """Test that get_tab returns None initially (lazy loading)."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))

        # Should return None before any tabs are loaded
        assert plugin.get_tab("thegent-projects") is None
        assert plugin.get_tab("thegent-agents") is None
        assert plugin.get_tab("thegent-runs") is None
        assert plugin.get_tab("thegent-gardener") is None
        assert plugin.get_tab("thegent-costs") is None
        assert plugin.get_tab("thegent-gamification") is None

    def test_plugin_is_tray_plugin_subclass(self):
        """Test that ThegentPlugin inherits from TrayPlugin."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        assert issubclass(ThegentPlugin, TrayPlugin)

    def test_plugin_stores_api_client(self):
        """Test that the plugin stores the API client."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        mock_client = MagicMock(spec=ThegentAPIClient)
        plugin = ThegentPlugin(api_client=mock_client)

        assert plugin.api_client is mock_client

    def test_plugin_has_api_client_property(self):
        """Test that the plugin has an api_client property."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))

        # Should be able to access api_client property
        _ = plugin.api_client

    def test_on_activate_is_callable(self):
        """Test that on_activate method exists and is callable."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))
        # Should not raise
        plugin.on_activate()

    def test_on_deactivate_is_callable(self):
        """Test that on_deactivate method exists and is callable."""
        from thegent.tray.plugins.thegent.plugin import ThegentPlugin

        plugin = ThegentPlugin(api_client=MagicMock(spec=ThegentAPIClient))
        # Should not raise
        plugin.on_deactivate()
