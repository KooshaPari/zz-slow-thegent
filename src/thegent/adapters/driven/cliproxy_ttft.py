"""TTFT (time-to-first-token) tracker for streaming LLM responses.

Extracted from cliproxy_adapter.py as part of L1 architecture hardening
(file-size reduction + module decomposition).

GW-38: Time-to-First-Token measurement for streaming responses.
"""

from __future__ import annotations

import time


class TTFTTracker:
    """Time-to-First-Token tracker for streaming LLM responses (GW-38).

    Usage:
        tracker = TTFTTracker()
        tracker.start()
        # ... receive first SSE chunk ...
        tracker.record_first_token()
        ttft = tracker.ttft_seconds  # float

    # @trace FR-OBS-038
    """

    def __init__(self) -> None:
        self._start: float | None = None
        self._first_token: float | None = None

    def start(self) -> None:
        """Record the request start time."""
        self._start = time.monotonic()

    def record_first_token(self) -> None:
        """Record when the first token arrived (idempotent — only first call counts)."""
        if self._first_token is None and self._start is not None:
            self._first_token = time.monotonic()

    @property
    def ttft_seconds(self) -> float | None:
        """Return TTFT in seconds, or None if not yet measured."""
        if self._start is None or self._first_token is None:
            return None
        return self._first_token - self._start

    def build_ttft_header(self) -> dict[str, str]:
        """Build tg-ttft-ms header with TTFT in milliseconds.

        Returns {} if TTFT not yet measured.
        """
        ttft = self.ttft_seconds
        if ttft is None:
            return {}
        return {"tg-ttft-ms": f"{ttft * 1000:.1f}"}
