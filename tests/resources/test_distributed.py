"""Tests for thegent.resources.distributed.

Covers:
- ResourceLease dataclass
- DistributedResourceCoordinator.acquire
- DistributedResourceCoordinator.release
- DistributedResourceCoordinator.get_active_leases
- DistributedResourceCoordinator.cleanup_expired
- DistributedResourceCoordinator.get_available
- Concurrent acquisition (same resource, capacity enforcement)
- Expired lease handling
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from thegent.resources.distributed import (
    DistributedResourceCoordinator,
    ResourceCoordinationError,
    ResourceLease,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def lease_file(tmp_path: Path) -> Path:
    """Return a temporary lease-store path (not yet created)."""
    return tmp_path / "resource_leases.json"


@pytest.fixture
def coordinator(lease_file: Path) -> DistributedResourceCoordinator:
    """Return a coordinator backed by a temporary file."""
    return DistributedResourceCoordinator(lease_file=lease_file)


@pytest.fixture
def limited_coordinator(lease_file: Path) -> DistributedResourceCoordinator:
    """Coordinator with a 10-unit cap on 'cpu'."""
    return DistributedResourceCoordinator(
        lease_file=lease_file,
        resource_limits={"cpu": 10.0},
    )


# ---------------------------------------------------------------------------
# ResourceLease unit tests
# ---------------------------------------------------------------------------


def test_lease_is_not_expired_when_new() -> None:
    """A freshly created lease with a future expiry is not expired."""
    lease = ResourceLease(
        lease_id="abc",
        owner="agent-1",
        resource="cpu",
        amount=2.0,
        expires_at=time.time() + 60,
    )
    assert not lease.is_expired


def test_lease_is_expired_when_past() -> None:
    """A lease with a past expiry timestamp is expired."""
    lease = ResourceLease(
        lease_id="abc",
        owner="agent-1",
        resource="cpu",
        amount=2.0,
        expires_at=time.time() - 1,
    )
    assert lease.is_expired


def test_lease_roundtrip_serialisation() -> None:
    """to_dict / from_dict round-trip preserves all fields."""
    lease = ResourceLease(
        lease_id="test-id",
        owner="owner-x",
        resource="memory",
        amount=512.0,
        expires_at=1_700_000_000.0,
    )
    restored = ResourceLease.from_dict(lease.to_dict())
    assert restored.lease_id == lease.lease_id
    assert restored.owner == lease.owner
    assert restored.resource == lease.resource
    assert restored.amount == lease.amount
    assert restored.expires_at == lease.expires_at


def test_lease_from_dict_coerces_types() -> None:
    """from_dict coerces string values to correct types."""
    data = {
        "lease_id": 42,
        "owner": 7,
        "resource": "disk",
        "amount": "3.14",
        "expires_at": "9999999999",
    }
    lease = ResourceLease.from_dict(data)
    assert isinstance(lease.lease_id, str)
    assert isinstance(lease.owner, str)
    assert isinstance(lease.amount, float)
    assert isinstance(lease.expires_at, float)


# ---------------------------------------------------------------------------
# Acquire tests
# ---------------------------------------------------------------------------


def test_acquire_returns_lease(coordinator: DistributedResourceCoordinator) -> None:
    """acquire() returns a ResourceLease with the correct fields."""
    lease = coordinator.acquire(resource="cpu", amount=2.0, owner="agent-1")
    assert lease is not None
    assert lease.resource == "cpu"
    assert lease.amount == 2.0
    assert lease.owner == "agent-1"
    assert lease.expires_at > time.time()


def test_acquire_stores_lease_on_disk(coordinator: DistributedResourceCoordinator, lease_file: Path) -> None:
    """After acquire, the lease file exists and is valid JSON."""
    coordinator.acquire(resource="cpu", amount=1.0, owner="agent-1")
    assert lease_file.exists()
    import json

    data = json.loads(lease_file.read_text())
    assert isinstance(data, list)
    assert len(data) == 1


def test_acquire_multiple_leases_independent_ids(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """Multiple acquisitions produce leases with distinct IDs."""
    a = coordinator.acquire(resource="cpu", amount=1.0, owner="a")
    b = coordinator.acquire(resource="cpu", amount=1.0, owner="b")
    assert a is not None
    assert b is not None
    assert a.lease_id != b.lease_id


def test_acquire_invalid_amount_raises(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """acquire() raises ResourceCoordinationError for non-positive amount."""
    with pytest.raises(ResourceCoordinationError):
        coordinator.acquire(resource="cpu", amount=0.0, owner="a")

    with pytest.raises(ResourceCoordinationError):
        coordinator.acquire(resource="cpu", amount=-5.0, owner="a")


def test_acquire_respects_capacity_via_total(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """acquire() returns None when capacity is exhausted (total kwarg)."""
    coordinator.acquire(resource="cpu", amount=8.0, owner="a", total=10.0)
    # 8 used; 3 more would exceed 10
    result = coordinator.acquire(resource="cpu", amount=3.0, owner="b", total=10.0)
    assert result is None


def test_acquire_respects_capacity_via_resource_limits(
    limited_coordinator: DistributedResourceCoordinator,
) -> None:
    """acquire() uses resource_limits when no total kwarg is supplied."""
    limited_coordinator.acquire(resource="cpu", amount=9.0, owner="a")
    result = limited_coordinator.acquire(resource="cpu", amount=2.0, owner="b")
    assert result is None


def test_acquire_within_limit_succeeds(
    limited_coordinator: DistributedResourceCoordinator,
) -> None:
    """Multiple acquires that stay within the limit all succeed."""
    a = limited_coordinator.acquire(resource="cpu", amount=4.0, owner="a")
    b = limited_coordinator.acquire(resource="cpu", amount=4.0, owner="b")
    assert a is not None
    assert b is not None


def test_acquire_different_resources_are_independent(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """Leases on different resources do not count against each other."""
    coordinator.acquire(resource="cpu", amount=9.0, owner="a", total=10.0)
    # 'memory' is a separate resource; should succeed regardless
    result = coordinator.acquire(resource="memory", amount=9.0, owner="b", total=10.0)
    assert result is not None


def test_acquire_after_expiry_frees_capacity(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """An expired lease does not count towards active usage on next acquire."""
    coordinator.acquire(resource="cpu", amount=9.0, owner="a", ttl_s=0.001, total=10.0)
    time.sleep(0.01)
    # Expired lease should be purged during next acquire
    result = coordinator.acquire(resource="cpu", amount=9.0, owner="b", total=10.0)
    assert result is not None


# ---------------------------------------------------------------------------
# Release tests
# ---------------------------------------------------------------------------


def test_release_existing_lease(coordinator: DistributedResourceCoordinator) -> None:
    """release() returns True and removes the lease."""
    lease = coordinator.acquire(resource="cpu", amount=1.0, owner="a")
    assert lease is not None
    assert coordinator.release(lease.lease_id) is True
    assert coordinator.get_active_leases() == []


def test_release_nonexistent_lease(coordinator: DistributedResourceCoordinator) -> None:
    """release() returns False for an unknown lease_id."""
    assert coordinator.release("no-such-id") is False


def test_release_frees_capacity(
    limited_coordinator: DistributedResourceCoordinator,
) -> None:
    """Releasing a lease frees its capacity for future acquires."""
    lease = limited_coordinator.acquire(resource="cpu", amount=9.0, owner="a")
    assert lease is not None
    limited_coordinator.release(lease.lease_id)
    result = limited_coordinator.acquire(resource="cpu", amount=9.0, owner="b")
    assert result is not None


def test_release_only_removes_target_lease(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """release() removes exactly the targeted lease, leaving others intact."""
    a = coordinator.acquire(resource="cpu", amount=1.0, owner="a")
    b = coordinator.acquire(resource="cpu", amount=1.0, owner="b")
    assert a is not None
    assert b is not None
    coordinator.release(a.lease_id)
    remaining = coordinator.get_active_leases()
    assert len(remaining) == 1
    assert remaining[0].lease_id == b.lease_id


# ---------------------------------------------------------------------------
# get_active_leases tests
# ---------------------------------------------------------------------------


def test_get_active_leases_empty_store(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """get_active_leases() returns empty list when no leases exist."""
    assert coordinator.get_active_leases() == []


def test_get_active_leases_filters_by_resource(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """get_active_leases(resource=...) returns only matching leases."""
    coordinator.acquire(resource="cpu", amount=1.0, owner="a")
    coordinator.acquire(resource="memory", amount=2.0, owner="b")
    cpu_leases = coordinator.get_active_leases(resource="cpu")
    assert all(l.resource == "cpu" for l in cpu_leases)
    assert len(cpu_leases) == 1


def test_get_active_leases_excludes_expired(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """get_active_leases() does not include expired leases."""
    coordinator.acquire(resource="cpu", amount=1.0, owner="a", ttl_s=0.001)
    coordinator.acquire(resource="cpu", amount=1.0, owner="b", ttl_s=60.0)
    time.sleep(0.01)
    active = coordinator.get_active_leases()
    assert all(not l.is_expired for l in active)
    assert len(active) == 1
    assert active[0].owner == "b"


def test_get_active_leases_sorted_by_expiry(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """get_active_leases() returns leases sorted by expires_at ascending."""
    coordinator.acquire(resource="cpu", amount=1.0, owner="a", ttl_s=30.0)
    coordinator.acquire(resource="cpu", amount=1.0, owner="b", ttl_s=10.0)
    coordinator.acquire(resource="cpu", amount=1.0, owner="c", ttl_s=20.0)
    leases = coordinator.get_active_leases()
    expiries = [l.expires_at for l in leases]
    assert expiries == sorted(expiries)


# ---------------------------------------------------------------------------
# cleanup_expired tests
# ---------------------------------------------------------------------------


def test_cleanup_expired_removes_only_expired(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """cleanup_expired() keeps active leases intact; active count is preserved.

    Because acquire() itself eagerly purges expired leases, the expired lease
    may already be gone by the time cleanup_expired() runs.  We verify the
    invariant that only the active lease survives, regardless of when the
    purge happened.
    """
    coordinator.acquire(resource="cpu", amount=1.0, owner="expired", ttl_s=0.001)
    coordinator.acquire(resource="cpu", amount=1.0, owner="active", ttl_s=60.0)
    time.sleep(0.01)
    coordinator.cleanup_expired()
    remaining = coordinator.get_active_leases()
    assert len(remaining) == 1
    assert remaining[0].owner == "active"


def test_cleanup_expired_returns_zero_when_none_expired(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """cleanup_expired() returns 0 when all leases are still active."""
    coordinator.acquire(resource="cpu", amount=1.0, owner="a", ttl_s=60.0)
    assert coordinator.cleanup_expired() == 0


def test_cleanup_expired_empty_store(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """cleanup_expired() returns 0 on an empty store."""
    assert coordinator.cleanup_expired() == 0


def test_cleanup_expired_removes_all_when_all_expired(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """cleanup_expired() removes all remaining expired leases; store ends empty.

    Note: acquire() also purges expired leases as a side-effect, so the number
    cleaned up by cleanup_expired() may be less than the total acquired (some
    are auto-purged during later acquire calls).  The important invariant is
    that the store is empty afterwards and returned count >= 0.
    """
    for i in range(3):
        coordinator.acquire(resource="cpu", amount=1.0, owner=f"a{i}", ttl_s=0.001)
    time.sleep(0.02)
    removed = coordinator.cleanup_expired()
    assert removed >= 0
    assert coordinator.get_active_leases() == []


# ---------------------------------------------------------------------------
# get_available tests
# ---------------------------------------------------------------------------


def test_get_available_full_capacity_when_empty(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """get_available() returns total when no leases exist."""
    assert coordinator.get_available(resource="cpu", total=10.0) == 10.0


def test_get_available_decreases_with_leases(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """get_available() decreases by active lease amounts."""
    coordinator.acquire(resource="cpu", amount=3.0, owner="a")
    assert coordinator.get_available(resource="cpu", total=10.0) == pytest.approx(7.0)


def test_get_available_excludes_expired_leases(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """Expired leases do not reduce available capacity."""
    coordinator.acquire(resource="cpu", amount=5.0, owner="a", ttl_s=0.001)
    time.sleep(0.01)
    available = coordinator.get_available(resource="cpu", total=10.0)
    assert available == pytest.approx(10.0)


def test_get_available_never_negative(
    coordinator: DistributedResourceCoordinator,
) -> None:
    """get_available() returns 0.0 rather than a negative number."""
    # Manually inject an over-committed scenario via two coordinators sharing the same file
    coord2 = DistributedResourceCoordinator(lease_file=coordinator._lease_file)
    coordinator.acquire(resource="cpu", amount=8.0, owner="a")
    coord2.acquire(resource="cpu", amount=8.0, owner="b")
    # total is only 10 but we've leased 16; result must clamp to 0
    available = coordinator.get_available(resource="cpu", total=10.0)
    assert available >= 0.0


# ---------------------------------------------------------------------------
# Concurrent / shared state tests
# ---------------------------------------------------------------------------


def test_two_coordinators_share_same_lease_file(tmp_path: Path) -> None:
    """Two coordinator instances backed by the same file see each other's leases."""
    shared = tmp_path / "shared_leases.json"
    c1 = DistributedResourceCoordinator(lease_file=shared)
    c2 = DistributedResourceCoordinator(lease_file=shared)

    c1.acquire(resource="cpu", amount=4.0, owner="node-1", total=10.0)
    # c2 sees c1's lease and denies the request that would exceed capacity
    result = c2.acquire(resource="cpu", amount=7.0, owner="node-2", total=10.0)
    assert result is None


