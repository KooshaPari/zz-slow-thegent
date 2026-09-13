"""Shared assertion helpers for split e2e CLI suites."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

__all__ = ["expected_trend_health_signature", "load_cli_json"]


def load_cli_json(payload: str) -> dict[str, Any]:
    """Resilient JSON loader that skips non-JSON leading noise."""
    match = re.search(r"[\{\[]", payload)
    if not match:
        return json.loads(payload)
    return json.loads(payload[match.start() :])


def expected_trend_health_signature() -> tuple[dict[str, object], str]:
    """Return the expected trend-health policy payload and deterministic hash."""
    policy = {
        "healthy_threshold": 95,
        "warning_threshold": 80,
        "degraded_threshold": 50,
        "min_coverage_pct": 80.0,
        "max_invalid_timestamps": 0,
        "coverage_penalty_per_pct": 1.25,
        "deficit_penalty_per_missing_sample": 15.0,
        "invalid_timestamp_penalty_per_event": 12.0,
        "stale_penalty": 8.0,
        "critical_penalty": 20.0,
        "unknown_or_future_penalty": 30.0,
        "gap_penalty": 10.0,
        "missing_baseline_penalty": 45.0,
    }
    signature = hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return policy, signature
