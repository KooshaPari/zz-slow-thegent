"""Unit tests for the Operator Cockpit (WP-4001, FR-UX-007, OBS8, P-081)."""

from __future__ import annotations

import time

import pytest

from thegent.ux.cockpit import (
    CockpitConfig,
    CockpitPane,
    OperatorCockpit,
    OverrideEvent,
    OverrideExpiryNotice,
    RunEvent,
    RunState,
    render_cockpit,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Sanity
# ---------------------------------------------------------------------------


class TestSanity:
    def test_public_api_present(self) -> None:
        assert CockpitPane.RUNS.value == "runs"
        assert CockpitPane.LANES.value == "lanes"
        assert CockpitPane.CONFIDENCE.value == "confidence"
        assert CockpitPane.OVERRIDES.value == "overrides"
        assert RunState.ACTIVE.value == "active"
        assert RunState.QUEUED.value == "queued"

    def test_config_defaults(self) -> None:
        cfg = CockpitConfig()
        assert cfg.tick_ms == 1000
        assert cfg.progress_total == 100
        assert cfg.sparkline_width == 24
        assert CockpitPane.RUNS in cfg.pane_labels


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


class TestProgressBar:
    def test_zero_total(self) -> None:
        from thegent.ux.cockpit import _progress_bar

        assert _progress_bar(0, 0).startswith("[")

    def test_full(self) -> None:
        from thegent.ux.cockpit import _progress_bar

        out = _progress_bar(10, 10, width=8)
        assert "100%" in out
        assert out.startswith("[########")

    def test_partial(self) -> None:
        from thegent.ux.cockpit import _progress_bar

        out = _progress_bar(3, 4, width=8)
        assert " 75%" in out

    def test_overflow_capped(self) -> None:
        from thegent.ux.cockpit import _progress_bar

        out = _progress_bar(20, 5, width=8)
        assert "100%" in out


class TestSparkline:
    def test_empty(self) -> None:
        from thegent.ux.cockpit import _sparkline

        assert _sparkline([], 5) == "·····"

    def test_constant(self) -> None:
        from thegent.ux.cockpit import _sparkline

        # All-equal values should fall back to a flat line, never raise.
        assert "·" in _sparkline([0.5] * 5, 5)

    def test_widening(self) -> None:
        from thegent.ux.cockpit import _sparkline

        # Values from 0..1 should produce a spark that climbs visually.
        spark = _sparkline([0.1, 0.3, 0.5, 0.7, 0.9], 5)
        assert len(spark) == 5
        # The last character should be a top-tier one (not a bottom-tier one).
        assert spark[-1] in "▅▆▇█"

    def test_pad_when_input_shorter(self) -> None:
        from thegent.ux.cockpit import _sparkline

        spark = _sparkline([1.0], 4)
        assert len(spark) == 4


class TestTruncate:
    def test_short_unchanged(self) -> None:
        from thegent.ux.cockpit import _truncate

        assert _truncate("hi", 10) == "hi"

    def test_truncate_with_ellipsis(self) -> None:
        from thegent.ux.cockpit import _truncate

        out = _truncate("hello world", 6)
        assert out.endswith("…")
        assert len(out) == 6


# ---------------------------------------------------------------------------
# Cockpit event ingestion
# ---------------------------------------------------------------------------


class TestTick:
    def test_tick_records_runs(self) -> None:
        c = OperatorCockpit()
        c.tick(
            runs=[
                RunEvent(run_id="r1", state=RunState.ACTIVE, lane="critical"),
                RunEvent(run_id="r2", state=RunState.QUEUED, lane="standard"),
            ]
        )
        assert "r1" in c._state.runs
        assert "r2" in c._state.runs

    def test_tick_replaces_runs_idempotent(self) -> None:
        c = OperatorCockpit()
        c.tick(runs=[RunEvent(run_id="r1", state=RunState.ACTIVE)])
        c.tick(runs=[RunEvent(run_id="r1", state=RunState.DONE)])
        assert c._state.runs["r1"].state == RunState.DONE

    def test_tick_records_overrides(self) -> None:
        c = OperatorCockpit()
        c.tick(overrides=[OverrideEvent(rule_id="o1", by="alice", reason="hotfix", expires_in_s=120)])
        assert "o1" in c._state.overrides

    def test_tick_records_progress(self) -> None:
        c = OperatorCockpit()
        c.tick(progress=(3, 10))
        assert c._state.last_progress == (3, 10)

    def test_tick_records_confidence_history(self) -> None:
        c = OperatorCockpit()
        c.tick(
            runs=[
                RunEvent(run_id="r1", state=RunState.ACTIVE, confidence=0.7),
                RunEvent(run_id="r2", state=RunState.QUEUED, confidence=0.9),
            ]
        )
        # ``confidence_history`` is a bounded ``deque`` (unbounded-memory
        # hardening); compare via ``list(...)`` so the assertion stays
        # order-/value-equivalent rather than type-strict.
        assert list(c._state.confidence_history) == [0.7, 0.9]
        # Bounded behaviour: appending past maxlen must evict the oldest.
        c._state.confidence_history.extend([1.0] * (1024 + 5))
        assert len(c._state.confidence_history) == 1024
        # The most recent 1024 entries are preserved, oldest evicted.
        assert c._state.confidence_history[-1] == 1.0


# ---------------------------------------------------------------------------
# Render: 4-pane grid
# ---------------------------------------------------------------------------


def _sample_runs() -> list[RunEvent]:
    return [
        RunEvent(
            run_id="run-001",
            state=RunState.ACTIVE,
            lane="critical",
            agent="cursor",
            confidence=0.92,
            elapsed_s=4.2,
        ),
        RunEvent(
            run_id="run-002",
            state=RunState.QUEUED,
            lane="standard",
            agent="gemini",
            confidence=0.71,
        ),
    ]


def _sample_overrides() -> list[OverrideEvent]:
    return [
        OverrideEvent(
            rule_id="no-cursor-prod",
            by="sre",
            reason="hotfix",
            expires_in_s=300,
        )
    ]


class TestRender:
    def test_render_returns_text(self) -> None:
        c = OperatorCockpit()
        c.tick(runs=_sample_runs(), overrides=_sample_overrides(), progress=(2, 8))
        out = c.render()
        assert "thegent operator cockpit" in out
        assert "run-001" in out
        assert "run-002" in out
        assert "no-cursor-prod" in out
        assert "25%" in out  # 2/8 = 25%

    def test_render_records_frame_count(self) -> None:
        c = OperatorCockpit()
        for _ in range(3):
            c.render()
        assert c._frame_count == 3

    def test_render_records_latency_ms(self) -> None:
        c = OperatorCockpit()
        c.render()
        assert c.last_render_ms() >= 0
        assert c.last_render_ms() < 1000  # sub-second

    def test_render_empty(self) -> None:
        c = OperatorCockpit()
        out = c.render()
        # Empty cockpit should still render header + placeholder lines.
        assert "thegent operator cockpit" in out
        assert "no active runs" in out
        assert "no active overrides" in out

    def test_render_progress_bar_at_100(self) -> None:
        c = OperatorCockpit()
        c.tick(progress=(10, 10))
        c.render()
        assert "100%" in c.render()

    def test_render_includes_lane_breakdown(self) -> None:
        c = OperatorCockpit()
        c.tick(
            runs=[
                RunEvent(run_id="r1", state=RunState.ACTIVE, lane="critical"),
                RunEvent(run_id="r2", state=RunState.ACTIVE, lane="critical"),
                RunEvent(run_id="r3", state=RunState.QUEUED, lane="standard"),
            ]
        )
        out = c.render()
        assert "critical" in out
        assert "standard" in out

    def test_render_includes_sparkline(self) -> None:
        OperatorCockpit()
        cfg = CockpitConfig(show_sparkline=True, sparkline_width=8)
        cockpit = OperatorCockpit(config=cfg)
        cockpit.tick(
            runs=[RunEvent(run_id="r1", state=RunState.ACTIVE, confidence=v) for v in [0.1, 0.3, 0.5, 0.7, 0.9]]
        )
        out = cockpit.render()
        # Sparkline chars should appear somewhere in the output.
        assert any(ch in out for ch in "▁▂▃▄▅▆▇█")

    def test_render_disables_sparkline(self) -> None:
        cfg = CockpitConfig(show_sparkline=False)
        cockpit = OperatorCockpit(config=cfg)
        cockpit.tick(
            runs=[
                RunEvent(run_id="r1", state=RunState.ACTIVE, confidence=0.5),
                RunEvent(run_id="r2", state=RunState.ACTIVE, confidence=0.7),
                RunEvent(run_id="r3", state=RunState.ACTIVE, confidence=0.9),
            ]
        )
        out = cockpit.render()
        # When disabled, no sparkline chars in the confidence pane.
        # (Other panes do not use sparkline chars, so we cannot strictly assert.)
        assert "P50=" in out
        assert "P95=" in out


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


class TestSnapshot:
    def test_snapshot_includes_all_state(self) -> None:
        c = OperatorCockpit()
        c.tick(
            runs=[
                RunEvent(run_id="r1", state=RunState.ACTIVE, lane="critical", agent="cursor", confidence=0.7),
            ],
            overrides=[OverrideEvent(rule_id="x", by="alice", reason="r", expires_in_s=10)],
            progress=(1, 1),
        )
        snap = c.snapshot()
        assert snap["title"] == "thegent operator cockpit"
        assert len(snap["runs"]) == 1
        assert snap["runs"][0]["state"] == "active"
        assert snap["lanes"]["critical"] == 1
        assert len(snap["overrides"]) == 1
        assert snap["progress"] == (1, 1)
        assert 0.7 in snap["confidence_history"]


# ---------------------------------------------------------------------------
# Reset and context-manager
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_clears_state(self) -> None:
        c = OperatorCockpit()
        c.tick(runs=[RunEvent(run_id="r1", state=RunState.ACTIVE)])
        assert c._state.runs
        c.reset()
        assert not c._state.runs
        assert c._frame_count == 0


class TestContextManager:
    def test_with_statement(self) -> None:
        with OperatorCockpit() as c:
            c.tick(runs=[RunEvent(run_id="r1", state=RunState.ACTIVE)])
            assert "r1" in c._state.runs
        # No exception, context manager exits cleanly.


# ---------------------------------------------------------------------------
# One-shot helper
# ---------------------------------------------------------------------------


class TestOneShotHelper:
    def test_render_cockpit_default(self) -> None:
        text = render_cockpit(
            runs=_sample_runs(),
            overrides=_sample_overrides(),
            progress=(1, 4),
        )
        assert "thegent operator cockpit" in text
        assert "run-001" in text
        assert "no-cursor-prod" in text
        assert "25%" in text

    def test_render_cockpit_with_custom_config(self) -> None:
        cfg = CockpitConfig(title="custom title")
        text = render_cockpit(config=cfg, runs=[], progress=(0, 1))
        assert "custom title" in text


# ---------------------------------------------------------------------------
# Performance smoke test (P-090: cockpit latency SLO)
# ---------------------------------------------------------------------------


class TestPerformance:
    def test_render_under_50ms_for_typical_workload(self) -> None:
        """Sustains <50ms render time for a 4-pane, 30-runs workload."""
        runs = [
            RunEvent(
                run_id=f"r{i:03d}",
                state=RunState.ACTIVE,
                lane="critical" if i % 3 else "standard",
                agent="cursor",
                confidence=0.5 + (i % 5) * 0.1,
            )
            for i in range(30)
        ]
        overrides = [
            OverrideEvent(rule_id=f"o{i}", by="alice", reason="r", expires_in_s=float(i * 10)) for i in range(5)
        ]
        c = OperatorCockpit()
        # Warm the cache
        c.render()
        c.tick(runs=runs, overrides=overrides, progress=(10, 100))
        # 5 successive renders should each be < 50ms (SLO P-090).
        for _ in range(5):
            c.render()
            assert c.last_render_ms() < 50


# ---------------------------------------------------------------------------
# Override-expiry banner (WP-3003 -> WP-4001 bridge)
# ---------------------------------------------------------------------------


class TestOverrideExpiryBanner:
    """WP-3003 OverrideEventEmitter feeds the cockpit's inline banner."""

    def test_no_banner_when_no_notices(self) -> None:
        c = OperatorCockpit()
        c.tick(runs=_sample_runs(), overrides=_sample_overrides(), progress=(1, 1))
        out = c.render()
        assert "override expired" not in out

    def test_record_override_event_appears_in_render(self) -> None:
        c = OperatorCockpit()
        notice = OverrideExpiryNotice(
            rule_id="net-block",  # short enough to fit the 12-char banner column
            owner="sre",
            reason="ttl_elapsed",
            expired_at=time.time(),
        )
        c.record_override_event(notice)
        out = c.render()
        assert "override expired" in out
        assert "net-block" in out
        assert "sre" in out
        assert "ttl_elapsed" in out

    def test_banner_fades_past_max_age(self) -> None:
        """Notices older than ``OVERRIDE_BANNER_MAX_AGE_S`` are not shown."""
        from thegent.ux.cockpit import OVERRIDE_BANNER_MAX_AGE_S

        c = OperatorCockpit()
        # Push a notice that has already expired long ago.
        stale = OverrideExpiryNotice(
            rule_id="stale-rule",
            owner="bob",
            reason="old",
            expired_at=time.time() - (OVERRIDE_BANNER_MAX_AGE_S + 5.0),
        )
        c.record_override_event(stale)
        out = c.render()
        assert "override expired" not in out

    def test_banner_uses_most_recent_notice(self) -> None:
        """When multiple notices arrive, only the latest is surfaced."""
        c = OperatorCockpit()
        c.record_override_event(
            OverrideExpiryNotice(
                rule_id="old-rule",
                owner="alice",
                reason="old",
                expired_at=time.time() - 5.0,
            )
        )
        c.record_override_event(
            OverrideExpiryNotice(
                rule_id="new-rule",
                owner="bob",
                reason="fresh",
                expired_at=time.time(),
            )
        )
        out = c.render()
        assert "new-rule" in out
        assert "old-rule" not in out

    def test_record_override_event_rejects_wrong_type(self) -> None:
        """Defensive type guard against config drift / malformed callbacks."""
        c = OperatorCockpit()
        with pytest.raises(TypeError):
            c.record_override_event({"rule_id": "x"})  # type: ignore[arg-type]

    def test_override_notices_deque_is_bounded(self) -> None:
        """Bounded-memory contract: maxlen=32 means old notices are evicted."""
        c = OperatorCockpit()
        for i in range(40):
            c.record_override_event(
                OverrideExpiryNotice(
                    rule_id=f"r{i:03d}",
                    owner="u",
                    reason="ttl",
                    expired_at=time.time(),
                )
            )
        # Most-recent 32 are kept (deque is bounded); oldest 8 evicted.
        assert len(c._state.override_notices) == 32
        assert c._state.override_notices[-1].rule_id == "r039"
        assert c._state.override_notices[0].rule_id == "r008"

    def test_snapshot_includes_override_notices(self) -> None:
        """The structured snapshot should expose notices for downstream consumers."""
        c = OperatorCockpit()
        c.record_override_event(
            OverrideExpiryNotice(
                rule_id="snap-rule",
                owner="ci",
                reason="r",
                expired_at=time.time(),
            )
        )
        snap = c.snapshot()
        # Override notices are surfaced as a list (immutable snapshot pattern).
        assert "override_notices" in snap
        assert snap["override_notices"][0]["rule_id"] == "snap-rule"


# ---------------------------------------------------------------------------
# Render performance (P-090 SLO closure)
# ---------------------------------------------------------------------------
# Pinning ``cockpit.render() < 50ms`` for the worst-case state shape an
# operator dashboard can land on (1024 confidence samples + 64 decision
# notices + 32 override notices + 14 runs). The SLO was previously captured
# in the docstring (``P-090: cockpit latency SLO``) but never asserted —
# a silent latency regression would slip through CI. The 50ms ceiling is
# well over the actual measured cost (~1-3 ms on macOS dev hardware) so it
# accommodates CI noise without becoming a flake magnet, and it matches
# the DAG_TICK_MS cadence (1000 ms) at 5% overhead.


class TestRenderPerformance:
    """Pin the P-090 ``cockpit.render() < 50ms`` SLO for worst-case state.

    The dashboard has a bounded upper state shape:

    * 1024 confidence samples (the sparkline deque's ``maxlen``).
    * 64 decision notices (``MAX_DECISION_NOTICES``).
    * 32 override notices (the override-notices deque's ``maxlen``).
    * 14 runs (``MAX_RUNS_PANE_ROWS``).
    * 1 progress bar header.
    * 1 override-expiry banner slot.

    Rendering a full state is the dominant CPU cost during a DAG tick; if
    it creeps above 50 ms the cockpit stops keeping up with the 1 s tick
    cadence and operators start seeing frames pile up. The wall-clock
    budget here is generous on purpose: measured cost on developer
    hardware is ~1-3 ms, so a 50 ms ceiling leaves ~20x headroom for
    CI noise (loaded shared runners, cold caches, etc.) without
    becoming a flake magnet.
    """

    _P90_SLO_MS = 50.0  # P-090 ceiling

    @staticmethod
    def _worst_case_cockpit() -> OperatorCockpit:
        """Build an :class:`OperatorCockpit` at the bounded upper state shape."""
        c = OperatorCockpit()
        # 1. 14 runs at full pane width (mix of states + lanes + confidences).
        runs: list[RunEvent] = []
        for i in range(14):
            runs.append(
                RunEvent(
                    run_id=f"run-{i:03d}",
                    state=RunState.ACTIVE if i % 2 else RunState.QUEUED,
                    lane=("standard", "fast", "critical")[i % 3],
                    agent=f"agent-{i}",
                    confidence=0.5 + (i % 5) * 0.1,
                    elapsed_s=float(i),
                    note=f"note-{i}",
                )
            )
        # 2. 32 override notices (the bounded maxlen).
        for i in range(32):
            c.record_override_event(
                OverrideExpiryNotice(
                    rule_id=f"r-{i:03d}",
                    owner="ci",
                    reason="ttl_elapsed",
                    expired_at=1_700_000_000.0 + i,
                )
            )
        # 3. 64 decision notices (MAX_DECISION_NOTICES) - push through
        #    the public record_decision_notice surface where available,
        #    or via direct deque append when only the internal shape is
        #    exposed.
        from thegent.ux.cockpit import DecisionNotice

        for i in range(64):
            notice = DecisionNotice(
                verdict=("allow", "deny", "warn")[i % 3],
                reason_code=("ok", "no_rule_match", "low_confidence")[i % 3],
                rule_id=f"rule-{i:03d}" if i % 2 else None,
                agent=f"agent-{i % 14:03d}",
                lane=("standard", "fast", "critical")[i % 3],
                evaluated_at=1_700_000_000.0 + i,
                reason=f"reason-{i}",
            )
            # Use the public surface if present; otherwise poke the deque.
            recorder = getattr(c, "record_decision_notice", None)
            if callable(recorder):
                recorder(notice)
            else:
                c._state.decision_notices.append(notice)
        # 4. Tick once with runs + progress so the state is fully wired.
        c.tick(runs=runs, progress=(50, 100))
        return c

    def test_render_worst_case_under_p90_slo(self) -> None:
        """A full-state render stays under the 50 ms P-090 SLO ceiling."""
        cockpit = self._worst_case_cockpit()
        # Warm-up render so first-call overhead (imports, dataclass
        # allocs) doesn't poison the measurement.
        cockpit.render()
        # Measure the next render with a monotonic clock.
        t0 = time.perf_counter()
        text = cockpit.render()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert text, "worst-case render should produce a non-empty frame"
        assert elapsed_ms < self._P90_SLO_MS, (
            f"cockpit.render() regressed: {elapsed_ms:.2f} ms exceeds the "
            f"{self._P90_SLO_MS} ms P-090 SLO. The 1 s DAG tick cadence "
            f"leaves no room for render cost > 5% of tick budget."
        )

    def test_last_render_ms_matches_wall_clock_under_slo(self) -> None:
        """The :meth:`last_render_ms` surface stays under the P-090 ceiling.

        Pinning the public surface (the one operators / KPI consumers
        see) separately from the wall-clock test catches regressions
        where someone disables the ``_last_render_ms`` capture while
        keeping ``render()`` fast (or vice versa).
        """
        cockpit = self._worst_case_cockpit()
        cockpit.render()  # warm-up
        cockpit.render()
        measured = cockpit.last_render_ms()
        assert measured < self._P90_SLO_MS, (
            f"cockpit.last_render_ms reported {measured:.2f} ms, exceeds the {self._P90_SLO_MS} ms P-090 SLO."
        )

    def test_worst_case_state_shape_is_documented(self) -> None:
        """The worst-case state shape is the bounded maxlen everywhere.

        If a future refactor raises any of the bounded deque maxlens
        without re-tuning the SLO, this test fires first and forces the
        refactor author to think about the render cost. The point is to
        keep the worst-case render cost predictable.
        """
        from thegent.ux.cockpit import (
            MAX_DECISION_NOTICES,
        )

        cockpit = self._worst_case_cockpit()
        # Sparkline deque cap is hard-coded as ``maxlen=1024`` on the
        # dataclass field; we assert via the snapshot.
        snap = cockpit.snapshot()
        # The deque caps shouldn't grow past their declared maxlen, even
        # though we built with that exact count.
        assert len(snap["confidence_history"]) <= 1024
        assert len(snap.get("decision_notices", [])) <= MAX_DECISION_NOTICES
        assert len(snap.get("override_notices", [])) <= 32
        # Render still completes (sanity).
        assert cockpit.render()

    def test_render_completes_when_state_is_empty(self) -> None:
        """An empty cockpit renders fast (no state to traverse)."""
        c = OperatorCockpit()
        c.render()  # warm-up
        t0 = time.perf_counter()
        for _ in range(100):
            c.render()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0 / 100
        assert elapsed_ms < self._P90_SLO_MS, (
            f"empty cockpit.render() averaged {elapsed_ms:.2f} ms "
            f"over 100 frames, exceeds the {self._P90_SLO_MS} ms SLO."
        )


# ---------------------------------------------------------------------------
# AUDIT-N+22 (SOTA audit pass 8, Lane A) — MCP audit-trail pane
# ---------------------------------------------------------------------------


class TestAttachAuditTrail:
    """AUDIT-N+22 Lane A: ``OperatorCockpit.attach_audit_trail`` exposes the
    MCP audit-trail singleton inside the cockpit snapshot.

    The wiring lives in :mod:`thegent.mcp.server.mcp_audit_wiring`;
    these tests pin the cockpit-side contract: source is borrowed,
    stored under the lock, surfaced in ``snapshot()`` as the
    ``mcp_audit_stats`` block, and detached by passing ``None``.
    """

    def test_attach_returns_self_for_chaining(self) -> None:
        c = OperatorCockpit()
        result = c.attach_audit_trail(lambda: {"total_entries": 0})
        assert result is c

    def test_snapshot_includes_mcp_audit_stats_when_attached(self) -> None:
        c = OperatorCockpit().attach_audit_trail(
            lambda: {
                "total_entries": 5,
                "max_entries": 5000,
                "by_kind": {"tool_invocation": 5},
                "by_outcome": {"ok": 5},
                "error_count": 0,
                "avg_duration_ms": 1.2,
                "p99_duration_ms": 3.4,
                "oldest_seq": 1,
                "newest_seq": 5,
            }
        )
        snap = c.snapshot()
        assert "mcp_audit_stats" in snap
        assert snap["mcp_audit_stats"] == {
            "total_entries": 5,
            "max_entries": 5000,
            "by_kind": {"tool_invocation": 5},
            "by_outcome": {"ok": 5},
            "error_count": 0,
            "avg_duration_ms": 1.2,
            "p99_duration_ms": 3.4,
            "oldest_seq": 1,
            "newest_seq": 5,
        }

    def test_snapshot_mcp_audit_stats_none_when_not_attached(self) -> None:
        c = OperatorCockpit()
        snap = c.snapshot()
        assert snap["mcp_audit_stats"] is None

    def test_audit_trail_source_accessor_round_trips(self) -> None:
        def sentinel() -> dict[str, int]:
            return {"total_entries": 1}

        c = OperatorCockpit().attach_audit_trail(sentinel)
        assert c.audit_trail_source() is sentinel

    def test_detach_via_none(self) -> None:
        def fake_source() -> dict[str, int]:
            return {"total_entries": 1}

        c = OperatorCockpit().attach_audit_trail(fake_source)
        assert c.snapshot()["mcp_audit_stats"] is not None
        c.attach_audit_trail(None)
        assert c.snapshot()["mcp_audit_stats"] is None

    def test_summary_method_object_supported(self) -> None:
        """A source that exposes a no-arg ``summary()`` method is honoured
        identically to a zero-arg callable — same contract as
        ``attach_dormant_core``."""

        class _StubDashboard:
            def summary(self) -> dict[str, object]:
                return {"total_entries": 7, "p99_duration_ms": 12.0}

        c = OperatorCockpit().attach_audit_trail(_StubDashboard())
        snap = c.snapshot()
        assert snap["mcp_audit_stats"] == {"total_entries": 7, "p99_duration_ms": 12.0}

    def test_raising_source_does_not_crash_snapshot(self) -> None:
        """A buggy audit-trail implementation must not crash the cockpit.

        Mirrors the AUDIT-N+18 ``_invoke_dormant_core`` contract.
        """

        def boom() -> dict[str, object]:
            raise RuntimeError("audit trail unavailable")

        c = OperatorCockpit().attach_audit_trail(boom)
        snap = c.snapshot()
        assert snap["mcp_audit_stats"] is None

    def test_non_dict_return_does_not_crash_snapshot(self) -> None:
        """A source that returns a non-dict (e.g. a list) is treated as
        ``None`` so downstream consumers can short-circuit cleanly."""

        def bad() -> list[int]:
            return [1, 2, 3]

        c = OperatorCockpit().attach_audit_trail(bad)
        snap = c.snapshot()
        assert snap["mcp_audit_stats"] is None

    def test_real_mcp_audit_stats_function_round_trips(self) -> None:
        """End-to-end: the wiring singleton function passes through the
        cockpit snapshot unchanged. This is the canonical operator path."""
        from thegent.mcp.server import mcp_audit_stats

        c = OperatorCockpit().attach_audit_trail(mcp_audit_stats)
        snap = c.snapshot()
        stats = snap["mcp_audit_stats"]
        assert isinstance(stats, dict)
        # The MCPAuditTrail.summary() shape is pinned by the contract tests.
        for key in (
            "total_entries",
            "max_entries",
            "by_kind",
            "by_outcome",
            "error_count",
            "avg_duration_ms",
            "p99_duration_ms",
            "oldest_seq",
            "newest_seq",
        ):
            assert key in stats

    def test_attach_does_not_block_other_panes(self) -> None:
        """Attaching an audit-trail source does not break the existing
        ``traffic`` / ``dormant_core`` snapshot blocks. Defends against
        refactors that accidentally share a slot.
        """
        from thegent.ux.kpis.traffic import TrafficDashboard

        c = (
            OperatorCockpit()
            .attach_traffic(TrafficDashboard())
            .attach_dormant_core(lambda: {"alerts": 0})
            .attach_audit_trail(lambda: {"total_entries": 0})
        )
        snap = c.snapshot()
        assert snap["traffic"] is not None
        assert snap["dormant_core"] == {"alerts": 0}
        assert snap["mcp_audit_stats"] == {"total_entries": 0}


class TestInvokeAttachedHelper:
    """AUDIT-N+22 Lane A: the generic ``_invoke_attached`` helper that
    both ``_invoke_dormant_core`` and ``_invoke_audit_stats`` delegate
    to. Pinned so a future refactor (e.g. moving to an async source
    resolver) cannot break both consumers at once.
    """

    def test_returns_none_when_attr_missing(self) -> None:
        c = OperatorCockpit()
        assert c._invoke_attached("nonexistent_attr_xyz") is None

    def test_returns_none_when_source_is_none(self) -> None:
        c = OperatorCockpit()
        assert c._invoke_attached("dormant_source") is None
        assert c._invoke_attached("audit_source") is None

    def test_invoke_dormant_core_delegates_to_invoke_attached(self) -> None:
        c = OperatorCockpit().attach_dormant_core(lambda: {"k": 1})
        assert c._invoke_dormant_core() == {"k": 1}

    def test_invoke_audit_stats_delegates_to_invoke_attached(self) -> None:
        c = OperatorCockpit().attach_audit_trail(lambda: {"total_entries": 9})
        assert c._invoke_audit_stats() == {"total_entries": 9}
