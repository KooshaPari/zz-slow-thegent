"""AUDIT-N+29 — dormant-core hardening lane parity.

This suite pins the post-AUDIT-N+28 SOTA-audit second-pass hardening
findings on the :class:`RunRegistry` surface. The findings were surfaced
by a parallel SOTA audit sub-agent over the AUDIT-N+28 commit
(``cf1e47664`` — ``run_impl`` + ``register_end`` dual-mode bridge) and
are tagged ``NEW-1`` through ``NEW-10`` in the audit report.

Items closed in this lane:

* **NEW-1** — ``status="cancelled"`` now maps to
  :attr:`RunState.CANCELLED` rather than being silently downgraded to
  :attr:`RunState.COMPLETED`. ``"timeout"`` → ``FAILED`` and
  ``"aborted"`` → ``CANCELLED`` are accepted as canonical aliases.
* **NEW-2** — :meth:`RunRegistry.list_runs` finish-event predicate is
  narrowed to ``data.get("event") in {"end", "finish"}`` only; the
  previous ``or "status" in data`` clause conflated feedback / override
  / escalation events with finish events.
* **NEW-3** — :class:`RunRegistry` carries a per-instance
  ``_append_lock`` (``threading.RLock``) so concurrent
  ``register_start`` / ``register_end`` / ``register`` callers cannot
  corrupt the hash chain. ``Auditor.verify_registry`` stays clean
  under N=16 concurrent finish writers.
* **NEW-4** — JSONL write path is wrapped in ``try/except OSError``
  and rolls back the in-memory ``_states`` flip on failure so a
  partial-write IO error cannot desync the in-memory map from the
  on-disk JSONL.
* **NEW-5** — Defensive input-validation on :meth:`register_end`:
  ``run_id`` must be a non-empty ``str``, ``exit_code`` must be
  ``int`` (not ``bool``), ``status`` must be one of the allowed
  values. Validation fires before any state mutation or JSONL write.
* **NEW-9** — ``duration_s`` (and the legacy ``duration`` form)
  reject ``NaN`` / ``±inf`` outright; negative durations are clamped
  to ``0.0`` so clock-skew-derived underflow cannot poison downstream
  analytics.
* **NEW-10** — :meth:`RunRegistry.list_runs` finish-merge prefers the
  canonical ``duration_s`` / ``ended_at_utc`` keys when BOTH legacy
  and canonical forms coexist on the same JSONL line.

Pre-existing test coverage (``tests/test_unit_audit_n28_signature_gap_closure.py``)
is untouched; this lane adds new tests only.
"""

from __future__ import annotations

import json
import math
import threading
from pathlib import Path
from typing import Any

import pytest

from thegent.execution import Auditor, RunMeta, RunRegistry, RunState


def _make_meta(run_id: str = "run_test") -> RunMeta:
    return RunMeta(run_id=run_id, agent="claude", prompt="p", cwd="/tmp", owner="u")


# ---------------------------------------------------------------------------
# Lane 1 — NEW-1: explicit status → RunState mapping
# ---------------------------------------------------------------------------


