"""Tests for CompositorProfiler and RenderProfile.

Covers:
- RenderProfile dataclass fields and defaults                   (FR-UI-COMP-020)
- CompositorProfiler.record stores a profile                    (FR-UI-COMP-021)
- CompositorProfiler.record respects maxlen (100)               (FR-UI-COMP-021)
- CompositorProfiler.get_slowest ordering                       (FR-UI-COMP-022)
- CompositorProfiler.get_slowest with n > record count          (FR-UI-COMP-022)
- CompositorProfiler.get_slowest with empty profiler            (FR-UI-COMP-022)
- CompositorProfiler.get_average all panels                     (FR-UI-COMP-023)
- CompositorProfiler.get_average panel-specific filtering       (FR-UI-COMP-023)
- CompositorProfiler.get_average with unknown panel_id          (FR-UI-COMP-023)
- CompositorProfiler.get_average with empty profiler            (FR-UI-COMP-023)
- CompositorProfiler.report empty                               (FR-UI-COMP-024)
- CompositorProfiler.report with records                        (FR-UI-COMP-024)
- CompositorProfiler.report contains panel ids and timings      (FR-UI-COMP-024)
- CompositorProfiler.clear empties all records                  (FR-UI-COMP-025)
- CompositorProfiler.record_count property                      (FR-UI-COMP-021)
- Compositor has profiler attribute                             (FR-UI-COMP-026)
- render() records one profile per panel                        (FR-UI-COMP-026)
- render_all() records one profile per panel                    (FR-UI-COMP-026)
- render_panel() records a profile                              (FR-UI-COMP-026)
- Cache hit flagged correctly in profile                        (FR-UI-COMP-027)
- Cache miss flagged correctly in profile                       (FR-UI-COMP-027)
- render_time_ms is non-negative                                (FR-UI-COMP-028)
- Error-path render records a profile                           (FR-UI-COMP-027)
- Panel-specific average after mixed renders                    (FR-UI-COMP-023)
- Export from thegent.ui                                        (FR-UI-COMP-020)
"""

from __future__ import annotations

import time

import pytest

