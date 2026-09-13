"""Planning tuning module."""

from __future__ import annotations

from typing import Any

__all__ = ["RunbookTuner"]


class RunbookTuner:
    """Tuner for runbooks."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    def tune(self, runbook: dict[str, Any]) -> dict[str, Any]:
        """Tune a runbook."""
        return runbook