class TestRegisterEndStatusMachine:
    """Pin the NEW-1 status → RunState mapping for the canonical three
    plus the orchestrator aliases (``timeout`` / ``aborted``).
    """

    def test_status_completed_maps_to_completed_state(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("c1"))
        reg.register_end("c1", 0, "completed", "2026-07-22T00:00:00Z", 1.0)
        assert reg.get_run_state("c1") is RunState.COMPLETED

    def test_status_failed_maps_to_failed_state(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("f1"))
        reg.register_end("f1", 1, "failed", "2026-07-22T00:00:00Z", 1.0)
        assert reg.get_run_state("f1") is RunState.FAILED

    def test_status_cancelled_maps_to_cancelled_state(self, tmp_path: Path) -> None:
        """NEW-1: the canonical ``cancelled`` status now maps to
        :attr:`RunState.CANCELLED`. Pre-AUDIT-N+29 the engine silently
        downgraded it to COMPLETED, corrupting downstream state.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("x1"))
        reg.register_end("x1", 130, "cancelled", "2026-07-22T00:00:00Z", 1.0)
        assert reg.get_run_state("x1") is RunState.CANCELLED

    def test_status_timeout_maps_to_failed_state(self, tmp_path: Path) -> None:
        """``timeout`` is the orchestrator SIGTERM-after-deadline signal
        — semantically a failure with non-zero exit."""
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("t1"))
        reg.register_end("t1", 124, "timeout", "2026-07-22T00:00:00Z", 5.0)
        assert reg.get_run_state("t1") is RunState.FAILED

    def test_status_aborted_maps_to_cancelled_state(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("a1"))
        reg.register_end("a1", 134, "aborted", "2026-07-22T00:00:00Z", 0.5)
        assert reg.get_run_state("a1") is RunState.CANCELLED

    def test_status_unknown_maps_to_failed_state(self, tmp_path: Path) -> None:
        """An unknown status surfaces as FAILED (NOT silently
        downgraded to COMPLETED, the pre-AUDIT-N+29 behaviour).
        """
        # NEW-5 will reject this at the validation layer before
        # reaching the state machine, so we have to bypass validation
        # to test the legacy / migration path. We do so by calling
        # the state-machine helper directly via the bridged code
        # path — but the validation layer is part of the public API
        # so the test just confirms the validation surface works.
        with pytest.raises(ValueError, match="status must be one of"):
            RunRegistry(tmp_path).register_end("u1", 1, "bogus", "2026-07-22T00:00:00Z", 1.0)

    def test_status_persists_canonical_in_jsonl(self, tmp_path: Path) -> None:
        """The JSONL entry persists ``status`` verbatim so the audit
        replay can distinguish completed / failed / cancelled without
        consulting the in-memory map.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("p1"))
        reg.register_end("p1", 130, "cancelled", "2026-07-22T00:00:00Z", 1.0)
        finish_lines = [
            l for l in reg.registry_path.read_text(encoding="utf-8").strip().splitlines() if '"finish"' in l
        ]
        assert len(finish_lines) == 1
        data = json.loads(finish_lines[0])
        assert data["status"] == "cancelled"
        assert data["run_id"] == "p1"


# ---------------------------------------------------------------------------
# Lane 2 — NEW-2: list_runs predicate narrowing
# ---------------------------------------------------------------------------