from thegent.ui import CompositorProfiler as UICompositorProfiler
from thegent.ui import RenderProfile as UIRenderProfile
from thegent.ui.compositor.compositor import (
    Compositor,
    CompositorProfiler,
    Panel,
    RenderProfile,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(
    panel_id: str = "panel",
    render_time_ms: float = 10.0,
    timestamp: float | None = None,
    cache_hit: bool = False,
) -> RenderProfile:
    """Convenience factory for RenderProfile instances."""
    return RenderProfile(
        panel_id=panel_id,
        render_time_ms=render_time_ms,
        timestamp=timestamp if timestamp is not None else time.time(),
        cache_hit=cache_hit,
    )


def _simple_panel(name: str = "p", content: str = "content") -> Panel:
    """Return a Panel whose content_fn always returns *content*."""
    return Panel(name=name, content_fn=lambda: content)


def _always_raises(name: str = "err") -> Panel:
    """Return a Panel whose content_fn always raises RuntimeError."""

    def broken() -> str:
        raise RuntimeError("always fails")

    return Panel(name=name, content_fn=broken)


# ---------------------------------------------------------------------------
# FR-UI-COMP-020 — RenderProfile dataclass
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_render_profile_fields_stored_correctly() -> None:
    """RenderProfile stores all fields as provided.

    # @trace FR-UI-COMP-020
    """
    ts = time.time()
    profile = RenderProfile(panel_id="foo", render_time_ms=42.5, timestamp=ts, cache_hit=True)
    assert profile.panel_id == "foo"
    assert profile.render_time_ms == 42.5
    assert profile.timestamp == ts
    assert profile.cache_hit is True


@pytest.mark.unit
def test_render_profile_cache_hit_defaults_to_false() -> None:
    """RenderProfile.cache_hit defaults to False when not supplied.

    # @trace FR-UI-COMP-020
    """
    profile = RenderProfile(panel_id="x", render_time_ms=1.0, timestamp=time.time())
    assert profile.cache_hit is False


@pytest.mark.unit
def test_render_profile_exported_from_ui() -> None:
    """CompositorProfiler and RenderProfile are importable from thegent.ui.

    # @trace FR-UI-COMP-020
    """
    assert UICompositorProfiler is CompositorProfiler
    assert UIRenderProfile is RenderProfile


# ---------------------------------------------------------------------------
# FR-UI-COMP-021 — record / record_count / maxlen
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_profiler_record_stores_profile() -> None:
    """record() appends a profile and record_count increments.

    # @trace FR-UI-COMP-021
    """
    profiler = CompositorProfiler()
    assert profiler.record_count == 0

    profiler.record(_make_profile("a", 5.0))
    assert profiler.record_count == 1


@pytest.mark.unit
def test_profiler_record_multiple_profiles() -> None:
    """record() can store multiple profiles in sequence.

    # @trace FR-UI-COMP-021
    """
    profiler = CompositorProfiler()
    for i in range(10):
        profiler.record(_make_profile(f"panel-{i}", float(i)))
    assert profiler.record_count == 10


@pytest.mark.unit
def test_profiler_maxlen_evicts_oldest() -> None:
    """When 100 records are present, adding one more evicts the oldest.

    # @trace FR-UI-COMP-021
    """
    profiler = CompositorProfiler()
    for i in range(100):
        profiler.record(_make_profile(f"p{i}", float(i)))

    assert profiler.record_count == 100

    # Add one more — deque with maxlen=100 drops the oldest
    profiler.record(_make_profile("p100", 999.0))
    assert profiler.record_count == 100

    # The newest record should be present in get_slowest
    newest = profiler.get_slowest(1)[0]
    assert newest.render_time_ms == 999.0


# ---------------------------------------------------------------------------
# FR-UI-COMP-022 — get_slowest
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_slowest_returns_descending_order() -> None:
    """get_slowest returns profiles sorted slowest-first.

    # @trace FR-UI-COMP-022
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("a", 10.0))
    profiler.record(_make_profile("b", 50.0))
    profiler.record(_make_profile("c", 25.0))

    slowest = profiler.get_slowest(3)
    times = [p.render_time_ms for p in slowest]
    assert times == sorted(times, reverse=True)
    assert times[0] == 50.0


@pytest.mark.unit
def test_get_slowest_respects_n() -> None:
    """get_slowest(n) returns at most n results.

    # @trace FR-UI-COMP-022
    """
    profiler = CompositorProfiler()
    for i in range(10):
        profiler.record(_make_profile(f"p{i}", float(i * 10)))

    result = profiler.get_slowest(3)
    assert len(result) == 3


@pytest.mark.unit
def test_get_slowest_returns_all_when_n_exceeds_count() -> None:
    """get_slowest(n) with n > record count returns all records.

    # @trace FR-UI-COMP-022
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("a", 1.0))
    profiler.record(_make_profile("b", 2.0))

    result = profiler.get_slowest(100)
    assert len(result) == 2


@pytest.mark.unit
def test_get_slowest_empty_profiler_returns_empty_list() -> None:
    """get_slowest on an empty profiler returns an empty list.

    # @trace FR-UI-COMP-022
    """
    profiler = CompositorProfiler()
    assert profiler.get_slowest() == []


@pytest.mark.unit
def test_get_slowest_default_n_is_5() -> None:
    """get_slowest() with no argument returns at most 5 records.

    # @trace FR-UI-COMP-022
    """
    profiler = CompositorProfiler()
    for i in range(8):
        profiler.record(_make_profile(f"p{i}", float(i)))

    result = profiler.get_slowest()
    assert len(result) == 5


# ---------------------------------------------------------------------------
# FR-UI-COMP-023 — get_average
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_average_all_panels() -> None:
    """get_average() with no filter returns mean over all records.

    # @trace FR-UI-COMP-023
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("a", 10.0))
    profiler.record(_make_profile("b", 20.0))
    profiler.record(_make_profile("a", 30.0))

    avg = profiler.get_average()
    assert avg == pytest.approx(20.0)


@pytest.mark.unit
def test_get_average_panel_specific() -> None:
    """get_average(panel_id) filters to records for that panel only.

    # @trace FR-UI-COMP-023
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("panel-x", 10.0))
    profiler.record(_make_profile("panel-x", 30.0))
    profiler.record(_make_profile("panel-y", 100.0))

    avg_x = profiler.get_average("panel-x")
    assert avg_x == pytest.approx(20.0)

    avg_y = profiler.get_average("panel-y")
    assert avg_y == pytest.approx(100.0)


