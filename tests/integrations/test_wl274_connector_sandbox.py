"""Tests for thegent.integrations.connector_sandbox — Sandbox mode and promotion.

@trace WL-274
"""

from __future__ import annotations

import pytest

from thegent.integrations.connector_sandbox import (
    ConnectorSandboxRegistry,
    SandboxConnector,
)


class TestSandboxConnector:
    """Test SandboxConnector dataclass. @trace WL-274"""

    @pytest.mark.requirement("WL-274")
    def test_create_default_sandbox(self) -> None:
        """Can create SandboxConnector with default sandbox=True."""
        connector = SandboxConnector(connector_id="github", project_id="proj1")

        assert connector.connector_id == "github"
        assert connector.project_id == "proj1"
        assert connector.sandbox is True

    @pytest.mark.requirement("WL-274")
    def test_create_production(self) -> None:
        """Can create SandboxConnector with sandbox=False."""
        connector = SandboxConnector(
            connector_id="github", project_id="proj1", sandbox=False
        )

        assert connector.connector_id == "github"
        assert connector.sandbox is False

    @pytest.mark.requirement("WL-274")
    def test_connector_fields(self) -> None:
        """SandboxConnector has all required fields."""
        connector = SandboxConnector(
            connector_id="linear",
            project_id="proj-123",
            sandbox=True,
        )

        assert hasattr(connector, "connector_id")
        assert hasattr(connector, "project_id")
        assert hasattr(connector, "sandbox")


class TestConnectorSandboxRegistry:
    """Test ConnectorSandboxRegistry operations. @trace WL-274"""

    @pytest.mark.requirement("WL-274")
    def test_register_single_connector(self) -> None:
        """Can register a single connector."""
        registry = ConnectorSandboxRegistry()
        connector = registry.register("github", "proj1")

        assert connector.connector_id == "github"
        assert connector.project_id == "proj1"
        assert connector.sandbox is True

    @pytest.mark.requirement("WL-274")
    def test_register_multiple_connectors(self) -> None:
        """Can register multiple connectors."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1")
        registry.register("linear", "proj2")
        registry.register("slack", "proj3")

        assert registry.is_sandbox("github") is True
        assert registry.is_sandbox("linear") is True
        assert registry.is_sandbox("slack") is True

    @pytest.mark.requirement("WL-274")
    def test_register_with_sandbox_false(self) -> None:
        """Can register connector directly in production mode."""
        registry = ConnectorSandboxRegistry()
        connector = registry.register("github", "proj1", sandbox=False)

        assert connector.sandbox is False
        assert registry.is_sandbox("github") is False

    @pytest.mark.requirement("WL-274")
    def test_is_sandbox_existing(self) -> None:
        """is_sandbox returns correct value for registered connectors."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=True)
        registry.register("linear", "proj2", sandbox=False)

        assert registry.is_sandbox("github") is True
        assert registry.is_sandbox("linear") is False

    @pytest.mark.requirement("WL-274")
    def test_is_sandbox_nonexistent(self) -> None:
        """is_sandbox returns False for unregistered connectors."""
        registry = ConnectorSandboxRegistry()
        assert registry.is_sandbox("nonexistent") is False

    @pytest.mark.requirement("WL-274")
    def test_all_sandbox_empty(self) -> None:
        """all_sandbox returns empty list when none in sandbox."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=False)
        registry.register("linear", "proj2", sandbox=False)

        sandbox_list = registry.all_sandbox()
        assert len(sandbox_list) == 0

    @pytest.mark.requirement("WL-274")
    def test_all_sandbox_partial(self) -> None:
        """all_sandbox returns only connectors in sandbox mode."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=True)
        registry.register("linear", "proj2", sandbox=False)
        registry.register("slack", "proj3", sandbox=True)

        sandbox_list = registry.all_sandbox()
        assert len(sandbox_list) == 2

        connector_ids = {c.connector_id for c in sandbox_list}
        assert connector_ids == {"github", "slack"}

    @pytest.mark.requirement("WL-274")
    def test_all_sandbox_all(self) -> None:
        """all_sandbox returns all connectors when all are in sandbox."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=True)
        registry.register("linear", "proj2", sandbox=True)

        sandbox_list = registry.all_sandbox()
        assert len(sandbox_list) == 2

    @pytest.mark.requirement("WL-274")
    def test_promote_from_sandbox(self) -> None:
        """promote() changes sandbox connector to production."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=True)

        assert registry.is_sandbox("github") is True
        registry.promote("github")
        assert registry.is_sandbox("github") is False

    @pytest.mark.requirement("WL-274")
    def test_promote_production_no_change(self) -> None:
        """promote() on production connector keeps it production."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=False)

        registry.promote("github")
        assert registry.is_sandbox("github") is False

    @pytest.mark.requirement("WL-274")
    def test_promote_nonexistent_raises(self) -> None:
        """promote() raises ValueError for unregistered connectors."""
        registry = ConnectorSandboxRegistry()

        with pytest.raises(ValueError, match="Connector not registered"):
            registry.promote("nonexistent")

    @pytest.mark.requirement("WL-274")
    def test_all_sandbox_after_promotion(self) -> None:
        """all_sandbox updates when connectors are promoted."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=True)
        registry.register("linear", "proj2", sandbox=True)

        assert len(registry.all_sandbox()) == 2

        registry.promote("github")
        assert len(registry.all_sandbox()) == 1

        registry.promote("linear")
        assert len(registry.all_sandbox()) == 0

    @pytest.mark.requirement("WL-274")
    def test_register_overwrites(self) -> None:
        """Registering same connector again overwrites."""
        registry = ConnectorSandboxRegistry()
        registry.register("github", "proj1", sandbox=True)
        registry.register("github", "proj2", sandbox=False)

        connector = registry.all_sandbox()
        assert len(connector) == 0
        assert registry.is_sandbox("github") is False


