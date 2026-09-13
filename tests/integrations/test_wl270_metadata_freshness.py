"""Tests for thegent.integrations.metadata_freshness — TTL-based metadata caching.

@trace WL-270
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest

from thegent.integrations.metadata_freshness import (
    MetadataFreshnessTTL,
    MetadataRecord,
)


class TestMetadataRecord:
    """Test MetadataRecord dataclass. @trace WL-270"""

    @pytest.mark.requirement("WL-270")
    def test_create_record(self) -> None:
        """Can create a MetadataRecord with all fields."""
        now = datetime.now(UTC)
        record = MetadataRecord(key="api_version", value="v2.5", fetched_at=now)

        assert record.key == "api_version"
        assert record.value == "v2.5"
        assert record.fetched_at == now

    @pytest.mark.requirement("WL-270")
    def test_record_with_different_values(self) -> None:
        """MetadataRecord can hold various string values."""
        now = datetime.now(UTC)
        test_cases = [
            ("empty", ""),
            ("whitespace", "   "),
            ("long", "x" * 1000),
            ("special", "!@#$%^&*()"),
        ]

        for key, value in test_cases:
            record = MetadataRecord(key=key, value=value, fetched_at=now)
            assert record.key == key
            assert record.value == value


class TestMetadataFreshnessTTL:
    """Test MetadataFreshnessTTL operations. @trace WL-270"""

    @pytest.mark.requirement("WL-270")
    def test_init_default(self) -> None:
        """Can initialize with default TTL (300 seconds)."""
        ttl = MetadataFreshnessTTL()
        assert ttl._ttl_seconds == 300.0

    @pytest.mark.requirement("WL-270")
    def test_init_custom_ttl(self) -> None:
        """Can initialize with custom TTL."""
        ttl = MetadataFreshnessTTL(ttl_seconds=60.0)
        assert ttl._ttl_seconds == 60.0

    @pytest.mark.requirement("WL-270")
    def test_init_invalid_ttl(self) -> None:
        """Raises ValueError for invalid TTL values."""
        with pytest.raises(ValueError, match=r"ttl_seconds must be > 0\.0"):
            MetadataFreshnessTTL(ttl_seconds=0.0)
        with pytest.raises(ValueError, match=r"ttl_seconds must be > 0\.0"):
            MetadataFreshnessTTL(ttl_seconds=-1.0)

    @pytest.mark.requirement("WL-270")
    def test_put_and_get_fresh(self) -> None:
        """Can put and retrieve fresh metadata."""
        ttl = MetadataFreshnessTTL(ttl_seconds=300.0)
        record = ttl.put("api_key", "secret123")

        assert record.key == "api_key"
        assert record.value == "secret123"
        assert record.fetched_at is not None

        retrieved = ttl.get("api_key")
        assert retrieved == "secret123"

    @pytest.mark.requirement("WL-270")
    def test_get_nonexistent(self) -> None:
        """Returns None for non-existent keys."""
        ttl = MetadataFreshnessTTL()
        assert ttl.get("nonexistent") is None

    @pytest.mark.requirement("WL-270")
    def test_put_overwrites(self) -> None:
        """Putting same key overwrites previous value."""
        ttl = MetadataFreshnessTTL()
        ttl.put("config", "v1")
        ttl.put("config", "v2")

        assert ttl.get("config") == "v2"

    @pytest.mark.requirement("WL-270")
    def test_is_fresh_when_young(self) -> None:
        """is_fresh returns True for recent records."""
        ttl = MetadataFreshnessTTL(ttl_seconds=10.0)
        ttl.put("test", "value")
        assert ttl.is_fresh("test") is True

    @pytest.mark.requirement("WL-270")
    def test_is_fresh_when_expired(self) -> None:
        """is_fresh returns False for expired records."""
        ttl = MetadataFreshnessTTL(ttl_seconds=0.1)
        ttl.put("test", "value")
        time.sleep(0.15)
        assert ttl.is_fresh("test") is False

    @pytest.mark.requirement("WL-270")
    def test_is_fresh_nonexistent(self) -> None:
        """is_fresh returns False for non-existent keys."""
        ttl = MetadataFreshnessTTL()
        assert ttl.is_fresh("nonexistent") is False

    @pytest.mark.requirement("WL-270")
    def test_get_expired_returns_none(self) -> None:
        """get returns None and removes expired records."""
        ttl = MetadataFreshnessTTL(ttl_seconds=0.1)
        ttl.put("test", "value")
        time.sleep(0.15)

        result = ttl.get("test")
        assert result is None
        assert ttl.is_fresh("test") is False

    @pytest.mark.requirement("WL-270")
    def test_evict_stale_empty(self) -> None:
        """evict_stale returns 0 when no stale records."""
        ttl = MetadataFreshnessTTL(ttl_seconds=60.0)
        ttl.put("fresh", "value")
        evicted = ttl.evict_stale()
        assert evicted == 0

    @pytest.mark.requirement("WL-270")
    def test_evict_stale_with_expiration(self) -> None:
        """evict_stale removes all expired records."""
        ttl = MetadataFreshnessTTL(ttl_seconds=0.1)
        ttl.put("old1", "value1")
        ttl.put("old2", "value2")
        time.sleep(0.15)
        ttl.put("fresh", "value3")

        evicted = ttl.evict_stale()
        assert evicted == 2
        assert ttl.get("fresh") == "value3"
        assert ttl.get("old1") is None
        assert ttl.get("old2") is None

    @pytest.mark.requirement("WL-270")
    def test_multiple_keys_independent(self) -> None:
        """Different keys have independent TTL tracking."""
        ttl = MetadataFreshnessTTL(ttl_seconds=0.2)
        ttl.put("fast", "value1")
        time.sleep(0.1)
        ttl.put("slow", "value2")
        time.sleep(0.15)

        assert ttl.get("fast") is None
        assert ttl.get("slow") == "value2"

    @pytest.mark.requirement("WL-270")
    def test_ttl_boundary_condition(self) -> None:
        """Records expire at exactly TTL boundary."""
        ttl = MetadataFreshnessTTL(ttl_seconds=0.2)
        _ = ttl.put("boundary", "value")
        time.sleep(0.21)

        result = ttl.get("boundary")
        assert result is None


class TestMetadataFreshnessTTLIntegration:
    """Integration tests for MetadataFreshnessTTL. @trace WL-270"""

    @pytest.mark.requirement("WL-270")
    def test_mixed_operations_sequence(self) -> None:
        """Complex sequence of put, get, evict operations."""
        ttl = MetadataFreshnessTTL(ttl_seconds=1.0)

        # Add initial records
        ttl.put("db_version", "3.2")
        ttl.put("api_endpoint", "https://api.example.com")
        ttl.put("timeout", "30")

        # All should be fresh
        assert ttl.get("db_version") == "3.2"
        assert ttl.get("api_endpoint") == "https://api.example.com"
        assert ttl.get("timeout") == "30"

        # Wait for partial expiration
        time.sleep(0.5)
        ttl.put("new_config", "v2")

        # Wait for first batch to expire
        time.sleep(0.6)

        # Old ones expired, new one fresh
        assert ttl.get("db_version") is None
        assert ttl.get("new_config") == "v2"

        # Evict any remaining stale
        evicted = ttl.evict_stale()
        assert evicted >= 0

    @pytest.mark.requirement("WL-270")
    def test_concurrent_key_updates(self) -> None:
        """Updating same key multiple times maintains freshness."""
        ttl = MetadataFreshnessTTL(ttl_seconds=1.0)

        ttl.put("counter", "1")
        time.sleep(0.2)
        ttl.put("counter", "2")
        time.sleep(0.2)
        ttl.put("counter", "3")

        # Last update should be fresh
        assert ttl.get("counter") == "3"
        assert ttl.is_fresh("counter") is True
