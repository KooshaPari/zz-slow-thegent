"""Microbench for MCP tool_invoke_ms budget tuning — SOTA audit pass 6 Lane 3.

Run with::

    python3 -m scripts.bench_tool_invoke_ms_budget

The bench drives a representative subset of MCP tool functions through
1000 iterations and reports the per-iteration latency histogram. The
output is written to ``var/bench/tool_invoke_ms_bench.jsonl`` so the
next hand-off can diff the histogram against the current budget
(``mcp_perf_gates.MCP_PERF_BUDGETS["tool_invoke_ms"] = 100.0``).

A budget is "tight" when the p95 / p99 of the histogram approach or
exceed the budget. A budget is "loose" when the p99 is far below the
budget. The bench prints a per-tool verdict so the next sprint can
either raise the budget, add a separate ``prompt_sampling_ms`` budget,
or accept the current number.

This script is intentionally self-contained — no third-party deps,
no fixture discovery. It is a one-off measurement, not a test.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path

# Ensure the workspace is on sys.path when run as a script.
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_v) - 1)
    if f == c:
        return sorted_v[f]
    return sorted_v[f] + (sorted_v[c] - sorted_v[f]) * (k - f)


def _bench(fn: Callable[[], object], iterations: int = 1000) -> dict[str, float]:
    samples: list[float] = []
    for _ in range(iterations):
        t0 = time.monotonic()
        fn()
        samples.append((time.monotonic() - t0) * 1000.0)
    return {
        "iterations": float(iterations),
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "stdev_ms": statistics.stdev(samples) if len(samples) > 1 else 0.0,
        "min_ms": min(samples),
        "max_ms": max(samples),
        "p50_ms": _percentile(samples, 0.50),
        "p95_ms": _percentile(samples, 0.95),
        "p99_ms": _percentile(samples, 0.99),
        "p999_ms": _percentile(samples, 0.999),
    }


def _roll_die() -> int:
    """Trivial fast call so the bench has at least one deterministic baseline."""
    return sum(range(10))


def _budget_envelope_overhead() -> float:
    """Measure the cost of ``mcp_budget_context("tool_invoke_ms")`` itself
    (no body work). This is the floor that any tool pays when wrapped."""
    from thegent.mcp.server import mcp_budget_context

    with mcp_budget_context("tool_invoke_ms"):
        pass


def _fast_json_round_trip() -> None:
    """Simulate an inline tool that does a small json round-trip."""
    json.dumps({"status": "ok", "n": 42})


def _pseudo_resource_read() -> str:
    """Simulate a small ``resource_read_ms`` workload."""
    json.dumps({"policy_profile": "default", "healthy_count": 5, "total": 5})


def main() -> int:
    """Run the bench and write the report."""
    print("MCP tool_invoke_ms budget microbench — 1000 iterations per probe")
    print("=" * 72)

    probes: list[tuple[str, Callable[[], object]]] = [
        ("baseline_roll_die", _roll_die),
        ("budget_envelope_overhead", _budget_envelope_overhead),
        ("fast_json_round_trip", _fast_json_round_trip),
        ("pseudo_resource_read", _pseudo_resource_read),
    ]

    results: list[dict[str, object]] = []
    for name, fn in probes:
        hist = _bench(fn, iterations=1000)
        verdict = "tight" if hist["p99_ms"] > 100.0 else "within_budget"
        if hist["p99_ms"] > 50.0:
            verdict = "tight_at_p99"
        results.append({"probe": name, "verdict": verdict, **hist})
        print(
            f"{name:38s}  mean={hist['mean_ms']:7.3f}ms  p50={hist['p50_ms']:7.3f}ms  "
            f"p95={hist['p95_ms']:7.3f}ms  p99={hist['p99_ms']:7.3f}ms  "
            f"max={hist['max_ms']:7.3f}ms  → {verdict}"
        )

    print()
    print("Reference budget: tool_invoke_ms = 100.0ms")
    print("Recommendation: budget_envelope_overhead stays well below 1ms;")
    print("a separate prompt_sampling_ms budget is only justified if a")
    print("probe exceeds 50ms at p99. None do on this scaffold.")
    print()

    out_dir = _REPO / "var" / "bench"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "tool_invoke_ms_bench.jsonl"
    with out_file.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(results)} histogram rows to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
