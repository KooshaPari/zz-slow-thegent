"""Unit tests for tray plugin system."""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestSidebarItem:
    """Tests for SidebarItem dataclass."""

    def test_creation(self) -> None:
        """SidebarItem stores id, label, icon, tab_ids, section."""
        from thegent.tray.core.plugin_system import SidebarItem

        mock_icon = MagicMock()
        item = SidebarItem(
            id="test-item",
            label="Test Item",
            icon=mock_icon,
            tab_ids=["tab1", "tab2"],
            section="main",
        )
        assert item.id == "test-item"
        assert item.label == "Test Item"
        assert item.icon == mock_icon
        assert item.tab_ids == ["tab1", "tab2"]
        assert item.section == "main"

    def test_default_section(self) -> None:
        """section defaults to 'main'."""
        from thegent.tray.core.plugin_system import SidebarItem

        item = SidebarItem(
            id="test",
            label="Test",
            icon=MagicMock(),
            tab_ids=["tab1"],
        )
        assert item.section == "main"


@pytest.mark.unit
class TestTrayPlugin:
    """Tests for TrayPlugin abstract base class."""

    def test_abstract_methods_exist(self) -> None:
        """TrayPlugin has required abstract methods and properties."""
        from abc import ABC

        from thegent.tray.core.plugin_system import TrayPlugin

        # Verify TrayPlugin is an ABC
        assert issubclass(TrayPlugin, ABC)

        # Verify required abstract methods/properties exist
        assert hasattr(TrayPlugin, "name")
        assert hasattr(TrayPlugin, "sidebar_items")
        assert hasattr(TrayPlugin, "get_tab")
        assert hasattr(TrayPlugin, "on_activate")
        assert hasattr(TrayPlugin, "on_deactivate")

    def test_cannot_instantiate_directly(self) -> None:
        """TrayPlugin cannot be instantiated directly."""
        from thegent.tray.core.plugin_system import TrayPlugin

        with pytest.raises(TypeError):
            TrayPlugin()


@pytest.mark.unit
class TestPluginRegistry:
    """Tests for PluginRegistry class."""

    def test_empty_registry(self) -> None:
        """PluginRegistry starts empty."""
        from thegent.tray.core.plugin_system import PluginRegistry

        registry = PluginRegistry()
        assert registry.list_plugins() == []

    def test_register_plugin(self) -> None:
        """PluginRegistry can register a plugin."""
        from typing import Any

        from thegent.tray.core.plugin_system import PluginRegistry, TrayPlugin

        class MockPlugin(TrayPlugin):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def sidebar_items(self) -> list:
                return []

            def get_tab(self, tab_id: str) -> Any:
                return None

            def on_activate(self) -> None:
                pass

            def on_deactivate(self) -> None:
                pass

        registry = PluginRegistry()
        plugin = MockPlugin()
        registry.register("mock", plugin)

        assert "mock" in registry.list_plugins()

    def test_get_plugin(self) -> None:
        """PluginRegistry can retrieve a registered plugin."""
        from typing import Any

        from thegent.tray.core.plugin_system import PluginRegistry, TrayPlugin

        class MockPlugin(TrayPlugin):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def sidebar_items(self) -> list:
                return []

            def get_tab(self, tab_id: str) -> Any:
                return None

            def on_activate(self) -> None:
                pass

            def on_deactivate(self) -> None:
                pass

        registry = PluginRegistry()
        plugin = MockPlugin()
        registry.register("mock", plugin)

        retrieved = registry.get_plugin("mock")
        assert retrieved is plugin

    def test_get_plugin_not_found(self) -> None:
        """PluginRegistry returns None for unknown plugin."""
        from thegent.tray.core.plugin_system import PluginRegistry

        registry = PluginRegistry()
        assert registry.get_plugin("nonexistent") is None
