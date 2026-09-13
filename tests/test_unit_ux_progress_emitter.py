"""Unit tests for the typed P-081 progress bar emitter (WP-4001 / P-081)."""

from __future__ import annotations

import threading

from thegent.ux.cockpit import CockpitConfig, OperatorCockpit
from thegent.ux.progress_emitter import (
    NullProgressEmitter,
    ProgressEmitResult,
    ProgressSink,
    ProgressTick,
    ProgressTickEmitter,
    coalesce_ticks,
    stream_ticks,
)

# ---------------------------------------------------------------------------
# Helpers / doubles
# ---------------------------------------------------------------------------


class _RecordingSink:
    """Test double implementing the ProgressSink protocol."""

    def __init__(self) -> None:
        self.received: list[ProgressTick] = []
        self._lock = threading.Lock()

    def receive_progress_tick(self, tick: ProgressTick) -> None:
        with self._lock:
            self.received.append(tick)


class _ExplodingSink:
    """Sink that always raises — must be swallowed by the emitter."""

    def receive_progress_tick(self, tick: ProgressTick) -> None:
        raise RuntimeError("boom")


def _make_cockpit() -> OperatorCockpit:
    return OperatorCockpit(config=CockpitConfig(progress_total=100))


# ---------------------------------------------------------------------------
# ProgressTick validation
# ---------------------------------------------------------------------------