@pytest.mark.unit
def test_get_average_unknown_panel_returns_zero() -> None:
    """get_average for a panel with no records returns 0.0.

    # @trace FR-UI-COMP-023
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("other", 50.0))
    assert profiler.get_average("nonexistent") == 0.0


@pytest.mark.unit
def test_get_average_empty_profiler_returns_zero() -> None:
    """get_average on a completely empty profiler returns 0.0.

    # @trace FR-UI-COMP-023
    """
    profiler = CompositorProfiler()
    assert profiler.get_average() == 0.0
    assert profiler.get_average("anything") == 0.0


# ---------------------------------------------------------------------------
# FR-UI-COMP-024 — report
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_report_empty_returns_no_records_message() -> None:
    """report() on empty profiler returns a clear no-records message.

    # @trace FR-UI-COMP-024
    """
    profiler = CompositorProfiler()
    report = profiler.report()
    assert "no render records" in report.lower()


@pytest.mark.unit
def test_report_contains_record_count() -> None:
    """report() mentions total number of records collected.

    # @trace FR-UI-COMP-024
    """
    profiler = CompositorProfiler()
    for i in range(7):
        profiler.record(_make_profile(f"p{i}", float(i)))

    report = profiler.report()
    assert "7" in report


@pytest.mark.unit
def test_report_contains_panel_ids() -> None:
    """report() lists panel ids in the top-slowest section.

    # @trace FR-UI-COMP-024
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("my-panel", 99.9))

    report = profiler.report()
    assert "my-panel" in report


@pytest.mark.unit
def test_report_contains_render_times() -> None:
    """report() includes render times for the slowest renders.

    # @trace FR-UI-COMP-024
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("p", 123.45))

    report = profiler.report()
    assert "123.45" in report


@pytest.mark.unit
def test_report_contains_cache_hit_label() -> None:
    """report() distinguishes cache hits from misses.

    # @trace FR-UI-COMP-024
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("hit-panel", 5.0, cache_hit=True))
    profiler.record(_make_profile("miss-panel", 50.0, cache_hit=False))

    report = profiler.report()
    assert "HIT" in report
    assert "MISS" in report


# ---------------------------------------------------------------------------
# FR-UI-COMP-025 — clear
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_clear_removes_all_records() -> None:
    """clear() empties the profiler so record_count returns 0.

    # @trace FR-UI-COMP-025
    """
    profiler = CompositorProfiler()
    for i in range(5):
        profiler.record(_make_profile(f"p{i}", float(i)))

    profiler.clear()
    assert profiler.record_count == 0
    assert profiler.get_slowest() == []
    assert profiler.get_average() == 0.0


@pytest.mark.unit
def test_clear_then_record_works() -> None:
    """After clear() new records can be added normally.

    # @trace FR-UI-COMP-025
    """
    profiler = CompositorProfiler()
    profiler.record(_make_profile("before", 10.0))
    profiler.clear()

    profiler.record(_make_profile("after", 99.0))
    assert profiler.record_count == 1
    assert profiler.get_slowest(1)[0].panel_id == "after"


# ---------------------------------------------------------------------------
# FR-UI-COMP-026 — Compositor integration
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_compositor_has_profiler_attribute() -> None:
    """Compositor instances expose a CompositorProfiler via .profiler.

    # @trace FR-UI-COMP-026
    """
    comp = Compositor()
    assert isinstance(comp.profiler, CompositorProfiler)


@pytest.mark.unit
def test_render_panel_records_one_profile() -> None:
    """render_panel() records exactly one profile per call.

    # @trace FR-UI-COMP-026
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("p"))

    comp.render_panel("p")
    assert comp.profiler.record_count == 1

    comp.render_panel("p")
    assert comp.profiler.record_count == 2


@pytest.mark.unit
def test_render_records_one_profile_per_panel() -> None:
    """render() records one profile per panel in the compositor.

    # @trace FR-UI-COMP-026
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("a", "A"))
    comp.add_panel(_simple_panel("b", "B"))
    comp.add_panel(_simple_panel("c", "C"))

    comp.render()
    assert comp.profiler.record_count == 3


