"""CLI DAG (Directed Acyclic Graph) commands.

This module is the canonical facade for all 16 ``dag_*_cmd`` functions.
Sub-modules (``dag_run_cmd_impl``, ``dag_recover_cmd_impl``, and the
WL-124 split stubs on ``plan_cmds``) may provide richer
implementations; this module guarantees the names are importable and
callable so downstream consumers (``thegent.dag`` Typer sub-app, WL-120
extraction hardening tests, MCP server wrappers) can resolve them
without circular-import risk.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Thin stubs — callable, importable, deterministic.
# ---------------------------------------------------------------------------


def dag_validate_cmd(*args: Any, **kwargs: Any) -> int:
    """Validate a DAG definition."""
    return 0


def dag_list_cmd() -> list[dict]:
    """List all DAGs."""
    return []


def dag_add_cmd(*args: Any, **kwargs: Any) -> int:
    """Add a new DAG."""
    return 0


def dag_remove_cmd(*args: Any, **kwargs: Any) -> int:
    """Remove a DAG."""
    return 0


def dag_cancel_cmd(*args: Any, **kwargs: Any) -> int:
    """Cancel a running DAG."""
    return 0


def dag_status_cmd(*args: Any, **kwargs: Any) -> int:
    """Show DAG status."""

    return 0


def dag_update_cmd(*args: Any, **kwargs: Any) -> int:
    """Update a DAG definition."""
    return 0


def dag_ready_cmd(*args: Any, **kwargs: Any) -> int:
    """Mark a DAG as ready."""
    return 0


def dag_reconcile_cmd(*args: Any, **kwargs: Any) -> int:
    """Reconcile DAG state."""
    return 0


def dag_run_cmd(dag_id: str = "", **kwargs: Any) -> dict:
    """Run a DAG."""
    return {"dag_id": dag_id, "status": "started"}


def dag_sync_cmd(*args: Any, **kwargs: Any) -> int:
    """Sync DAG definitions."""
    return 0


def dag_checkpoint_cmd(*args: Any, **kwargs: Any) -> int:
    """Create a DAG checkpoint."""
    return 0


def dag_rollback_cmd(*args: Any, **kwargs: Any) -> int:
    """Rollback to a previous DAG checkpoint."""
    return 0


def dag_checkpoints_cmd(*args: Any, **kwargs: Any) -> int:
    """List DAG checkpoints."""
    return 0


def dag_recover_cmd(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Recover a failed DAG run."""
    return {"status": "recovered"}


def dag_probe_cmd(*args: Any, **kwargs: Any) -> int:
    """Probe DAG health."""
    return 0


__all__ = [
    "dag_validate_cmd",
    "dag_list_cmd",
    "dag_add_cmd",
    "dag_remove_cmd",
    "dag_cancel_cmd",
    "dag_status_cmd",
    "dag_update_cmd",
    "dag_ready_cmd",
    "dag_reconcile_cmd",
    "dag_run_cmd",
    "dag_sync_cmd",
    "dag_checkpoint_cmd",
    "dag_rollback_cmd",
    "dag_checkpoints_cmd",
    "dag_recover_cmd",
    "dag_probe_cmd",
]
