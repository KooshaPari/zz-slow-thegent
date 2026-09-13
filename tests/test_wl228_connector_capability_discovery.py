"""Tests for thegent.integrations.connector_capability_discovery — Connector capability discovery.

@trace WL-228
"""

from __future__ import annotations

import pytest

from thegent.integrations.connector_capability_discovery import (
    ConnectorCapability,
    ConnectorCapabilityRegistry,
)


class TestConnectorCapability:
    """Test ConnectorCapability dataclass. @trace WL-228"""

    @pytest.mark.requirement("WL-228")
    def test_create_capability(self) -> None:
        """Can create a ConnectorCapability with all fields."""
        cap = ConnectorCapability(
            connector_id="github", capabilities=["oauth2", "webhook", "streaming"]
        )

        assert cap.connector_id == "github"
        assert cap.capabilities == ["oauth2", "webhook", "streaming"]

    @pytest.mark.requirement("WL-228")
    def test_empty_capabilities(self) -> None:
        """Can create a ConnectorCapability with empty capabilities list."""
        cap = ConnectorCapability(connector_id="basic", capabilities=[])

        assert cap.connector_id == "basic"
        assert cap.capabilities == []


class TestConnectorCapabilityRegistry:
    """Test ConnectorCapabilityRegistry operations. @trace WL-228"""

    @pytest.fixture
    def registry(self) -> ConnectorCapabilityRegistry:
        """Provide a fresh registry."""
        return ConnectorCapabilityRegistry()

    @pytest.mark.requirement("WL-228")
    def test_register_connector(self, registry: ConnectorCapabilityRegistry) -> None:
        """Can register a connector with capabilities."""
        result = registry.register("github", ["oauth2", "webhook"])

        assert result.connector_id == "github"
        assert result.capabilities == ["oauth2", "webhook"]

    @pytest.mark.requirement("WL-228")
    def test_register_duplicate_raises(
        self, registry: ConnectorCapabilityRegistry
    ) -> None:
        """Registering the same connector twice raises ValueError."""
        registry.register("github", ["oauth2"])

        with pytest.raises(ValueError, match="already registered"):
            registry.register("github", ["webhook"])

    @pytest.mark.requirement("WL-228")
    def test_has_capability_true(self, registry: ConnectorCapabilityRegistry) -> None:
        """has_capability returns True for registered capability."""
        registry.register("github", ["oauth2", "webhook"])

        assert registry.has_capability("github", "oauth2") is True
        assert registry.has_capability("github", "webhook") is True

    @pytest.mark.requirement("WL-228")
    def test_has_capability_false(self, registry: ConnectorCapabilityRegistry) -> None:
        """has_capability returns False for missing capability."""
        registry.register("github", ["oauth2"])

        assert registry.has_capability("github", "webhook") is False
        assert registry.has_capability("unknown", "oauth2") is False

    @pytest.mark.requirement("WL-228")
    def test_connectors_with_capability(
        self, registry: ConnectorCapabilityRegistry
    ) -> None:
        """connectors_with returns all connectors with a capability."""
        registry.register("github", ["oauth2", "webhook"])
        registry.register("linear", ["oauth2", "rest"])
        registry.register("jira", ["rest", "basic"])

        oauth2_connectors = registry.connectors_with("oauth2")
        assert set(oauth2_connectors) == {"github", "linear"}

        rest_connectors = registry.connectors_with("rest")
        assert set(rest_connectors) == {"linear", "jira"}

        basic_connectors = registry.connectors_with("basic")
        assert basic_connectors == ["jira"]

    @pytest.mark.requirement("WL-228")
    def test_connectors_with_missing_capability(
        self, registry: ConnectorCapabilityRegistry
    ) -> None:
        """connectors_with returns empty list for missing capability."""
        registry.register("github", ["oauth2"])

        streaming_connectors = registry.connectors_with("streaming")
        assert streaming_connectors == []

    @pytest.mark.requirement("WL-228")
    def test_get_connector(self, registry: ConnectorCapabilityRegistry) -> None:
        """get returns the ConnectorCapability for a registered connector."""
        registry.register("github", ["oauth2", "webhook"])

        result = registry.get("github")
        assert result.connector_id == "github"
        assert result.capabilities == ["oauth2", "webhook"]

    @pytest.mark.requirement("WL-228")
    def test_get_unregistered_raises(
        self, registry: ConnectorCapabilityRegistry
    ) -> None:
        """get raises KeyError for unregistered connector."""
        with pytest.raises(KeyError, match="not found"):
            registry.get("unknown")

    @pytest.mark.requirement("WL-228")
    def test_multiple_connectors(self, registry: ConnectorCapabilityRegistry) -> None:
        """Can register and manage multiple connectors."""
        registry.register("github", ["oauth2", "webhook"])
        registry.register("linear", ["oauth2"])
        registry.register("jira", ["basic"])

        assert registry.has_capability("github", "oauth2")
        assert registry.has_capability("linear", "oauth2")
        assert registry.has_capability("jira", "basic")
        assert not registry.has_capability("jira", "oauth2")

    @pytest.mark.requirement("WL-228")
    def test_empty_registry_connectors_with(
        self, registry: ConnectorCapabilityRegistry
    ) -> None:
        """connectors_with on empty registry returns empty list."""
        result = registry.connectors_with("oauth2")
        assert result == []
