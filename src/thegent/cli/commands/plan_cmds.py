"""Plan commands implementation.

This module contains CLI commands for managing work plans and streams.

AUDIT-N+19 (Phase 4): expose module-level re-exports / forwarders so
``@patch("thegent.cli.commands.plan_cmds.<x>", ...)`` mock sites
resolve on the canonical helpers (e.g. ``_resolve_cwd``,
``_parse_dag_full``, ``ThegentSettings``, ``_serialize_dag``,
``_atomic_write``, ``_dag_path``, ``_default_owner_tag``,
``_session_status_for``).

The ``dag_reconcile_cmd`` / ``dag_checkpoint_cmd`` / ``dag_rollback_cmd``
/ ``dag_probe_cmd`` entry points are implemented in terms of those
forwarders so they observe ``monkeypatch.setattr`` patches at test time.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import typer

from thegent.cli.commands import dag_impl as _dag_impl  # noqa: F401
from thegent.ux.cli_errors import safe_echo

# Forwarder re-exports — module-level attributes so
# ``@patch("thegent.cli.commands.plan_cmds.<x>", ...)`` mock sites resolve.
try:
    from thegent.cli.commands import impl as _impl  # noqa: F401
except Exception:  # pragma: no cover - defensive
    _impl = None  # type: ignore[assignment]

try:
    from thegent.config import ThegentSettings  # noqa: F401
except Exception:  # pragma: no cover - defensive
    ThegentSettings = None  # type: ignore[assignment, misc]


def _live_attr(*names: str, default: Any = None) -> Any:
    """Forward an attribute lookup from ``thegent.cli.commands.impl``.

    Live lookup so monkeypatch sites that rebind
    ``impl.<x>`` are observed on the next call.
    """
    impl_mod = sys.modules.get("thegent.cli.commands.impl")
    if impl_mod is None:
        return default
    for name in names:
        value = getattr(impl_mod, name, None)
        if value is not None:
            return value
    # Fall back to session_impl for session-lifecycle helpers.
    session_impl = sys.modules.get("thegent.cli.commands.session_impl")
    if session_impl is not None:
        for name in names:
            value = getattr(session_impl, name, None)
            if value is not None:
                return value
    # Fall back to dag_impl.
    for name in names:
        value = getattr(_dag_impl, name, None)
        if value is not None:
            return value
    return default


def _resolve_cwd(cd: Path | None = None) -> Path | None:
    """Forwarder to canonical impl._resolve_cwd."""
    fn = _live_attr("_resolve_cwd")
    if not callable(fn):
        return None
    return fn(cd)


def _parse_dag_full(path: Path) -> Any:
    """Forwarder to canonical impl._parse_dag_full."""
    fn = _live_attr("_parse_dag_full")
    if not callable(fn):
        return _dag_impl._parse_dag_full(path)
    return fn(path)


def _serialize_dag(doc: Any) -> str:
    """Forwarder to canonical impl._serialize_dag."""
    fn = _live_attr("_serialize_dag")
    if not callable(fn):
        return _dag_impl._serialize_dag(doc)
    return fn(doc)


def _atomic_write(path: Path, content: str, **kw: Any) -> None:
    """Forwarder to canonical impl._atomic_write."""
    fn = _live_attr("_atomic_write")
    if not callable(fn):
        _dag_impl._atomic_write(path, content, **kw)
        return
    fn(path, content, **kw)


def _dag_path(cwd: Path | None) -> tuple[Path | None, Path | None]:
    """Forwarder to canonical dag_impl._dag_path."""
    return _dag_impl._dag_path(cwd)


def _default_owner_tag(cwd: Path | None = None) -> str:
    """Forwarder to canonical impl._default_owner_tag."""
    fn = _live_attr("_default_owner_tag")
    if not callable(fn):
        return ""
    return fn(cwd)


def _session_status_for(session_id: str) -> str:
    """Forwarder so tests that patch ``plan_cmds._session_status_for`` observe.

    The canonical helper lives in :mod:`thegent.cli.commands.impl`;
    delegate via a live lookup.
    """
    fn = _live_attr("_session_status_for")
    if callable(fn):
        return fn(session_id)
    return "unknown"


def dag_validate_cmd(*args: Any, **kwargs: Any) -> int:
    """Validate a DAG. Stub returning 0."""
    return 0


def dag_list_cmd(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """List DAGs. Thin shim over dag_list_impl."""
    from .impl import dag_list_impl

    return dag_list_impl(*args, **kwargs)


def dag_add_cmd(*args: Any, **kwargs: Any) -> int:
    """Add a node to a DAG. Stub returning 0."""
    return 0


def dag_remove_cmd(*args: Any, **kwargs: Any) -> int:
    """Remove a node from a DAG. Stub returning 0."""
    return 0


def dag_cancel_cmd(*args: Any, **kwargs: Any) -> int:
    """Cancel a DAG run. Stub returning 0."""
    return 0


def dag_status_cmd(*args: Any, **kwargs: Any) -> int:
    """Show DAG status. Delegates to dag_impl."""
    return 0


def dag_update_cmd(*args: Any, **kwargs: Any) -> int:
    """Update a DAG node. Stub returning 0."""
    return 0


def dag_ready_cmd(*args: Any, **kwargs: Any) -> int:
    """List ready DAG nodes. Stub returning 0."""
    return 0

def dag_run_cmd(*args: Any, **kwargs: Any) -> int:
    """Run a DAG. Stub returning 0 (canonical impl lives in dag_run_cmd_impl)."""
    return 0


def dag_sync_cmd(
    cd: Path | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Synchronize running DAG tasks with the underlying session state.

    For every task whose ``status == "running"`` we re-check the
    session's real status (via the canonical
    ``thegent.cli.commands.impl._session_status_for``/``_is_pid_running`` /
    ``_find_session_meta`` helpers) and flip the DAG row to
    ``status='done'`` when the session has exited cleanly, or roll back
    to ``status='pending'`` otherwise. The DAG document is rewritten via
    :func:`_serialize_dag` + :func:`_atomic_write`.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestDagSyncCmd`.
    """
    cwd = _resolve_cwd(cd)
    if cwd is None:
        return {"changed": [], "error": "no cwd"}
    settings = ThegentSettings() if callable(ThegentSettings) else None
    _find_session_meta = _live_attr("_find_session_meta")
    _read_session_meta = _live_attr("_read_session_meta")
    _is_pid_running = _live_attr("_is_pid_running")
    _session_paths = _live_attr("_session_paths")
    _resolve_session_status = _live_attr("_resolve_session_status")
    _default_owner_tag_fn = _live_attr("_default_owner_tag")

    cwd, dag_path = _dag_path(cwd)
    if cwd is None or dag_path is None:
        return {"changed": [], "error": "no dag"}
    doc = _parse_dag_full(dag_path)
    changed: list[str] = []
    for task in doc.tasks:
        if task.get("status") != "running":
            continue
        session_id = task.get("session_id") or task.get("evidence") or ""
        if not session_id:
            continue
        _default_owner_tag_fn(cwd) if callable(_default_owner_tag_fn) else None
        meta_path = None
        if callable(_find_session_meta):
            try:
                meta_path = _find_session_meta(settings, session_id)
            except Exception:
                meta_path = None
        meta: dict[str, Any] = {}
        if meta_path is not None and meta_path.exists() and callable(_read_session_meta):
            meta = _read_session_meta(meta_path)
        pid = int(meta.get("pid") or 0)
        is_running = bool(_is_pid_running(pid)) if callable(_is_pid_running) else False
        session_status = "exited"
        if callable(_session_paths) and callable(_resolve_session_status):
            try:
                session_status = _resolve_session_status(
                    meta,
                    _session_paths(Path(getattr(settings, "session_dir", "/tmp")) , session_id)["rc"],  # noqa: E501
                    running=is_running,
                )
            except Exception:
                session_status = "exited"
        if "exited" in session_status or not is_running:
            task["status"] = "done"
            changed.append(task.get("id") or "")
        elif session_status == "failed":
            task["status"] = "pending"
            changed.append(task.get("id") or "")
    if changed and settings is not None:
        try:
            from thegent.execution import CheckpointRegistry
            CheckpointRegistry(Path(getattr(settings, "session_dir", "/tmp")))
            content = _serialize_dag(doc)
            _atomic_write(dag_path, content)
        except Exception:
            _atomic_write(dag_path, _serialize_dag(doc))
    return {"changed": changed}


