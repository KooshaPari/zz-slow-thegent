"""AUDIT-N+31 hardening tests for the live dormant-core surfaces.

Targets the live class definitions in
``src/thegent/execution/__init__.py``:

- ``CheckpointRegistry`` (line ~1971, the dict-based surface used by
  ``test_unit_execution.py``, ``test_unit_cli_impl_dag.py``,
  ``test_unit_cli_commands_b.py``, ``test_unit_cli_coverage_c.py``,
  ``test_unit_cli_final_gaps.py``).
- ``HandoffManager`` (line ~2095) — manages agent-to-agent handoffs.
- ``KPIManager`` (line ~2172) — records KPI values + telemetry events.

The earlier file-based ``CheckpointRegistry`` (line ~351) is a dormant
surface shadowed by the redefinition and is NOT covered here; it has
no production callers in the current build.

This module verifies the AUDIT-N+31 hardening pass closed the
following SOTA-style gaps across all three surfaces:

- NEW-1: per-instance ``_append_lock`` (RLock) serialises writes
- NEW-2: defensive input validation fires before state mutation
- NEW-3: explicit ``clear()`` method that returns the cleared count
- NEW-4: ``list_*`` / ``get_*`` return deep copies so callers cannot
         mutate internal state by writing through returned values
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest

from thegent.execution import (
    CheckpointRegistry,
    HandoffManager,
    KPIManager,
)

# ---------------------------------------------------------------------------
# CheckpointRegistry
# ---------------------------------------------------------------------------


class TestCheckpointRegistryAppendLock:
    """AUDIT-N+31 NEW-1: per-instance ``_append_lock`` (RLock)."""

    def test_lock_attribute_is_rlock(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        assert hasattr(reg, "_append_lock"), "CheckpointRegistry must expose _append_lock"
        lock = reg._append_lock
        # RLock supports re-entry from the same thread.
        with lock, lock:  # re-entry: would deadlock if Lock, not RLock
            pass

    def test_concurrent_create_checkpoint_serialised(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)

        def _worker(idx: int) -> None:
            reg.create_checkpoint(f"reason-{idx}", f"dag-{idx}", f"owner-{idx}")

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 50 checkpoints persisted.
        assert len(reg.list_checkpoints()) == 50
        # Each checkpoint_id appears exactly once.
        ids = [cp["checkpoint_id"] for cp in reg.list_checkpoints()]
        assert len(set(ids)) == 50


class TestCheckpointRegistryValidation:
    """AUDIT-N+31 NEW-2: defensive input validation."""

    @pytest.mark.parametrize("bad_reason", ["", None, 123, [], {}, object()])
    def test_create_checkpoint_rejects_invalid_reason(self, tmp_path: Path, bad_reason: Any) -> None:
        reg = CheckpointRegistry(tmp_path)
        with pytest.raises((ValueError, TypeError)):
            reg.create_checkpoint(bad_reason, "dag", "owner")

    @pytest.mark.parametrize("bad_owner", ["", None, 123, [], {}, object()])
    def test_create_checkpoint_rejects_invalid_owner(self, tmp_path: Path, bad_owner: Any) -> None:
        reg = CheckpointRegistry(tmp_path)
        with pytest.raises((ValueError, TypeError)):
            reg.create_checkpoint("reason", "dag", bad_owner)

    @pytest.mark.parametrize("bad_dag", [None, 123, [], {}, object()])
    def test_create_checkpoint_rejects_invalid_dag_content(self, tmp_path: Path, bad_dag: Any) -> None:
        reg = CheckpointRegistry(tmp_path)
        with pytest.raises((ValueError, TypeError)):
            reg.create_checkpoint("reason", bad_dag, "owner")

    def test_validation_fires_before_state_mutation(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        with pytest.raises(ValueError):
            reg.create_checkpoint("", "dag", "owner")
        assert reg.list_checkpoints() == []


class TestCheckpointRegistryClear:
    """AUDIT-N+31 NEW-3: explicit ``clear()`` method."""

    def test_clear_returns_count_and_empties(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        for i in range(3):
            reg.create_checkpoint(f"r{i}", f"d{i}", f"o{i}")
        cleared = reg.clear()
        assert cleared == 3
        assert reg.list_checkpoints() == []

    def test_clear_empty_registry_returns_zero(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        assert reg.clear() == 0


class TestCheckpointRegistryDeepCopyReturns:
    """AUDIT-N+31 NEW-4: ``get_checkpoint`` / ``list_checkpoints`` deep copy."""

    def test_get_checkpoint_returns_independent_copy(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        meta = reg.create_checkpoint("init", "dag", "owner")
        snapshot = reg.get_checkpoint(meta.checkpoint_id)
        assert snapshot is not None
        # Mutate the returned dict.
        snapshot["reason"] = "tampered"
        # Internal state is untouched.
        fresh = reg.get_checkpoint(meta.checkpoint_id)
        assert fresh is not None
        assert fresh["reason"] == "init"

    def test_list_checkpoints_returns_independent_copies(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        reg.create_checkpoint("r1", "d1", "o1")
        snapshot_list = reg.list_checkpoints()
        assert len(snapshot_list) == 1
        # Mutate the returned list and dict.
        snapshot_list.append({"checkpoint_id": "fake"})
        snapshot_list[0]["reason"] = "tampered"
        # Internal state is untouched.
        fresh = reg.list_checkpoints()
        assert len(fresh) == 1
        assert fresh[0]["reason"] == "r1"

    def test_get_checkpoint_unknown_returns_none(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        assert reg.get_checkpoint("nonexistent") is None


# ---------------------------------------------------------------------------
# HandoffManager
# ---------------------------------------------------------------------------


class TestHandoffManagerAppendLock:
    """AUDIT-N+31 NEW-1: HandoffManager._append_lock (RLock)."""

    def test_lock_attribute_is_rlock(self) -> None:
        mgr = HandoffManager()
        assert hasattr(mgr, "_append_lock")
        lock = mgr._append_lock
        with lock, lock:  # re-entry
            pass

    def test_concurrent_register_handoff_serialised(self) -> None:
        mgr = HandoffManager()

        def _worker(idx: int) -> None:
            mgr.register_handoff(f"a-{idx}", f"b-{idx}", {"step": idx})

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(mgr.list_handoffs()) == 50


class TestHandoffManagerValidation:
    """AUDIT-N+31 NEW-2: HandoffManager defensive input validation."""

    @pytest.mark.parametrize("bad_from", ["", None, 123, [], {}, object()])
    def test_register_handoff_rejects_invalid_from(self, bad_from: Any) -> None:
        mgr = HandoffManager()
        with pytest.raises((ValueError, TypeError)):
            mgr.register_handoff(bad_from, "b", {})

    @pytest.mark.parametrize("bad_to", ["", None, 123, [], {}, object()])
    def test_register_handoff_rejects_invalid_to(self, bad_to: Any) -> None:
        mgr = HandoffManager()
        with pytest.raises((ValueError, TypeError)):
            mgr.register_handoff("a", bad_to, {})

    @pytest.mark.parametrize("bad_ctx", [None, "string", 123, [], object()])
    def test_register_handoff_rejects_invalid_context(self, bad_ctx: Any) -> None:
        mgr = HandoffManager()
        with pytest.raises((ValueError, TypeError)):
            mgr.register_handoff("a", "b", bad_ctx)

    def test_validation_fires_before_state_mutation(self) -> None:
        mgr = HandoffManager()
        with pytest.raises(ValueError):
            mgr.register_handoff("", "b", {})
        assert mgr.list_handoffs() == []


class TestHandoffManagerClear:
    """AUDIT-N+31 NEW-3: HandoffManager.clear()."""

    def test_clear_returns_count_and_empties(self) -> None:
        mgr = HandoffManager()
        for i in range(3):
            mgr.register_handoff(f"a-{i}", f"b-{i}", {"i": i})
        cleared = mgr.clear()
        assert cleared == 3
        assert mgr.list_handoffs() == []

    def test_clear_empty_returns_zero(self) -> None:
        assert HandoffManager().clear() == 0


class TestHandoffManagerDeepCopyReturns:
    """AUDIT-N+31 NEW-4: HandoffManager deep-copy returns."""

    def test_get_handoff_returns_independent_copy(self) -> None:
        mgr = HandoffManager()
        mgr.register_handoff("alice", "bob", {"k": 1, "nested": {"x": 1}})
        snap = mgr.get_handoff("alice", "bob")
        assert snap is not None
        snap["context"]["k"] = 999
        snap["context"]["nested"]["x"] = 999
        # Internal state untouched.
        fresh = mgr.get_handoff("alice", "bob")
        assert fresh is not None
        assert fresh["context"]["k"] == 1
        assert fresh["context"]["nested"]["x"] == 1

    def test_list_handoffs_returns_independent_copies(self) -> None:
        mgr = HandoffManager()
        mgr.register_handoff("alice", "bob", {"k": 1})
        snap_list = mgr.list_handoffs()
        assert len(snap_list) == 1
        snap_list.append({"from": "fake", "to": "x", "context": {}})
        snap_list[0]["context"]["k"] = 999
        fresh = mgr.list_handoffs()
        assert len(fresh) == 1
        assert fresh[0]["context"]["k"] == 1

    def test_get_handoff_unknown_returns_none(self) -> None:
        mgr = HandoffManager()
        assert mgr.get_handoff("a", "b") is None


# ---------------------------------------------------------------------------
# KPIManager
# ---------------------------------------------------------------------------


class TestKPIManagerAppendLock:
    """AUDIT-N+31 NEW-1: KPIManager._append_lock (RLock)."""

    def test_lock_attribute_is_rlock(self, tmp_path: Path) -> None:
        mgr = KPIManager(tmp_path)
        assert hasattr(mgr, "_append_lock")
        with mgr._append_lock, mgr._append_lock:
            pass

    def test_concurrent_record_serialised(self, tmp_path: Path) -> None:
        mgr = KPIManager(tmp_path)

        def _worker(idx: int) -> None:
            mgr.record(f"kpi-{idx}", float(idx))

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(mgr.events) == 50
        assert len(mgr.kpis) == 50


class TestKPIManagerValidation:
    """AUDIT-N+31 NEW-2: KPIManager defensive input validation."""

    @pytest.mark.parametrize("bad_name", ["", None, 123, [], {}, object()])
    def test_record_rejects_invalid_kpi_name(self, tmp_path: Path, bad_name: Any) -> None:
        mgr = KPIManager(tmp_path)
        with pytest.raises((ValueError, TypeError)):
            mgr.record(bad_name, 1.0)

    @pytest.mark.parametrize(
        "bad_value",
        [None, "string", [], {}, object(), float("nan"), float("inf"), float("-inf"), True, False],
    )
    def test_record_rejects_invalid_value(self, tmp_path: Path, bad_value: Any) -> None:
        mgr = KPIManager(tmp_path)
        with pytest.raises((ValueError, TypeError)):
            mgr.record("ok", bad_value)

    def test_validation_fires_before_state_mutation(self, tmp_path: Path) -> None:
        mgr = KPIManager(tmp_path)
        with pytest.raises(ValueError):
            mgr.record("", 1.0)
        assert mgr.events == []
        assert mgr.kpis == {}


class TestKPIManagerClear:
    """AUDIT-N+31 NEW-3: KPIManager.clear()."""

    def test_clear_returns_event_count_and_empties(self, tmp_path: Path) -> None:
        mgr = KPIManager(tmp_path)
        mgr.record("kpi-1", 1.0)
        mgr.record("kpi-2", 2.0)
        cleared = mgr.clear()
        assert cleared == 2
        assert mgr.events == []
        assert mgr.kpis == {}

    def test_clear_empty_returns_zero(self, tmp_path: Path) -> None:
        assert KPIManager(tmp_path).clear() == 0


class TestKPIManagerDeepCopyReturns:
    """AUDIT-N+31 NEW-4: KPIManager.summary returns a copy."""

    def test_summary_returns_independent_copy(self, tmp_path: Path) -> None:
        mgr = KPIManager(tmp_path)
        mgr.record("k1", 1.0)
        snap = mgr.summary()
        snap["k1"] = 999.0
        # Internal state untouched.
        assert mgr.kpis["k1"] == 1.0

    def test_summary_is_not_same_dict(self, tmp_path: Path) -> None:
        mgr = KPIManager(tmp_path)
        mgr.record("k1", 1.0)
        assert mgr.summary() is not mgr.kpis


# ---------------------------------------------------------------------------
# End-to-end smoke: hardened surfaces serve the contract
# ---------------------------------------------------------------------------


class TestEndToEndContract:
    """Smoke tests covering the complete AUDIT-N+31 hardened surface."""

    def test_checkpoint_create_get_list_clear_round_trip(self, tmp_path: Path) -> None:
        reg = CheckpointRegistry(tmp_path)
        a = reg.create_checkpoint("step1", "A -> B", "alice")
        b = reg.create_checkpoint("step2", "B -> C", "bob")
        assert reg.get_checkpoint(a.checkpoint_id) is not None
        assert reg.get_checkpoint(b.checkpoint_id) is not None
        assert len(reg.list_checkpoints()) == 2
        cleared = reg.clear()
        assert cleared == 2
        assert reg.list_checkpoints() == []

    def test_handoff_register_get_list_clear_round_trip(self) -> None:
        mgr = HandoffManager()
        mgr.register_handoff("alice", "bob", {"k": 1})
        mgr.register_handoff("bob", "carol", {"k": 2})
        assert mgr.get_handoff("alice", "bob") is not None
        assert mgr.get_handoff("bob", "carol") is not None
        assert len(mgr.list_handoffs()) == 2
        cleared = mgr.clear()
        assert cleared == 2
        assert mgr.list_handoffs() == []

    def test_kpi_record_get_clear_round_trip(self, tmp_path: Path) -> None:
        mgr = KPIManager(tmp_path)
        mgr.record("throughput", 100.0)
        mgr.record("latency", 0.5)
        assert mgr.get("throughput") == 100.0
        assert mgr.get("latency") == 0.5
        assert len(mgr.events) == 2
        cleared = mgr.clear()
        assert cleared == 2
        assert mgr.events == []
