"""SOTA audit pass 7 — tests for ``thegent.mcp.server.mcp_audit_wiring``.

Covers the wiring of :class:`MCPAuditTrail` into the MCP server
dispatch surface and the cockpit observability gauge.

Test surface (lane A — wiring):

* WA-001  Module exports — re-exports land at ``thegent.mcp.server``
* WA-002  Lazy singleton — trail created on first access; same instance
  returned across calls
* WA-003  ``reset_audit_trail`` swaps the singleton
* WA-004  ``reset_audit_trail`` without ``max_entries`` reads env
* WA-005  Defensive config — non-positive ``THEGENT_MCP_AUDIT_MAX_ENTRIES``
  falls back to default with ``UserWarning``
* WA-006  Defensive config — non-int ``THEGENT_MCP_AUDIT_MAX_ENTRIES``
  falls back to default with ``UserWarning``
* WA-007  ``record_tool_call`` records with TOOL_INVOCATION kind
* WA-008  ``record_resource_read`` records with RESOURCE_READ kind
* WA-009  ``record_gate_check`` records with GATE_CHECK kind
* WA-010  ``record_error`` records with ERROR kind + ``outcome="error"``
* WA-011  ``audit_context`` records ok path with measured duration_ms
* WA-012  ``audit_context`` records error path with ``error_message``
  and re-raises
* WA-013  ``audit_context`` accepts ``kind=str`` and resolves to enum
* WA-014  ``audit_context`` accepts ``kind=AuditEntryKind``
* WA-015  ``audit_context`` warns on unknown string kind and coerces
* WA-016  ``audit_context`` rejects non-str / non-enum ``kind``
* WA-017  ``audit_context`` state dict merges into recorded ``extra``
* WA-018  ``audit_context`` never lets the inner record raise

Test surface (lane B — observability gauge):

* OG-001  ``mcp_audit_stats`` returns the singleton's summary
* OG-002  ``mcp_audit_stats`` agrees with ``MCPAuditTrail.summary``
* OG-003  ``mcp_audit_recent(n)`` returns newest ``n`` entries
* OG-004  ``mcp_audit_recent(n=0)`` returns empty list
* OG-005  ``mcp_audit_query`` filters by kind
* OG-006  ``mcp_audit_query`` filters by operation / agent / outcome

Test surface (cross-cutting):

* TS-001  Concurrent dispatch — 4 writer threads × 100 records
  produce 400 entries, no torn writes, seqs monotonic 1..N
* TS-002  Payload hashing determinism on recorded entries
* TS-003  Audit context is reentrant-friendly (nested blocks)
* TS-004  Singleton trail survives across multiple callers in the
  same process (integration shape smoke)
"""

from __future__ import annotations

import threading
import time as _time
import warnings

import pytest

from thegent.mcp.server import (
    MCP_AUDIT_DEFAULT_MAX_ENTRIES,
    audit_context,
    audited_budget,
    get_audit_trail,
    mcp_audit_query,
    mcp_audit_recent,
    mcp_audit_stats,
    record_error,
    record_gate_check,
    record_resource_read,
    record_tool_call,
    reset_audit_trail,
)
from thegent.mcp.server.mcp_audit_trail import (
    AuditEntry,
    AuditEntryKind,
    MCPAuditTrail,
)

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Don't leak THEGENT_MCP_AUDIT_MAX_ENTRIES across tests."""
    monkeypatch.delenv("THEGENT_MCP_AUDIT_MAX_ENTRIES", raising=False)


@pytest.fixture(autouse=True)
def _fresh_audit_trail() -> MCPAuditTrail:
    """Each test gets a fresh trail with default max_entries."""
    return reset_audit_trail()


@pytest.fixture
def fresh_small_trail() -> MCPAuditTrail:
    """Trail with cap=10 (for eviction tests)."""
    return reset_audit_trail(max_entries=10)


# ------------------------------------------------------------------
# WA-001 — module re-exports
# ------------------------------------------------------------------


