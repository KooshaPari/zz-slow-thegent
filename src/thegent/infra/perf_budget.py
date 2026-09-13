"""Performance budget gates — P-090 (SOTA hardening audit).

Provides load-time and memory gates that enforce budgets on module
imports and runtime memory usage.  Referenced in the SOTA cockpit as
the performance-budget lane (P-090).

Usage::

    check_module_load_budget("json", max_load_ms=10.0)
    check_memory_budget("after-config", max_bytes=50_000_000)

    with budget_context("startup") as result:
        ...
    # result.within_budget, result.elapsed_ms, ...
"""

from __future__ import annotations

import importlib
import resource
import sys
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class PerformanceBudgetError(Exception):
    """Raised when a performance budget is exceeded.

    Attributes:
        module_name: Module that was checked (load-time gate) or *None*.
        actual_ms: Measured load time in ms (load-time gate).
        budget_ms: Allowed budget in ms (load-time gate).
        actual_bytes: Measured memory in bytes (memory gate).
        budget_bytes: Allowed budget in bytes (memory gate).
        label: Label for the checked resource.
    """

    def __init__(
        self,
        *,
        message: str,
        module_name: str | None = None,
        actual_ms: float | None = None,
        budget_ms: float | None = None,
        actual_bytes: int | None = None,
        budget_bytes: int | None = None,
        label: str | None = None,
    ) -> None:
        super().__init__(message)
        self.module_name = module_name
        self.actual_ms = actual_ms
        self.budget_ms = budget_ms
        self.actual_bytes = actual_bytes
        self.budget_bytes = budget_bytes
        self.label = label


# ---------------------------------------------------------------------------
# BudgetResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class BudgetResult:
    """Result yielded by :func:`budget_context`."""

    label: str
    elapsed_ms: float
    peak_memory_bytes: int
    within_budget: bool = True


# ---------------------------------------------------------------------------
# Module-level state (thread-safe)
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_checked_modules: dict[str, float] = {}
_violations: list[dict[str, Any]] = []
_peak_memory: int = 0


def _current_rss_bytes() -> int:
    """Return current RSS in bytes, handling platform differences.

    On Linux ``ru_maxrss`` is in kilobytes; on macOS it is in bytes.
    We detect the platform via ``sys.platform``.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = usage.ru_maxrss
    if sys.platform == "linux":
        rss *= 1024  # convert KB -> bytes
    return rss


def _record_violation(violation: dict[str, Any]) -> None:
    """Thread-safe append to the global violations list."""
    with _lock:
        _violations.append(violation)


# ---------------------------------------------------------------------------
# Load-time gate
# ---------------------------------------------------------------------------


def check_module_load_budget(
    module_name: str,
    *,
    max_load_ms: float = 50.0,
) -> float:
    """Measure import time for *module_name* and enforce *max_load_ms*.

    Results are cached so repeated checks for the same module are
    idempotent.  Raises :class:`PerformanceBudgetError` when the budget
    is exceeded.

    Returns the load time in milliseconds.
    """
    with _lock:
        if module_name in _checked_modules:
            elapsed_ms = _checked_modules[module_name]
            if elapsed_ms > max_load_ms:
                msg = f"Module '{module_name}' load time {elapsed_ms:.2f} ms exceeds budget {max_load_ms:.2f} ms (cached)"
                raise PerformanceBudgetError(
                    message=msg,
                    module_name=module_name,
                    actual_ms=elapsed_ms,
                    budget_ms=max_load_ms,
                )
            return elapsed_ms

    # Import outside lock to avoid holding it during I/O.
    t0 = time.perf_counter()
    importlib.import_module(module_name)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    with _lock:
        _checked_modules[module_name] = elapsed_ms

    if elapsed_ms > max_load_ms:
        _record_violation(
            {
                "type": "load_time",
                "module_name": module_name,
                "actual_ms": elapsed_ms,
                "budget_ms": max_load_ms,
            }
        )
        msg = f"Module '{module_name}' load time {elapsed_ms:.2f} ms exceeds budget {max_load_ms:.2f} ms"
        raise PerformanceBudgetError(
            message=msg,
            module_name=module_name,
            actual_ms=elapsed_ms,
            budget_ms=max_load_ms,
        )
    return elapsed_ms


# ---------------------------------------------------------------------------
# Memory gate
# ---------------------------------------------------------------------------


def check_memory_budget(
    label: str,
    *,
    max_bytes: int = 10_000_000,
) -> int:
    """Measure current RSS and enforce *max_bytes* budget.

    Raises :class:`PerformanceBudgetError` when the budget is exceeded.

    Returns the current RSS in bytes.
    """
    global _peak_memory  # noqa: PLW0603

    rss = _current_rss_bytes()
    with _lock:
        _peak_memory = max(_peak_memory, rss)

    if rss > max_bytes:
        _record_violation(
            {
                "type": "memory",
                "label": label,
                "actual_bytes": rss,
                "budget_bytes": max_bytes,
            }
        )
        msg = f"Memory budget exceeded for '{label}': {rss} bytes > {max_bytes} bytes"
        raise PerformanceBudgetError(
            message=msg,
            actual_bytes=rss,
            budget_bytes=max_bytes,
            label=label,
        )
    return rss


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def get_perf_summary() -> dict[str, Any]:
    """Return a summary of all performance budget checks.

    Keys:
        checked_modules: Dict mapping module name -> load time in ms.
        total_load_ms: Sum of all cached load times.
        peak_memory_bytes: Highest RSS observed via memory gates.
        violations: List of violation dicts recorded during this session.
    """
    with _lock:
        total_load = sum(_checked_modules.values())
        return {
            "checked_modules": dict(_checked_modules),
            "total_load_ms": total_load,
            "peak_memory_bytes": _peak_memory,
            "violations": list(_violations),
        }


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


@contextmanager
def budget_context(label: str) -> Generator[BudgetResult]:
    """Context manager that records wall-clock time and peak RSS.

    Yields a :class:`BudgetResult` dataclass.  Timing and memory
    fields are populated when the ``with`` block exits.
    """
    global _peak_memory  # noqa: PLW0603
    rss_start = _current_rss_bytes()
    t0 = time.perf_counter()
    result = BudgetResult(
        label=label,
        elapsed_ms=0.0,
        peak_memory_bytes=rss_start,
    )
    try:
        yield result
    finally:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        rss_end = _current_rss_bytes()
        with _lock:
            peak = max(rss_end, _peak_memory)
            _peak_memory = peak
        result.elapsed_ms = elapsed_ms
        result.peak_memory_bytes = peak