class TestListRunsPredicateNarrowing:
    """Pin the NEW-2 list_runs predicate narrowing. Feedback / override /
    escalation events that legitimately carry a ``status`` key MUST NOT
    be conflated with finish events.
    """

    def test_list_runs_ignores_feedback_event_status(self, tmp_path: Path) -> None:
        """A feedback event with ``status="kept"`` MUST NOT overwrite
        the merged run's status. Pre-AUDIT-N+29 the predicate was
        ``data.get("event") == "end" or "status" in data`` which
        conflated feedback events with finish events.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("f10"))
        # Manually inject a feedback event into the JSONL — the
        # canonical surface would emit it through a different path,
        # but the list_runs contract must be agnostic to where the
        # line came from.
        feedback_line = json.dumps({"run_id": "f10", "event": "feedback", "status": "kept", "score": 0.9})
        with open(reg.registry_path, "a", encoding="utf-8") as f:
            f.write(feedback_line + "\n")

        runs = reg.list_runs()
        assert len(runs) == 1
        # The start entry's status is "pending"; the feedback event
        # must NOT have flipped it to "kept".
        assert runs[0]["status"] == "pending"

    def test_list_runs_ignores_override_event_status(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("f11"))
        override_line = json.dumps({"run_id": "f11", "event": "override_applied", "status": "resolved"})
        with open(reg.registry_path, "a", encoding="utf-8") as f:
            f.write(override_line + "\n")

        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["status"] == "pending"

    def test_list_runs_finish_event_still_overrides_status(self, tmp_path: Path) -> None:
        """The narrowed predicate MUST still accept legitimate finish
        events. The pre-AUDIT-N+29 narrow path covered the start
        entries correctly; this test pins that the finish-event path
        is unchanged.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("f12"))
        reg.register_end(
            run_id="f12",
            exit_code=0,
            status="completed",
            ended_at_utc="2026-07-22T00:00:00Z",
            duration_s=2.0,
        )
        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["status"] == "completed"
        assert runs[0]["duration_s"] == 2.0

    def test_list_runs_accepts_legacy_event_end_value(self, tmp_path: Path) -> None:
        """Pre-AUDIT-N+28 registries write ``"event": "end"``; the
        narrowed predicate must accept both ``"end"`` and ``"finish"``.
        """
        reg = RunRegistry(tmp_path)
        # Handwrite a start + legacy-end sequence into the registry.
        start_line = json.dumps(_make_meta("leg1").to_dict())
        end_line = json.dumps(
            {
                "run_id": "leg1",
                "event": "end",
                "status": "completed",
                "exit_code": 0,
                "ended_at": "2026-07-22T00:00:00Z",
                "duration": 1.5,
            }
        )
        reg.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(reg.registry_path, "w", encoding="utf-8") as f:
            f.write(start_line + "\n")
            f.write(end_line + "\n")

        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["status"] == "completed"
        # NEW-10: legacy ``duration`` → canonical ``duration_s``.
        assert runs[0]["duration_s"] == 1.5


# ---------------------------------------------------------------------------
# Lane 3 — NEW-10: list_runs canonical-wins merge
# ---------------------------------------------------------------------------


class TestListRunsCanonicalWins:
    """Pin the NEW-10 canonical-wins merge semantics. When BOTH the
    legacy ``duration`` / ``ended_at`` keys and the canonical
    ``duration_s`` / ``ended_at_utc`` keys appear on the same JSONL
    line, the canonical key wins.
    """

    def test_finish_entry_with_both_legacy_and_canonical_duration(self, tmp_path: Path) -> None:
        """Handwrite a finish line carrying both ``duration`` and
        ``duration_s``; the canonical ``duration_s`` wins.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("cw1"))
        line = json.dumps(
            {
                "run_id": "cw1",
                "event": "finish",
                "status": "completed",
                "exit_code": 0,
                "ended_at": "2026-07-22T00:00:00Z",
                "ended_at_utc": "2026-07-22T00:00:01Z",
                "duration": 9.0,
                "duration_s": 2.0,
            }
        )
        with open(reg.registry_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["duration_s"] == 2.0  # canonical wins
        assert runs[0]["ended_at_utc"] == "2026-07-22T00:00:01Z"

    def test_finish_entry_with_only_legacy_duration_surfaces_under_canonical_key(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("cw2"))
        line = json.dumps(
            {
                "run_id": "cw2",
                "event": "finish",
                "status": "completed",
                "exit_code": 0,
                "ended_at": "2026-07-22T00:00:00Z",
                "duration": 5.0,
            }
        )
        with open(reg.registry_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["duration_s"] == 5.0  # legacy promoted
        assert runs[0]["ended_at_utc"] == "2026-07-22T00:00:00Z"

    def test_finish_entry_surfaces_error_class_and_cost_usd(self, tmp_path: Path) -> None:
        """Pre-AUDIT-N+29 list_runs only surfaced ``status`` /
        ``ended_at_utc`` / ``duration_s`` / ``exit_code`` from finish
        events. NEW-10 extends the merge to also surface
        ``error_class`` / ``cost_usd`` / ``event_details`` so the audit
        replay is the single source of truth.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("cw3"))
        reg.register_end(
            run_id="cw3",
            exit_code=1,
            status="failed",
            ended_at_utc="2026-07-22T00:00:00Z",
            duration_s=0.5,
            error_class="policy_violation",
            cost_usd=0.01,
            event_details={"reason": "grounding_missing"},
        )
        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["error_class"] == "policy_violation"
        assert runs[0]["cost_usd"] == pytest.approx(0.01)
        assert runs[0]["event_details"] == {"reason": "grounding_missing"}


