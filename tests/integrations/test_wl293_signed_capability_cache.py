"""Tests for thegent.integrations.signed_capability_cache — Signed Capability Cache.

@trace WL-293
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.signed_capability_cache import (
    SignedCapability,
    SignedCapabilityCache,
)


class TestSignedCapabilityCreation:
    """Test SignedCapability dataclass creation."""

    @pytest.mark.requirement("WL-293")
    def test_create_signed_capability(self) -> None:
        """Can create a SignedCapability with required fields."""
        now = datetime.now(UTC)
        expires = datetime.fromtimestamp(now.timestamp() + 3600, tz=UTC)

        cap = SignedCapability(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123def456",
            created_at=now,
            expires_at=expires,
            last_renewed_at=now,
        )

        assert cap.capability_id == "CAP-001"
        assert cap.connector == "github"
        assert cap.capability_type == "read"
        assert cap.enabled is True
        assert cap.signature == "sig_abc123def456"
        assert cap.created_at == now
        assert cap.expires_at == expires


class TestSignedCapabilityCacheInit:
    """Test SignedCapabilityCache initialization."""

    @pytest.mark.requirement("WL-293")
    def test_init_with_default_ttl(self) -> None:
        """SignedCapabilityCache initializes with default TTL."""
        cache = SignedCapabilityCache()

        assert cache._ttl_seconds == 3600

    @pytest.mark.requirement("WL-293")
    def test_init_with_custom_ttl(self) -> None:
        """SignedCapabilityCache accepts custom TTL."""
        cache = SignedCapabilityCache(ttl_seconds=7200)

        assert cache._ttl_seconds == 7200

    @pytest.mark.requirement("WL-293")
    def test_init_invalid_ttl_raises_error(self) -> None:
        """SignedCapabilityCache raises ValueError for non-positive TTL."""
        with pytest.raises(ValueError, match="ttl_seconds must be positive"):
            SignedCapabilityCache(ttl_seconds=0)

        with pytest.raises(ValueError, match="ttl_seconds must be positive"):
            SignedCapabilityCache(ttl_seconds=-1)


class TestSignedCapabilityCacheStore:
    """Test SignedCapabilityCache.store operations."""

    @pytest.fixture
    def cache(self) -> SignedCapabilityCache:
        """Provide a SignedCapabilityCache instance."""
        return SignedCapabilityCache(ttl_seconds=3600)

    @pytest.mark.requirement("WL-293")
    def test_store_single_capability(self, cache: SignedCapabilityCache) -> None:
        """store adds a capability to cache."""
        cap = cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )

        assert cap.capability_id == "CAP-001"
        assert cap.connector == "github"
        assert cap.enabled is True

    @pytest.mark.requirement("WL-293")
    def test_store_sets_expiry(self, cache: SignedCapabilityCache) -> None:
        """store sets expires_at based on TTL."""
        before = datetime.now(UTC)
        cap = cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )
        after = datetime.now(UTC)

        # expires_at should be approximately TTL from now
        min_expected = datetime.fromtimestamp(before.timestamp() + 3600, tz=UTC)
        max_expected = datetime.fromtimestamp(after.timestamp() + 3600, tz=UTC)

        assert min_expected <= cap.expires_at <= max_expected

    @pytest.mark.requirement("WL-293")
    def test_store_empty_capability_id_raises_error(self, cache: SignedCapabilityCache) -> None:
        """store raises ValueError for empty capability_id."""
        with pytest.raises(ValueError, match="capability_id cannot be empty"):
            cache.store("", "github", "read", True, "sig_abc123")

    @pytest.mark.requirement("WL-293")
    def test_store_empty_connector_raises_error(self, cache: SignedCapabilityCache) -> None:
        """store raises ValueError for empty connector."""
        with pytest.raises(ValueError, match="connector cannot be empty"):
            cache.store("CAP-001", "", "read", True, "sig_abc123")

    @pytest.mark.requirement("WL-293")
    def test_store_empty_capability_type_raises_error(self, cache: SignedCapabilityCache) -> None:
        """store raises ValueError for empty capability_type."""
        with pytest.raises(ValueError, match="capability_type cannot be empty"):
            cache.store("CAP-001", "github", "", True, "sig_abc123")

    @pytest.mark.requirement("WL-293")
    def test_store_empty_signature_raises_error(self, cache: SignedCapabilityCache) -> None:
        """store raises ValueError for empty signature."""
        with pytest.raises(ValueError, match="signature cannot be empty"):
            cache.store("CAP-001", "github", "read", True, "")

    @pytest.mark.requirement("WL-293")
    def test_store_multiple_capabilities(self, cache: SignedCapabilityCache) -> None:
        """store can add multiple capabilities."""
        for i in range(3):
            cache.store(
                capability_id=f"CAP-{i:03d}",
                connector="github",
                capability_type="read",
                enabled=True,
                signature=f"sig_{i}",
            )

        assert len(cache.get_all()) == 3


class TestSignedCapabilityCacheGet:
    """Test SignedCapabilityCache.get operations."""

    @pytest.fixture
    def cache_with_capability(self) -> SignedCapabilityCache:
        """Provide a cache with a stored capability."""
        cache = SignedCapabilityCache(ttl_seconds=3600)
        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )
        return cache

    @pytest.mark.requirement("WL-293")
    def test_get_existing_capability(self, cache_with_capability: SignedCapabilityCache) -> None:
        """get returns existing capability."""
        cap = cache_with_capability.get("CAP-001")

        assert cap is not None
        assert cap.capability_id == "CAP-001"

    @pytest.mark.requirement("WL-293")
    def test_get_nonexistent_capability_returns_none(self, cache_with_capability: SignedCapabilityCache) -> None:
        """get returns None for nonexistent capability."""
        cap = cache_with_capability.get("CAP-999")

        assert cap is None

    @pytest.mark.requirement("WL-293")
    def test_get_expired_capability_returns_none(self) -> None:
        """get returns None for expired capability."""
        cache = SignedCapabilityCache(ttl_seconds=1)
        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )

        # Manually expire the capability
        cap = cache._capabilities["CAP-001"]
        cap.expires_at = datetime.now(UTC)

        result = cache.get("CAP-001")
        assert result is None


class TestSignedCapabilityCacheIsExpired:
    """Test SignedCapabilityCache.is_expired operations."""

    @pytest.fixture
    def cache_with_capability(self) -> SignedCapabilityCache:
        """Provide a cache with a stored capability."""
        cache = SignedCapabilityCache(ttl_seconds=3600)
        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )
        return cache

    @pytest.mark.requirement("WL-293")
    def test_is_expired_false_for_valid(self, cache_with_capability: SignedCapabilityCache) -> None:
        """is_expired returns False for valid capability."""
        assert cache_with_capability.is_expired("CAP-001") is False

    @pytest.mark.requirement("WL-293")
    def test_is_expired_true_for_nonexistent(self, cache_with_capability: SignedCapabilityCache) -> None:
        """is_expired returns True for nonexistent capability."""
        assert cache_with_capability.is_expired("CAP-999") is True

    @pytest.mark.requirement("WL-293")
    def test_is_expired_true_for_expired(self, cache_with_capability: SignedCapabilityCache) -> None:
        """is_expired returns True for expired capability."""
        cap = cache_with_capability._capabilities["CAP-001"]
        cap.expires_at = datetime.now(UTC)

        assert cache_with_capability.is_expired("CAP-001") is True


class TestSignedCapabilityCacheRenew:
    """Test SignedCapabilityCache.renew operations."""

    @pytest.fixture
    def cache_with_capability(self) -> SignedCapabilityCache:
        """Provide a cache with a stored capability."""
        cache = SignedCapabilityCache(ttl_seconds=3600)
        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )
        return cache

    @pytest.mark.requirement("WL-293")
    def test_renew_updates_signature(self, cache_with_capability: SignedCapabilityCache) -> None:
        """renew updates the signature."""
        original_cap = cache_with_capability.get("CAP-001")
        assert original_cap is not None
        assert original_cap.signature == "sig_abc123"

        renewed = cache_with_capability.renew("CAP-001", "sig_new456")

        assert renewed is not None
        assert renewed.signature == "sig_new456"

    @pytest.mark.requirement("WL-293")
    def test_renew_updates_expiry(self, cache_with_capability: SignedCapabilityCache) -> None:
        """renew updates expires_at timestamp."""
        before = cache_with_capability.get("CAP-001")
        assert before is not None
        old_expiry = before.expires_at

        renewed = cache_with_capability.renew("CAP-001", "sig_new456")

        assert renewed is not None
        assert renewed.expires_at > old_expiry

    @pytest.mark.requirement("WL-293")
    def test_renew_updates_last_renewed(self, cache_with_capability: SignedCapabilityCache) -> None:
        """renew updates last_renewed_at timestamp."""
        before = datetime.now(UTC)
        renewed = cache_with_capability.renew("CAP-001", "sig_new456")
        after = datetime.now(UTC)

        assert renewed is not None
        assert before <= renewed.last_renewed_at <= after

    @pytest.mark.requirement("WL-293")
    def test_renew_nonexistent_returns_none(self, cache_with_capability: SignedCapabilityCache) -> None:
        """renew returns None for nonexistent capability."""
        result = cache_with_capability.renew("CAP-999", "sig_new456")

        assert result is None

    @pytest.mark.requirement("WL-293")
    def test_renew_empty_signature_raises_error(self, cache_with_capability: SignedCapabilityCache) -> None:
        """renew raises ValueError for empty signature."""
        with pytest.raises(ValueError, match="signature cannot be empty"):
            cache_with_capability.renew("CAP-001", "")


class TestSignedCapabilityCacheListConnectorCapabilities:
    """Test SignedCapabilityCache.list_connector_capabilities operations."""

    @pytest.fixture
    def cache_with_mixed_capabilities(self) -> SignedCapabilityCache:
        """Provide a cache with multiple connectors."""
        cache = SignedCapabilityCache(ttl_seconds=3600)

        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_1",
        )
        cache.store(
            capability_id="CAP-002",
            connector="github",
            capability_type="write",
            enabled=True,
            signature="sig_2",
        )
        cache.store(
            capability_id="CAP-003",
            connector="linear",
            capability_type="read",
            enabled=True,
            signature="sig_3",
        )

        return cache

    @pytest.mark.requirement("WL-293")
    def test_list_connector_capabilities_github(self, cache_with_mixed_capabilities: SignedCapabilityCache) -> None:
        """list_connector_capabilities returns only github capabilities."""
        caps = cache_with_mixed_capabilities.list_connector_capabilities("github")

        assert len(caps) == 2
        assert all(c.connector == "github" for c in caps)

    @pytest.mark.requirement("WL-293")
    def test_list_connector_capabilities_linear(self, cache_with_mixed_capabilities: SignedCapabilityCache) -> None:
        """list_connector_capabilities returns only linear capabilities."""
        caps = cache_with_mixed_capabilities.list_connector_capabilities("linear")

        assert len(caps) == 1
        assert caps[0].connector == "linear"

    @pytest.mark.requirement("WL-293")
    def test_list_connector_capabilities_nonexistent(
        self, cache_with_mixed_capabilities: SignedCapabilityCache
    ) -> None:
        """list_connector_capabilities returns empty for nonexistent connector."""
        caps = cache_with_mixed_capabilities.list_connector_capabilities("slack")

        assert caps == []


class TestSignedCapabilityCacheInvalidate:
    """Test SignedCapabilityCache.invalidate operations."""

    @pytest.fixture
    def cache_with_capability(self) -> SignedCapabilityCache:
        """Provide a cache with a stored capability."""
        cache = SignedCapabilityCache()
        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )
        return cache

    @pytest.mark.requirement("WL-293")
    def test_invalidate_removes_capability(self, cache_with_capability: SignedCapabilityCache) -> None:
        """invalidate removes capability from cache."""
        assert cache_with_capability.get("CAP-001") is not None

        result = cache_with_capability.invalidate("CAP-001")

        assert result is True
        assert cache_with_capability.get("CAP-001") is None

    @pytest.mark.requirement("WL-293")
    def test_invalidate_nonexistent_returns_false(self, cache_with_capability: SignedCapabilityCache) -> None:
        """invalidate returns False for nonexistent capability."""
        result = cache_with_capability.invalidate("CAP-999")

        assert result is False


class TestSignedCapabilityCacheCleanupExpired:
    """Test SignedCapabilityCache.cleanup_expired operations."""

    @pytest.mark.requirement("WL-293")
    def test_cleanup_expired_removes_expired(self) -> None:
        """cleanup_expired removes expired capabilities."""
        cache = SignedCapabilityCache(ttl_seconds=3600)

        # Add one valid capability
        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_1",
        )

        # Add one expired capability manually
        now = datetime.now(UTC)
        expired_cap = SignedCapability(
            capability_id="CAP-002",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_2",
            created_at=now,
            expires_at=datetime.fromtimestamp(now.timestamp() - 1, tz=UTC),
            last_renewed_at=now,
        )
        cache._capabilities["CAP-002"] = expired_cap

        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.get("CAP-001") is not None
        assert cache.get("CAP-002") is None

    @pytest.mark.requirement("WL-293")
    def test_cleanup_expired_no_expired(self) -> None:
        """cleanup_expired returns 0 when no expired capabilities."""
        cache = SignedCapabilityCache()
        cache.store(
            capability_id="CAP-001",
            connector="github",
            capability_type="read",
            enabled=True,
            signature="sig_abc123",
        )

        removed = cache.cleanup_expired()

        assert removed == 0


class TestSignedCapabilityCacheGetAll:
    """Test SignedCapabilityCache.get_all operations."""

    @pytest.mark.requirement("WL-293")
    def test_get_all_empty_cache(self) -> None:
        """get_all returns empty list for empty cache."""
        cache = SignedCapabilityCache()

        assert cache.get_all() == []

    @pytest.mark.requirement("WL-293")
    def test_get_all_returns_all_capabilities(self) -> None:
        """get_all returns all capabilities."""
        cache = SignedCapabilityCache()

        for i in range(3):
            cache.store(
                capability_id=f"CAP-{i:03d}",
                connector="github",
                capability_type="read",
                enabled=True,
                signature=f"sig_{i}",
            )

        all_caps = cache.get_all()

        assert len(all_caps) == 3
