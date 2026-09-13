"""Tests for thegent.mesh.coordination — file coordination, OCC, and conflict prediction.

FR traceability: TGNT-P7.2 (conflict prediction from intents)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from thegent.mesh.coordination import (
    ConflictPrediction,
    EditIntent,
    FileClaimsRegistry,
    HLCTimestamp,
    IntentRegistry,
    OptimisticConcurrencyControl,
    predict_merge_conflicts,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# SCLI-P6.2: HLCTimestamp
# ---------------------------------------------------------------------------


class TestHLCTimestamp:
    """Tests for HLCTimestamp hybrid logical clock. @trace SCLI-P6.2"""

    def test_init_sets_physical_from_clock(self):
        """Default HLCTimestamp uses current time in milliseconds."""
        before = int(time.time() * 1000)
        ts = HLCTimestamp()
        after = int(time.time() * 1000)
        assert before <= ts.physical <= after
        assert ts.logical == 0

    def test_init_with_explicit_values(self):
        """HLCTimestamp accepts explicit physical and logical values."""
        ts = HLCTimestamp(physical=1000, logical=5)
        assert ts.physical == 1000
        assert ts.logical == 5

    def test_str_format(self):
        """String representation is 'physical:logical_hex'."""
        ts = HLCTimestamp(physical=12345, logical=255)
        assert str(ts) == "12345:00ff"

    def test_parse_roundtrip(self):
        """Parsing a stringified HLCTimestamp recovers the values."""
        original = HLCTimestamp(physical=99999, logical=16)
        parsed = HLCTimestamp.parse(str(original))
        assert parsed.physical == original.physical
        assert parsed.logical == original.logical

    def test_parse_invalid_returns_default(self):
        """Parsing an invalid string returns a default timestamp."""
        ts = HLCTimestamp.parse("invalid")
        assert isinstance(ts, HLCTimestamp)

    def test_update_advances_physical(self):
        """update() without other clock advances physical to at least now."""
        ts = HLCTimestamp(physical=1, logical=0)
        ts.update()
        assert ts.physical >= int(time.time() * 1000) - 1

    def test_update_with_other_takes_max(self):
        """update() with another clock takes the maximum physical time."""
        ts = HLCTimestamp(physical=1, logical=0)
        other = HLCTimestamp(physical=999_999_999_999, logical=3)
        ts.update(other)
        assert ts.physical >= other.physical


# ---------------------------------------------------------------------------
# SCLI-P6.1: OptimisticConcurrencyControl
# ---------------------------------------------------------------------------


class TestOptimisticConcurrencyControl:
    """Tests for OCC version tracking. @trace SCLI-P6.1"""

    def test_get_version_returns_empty_for_missing_file(self, tmp_path: Path):
        """get_version returns 'empty' for a nonexistent file."""
        occ = OptimisticConcurrencyControl(tmp_path)
        assert occ.get_version(tmp_path / "ghost.txt") == "empty"

    def test_get_version_returns_sha256(self, tmp_path: Path):
        """get_version returns a sha256 hex digest for an existing file."""
        occ = OptimisticConcurrencyControl(tmp_path)
        f = tmp_path / "file.txt"
        f.write_text("hello", encoding="utf-8")
        version = occ.get_version(f)
        assert len(version) == 64  # sha256 hex

    def test_claim_and_verify_unchanged(self, tmp_path: Path):
        """Claiming then verifying an unchanged file returns True."""
        occ = OptimisticConcurrencyControl(tmp_path)
        f = tmp_path / "data.txt"
        f.write_text("original", encoding="utf-8")
        occ.claim_version(f, "agent-1")
        assert occ.verify_version(f, "agent-1") is True

    def test_verify_detects_change(self, tmp_path: Path):
        """verify_version returns False when file changed after claim."""
        occ = OptimisticConcurrencyControl(tmp_path)
        f = tmp_path / "data.txt"
        f.write_text("original", encoding="utf-8")
        occ.claim_version(f, "agent-1")
        f.write_text("modified", encoding="utf-8")
        assert occ.verify_version(f, "agent-1") is False

    def test_verify_no_claim_returns_true(self, tmp_path: Path):
        """verify_version returns True when no claim exists."""
        occ = OptimisticConcurrencyControl(tmp_path)
        f = tmp_path / "unclaimed.txt"
        f.write_text("x", encoding="utf-8")
        assert occ.verify_version(f, "agent-unknown") is True


# ---------------------------------------------------------------------------
# SCLI-P6.3/P6.4: FileClaimsRegistry
# ---------------------------------------------------------------------------


class TestFileClaimsRegistry:
    """Tests for lease-based file claims. @trace SCLI-P6.3"""

    def test_acquire_and_release_lease(self, tmp_path: Path):
        """Acquiring then releasing a lease succeeds."""
        registry = FileClaimsRegistry(tmp_path)
        f = tmp_path / "target.py"
        assert registry.acquire_lease(f, "agent-a") is True
        assert registry.release_lease(f, "agent-a") is True

    def test_exclusive_lease_blocks_other_agent(self, tmp_path: Path):
        """A second agent cannot acquire an already-held exclusive lease."""
        registry = FileClaimsRegistry(tmp_path)
        f = tmp_path / "target.py"
        assert registry.acquire_lease(f, "agent-a", ttl=60) is True
        assert registry.acquire_lease(f, "agent-b", ttl=60) is False

    def test_same_agent_can_renew_lease(self, tmp_path: Path):
        """The same agent can re-acquire (renew) its own lease."""
        registry = FileClaimsRegistry(tmp_path)
        f = tmp_path / "target.py"
        assert registry.acquire_lease(f, "agent-a") is True
        assert registry.acquire_lease(f, "agent-a") is True

    def test_expired_lease_can_be_claimed(self, tmp_path: Path):
        """An expired lease does not block another agent."""
        registry = FileClaimsRegistry(tmp_path)
        f = tmp_path / "target.py"
        registry.acquire_lease(f, "agent-a", ttl=0)
        time.sleep(0.01)
        assert registry.acquire_lease(f, "agent-b") is True

    def test_release_wrong_agent_returns_false(self, tmp_path: Path):
        """Releasing a lease held by a different agent returns False."""
        registry = FileClaimsRegistry(tmp_path)
        f = tmp_path / "target.py"
        registry.acquire_lease(f, "agent-a")
        assert registry.release_lease(f, "agent-b") is False

    def test_cleanup_expired_removes_stale_leases(self, tmp_path: Path):
        """cleanup_expired removes only expired leases. @trace SCLI-P6.4"""
        registry = FileClaimsRegistry(tmp_path)
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        registry.acquire_lease(f1, "agent-a", ttl=0)
        registry.acquire_lease(f2, "agent-b", ttl=600)
        time.sleep(0.01)
        removed = registry.cleanup_expired()
        assert removed == 1


# ---------------------------------------------------------------------------
# TGNT-P7.2: IntentRegistry
# ---------------------------------------------------------------------------


class TestIntentRegistry:
    """Tests for the intent registry. @trace TGNT-P7.2"""

    def test_register_and_retrieve_intent(self, tmp_path: Path):
        """Registering an intent makes it retrievable via get_intents."""
        reg = IntentRegistry(tmp_path)
        intent = EditIntent(agent_id="a1", file_path="src/foo.py", operation="modify")
        reg.register_intent(intent)
        intents = reg.get_intents()
        assert len(intents) == 1
        assert intents[0].agent_id == "a1"
        assert intents[0].file_path == "src/foo.py"

    def test_get_intents_filters_by_agent(self, tmp_path: Path):
        """get_intents with agent_id filter returns only that agent's intents."""
        reg = IntentRegistry(tmp_path)
        reg.register_intent(EditIntent(agent_id="a1", file_path="x.py", operation="modify"))
        reg.register_intent(EditIntent(agent_id="a2", file_path="y.py", operation="create"))
        assert len(reg.get_intents(agent_id="a1")) == 1
        assert len(reg.get_intents(agent_id="a2")) == 1

    def test_clear_intents_removes_agent_intents(self, tmp_path: Path):
        """clear_intents removes all intents for the specified agent."""
        reg = IntentRegistry(tmp_path)
        reg.register_intent(EditIntent(agent_id="a1", file_path="x.py", operation="modify"))
        reg.register_intent(EditIntent(agent_id="a2", file_path="y.py", operation="modify"))
        removed = reg.clear_intents("a1")
        assert removed == 1
        assert len(reg.get_intents(agent_id="a1")) == 0
        assert len(reg.get_intents(agent_id="a2")) == 1

    def test_register_returns_path(self, tmp_path: Path):
        """register_intent returns the Path to the written intent file."""
        reg = IntentRegistry(tmp_path)
        intent = EditIntent(agent_id="a1", file_path="f.py", operation="modify")
        path = reg.register_intent(intent)
        assert path.exists()
        assert path.suffix == ".json"


