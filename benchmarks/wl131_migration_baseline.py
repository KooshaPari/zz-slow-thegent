"""WL-131: Python baseline benchmarks for Batch-A Rust migration candidates.

Records per-call latency for parse_model_suffix — the primary function
nominated for Rust migration in the WL-131 Batch-A plan.

# @trace WL-131 B90-W2-F3
"""

from __future__ import annotations

import logging
import time

import orjson as json
from thegent.routing.model_suffix_parser import parse_model_suffix

INPUTS = [
    "openai/gpt-4o",
    "anthropic/claude-3-5-sonnet",
    "mistral/mistral-large-2411",
    "google/gemini-pro-1.5",
    "openrouter/meta/llama-3.1-70b",
]


def benchmark_parse_model_suffix() -> dict[str, float | int]:
    """Benchmark parse_model_suffix over N iterations and return timing dict."""
    N = 10_000
    start = time.perf_counter()
    for _ in range(N):
        for inp in INPUTS:
            parse_model_suffix(inp)
    elapsed = time.perf_counter() - start
    total_calls = N * len(INPUTS)
    return {
        "n": total_calls,
        "elapsed_s": elapsed,
        "per_call_us": (elapsed / total_calls) * 1e6,
    }


if __name__ == "__main__":
    result = benchmark_parse_model_suffix()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger(__name__).info(json.dumps(result, indent=2).decode())