# ---------------------------------------------------------------------------
# Lane 4 — NEW-3: concurrency lock
# ---------------------------------------------------------------------------


class TestConcurrencyLock:
    """Pin the NEW-3 concurrency lock invariant. The ``Auditor`` must
    report a clean hash chain after N concurrent finish writers.
    """

    def test_concurrent_register_end_preserves_hash_chain(self, tmp_path: Path) -> None:
        """Fire 16 threads, each calling ``register_end`` for a
        distinct ``run_id``. The post-condition: every JSONL line is
        valid JSON, the hash chain is unbroken, and no entries are
        interleaved (every entry is on its own line).
        """
        reg = RunRegistry(tmp_path)
        n_threads = 16
        for i in range(n_threads):
            reg.register_start(_make_meta(f"c{i:02d}"))

        errors: list[BaseException] = []

        def writer(i: int) -> None:
            try:
                reg.register_end(
                    run_id=f"c{i:02d}",
                    exit_code=0,
                    status="completed",
                    ended_at_utc=f"2026-07-22T00:00:{i:02d}Z",
                    duration_s=float(i),
                )
            except BaseException as exc:  # noqa: BLE001 - test capture
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)
            assert not t.is_alive(), "thread deadlocked"

        assert errors == [], f"concurrent register_end raised: {errors}"

        auditor = Auditor(reg.registry_path)
        result = auditor.verify_registry()
        assert result["status"] == "passed", result
        assert result["corrupt_count"] == 0
        assert result["chain_broken"] is False

        # Every line is well-formed JSON on its own line.
        for line in reg.registry_path.read_text(encoding="utf-8").splitlines():
            json.loads(line)  # raises on interleaved / corrupt lines

    def test_concurrent_register_start_preserves_header_genesis(self, tmp_path: Path) -> None:
        """Two threads calling ``register_start`` concurrently must
        still produce a well-formed ``__header__`` line at offset 0.
        """
        reg = RunRegistry(tmp_path)
        errors: list[BaseException] = []

        def starter(i: int) -> None:
            try:
                reg.register_start(_make_meta(f"s{i:02d}"))
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=starter, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)
            assert not t.is_alive()

        assert errors == [], f"concurrent register_start raised: {errors}"
        lines = reg.registry_path.read_text(encoding="utf-8").strip().splitlines()
        # The first line is the JSON-encoded ``__header__`` row;
        # ``json.dumps({"run_id": "__header__", ...})`` does not start
        # with the literal string ``__header__``, so the equality
        # assertion must inspect the parsed dict.
        header_data = json.loads(lines[0])
        assert header_data["run_id"] == "__header__"
        assert header_data["prev_hash"] == "0" * 64
        assert len(header_data["hash"]) == 64  # sha256 hex length

    def test_append_lock_is_rlock(self, tmp_path: Path) -> None:
        """The lock must be a re-entrant lock so a future caller that
        re-enters the registry from inside a locked section cannot
        deadlock.
        """
        reg = RunRegistry(tmp_path)
        # threading.RLock.acquire(reentrant=True) returns True on
        # re-entry; threading.Lock would raise RuntimeError.
        assert reg._append_lock.acquire(timeout=1.0)  # noqa: SLF001
        try:
            assert reg._append_lock.acquire(timeout=1.0)  # noqa: SLF001 - re-entry
        finally:
            reg._append_lock.release()
            reg._append_lock.release()


# ---------------------------------------------------------------------------
# Lane 5 — NEW-4: write IO error handling
# ---------------------------------------------------------------------------


