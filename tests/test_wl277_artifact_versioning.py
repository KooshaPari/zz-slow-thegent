"""Tests for artifact format versioning.

# @trace WL-277
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.artifact_versioning import (
    ArtifactFormatRegistry,
    ArtifactVersion,
)


@pytest.mark.requirement("WL-277")
class TestArtifactVersion:
    """Test ArtifactVersion dataclass."""

    def test_artifact_version_creation(self) -> None:
        """Test creating an ArtifactVersion."""
        now = datetime.now(UTC)
        version = ArtifactVersion(format_version="1.0", schema_hash="abc123", created_at=now)
        assert version.format_version == "1.0"
        assert version.schema_hash == "abc123"
        assert version.created_at == now

    def test_artifact_version_fields(self) -> None:
        """Test ArtifactVersion has expected fields."""
        now = datetime.now(UTC)
        version = ArtifactVersion(format_version="2.0", schema_hash="def456", created_at=now)
        assert hasattr(version, "format_version")
        assert hasattr(version, "schema_hash")
        assert hasattr(version, "created_at")


@pytest.mark.requirement("WL-277")
class TestArtifactFormatRegistry:
    """Test ArtifactFormatRegistry."""

    def test_register_version(self) -> None:
        """Test registering a new version."""
        registry = ArtifactFormatRegistry()
        before = datetime.now(UTC)
        version = registry.register("1.0", "hash123")
        after = datetime.now(UTC)
        assert version.format_version == "1.0"
        assert version.schema_hash == "hash123"
        assert before <= version.created_at <= after

    def test_get_version(self) -> None:
        """Test retrieving a registered version."""
        registry = ArtifactFormatRegistry()
        registered = registry.register("1.0", "hash123")
        retrieved = registry.get("1.0")
        assert retrieved.format_version == "1.0"
        assert retrieved.schema_hash == "hash123"
        assert retrieved == registered

    def test_get_version_not_found(self) -> None:
        """Test retrieving a non-existent version raises KeyError."""
        registry = ArtifactFormatRegistry()
        with pytest.raises(KeyError):
            registry.get("2.0")

    def test_latest_with_versions(self) -> None:
        """Test getting the latest version."""
        registry = ArtifactFormatRegistry()
        registry.register("1.0", "hash1")
        v2 = registry.register("2.0", "hash2")
        latest = registry.latest()
        assert latest == v2
        assert latest.format_version == "2.0"

    def test_latest_empty_registry(self) -> None:
        """Test latest() returns None for empty registry."""
        registry = ArtifactFormatRegistry()
        assert registry.latest() is None

    def test_all_versions(self) -> None:
        """Test retrieving all versions."""
        registry = ArtifactFormatRegistry()
        v1 = registry.register("1.0", "hash1")
        v2 = registry.register("2.0", "hash2")
        versions = registry.all_versions()
        assert len(versions) == 2
        assert v1 in versions
        assert v2 in versions

    def test_all_versions_empty(self) -> None:
        """Test all_versions() returns empty list for new registry."""
        registry = ArtifactFormatRegistry()
        versions = registry.all_versions()
        assert versions == []

    def test_multiple_registrations(self) -> None:
        """Test registering multiple versions."""
        registry = ArtifactFormatRegistry()
        registry.register("1.0", "hash1")
        registry.register("1.1", "hash1-patch")
        registry.register("2.0", "hash2")
        versions = registry.all_versions()
        assert len(versions) == 3

    def test_register_overwrites(self) -> None:
        """Test that registering same version overwrites previous."""
        registry = ArtifactFormatRegistry()
        registry.register("1.0", "hash1")
        registry.register("1.0", "hash1-new")
        versions = registry.all_versions()
        assert len(versions) == 1
        assert versions[0].schema_hash == "hash1-new"
