"""DAG recover command implementation (AUDIT-N+19 Phase 4).

Implements the three canonical recovery actions:

  * ``retry-failed`` — flip every ``status == "failed"`` task to
    ``"pending"`` so the next ``dag_run`` picks them up again.
  * ``clear-stuck`` — flip every ``status == "running"`` task to
    ``"pending"`` so the operator can re-spawn.
  * ``reset-retries`` — reset every task's ``retry_count`` to ``"0"``
    so retry limits are restored.

Parses the canonical ``.factory/dag-session.md`` via the canonical
``dag_impl`` helpers and writes back via :func:`_atomic_write` so the
operator's changes are durable.

Pinned by ``tests/test_unit_cli_impl_dag.py::TestDagRecoverCmd``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Module-level shim so @patch("thegent.cli.commands.dag_recover_cmd_impl.<x>", ...)
# mock targets resolve cleanly. The real implementations live in
# dag_impl / impl — these are pure re-exports.
try:
    from thegent.cli.commands import dag_impl as _dag_impl  # noqa: F401
except Exception:  # pragma: no cover - defensive
    _dag_impl = None  # type: ignore[assignment]


_VALID_ACTIONS = frozenset({"retry-failed", "clear-stuck", "reset-retries"})


def _impl_module() -> Any:
    """Return the live ``thegent.cli.commands.impl`` module."""
    return sys.modules.get("thegent.cli.commands.impl")


def _resolve_cwd(cd: Path | None) -> Path | None:
    """Delegate to :func:`thegent.cli.commands.impl._resolve_cwd` (live lookup)."""
    impl_mod = _impl_module()
    fn = getattr(impl_mod, "_resolve_cwd", None) if impl_mod is not None else None
    if fn is None:
        from thegent.cli.commands.session_impl import _resolve_cwd as _rcwd

        return _rcwd(cd)
    return fn(cd)


def dag_recover_cmd(*, cd: Path | None = None, action: str = "retry-failed") -> dict[str, Any]:
    """Recover a DAG document according to ``action``.

    Args:
        cd: Optional working directory.
        action: One of ``"retry-failed"``, ``"clear-stuck"``,
            ``"reset-retries"``. Unknown actions raise :class:`ValueError`.

    Returns:
        Dict with ``action``, ``changed`` (list of task ids) and the
        post-recovery document.

    Raises:
        ValueError: When ``action`` is not one of the canonical three.

    Pinned by ``tests/test_unit_cli_impl_dag.py::TestDagRecoverCmd``.
    """
    if action not in _VALID_ACTIONS:
        raise ValueError(f"Unknown dag_recover_cmd action: {action!r}. Expected one of: {sorted(_VALID_ACTIONS)}")
    if _dag_impl is None:
        return {"action": action, "changed": [], "error": "dag_impl unavailable"}

    cwd = _resolve_cwd(cd)
    if cwd is None:
        return {"action": action, "changed": [], "error": "could not resolve cwd"}
    dag_path = cwd / ".factory" / "dag-session.md"
    if not dag_path.exists():
        return {"action": action, "changed": [], "error": f"DAG not found: {dag_path}"}

    doc = _dag_impl._parse_dag_full(dag_path)
    changed: list[str] = []
    for task in doc.tasks:
        tid = task.get("id")
        status = task.get("status")
        if action == "retry-failed" and status == "failed":
            task["status"] = "pending"
            changed.append(tid)
        elif (action == "clear-stuck" and status == "running") or (action == "reset-retries" and "retry_count" in task):
            if action == "clear-stuck":
                task["status"] = "pending"
            else:
                task["retry_count"] = "0"
            changed.append(tid)

    # Persist via the canonical atomic-write helper.
    if changed:
        serialized = _dag_impl._serialize_dag(doc)
        _dag_impl._atomic_write(dag_path, serialized)

    return {"action": action, "changed": changed, "doc": doc}


__all__ = ["dag_recover_cmd"]