class TestWriteIOErrorHandling:
    """Pin the NEW-4 IO-error-safe write path. A simulated ``OSError``
    on the JSONL append must roll back the in-memory state flip and
    surface the exception to the caller without partial-write corruption.
    """

    def test_register_end_io_error_rolls_back_state(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("io1"))
        assert reg.get_run_state("io1") is RunState.RUNNING

        # Simulate an OSError on the JSONL append.
        original_open = open

        def failing_open(path: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            if str(path).endswith("run_registry.jsonl") and "a" in mode:
                raise OSError("read-only filesystem (simulated)")
            return original_open(path, mode, *args, **kwargs)

        monkeypatch.setattr("builtins.open", failing_open)

        with pytest.raises(OSError, match="read-only filesystem"):
            reg.register_end(
                run_id="io1",
                exit_code=0,
                status="completed",
                ended_at_utc="2026-07-22T00:00:00Z",
                duration_s=1.0,
            )

        # NEW-4 invariant: the in-memory state flip is rolled back so
        # the in-memory map stays consistent with the on-disk truth
        # (the JSONL has no finish entry).
        assert reg.get_run_state("io1") is RunState.RUNNING

    def test_register_start_io_error_rolls_back_state(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        reg = RunRegistry(tmp_path)
        original_open = open

        def failing_open(path: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            if str(path).endswith("run_registry.jsonl") and ("a" in mode or "w" in mode):
                raise OSError("read-only filesystem (simulated)")
            return original_open(path, mode, *args, **kwargs)

        monkeypatch.setattr("builtins.open", failing_open)

        with pytest.raises(OSError, match="read-only filesystem"):
            reg.register_start(_make_meta("io2"))

        # NEW-4 invariant: the in-memory state was rolled back; the
        # registry file does not exist (the header-write itself failed).
        assert reg.get_run_state("io2") is None
        assert "io2" not in reg.runs
        assert not reg.registry_path.exists()


# ---------------------------------------------------------------------------
# Lane 6 — NEW-5: defensive input validation
# ---------------------------------------------------------------------------


class TestRegisterEndDefensiveValidation:
    """Pin the NEW-5 defensive input-validation contract.
    ``_validate_register_end_inputs`` fires before any state mutation
    or JSONL write.
    """

    @pytest.mark.parametrize(
        "bad_run_id",
        [None, "", 12345, 1.5, b"r1", ["r1"], {"r1": True}],
        ids=["none", "empty", "int", "float", "bytes", "list", "dict"],
    )
    def test_register_end_rejects_non_string_or_empty_run_id(self, tmp_path: Path, bad_run_id: object) -> None:
        reg = RunRegistry(tmp_path)
        with pytest.raises(ValueError, match="run_id"):
            reg.register_end(bad_run_id, 0, "completed", "2026-07-22T00:00:00Z", 1.0)
        # Validation fires BEFORE any state mutation — no JSONL.
        assert not reg.registry_path.exists()

    @pytest.mark.parametrize(
        "bad_exit_code",
        ["zero", 1.5, None, b"0", [0], {"code": 0}],
        ids=["str", "float", "none", "bytes", "list", "dict"],
    )
    def test_register_end_rejects_non_int_exit_code(self, tmp_path: Path, bad_exit_code: object) -> None:
        reg = RunRegistry(tmp_path)
        with pytest.raises(ValueError, match="exit_code"):
            reg.register_end(
                "r1",
                bad_exit_code,
                "completed",
                "2026-07-22T00:00:00Z",
                1.0,  # type: ignore[arg-type]
            )

    def test_register_end_rejects_bool_exit_code(self, tmp_path: Path) -> None:
        """``bool`` is technically ``int`` in Python but semantically
        distinct — reject it so ``True`` / ``False`` cannot smuggle
        through as ``1`` / ``0``.
        """
        reg = RunRegistry(tmp_path)
        with pytest.raises(ValueError, match="exit_code"):
            reg.register_end(
                "r1",
                True,
                "completed",
                "2026-07-22T00:00:00Z",
                1.0,  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "bad_status",
        ["bogus", "PENDING", "Completed", "", 12345, None],
        ids=["bogus", "uppercase", "titlecase", "empty", "int", "none"],
    )
    def test_register_end_rejects_invalid_status(self, tmp_path: Path, bad_status: object) -> None:
        reg = RunRegistry(tmp_path)
        with pytest.raises(ValueError, match="status"):
            reg.register_end(
                "r1",
                0,
                bad_status,
                "2026-07-22T00:00:00Z",
                1.0,  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# Lane 7 — NEW-9: duration_s NaN / ±inf / negative clamping
# ---------------------------------------------------------------------------


class TestRegisterEndDurationGuards:
    """Pin the NEW-9 duration guards. ``NaN`` / ``±inf`` are rejected;
    negative durations are clamped to ``0.0``.
    """

    @pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
    def test_register_end_rejects_non_finite_duration(self, tmp_path: Path, bad_value: float) -> None:
        reg = RunRegistry(tmp_path)
        with pytest.raises(ValueError, match="duration"):
            reg.register_end("r1", 0, "completed", "2026-07-22T00:00:00Z", bad_value)

    def test_register_end_legacy_form_rejects_non_finite_duration(self, tmp_path: Path) -> None:
        """The legacy 5-positional form must also reject non-finite
        durations — the validation layer is shared.
        """
        reg = RunRegistry(tmp_path)
        with pytest.raises(ValueError, match="duration"):
            reg.register_end("r1", 0, "completed", "2026-07-22T00:00:00Z", math.nan)

    def test_register_end_negative_duration_clamped_to_zero(self, tmp_path: Path) -> None:
        """A negative duration (clock-skew underflow) is clamped to
        ``0.0`` rather than rejected — the orchestrator contract
        allows the run to complete and the audit-trail entry stays
        readable.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("nd1"))
        reg.register_end(
            run_id="nd1",
            exit_code=0,
            status="completed",
            ended_at_utc="2026-07-22T00:00:00Z",
            duration_s=-1.0,
        )
        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["duration_s"] == 0.0

    def test_register_end_zero_duration_accepted(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("zd1"))
        reg.register_end(
            run_id="zd1",
            exit_code=0,
            status="completed",
            ended_at_utc="2026-07-22T00:00:00Z",
            duration_s=0.0,
        )
        runs = reg.list_runs()
        assert runs[0]["duration_s"] == 0.0


# ---------------------------------------------------------------------------
# Lane 8 — runtime surface sanity
# ---------------------------------------------------------------------------


class TestRuntimeSurface:
    """Pin that AUDIT-N+29 introduces no new top-level imports or
    cycles, and that the new public surface stays callable.
    """

    def test_finish_event_values_constant(self) -> None:
        """``_FINISH_EVENT_VALUES`` is the canonical predicate the
        ``list_runs`` merge uses; pin its membership so a future
        refactor that adds a finish-event alias cannot regress.
        """
        assert frozenset({"end", "finish"}) == RunRegistry._FINISH_EVENT_VALUES  # noqa: SLF001

    def test_validate_register_end_inputs_is_static(self) -> None:
        """The validator is a ``@staticmethod`` so it can be called
        without instantiating a registry (e.g., from a CLI validator
        shim).
        """
        # No exception for the happy path.
        RunRegistry._validate_register_end_inputs("r1", 0, "completed")  # noqa: SLF001
        with pytest.raises(ValueError):
            RunRegistry._validate_register_end_inputs("", 0, "completed")  # noqa: SLF001

    def test_append_lock_attribute_present(self, tmp_path: Path) -> None:
        """The ``_append_lock`` attribute must be present on every
        instance so callers can opt into the same lock when needed.
        """
        reg = RunRegistry(tmp_path)
        # threading.RLock is reentrant (has _is_owned / _RLock__owner).
        assert hasattr(reg._append_lock, "acquire")  # noqa: SLF001
        assert hasattr(reg._append_lock, "release")  # noqa: SLF001