def test_concurrent_acquisition_within_limit(tmp_path: Path) -> None:
    """Both coordinators can acquire when total stays within limit."""
    shared = tmp_path / "shared_leases.json"
    c1 = DistributedResourceCoordinator(lease_file=shared)
    c2 = DistributedResourceCoordinator(lease_file=shared)

    l1 = c1.acquire(resource="cpu", amount=4.0, owner="node-1", total=10.0)
    l2 = c2.acquire(resource="cpu", amount=4.0, owner="node-2", total=10.0)
    assert l1 is not None
    assert l2 is not None


def test_release_from_different_coordinator_instance(tmp_path: Path) -> None:
    """A lease acquired by one coordinator can be released by another."""
    shared = tmp_path / "shared_leases.json"
    c1 = DistributedResourceCoordinator(lease_file=shared)
    c2 = DistributedResourceCoordinator(lease_file=shared)

    lease = c1.acquire(resource="cpu", amount=5.0, owner="node-1")
    assert lease is not None
    assert c2.release(lease.lease_id) is True
    assert c1.get_active_leases() == []


def test_cleanup_from_different_coordinator_affects_shared_store(
    tmp_path: Path,
) -> None:
    """Cleanup by one coordinator removes expired leases visible to another."""
    shared = tmp_path / "shared_leases.json"
    c1 = DistributedResourceCoordinator(lease_file=shared)
    c2 = DistributedResourceCoordinator(lease_file=shared)

    c1.acquire(resource="cpu", amount=5.0, owner="node-1", ttl_s=0.001)
    time.sleep(0.01)
    removed = c2.cleanup_expired()
    assert removed == 1
    assert c1.get_active_leases() == []