class TestConnectorSandboxRegistryIntegration:
    """Integration tests for ConnectorSandboxRegistry. @trace WL-274"""

    @pytest.mark.requirement("WL-274")
    def test_complete_lifecycle(self) -> None:
        """Complete workflow: register -> verify -> promote -> verify."""
        registry = ConnectorSandboxRegistry()

        # Register in sandbox
        registry.register("github", "proj1", sandbox=True)
        registry.register("linear", "proj2", sandbox=True)
        registry.register("slack", "proj3", sandbox=False)

        # Verify sandbox state
        assert len(registry.all_sandbox()) == 2
        assert registry.is_sandbox("github") is True
        assert registry.is_sandbox("linear") is True
        assert registry.is_sandbox("slack") is False

        # Promote github to production
        registry.promote("github")

        # Verify updated state
        assert len(registry.all_sandbox()) == 1
        assert registry.is_sandbox("github") is False
        assert registry.is_sandbox("linear") is True

        # Promote remaining
        registry.promote("linear")
        assert len(registry.all_sandbox()) == 0

    @pytest.mark.requirement("WL-274")
    def test_multiple_projects_same_connector(self) -> None:
        """Can register same connector type for different projects."""
        registry = ConnectorSandboxRegistry()

        registry.register("github", "proj1", sandbox=True)
        registry.register("github", "proj2", sandbox=False)

        # Second registration overwrites
        assert registry.is_sandbox("github") is False

    @pytest.mark.requirement("WL-274")
    def test_connector_metadata_preserved(self) -> None:
        """Connector project_id is preserved through operations."""
        registry = ConnectorSandboxRegistry()
        connector = registry.register("github", "proj-xyz", sandbox=True)

        assert connector.project_id == "proj-xyz"

        registry.promote("github")

        # Registry doesn't have direct access to connector, but we can verify it was registered
        assert registry.is_sandbox("github") is False

    @pytest.mark.requirement("WL-274")
    def test_sandbox_list_ordering(self) -> None:
        """all_sandbox returns list of sandbox connectors."""
        registry = ConnectorSandboxRegistry()
        registry.register("connector_a", "proj1", sandbox=True)
        registry.register("connector_b", "proj2", sandbox=False)
        registry.register("connector_c", "proj3", sandbox=True)

        sandbox_list = registry.all_sandbox()
        assert len(sandbox_list) == 2

        # All returned connectors should have sandbox=True
        for connector in sandbox_list:
            assert connector.sandbox is True

    @pytest.mark.requirement("WL-274")
    def test_large_registry(self) -> None:
        """Registry handles large number of connectors."""
        registry = ConnectorSandboxRegistry()

        for i in range(100):
            connector_id = f"connector_{i}"
            project_id = f"proj_{i % 10}"
            sandbox = i % 2 == 0

            registry.register(connector_id, project_id, sandbox=sandbox)

        sandbox_list = registry.all_sandbox()
        assert len(sandbox_list) == 50
