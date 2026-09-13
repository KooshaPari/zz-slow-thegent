"""Work stream implementation.

This module contains the work stream implementation functions.

WL-125 closure: surfaces the orchestration wrappers and pre_work_gate
governance wrappers required by ``tests/test_wl125_*_parity.py`` and the
architecture contract in ``scripts/check_instruction_architecture.py``.
All wrappers are thin single-call delegates to canonical homes in
:mod:`thegent.cli.services`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from thegent.cli.services import (
    pre_work_gate_helpers,
    work_stream_orchestration,
)


def create_work_stream(name: str, **kwargs) -> dict:
    """Create a new work stream.

    Args:
        name: Work stream name.
        **kwargs: Additional options.

    Returns:
        Created work stream dictionary.
    """
    return {"name": name, "status": "created"}


def list_work_streams(**kwargs) -> list[dict]:
    """List all work streams.

    Args:
        **kwargs: Additional options.

    Returns:
        List of work stream dictionaries.
    """
    return []


def get_work_stream(stream_id: str) -> dict | None:
    """Get a work stream by ID.

    Args:
        stream_id: Work stream identifier.

    Returns:
        Work stream dictionary or None if not found.
    """
    return None


# -- pre_work_gate governance wrappers (WL-125 closure) ------------------


def _pre_work_gate_defaults() -> dict[str, Any]:
    """WL-125 delegate to :func:`pre_work_gate_helpers.pre_work_gate_defaults`."""
    return pre_work_gate_helpers.pre_work_gate_defaults()


def _pre_work_gate_thresholds(project_dir: Path) -> tuple[dict[str, Any], str]:
    """WL-125 delegate to :func:`pre_work_gate_helpers.pre_work_gate_thresholds`."""
    return pre_work_gate_helpers.pre_work_gate_thresholds(project_dir)


def _evidence_age_minutes(path: Path) -> int:
    """WL-125 delegate to :func:`pre_work_gate_helpers.evidence_age_minutes`."""
    return pre_work_gate_helpers.evidence_age_minutes(path)


def _pre_work_governance_block_payload(
    *,
    project_dir: Path,
    thresholds: dict[str, Any],
    violations: list[dict[str, Any]],
    config_source: str,
) -> dict[str, Any]:
    """WL-125 delegate to :func:`pre_work_gate_helpers.pre_work_governance_block_payload`."""
    return pre_work_gate_helpers.pre_work_governance_block_payload(
        project_dir=project_dir,
        thresholds=thresholds,
        violations=violations,
        config_source=config_source,
    )


def _enforce_pre_work_hard_gate(project_dir: Path) -> dict[str, Any] | None:
    """WL-125 delegate to :func:`pre_work_gate_helpers.enforce_pre_work_hard_gate`."""
    return pre_work_gate_helpers.enforce_pre_work_hard_gate(project_dir)


# -- orchestration wrappers (WL-125 closure) -----------------------------


def do_next_impl(cd: Path | None = None, limit: int = 5) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.do_next_impl`."""
    return work_stream_orchestration.do_next_impl(cd=cd, limit=limit)


def wait_next_impl(
    cd: Path | None = None,
    poll_interval: float = 2.0,
    timeout: float = 0.0,
    sources: tuple[str, ...] = ("do_next",),
) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.wait_next_impl`."""
    return work_stream_orchestration.wait_next_impl(
        cd=cd,
        poll_interval=poll_interval,
        timeout=timeout,
        sources=sources,
    )


def spawn_next_impl(
    cd: Path | None = None,
    limit: int = 10,
    agent: str = "free",
    timeout: int | None = None,
    lane: str = "critical",
    override_reason: str = "manual-next-step",
    claim: bool = True,
) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.spawn_next_impl`."""
    return work_stream_orchestration.spawn_next_impl(
        cd=cd,
        limit=limit,
        agent=agent,
        timeout=timeout,
        lane=lane,
        override_reason=override_reason,
        claim=claim,
    )


def work_stream_claim_impl(
    item_id: str,
    agent_id: str,
    cd: Path | None = None,
) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.work_stream_claim_impl`."""
    return work_stream_orchestration.work_stream_claim_impl(item_id=item_id, agent_id=agent_id, cd=cd)


def work_stream_complete_impl(
    item_id: str,
    agent_id: str,
    cd: Path | None = None,
) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.work_stream_complete_impl`."""
    return work_stream_orchestration.work_stream_complete_impl(item_id=item_id, agent_id=agent_id, cd=cd)


def incorporate_impl(cd: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.incorporate_impl`."""
    return work_stream_orchestration.incorporate_impl(cd=cd, dry_run=dry_run)


def _validate_task_and_record_errors(
    tf: Path,
    validation_errors: list[dict[str, Any]],
) -> None:
    """WL-125 thin delegate to :func:`work_stream_orchestration._validate_task_and_record_errors`."""
    work_stream_orchestration._validate_task_and_record_errors(
        tf=tf,
        validation_errors=validation_errors,
    )


def continuity_snapshot_impl(
    owner: str,
    run_ids: list[str],
    state_summary: dict[str, Any] | None = None,
    next_steps: list[str] | None = None,
) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.continuity_snapshot_impl`."""
    return work_stream_orchestration.continuity_snapshot_impl(
        owner=owner,
        run_ids=run_ids,
        state_summary=state_summary,
        next_steps=next_steps,
    )


__all__ = [
    "create_work_stream",
    "list_work_streams",
    "get_work_stream",
    # pre_work_gate wrappers (WL-125 closure)
    "_pre_work_gate_defaults",
    "_pre_work_gate_thresholds",
    "_evidence_age_minutes",
    "_pre_work_governance_block_payload",
    "_enforce_pre_work_hard_gate",
    # orchestration wrappers (WL-125 closure)
    "do_next_impl",
    "wait_next_impl",
    "spawn_next_impl",
    "work_stream_claim_impl",
    "work_stream_complete_impl",
    "incorporate_impl",
    "_validate_task_and_record_errors",
    "continuity_snapshot_impl",
]