# ---------------------------------------------------------------------------
# TGNT-P7.2: predict_merge_conflicts — trial merge before commit
# ---------------------------------------------------------------------------


class TestPredictMergeConflicts:
    """Tests for predict_merge_conflicts(). @trace TGNT-P7.2"""

    def test_different_files_no_conflict(self):
        """Intents targeting different files never conflict. @trace TGNT-P7.2"""
        a = EditIntent(agent_id="a1", file_path="src/foo.py", operation="modify")
        b = EditIntent(agent_id="a2", file_path="src/bar.py", operation="modify")
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is False
        assert result.conflicting_files == []

    def test_both_delete_same_file_no_conflict(self):
        """Both agents deleting the same file is idempotent. @trace TGNT-P7.2"""
        a = EditIntent(agent_id="a1", file_path="old.py", operation="delete")
        b = EditIntent(agent_id="a2", file_path="old.py", operation="delete")
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is False

    def test_create_vs_modify_conflicts(self):
        """Create vs modify on same file is a conflict. @trace TGNT-P7.2"""
        a = EditIntent(agent_id="a1", file_path="f.py", operation="create")
        b = EditIntent(agent_id="a2", file_path="f.py", operation="modify")
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is True
        assert "f.py" in result.conflicting_files

    def test_dual_create_conflicts(self):
        """Two agents creating the same file conflicts. @trace TGNT-P7.2"""
        a = EditIntent(agent_id="a1", file_path="new.py", operation="create")
        b = EditIntent(agent_id="a2", file_path="new.py", operation="create")
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is True

    def test_delete_vs_modify_conflicts(self):
        """Delete vs modify on same file is a conflict. @trace TGNT-P7.2"""
        a = EditIntent(agent_id="a1", file_path="f.py", operation="delete")
        b = EditIntent(agent_id="a2", file_path="f.py", operation="modify")
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is True

    def test_overlapping_line_ranges_conflict(self):
        """Modify intents with overlapping line ranges conflict. @trace TGNT-P7.2"""
        a = EditIntent(
            agent_id="a1",
            file_path="f.py",
            operation="modify",
            line_ranges=[(10, 20)],
        )
        b = EditIntent(
            agent_id="a2",
            file_path="f.py",
            operation="modify",
            line_ranges=[(15, 25)],
        )
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is True
        assert "Overlapping" in result.details

    def test_nonoverlapping_line_ranges_no_conflict(self):
        """Modify intents with disjoint line ranges do not conflict. @trace TGNT-P7.2"""
        a = EditIntent(
            agent_id="a1",
            file_path="f.py",
            operation="modify",
            line_ranges=[(1, 10)],
        )
        b = EditIntent(
            agent_id="a2",
            file_path="f.py",
            operation="modify",
            line_ranges=[(20, 30)],
        )
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is False

    def test_modify_without_ranges_is_conservative_conflict(self):
        """Both modify same file without line ranges: conservative conflict. @trace TGNT-P7.2"""
        a = EditIntent(agent_id="a1", file_path="f.py", operation="modify")
        b = EditIntent(agent_id="a2", file_path="f.py", operation="modify")
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is True
        assert "conservative" in result.details.lower()

    def test_prediction_returns_dataclass(self):
        """predict_merge_conflicts returns a ConflictPrediction. @trace TGNT-P7.2"""
        a = EditIntent(agent_id="a1", file_path="a.py", operation="modify")
        b = EditIntent(agent_id="a2", file_path="b.py", operation="modify")
        result = predict_merge_conflicts(a, b)
        assert isinstance(result, ConflictPrediction)

    def test_adjacent_line_ranges_no_conflict(self):
        """Adjacent but non-overlapping ranges (1-10, 11-20) do not conflict. @trace TGNT-P7.2"""
        a = EditIntent(
            agent_id="a1",
            file_path="f.py",
            operation="modify",
            line_ranges=[(1, 10)],
        )
        b = EditIntent(
            agent_id="a2",
            file_path="f.py",
            operation="modify",
            line_ranges=[(11, 20)],
        )
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is False

    def test_touching_line_ranges_conflict(self):
        """Touching ranges (1-10, 10-20) overlap at boundary. @trace TGNT-P7.2"""
        a = EditIntent(
            agent_id="a1",
            file_path="f.py",
            operation="modify",
            line_ranges=[(1, 10)],
        )
        b = EditIntent(
            agent_id="a2",
            file_path="f.py",
            operation="modify",
            line_ranges=[(10, 20)],
        )
        result = predict_merge_conflicts(a, b)
        assert result.has_conflict is True


# ---------------------------------------------------------------------------
# EditIntent dataclass
# ---------------------------------------------------------------------------


class TestEditIntent:
    """Tests for EditIntent dataclass construction. @trace TGNT-P7.2"""

    def test_auto_timestamp(self):
        """EditIntent sets a timestamp automatically when none provided."""
        intent = EditIntent(agent_id="a1", file_path="f.py", operation="modify")
        assert intent.timestamp is not None
        assert ":" in intent.timestamp

    def test_explicit_timestamp_preserved(self):
        """An explicitly provided timestamp is not overwritten."""
        intent = EditIntent(
            agent_id="a1",
            file_path="f.py",
            operation="modify",
            timestamp="12345:0000",
        )
        assert intent.timestamp == "12345:0000"

    def test_default_line_ranges_empty(self):
        """Default line_ranges is an empty list."""
        intent = EditIntent(agent_id="a1", file_path="f.py", operation="modify")
        assert intent.line_ranges == []
