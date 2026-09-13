"""Tests for Compositor render caching.

Covers:
- Cache hit returns same output without calling content_fn again   (FR-UI-COMP-010)
- Cache miss calls content_fn                                       (FR-UI-COMP-010)
- invalidate(panel_name) clears only that panel's cache            (FR-UI-COMP-011)
- invalidate(None) clears the entire cache                         (FR-UI-COMP-011)
- TTL expiry causes re-render (cache miss after expiry)            (FR-UI-COMP-012)
- cache_stats tracks hits, misses, and size correctly              (FR-UI-COMP-013)
- Error-state fallback is cached in the short-TTL error cache      (FR-UI-COMP-014)
- Error cache expires and re-invokes content_fn                    (FR-UI-COMP-014)
- add_panel replacement invalidates previous panel cache           (FR-UI-COMP-015)
- remove_panel invalidates cache for removed panel                 (FR-UI-COMP-015)
- render(), render_all(), render_panel() all use the cache         (FR-UI-COMP-010)
- recover_panel clears error state; next render re-invokes fn      (FR-UI-COMP-014)
- Compositor with multiple panels: each panel cached independently (FR-UI-COMP-010)
- Content change requires invalidation before re-render           (FR-UI-COMP-010)
- cache_stats size reflects live cache entries                     (FR-UI-COMP-013)
- invalidate on unknown panel_name is safe (no error)             (FR-UI-COMP-011)
- Compositor default TTL/maxsize constructors                      (FR-UI-COMP-010)
- CacheStats TypedDict shape                                       (FR-UI-COMP-013)
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from thegent.ui.compositor.compositor import Compositor, Panel

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _counter_panel(name: str = "p", initial: str = "v0") -> tuple[Panel, list[str]]:
    """Return a Panel whose content_fn records each call and returns the next value.

    The returned list is the shared call log; mutate ``log[0]`` to change the
    returned content.
    """
    log: list[str] = [initial]

    def content_fn() -> str:
        return log[0]

    panel = Panel(name=name, content_fn=content_fn)
    return panel, log


def _error_panel(name: str = "err") -> tuple[Panel, list[int]]:
    """Return a Panel whose content_fn always raises RuntimeError.

    The second element of the tuple is a call-count list for assertions.
    """
    count: list[int] = [0]

    def content_fn() -> str:
        count[0] += 1
        raise RuntimeError("always fails")

    panel = Panel(name=name, content_fn=content_fn)
    return panel, count


# ---------------------------------------------------------------------------
# FR-UI-COMP-010 — Cache hit / miss basics
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cache_hit_returns_same_output() -> None:
    """Second render of the same content returns identical output.

    # @trace FR-UI-COMP-010
    """
    comp = Compositor()
    panel, _ = _counter_panel()
    comp.add_panel(panel)

    first = comp.render_panel("p")
    second = comp.render_panel("p")

    assert first == second == "v0"


@pytest.mark.unit
def test_cache_hit_does_not_reinvoke_content_fn() -> None:
    """content_fn is called only once on repeated renders of same content.

    # @trace FR-UI-COMP-010
    """
    mock_fn = MagicMock(return_value="content")
    panel = Panel(name="m", content_fn=mock_fn)
    comp = Compositor()
    comp.add_panel(panel)

    comp.render_panel("m")
    comp.render_panel("m")
    comp.render_panel("m")

    assert mock_fn.call_count == 1
    stats = comp.cache_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 2


@pytest.mark.unit
def test_cache_miss_on_first_render() -> None:
    """First render for a panel is always a cache miss.

    # @trace FR-UI-COMP-010
    """
    comp = Compositor()
    panel, _ = _counter_panel()
    comp.add_panel(panel)

    comp.render_panel("p")

    stats = comp.cache_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0


@pytest.mark.unit
def test_render_list_uses_cache() -> None:
    """render() list path also hits the cache on repeated calls.

    # @trace FR-UI-COMP-010
    """
    comp = Compositor()
    comp.add_panel(Panel(name="a", content_fn=lambda: "AAA"))
    comp.add_panel(Panel(name="b", content_fn=lambda: "BBB"))

    comp.render()  # 2 misses
    comp.render()  # 2 hits

    stats = comp.cache_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 2


@pytest.mark.unit
def test_render_all_dict_uses_cache() -> None:
    """render_all() dict path also hits the cache on repeated calls.

    # @trace FR-UI-COMP-010
    """
    comp = Compositor()
    comp.add_panel(Panel(name="x", content_fn=lambda: "X"))

    comp.render_all()  # miss
    result = comp.render_all()  # hit

    assert result == {"x": "X"}
    assert comp.cache_stats()["hits"] == 1


@pytest.mark.unit
def test_content_change_requires_invalidation() -> None:
    """Changing content_fn output does not bypass a valid TTL cache.

    # @trace FR-UI-COMP-010
    """
    panel, log = _counter_panel()
    comp = Compositor()
    comp.add_panel(panel)

    comp.render_panel("p")  # miss → "v0"
    log[0] = "v1"
    result = comp.render_panel("p")  # valid cache still returns old content

    assert result == "v0"
    assert comp.cache_stats()["hits"] == 1

    comp.invalidate("p")
    assert comp.render_panel("p") == "v1"
    assert comp.cache_stats()["misses"] == 2


@pytest.mark.unit
def test_multiple_panels_cached_independently() -> None:
    """Each panel's cache is keyed independently; one hit does not bleed across panels.

    # @trace FR-UI-COMP-010
    """
    comp = Compositor()
    comp.add_panel(Panel(name="alpha", content_fn=lambda: "A"))
    comp.add_panel(Panel(name="beta", content_fn=lambda: "B"))

    # First render: 2 misses
    comp.render_all()
    # Second render: 2 hits
    comp.render_all()

    stats = comp.cache_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 2


# ---------------------------------------------------------------------------
# FR-UI-COMP-011 — Cache invalidation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_invalidate_single_panel_clears_only_that_panel() -> None:
    """invalidate(name) removes only the named panel's cache entry.

    # @trace FR-UI-COMP-011
    """
    comp = Compositor()
    panel_a, log_a = _counter_panel("a", "a_v0")
    panel_b, _ = _counter_panel("b", "b_v0")
    comp.add_panel(panel_a)
    comp.add_panel(panel_b)

    comp.render_all()  # 2 misses

    comp.invalidate("a")
    log_a[0] = "a_v1"

    result = comp.render_all()
    assert result["a"] == "a_v1"  # re-rendered
    assert result["b"] == "b_v0"  # still from cache

    stats = comp.cache_stats()
    # 2 original misses + 1 miss for re-render of a; 1 hit for b
    assert stats["misses"] == 3
    assert stats["hits"] == 1


@pytest.mark.unit
def test_invalidate_all_panels_clears_entire_cache() -> None:
    """invalidate(None) clears the entire render cache for all panels.

    # @trace FR-UI-COMP-011
    """
    comp = Compositor()
    comp.add_panel(Panel(name="p1", content_fn=lambda: "P1"))
    comp.add_panel(Panel(name="p2", content_fn=lambda: "P2"))

    comp.render_all()  # 2 misses
    comp.invalidate()  # clear all
    comp.render_all()  # 2 more misses

    assert comp.cache_stats()["misses"] == 4
    assert comp.cache_stats()["hits"] == 0


@pytest.mark.unit
def test_invalidate_unknown_panel_does_not_raise() -> None:
    """invalidate() with an unrecognised panel_name completes without error.

    # @trace FR-UI-COMP-011
    """
    comp = Compositor()
    # Should not raise even though the panel doesn't exist
    comp.invalidate("nonexistent")


@pytest.mark.unit
def test_add_panel_replacement_invalidates_cache() -> None:
    """Replacing a panel via add_panel automatically invalidates its cache.

    # @trace FR-UI-COMP-015
    """
    comp = Compositor()
    comp.add_panel(Panel(name="p", content_fn=lambda: "old"))
    comp.render_panel("p")  # populate cache

    comp.add_panel(Panel(name="p", content_fn=lambda: "new"))
    result = comp.render_panel("p")

    assert result == "new"


@pytest.mark.unit
def test_remove_panel_invalidates_cache() -> None:
    """remove_panel evicts the cache entry for the removed panel.

    # @trace FR-UI-COMP-015
    """
    comp = Compositor()
    comp.add_panel(Panel(name="p", content_fn=lambda: "content"))
    comp.render_panel("p")  # populate cache
    hits_before = comp.cache_stats()["hits"]

    comp.remove_panel("p")

    # Re-add to confirm it's a miss, not a hit
    comp.add_panel(Panel(name="p", content_fn=lambda: "content2"))
    comp.render_panel("p")

    assert comp.cache_stats()["hits"] == hits_before  # no additional hits


# ---------------------------------------------------------------------------
# FR-UI-COMP-012 — TTL expiry
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ttl_expiry_causes_re_render() -> None:
    """After TTL expires the panel is re-rendered (cache miss).

    The content_fn returns a stable value so that the first miss populates the
    cache.  We then sleep past the TTL and verify that the compositor reports a
    second miss (i.e. the cached entry was evicted).

    # @trace FR-UI-COMP-012
    """
    comp = Compositor(ttl=0.05)  # 50 ms TTL
    # Use a stable content so the first two renders see the same hash.
    comp.add_panel(Panel(name="t", content_fn=lambda: "stable"))

    comp.render_panel("t")  # miss
    comp.render_panel("t")  # hit
    assert comp.cache_stats()["hits"] == 1
    assert comp.cache_stats()["misses"] == 1

    time.sleep(0.12)  # wait for TTL expiry (2.4x the TTL for safety)

    comp.render_panel("t")  # TTL expired → miss again
    assert comp.cache_stats()["misses"] == 2


@pytest.mark.unit
def test_error_ttl_expiry_retries_content_fn() -> None:
    """After error_ttl expires the broken content_fn is retried.

    # @trace FR-UI-COMP-012
    """
    comp = Compositor(error_ttl=0.05)
    calls: list[int] = [0]

    def content_fn() -> str:
        calls[0] += 1
        raise ValueError("broken")

    comp.add_panel(Panel(name="e", content_fn=content_fn))

    comp.render_panel("e")  # miss → calls content_fn, caches error fallback
    comp.render_panel("e")  # hit → error cache, no extra call

    time.sleep(0.1)

    comp.render_panel("e")  # error TTL expired → misses again, calls content_fn

    # content_fn should have been invoked at least twice (first miss + after expiry)
    assert calls[0] >= 2


# ---------------------------------------------------------------------------
# FR-UI-COMP-013 — cache_stats monitoring
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cache_stats_initial_state() -> None:
    """Freshly created Compositor has zero hits, misses, and size.

    # @trace FR-UI-COMP-013
    """
    comp = Compositor()
    stats = comp.cache_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["size"] == 0


@pytest.mark.unit
def test_cache_stats_increments_correctly() -> None:
    """cache_stats accurately tracks hits and misses across multiple renders.

    # @trace FR-UI-COMP-013
    """
    comp = Compositor()
    comp.add_panel(Panel(name="s", content_fn=lambda: "stable"))

    comp.render_panel("s")  # miss 1
    comp.render_panel("s")  # hit 1
    comp.render_panel("s")  # hit 2

    stats = comp.cache_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 1


@pytest.mark.unit
def test_cache_stats_size_reflects_cache_entries() -> None:
    """cache_stats['size'] equals the number of live cache entries.

    # @trace FR-UI-COMP-013
    """
    comp = Compositor()
    comp.add_panel(Panel(name="a", content_fn=lambda: "A"))
    comp.add_panel(Panel(name="b", content_fn=lambda: "B"))

    assert comp.cache_stats()["size"] == 0

    comp.render_panel("a")
    assert comp.cache_stats()["size"] == 1

    comp.render_panel("b")
    assert comp.cache_stats()["size"] == 2


@pytest.mark.unit
def test_cache_stats_size_decreases_after_invalidate() -> None:
    """Size drops after invalidation.

    # @trace FR-UI-COMP-013
    """
    comp = Compositor()
    comp.add_panel(Panel(name="q", content_fn=lambda: "Q"))
    comp.render_panel("q")
    assert comp.cache_stats()["size"] == 1

    comp.invalidate("q")
    assert comp.cache_stats()["size"] == 0


@pytest.mark.unit
def test_cache_stats_typed_dict_shape() -> None:
    """cache_stats() returns a TypedDict with the expected keys.

    # @trace FR-UI-COMP-013
    """
    comp = Compositor()
    stats = comp.cache_stats()
    assert set(stats.keys()) == {"hits", "misses", "size"}
    assert isinstance(stats["hits"], int)
    assert isinstance(stats["misses"], int)
    assert isinstance(stats["size"], int)


# ---------------------------------------------------------------------------
# FR-UI-COMP-014 — Error-state caching
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_error_state_is_cached_with_short_ttl() -> None:
    """content_fn raising is cached; repeated renders return the cached fallback.

    The first miss calls content_fn through Panel.render() and caches the
    fallback. The second render serves that fallback from the error cache.

    # @trace FR-UI-COMP-014
    """
    comp = Compositor()
    panel, count = _error_panel()
    comp.add_panel(panel)

    r1 = comp.render_panel("err")

    r2 = comp.render_panel("err")

    assert r1 == r2  # same cached fallback on both renders
    assert comp.cache_stats()["hits"] == 1
    assert count[0] == 1


@pytest.mark.unit
def test_error_cache_does_not_use_main_cache() -> None:
    """Error fallbacks go to the error_cache, not the main TTL cache.

    # @trace FR-UI-COMP-014
    """
    comp = Compositor()
    panel, _ = _error_panel()
    comp.add_panel(panel)

    comp.render_panel("err")  # miss → stored in error_cache

    # Main cache should be empty; error_cache should have 1 entry
    assert len(comp._cache) == 0
    assert len(comp._error_cache) == 1


@pytest.mark.unit
def test_error_cache_obeys_maxsize() -> None:
    """Error fallbacks are included in cache size eviction.

    # @trace FR-UI-COMP-014
    """
    comp = Compositor(maxsize=1)
    panel_a, _ = _error_panel("a")
    panel_b, _ = _error_panel("b")
    comp.add_panel(panel_a)
    comp.add_panel(panel_b)

    comp.render_panel("a")
    comp.render_panel("b")

    assert len(comp._cache) + len(comp._error_cache) == 1


@pytest.mark.unit
def test_recover_panel_then_render_gets_fresh_result() -> None:
    """After recover_panel() + invalidate, the next render calls content_fn again.

    After recover + invalidate the function starts succeeding and the
    compositor returns the happy result.

    # @trace FR-UI-COMP-014
    """
    calls: list[int] = [0]
    fail_limit: int = 2

    def content_fn() -> str:
        calls[0] += 1
        if calls[0] < fail_limit:
            raise RuntimeError("not ready")
        return "ok"

    panel = Panel(name="r", content_fn=content_fn)
    comp = Compositor()
    comp.add_panel(panel)

    comp.render_panel("r")
    assert panel.has_error

    comp.recover_panel("r")
    comp.invalidate("r")

    r2 = comp.render_panel("r")
    assert r2 == "ok"
    assert not panel.has_error


# ---------------------------------------------------------------------------
# FR-UI-COMP-010 (additional) — Compositor constructor options
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_compositor_custom_ttl_accepted() -> None:
    """Compositor accepts a custom TTL without error.

    # @trace FR-UI-COMP-010
    """
    comp = Compositor(ttl=120.0)
    comp.add_panel(Panel(name="c", content_fn=lambda: "C"))
    assert comp.render_panel("c") == "C"


@pytest.mark.unit
def test_compositor_custom_maxsize_accepted() -> None:
    """Compositor accepts a custom maxsize without error.

    # @trace FR-UI-COMP-010
    """
    comp = Compositor(maxsize=10)
    for i in range(10):
        comp.add_panel(Panel(name=f"p{i}", content_fn=lambda i=i: f"v{i}"))
    results = comp.render()
    assert len(results) == 10
