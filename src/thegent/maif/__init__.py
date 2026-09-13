"""STUB MODULE - thegent.maif

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.

AUDIT-N+5 — extended with a minimal ``MAIFRunner`` so
:mod:`thegent.cli.services.run_execution_core_helpers` imports cleanly.
The full MAIF pipeline is tracked as follow-up work; this shim records
the two call-site events (``record_run_start``, ``record_run_end``) to a
module-level list so audit-trail inspectors can pick them up without
spinning up the full MAIF stack.
"""

from __future__ import annotations

from typing import Any

__all__ = ["MAIFRunner"]


_RECORDED_RUNS: list[dict[str, Any]] = []


class MAIFRunner:
    """AUDIT-N+5 stub — records ``record_run_start`` / ``record_run_end``
    events into a module-level list.

    The orchestrator in
    :mod:`thegent.cli.services.run_execution_core_helpers` only needs
    these two methods to fire without raising; persisted MAIF artifacts
    are produced via :class:`thegent.execution.Auditor`.
    """

    __slots__ = ("session_dir",)

    def __init__(self, session_dir: Any = None) -> None:
        self.session_dir = session_dir

    def record_run_start(
        self,
        *,
        run_id: str,
        owner: str,
        prompt: str,
        agent: str,
    ) -> None:
        """Record a run-start event."""
        _RECORDED_RUNS.append(
            {
                "event": "start",
                "run_id": run_id,
                "owner": owner,
                "prompt": prompt,
                "agent": agent,
            }
        )

    def record_run_end(
        self,
        *,
        run_id: str,
        status: str,
        output_summary: str,
    ) -> None:
        """Record a run-end event."""
        _RECORDED_RUNS.append(
            {
                "event": "end",
                "run_id": run_id,
                "status": status,
                "output_summary": output_summary,
            }
        )