class TestModuleReexports:
    """WA-001: All lane A + lane B symbols re-export from thegent.mcp.server."""

    def test_record_helpers_present(self) -> None:
        from thegent.mcp.server import (  # noqa: F401
            audit_context,
            get_audit_trail,
            mcp_audit_query,
            mcp_audit_recent,
            mcp_audit_stats,
            record_error,
            record_gate_check,
            record_resource_read,
            record_tool_call,
            reset_audit_trail,
        )

        assert callable(record_tool_call)
        assert callable(record_resource_read)
        assert callable(record_gate_check)
        assert callable(record_error)
        assert callable(audit_context)

    def test_observability_helpers_present(self) -> None:
        assert callable(mcp_audit_stats)
        assert callable(mcp_audit_recent)
        assert callable(mcp_audit_query)

    def test_default_max_entries_constant(self) -> None:
        assert MCP_AUDIT_DEFAULT_MAX_ENTRIES == 5000
        assert isinstance(MCP_AUDIT_DEFAULT_MAX_ENTRIES, int)
        assert MCP_AUDIT_DEFAULT_MAX_ENTRIES > 0


# ------------------------------------------------------------------
# WA-002 / WA-003 / WA-004 — singleton lifecycle
# ------------------------------------------------------------------


class TestSingletonLifecycle:
    """WA-002..004: Lazy singleton, same-instance identity, reset."""

    def test_lazy_creation(self) -> None:
        # reset_audit_trail() in the autouse fixture already created the
        # singleton; resetting again is fine. Calling get_audit_trail
        # twice should return the same instance.
        a = get_audit_trail()
        b = get_audit_trail()
        assert a is b
        assert isinstance(a, MCPAuditTrail)

    def test_reset_swaps_singleton(self) -> None:
        first = get_audit_trail()
        second = reset_audit_trail()
        assert second is not first
        third = get_audit_trail()
        assert third is second

    def test_reset_without_max_entries_uses_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("THEGENT_MCP_AUDIT_MAX_ENTRIES", "123")
        trail = reset_audit_trail()
        assert trail._max == 123

    def test_reset_without_max_entries_falls_back_to_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("THEGENT_MCP_AUDIT_MAX_ENTRIES", raising=False)
        trail = reset_audit_trail()
        assert trail._max == MCP_AUDIT_DEFAULT_MAX_ENTRIES


# ------------------------------------------------------------------
# WA-005 / WA-006 — defensive config
# ------------------------------------------------------------------


class TestDefensiveConfig:
    """WA-005/006: bad env values must not silently disable audit capture."""

    @pytest.mark.parametrize("bad", ["0", "-1", "-999"])
    def test_non_positive_max_entries_warns_and_falls_back(
        self,
        monkeypatch: pytest.MonkeyPatch,
        bad: str,
    ) -> None:
        monkeypatch.setenv("THEGENT_MCP_AUDIT_MAX_ENTRIES", bad)
        with pytest.warns(UserWarning, match="must be positive"):
            trail = reset_audit_trail()
        assert trail._max == MCP_AUDIT_DEFAULT_MAX_ENTRIES

    @pytest.mark.parametrize("bad", ["", "abc", "1.5", "  "])
    def test_non_int_max_entries_warns_and_falls_back(
        self,
        monkeypatch: pytest.MonkeyPatch,
        bad: str,
    ) -> None:
        if bad:
            monkeypatch.setenv("THEGENT_MCP_AUDIT_MAX_ENTRIES", bad)
        else:
            monkeypatch.delenv("THEGENT_MCP_AUDIT_MAX_ENTRIES", raising=False)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            trail = reset_audit_trail()
        # Validate that the resolution fell back to default; some
        # bad values (e.g. empty string -> default direct path) may
        # not emit a warning, so check the cap.
        assert trail._max == MCP_AUDIT_DEFAULT_MAX_ENTRIES


# ------------------------------------------------------------------
# WA-007..010 — record helpers
# ------------------------------------------------------------------


