"""Tests for thegent.integrations.versioned_mapping — Versioned mapping registry.

@trace WL-311
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.versioned_mapping import (
    MappingVersion,
    VersionedMappingRegistry,
)


class TestMappingVersion:
    """Test MappingVersion dataclass. @trace WL-311"""

    @pytest.mark.requirement("WL-311")
    def test_create_mapping_version(self) -> None:
        """Can create a MappingVersion with all fields."""
        now = datetime.now(UTC)
        mappings = {"key1": "value1", "key2": "value2"}
        version = MappingVersion(
            version=1,
            mappings=mappings,
            created_at=now,
            label="Initial version",
        )

        assert version.version == 1
        assert version.mappings == mappings
        assert version.created_at == now
        assert version.label == "Initial version"

    @pytest.mark.requirement("WL-311")
    def test_mapping_version_default_label(self) -> None:
        """MappingVersion defaults label to empty string."""
        now = datetime.now(UTC)
        version = MappingVersion(
            version=1,
            mappings={"key": "value"},
            created_at=now,
        )

        assert version.label == ""


class TestVersionedMappingRegistryInit:
    """Test VersionedMappingRegistry initialization. @trace WL-311"""

    @pytest.mark.requirement("WL-311")
    def test_init_creates_empty_registry(self) -> None:
        """Registry initializes empty."""
        registry = VersionedMappingRegistry()
        assert registry.list_versions() == []

    @pytest.mark.requirement("WL-311")
    def test_init_sets_next_version_to_1(self) -> None:
        """Registry starts with next version 1."""
        registry = VersionedMappingRegistry()
        mappings = {"key": "value"}
        version = registry.register(mappings)
        assert version.version == 1


class TestVersionedMappingRegistryRegister:
    """Test VersionedMappingRegistry.register() method. @trace WL-311"""

    @pytest.mark.requirement("WL-311")
    def test_register_first_version(self) -> None:
        """Can register first version."""
        registry = VersionedMappingRegistry()
        mappings = {"key1": "value1"}

        version = registry.register(mappings)

        assert version.version == 1
        assert version.mappings == mappings
        assert isinstance(version.created_at, datetime)

    @pytest.mark.requirement("WL-311")
    def test_register_auto_increments_version(self) -> None:
        """Versions auto-increment."""
        registry = VersionedMappingRegistry()

        v1 = registry.register({"a": "1"})
        v2 = registry.register({"b": "2"})
        v3 = registry.register({"c": "3"})

        assert v1.version == 1
        assert v2.version == 2
        assert v3.version == 3

    @pytest.mark.requirement("WL-311")
    def test_register_with_label(self) -> None:
        """Can register with a descriptive label."""
        registry = VersionedMappingRegistry()
        mappings = {"key": "value"}

        version = registry.register(mappings, label="Production v1.0")

        assert version.label == "Production v1.0"

    @pytest.mark.requirement("WL-311")
    def test_register_copies_mappings(self) -> None:
        """Register copies mappings (doesn't hold reference)."""
        registry = VersionedMappingRegistry()
        mappings = {"key": "value"}

        version = registry.register(mappings)
        mappings["key"] = "modified"

        assert version.mappings["key"] == "value"


class TestVersionedMappingRegistryGetVersion:
    """Test VersionedMappingRegistry.get_version() method. @trace WL-311"""

    @pytest.mark.requirement("WL-311")
    def test_get_version_exists(self) -> None:
        """Can retrieve an existing version."""
        registry = VersionedMappingRegistry()
        mappings = {"key": "value"}
        expected = registry.register(mappings)

        retrieved = registry.get_version(1)

        assert retrieved.version == expected.version
        assert retrieved.mappings == expected.mappings

    @pytest.mark.requirement("WL-311")
    def test_get_version_not_found(self) -> None:
        """Raises KeyError for non-existent version."""
        registry = VersionedMappingRegistry()
        registry.register({"key": "value"})

        with pytest.raises(KeyError) as exc_info:
            registry.get_version(999)

        assert "999" in str(exc_info.value)

    @pytest.mark.requirement("WL-311")
    def test_get_version_from_empty_registry(self) -> None:
        """Raises KeyError when retrieving from empty registry."""
        registry = VersionedMappingRegistry()

        with pytest.raises(KeyError):
            registry.get_version(1)


class TestVersionedMappingRegistryLatest:
    """Test VersionedMappingRegistry.latest() method. @trace WL-311"""

    @pytest.mark.requirement("WL-311")
    def test_latest_single_version(self) -> None:
        """Can get latest when only one version exists."""
        registry = VersionedMappingRegistry()
        expected = registry.register({"key": "value"})

        latest = registry.latest()

        assert latest.version == expected.version

    @pytest.mark.requirement("WL-311")
    def test_latest_multiple_versions(self) -> None:
        """Returns highest version number."""
        registry = VersionedMappingRegistry()
        registry.register({"v": "1"})
        registry.register({"v": "2"})
        expected = registry.register({"v": "3"})

        latest = registry.latest()

        assert latest.version == expected.version
        assert latest.mappings == {"v": "3"}

    @pytest.mark.requirement("WL-311")
    def test_latest_empty_registry(self) -> None:
        """Raises ValueError when no versions exist."""
        registry = VersionedMappingRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.latest()

        assert "No versions" in str(exc_info.value)


class TestVersionedMappingRegistryListVersions:
    """Test VersionedMappingRegistry.list_versions() method. @trace WL-311"""

    @pytest.mark.requirement("WL-311")
    def test_list_versions_empty(self) -> None:
        """Empty registry returns empty list."""
        registry = VersionedMappingRegistry()

        versions = registry.list_versions()

        assert versions == []

    @pytest.mark.requirement("WL-311")
    def test_list_versions_single(self) -> None:
        """Can list single version."""
        registry = VersionedMappingRegistry()
        registry.register({"key": "value"})

        versions = registry.list_versions()

        assert versions == [1]

    @pytest.mark.requirement("WL-311")
    def test_list_versions_multiple(self) -> None:
        """Lists multiple versions in ascending order."""
        registry = VersionedMappingRegistry()
        registry.register({"v": "1"})
        registry.register({"v": "2"})
        registry.register({"v": "3"})

        versions = registry.list_versions()

        assert versions == [1, 2, 3]

    @pytest.mark.requirement("WL-311")
    def test_list_versions_sorted(self) -> None:
        """Versions are returned in sorted order."""
        registry = VersionedMappingRegistry()
        registry.register({"a": "1"})
        registry.register({"b": "2"})
        registry.register({"c": "3"})

        versions = registry.list_versions()

        assert versions == sorted(versions)


class TestVersionedMappingRegistryResolve:
    """Test VersionedMappingRegistry.resolve() method. @trace WL-311"""

    @pytest.mark.requirement("WL-311")
    def test_resolve_with_specific_version(self) -> None:
        """Can resolve key from specific version."""
        registry = VersionedMappingRegistry()
        registry.register({"conn_a": "github"})
        registry.register({"conn_b": "linear"})

        result = registry.resolve("conn_a", version=1)

        assert result == "github"

    @pytest.mark.requirement("WL-311")
    def test_resolve_with_latest_version(self) -> None:
        """Resolves from latest version when version=None."""
        registry = VersionedMappingRegistry()
        registry.register({"conn": "github"})
        registry.register({"conn": "linear"})

        result = registry.resolve("conn")

        assert result == "linear"

    @pytest.mark.requirement("WL-311")
    def test_resolve_key_not_found_in_version(self) -> None:
        """Raises KeyError if key not found in version."""
        registry = VersionedMappingRegistry()
        registry.register({"key1": "value1"})

        with pytest.raises(KeyError) as exc_info:
            registry.resolve("missing_key", version=1)

        assert "missing_key" in str(exc_info.value)

    @pytest.mark.requirement("WL-311")
    def test_resolve_version_not_found(self) -> None:
        """Raises KeyError if version doesn't exist."""
        registry = VersionedMappingRegistry()
        registry.register({"key": "value"})

        with pytest.raises(KeyError):
            registry.resolve("key", version=999)

    @pytest.mark.requirement("WL-311")
    def test_resolve_no_versions(self) -> None:
        """Raises ValueError if no versions registered."""
        registry = VersionedMappingRegistry()

        with pytest.raises(ValueError):
            registry.resolve("key")

    @pytest.mark.requirement("WL-311")
    def test_resolve_different_keys_across_versions(self) -> None:
        """Different versions can have different keys."""
        registry = VersionedMappingRegistry()
        registry.register({"connector1": "github"})
        registry.register({"connector1": "github", "connector2": "linear"})
        registry.register({"connector1": "github", "connector2": "linear", "connector3": "jira"})

        assert registry.resolve("connector1", version=1) == "github"
        assert registry.resolve("connector2", version=2) == "linear"
        assert registry.resolve("connector3", version=3) == "jira"

        # Version 1 doesn't have connector2
        with pytest.raises(KeyError):
            registry.resolve("connector2", version=1)
