"""Unit tests for the real-time TRAFFIC KPI dashboard (WP-Y7, P-081)."""

from __future__ import annotations

import time

import pytest

from thegent.ux.kpis.traffic import (
    TrafficDashboard,
    TrafficEvent,
    TrafficWindow,
    progress_bar,
    render_traffic,
    render_trend,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Sanity
# ---------------------------------------------------------------------------


class TestSanity:
    def test_public_api(self) -> None:
        from thegent.ux.kpis import traffic as t

        for name in (
            "TrafficDashboard",
            "TrafficEvent",
            "TrafficWindow",
            "progress_bar",
            "render_traffic",
            "render_trend",
        ):
            assert hasattr(t, name), f"missing public symbol: {name}"


# ---------------------------------------------------------------------------
# progress_bar
# ---------------------------------------------------------------------------


class TestProgressBar:
    def test_zero_total(self) -> None:
        assert progress_bar(0, 0).startswith("[")

    def test_full(self) -> None:
        out = progress_bar(10, 10, width=8)
        assert "100%" in out

    def test_partial(self) -> None:
        out = progress_bar(5, 10, width=8)
        assert " 50%" in out

    def test_overflow_clamped(self) -> None:
        out = progress_bar(20, 5, width=8)
        assert "100%" in out

    def test_width_stable(self) -> None:
        out = progress_bar(0, 100, width=20)
        # Format is `[--------------------]   0%`: 1+20+1+6 = 28 chars.
        assert out == "[" + "-" * 20 + "]   0%"
        assert out.endswith("0%")


# ---------------------------------------------------------------------------
# render_trend
# ---------------------------------------------------------------------------


class TestRenderTrend:
    def test_empty(self) -> None:
        assert render_trend([], width=4) == "····"

    def test_zero_width(self) -> None:
        assert render_trend([1.0, 2.0], width=0) == ""

    def test_constant_flat(self) -> None:
        # Constant input produces a flat 'middle' line or all '·'.
        out = render_trend([3.14] * 4, width=4)
        # All "·" because hi == lo -> fallback path
        assert all(c == "·" for c in out)

    def test_widening(self) -> None:
        out = render_trend([0.1, 0.3, 0.5, 0.7, 0.9], width=5)
        # Right edge should be a top-tier character
        assert out[-1] in "▅▆▇█"

    def test_pad_when_input_shorter(self) -> None:
        out = render_trend([1.0], width=4)
        assert len(out) == 4


# ---------------------------------------------------------------------------
# TrafficWindow
# ---------------------------------------------------------------------------


class TestTrafficWindow:
    def test_empty_summary(self) -> None:
        w = TrafficWindow()
        snap = w.summary()
        assert snap["count"] == 0
        assert snap["rps"] == 0.0
        assert snap["error_rate"] == 0.0

    def test_record_event_increments_count(self) -> None:
        w = TrafficWindow()
        now = time.time()
        for _ in range(5):
            w.record(TrafficEvent(ts=now, lane="critical", agent="cursor", status="ok"))
        snap = w.summary()
        assert snap["count"] == 5
        assert snap["by_lane"]["critical"] == 5
        assert snap["by_status"]["ok"] == 5

    def test_eviction_works(self) -> None:
        w = TrafficWindow(window_s=1.0)
        now = time.time()
        w.record(TrafficEvent(ts=now - 5.0, lane="critical", status="ok"))
        # Recent event
        w.record(TrafficEvent(ts=now, lane="critical", status="ok"))
        snap = w.summary(now=now)
        assert snap["count"] == 1

    def test_error_rate(self) -> None:
        w = TrafficWindow()
        now = time.time()
        w.record(TrafficEvent(ts=now, lane="critical", status="ok"))
        w.record(TrafficEvent(ts=now, lane="critical", status="error"))
        w.record(TrafficEvent(ts=now, lane="critical", status="ok"))
        snap = w.summary()
        assert snap["error_rate"] == pytest.approx(1.0 / 3)

    def test_latency_percentiles(self) -> None:
        w = TrafficWindow()
        now = time.time()
        for d in [10.0, 20.0, 30.0, 40.0, 50.0]:
            w.record(TrafficEvent(ts=now, status="ok", duration_ms=d))
        snap = w.summary()
        assert snap["p50_ms"] == 30.0
        assert snap["p95_ms"] == 50.0 or snap["p95_ms"] == 40.0  # n=5 int(0.95*4)=3

    def test_override_count(self) -> None:
        w = TrafficWindow()
        now = time.time()
        w.record(TrafficEvent(ts=now, status="ok", override_active=True))
        w.record(TrafficEvent(ts=now, status="ok", override_active=False))
        snap = w.summary()
        assert snap["override_count"] == 1


# ---------------------------------------------------------------------------
# TrafficDashboard
# ---------------------------------------------------------------------------


class TestTrafficDashboard:
    def test_summary_includes_trend(self) -> None:
        d = TrafficDashboard(window_s=10.0, trend_width=8)
        now = time.time()
        for _ in range(3):
            d.record(TrafficEvent(ts=now, status="ok"))
        snap = d.summary()
        assert snap["count"] == 3
        assert "rps_trend" in snap
        assert len(snap["rps_trend"]) == 8

    def test_rps_trend_helper(self) -> None:
        d = TrafficDashboard(trend_width=4)
        d.record(TrafficEvent(ts=time.time()))
        assert len(d.rps_trend()) == 4

    def test_progress_bar(self) -> None:
        d = TrafficDashboard(window_s=10.0)
        now = time.time()
        for _ in range(5):
            d.record(TrafficEvent(ts=now, status="ok"))
        bar = d.progress_bar()
        assert bar.startswith("[")
        assert "%" in bar


# ---------------------------------------------------------------------------
# render_traffic
# ---------------------------------------------------------------------------


class TestRenderTraffic:
    def test_renders_full_breakdown(self) -> None:
        d = TrafficDashboard(window_s=10.0, trend_width=10)
        now = time.time()
        for _ in range(4):
            d.record(TrafficEvent(ts=now, lane="critical", agent="cursor", status="ok"))
        d.record(TrafficEvent(ts=now, lane="critical", status="error", duration_ms=320))
        text = render_traffic(d, title="TRAFFIC")
        assert "TRAFFIC" in text
        assert "rps:" in text
        assert "error_rate:" in text
        assert "p50_ms:" in text
        assert "p95_ms:" in text
        assert "by_lane:" in text
        assert "by_status:" in text
        assert "rps trend" in text

    def test_renders_empty(self) -> None:
        d = TrafficDashboard(window_s=10.0, trend_width=10)
        text = render_traffic(d)
        # Header should still render; lane/status may show '-'.
        assert "TRAFFIC" in text
        assert "-" in text  # placeholder chars for empty by_lane


# ---------------------------------------------------------------------------
# Performance smoke test (SLO P-090)
# ---------------------------------------------------------------------------


class TestPerformance:
    def test_summary_sub_50ms(self) -> None:
        """Smoke-test: 50 summaries over a 100-event window < 50ms each on avg.

        Loosely enforced because CI runners vary, but should comfortably fit
        inside the SLO P-090 budget on a single-threaded execution.
        """
        d = TrafficDashboard(window_s=10.0)
        now = time.time()
        for i in range(100):
            d.record(
                TrafficEvent(
                    ts=now,
                    lane="critical" if i % 3 else "standard",
                    status="ok" if i % 19 else "error",
                    duration_ms=100.0 + i,
                )
            )
        start = time.time()
        for _ in range(50):
            d.summary()
        elapsed = (time.time() - start) * 1000
        # <50ms per summary on average; this is SLO P-090 (cockpit render SLO)
        # for a single-threaded, single-process summary call.
        assert elapsed / 50 < 50