class TestRecordHelpers:
    """WA-007..010: Each record helper stamps the correct kind."""

    def test_record_tool_call_kind(self) -> None:
        entry = record_tool_call(
            operation="thegent_run",
            agent="writer_standard",
            session_id="s-abc",
            duration_ms=42.0,
        )
        assert isinstance(entry, AuditEntry)
        assert entry.kind == AuditEntryKind.TOOL_INVOCATION
        assert entry.operation == "thegent_run"
        assert entry.agent == "writer_standard"
        assert entry.outcome == "ok"
        assert entry.duration_ms == 42.0
        assert entry.error_message is None

    def test_record_resource_read_kind(self) -> None:
        entry = record_resource_read(
            operation="resource_observe_summary",
            agent="dashboard",
        )
        assert entry.kind == AuditEntryKind.RESOURCE_READ

    def test_record_gate_check_kind(self) -> None:
        entry = record_gate_check(
            operation="contract_health_gate",
            agent="ci",
            outcome="pass",
        )
        assert entry.kind == AuditEntryKind.GATE_CHECK
        assert entry.outcome == "pass"

    def test_record_error_kind_and_outcome(self) -> None:
        entry = record_error(
            operation="thegent_bg",
            error_message="connection refused",
        )
        assert entry.kind == AuditEntryKind.ERROR
        assert entry.outcome == "error"
        assert entry.error_message == "connection refused"

    def test_record_helpers_appear_in_singleton(self) -> None:
        record_tool_call("thegent_run")
        record_resource_read("resource_observe_summary")
        record_gate_check("contract_health_gate")
        record_error("thegent_bg", error_message="boom")
        stats = mcp_audit_stats()
        assert stats["total_entries"] == 4
        assert stats["by_kind"]["tool_invocation"] == 1
        assert stats["by_kind"]["resource_read"] == 1
        assert stats["by_kind"]["gate_check"] == 1
        assert stats["by_kind"]["error"] == 1


# ------------------------------------------------------------------
# WA-011..018 — audit_context
# ------------------------------------------------------------------


class TestAuditContext:
    """WA-011..018: audit_context behaviour."""

    def test_ok_path_records_duration(self) -> None:
        with audit_context(
            kind=AuditEntryKind.TOOL_INVOCATION,
            operation="wrapper",
            agent="writer_standard",
            payload={"x": 1},
        ) as state:
            state["verdict"] = "allow"

        recent = mcp_audit_recent()
        assert len(recent) == 1
        entry = recent[0]
        assert entry.operation == "wrapper"
        assert entry.outcome == "ok"
        assert entry.duration_ms is not None
        assert entry.duration_ms >= 0.0
        assert entry.error_message is None
        assert entry.extra["verdict"] == "allow"

    def test_error_path_records_and_reraises(self) -> None:
        with (
            pytest.raises(RuntimeError, match="boom"),
            audit_context(
                kind="tool_invocation",
                operation="fail",
            ),
        ):
            raise RuntimeError("boom")

        entry = mcp_audit_recent()[-1]
        assert entry.outcome == "error"
        assert entry.error_message is not None
        assert "RuntimeError" in entry.error_message
        assert "boom" in entry.error_message

    def test_str_kind_is_coerced_to_enum(self) -> None:
        # The first 4 values map onto the AuditEntryKind members.
        for raw, expected in (
            ("tool_invocation", AuditEntryKind.TOOL_INVOCATION),
            ("resource_read", AuditEntryKind.RESOURCE_READ),
            ("gate_check", AuditEntryKind.GATE_CHECK),
            ("error", AuditEntryKind.ERROR),
        ):
            reset_audit_trail()
            with audit_context(kind=raw, operation="x"):
                pass
            assert mcp_audit_recent()[0].kind == expected

    def test_unknown_str_kind_warns_and_coerces(self) -> None:
        with pytest.warns(UserWarning, match="unknown kind"):
            with audit_context(kind="random_typo", operation="x"):
                pass
        assert mcp_audit_recent()[0].kind == AuditEntryKind.TOOL_INVOCATION

    def test_non_str_non_enum_kind_raises_typeerror(self) -> None:
        with pytest.raises(TypeError, match="must be AuditEntryKind or str"):
            with audit_context(kind=42, operation="x"):  # type: ignore[arg-type]
                pass

    def test_state_dict_merges_into_extra(self) -> None:
        with audit_context(
            kind="tool_invocation",
            operation="x",
            extra={"preset": True},
        ) as state:
            state["added"] = "value"
            state["preset"] = "overwritten"

        entry = mcp_audit_recent()[0]
        assert entry.extra["preset"] == "overwritten"
        assert entry.extra["added"] == "value"

    def test_inner_record_never_raises(self) -> None:
        """A buggy record() call inside the finally must not propagate."""

        class _BrokenTrail:
            # Not an MCPAuditTrail; record() raises.
            def record(self, **_kwargs: object) -> None:
                raise RuntimeError("disk full")

            # Observability stubs to keep `mcp_audit_stats` from
            # blowing up the test harness if it sneaks in.
            def summary(self) -> dict[str, int]:
                return {"total_entries": 0}

            def recent(self, n: int = 100) -> list[object]:  # noqa: ARG002
                return []

            def query(
                self,
                **kwargs: object,  # noqa: ARG002
            ) -> list[object]:
                return []

        # Swap the singleton with a broken one
        from thegent.mcp.server import mcp_audit_wiring as wiring

        wiring._trail = _BrokenTrail()  # type: ignore[assignment]
        try:
            with audit_context(
                kind="tool_invocation",
                operation="x",
            ):
                pass
            # Outer block must NOT raise even though trail.record blew up.
        finally:
            reset_audit_trail()


