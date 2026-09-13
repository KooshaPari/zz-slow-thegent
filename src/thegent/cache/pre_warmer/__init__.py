"""Cache pre-warmer module.

Predictive cache pre-warming (FR-CACHE-003): registers a set of warming
strategies that can be invoked manually via :meth:`CachePreWarmer.warm_all`
or scheduled to run in the background via
:meth:`CachePreWarmer.start_background`.

Thread safety: a single re-entrant lock guards the strategies dict, the
warm counters, the last-run timestamps, and the background-running flag,
so concurrent register / warm / stats calls are safe.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Type aliases ----------------------------------------------------------------

PredictFn = Callable[[], list[str]]
LoadFn = Callable[[str], Any]


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# WarmingStrategy
# ---------------------------------------------------------------------------

_VALID_STRATEGY_NAME_MSG = "name must not be empty"
_VALID_STRATEGY_SCHEDULE_MSG = "schedule_seconds must be positive"


@dataclass(frozen=True)
class WarmingStrategy:
    """A single cache pre-warming strategy.

    Parameters
    ----------
    name:
        Human-readable strategy name; must be non-empty.
    predict_fn:
        Callable returning the list of cache keys to warm on each run.
    load_fn:
        Callable taking a single cache key and returning the value to
        store. Returning ``None`` is treated as a "do not cache" signal.
    schedule_seconds:
        Minimum interval between background runs for this strategy; must
        be strictly positive. Default 300 seconds.
    """

    name: str
    predict_fn: PredictFn
    load_fn: LoadFn
    schedule_seconds: float = 300.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(_VALID_STRATEGY_NAME_MSG)
        if self.schedule_seconds <= 0:
            raise ValueError(_VALID_STRATEGY_SCHEDULE_MSG)


@dataclass
class _StrategyState:
    """Mutable per-strategy runtime state (counters + last-run timestamp)."""

    strategy: WarmingStrategy
    warm_count: int = 0
    error_count: int = 0
    last_run: datetime | None = None


def _should_run(state: _StrategyState, now: datetime) -> bool:
    """Return True when *state* is due for a run relative to *now*."""
    if state.last_run is None:
        return True
    elapsed = (now - state.last_run).total_seconds()
    return elapsed >= state.strategy.schedule_seconds


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------

_DEFAULT_MODEL_KEYS: tuple[str, ...] = ("models:list", "models:available")
_DEFAULT_SESSION_KEYS: tuple[str, ...] = ("sessions:active", "sessions:recent")


def model_list_strategy(
    load_fn: LoadFn,
    model_keys: list[str] | None = None,
    schedule_seconds: float = 300.0,
) -> WarmingStrategy:
    """Return a WarmingStrategy that pre-warms the model-list cache keys."""
    keys = tuple(model_keys) if model_keys is not None else _DEFAULT_MODEL_KEYS
    return WarmingStrategy(
        name="model_list",
        predict_fn=lambda: list(keys),
        load_fn=load_fn,
        schedule_seconds=schedule_seconds,
    )


def session_list_strategy(
    load_fn: LoadFn,
    session_keys: list[str] | None = None,
    schedule_seconds: float = 300.0,
) -> WarmingStrategy:
    """Return a WarmingStrategy that pre-warms the session-list cache keys."""
    keys = tuple(session_keys) if session_keys is not None else _DEFAULT_SESSION_KEYS
    return WarmingStrategy(
        name="session_list",
        predict_fn=lambda: list(keys),
        load_fn=load_fn,
        schedule_seconds=schedule_seconds,
    )


# ---------------------------------------------------------------------------
# CachePreWarmer
# ---------------------------------------------------------------------------

_BACKGROUND_TICK_SECONDS = 0.05


class CachePreWarmer:
    """Cache pre-warming utility.

    Maintains a thread-safe registry of :class:`WarmingStrategy` objects
    that can be invoked manually via :meth:`warm_all` or scheduled via
    the background daemon thread started by :meth:`start_background`.
    """

    def __init__(self, cache: Any) -> None:
        self._cache = cache
        self._lock = threading.RLock()
        self._states: dict[str, _StrategyState] = {}
        self._warm_count: int = 0
        self._last_run: datetime | None = None
        self._bg_thread: threading.Thread | None = None
        self._bg_stop: threading.Event = threading.Event()

    # -- strategy registry -------------------------------------------------

    def register_strategy(self, strategy: WarmingStrategy) -> None:
        """Register (or replace) *strategy* in the warmer's registry."""
        with self._lock:
            self._states[strategy.name] = _StrategyState(strategy=strategy)

    def unregister_strategy(self, name: str) -> bool:
        """Remove the strategy named *name*; return True if it existed."""
        with self._lock:
            return self._states.pop(name, None) is not None

    # -- single-key warming ------------------------------------------------

    def warm_key(self, key: str, load_fn: LoadFn) -> bool:
        """Fetch *key* via *load_fn* and store it in the cache.

        Returns ``True`` when the value was successfully stored, ``False``
        when the loader returned ``None`` or raised.
        """
        try:
            value = load_fn()
        except Exception:  # noqa: BLE001 — load_fn failures are per-key, not fatal
            logger.debug("warm_key(%r) load raised", key, exc_info=True)
            return False
        if value is None:
            return False
        with self._lock:
            self._cache.set(key, value)
            self._warm_count += 1
        return True

    # -- bulk warming ------------------------------------------------------

    def warm_all(self) -> dict[str, bool]:
        """Run every registered strategy once; return per-key success map."""
        results: dict[str, bool] = {}
        now = _utcnow()
        with self._lock:
            states = list(self._states.values())
            for state in states:
                try:
                    keys = state.strategy.predict_fn()
                except Exception:  # noqa: BLE001 — predict failure skips strategy
                    logger.debug(
                        "predict_fn for %r raised; skipping",
                        state.strategy.name,
                        exc_info=True,
                    )
                    state.last_run = now
                    continue
                if not keys:
                    state.last_run = now
                    continue
                for key in keys:
                    try:
                        value = state.strategy.load_fn(key)
                    except Exception:  # noqa: BLE001
                        state.error_count += 1
                        results[key] = False
                        continue
                    if value is None:
                        results[key] = False
                        continue
                    self._cache.set(key, value)
                    state.warm_count += 1
                    self._warm_count += 1
                    results[key] = True
                state.last_run = now
            self._last_run = now
        return results

    # -- stats -------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Return a snapshot of the warmer's current state."""
        with self._lock:
            strategy_stats = [
                {
                    "name": state.strategy.name,
                    "warm_count": state.warm_count,
                    "error_count": state.error_count,
                    "last_run": state.last_run,
                }
                for state in self._states.values()
            ]
            return {
                "strategies": len(self._states),
                "warm_count": self._warm_count,
                "last_run": self._last_run,
                "background_running": self._bg_thread is not None and self._bg_thread.is_alive(),
                "strategy_stats": strategy_stats,
            }

    # -- background daemon -------------------------------------------------

    def start_background(self) -> None:
        """Start the background warming thread (idempotent)."""
        with self._lock:
            if self._bg_thread is not None and self._bg_thread.is_alive():
                return
            self._bg_stop.clear()
            self._bg_thread = threading.Thread(
                target=self._run_background,
                name="CachePreWarmer-bg",
                daemon=True,
            )
            self._bg_thread.start()

    def stop_background(self, timeout: float = 5.0) -> bool:
        """Signal the background thread to stop and wait for it to exit."""
        thread = self._bg_thread
        if thread is None or not thread.is_alive():
            self._bg_thread = None
            return True
        self._bg_stop.set()
        thread.join(timeout=timeout)
        with self._lock:
            still_alive = thread.is_alive()
            if not still_alive:
                self._bg_thread = None
            return not still_alive

    @property
    def is_running(self) -> bool:
        """True when the background warming thread is alive."""
        thread = self._bg_thread
        return thread is not None and thread.is_alive()

    def _run_background(self) -> None:
        """Background loop: due strategies are warmed on each tick."""
        while not self._bg_stop.is_set():
            with self._lock:
                states = list(self._states.values())
            now = _utcnow()
            for state in states:
                if not _should_run(state, now):
                    continue
                self._run_one_strategy(state)
            if self._bg_stop.wait(_BACKGROUND_TICK_SECONDS):
                return

    def _run_one_strategy(self, state: _StrategyState) -> None:
        """Run *state*'s predict_fn and warm each returned key."""
        now = _utcnow()
        with self._lock:
            try:
                keys = state.strategy.predict_fn()
            except Exception:  # noqa: BLE001
                logger.debug(
                    "background predict_fn for %r raised",
                    state.strategy.name,
                    exc_info=True,
                )
                state.last_run = now
                return
            for key in keys:
                try:
                    value = state.strategy.load_fn(key)
                except Exception:  # noqa: BLE001
                    state.error_count += 1
                    continue
                if value is None:
                    continue
                self._cache.set(key, value)
                state.warm_count += 1
                self._warm_count += 1
            state.last_run = now


__all__ = [
    "CachePreWarmer",
    "WarmingStrategy",
    "_should_run",
    "_StrategyState",
    "_utcnow",
    "_backoff_delay",
    "model_list_strategy",
    "session_list_strategy",
]


def _backoff_delay(attempt: int, base: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay."""
    import math

    return min(base * (2**attempt), max_delay)