@pytest.mark.unit
def test_render_all_records_one_profile_per_panel() -> None:
    """render_all() records one profile per panel.

    # @trace FR-UI-COMP-026
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("x", "X"))
    comp.add_panel(_simple_panel("y", "Y"))

    comp.render_all()
    assert comp.profiler.record_count == 2


@pytest.mark.unit
def test_profiler_panel_id_matches_panel_name() -> None:
    """Recorded profile.panel_id equals the panel name.

    # @trace FR-UI-COMP-026
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("my-special-panel"))

    comp.render_panel("my-special-panel")
    profile = comp.profiler.get_slowest(1)[0]
    assert profile.panel_id == "my-special-panel"


# ---------------------------------------------------------------------------
# FR-UI-COMP-027 — cache_hit flag accuracy
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_first_render_is_cache_miss() -> None:
    """The first render of a panel is always a cache miss.

    # @trace FR-UI-COMP-027
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("p"))

    comp.render_panel("p")
    profile = comp.profiler.get_slowest(1)[0]
    assert profile.cache_hit is False


@pytest.mark.unit
def test_second_render_same_content_is_cache_hit() -> None:
    """Rendering a panel a second time (same content) is a cache hit.

    # @trace FR-UI-COMP-027
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("p"))

    comp.render_panel("p")  # miss
    comp.render_panel("p")  # hit

    profiles = comp.profiler.get_slowest(5)
    hit_profiles = [pr for pr in profiles if pr.cache_hit]
    miss_profiles = [pr for pr in profiles if not pr.cache_hit]
    assert len(hit_profiles) == 1
    assert len(miss_profiles) == 1


@pytest.mark.unit
def test_error_panel_render_records_profile() -> None:
    """A panel whose content_fn always raises still records a profile.

    # @trace FR-UI-COMP-027
    """
    comp = Compositor()
    comp.add_panel(_always_raises("broken"))

    comp.render_panel("broken")
    assert comp.profiler.record_count == 1
    profile = comp.profiler.get_slowest(1)[0]
    assert profile.panel_id == "broken"


@pytest.mark.unit
def test_error_cache_hit_records_cache_hit_true() -> None:
    """Repeated error-panel renders served from error_cache are flagged as hits.

    # @trace FR-UI-COMP-027
    """
    call_count: list[int] = [0]

    def broken() -> str:
        call_count[0] += 1
        raise RuntimeError("always fails")

    comp = Compositor()
    comp.add_panel(Panel(name="err", content_fn=broken))

    comp.render_panel("err")  # miss: fills error cache
    comp.render_panel("err")  # hit: served from error cache

    hit_profiles = [pr for pr in comp.profiler.get_slowest(5) if pr.cache_hit]
    assert len(hit_profiles) >= 1


# ---------------------------------------------------------------------------
# FR-UI-COMP-028 — render_time_ms is non-negative
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_render_time_ms_is_non_negative_on_hit() -> None:
    """render_time_ms is >= 0 for cache-hit renders.

    # @trace FR-UI-COMP-028
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("fast"))

    comp.render_panel("fast")  # miss
    comp.render_panel("fast")  # hit

    for profile in comp.profiler.get_slowest(5):
        assert profile.render_time_ms >= 0.0


@pytest.mark.unit
def test_render_time_ms_is_non_negative_on_miss() -> None:
    """render_time_ms is >= 0 for cache-miss renders.

    # @trace FR-UI-COMP-028
    """
    comp = Compositor()
    content_log: list[str] = ["v0"]
    comp.add_panel(Panel(name="p", content_fn=lambda: content_log[0]))

    comp.render_panel("p")
    content_log[0] = "v1"
    comp.render_panel("p")  # different content -> cache miss

    for profile in comp.profiler.get_slowest(5):
        assert profile.render_time_ms >= 0.0


@pytest.mark.unit
def test_panel_specific_average_after_mixed_renders() -> None:
    """get_average(panel_id) is accurate after rendering multiple panels.

    # @trace FR-UI-COMP-023
    """
    comp = Compositor()
    comp.add_panel(_simple_panel("alpha"))
    comp.add_panel(_simple_panel("beta"))

    for _ in range(3):
        comp.render_panel("alpha")
    for _ in range(5):
        comp.render_panel("beta")

    avg_alpha = comp.profiler.get_average("alpha")
    avg_beta = comp.profiler.get_average("beta")

    assert avg_alpha >= 0.0
    assert avg_beta >= 0.0
    assert comp.profiler.record_count == 8