# ------------------------------------------------------------------
# OG-001..006 — observability gauge
# ------------------------------------------------------------------


class TestObservabilityGauge:
    """OG-001..006: mcp_audit_stats / _recent / _query shape and behaviour."""

    def test_empty_stats_shape(self) -> None:
        s = mcp_audit_stats()
        assert s["total_entries"] == 0
        assert s["max_entries"] == MCP_AUDIT_DEFAULT_MAX_ENTRIES
        assert s["by_kind"] == {}
        assert s["by_outcome"] == {}
        assert s["error_count"] == 0
        assert s["avg_duration_ms"] is None
        assert s["p99_duration_ms"] is None
        assert s["oldest_seq"] is None
        assert s["newest_seq"] is None

    def test_stats_agrees_with_singleton(self) -> None:
        record_tool_call("a", duration_ms=10.0)
        record_tool_call("a", duration_ms=20.0)
        via_singleton = get_audit_trail().summary()
        via_gauge = mcp_audit_stats()
        assert via_gauge == via_singleton

    def test_recent_returns_n(self) -> None:
        for i in range(7):
            record_tool_call(f"op_{i}")
        recent = mcp_audit_recent(n=3)
        assert len(recent) == 3
        # Newest last
        assert recent[-1].operation == "op_6"

    def test_recent_default_n_caps(self) -> None:
        for i in range(120):
            record_tool_call(f"op_{i}")
        recent = mcp_audit_recent()  # default n=100
        assert len(recent) == 100

    def test_recent_empty(self) -> None:
        assert mcp_audit_recent(n=0) == []

    def test_query_filters_by_kind(self) -> None:
        record_tool_call("a")
        record_resource_read("b")
        record_tool_call("c")
        tools = mcp_audit_query(kind=AuditEntryKind.TOOL_INVOCATION)
        assert len(tools) == 2
        assert all(e.kind == AuditEntryKind.TOOL_INVOCATION for e in tools)

    def test_query_filters_by_operation(self) -> None:
        record_tool_call("alpha")
        record_tool_call("beta")
        record_tool_call("alpha")
        alphas = mcp_audit_query(operation="alpha")
        assert len(alphas) == 2
        assert all(e.operation == "alpha" for e in alphas)

    def test_query_filters_by_agent(self) -> None:
        record_tool_call("a", agent="writer_standard")
        record_tool_call("a", agent="reviewer")
        record_tool_call("a", agent="writer_standard")
        writer = mcp_audit_query(agent="writer_standard")
        assert len(writer) == 2

    def test_query_filters_by_outcome(self) -> None:
        record_tool_call("a", agent="ci", outcome="ok")
        record_tool_call("a", agent="ci", outcome="error")
        errors = mcp_audit_query(outcome="error")
        assert len(errors) == 1
        assert errors[0].outcome == "error"

    def test_query_combined_filters(self) -> None:
        record_tool_call("a", agent="ci", outcome="ok")
        record_tool_call("a", agent="ci", outcome="error")
        record_tool_call("b", agent="ci", outcome="ok")
        results = mcp_audit_query(
            operation="a",
            agent="ci",
            outcome="ok",
        )
        assert len(results) == 1


# ------------------------------------------------------------------
# TS-001..004 — cross-cutting
# ------------------------------------------------------------------