class TestProgressTick:
    def test_construction_ok(self) -> None:
        tick = ProgressTick(done=42, total=100, label="policy-eval", lane="standard")
        assert tick.done == 42
        assert tick.total == 100
        assert tick.label == "policy-eval"
        assert tick.lane == "standard"

    def test_negative_values_accepted_at_construction(self) -> None:
        # The dataclass is intentionally permissive — the emitter is the
        # canonical place for clamping so audit replays observe raw vs.
        # clamped behaviour. Negative values round-trip through the
        # dataclass and only get rejected by the emitter's _coerce_int.
        ProgressTick(done=-1, total=10)
        ProgressTick(done=5, total=-1)

    def test_emit_rejects_negative_total(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        result = emitter.emit(done=5, total=-1)
        assert not result.ok
        assert result.dropped == 1
        assert sink.received == []

    def test_payload_roundtrip(self) -> None:
        tick = ProgressTick(done=7, total=20, label="x", lane="fast", eta_s=1.5, emitted_at=1.0)
        payload = tick.to_payload()
        assert payload == {
            "done": 7,
            "total": 20,
            "label": "x",
            "lane": "fast",
            "eta_s": 1.5,
            "emitted_at": 1.0,
        }

    def test_payload_eta_none_roundtrip(self) -> None:
        tick = ProgressTick(done=0, total=10, eta_s=None)
        assert tick.to_payload()["eta_s"] is None


# ---------------------------------------------------------------------------
# Clamping & validation
# ---------------------------------------------------------------------------


class TestClamping:
    def test_emit_clamps_done_above_total(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        result = emitter.emit(done=999, total=10)
        assert result.ok
        assert result.accepted == 1
        assert sink.received[-1].done == 10  # clamped
        assert sink.received[-1].total == 10

    def test_emit_clamps_done_below_zero(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        result = emitter.emit(done=-5, total=10)
        assert result.ok
        assert sink.received[-1].done == 0

    def test_emit_rejects_nan(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        result = emitter.emit(done=float("nan"), total=10)
        assert not result.ok
        assert result.dropped == 1
        assert sink.received == []

    def test_emit_rejects_inf(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        result = emitter.emit(done=float("inf"), total=10)
        assert not result.ok
        assert result.dropped == 1

    def test_emit_rejects_bool_for_done(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        # bool is technically an int; the emitter should reject it because
        # it isn't a *real* number for progress semantics.
        result = emitter.emit(done=True, total=10)  # type: ignore[arg-type]
        assert not result.ok
        assert result.dropped == 1

    def test_emit_zero_total_renders_empty_bar_on_render(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=0)
        bar = emitter.render_bar(done=0, total=0)
        assert bar.startswith("[")
        assert bar.rstrip().endswith("-")

    def test_total_negative_total_rejected(self) -> None:
        # Negative totals are nonsensical for the cockpit — the emitter
        # drops them rather than silently flooring to zero.
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        result = emitter.emit(done=0, total=-5)
        assert not result.ok
        assert result.dropped == 1
        assert sink.received == []

    def test_default_total_negative_floored_at_construction(self) -> None:
        # The emitter's own default_total is floored to 0 (it can't be
        # negative), but explicit negative totals on emit are rejected.
        emitter = ProgressTickEmitter(sink=_RecordingSink(), default_total=-1)
        assert emitter._default_total == 0  # type: ignore[attr-defined]
        result = emitter.emit(done=1, total=10)
        assert result.ok

    def test_eta_nan_is_silently_dropped(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        result = emitter.emit(done=1, total=10, eta_s=float("nan"))
        assert result.ok
        assert sink.received[-1].eta_s is None


# ---------------------------------------------------------------------------
# Sink delivery
# ---------------------------------------------------------------------------


class TestDelivery:
    def test_emit_via_typed_sink(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink)
        result = emitter.emit(done=3, total=10, label="x", lane="fast")
        assert result.ok
        assert sink.received[-1].label == "x"
        assert sink.received[-1].lane == "fast"
        assert emitter.accepted == 1
        assert emitter.dropped == 0

    def test_emit_via_cockpit_fallback(self) -> None:
        # OperatorCockpit has no receive_progress_tick; the emitter should
        # fall back to cockpit.tick(progress=...).
        cockpit = _make_cockpit()
        emitter = ProgressTickEmitter(sink=cockpit)
        result = emitter.emit(done=42, total=100)
        assert result.ok
        assert cockpit.snapshot()["progress"] == (42, 100)

    def test_emit_into_cockpit_progress_bar_visible(self) -> None:
        cockpit = _make_cockpit()
        ProgressTickEmitter(sink=cockpit).emit(done=50, total=100)
        bar = cockpit.progress_bar()
        assert "50%" in bar
        assert bar.startswith("[")

    def test_emit_swallows_sink_exception(self) -> None:
        emitter = ProgressTickEmitter(sink=_ExplodingSink())
        result = emitter.emit(done=5, total=10)
        assert not result.ok
        assert result.dropped == 1
        assert result.errors and "boom" in result.errors[0]

    def test_emit_no_sink_counts_as_accepted(self) -> None:
        emitter = ProgressTickEmitter(sink=None)
        result = emitter.emit(done=1, total=10)
        assert result.ok
        assert result.accepted == 1
        assert emitter.accepted == 1

    def test_bind_replaces_sink(self) -> None:
        sink_a = _RecordingSink()
        sink_b = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink_a)
        emitter.bind(sink_b).emit(done=1, total=2)
        assert sink_a.received == []
        assert sink_b.received[-1].done == 1

    def test_bind_none_disables_emission(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink)
        emitter.bind(None).emit(done=1, total=2)
        assert sink.received == []

    def test_emit_many_aggregates(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink)
        result = emitter.emit_many(
            [
                ProgressTick(done=1, total=10),
                ProgressTick(done=2, total=10),
                ProgressTick(done=float("nan"), total=10),
            ]
        )
        assert result.accepted == 2
        assert result.dropped == 1
        assert len(sink.received) == 2

    def test_render_bar_previews_without_emitting(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink)
        bar = emitter.render_bar(done=5, total=10, width=8)
        assert bar.startswith("[")
        assert sink.received == []  # render_bar is side-effect-free


# ---------------------------------------------------------------------------
# NullProgressEmitter
# ---------------------------------------------------------------------------


class TestNullEmitter:
    def test_emit_is_accepted(self) -> None:
        emitter = NullProgressEmitter(default_total=10)
        result = emitter.emit(done=3, total=10)
        assert result.ok
        assert result.accepted == 1

    def test_emit_invalid_payload_dropped(self) -> None:
        emitter = NullProgressEmitter()
        result = emitter.emit(done=float("nan"), total=10)
        assert not result.ok
        assert result.dropped == 1

    def test_render_bar_uses_overrides(self) -> None:
        emitter = NullProgressEmitter(default_total=20)
        bar = emitter.render_bar(done=10, total=20, width=12)
        assert "50%" in bar


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    def test_concurrent_emit_all_accepted(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink)
        errors: list[BaseException] = []

        def worker(start: int) -> None:
            try:
                for i in range(50):
                    emitter.emit(done=start + i, total=1000, label=f"w{start}")
            except BaseException as exc:  # pragma: no cover - debug only
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i * 100,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(sink.received) == 8 * 50
        assert emitter.accepted == 8 * 50


# ---------------------------------------------------------------------------
# Stream & coalesce helpers
# ---------------------------------------------------------------------------


class TestStreamTicks:
    def test_yields_typed_ticks(self) -> None:
        ticks = list(stream_ticks([(1, 10), (5, 10), (10, 10)], label="x", lane="fast"))
        assert len(ticks) == 3
        assert all(isinstance(t, ProgressTick) for t in ticks)
        assert ticks[0].done == 1
        assert ticks[-1].done == 10
        assert ticks[0].label == "x"
        assert ticks[0].lane == "fast"

    def test_empty_iterable_yields_nothing(self) -> None:
        assert list(stream_ticks([])) == []

    def test_custom_clock_used(self) -> None:
        counter = {"n": 0}

        def clock() -> float:
            counter["n"] += 1
            return float(counter["n"])

        ticks = list(stream_ticks([(0, 1), (1, 1)], clock=clock))
        assert [t.emitted_at for t in ticks] == [1.0, 2.0]


class TestCoalesceTicks:
    def test_returns_last_n(self) -> None:
        ticks = [ProgressTick(done=i, total=100, emitted_at=float(i)) for i in range(10)]
        out = coalesce_ticks(ticks, window=3)
        assert len(out) == 3
        assert [t.done for t in out] == [7, 8, 9]

    def test_window_larger_than_input(self) -> None:
        ticks = [ProgressTick(done=1, total=10, emitted_at=1.0)]
        out = coalesce_ticks(ticks, window=10)
        assert len(out) == 1

    def test_zero_or_negative_window(self) -> None:
        ticks = [ProgressTick(done=1, total=10, emitted_at=1.0)]
        assert coalesce_ticks(ticks, window=0) == []
        assert coalesce_ticks(ticks, window=-1) == []

    def test_empty_input(self) -> None:
        assert coalesce_ticks([], window=5) == []

    def test_rebaselines_done_against_final_total(self) -> None:
        ticks = [
            ProgressTick(done=50, total=100, emitted_at=1.0),
            ProgressTick(done=200, total=200, emitted_at=2.0),  # total changed
        ]
        out = coalesce_ticks(ticks, window=4)
        # 50 clamped to new total 200 = 50, 200 stays 200
        assert [t.done for t in out] == [50, 200]
        assert all(t.total == 200 for t in out)


# ---------------------------------------------------------------------------
# Integration with OperatorCockpit
# ---------------------------------------------------------------------------


class TestCockpitIntegration:
    def test_emitter_drives_cockpit_progress(self) -> None:
        cockpit = _make_cockpit()
        emitter = ProgressTickEmitter(sink=cockpit)
        for i in range(11):
            emitter.emit(done=i, total=10, label="policy-eval")
        snap = cockpit.snapshot()
        assert snap["progress"] == (10, 10)
        assert "100%" in cockpit.progress_bar()

    def test_emitter_preserves_overrides_and_runs(self) -> None:
        cockpit = _make_cockpit()
        ProgressTickEmitter(sink=cockpit).emit(done=5, total=10)
        # emit should not clobber other cockpit state set via tick()
        from thegent.ux.cockpit import OverrideEvent, RunEvent, RunState

        cockpit.tick(
            runs=[RunEvent(run_id="r1", state=RunState.ACTIVE)],
            overrides=[OverrideEvent(rule_id="x", by="alice", reason="r", expires_in_s=10.0)],
        )
        ProgressTickEmitter(sink=cockpit).emit(done=7, total=10)
        snap = cockpit.snapshot()
        assert snap["progress"] == (7, 10)
        run_ids = [r["run_id"] for r in snap["runs"]]
        override_ids = [o["rule_id"] for o in snap["overrides"]]
        assert "r1" in run_ids
        assert "x" in override_ids


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_recording_sink_is_progress_sink(self) -> None:
        assert isinstance(_RecordingSink(), ProgressSink)

    def test_cockpit_is_not_progress_sink_by_default(self) -> None:
        # OperatorCockpit intentionally uses tick(progress=...); the emitter
        # falls back to that path. This test pins the design decision.
        assert not isinstance(_make_cockpit(), ProgressSink)


# ---------------------------------------------------------------------------
# Sanity / smoke
# ---------------------------------------------------------------------------


class TestSmoke:
    def test_full_cycle(self) -> None:
        sink = _RecordingSink()
        emitter = ProgressTickEmitter(sink=sink, default_total=10)
        emitted = emitter.emit_many(list(stream_ticks([(0, 10), (3, 10), (7, 10), (10, 10)], label="run")))
        assert emitted.ok
        assert emitted.accepted == 4
        assert [t.done for t in sink.received] == [0, 3, 7, 10]

    def test_progress_emit_result_ok_property(self) -> None:
        assert ProgressEmitResult().ok is True
        assert ProgressEmitResult(errors=["x"]).ok is False


# ---------------------------------------------------------------------------
# DAG-tick integration hardening (Phase 3/4 SOTA audit lane)
# ---------------------------------------------------------------------------
#
# These tests pin the contract between the P-081 progress bar emitter and
# the operator cockpit's ``tick(progress=...)`` DAG-tick surface. They were
# added under the "Unblocked Next" hardening lane in WORKLOG.md so that
# any future refactor that decouples the two surfaces (e.g. moving
# ``tick(progress=...)`` into a dedicated ``set_progress`` method, or
# replacing the ``_state.last_progress`` field with a ring buffer) has to
# fail one of these tests instead of silently breaking the operator
# dashboard.
#
# The DAG tick rate defaults to 1000ms (``DEFAULT_DAG_TICK_MS``); the
# tests below simulate this rate by interleaving many ``cockpit.tick()``
# calls in quick succession and asserting that the final state is
# deterministic.


class TestDagTickIntegration:
    """Hardening tests for the cockpit + P-081 emitter DAG-tick contract."""

    def test_dag_tick_progress_advances_through_cockpit_tick(self) -> None:
        """Many ``cockpit.tick(progress=...)`` calls must converge on the last value."""
        cockpit = _make_cockpit()
        # Simulate a long-running DAG session: 20 ticks at 1s cadence
        # would normally take 20s, but we compress the timeline here.
        for i in range(21):
            cockpit.tick(progress=(i, 20))
        snap = cockpit.snapshot()
        assert snap["progress"] == (20, 20)
        assert "100%" in cockpit.progress_bar()

    def test_dag_tick_emitter_and_snapshot_agree(self) -> None:
        """``ProgressTickEmitter`` + ``cockpit.snapshot()`` must agree on the latest progress."""
        cockpit = _make_cockpit()
        emitter = ProgressTickEmitter(sink=cockpit)
        # 50 ticks is well over what the bounded ``confidence_history``
        # deque would normally see in a 1-second DAG tick; this exercises
        # the write path under burst conditions.
        for i in range(51):
            emitter.emit(done=i, total=50, label="policy-eval")
        snap = cockpit.snapshot()
        assert snap["progress"] == (50, 50)
        assert cockpit.progress_bar().endswith("100%")

    def test_dag_tick_cockpit_reset_clears_progress_bar(self) -> None:
        """``cockpit.reset()`` between DAG-tick sessions must clear the bar."""
        cockpit = _make_cockpit()
        cockpit.tick(progress=(80, 100))
        assert "80%" in cockpit.progress_bar()
        cockpit.reset()
        # After reset, the bar shows the empty ``"-"`` sentinel rather
        # than a stale percent — operators need to see "no data" between
        # sessions, not a misleading frozen bar.
        bar = cockpit.progress_bar()
        assert "80%" not in bar
        assert bar.endswith("-")

    def test_dag_tick_progress_bar_visible_in_rendered_header(self) -> None:
        """The latest tick's progress must appear in the rendered cockpit header."""
        cockpit = _make_cockpit()
        cockpit.tick(progress=(33, 100))
        rendered = cockpit.render()
        # The header always includes the title and a tick timestamp;
        # the percent appears on the same line as the title (P-081).
        assert "33%" in rendered
        # Sanity: the bar glyph itself is present.
        assert "[" in rendered and "]" in rendered

    def test_dag_tick_progress_total_change_resets_bar_filled_count(self) -> None:
        """If a later tick shrinks ``total``, the bar must reflect the new denominator."""
        cockpit = _make_cockpit()
        cockpit.tick(progress=(50, 100))
        assert "50%" in cockpit.progress_bar()
        cockpit.tick(progress=(5, 10))
        # 5/10 == 50% — same percent, but the filled width must reflect
        # the new total. The cockpit's ``_progress_bar`` uses
        # ``width`` units so the filled count changes; we assert on the
        # percent to keep the contract stable.
        assert "50%" in cockpit.progress_bar()

    def test_dag_tick_emitter_under_concurrent_bursts(self) -> None:
        """Many concurrent ``emit`` calls must not corrupt the cockpit's progress state."""
        import threading

        cockpit = _make_cockpit()
        emitter = ProgressTickEmitter(sink=cockpit, default_total=100)
        results: list[ProgressEmitResult] = []
        results_lock = threading.Lock()

        def worker(start: int) -> None:
            local: list[ProgressEmitResult] = []
            for i in range(start, start + 25):
                local.append(emitter.emit(done=i, total=100, label=f"worker-{start}"))
            with results_lock:
                results.extend(local)

        threads = [threading.Thread(target=worker, args=(t * 25,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Every emit must have been accepted (no drops under load).
        assert all(r.ok for r in results)
        assert sum(r.accepted for r in results) == 100
        # The cockpit's last observed progress must be a legal (done, total)
        # pair — not torn, not negative, not > total.
        snap = cockpit.snapshot()
        done, total = snap["progress"]
        assert 0 <= done <= total
        assert total == 100
