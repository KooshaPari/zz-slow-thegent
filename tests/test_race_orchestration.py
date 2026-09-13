"""Thread-safety tests for ResourcePool.

FR-ORCH-001: ResourcePool must serialise concurrent allocate() calls so that
capacity is never over-committed.
"""

from __future__ import annotations

import threading

import pytest


@pytest.mark.requirement("FR-ORCH-001")
def test_resource_allocation_no_race() -> None:
    """50 concurrent threads compete for a pool of capacity=1.

    Exactly 1 must succeed and 49 must receive ResourceAllocationError.
    This deterministically fails if the lock is removed from ResourcePool.
    """
    from thegent.orchestration.resource.pool import (
        ResourceAllocationError,
        ResourcePool,
    )

    pool = ResourcePool(capacity=1)
    errors: list[Exception] = []
    successes: list[object] = []

    barrier = threading.Barrier(50)

    def allocate() -> None:
        barrier.wait()
        try:
            result = pool.allocate("agent-x", amount=1)
            successes.append(result)
        except ResourceAllocationError as e:
            errors.append(e)

    threads = [threading.Thread(target=allocate) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(successes) == 1, (
        f"Expected exactly 1 successful allocation, got {len(successes)}"
    )
    assert len(errors) == 49, f"Expected 49 failures, got {len(errors)}"


@pytest.mark.requirement("FR-ORCH-001")
def test_resource_pool_release_allows_reallocation() -> None:
    """After releasing, the pool must accept a new allocation."""
    from thegent.orchestration.resource.pool import ResourcePool

    pool = ResourcePool(capacity=1)
    pool.allocate("agent-a", amount=1)
    pool.release(amount=1)
    result = pool.allocate("agent-b", amount=1)
    assert result["agent_id"] == "agent-b"


@pytest.mark.requirement("FR-ORCH-001")
def test_resource_pool_available_tracks_allocations() -> None:
    """available property reflects current allocation state."""
    from thegent.orchestration.resource.pool import ResourcePool

    pool = ResourcePool(capacity=5)
    assert pool.available == 5
    pool.allocate("a", amount=3)
    assert pool.available == 2
    pool.release(amount=2)
    assert pool.available == 4


@pytest.mark.requirement("FR-ORCH-001")
def test_resource_pool_over_capacity_raises() -> None:
    """Allocating more than capacity must raise ResourceAllocationError."""
    from thegent.orchestration.resource.pool import (
        ResourceAllocationError,
        ResourcePool,
    )

    pool = ResourcePool(capacity=2)
    pool.allocate("a", amount=2)
    with pytest.raises(ResourceAllocationError):
        pool.allocate("b", amount=1)
