"""Tests for WL-193: Per-Connector Timeout Controls.

Verifies that per-connector timeout configurations are correctly managed.

# @trace WL-193
"""

from __future__ import annotations

import pytest

from thegent.integrations.connector_timeout import (
    ConnectorTimeoutConfig,
    ConnectorTimeoutRegistry,
)


@pytest.mark.requirement("WL-193")
class TestConnectorTimeoutRegistry:
    """WL-193: Per-connector timeout controls."""

    def test_init_default_timeout(self):
        """Default timeout is 30.0 seconds."""
        registry = ConnectorTimeoutRegistry()
        assert registry.get_timeout("any_connector") == 30.0

    def test_init_custom_default_timeout(self):
        """Custom default timeout is set."""
        registry = ConnectorTimeoutRegistry(default_timeout=60.0)
        assert registry.get_timeout("any_connector") == 60.0

    def test_init_invalid_default_timeout(self):
        """Default timeout <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="default_timeout must be > 0"):
            ConnectorTimeoutRegistry(default_timeout=0)

    def test_init_negative_default_timeout(self):
        """Negative default timeout raises ValueError."""
        with pytest.raises(ValueError, match="default_timeout must be > 0"):
            ConnectorTimeoutRegistry(default_timeout=-10.0)

    def test_set_timeout_basic(self):
        """set_timeout() configures a timeout for a connector."""
        registry = ConnectorTimeoutRegistry()
        registry.set_timeout("connector_a", 45.0)
        assert registry.get_timeout("connector_a") == 45.0

    def test_set_timeout_multiple_connectors(self):
        """set_timeout() configures different timeouts for different connectors."""
        registry = ConnectorTimeoutRegistry()
        registry.set_timeout("connector_a", 45.0)
        registry.set_timeout("connector_b", 60.0)
        registry.set_timeout("connector_c", 15.0)
        assert registry.get_timeout("connector_a") == 45.0
        assert registry.get_timeout("connector_b") == 60.0
        assert registry.get_timeout("connector_c") == 15.0

    def test_set_timeout_override(self):
        """set_timeout() can override an existing timeout."""
        registry = ConnectorTimeoutRegistry()
        registry.set_timeout("connector_a", 30.0)
        assert registry.get_timeout("connector_a") == 30.0
        registry.set_timeout("connector_a", 90.0)
        assert registry.get_timeout("connector_a") == 90.0

    def test_set_timeout_invalid_zero(self):
        """set_timeout() with 0 seconds raises ValueError."""
        registry = ConnectorTimeoutRegistry()
        with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
            registry.set_timeout("connector_a", 0)

    def test_set_timeout_invalid_negative(self):
        """set_timeout() with negative seconds raises ValueError."""
        registry = ConnectorTimeoutRegistry()
        with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
            registry.set_timeout("connector_a", -5.0)

    def test_get_timeout_unconfigured_connector(self):
        """get_timeout() returns default for unconfigured connectors."""
        registry = ConnectorTimeoutRegistry(default_timeout=30.0)
        assert registry.get_timeout("unconfigured") == 30.0

    def test_get_timeout_after_set(self):
        """get_timeout() returns set value."""
        registry = ConnectorTimeoutRegistry(default_timeout=30.0)
        registry.set_timeout("connector_a", 75.0)
        assert registry.get_timeout("connector_a") == 75.0

    def test_remove_existing_connector(self):
        """remove() reverts a connector to default timeout."""
        registry = ConnectorTimeoutRegistry(default_timeout=30.0)
        registry.set_timeout("connector_a", 60.0)
        assert registry.get_timeout("connector_a") == 60.0
        registry.remove("connector_a")
        assert registry.get_timeout("connector_a") == 30.0

    def test_remove_unconfigured_connector(self):
        """remove() on unconfigured connector does nothing."""
        registry = ConnectorTimeoutRegistry()
        registry.remove("unconfigured")  # Should not raise
        assert registry.get_timeout("unconfigured") == 30.0

    def test_all_configs_empty(self):
        """all_configs() returns empty list initially."""
        registry = ConnectorTimeoutRegistry()
        assert registry.all_configs() == []

    def test_all_configs_single_connector(self):
        """all_configs() returns single config."""
        registry = ConnectorTimeoutRegistry()
        registry.set_timeout("connector_a", 45.0)
        configs = registry.all_configs()
        assert len(configs) == 1
        assert configs[0].connector_id == "connector_a"
        assert configs[0].timeout_seconds == 45.0

    def test_all_configs_multiple_connectors(self):
        """all_configs() returns all configured connectors."""
        registry = ConnectorTimeoutRegistry()
        registry.set_timeout("connector_a", 45.0)
        registry.set_timeout("connector_b", 60.0)
        registry.set_timeout("connector_c", 15.0)
        configs = registry.all_configs()
        assert len(configs) == 3

    def test_all_configs_returns_sorted(self):
        """all_configs() returns sorted by connector_id."""
        registry = ConnectorTimeoutRegistry()
        registry.set_timeout("zebra", 45.0)
        registry.set_timeout("apple", 60.0)
        registry.set_timeout("banana", 15.0)
        configs = registry.all_configs()
        connector_ids = [c.connector_id for c in configs]
        assert connector_ids == ["apple", "banana", "zebra"]

    def test_all_configs_after_remove(self):
        """all_configs() excludes removed connectors."""
        registry = ConnectorTimeoutRegistry()
        registry.set_timeout("connector_a", 45.0)
        registry.set_timeout("connector_b", 60.0)
        registry.remove("connector_a")
        configs = registry.all_configs()
        assert len(configs) == 1
        assert configs[0].connector_id == "connector_b"

    def test_connector_timeout_config_dataclass(self):
        """ConnectorTimeoutConfig dataclass works correctly."""
        config = ConnectorTimeoutConfig(connector_id="test", timeout_seconds=42.5)
        assert config.connector_id == "test"
        assert config.timeout_seconds == 42.5

    def test_connector_timeout_config_default(self):
        """ConnectorTimeoutConfig has default timeout_seconds."""
        config = ConnectorTimeoutConfig(connector_id="test")
        assert config.timeout_seconds == 30.0

    def test_set_and_remove_cycle(self):
        """Set, remove, and re-set cycles work correctly."""
        registry = ConnectorTimeoutRegistry(default_timeout=30.0)
        registry.set_timeout("connector_a", 45.0)
        assert registry.get_timeout("connector_a") == 45.0
        registry.remove("connector_a")
        assert registry.get_timeout("connector_a") == 30.0
        registry.set_timeout("connector_a", 90.0)
        assert registry.get_timeout("connector_a") == 90.0