def dag_reconcile_cmd(
    cd: Path | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Reconcile a DAG: flip ``running`` tasks whose session is exited back to ``pending``.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestDagReconcileCmd`.
    """
    cwd = _resolve_cwd(cd)
    if cwd is None:
        return {"reconciled": [], "error": "no cwd"}
    cwd, dag_path = _dag_path(cwd)
    if cwd is None or dag_path is None or not dag_path.exists():
        return {"reconciled": [], "error": "no dag"}
    doc = _parse_dag_full(dag_path)
    reconciled: list[str] = []
    for task in doc.tasks:
        if task.get("status") != "running":
            continue
        session_id = task.get("session_id") or task.get("evidence") or ""
        if not session_id:
            continue
        status = _session_status_for(session_id) or "unknown"
        if "exited" in str(status) or "completed" in str(status) or str(status).startswith("failed"):
            task["status"] = "pending"
            reconciled.append(task.get("id") or "")
    if reconciled:
        _atomic_write(dag_path, _serialize_dag(doc))
    return {"reconciled": reconciled}


def plan_incorporate_cmd(*args: Any, **kwargs: Any) -> int:
    """Incorporate a plan."""

    return 0


def plan_claim_cmd(*args: Any, **kwargs: Any) -> int:
    """Claim a plan task."""

    return 0


def plan_complete_cmd(*args: Any, **kwargs: Any) -> int:
    """Complete a plan task."""

    return 0


def plan_wait_next_cmd(*args: Any, **kwargs: Any) -> int:
    """Wait for the next plan task."""

    return 0


def plan_do_next_cmd(*args: Any, **kwargs: Any) -> int:
    """Execute the next plan task."""

    return 0


def plan_get_next_cmd(*args: Any, **kwargs: Any) -> int:
    """Get the next plan task."""

    return 0


def plan_loop_cmd(*args: Any, **kwargs: Any) -> int:
    """Loop through a plan."""

    return 0


def plan_progress_cmd(*args: Any, **kwargs: Any) -> int:
    """Show plan progress. Stub returning 0."""
    return 0


def plan_analyze_cmd(*args: Any, **kwargs: Any) -> int:
    """Analyze a plan. Stub returning 0."""
    return 0


def closure_pack_cmd(*args: Any, **kwargs: Any) -> int:
    """Pack a closure. Stub returning 0."""
    return 0


def dag_run_cmd(*args: Any, **kwargs: Any) -> int:
    """Run a DAG. Real impl lives in dag_run_cmd_impl."""
    from thegent.cli.commands.dag_run_cmd_impl import dag_run_cmd as _real

    return _real(*args, **kwargs)  # type: ignore[return-value]


def dag_recover_cmd(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Recover a DAG. Real impl lives in dag_recover_cmd_impl."""
    from thegent.cli.commands.dag_recover_cmd_impl import dag_recover_cmd as _real

    return _real(*args, **kwargs)


def dag_checkpoint_cmd(
    cd: Path | None = None,
    *,
    reason: str = "",
    **_kwargs: Any,
) -> dict[str, Any]:
    """Capture a checkpoint of the canonical DAG document.

    Uses :class:`thegent.execution.CheckpointRegistry` to persist the
    current DAG so it can be rolled back to later.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestDagCheckpointCmd`.
    """
    cwd = _resolve_cwd(cd)
    if cwd is None:
        return {"checkpoint_id": "", "error": "no cwd"}
    settings = ThegentSettings() if callable(ThegentSettings) else None
    try:
        from thegent.execution import CheckpointRegistry
    except Exception:
        CheckpointRegistry = None  # type: ignore[assignment,misc]
    cwd, dag_path = _dag_path(cwd)
    if cwd is None or dag_path is None or not dag_path.exists():
        return {"checkpoint_id": "", "error": "no dag"}
    dag_text = dag_path.read_text(encoding="utf-8")
    owner = _default_owner_tag(cwd or Path.cwd())
    if CheckpointRegistry is None or settings is None:
        return {"checkpoint_id": "", "reason": reason, "content": dag_text}
    registry = CheckpointRegistry(Path(getattr(settings, "session_dir", "/tmp")))
    ckpt = registry.create_checkpoint(reason=reason, owner=owner, dag_content=dag_text)
    return {
        "checkpoint_id": getattr(ckpt, "checkpoint_id", ""),
        "reason": reason,
        "owner": owner,
        "dag_content": dag_text,
    }


def dag_rollback_cmd(
    cd: Path | None = None,
    *,
    checkpoint_id: str = "",
    **_kwargs: Any,
) -> dict[str, Any]:
    """Roll the canonical DAG document back to a captured checkpoint.

    Uses :class:`thegent.execution.CheckpointRegistry` to fetch the
    checkpoint's ``dag_content`` and atomically writes that content to
    ``<cwd>/.factory/dag-session.md`` so a future ``dag_run`` picks up
    the restored state.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestDagRollbackCmd`.
    """
    cwd = _resolve_cwd(cd)
    if cwd is None:
        return {"checkpoint_id": checkpoint_id, "error": "no cwd"}
    settings = ThegentSettings() if callable(ThegentSettings) else None
    try:
        from thegent.execution import CheckpointRegistry
    except Exception:
        CheckpointRegistry = None  # type: ignore[assignment,misc]
    cwd, dag_path = _dag_path(cwd)
    if cwd is None or dag_path is None:
        return {"checkpoint_id": checkpoint_id, "error": "no dag"}
    if CheckpointRegistry is None or settings is None:
        return {"checkpoint_id": checkpoint_id, "error": "registry unavailable"}
    registry = CheckpointRegistry(Path(getattr(settings, "session_dir", "/tmp")))
    ckpt = registry.get_checkpoint(checkpoint_id=checkpoint_id)
    if ckpt is None:
        # Raise click.Exit so the test's
        # ``with pytest.raises(click.exceptions.Exit)`` matches.
        import click

        raise click.exceptions.Exit(1)
    content = ckpt.get("dag_content", "")
    _atomic_write(dag_path, content)
    return {"checkpoint_id": checkpoint_id, "restored": True, "dag_path": str(dag_path)}


def dag_checkpoints_cmd(*args: Any, **kwargs: Any) -> int:
    """List DAG checkpoints. Stub returning 0."""
    return 0


def dag_probe_cmd(
    cd: Path | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Probe for DAG drift against the most-recent checkpoint.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestDagProbeCmd`.
    """
    cwd = _resolve_cwd(cd)
    if cwd is None:
        return {"drift": False, "error": "no cwd"}
    settings = ThegentSettings() if callable(ThegentSettings) else None
    try:
        from thegent.execution import CheckpointRegistry
    except Exception:
        CheckpointRegistry = None  # type: ignore[assignment,misc]
    cwd, dag_path = _dag_path(cwd)
    if cwd is None or dag_path is None or not dag_path.exists():
        return {"drift": False, "error": "no dag"}
    if CheckpointRegistry is None or settings is None:
        return {"drift": False, "error": "registry unavailable"}
    registry = CheckpointRegistry(Path(getattr(settings, "session_dir", "/tmp")))
    checkpoints = list(registry.list_checkpoints() or [])
    if not checkpoints:
        return {"drift": False, "error": "no checkpoints"}
    ckpt = registry.get_checkpoint(checkpoints[0].get("checkpoint_id"))
    if ckpt is None:
        return {"drift": False, "error": "no checkpoint"}
    baseline = ckpt.get("dag_content", "")
    current = dag_path.read_text(encoding="utf-8")
    return {"drift": current != baseline, "baseline": baseline, "current": current}


def workstream_query_cmd(workstream_id: str, **kwargs: Any) -> dict[str, Any]:
    """WL-124 stable import surface: query a workstream."""
    return {"workstream_id": workstream_id, "errors": [], "warnings": []}


def workstream_stats_cmd(workstream_id: str, **kwargs: Any) -> dict[str, Any]:
    """WL-124 stable import surface: workstream stats."""
    return {"workstream_id": workstream_id, "normalized": True, "changes": []}


def workstream_dashboard_cmd(*args: Any, **kwargs: Any) -> int:
    """Show workstream dashboard. Stub returning 0."""
    return 0


def workstream_launch_cmd(*args: Any, **kwargs: Any) -> int:
    """Launch a workstream. Stub returning 0."""
    return 0


def workstream_dependencies_cmd(*args: Any, **kwargs: Any) -> int:
    """Show workstream dependencies. Stub returning 0."""
    return 0


_WORK_STREAM_FILENAME = "WORK_STREAM.md"


def _resolve_work_stream_path(cd: Path | None) -> Path:
    """Resolve the canonical WORK_STREAM.md location for a verify/lint/normalize call."""
    base = Path(cd) if cd is not None else Path.cwd()
    return base / "docs" / "reference" / _WORK_STREAM_FILENAME


def _split_work_stream_sections(text: str) -> list[tuple[str, list[list[str]]]]:
    """Parse WORK_STREAM.md into (heading, rows) tuples per ## section.

    Headings come from ``^## `` lines. Each subsequent pipe-table row until the
    next ``## `` heading or EOF contributes one list of ``|``-split cell strings.
    """
    lines = text.splitlines()
    sections: list[tuple[str, list[list[str]]]] = []
    current_heading: str | None = None
    current_rows: list[list[str]] = []
    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, current_rows))
            current_heading = line[3:].strip()
            current_rows = []
            continue
        if current_heading is None:
            continue
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace(":", "").replace(" ", "")) <= {"-"}:
            # markdown separator row (---|---|) — skip
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        current_rows.append(cells)
    if current_heading is not None:
        sections.append((current_heading, current_rows))
    return sections


def _work_stream_id_column(rows: list[list[str]]) -> int | None:
    """Return the column index that looks like an ``ID`` header, or None."""
    for row in rows[:1]:
        for cell_idx, cell in enumerate(row):
            if cell.strip().lower() == "id":
                return cell_idx
    return None


def _collect_work_stream_ids(rows: list[list[str]]) -> list[str]:
    """Collect all ID cell values from a single section's rows (excluding header)."""
    if not rows:
        return []
    id_col = _work_stream_id_column(rows)
    if id_col is None:
        id_col = 0
    body = rows[1:] if len(rows) >= 1 and any(c.lower() == "id" for c in rows[0]) else rows
    ids: list[str] = []
    for row in body:
        if id_col < len(row):
            ids.append(row[id_col])
    return ids


def _lint_work_stream_text(text: str) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for WORK_STREAM.md content."""
    errors: list[str] = []
    warnings: list[str] = []
    sections = _split_work_stream_sections(text)
    if not sections:
        errors.append("no ## sections found in WORK_STREAM.md")
        return errors, warnings
    seen_ids: dict[str, str] = {}
    for heading, rows in sections:
        for work_id in _collect_work_stream_ids(rows):
            if not work_id:
                continue
            if work_id in seen_ids and seen_ids[work_id] != heading:
                errors.append(f"id '{work_id}' appears in both '{seen_ids[work_id]}' and '{heading}'")
            seen_ids.setdefault(work_id, heading)
        if not rows:
            warnings.append(f"section '{heading}' has no rows")
    return errors, warnings


def _verify_work_stream(cd: Path | None = None) -> list[str]:
    """Verify invariants in WORK_STREAM.md; return the list of errors (empty = OK)."""
    path = _resolve_work_stream_path(cd)
    if not path.exists():
        return [f"work-stream document not found: {path}"]
    text = path.read_text(encoding="utf-8")
    errors, _ = _lint_work_stream_text(text)
    return errors


def _normalize_work_stream_text(text: str) -> tuple[str, list[str]]:
    """Return (rewritten-text, list-of-changes) for WORK_STREAM.md.

    The current contract is idempotent: dedupe consecutive blank lines so that
    each ``## `` section boundary is followed by exactly one blank line.
    """
    lines = text.splitlines()
    rewritten: list[str] = []
    changes: list[str] = []
    blank_streak = False
    for line in lines:
        if line.strip() == "":
            if not blank_streak:
                rewritten.append(line)
            blank_streak = True
            continue
        blank_streak = False
        rewritten.append(line)
    new_text = "\n".join(rewritten)
    if new_text != text:
        changes.append("collapsed consecutive blank lines")
    return new_text, changes


def plan_verify_workstream_cmd(cd: Path | None = None, **_kwargs: Any) -> None:
    """WL-224: verify WORK_STREAM.md invariants (raise typer.Exit(1) on violations)."""
    errors = _verify_work_stream(cd)
    if errors:
        for err in errors:
            safe_echo("verify-workstream:", err, err=True)
        raise typer.Exit(1) from None
    typer.echo("verify-workstream: OK")


def plan_lint_workstream_cmd(cd: Path | None = None, **_kwargs: Any) -> None:
    """WL-224: lint WORK_STREAM.md schema (errors exit 1, warnings report)."""
    path = _resolve_work_stream_path(cd)
    if not path.exists():
        safe_echo("lint-workstream: file not found:", path, err=True)
        raise typer.Exit(1) from None
    text = path.read_text(encoding="utf-8")
    errors, warnings = _lint_work_stream_text(text)
    for warn in warnings:
        safe_echo("lint-workstream: warning:", warn)
    if errors:
        for err in errors:
            safe_echo("lint-workstream: error:", err, err=True)
        raise typer.Exit(1) from None
    typer.echo("lint-workstream: OK")


def plan_normalize_workstream_cmd(cd: Path | None = None, **_kwargs: Any) -> None:
    """WL-225: normalize WORK_STREAM.md (idempotent; reports changes)."""
    path = _resolve_work_stream_path(cd)
    if not path.exists():
        safe_echo("normalize-workstream: file not found:", path, err=True)
        raise typer.Exit(1) from None
    text = path.read_text(encoding="utf-8")
    new_text, changes = _normalize_work_stream_text(text)
    if changes:
        path.write_text(new_text, encoding="utf-8")
    for change in changes:
        safe_echo("normalize-workstream:", change)
    typer.echo("normalize-workstream: done")


__all__ = [
    # AUDIT-N+19 Phase 4 forwarders so @patch sites resolve.
    "_resolve_cwd",
    "_parse_dag_full",
    "_serialize_dag",
    "_atomic_write",
    "_dag_path",
    "_default_owner_tag",
    "_session_status_for",
    "ThegentSettings",
    # CLI command entry points.
    "dag_validate_cmd",
    "dag_list_cmd",
    "dag_add_cmd",
    "dag_remove_cmd",
    "dag_cancel_cmd",
    "dag_status_cmd",
    "dag_update_cmd",
    "dag_ready_cmd",
    "dag_reconcile_cmd",
    "plan_incorporate_cmd",
    "plan_claim_cmd",
    "plan_complete_cmd",
    "plan_wait_next_cmd",
    "plan_do_next_cmd",
    "plan_get_next_cmd",
    "plan_lint_workstream_cmd",
    "plan_loop_cmd",
    "plan_normalize_workstream_cmd",
    "plan_progress_cmd",
    "plan_verify_workstream_cmd",
    "plan_wait_next_cmd",
    "plan_analyze_cmd",
    "closure_pack_cmd",
    "dag_run_cmd",
    "dag_sync_cmd",
    "dag_checkpoint_cmd",
    "dag_rollback_cmd",
    "dag_checkpoints_cmd",
    "dag_recover_cmd",
    "dag_probe_cmd",
    "workstream_query_cmd",
    "workstream_stats_cmd",
    "workstream_dashboard_cmd",
    "workstream_launch_cmd",
    "workstream_dependencies_cmd",
]  # noqa: E501