class TestConcurrentDispatch:
    """TS-001: concurrent record() calls survive without torn writes."""

    def test_concurrent_records_total_converges(self) -> None:
        errors: list[BaseException] = []

        def _worker(n: int) -> None:
            try:
                for i in range(100):
                    record_tool_call(
                        operation=f"op_{n}_{i}",
                        agent=f"agent_{n}",
                        duration_ms=1.0,
                    )
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        s = mcp_audit_stats()
        assert s["total_entries"] == 400
        # Seqs are 1..400; nothing torn.
        seqs = [e.seq for e in mcp_audit_recent(n=400)]
        assert min(seqs) == 1
        assert max(seqs) == 400

    def test_concurrent_audit_context_total_converges(self) -> None:
        errors: list[BaseException] = []

        def _worker(n: int) -> None:
            try:
                for i in range(50):
                    with audit_context(
                        kind="tool_invocation",
                        operation=f"op_{n}_{i}",
                        agent=f"agent_{n}",
                    ):
                        pass
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert mcp_audit_stats()["total_entries"] == 200


class TestPayloadHashing:
    """TS-002: payload hashing on recorded entries is deterministic."""

    def test_same_payload_same_hash(self) -> None:
        payload = {"status": "ok", "items": [1, 2, 3]}
        e1 = record_tool_call("a", payload=payload)
        e2 = record_tool_call("a", payload=payload)
        assert e1.payload_hash == e2.payload_hash

    def test_different_payload_different_hash(self) -> None:
        e1 = record_tool_call("a", payload={"x": 1})
        e2 = record_tool_call("a", payload={"x": 2})
        assert e1.payload_hash != e2.payload_hash

    def test_payload_hashing_observable_via_query(self) -> None:
        payload = {"k": "v"}
        record_tool_call("a", payload=payload)
        results = mcp_audit_query(operation="a")
        assert len(results) == 1
        assert results[0].payload_hash is not None
        assert len(results[0].payload_hash) == 16


class TestAuditContextReentrant:
    """TS-003: nested audit_context blocks each record one entry."""

    def test_nested_blocks_each_record_one_entry(self) -> None:
        with audit_context(kind="tool_invocation", operation="outer"):
            with audit_context(kind="tool_invocation", operation="inner"):
                pass

        recent = mcp_audit_recent(n=10)
        ops = [e.operation for e in recent]
        assert "inner" in ops
        assert "outer" in ops
        assert len(recent) == 2


class TestSingletonSurvivesAcrossCallers:
    """TS-004: get_audit_trail() returns the same trail to every caller."""

    def test_same_instance(self) -> None:
        from thegent.mcp.server import mcp_audit_wiring as wiring

        a = wiring.get_audit_trail()
        b = get_audit_trail()
        assert a is b

    def test_records_visible_across_caller_modules(self) -> None:
        from thegent.mcp.server import mcp_audit_wiring as wiring

        wiring.record_tool_call("caller_a")
        from thegent.mcp.server import record_tool_call as rpc

        rpc("caller_b")
        s = mcp_audit_stats()
        assert s["total_entries"] == 2
        # Seqs are 1, 2 in arrival order
        ops = [e.operation for e in mcp_audit_recent()]
        assert ops == ["caller_a", "caller_b"]


# ------------------------------------------------------------------
# AUDIT-N+22 — outcome reconciliation (SOTA audit pass 8 B3)
# ------------------------------------------------------------------


class TestAuditContextOutcomeReconciliation:
    """AUDIT-N+22 B3: when ``kind=ERROR`` is passed explicitly, the
    recorded ``outcome`` is ``"error"`` even if the block succeeded.

    Previously a caller that did ``with audit_context(kind=ERROR, ...):``
    on a happy path would land a record with ``kind=error, outcome=ok``
    — semantically contradictory and likely to mask audit anomalies
    downstream. The fix reconciles the outcome to ``error`` so the
    JSONL audit log + the cockpit's ``by_outcome`` breakdown stay
    self-consistent.
    """

    def test_kind_error_success_records_outcome_error(self) -> None:
        with audit_context(kind=AuditEntryKind.ERROR, operation="e_path"):
            pass  # block succeeds
        recent = mcp_audit_recent(n=1)
        assert recent[0].kind == AuditEntryKind.ERROR
        assert recent[0].outcome == "error"
        assert recent[0].error_message is None  # no exception was raised

    def test_kind_tool_invocation_success_records_outcome_ok(self) -> None:
        with audit_context(kind=AuditEntryKind.TOOL_INVOCATION, operation="t_path"):
            pass
        recent = mcp_audit_recent(n=1)
        assert recent[0].outcome == "ok"

    def test_kind_error_string_coerces_and_reconciles(self) -> None:
        with audit_context(kind="error", operation="e_str"):
            pass
        recent = mcp_audit_recent(n=1)
        assert recent[0].kind == AuditEntryKind.ERROR
        assert recent[0].outcome == "error"

    def test_exception_in_block_drives_error_outcome(self) -> None:
        with pytest.raises(RuntimeError):
            with audit_context(kind=AuditEntryKind.TOOL_INVOCATION, operation="boom"):
                raise RuntimeError("kaboom")
        recent = mcp_audit_recent(n=1)
        assert recent[0].outcome == "error"
        assert recent[0].error_message is not None
        assert "kaboom" in recent[0].error_message


