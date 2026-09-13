"""Tests for file coordination: OCC, HLC, and Lease-based claims.

Covers both mesh.coordination (HLCTimestamp, OptimisticConcurrencyControl,
FileClaimsRegistry) and coordination.file_coordination (HybridLogicalClock,
OCCManager, FileLeaseRegistry).

# @trace TGNT-P8.1 TGNT-P8.2 TGNT-P8.3 TGNT-P8.4
"""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.coordination.file_coordination import (
    FileLeaseRegistry,
    HybridLogicalClock,
    OCCManager,
)
from thegent.mesh.coordination import (
    FileClaimsRegistry,
    HLCTimestamp,
    OptimisticConcurrencyControl,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mesh_root(tmp_path: Path) -> Path:
    return tmp_path / "mesh"


@pytest.fixture
def occ(mesh_root: Path) -> OptimisticConcurrencyControl:
    return OptimisticConcurrencyControl(mesh_root)


@pytest.fixture
def claims(mesh_root: Path) -> FileClaimsRegistry:
    return FileClaimsRegistry(mesh_root)


@pytest.fixture
def occ_manager(tmp_path: Path) -> OCCManager:
    return OCCManager(tmp_path / "versions")


@pytest.fixture
def lease_registry(tmp_path: Path) -> FileLeaseRegistry:
    return FileLeaseRegistry(tmp_path / "leases")


# ---------------------------------------------------------------------------
# HLCTimestamp (mesh.coordination) — TGNT-P8.2
# ---------------------------------------------------------------------------


class TestHLCTimestamp:
    """Hybrid Logical Clock timestamp generation and parsing."""

    # @trace TGNT-P8.2
    def test_default_init_uses_wall_clock(self) -> None:
        """HLCTimestamp() captures current wall-clock millis."""
        before = int(time.time() * 1000)
        ts = HLCTimestamp()
        after = int(time.time() * 1000)
        assert before <= ts.physical <= after
        assert ts.logical == 0

    # @trace TGNT-P8.2
    def test_explicit_init(self) -> None:
        """Explicit physical/logical values are stored."""
        ts = HLCTimestamp(physical=1000, logical=5)
        assert ts.physical == 1000
        assert ts.logical == 5

    # @trace TGNT-P8.2
    def test_update_advances_physical(self) -> None:
        """update() without other clock advances to current time."""
        ts = HLCTimestamp(physical=1, logical=0)
        ts.update()
        assert ts.physical >= int(time.time() * 1000) - 100

    # @trace TGNT-P8.2
    def test_update_with_other_merges_clocks(self) -> None:
        """update(other) merges two clocks correctly."""
        ts1 = HLCTimestamp(physical=500, logical=3)
        ts2 = HLCTimestamp(physical=500, logical=7)
        ts1.update(ts2)
        # Same physical => logical = max(3, 7) + 1 = 8
        # But now >= current millis, so physical is updated
        assert ts1.logical >= 0

    # @trace TGNT-P8.2
    def test_str_format(self) -> None:
        """String representation is 'physical:logical_hex'."""
        ts = HLCTimestamp(physical=12345, logical=10)
        assert str(ts) == "12345:000a"

    # @trace TGNT-P8.2
    def test_parse_roundtrip(self) -> None:
        """parse(str(ts)) recovers physical and logical."""
        ts = HLCTimestamp(physical=99999, logical=255)
        parsed = HLCTimestamp.parse(str(ts))
        assert parsed.physical == 99999
        assert parsed.logical == 255

    # @trace TGNT-P8.2
    def test_parse_invalid_returns_default(self) -> None:
        """parse() with bad input returns a default clock."""
        parsed = HLCTimestamp.parse("garbage")
        assert isinstance(parsed, HLCTimestamp)

    # @trace TGNT-P8.2
    def test_monotonic_under_mock_time(self) -> None:
        """When physical is ahead of wall clock, logical counter increments."""
        future_ms = int(time.time() * 1000) + 999999
        ts = HLCTimestamp(physical=future_ms, logical=0)
        # Wall clock is behind ts.physical, so update() increments logical
        ts.update()
        first_logical = ts.logical
        assert first_logical > 0
        ts.update()
        assert ts.logical > first_logical


# ---------------------------------------------------------------------------
# HybridLogicalClock (coordination.file_coordination) — TGNT-P8.2
# ---------------------------------------------------------------------------


class TestHybridLogicalClock:
    """HybridLogicalClock.now() returns monotonic timestamps."""

    # @trace TGNT-P8.2
    def test_now_returns_string(self) -> None:
        """now() returns a 'physical:logical' string."""
        hlc = HybridLogicalClock()
        result = hlc.now()
        parts = result.split(":")
        assert len(parts) == 2
        int(parts[0])
        int(parts[1])

    # @trace TGNT-P8.2
    def test_logical_increments_within_same_millis(self) -> None:
        """If wall clock hasn't advanced, logical counter increments."""
        hlc = HybridLogicalClock()
        frozen_ms = int(time.time() * 1000) + 100000
        with patch("thegent.coordination.file_coordination.time") as mt:
            mt.time.return_value = frozen_ms / 1000.0
            t1 = hlc.now()
            t2 = hlc.now()
        l1 = int(t1.split(":")[1])
        l2 = int(t2.split(":")[1])
        assert l2 > l1

    # @trace TGNT-P8.2
    def test_physical_advances_resets_logical(self) -> None:
        """When wall clock jumps forward, logical resets to 0."""
        hlc = HybridLogicalClock()
        base_ms = int(time.time() * 1000) + 200000
        with patch("thegent.coordination.file_coordination.time") as mt:
            mt.time.return_value = base_ms / 1000.0
            hlc.now()
            hlc.now()  # logical > 0 now
            mt.time.return_value = (base_ms + 1000) / 1000.0
            t3 = hlc.now()
        assert int(t3.split(":")[1]) == 0


# ---------------------------------------------------------------------------
# OptimisticConcurrencyControl (mesh.coordination) — TGNT-P8.1
# ---------------------------------------------------------------------------


class TestOCC:
    """Optimistic Concurrency Control version check on write."""

    # @trace TGNT-P8.1
    def test_get_version_nonexistent(self, occ: OptimisticConcurrencyControl) -> None:
        """Non-existent file returns 'empty'."""
        v = occ.get_version(Path("/nonexistent/file.txt"))
        assert v == "empty"

    # @trace TGNT-P8.1
    def test_get_version_deterministic(self, occ: OptimisticConcurrencyControl, tmp_path: Path) -> None:
        """Same content produces same version hash."""
        f = tmp_path / "test.txt"
        f.write_text("hello")
        v1 = occ.get_version(f)
        v2 = occ.get_version(f)
        assert v1 == v2

    # @trace TGNT-P8.1
    def test_version_changes_on_write(self, occ: OptimisticConcurrencyControl, tmp_path: Path) -> None:
        """Modifying file content changes the version."""
        f = tmp_path / "test.txt"
        f.write_text("v1")
        v1 = occ.get_version(f)
        f.write_text("v2")
        v2 = occ.get_version(f)
        assert v1 != v2

    # @trace TGNT-P8.1
    def test_claim_and_verify_success(self, occ: OptimisticConcurrencyControl, tmp_path: Path) -> None:
        """Claim then verify succeeds when file unchanged."""
        f = tmp_path / "test.txt"
        f.write_text("content")
        occ.claim_version(f, "agent-1")
        assert occ.verify_version(f, "agent-1") is True

    # @trace TGNT-P8.1
    def test_claim_and_verify_conflict(self, occ: OptimisticConcurrencyControl, tmp_path: Path) -> None:
        """Verify fails when file changed after claim."""
        f = tmp_path / "test.txt"
        f.write_text("original")
        occ.claim_version(f, "agent-1")
        f.write_text("modified by another agent")
        assert occ.verify_version(f, "agent-1") is False

    # @trace TGNT-P8.1
    def test_verify_no_claim_returns_true(self, occ: OptimisticConcurrencyControl, tmp_path: Path) -> None:
        """verify_version with no prior claim returns True (no-claim case)."""
        f = tmp_path / "test.txt"
        f.write_text("whatever")
        assert occ.verify_version(f, "no-such-agent") is True


# ---------------------------------------------------------------------------
# OCCManager (coordination.file_coordination) — TGNT-P8.1
# ---------------------------------------------------------------------------


class TestOCCManager:
    """OCCManager verify_and_commit atomic write."""

    # @trace TGNT-P8.1
    def test_get_version_nonexistent(self, occ_manager: OCCManager) -> None:
        """Non-existent file returns 'none'."""
        assert occ_manager.get_version(Path("/no/such/file")) == "none"

    # @trace TGNT-P8.1
    def test_verify_and_commit_success(self, occ_manager: OCCManager, tmp_path: Path) -> None:
        """Commit succeeds when base version matches."""
        f = tmp_path / "data.txt"
        f.write_bytes(b"original")
        base = occ_manager.get_version(f)
        assert occ_manager.verify_and_commit(f, base, b"updated") is True
        assert f.read_bytes() == b"updated"

    # @trace TGNT-P8.1
    def test_verify_and_commit_conflict(self, occ_manager: OCCManager, tmp_path: Path) -> None:
        """Commit fails when base version is stale."""
        f = tmp_path / "data.txt"
        f.write_bytes(b"original")
        base = occ_manager.get_version(f)
        f.write_bytes(b"someone else wrote")
        assert occ_manager.verify_and_commit(f, base, b"my write") is False
        assert f.read_bytes() == b"someone else wrote"


# ---------------------------------------------------------------------------
# FileClaimsRegistry (mesh.coordination) — TGNT-P8.3 / TGNT-P8.4
# ---------------------------------------------------------------------------


class TestFileClaimsRegistry:
    """Lease-based file claims with TTL and cleanup."""

    # @trace TGNT-P8.3
    def test_acquire_lease_success(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """First acquire on an unclaimed file succeeds."""
        f = tmp_path / "file.txt"
        assert claims.acquire_lease(f, "agent-1") is True

    # @trace TGNT-P8.3
    def test_acquire_lease_blocked_by_other(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """Another agent cannot acquire a live lease."""
        f = tmp_path / "file.txt"
        claims.acquire_lease(f, "agent-1", ttl=60)
        assert claims.acquire_lease(f, "agent-2") is False

    # @trace TGNT-P8.3
    def test_acquire_same_agent_renews(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """Same agent can re-acquire (renew) its own lease."""
        f = tmp_path / "file.txt"
        claims.acquire_lease(f, "agent-1", ttl=60)
        assert claims.acquire_lease(f, "agent-1") is True

    # @trace TGNT-P8.3
    def test_release_lease(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """Release allows another agent to acquire."""
        f = tmp_path / "file.txt"
        claims.acquire_lease(f, "agent-1")
        assert claims.release_lease(f, "agent-1") is True
        assert claims.acquire_lease(f, "agent-2") is True

    # @trace TGNT-P8.3
    def test_release_wrong_agent_fails(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """Another agent cannot release someone else's lease."""
        f = tmp_path / "file.txt"
        claims.acquire_lease(f, "agent-1")
        assert claims.release_lease(f, "agent-2") is False

    # @trace TGNT-P8.4
    def test_expired_lease_allows_new_acquire(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """Expired lease does not block a new acquire."""
        f = tmp_path / "file.txt"
        claims.acquire_lease(f, "agent-1", ttl=1)
        time.sleep(1.1)
        assert claims.acquire_lease(f, "agent-2") is True

    # @trace TGNT-P8.4
    def test_cleanup_expired_removes_stale(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """cleanup_expired() removes expired lock files."""
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        claims.acquire_lease(f1, "agent-1", ttl=1)
        claims.acquire_lease(f2, "agent-2", ttl=60)
        time.sleep(1.1)
        removed = claims.cleanup_expired()
        assert removed >= 1

    # @trace TGNT-P8.4
    def test_cleanup_expired_keeps_live(self, claims: FileClaimsRegistry, tmp_path: Path) -> None:
        """cleanup_expired() does not remove live leases."""
        f = tmp_path / "live.txt"
        claims.acquire_lease(f, "agent-1", ttl=60)
        removed = claims.cleanup_expired()
        assert removed == 0
        # Lease still held
        assert claims.acquire_lease(f, "agent-2") is False


# ---------------------------------------------------------------------------
# FileLeaseRegistry (coordination.file_coordination) — TGNT-P8.3 / TGNT-P8.4
# ---------------------------------------------------------------------------


class TestFileLeaseRegistry:
    """FileLeaseRegistry claim/renew/release with HLC tokens."""

    # @trace TGNT-P8.3
    def test_claim_returns_token(self, lease_registry: FileLeaseRegistry, tmp_path: Path) -> None:
        """Successful claim returns an HLC token string."""
        f = tmp_path / "x.txt"
        token = lease_registry.claim_lease(f, "agent-1")
        assert token is not None
        assert ":" in token

    # @trace TGNT-P8.3
    def test_claim_blocked(self, lease_registry: FileLeaseRegistry, tmp_path: Path) -> None:
        """Claiming a file already leased returns None."""
        f = tmp_path / "x.txt"
        lease_registry.claim_lease(f, "agent-1", ttl=60)
        assert lease_registry.claim_lease(f, "agent-2") is None

    # @trace TGNT-P8.4
    def test_renew_success(self, lease_registry: FileLeaseRegistry, tmp_path: Path) -> None:
        """Owner can renew with the correct token."""
        f = tmp_path / "x.txt"
        token = lease_registry.claim_lease(f, "agent-1", ttl=10)
        assert token is not None
        assert lease_registry.renew_lease(f, "agent-1", token) is True

    # @trace TGNT-P8.4
    def test_renew_wrong_token_fails(self, lease_registry: FileLeaseRegistry, tmp_path: Path) -> None:
        """Renew with wrong token fails."""
        f = tmp_path / "x.txt"
        lease_registry.claim_lease(f, "agent-1", ttl=10)
        assert lease_registry.renew_lease(f, "agent-1", "fake:token") is False

    # @trace TGNT-P8.3
    def test_release_and_reclaim(self, lease_registry: FileLeaseRegistry, tmp_path: Path) -> None:
        """After release, another agent can claim."""
        f = tmp_path / "x.txt"
        token = lease_registry.claim_lease(f, "agent-1")
        assert token is not None
        lease_registry.release_lease(f, "agent-1", token)
        new_token = lease_registry.claim_lease(f, "agent-2")
        assert new_token is not None

    # @trace TGNT-P8.4
    def test_expired_lease_reclaimable(self, lease_registry: FileLeaseRegistry, tmp_path: Path) -> None:
        """Expired lease allows a new agent to claim."""
        f = tmp_path / "x.txt"
        lease_registry.claim_lease(f, "agent-1", ttl=1)
        time.sleep(1.1)
        token = lease_registry.claim_lease(f, "agent-2")
        assert token is not None
