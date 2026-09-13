"""WP-5005: Usage spike circuit breakers.

Hardening (AUDIT-N+53 — SOTA pass-37)
--------------------------------------
Contract surface asserted by
``tests/test_unit_audit_n53_breakers_hardening.py``
(``FR-GOV-CB-001..015``).

# @trace AUDIT-N+53
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson as json

_log = logging.getLogger(__name__)


class CircuitBreaker:
    """Breaks the flow when usage spikes are detected.

    ``FR-GOV-CB-001`` .. ``FR-GOV-CB-015``.
    """

    def __init__(
        self,
        session_dir: Path,
        threshold_usd_per_min: float = 1.0,
    ) -> None:
        session_dir = Path(session_dir)
        # FR-GOV-CB-002 — absolute path required.
        if not session_dir.is_absolute():
            raise ValueError(f"session_dir must be an absolute path (got {session_dir!s})")
        # FR-GOV-CB-003 — threshold must be strictly positive.
        if threshold_usd_per_min <= 0:
            raise ValueError(f"threshold_usd_per_min must be > 0 (got {threshold_usd_per_min})")

        self.session_dir = session_dir
        self.breaker_file = session_dir / "circuit_breakers.jsonl"
        self.threshold_usd_per_min = threshold_usd_per_min

    def check_spike(self, current_batch_cost: float) -> bool:
        """Return True (and trip) when *current_batch_cost* exceeds threshold.

        ``FR-GOV-CB-004`` / ``FR-GOV-CB-005``: uses strict ``>`` so equality
        is not treated as a spike.
        """
        if current_batch_cost > self.threshold_usd_per_min:
            self.trip("Usage spike detected", current_batch_cost)
            return True
        return False

    def trip(self, reason: str, value: float) -> None:
        """Append a tripped event to the JSONL ledger.

        ``FR-GOV-CB-006`` / ``FR-GOV-CB-007``.
        """
        _log.critical("CIRCUIT BREAKER TRIPPED: %s (value: %s)", reason, value)
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "tripped",
            "reason": reason,
            "value": value,
        }
        self._append_event(event)

    def is_tripped(self) -> bool:
        """Return True if the most recent valid event is ``tripped``.

        ``FR-GOV-CB-008`` / ``FR-GOV-CB-009`` / ``FR-GOV-CB-010``.
        """
        last = self.last_event()
        if last is None:
            return False
        return last.get("event") == "tripped"

    def reset(self) -> None:
        """Clear the tripped state by appending a ``reset`` event.

        ``FR-GOV-CB-011`` / ``FR-GOV-CB-012``.
        """
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "reset",
            "reason": "manual_reset",
            "value": 0.0,
        }
        self._append_event(event)

    def last_event(self) -> dict[str, Any] | None:
        """Return the most recent parseable JSONL event, or None.

        ``FR-GOV-CB-013``. Corrupt trailing lines are skipped.
        """
        if not self.breaker_file.exists():
            return None
        lines = self.breaker_file.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _append_event(self, event: dict[str, Any]) -> None:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        with self.breaker_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event).decode() + "\n")


__all__ = [
    "CircuitBreaker",
]