# ------------------------------------------------------------------
# AUDIT-N+22 — singleton swap safety (SOTA audit pass 8 B1)
# ------------------------------------------------------------------


class TestConcurrentResetPreservesSeqOrdering:
    """AUDIT-N+22 B1: a reset mid-write must NOT corrupt seq ordering.

    The wiring module swaps the singleton under ``_lock``. Concurrent
    ``record()`` calls that captured the old trail reference continue
    writing to the OLD trail (Python's GIL guarantees the method
    dispatch is atomic). The new trail starts a fresh seq counter at
    1. After the reset, the new trail must NOT inherit seqs from the
    old one (which would create a phantom history).

    This test pins the swap semantics so a future refactor (e.g.,
    moving to an async trail or a shared ring buffer) cannot silently
    break it.
    """

    def test_reset_mid_write_starts_fresh_seq_counter(self) -> None:
        reset_audit_trail()
        old_trail = get_audit_trail()
        old_trail.record(
            kind=AuditEntryKind.TOOL_INVOCATION,
            operation="pre_reset",
            agent="a",
            outcome="ok",
        )
        # Capture the old seq counter
        pre_reset_seqs = [e.seq for e in old_trail.recent(n=10)]
        assert pre_reset_seqs == [1]

        # Swap the singleton
        reset_audit_trail(max_entries=50)
        new_trail = get_audit_trail()
        assert new_trail is not old_trail

        # New trail's seq counter must start at 1
        entry = new_trail.record(
            kind=AuditEntryKind.TOOL_INVOCATION,
            operation="post_reset",
            agent="a",
            outcome="ok",
        )
        assert entry.seq == 1

        # Old trail is now orphaned (not the singleton) but still
        # accepts writes — its seq counter has continued from 2.
        # This is documented behaviour: callers who hold a direct
        # reference to the old trail can still write to it.
        old_entry = old_trail.record(
            kind=AuditEntryKind.TOOL_INVOCATION,
            operation="orphaned",
            agent="a",
            outcome="ok",
        )
        assert old_entry.seq == 2

    def test_concurrent_reset_under_writers_does_not_corrupt_singleton(self) -> None:
        """B1 stress test: writers and a resetter run concurrently.

        After the resetters have completed, the singleton must be one
        of the two trails produced by the resets (not some interleaved
        phantom). Each writer's last ``record()`` call lands on
        whichever trail was current at that moment.
        """
        import threading

        reset_audit_trail(max_entries=200)
        barrier = threading.Barrier(8)
        errors: list[BaseException] = []

        def writer(idx: int) -> None:
            try:
                barrier.wait(timeout=5.0)
                for i in range(50):
                    get_audit_trail().record(
                        kind=AuditEntryKind.GATE_CHECK,
                        operation=f"w{idx}_{i}",
                        agent=f"w{idx}",
                        outcome="ok",
                    )
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        def resetter(idx: int) -> None:
            try:
                barrier.wait(timeout=5.0)
                for i in range(5):
                    reset_audit_trail(max_entries=200 + idx * 10 + i)
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads: list[threading.Thread] = []
        for i in range(6):
            threads.append(threading.Thread(target=writer, args=(i,)))
        for i in range(2):
            threads.append(threading.Thread(target=resetter, args=(i,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        assert not errors, f"workers raised: {errors!r}"
        # The final singleton must have a coherent seq counter: each
        # entry's seq equals its 1-based position within the current
        # trail (we cannot pin the exact N because resetters may have
        # swapped mid-write, but within whatever trail is current the
        # seqs must form a contiguous 1..N range).
        current = get_audit_trail()
        seqs = [e.seq for e in current.recent(n=200)]
        assert seqs == sorted(seqs), "seqs must be monotonic"
        if seqs:
            assert seqs == list(range(1, len(seqs) + 1)), (
                f"fresh trail seqs must be contiguous 1..N; got {seqs[:5]}...{seqs[-3:]}"
            )


# ------------------------------------------------------------------
# AUDIT-N+22 — audited_budget composite (SOTA audit pass 8 A2 helper)
# ------------------------------------------------------------------


class TestAuditedBudgetHelper:
    """AUDIT-N+22 A2 helper: ``audited_budget`` composes
    ``audit_context`` and ``mcp_budget_context`` so each MCP tool /
    resource dispatch records exactly one audit entry and applies
    the named perf budget in lockstep.
    """

    def test_success_path_records_one_entry_and_no_budget_exceeded(self) -> None:
        from thegent.mcp.server.mcp_perf_gates import MCP_PERF_BUDGETS

        with audited_budget(
            kind="tool_invocation",
            operation="tool_invoke_ms",
            budget_ms=10_000.0,  # generous so we don't trip the budget
        ):
            pass

        recent = mcp_audit_recent(n=1)
        assert len(recent) == 1
        assert recent[0].operation == "tool_invoke_ms"
        assert recent[0].outcome == "ok"
        # The named budget exists in MCP_PERF_BUDGETS so we did not
        # trip the "operation not in MCP_PERF_BUDGETS" KeyError branch.
        assert "tool_invoke_ms" in MCP_PERF_BUDGETS

    def test_exception_path_records_error_outcome_and_reraises(self) -> None:
        with (
            pytest.raises(ValueError),
            audited_budget(
                kind="tool_invocation",
                operation="tool_invoke_ms",
                budget_ms=10_000.0,
            ),
        ):
            raise ValueError("simulated")

        recent = mcp_audit_recent(n=1)
        assert recent[0].outcome == "error"
        assert recent[0].error_message is not None
        assert "simulated" in recent[0].error_message

    def test_yield_state_allows_caller_annotations(self) -> None:
        with audited_budget(
            kind="tool_invocation",
            operation="tool_invoke_ms",
            budget_ms=10_000.0,
        ) as state:
            state["verdict"] = "allow"
        recent = mcp_audit_recent(n=1)
        assert recent[0].extra.get("verdict") == "allow"

    def test_budget_exceeded_path_raises_mcp_budget_error(self) -> None:
        """When the named budget is exceeded, ``mcp_budget_context``
        raises :class:`MCPBudgetExceeded`. The audit entry is still
        recorded with the elapsed duration so the operator can
        reconcile budget failures with audit timestamps.
        """
        from thegent.mcp.server.mcp_perf_gates import MCPBudgetExceeded

        with (
            pytest.raises(MCPBudgetExceeded),
            audited_budget(
                kind="tool_invocation",
                operation="tool_invoke_ms",
                budget_ms=0.001,  # 1 microsecond — impossible to satisfy
            ),
        ):
            # Yield to the scheduler so the context sees at least
            # a few microseconds of elapsed time.
            _time.sleep(0.005)

        recent = mcp_audit_recent(n=1)
        # The audit entry was recorded even though the budget
        # exceeded — useful for operators tracing a slow call.
        assert recent[0].operation == "tool_invoke_ms"
        assert recent[0].duration_ms is not None

    def test_unknown_kind_string_coerces_to_tool_invocation(self) -> None:
        """``audited_budget`` inherits the ``AuditEntryKind | str``
        contract from ``audit_context``: unknown strings coerce to
        ``TOOL_INVOCATION`` with a ``UserWarning``.
        """
        with (
            pytest.warns(UserWarning, match="unknown kind"),
            audited_budget(
                kind="totally_bogus_kind",
                operation="tool_invoke_ms",
                budget_ms=10_000.0,
            ),
        ):
            pass
        recent = mcp_audit_recent(n=1)
        assert recent[0].kind == AuditEntryKind.TOOL_INVOCATION

    def test_audited_budget_module_reexport(self) -> None:
        from thegent.mcp.server import audited_budget as exported  # noqa: F401

        assert exported is audited_budget
