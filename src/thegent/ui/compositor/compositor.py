"""Core compositor, panel, and profiling primitives."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter, time
from typing import TypedDict


class CacheStats(TypedDict):
    hits: int
    misses: int
    size: int


@dataclass(slots=True)
class RenderProfile:
    panel_id: str
    render_time_ms: float
    timestamp: float
    cache_hit: bool = False


class CompositorProfiler:
    def __init__(self) -> None:
        self._records: deque[RenderProfile] = deque(maxlen=100)

    @property
    def record_count(self) -> int:
        return len(self._records)

    def record(self, profile: RenderProfile) -> None:
        self._records.append(profile)

    def get_slowest(self, n: int = 5) -> list[RenderProfile]:
        return sorted(self._records, key=lambda profile: profile.render_time_ms, reverse=True)[:n]

    def get_average(self, panel_id: str | None = None) -> float:
        records = [r for r in self._records if panel_id is None or r.panel_id == panel_id]
        if not records:
            return 0.0
        return sum(r.render_time_ms for r in records) / len(records)

    def report(self) -> str:
        if not self._records:
            return "No render records available."
        lines = [f"{self.record_count} render records"]
        for profile in self.get_slowest():
            state = "HIT" if profile.cache_hit else "MISS"
            lines.append(f"{profile.panel_id}: {profile.render_time_ms:.2f} ms [{state}]")
        return "\n".join(lines)

    def clear(self) -> None:
        self._records.clear()


@dataclass
class Panel:
    name: str
    content_fn: Callable[[], str]
    error_fallback: str | Callable[[Exception], str] | None = None
    last_error: Exception | None = None

    @property
    def has_error(self) -> bool:
        return self.last_error is not None

    def recover(self) -> None:
        self.last_error = None

    def render(self) -> str:
        try:
            content = self.content_fn()
        except Exception as exc:
            self.last_error = exc
            return self._fallback(exc)
        self.last_error = None
        return content

    def _fallback(self, exc: Exception) -> str:
        if isinstance(self.error_fallback, str):
            return self.error_fallback
        if callable(self.error_fallback):
            try:
                return self.error_fallback(exc)
            except Exception:
                return f"[Panel error: {self.name} — {type(exc).__name__}; fallback also failed]"
        return f"[Panel error: {self.name} — {type(exc).__name__}]"


class Compositor:
    def __init__(self, ttl: float = 60.0, error_ttl: float = 5.0, maxsize: int = 128) -> None:
        self.ttl = ttl
        self.error_ttl = error_ttl
        self.maxsize = maxsize
        self._panels: dict[str, Panel] = {}
        self._cache: dict[str, tuple[str, float]] = {}
        self._error_cache: dict[str, tuple[str, float]] = {}
        self._hits = 0
        self._misses = 0
        self.profiler = CompositorProfiler()

    def __contains__(self, name: str) -> bool:
        return name in self._panels

    def add_panel(self, panel: Panel) -> None:
        self._panels[panel.name] = panel
        self.invalidate(panel.name)

    def remove_panel(self, name: str) -> None:
        self._panels.pop(name, None)
        self.invalidate(name)

    def get_panel(self, name: str) -> Panel | None:
        return self._panels.get(name)

    def invalidate(self, panel_name: str | None = None) -> None:
        if panel_name is None:
            self._cache.clear()
            self._error_cache.clear()
            return
        self._cache.pop(panel_name, None)
        self._error_cache.pop(panel_name, None)

    def recover_panel(self, name: str) -> bool:
        panel = self._panels.get(name)
        if panel is None:
            return False
        panel.recover()
        self.invalidate(name)
        return True

    def recover_all(self) -> None:
        for panel in self._panels.values():
            panel.recover()
        self.invalidate()

    def errored_panels(self) -> list[str]:
        return [name for name, panel in self._panels.items() if panel.has_error]

    def cache_stats(self) -> CacheStats:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}

    def render_panel(self, name: str) -> str | None:
        panel = self._panels.get(name)
        if panel is None:
            return None
        now = time()
        error_cached = self._error_cache.get(name)
        if panel.has_error and error_cached and now - error_cached[1] <= self.error_ttl:
            return self._record_cache_hit(name, error_cached[0], now)
        cached = self._cache.get(name)
        if cached and now - cached[1] <= self.ttl:
            return self._record_cache_hit(name, cached[0], now)

        start = perf_counter()
        rendered = panel.render()
        rendered_at = time()
        duration = max((perf_counter() - start) * 1000.0, 0.0)
        self._store_rendered_panel(name, panel, rendered, rendered_at)
        self._misses += 1
        self.profiler.record(RenderProfile(name, duration, rendered_at, cache_hit=False))
        return rendered

    def _record_cache_hit(self, name: str, rendered: str, now: float) -> str:
        self._hits += 1
        self.profiler.record(RenderProfile(name, 0.0, now, cache_hit=True))
        return rendered

    def _store_rendered_panel(
        self,
        name: str,
        panel: Panel,
        rendered: str,
        now: float,
    ) -> None:
        if panel.has_error:
            self._error_cache[name] = (rendered, now)
            self._evict_if_needed()
            return
        self._cache[name] = (rendered, now)
        self._evict_if_needed()

    def render_all(self) -> dict[str, str | None]:
        return {name: self.render_panel(name) for name in self._panels}

    def render(self) -> list[str | None]:
        return [self.render_panel(name) for name in self._panels]

    def _evict_if_needed(self) -> None:
        while len(self._cache) + len(self._error_cache) > self.maxsize:
            key = next(iter(self._cache or self._error_cache))
            if key in self._cache:
                self._cache.pop(key, None)
            else:
                self._error_cache.pop(key, None)


__all__ = ["CacheStats", "Compositor", "CompositorProfiler", "Panel", "RenderProfile"]
