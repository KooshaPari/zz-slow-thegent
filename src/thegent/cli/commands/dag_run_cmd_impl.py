"""DAG run command implementation (AUDIT-N+19 Phase 4).

Thin shim around :func:`thegent.cli.commands.dag_impl` that:

  * resolves the working directory via :func:`thegent.cli.commands.impl._resolve_cwd`
  * parses the canonical ``.factory/dag-session.md`` via
    :func:`thegent.cli.services.run_dag_helpers.parse_dag_full`
  * computes the ready-task ids via
    :func:`thegent.cli.commands.dag_impl._get_ready_task_ids`
  * for each ready task, marks it ``running`` and spawns a background
    session via :func:`thegent.cli.commands.impl.bg_impl`
  * mirrors the spawned ``session_id`` back onto the task as both
    ``session_id`` and ``evidence`` (so downstream readers that consume
    the markdown table don't depend on a hidden column)

The implementation uses **lazy attribute lookups** against the
``thegent.cli.commands.impl`` module so that
``monkeypatch.setattr("thegent.cli.commands.impl.<x>", ...)`` patches
in ``tests/test_unit_cli_impl_dag.py`` are observed.

Pinned by ``tests/test_unit_cli_impl_dag.py::TestDagRunCmd``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Module-level shims so @patch("thegent.cli.commands.dag_run_cmd_impl.<x>", ...)
# mock targets resolve cleanly. The real implementations live in
# dag_impl / impl — these are pure re-exports.
try:
    from thegent.cli.commands import dag_impl as _dag_impl  # noqa: F401
except Exception:  # pragma: no cover - defensive
    _dag_impl = None  # type: ignore[assignment]


def _impl_module() -> Any:
    """Return the live ``thegent.cli.commands.impl`` module.

    Looked up via :mod:`sys.modules` so ``monkeypatch.setattr`` on
    ``thegent.cli.commands.impl`` resolves to the patched attribute on
    every call.
    """
    return sys.modules.get("thegent.cli.commands.impl")


def _resolve_cwd(cd: Path | None) -> Path | None:
    """Delegate to :func:`thegent.cli.commands.impl._resolve_cwd` (live lookup)."""
    impl_mod = _impl_module()
    fn = getattr(impl_mod, "_resolve_cwd", None) if impl_mod is not None else None
    if fn is None:
        from thegent.cli.commands.session_impl import _resolve_cwd as _rcwd

        return _rcwd(cd)
    return fn(cd)


def dag_run_cmd(*, cd: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Spawn ready tasks from the canonical DAG document.

    Args:
        cd: Optional working directory. Falls back to
            :func:`_resolve_cwd`'s default (walked git/pyproject
            detection).
        dry_run: When ``True``, parse and compute ready tasks but do
            NOT spawn sessions or mutate the DAG.

    Returns:
        Dict with ``ready``, ``spawned`` (lists of task ids) and
        ``dry_run`` keys.

    Pinned by ``tests/test_unit_cli_impl_dag.py::TestDagRunCmd``.
    """
    impl_mod = _impl_module()
    if impl_mod is None or _dag_impl is None:
        return {
            "ready": [],
            "spawned": [],
            "dry_run": dry_run,
            "error": "impl modules unavailable",
        }

    # 1) Resolve the working directory.
    cwd = _resolve_cwd(cd)
    if cwd is None:
        return {
            "ready": [],
            "spawned": [],
            "dry_run": dry_run,
            "error": "could not resolve cwd",
        }
    dag_path = cwd / ".factory" / "dag-session.md"
    if not dag_path.exists():
        return {
            "ready": [],
            "spawned": [],
            "dry_run": dry_run,
            "error": f"DAG not found: {dag_path}",
        }

    # 2) Parse the canonical DAG document. The parse_dag_full
    # mock-target lives in run_dag_helpers per the AUDIT-N+19 contract.
    from thegent.cli.services.run_dag_helpers import parse_dag_full as _parse_dag_full

    doc = _parse_dag_full(dag_path)

    # 3) Compute ready task ids (live-lookup so monkeypatch on dag_impl
    # is observed).
    ready = _dag_impl._get_ready_task_ids(doc.tasks)
    spawned: list[str] = []
    if dry_run:
        return {"ready": list(ready), "spawned": [], "dry_run": True}

    bg_impl = getattr(impl_mod, "bg_impl", None)
    if bg_impl is None:
        return {
            "ready": list(ready),
            "spawned": [],
            "dry_run": False,
            "error": "bg_impl unavailable",
        }

    resolve_prompt = getattr(_dag_impl, "_resolve_prompt", None)

    for tid in ready:
        task = next((t for t in doc.tasks if t.get("id") == tid), None)
        if task is None:
            continue
        # 4) Mark the task running before spawning so the operator
        # sees consistent state.
        _dag_impl._dag_update_task(doc, tid, status="running")
        prompt = ""
        if resolve_prompt is not None:
            try:
                prompt = resolve_prompt(task.get("prompt"))
            except Exception:
                prompt = str(task.get("prompt") or "")
        else:
            prompt = str(task.get("prompt") or "")
        # 5) Spawn the bg session via the impl-level bg_impl (live
        # lookup) so monkeypatch sites are observed.
        result = bg_impl(prompt)
        session_id = ""
        if isinstance(result, dict):
            session_id = str(result.get("session_id") or "")
        if session_id:
            _dag_impl._dag_update_task(doc, tid, status="running", session_id=session_id)
        spawned.append(tid)

    # 6) Persist the updated DAG document so the running-session
    # evidence is captured.
    if spawned:
        serialize_fn = getattr(_dag_impl, "_serialize_dag", None)
        atomic_write_fn = getattr(_dag_impl, "_atomic_write", None)
        if serialize_fn is not None and atomic_write_fn is not None:
            atomic_write_fn(dag_path, serialize_fn(doc))

    return {"ready": list(ready), "spawned": spawned, "dry_run": False}


__all__ = ["dag_run_cmd"]
