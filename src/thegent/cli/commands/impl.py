"""CLI implementation helpers.

This module provides the core CLI implementation functions extracted from
the main CLI module.
"""

from __future__ import annotations

import errno
import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

from thegent.config import ThegentSettings

if TYPE_CHECKING:
    from thegent.contracts.telemetry import ContractTelemetry


def _impl_globals() -> dict[str, Any]:
    """Return the live ``impl`` module's ``__dict__``.

    AUDIT-N+16 (WL-125 closure): wrapper functions that forward resolver
    callbacks (e.g. ``log_path_resolver=impl._health_snapshot_log_path``)
    must look the callback up on the **current** module globals each call,
    not on the closure cell created at definition time. Otherwise
    ``monkeypatch.setattr("thegent.cli.commands.impl.<callback>", ...)``
    patches in ``tests/test_wl125_*_parity.py`` would not be observed.
    """
    return sys.modules[__name__].__dict__


# EAGAIN/EWOULDBLOCK errno numbers for retry logic
_EAGAIN_ERRNOS = {errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR}

# Health payload schema version
HEALTH_PAYLOAD_SCHEMA_VERSION = "3.0"


# Retry if eagain decorator
def _retry_if_eagain(func: Any) -> Any:
    """Retry function if EAGAIN error occurs."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OSError as e:
                if e.errno in _EAGAIN_ERRNOS and attempt < max_retries - 1:
                    time.sleep(0.1 * (2**attempt))
                    continue
                raise
        return None

    return wrapper


# Backoff delay function
def _backoff_delay(attempt: int, base: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay."""
    return min(base * (2**attempt), max_delay)


# Atomic write function
def _atomic_write(path: Path, content: str, *, backup: bool = False) -> None:
    """AUDIT-N+19: delegate to :func:`dag_impl._atomic_write`.

    The canonical atomic-write helper lives in :mod:`dag_impl` and
    supports an optional ``backup=True`` kwarg that copies the existing
    file to ``<path>.bak`` before swapping in the new content.
    """
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._atomic_write(path, content, backup=backup)


# Spawn with eagain retry
def _spawn_with_eagain_retry(cmd: list[str], **kwargs: Any) -> Any:
    """Spawn process with EAGAIN retry logic."""
    import subprocess

    max_retries = 3
    for attempt in range(max_retries):
        try:
            return subprocess.run(cmd, **kwargs)
        except OSError as e:
            if e.errno in _EAGAIN_ERRNOS and attempt < max_retries - 1:
                time.sleep(0.1 * (2**attempt))
                continue
            raise
    return None


# AUDIT-N+14: ``_resolve_cwd`` lives in :mod:`thegent.cli.commands.session_impl`
# (canonical home). The local stub is removed so the AUDIT-N+12 re-export
# binds the canonical 4-arg form (with caching + project-indicator scan).
# Legacy callers must import from ``thegent.cli.commands.session_impl``
# directly or via ``thegent.cli.commands.impl._resolve_cwd`` (re-export).

# AUDIT-N+14: ``_resolve_droids_dir`` lives here (impl.py is the canonical
# home — it is not a session-lifecycle helper).


def _resolve_droids_dir(cwd: Path | None, settings: ThegentSettings) -> Path:
    """Resolve the droids directory.

    Args:
        cwd: The working directory.
        settings: Thegent settings.

    Returns:
        Path to the droids directory.
    """
    if cwd is not None:
        factory_droids = cwd / ".factory" / "droids"
        if factory_droids.exists():
            return factory_droids.resolve()

    return settings.factory_droids_dir.expanduser().resolve()


# AUDIT-N+14: ``_compose_owner_tag`` and ``_default_owner_tag`` live in
# :mod:`thegent.cli.commands.session_impl` (canonical home). The local stubs
# are removed so the AUDIT-N+12 re-export binds the canonical 4-arg form
# (with ``{pid}`` / ``{cwd}`` placeholder expansion + ``THGENT_OWNER_TAG``
# env override).

# AUDIT-N+14: ``_write_session_state`` and ``_normalize_image_paths`` stay
# here (impl.py is the canonical home — they are not session-lifecycle
# helpers).


def _write_session_state(session_dir: Path, state: dict[str, Any]) -> None:
    """Write session state to disk."""
    import json

    state_file = session_dir / "session_state.json"
    state_file.write_text(json.dumps(state))


def _normalize_image_paths(paths: list[str]) -> list[str]:
    """Normalize image paths."""
    from pathlib import Path

    return [str(Path(p).expanduser().resolve()) for p in paths]


class DagPrioritizer:
    """Prioritizer for DAG nodes.

    Thin placeholder — canonical prioritization lives in
    :mod:`thegent.cli.commands.dag_impl`. Retained here only so legacy
    callers that import :class:`DagPrioritizer` from ``impl`` keep
    working during the AUDIT-N+19 Phase 4 migration.
    """

    def __init__(self) -> None:
        self.priorities: dict[str, int] = {}

    def prioritize(self, nodes: list[str]) -> list[str]:
        """Prioritize DAG nodes by their priority values."""
        return sorted(nodes, key=lambda n: self.priorities.get(n, 999))


# AUDIT-N+19: ``DagDocument`` lives in :mod:`thegent.cli.commands.dag_impl`
# (canonical dataclass home). Re-export here so legacy callers (and the
# AUDIT-N+11 identity contract) continue to bind to the canonical type.
from thegent.cli.commands.dag_impl import (
    DagDocument as DagDocument,  # noqa: F401,E402,PLC0414
)


def run_impl(
    prompt: str,
    audio_files: list[str] | None = None,
    google_grounding: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the implementation.

    Thin delegate to
    :func:`thegent.cli.commands.run.impl_core_runners.run_impl_core`,
    which is the AUDIT-N+16 canonical home for the dispatch shim (it
    threads ``impl_ns`` and forwards every caller kwarg verbatim to
    :func:`thegent.cli.services.run_execution_core_helpers.run_impl_core`).
    The full execution pipeline (Pareto routing, policy, escalation,
    MAIF, observability) lives in the extracted core; this wrapper
    exists to keep the public CLI surface stable.

    AUDIT-N+28: ``audio_files`` + ``google_grounding`` are explicit kwargs
    (pinned by ``tests/test_wl116_audio_inputs.py::test_run_impl_accepts_audio_files_and_google_grounding``)
    so callers see them in ``inspect.signature(run_impl)`` without having
    to grep through ``**kwargs``. Both are forwarded to the canonical
    helper verbatim alongside every other caller kwarg.
    """
    from thegent.cli.commands.run.impl_core_runners import run_impl_core

    return run_impl_core(
        prompt=prompt,
        audio_files=audio_files,
        google_grounding=google_grounding,
        **kwargs,
    )


def list_models_impl(**kwargs: Any) -> dict[str, Any]:
    """Implementation for list models command."""
    return {"models": []}


def list_impl(**kwargs: Any) -> dict[str, Any]:
    """Implementation for list command.

    Args:
        **kwargs: Additional keyword arguments.

    Returns:
        List result dictionary.
    """
    return {"items": [], "count": 0}


def session_list_impl(session_ids: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Implementation for session list command.

    Args:
        session_ids: Optional list of session IDs to filter.
        **kwargs: Additional keyword arguments.

    Returns:
        Session list result dictionary.
    """
    return {"sessions": [], "count": 0, "session_ids": session_ids or []}


def bg_impl(prompt: str, **kwargs: Any) -> dict[str, Any]:
    """Background-run implementation.

    Thin delegate to
    :func:`thegent.cli.commands.run.impl_core_runners.bg_impl_core`,
    mirroring :func:`run_impl`'s delegation contract. The canonical home
    for the dispatch shim threads ``impl_ns`` and forwards every caller
    kwarg verbatim to
    :func:`thegent.cli.services.run_execution_core_helpers.bg_impl_core`.
    """
    from thegent.cli.commands.run.impl_core_runners import bg_impl_core

    return bg_impl_core(prompt=prompt, **kwargs)


# ---------------------------------------------------------------------------
# AUDIT-N+14: real session-lifecycle entry-point implementations
# Pinned by tests/test_unit_cli_impl_session.py (FR-CLI-100..150).
# Each function uses ``impl.<x>`` references for the canonical imports
# above so ``@patch("thegent.cli.commands.impl.<x>", ...)`` decorators
# continue to work.
# ---------------------------------------------------------------------------


def status_impl(session_id: str, include_contract: bool = False, **kwargs: Any) -> dict[str, Any]:
    """Return the canonical status payload for a session.

    Resolves the session-meta file via :func:`_find_session_meta`, reads
    it, computes ``running`` via :func:`_is_pid_running`, and composes
    the canonical status string via :func:`_resolve_session_status`.
    Returns ``{"error": ...}`` if the session is not found.

    Pinned by ``TestStatusImpl`` in tests/test_unit_cli_impl_session.py.
    """
    settings = ThegentSettings()
    try:
        meta_path = _find_session_meta(settings, session_id)
    except typer.BadParameter as exc:
        return {"error": str(exc), "session_id": session_id}
    meta = _read_session_meta(meta_path)
    pid = int(meta.get("pid") or 0)
    running = _is_pid_running(pid)
    paths = _session_paths(Path(settings.session_dir), session_id)
    status = _resolve_session_status(meta, paths["rc"], running=running)
    exit_code = meta.get("exit_code")
    if exit_code is None and paths["rc"].exists():
        try:
            exit_code = int(paths["rc"].read_text(encoding="utf-8").strip())
        except ValueError:
            exit_code = None
    result: dict[str, Any] = {
        "session_id": session_id,
        "status": status,
        "running": running,
        "exit_code": exit_code,
        "pid": pid,
        "owner": meta.get("owner"),
        "agent": meta.get("agent"),
    }
    if include_contract:
        if "route_contract" in meta:
            result["route_contract"] = meta["route_contract"]
        if "route_request" in meta:
            result["route_request"] = meta["route_request"]
    return result


def stop_impl(
    session_id: str,
    force: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Stop a running session by signaling its PID.

    Sends ``SIGTERM`` (graceful) or ``SIGKILL`` (``force=True``) to the
    session PID via :func:`os.killpg`. Returns ``{"status": "stopped"}``
    / ``{"status": "stopped_force"}`` on success, ``{"status": "error", ...}``
    on OS errors, or ``{"status": "not_running"}`` if the session is
    already stopped.

    Pinned by ``TestStopImpl`` in tests/test_unit_cli_impl_session.py.
    """
    import os as _os
    import signal as _signal

    settings = ThegentSettings()
    try:
        meta_path = _find_session_meta(settings, session_id)
    except typer.BadParameter as exc:
        return {"error": str(exc), "session_id": session_id}
    meta = _read_session_meta(meta_path)
    pid = int(meta.get("pid") or 0)
    if not _is_pid_running(pid):
        return {"status": "not_running", "session_id": session_id}
    sig = _signal.SIGKILL if force else _signal.SIGTERM
    try:
        _os.killpg(pid, sig)
    except OSError as exc:
        return {"status": "error", "error": str(exc), "session_id": session_id}
    return {
        "status": "stopped_force" if force else "stopped",
        "session_id": session_id,
    }


def wait_impl(
    session_id: str,
    timeout: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Wait for a session to finish, optionally bounded by ``timeout``.

    Returns ``{"exit_code": int, "timed_out": bool}`` on success or
    ``{"error": ...}`` if the session is not found.

    Pinned by ``TestWaitImpl`` in tests/test_unit_cli_impl_session.py.
    """
    settings = ThegentSettings()
    try:
        meta_path = _find_session_meta(settings, session_id)
    except typer.BadParameter as exc:
        return {"error": str(exc), "session_id": session_id}
    meta = _read_session_meta(meta_path)
    pid = int(meta.get("pid") or 0)
    paths = _session_paths(Path(settings.session_dir), session_id)
    timed_out = False
    if _is_pid_running(pid):
        deadline = (time.time() + timeout) if timeout else None
        while _is_pid_running(pid):
            if deadline is not None and time.time() >= deadline:
                timed_out = True
                break
            time.sleep(0.1)
    exit_code = meta.get("exit_code")
    if exit_code is None and paths["rc"].exists():
        try:
            exit_code = int(paths["rc"].read_text(encoding="utf-8").strip())
        except ValueError:
            exit_code = None
    return {
        "session_id": session_id,
        "exit_code": exit_code,
        "timed_out": timed_out,
    }


def logs_impl(
    session_id: str,
    stderr: bool = False,
    tail: int | None = None,
    **kwargs: Any,
) -> str:
    """Return the canonical logs payload for a session as a string.

    Returns stdout by default, stderr when ``stderr=True``, and the
    last ``tail`` lines when ``tail`` is set. The test contract pins
    the return type as ``str`` (with error prefixes inlined).

    Pinned by ``TestLogsImpl`` in tests/test_unit_cli_impl_session.py.
    """
    settings = ThegentSettings()
    try:
        meta_path = _find_session_meta(settings, session_id)
    except typer.BadParameter as exc:
        return f"Error: {exc}"
    if not meta_path.exists():
        return f"Error: session meta not found: {session_id}"
    paths = _session_paths(Path(settings.session_dir), session_id)
    log_path = paths["stderr"] if stderr else paths["stdout"]
    if not log_path.exists():
        return f"Log file missing: {log_path.name}"
    content = log_path.read_text(encoding="utf-8")
    if tail is not None:
        lines = content.splitlines()
        content = "\n".join(lines[-tail:])
    return content


def session_meta_impl(session_id: str, **kwargs: Any) -> dict[str, Any]:
    """Return the canonical session-meta payload.

    Pinned by ``TestSessionMetaImpl`` in tests/test_unit_cli_impl_session.py.
    """
    settings = ThegentSettings()
    try:
        meta_path = _find_session_meta(settings, session_id)
    except typer.BadParameter as exc:
        return {"error": str(exc), "session_id": session_id}
    if not meta_path.exists():
        return {
            "error": f"session meta not found: {session_id}",
            "session_id": session_id,
        }
    meta = _read_session_meta(meta_path)
    return {
        "session_id": session_id,
        "agent": meta.get("agent"),
        "owner": meta.get("owner"),
        "started_at_utc": meta.get("started_at_utc"),
        "metadata": meta,
    }


# ---------------------------------------------------------------------------
# WL-125 helper-attribute stubs (monkeypatch sites for run_post_surface_helpers,
# run_session_helpers, and pre_work_gate_helpers). The canonical owners of
# these symbols live in their respective service helpers; impl merely exposes
# them so monkeypatch.setattr("thegent.cli.commands.impl.<name>", ...) resolves.
# ---------------------------------------------------------------------------


def _resolve_latest_session_id(settings: Any) -> str:
    """Resolve the most recent session id under ``settings.session_dir``.

    The canonical implementation lives in ``thegent.cli.services.run_session_helpers``.
    This thin delegation ensures the WL-125 patch site
    ``monkeypatch.setattr("thegent.cli.commands.impl.run_session_helpers.<x>", ...)``
    is observed by callers that invoke ``impl._resolve_latest_session_id``.
    """

    return run_session_helpers.resolve_latest_session_id(settings=settings)


def _normalize_contract_string(value: Any) -> str | None:
    """Normalize a state-contract field to a stripped string or ``None``.

    Delegates to ``thegent.cli.services.run_session_helpers`` so the WL-125
    patch sites can replace the canonical implementation at test time.
    """

    return run_session_helpers.normalize_contract_string(value)


def session_send_impl(session_id: str, message: str, msg_type: str = "reprompt") -> tuple[bool, str]:
    """Default ``session_send_impl`` dispatcher used by ``resume_impl``.

    The canonical implementation lives in
    ``thegent.cli.services.run_session_helpers``; this stub exists so the
    WL-125 patch site
    ``monkeypatch.setattr("thegent.cli.commands.impl.session_send_impl", ...)``
    resolves cleanly when no override is supplied.
    """

    return run_session_helpers.session_send_impl(
        session_id=session_id,
        message=message,
        msg_type=msg_type,
    )


def list_agents_impl() -> list[dict[str, str]]:
    """List agent backends exposed via the MCP ``agents`` resource.

    Thin delegate to :func:`run_post_surface_helpers.list_agents_impl`
    so WL-125 monkeypatch sites that target ``impl.list_agents_impl``
    (e.g. ``tests/test_unit_mcp.py``) resolve cleanly.
    """
    return run_post_surface_helpers.list_agents_impl()


def events_impl(
    run_id: str | None = None,
    limit: int = 100,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Return run-registry events filtered by ``run_id`` and capped by ``limit``.

    The canonical registry file lives at ``<session_dir>/run_registry.jsonl``
    and contains one JSON object per line.

    Pinned by ``TestEventsImpl`` in tests/test_unit_cli_impl_session.py.
    """
    import orjson as _json

    settings = ThegentSettings()
    registry_path = Path(settings.session_dir) / "run_registry.jsonl"
    if not registry_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for raw in registry_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            obj = _json.loads(raw)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        events.append(obj)
    if run_id is not None:
        events = [e for e in events if e.get("run_id") == run_id]
    if limit is not None and limit > 0:
        events = events[-limit:]
    return events


def history_impl(limit: int = 50, **kwargs: Any) -> list[dict[str, Any]]:
    """Return the most-recent runs from the run registry.

    Pinned by ``TestHistoryImpl`` in tests/test_unit_cli_impl_session.py.
    """
    settings = ThegentSettings()
    registry = RunRegistry(settings.session_dir)
    if hasattr(registry, "list_runs"):
        runs = registry.list_runs(limit=limit)
        return list(runs or [])
    # Fallback: read the canonical registry file when list_runs is unavailable.
    return events_impl(run_id=None, limit=limit)


def ps_impl(
    all: bool = False,  # noqa: A002 — test surface
    owner: str | None = None,
    include_contract: bool = False,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """List session-process rows.

    When ``all=True`` scans every scope dir under ``session_dir``;
    otherwise filters to the current owner (or ``owner=``).

    Pinned by ``TestPsImpl`` in tests/test_unit_cli_impl_session.py.
    """
    settings = ThegentSettings()
    session_root = Path(settings.session_dir)
    if all:
        owner_filter: str | None = None
        scope_dirs: list[Path] = sorted(p for p in session_root.iterdir() if p.is_dir())
    else:
        owner_filter = owner or _default_owner_tag(Path.cwd())
        scope_dirs = _session_scope_dirs(session_root, owner_filter)
    rows: list[dict[str, Any]] = []
    for scope_dir in scope_dirs:
        for meta_path in sorted(scope_dir.glob("*.json")):
            try:
                meta = _read_session_meta(meta_path)
            except Exception:
                continue
            sid = meta.get("session_id") or meta_path.stem
            pid = int(meta.get("pid") or 0)
            running = bool(_is_pid_running(pid))
            if owner_filter is not None and meta.get("owner") != owner_filter:
                continue
            prompt = str(meta.get("prompt") or "")
            prompt_preview = prompt if len(prompt) <= 40 else prompt[:40] + "..."
            row: dict[str, Any] = {
                "id": sid,
                "session_id": sid,
                "owner": meta.get("owner"),
                "agent": meta.get("agent"),
                "pid": pid,
                "running": running,
                "started_at_utc": meta.get("started_at_utc"),
                "status": _resolve_session_status(meta, scope_dir / f"{sid}.rc", running=running),
                "prompt_preview": prompt_preview,
            }
            if include_contract and "route_contract" in meta:
                row["route_contract"] = meta["route_contract"]
            rows.append(row)
    return rows


def inspect_impl(
    session_ids: list[str],
    owner: str | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Return a list of inspect payloads for one or more sessions.

    When ``session_ids`` is empty, scans all sessions owned by
    ``owner`` (or the default owner tag if ``owner`` is ``None``).

    Pinned by ``TestInspectImpl`` in tests/test_unit_cli_impl_session.py.
    """
    if not session_ids and owner is None:
        return []
    settings = ThegentSettings()
    results: list[dict[str, Any]] = []
    if not session_ids:
        # Owner-discovery path: scan every scope dir for the owner prefix.
        owner_tag = owner or _default_owner_tag(Path.cwd())
        scope_dirs = _session_scope_dirs(Path(settings.session_dir), owner_tag)
        for scope_dir in scope_dirs:
            for meta_path in sorted(scope_dir.glob("*.json")):
                sid = meta_path.stem
                results.extend(_inspect_one(settings, sid))
        return results
    for sid in session_ids:
        results.extend(_inspect_one(settings, sid))
    return results


def _inspect_one(settings: ThegentSettings, session_id: str) -> list[dict[str, Any]]:
    """Helper: build the inspect payload for a single session."""
    try:
        meta_path = _find_session_meta(settings, session_id)
    except typer.BadParameter:
        return []
    if not meta_path.exists():
        return []
    meta = _read_session_meta(meta_path)
    paths = _session_paths(Path(settings.session_dir), session_id)
    stdout_text = ""
    if paths["stdout"].exists():
        stdout_text = paths["stdout"].read_text(encoding="utf-8")
    return [
        {
            "session_id": session_id,
            "owner": meta.get("owner"),
            "agent": meta.get("agent"),
            "logs": stdout_text,
            "pid": meta.get("pid"),
        }
    ]


# NOTE: ``history_impl`` and ``events_impl`` are defined earlier in this
# module (canonical single home — AUDIT-N+14 removed the duplicate
# definitions that previously shadowed the canonical pair).

__all__ = [
    # AUDIT-N+9: observability surface (canonical home: observability_impl)
    "_inject_time_constraint",
    "_append_observe_summary_snapshot",
    "_validate_image_capability",
    "_resolve_audio_transcript_for_output",
    "_resolve_grounding_sources_for_output",
    "_append_health_snapshot",
    "observe_summary_impl",
    # AUDIT-N+13: dormant-core trend payload wire-up.
    "_build_observe_trend_block",
    "_build_observe_trend_payload",
    # AUDIT-N+12: session lifecycle surface (canonical home: session_impl)
    "_is_pid_running",
    "_scope_key",
    "_session_paths",
    "_new_session_id",
    "_save_session_meta",
    "_read_session_meta",
    "_find_session_meta",
    "_resolve_session_status",
    "_resolve_agent_model",
    "_load_prior_session_output",
    "_CONTINUATION_TAIL_CHARS",
    "_CWD_CACHE",
    "_session_dir",
    "_session_scope_dirs",
    "_build_continuation_prompt",
    # AUDIT-N+12: I/O helpers (canonical home: impl.py)
    "_resolve_cwd",
    "_resolve_droids_dir",
    "_compose_owner_tag",
    "_default_owner_tag",
    "_backoff_delay",
    "_retry_if_eagain",
    "_atomic_write",
    "_spawn_with_eagain_retry",
    "_EAGAIN_ERRNOS",
    "_write_session_state",
    "_normalize_image_paths",
    # Public entry points (canonical home: impl.py)
    "run_impl",
    "logs_impl",
    "ps_impl",
    "list_models_impl",
    "status_impl",
    "resume_impl",
    "list_impl",
    "session_list_impl",
    "bg_impl",
    # AUDIT-N+18 / WL-125: orchestration wrappers (canonical home:
    # thegent.cli.services.work_stream_orchestration).
    "do_next_impl",
    "wait_next_impl",
    "spawn_next_impl",
    "work_stream_claim_impl",
    "work_stream_complete_impl",
    "incorporate_impl",
    "continuity_snapshot_impl",
    # DAG model classes (canonical home: impl.py)
    "DagDocument",
    "DagPrioritizer",
]


# AUDIT-N+9: re-export observability surface for backward compat with
# external callers that still import from thegent.cli.commands.impl
from thegent.cli.commands.observability_impl import (  # noqa: F401
    _append_health_snapshot,
    _append_observe_summary_snapshot,
    _build_audio_summary_metadata,
    _build_observe_summary_trend_scope,
    _build_observe_trend_block,
    _build_observe_trend_payload,
    _build_run_event_details,
    _classify_observe_summary_trend_health,
    _compact_health_snapshot_log,
    _hash_health_payload,
    _hash_observe_summary_payload,
    _hash_observe_summary_trend_scope,
    _health_scope_key,
    _inject_time_constraint,
    _load_observe_summary_snapshots,
    _load_previous_health_snapshot,
    _observe_summary_freshness_bucket,
    _parse_observe_summary_env_float,
    _parse_observe_summary_env_int,
    _parse_observe_summary_timestamp,
    _resolve_audio_transcript_for_output,
    _resolve_grounding_sources_for_output,
    _resolve_health_policy,
    _run_background_session_observer,
    _validate_image_capability,
    observe_summary_impl,
)

# AUDIT-N+27: no WL-120 shadow wrappers for the AUDIT-N+9 moved helpers
# (``_resolve_audio_transcript_for_output`` /
# ``_resolve_grounding_sources_for_output`` /
# ``_build_audio_summary_metadata`` / ``_build_run_event_details``).
# Each is a single canonical implementation in
# :mod:`thegent.cli.commands.observability_impl` (which dispatches to the
# service modules) so the WL-125 monkeypatch sites
# (``impl.run_event_helpers.<name>``, ``impl.run_audio_helpers.<name>``,
# ``impl.run_input_helpers.<name>``) are observed via the shared module
# identity between ``impl`` and ``observability_impl`` for the imported
# service modules. The re-export block above is the AUDIT-N+9 identity
# contract — ``impl.<name> is observability_impl.<name>`` for every
# member of :data:`tests.test_unit_audit_n9_observability_impl_extraction_parity.MOVED_HELPERS`.


def _resolve_agent_model(
    agent: str,
    model: str | None = None,
    mode: str = "full",
    settings: Any = None,
) -> str:
    """WL-125 thin delegate to :func:`run_session_helpers.resolve_agent_model`.

    Routes through ``run_session_helpers`` (not ``run_model_helpers``)
    so that monkeypatch sites targeting
    ``impl.run_session_helpers.resolve_agent_model`` are observed.
    """
    from thegent.cli.services import run_session_helpers as _rsh

    return _rsh.resolve_agent_model(
        agent=agent,
        model=model,
        mode=mode,
        settings=settings,
    )


# AUDIT-N+12: re-export the session-lifecycle surface from
# :mod:`thegent.cli.commands.session_impl`. These helpers previously
# lived inline in ``impl.py`` but were never reachable because the
# surface was incomplete (missing ``_CONTINUATION_TAIL_CHARS``,
# ``_CWD_CACHE``, ``_load_prior_session_output``,
# ``_resolve_agent_model`` 4-arg form, etc.). Extracting them into a
# canonical module preserves the ``impl.<x>`` import path for legacy
# callers and ``tests/test_unit_cli_impl_session.py`` patch sites.
# AUDIT-N+16 (WL-125 closure): wrapped in try/except so partially-stubbed
# ``session_impl`` modules (used by ``tests/test_wl125_*_parity.py`` to
# isolate ``impl.py`` import surface) don't fail. Falls back to
# module-level sentinel attributes that callers can ``monkeypatch``.
_SESSION_IMPL_REEXPORTS = (
    "_CONTINUATION_TAIL_CHARS",
    "_CWD_CACHE",
    "_is_pid_running",
    "_scope_key",
    "_session_paths",
    "_new_session_id",
    "_save_session_meta",
    "_read_session_meta",
    "_find_session_meta",
    "_resolve_session_status",
    "_resolve_cwd",
    "_compose_owner_tag",
    "_default_owner_tag",
    "_load_prior_session_output",
    "_build_continuation_prompt",
    "_session_dir",
    "_session_scope_dirs",
    "_run_background_session_observer",
    # WL-125: _resolve_agent_model intentionally excluded — the
    # canonical definition at line ~783 delegates through
    # run_session_helpers so monkeypatch sites targeting
    # impl.run_session_helpers.resolve_agent_model are observed.
)
try:
    from thegent.cli.commands import session_impl as _session_impl  # noqa: F401

    _sym: str  # noqa: F842 - always bound below
    for _sym in _SESSION_IMPL_REEXPORTS:
        try:
            globals()[_sym] = getattr(_session_impl, _sym)
        except AttributeError:  # pragma: no cover - defensive
            globals()[_sym] = None
except ImportError:  # pragma: no cover - defensive
    for _sym in _SESSION_IMPL_REEXPORTS:
        globals().setdefault(_sym, None)
del _SESSION_IMPL_REEXPORTS
# AUDIT-N+12: surface ``thegent.cli.services.run_observe_helpers`` as a
# module attribute on ``impl`` so legacy ``monkeypatch.setattr`` sites
# like ``monkeypatch.setattr("thegent.cli.commands.impl.run_observe_helpers.<x>", ...)``
# (in ``tests/test_wl125_run_observe_helpers_parity.py``) resolve.
# AUDIT-N+12: surface ``thegent.cli.services.observability`` as a module
# attribute on ``impl`` so the WL-120 reconciliation tests can monkeypatch
# the dormant trend/escalation builders via
# ``monkeypatch.setattr("thegent.cli.commands.impl.services_observability.<x>", ...)``.
from thegent.cli.services import observability as services_observability  # noqa: F401

# AUDIT-N+16 (WL-125 closure): surface ``thegent.cli.services.prompt_constraint_helpers``
# as a module attribute on ``impl`` so legacy ``monkeypatch.setattr`` sites like
# ``monkeypatch.setattr("thegent.cli.commands.impl.prompt_constraint_helpers.<x>", ...)``
# (in ``tests/test_wl125_prompt_constraint_helpers_parity.py``) resolve.
# AUDIT-N+16 (WL-125 closure): surface canonical ``thegent.cli.services`` helper
# modules as attributes on ``impl`` so legacy ``monkeypatch.setattr`` sites
# like ``monkeypatch.setattr("thegent.cli.commands.impl.<svc_module>.<x>", ...)``
# (in ``tests/test_wl125_*_parity.py``) resolve. These are thin re-exports:
# canonical implementations live in the respective ``services`` submodules.
from thegent.cli.services import (
    pre_work_gate_helpers,  # noqa: F401
    process_helpers,  # noqa: F401
    prompt_constraint_helpers,  # noqa: F401
    retry_helpers,  # noqa: F401
    run_audio_helpers,  # noqa: F401
    run_dag_helpers,  # noqa: F401
    run_event_helpers,  # noqa: F401
    run_health_helpers,  # noqa: F401
    run_input_helpers,  # noqa: F401
    run_model_helpers,  # noqa: F401
    run_observe_helpers,  # noqa: F401
    run_post_surface_helpers,  # noqa: F401
    run_session_helpers,  # noqa: F401
    run_workstream_helpers,  # noqa: F401
    session_id_helpers,  # noqa: F401
    session_path_helpers,  # noqa: F401
    spawn_retry_helpers,  # noqa: F401
)

# AUDIT-N+16 (WL-125 closure): re-export the ``SECONDS_PER_TOOL_CALL`` constant
# from the canonical home so external callers (and
# ``tests/test_wl125_prompt_constraint_helpers_parity.py``) can read it via
# ``thegent.cli.commands.impl.SECONDS_PER_TOOL_CALL``. NOTE: We deliberately do
# NOT re-define ``_inject_time_constraint`` here — the canonical version is
# re-exported from ``observability_impl`` above (AUDIT-N+9 identity contract)
# and now delegates to ``prompt_constraint_helpers.inject_time_constraint`` at
# runtime (AUDIT-N+16). This satisfies the WL-125 patch site contract:
# ``monkeypatch.setattr("thegent.cli.commands.impl.prompt_constraint_helpers.inject_time_constraint", ...)``
# is observed by the next ``impl._inject_time_constraint(...)`` call.
try:
    from thegent.cli.services.prompt_constraint_helpers import (  # noqa: F401
        SECONDS_PER_TOOL_CALL,
    )
except ImportError:  # pragma: no cover - defensive
    SECONDS_PER_TOOL_CALL = 2.3  # type: ignore[assignment, has-type]


# ---------------------------------------------------------------------------
# AUDIT-N+14: re-export the canonical imports so the test mocks at
# ``thegent.cli.commands.impl.<x>`` resolve. Each test patches names like
# ``thegent.cli.commands.impl.resolve_agent`` / ``impl.subprocess`` /
# ``impl.ThegentSettings`` / ``impl.MigrationController`` / etc.; without
# these re-exports the ``@patch(...)`` decorators raise
# ``AttributeError: module ... does not have the attribute '...'``.
# ---------------------------------------------------------------------------
import subprocess as _subprocess  # noqa: F401

from thegent.agents import get_fallback_agents, get_runner, resolve_agent  # noqa: F401
from thegent.agents.base import AgentRunner, RunResult  # noqa: F401
from thegent.agents.resilience import is_usage_limit  # noqa: F401
from thegent.cli.commands._cli_shared import RunRegistry  # noqa: F401
from thegent.contracts.telemetry import (  # noqa: F401
    ContractTelemetry,
    rank_providers_by_parser_quality,
)
from thegent.execution import (  # noqa: F401
    AgentSource,
    Auditor,
    CircuitBreakerRegistry,
    ConcurrencyController,
    FreshnessValidator,
    InteractivityMode,
    InterruptionTracker,
    LoadClassifier,
    OverrideRegistry,
    PolicyEngine,
    RunMeta,
    TrustBoundaryValidator,
)
from thegent.output_parser import extract_condensed  # noqa: F401

# Aliases that the test patch sites reference.
subprocess = _subprocess
ThegentSettingsCls = ThegentSettings


# ---------------------------------------------------------------------------
# AUDIT-N+14: real entry-point implementations
# ---------------------------------------------------------------------------
# AUDIT-N+10: re-export governance / escalation / HITL / data-protection
# surface for backward compat with external callers (and the legacy
# ``tests/test_unit_cli_*.py`` patch sites) that still import from
# ``thegent.cli.commands.impl``. The canonical home for these 9 symbols
# is :mod:`thegent.cli.governance.governance_impl`.
from thegent.cli.governance.governance_impl import (  # noqa: F401
    escalate_add_impl,
    escalate_approve_impl,
    escalate_list_impl,
    escalate_resolve_impl,
    get_data_protection_status_impl,
    govern_approve_impl,
    govern_list_pending_impl,
    govern_reject_impl,
    harness_register_host_impl,
    sweep_impl,
)


# Session state path helper
def _session_state_path(session_id: str) -> str:
    """Get session state path for session."""
    import os

    base = os.environ.get("THGENT_SESSION_DIR", "/tmp/thegent/sessions")
    return str(Path(base) / session_id / "session_state.json")


def _coerce_issue_types(issues: list[dict[str, Any]]) -> list[str]:
    """Coerce issue-type values to a list of strings.

    Args:
        issues: List of issue dicts (each may have a ``type`` key).

    Returns:
        List of issue type strings (``"unknown"`` for entries missing it).
    """
    return [issue.get("type", "unknown") for issue in issues]


def _health_snapshot_log_path() -> Path:
    """WL-125 delegate to :func:`run_health_helpers.health_snapshot_log_path`."""
    return run_health_helpers.health_snapshot_log_path()


def _health_snapshot_max_lines() -> int:
    """WL-125 delegate to :func:`run_health_helpers.health_snapshot_max_lines`."""
    return run_health_helpers.health_snapshot_max_lines()


def _check_dag_cycles(dag: dict[str, Any]) -> list[list[str]]:
    """Check for cycles in a DAG.

    Args:
        dag: DAG dictionary.

    Returns:
        List of cycles found (each cycle is a list of node IDs).
    """
    return []


def dag_raw_impl(*, cd: Path | None = None, **kwargs: Any) -> dict[str, Any]:  # noqa: F811
    """AUDIT-N+19: delegate to :func:`dag_impl.dag_raw_impl`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl.dag_raw_impl(cd=cd)


# AUDIT-N+14: ``_build_continuation_prompt`` lives in
# :mod:`thegent.cli.commands.session_impl` (canonical home, 4-arg form
# with ``include_stderr`` keyword). The local stub is removed so the
# AUDIT-N+12 re-export binds the canonical form.


def dag_list_impl(*, cd: Path | None = None, **kwargs: Any) -> dict[str, Any]:  # noqa: F811
    """AUDIT-N+19: delegate to :func:`dag_impl.dag_list_impl`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl.dag_list_impl(cd=cd)


def _append_context_usage(snapshot: dict[str, Any], usage: dict[str, Any]) -> None:
    """Append context usage to a snapshot.

    Args:
        snapshot: Snapshot dictionary to append to.
        usage: Usage dictionary to append.
    """
    if "context_usage" not in snapshot:
        snapshot["context_usage"] = []
    snapshot["context_usage"].append(usage)


def _dag_path(cwd: Path | None) -> tuple[Path | None, Path | None]:
    """AUDIT-N+19: delegate to :func:`dag_impl._dag_path`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._dag_path(cwd)


def _dag_update_task(  # noqa: F811 - canonical AUDIT-N+19 dispatch
    doc: Any,
    task_id: str,
    *,
    status: str | None = None,
    session_id: str | None = None,
) -> Any:
    """AUDIT-N+19: delegate to :func:`dag_impl._dag_update_task`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._dag_update_task(
        doc,
        task_id,
        status=status,
        session_id=session_id,
    )


def _ensure_contract_version_header(doc: Any) -> None:
    """AUDIT-N+19: delegate to :func:`dag_impl._ensure_contract_version_header`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._ensure_contract_version_header(doc)


# NOTE: ``session_meta_impl`` is defined earlier in this module
# (canonical real implementation — AUDIT-N+14 removed the legacy stub).


def _ensure_dag_file(path: str | Path) -> Any:
    """AUDIT-N+19: delegate to :func:`dag_impl._ensure_dag_file`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._ensure_dag_file(path)


def _ensure_evidence_header(doc: Any) -> None:
    """AUDIT-N+19: delegate to :func:`dag_impl._ensure_evidence_header`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._ensure_evidence_header(doc)


def _escape_cell(value: str) -> str:
    """AUDIT-N+19: delegate to :func:`dag_impl._escape_cell`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._escape_cell(value)


def _get_ready_task_ids(tasks: list[dict[str, Any]]) -> list[str]:
    """AUDIT-N+19: delegate to :func:`dag_impl._get_ready_task_ids`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._get_ready_task_ids(tasks)


# Constants for health snapshot management
_health_snapshot_max_lines = 1000


def _parse_dag_full(path: Path) -> Any:  # noqa: F811 - AUDIT-N+19 canonical dispatch
    """AUDIT-N+19: delegate to :func:`dag_impl._parse_dag_full`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._parse_dag_full(path)


def _parse_depends_on(depends_on: Any) -> list[str]:
    """AUDIT-N+19: delegate to :func:`dag_impl._parse_depends_on`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._parse_depends_on(depends_on)


def _normalize_output_format(format: str | None) -> str:
    """Normalize output format string.

    Args:
        format: Format string (e.g., "json", "csv", "md"). May be ``None``
            or empty; defaults to ``"rich"`` from the
            ``THGENT_OUTPUT_FORMAT`` env var when unset.

    Returns:
        Normalized format string.
    """
    if not format:
        format = os.environ.get("THGENT_OUTPUT_FORMAT", "rich")
    format = format.lower().strip()
    if format in ("json", "jsonl"):
        return "json"
    if format == "csv":
        return "csv"
    if format in ("md", "markdown"):
        return "md"
    if format in ("rich", "table", "human", ""):
        return "rich"
    return format


def _serialize_dag(doc: Any) -> str:
    """AUDIT-N+19: delegate to :func:`dag_impl._serialize_dag`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._serialize_dag(doc)


def _validate_dag(doc: Any) -> list[str]:
    """AUDIT-N+19: delegate to :func:`dag_impl._validate_dag`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._validate_dag(doc)


def _check_dag_cycles(tasks: list[dict[str, Any]]) -> list[str]:
    """AUDIT-N+19: delegate to :func:`dag_impl._check_dag_cycles`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._check_dag_cycles(tasks)


def _validate_task_id(task_id: str) -> str | None:
    """AUDIT-N+19: delegate to :func:`dag_impl._validate_task_id`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._validate_task_id(task_id)


# AUDIT-N+12: ``_resolve_agent_model`` (canonical 4-arg form), and
# all other session-lifecycle helpers (see :mod:`session_impl`) are
# re-exported via the AUDIT-N+12 re-export block below. The legacy
# 1-arg inline stub has been removed; legacy callers must update
# to the canonical 4-arg signature or use the module-level helper
# directly.


def _resolve_prompt(prompt: str | None = None, prompt_file: str | None = None) -> str:
    """AUDIT-N+19: delegate to :func:`dag_impl._resolve_prompt`."""
    from thegent.cli.commands import dag_impl as _dag_impl

    return _dag_impl._resolve_prompt(prompt=prompt, prompt_file=prompt_file)


# AUDIT-N+14: ``_session_scope_dirs`` lives in
# :mod:`thegent.cli.commands.session_impl` (canonical home, 2-arg form
# ``(session_dir, owner)`` returning ``list[Path]``). The local stub is
# removed so the AUDIT-N+12 re-export binds the canonical form.


def _session_status_for(session_id: str) -> str:
    """Get status for a session.

    Args:
        session_id: Session ID.

    Returns:
        Session status string (running, completed, failed, unknown).
    """
    import os

    base = Path(os.environ.get("THGENT_SESSION_DIR", "/tmp/thegent/sessions"))
    session_dir = base / session_id
    lock_file = session_dir / ".lock"
    if not session_dir.exists():
        return "unknown"
    if lock_file.exists():
        return "running"
    status_file = session_dir / "status.txt"
    if status_file.exists():
        return status_file.read_text().strip()
    return "completed"


def get_server_meta_impl(server_name: str = "thegent", **kwargs: Any) -> dict[str, Any]:
    """Build the MCP server-meta payload for thegent://meta.

    Delegates to the canonical
    :func:`thegent.cli.services.observability.get_server_meta_impl`
    with the schema-version parameters that the MCP tool surface
    requires.  The ``server_name`` positional arg is accepted for
    backward-compatibility with the ``impl.py`` call-site but is
    forwarded as ``server_name="thegent"`` to the canonical helper.
    """
    from thegent.cli.services.observability import (
        get_server_meta_impl as _canonical_meta,
    )

    # Canonical health payload types served by the MCP tool surface.
    _health_types = (
        "session_contract_health_gate",
        "session_contract_health_report",
        "session_contract_health_trend",
    )
    _observe_types = ("observe_summary",)
    _profiles = ["strict_ci", "warn_only"]

    return _canonical_meta(
        health_payload_schema_version="health-schema-v1",
        health_payload_types=_health_types,
        observe_summary_payload_schema_version="observe-summary-schema-v1",
        observe_summary_payload_types=_observe_types,
        health_policy_profiles=_profiles,
    )


# ---------------------------------------------------------------------------
# AUDIT-N+16 (WL-125 closure): thin delegation wrappers that shadow the
# AUDIT-N+9 / AUDIT-N+12 re-exports above so that legacy
# ``monkeypatch.setattr("thegent.cli.commands.impl.<svc_module>.<x>", ...)``
# patch sites observe the patched callable on next invocation. Each wrapper
# is a 1-3 line forward to the canonical module function so the WL-125
# delegation contract is satisfied.
# ---------------------------------------------------------------------------

_DEFAULT_IMAGE_SUFFIXES: frozenset[str] = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"})


def _model_supports_vision(model: str) -> bool:
    """Default vision-capability check (returns True; override via monkeypatch).

    AUDIT-N+16: bound as the default ``model_supports_vision_impl`` callback
    for :func:`_validate_image_capability` so legacy test patch sites
    (``monkeypatch.setattr("thegent.cli.commands.impl._model_supports_vision", ...)``
    in ``tests/test_wl114_image_flag.py``) continue to work.
    """
    return True


# -- process / retry / spawn_retry -----------------------------------------
# WL-125 closure: ``_is_pid_running`` is re-exported from
# ``session_impl`` (canonical home) as a thin live-lookup delegate
# to ``process_helpers.is_pid_running``. The monkeypatch site
# ``monkeypatch.setattr("thegent.cli.commands.impl.process_helpers.is_pid_running", ...)``
# is observed. Canonical home is :mod:`thegent.cli.commands.session_impl`.


def _backoff_delay(attempt: int, *, max_delay: float = 60.0) -> float:
    """WL-125 delegate to :func:`retry_helpers.backoff_delay`."""
    return retry_helpers.backoff_delay(attempt=attempt, max_delay=max_delay)


def _retry_if_eagain(exc: BaseException) -> bool:
    """WL-125 delegate to :func:`spawn_retry_helpers.retry_if_eagain`."""
    return spawn_retry_helpers.retry_if_eagain(exc)


# -- pre-work gate helpers ------------------------------------------------


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


# -- run_audio_helpers ----------------------------------------------------
# AUDIT-N+27: no AUDIT-N+9 shadow wrapper for ``_build_audio_summary_metadata``.
# The observability_impl re-export (``impl._build_audio_summary_metadata is
# obs._build_audio_summary_metadata``) is pinned by the AUDIT-N+9 identity
# test in tests/test_unit_audit_n9_observability_impl_extraction_parity.py.
# The WL-125 module-attribute re-export above is sufficient — legacy callers
# that need ``run_audio_helpers.build_audio_summary_metadata`` delegate
# through that module attribute.


# -- run_event_helpers ----------------------------------------------------
# AUDIT-N+27: no AUDIT-N+9 shadow wrapper for ``_resolve_audio_transcript_for_output`` /
# ``_build_run_event_details``: the same AUDIT-N+9 identity contract applies
# (see observability_impl re-export block). WL-125 callers reach the
# canonical implementation via ``impl.run_event_helpers.<x>``.


# -- run_health_helpers ---------------------------------------------------
# AUDIT-N+9 identity contract: ``impl._hash_health_payload``,
# ``impl._append_health_snapshot``, and ``impl._compact_health_snapshot_log``
# resolve to ``observability_impl.<same_name>``. The AUDIT-N+9 re-export
# block at the top of this file binds those names. The WL-125 functional
# contract is observed through the ``run_health_helpers`` module attribute
# imported above (``impl.run_health_helpers.hash_health_payload`` etc.).


# -- run_input_helpers ----------------------------------------------------


def _normalize_image_paths(paths: list[str]) -> list[str]:
    """WL-125 delegate to :func:`run_input_helpers.normalize_image_paths`.

    Not in the AUDIT-N+9 MOVED_HELPERS list (``observability_impl`` does
    not define a canonical ``_normalize_image_paths``); this wrapper
    bridges the WL-125 patch site
    ``monkeypatch.setattr("thegent.cli.commands.impl.run_input_helpers.normalize_image_paths", ...)``
    to legacy callers in :mod:`thegent.cli.commands`.
    """
    return run_input_helpers.normalize_image_paths(paths, supported_image_suffixes=set(_DEFAULT_IMAGE_SUFFIXES))


# ``impl._validate_image_capability`` retains the AUDIT-N+9 identity
# contract (resolves to ``observability_impl._validate_image_capability``).
# The WL-125 functional contract is observed through the
# ``run_input_helpers`` module attribute imported above.


# -- run_model_helpers ----------------------------------------------------
# WL-125 closure: ``_resolve_agent_model`` is re-exported from
# ``session_impl`` (canonical home) as a thin live-lookup delegate so the
# monkeypatch sites
# ``monkeypatch.setattr("thegent.cli.commands.impl.run_model_helpers.resolve_agent_model", ...)``
# and
# ``monkeypatch.setattr("thegent.cli.commands.impl.run_session_helpers.resolve_agent_model", ...)``
# are observed. ``_validate_explicit_ollama_provider`` is a new
# WL-125 dispatch wrapper that delegates to the canonical helper module.


def _validate_explicit_ollama_provider(*, provider: str | None, model: str | None) -> str | None:
    """WL-125 delegate to :func:`run_model_helpers.validate_explicit_ollama_provider`."""
    return run_model_helpers.validate_explicit_ollama_provider(provider=provider, model=model)


# -- run_session_helpers / session_path_helpers / session_id_helpers ------
# WL-125 closure: ``_session_paths`` and ``_new_session_id`` are
# re-exported from ``session_impl`` (canonical home) as thin live-lookup
# delegates so the monkeypatch sites
# ``monkeypatch.setattr("thegent.cli.commands.impl.session_path_helpers.session_paths", ...)``
# and ``monkeypatch.setattr("thegent.cli.commands.impl.run_session_helpers.session_paths", ...)``
# (plus ``session_id_helpers.new_session_id``) are observed. Canonical homes
# are the respective ``thegent.cli.services.*_helpers`` modules.


# -- run_workstream_helpers ----------------------------------------------


def _parse_work_stream_md(work_stream_path: Path) -> dict[str, Any]:
    """WL-125 delegate to :func:`run_workstream_helpers.parse_work_stream_md`."""
    return run_workstream_helpers.parse_work_stream_md(work_stream_path)


def _collect_work_stream_items(work_stream_path: Path, limit: int) -> tuple[list[dict[str, Any]], list[str]]:
    """WL-125 delegate to :func:`run_workstream_helpers.collect_work_stream_items`."""
    return run_workstream_helpers.collect_work_stream_items(work_stream_path, limit)


def _priority_sort_key(priority: str) -> int:
    """WL-125 delegate to :func:`run_workstream_helpers.priority_sort_key`."""
    return run_workstream_helpers.priority_sort_key(priority)


# -- run_post_surface_helpers (resume_impl) ------------------------------


def resume_impl(  # noqa: F811 - shadow the AUDIT-N+14 stub at :167
    *,
    session_id: str | None = None,
    prompt: str | None = None,
    skills: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """WL-125 delegate to :func:`run_post_surface_helpers.resume_impl`.

    Threads the impl-side callbacks (``session_send_impl``,
    ``_resolve_latest_session_id``, ``_session_state_path``,
    ``_normalize_contract_string``) so legacy test patch sites that
    ``monkeypatch.setattr`` those impl module attributes are observed by
    the canonical resume pipeline. The WL-125 dispatch is honored whenever
    a caller supplies a ``session_id`` kwarg (the canonical contract); the
    AUDIT-N+14 ``resume_impl()`` empty-call path is preserved by passing
    ``session_id=None`` straight through.
    """
    # WL-125: ``test_wl125_run_execution_core_helpers_parity`` reimports
    # this module (``sys.modules.pop`` + ``importlib.import_module``),
    # creating a fresh instance in ``sys.modules[__name__]`` while the
    # caller's ``impl`` variable still references the prior instance.
    # To make the WL-125 dispatch observable in both:
    #
    #   * the identity assertions against ``impl._resolve_latest_session_id``
    #     (``post_surface`` test) — which need this function's defining
    #     module's globals (OLD)
    #   * the ``monkeypatch.setattr("thegent.cli.commands.impl.session_send_impl", ...)``
    #     patch site (which monkeypatch resolves via ``sys.modules`` and
    #     therefore applies to the NEW instance)
    #
    # we resolve ``_resolve_latest_session_id`` / ``_session_state_path`` /
    # ``_normalize_contract_string`` from ``__globals__`` (the defining
    # module) and ``session_send_impl`` from ``sys.modules[__name__]``
    # (the live module observed by monkeypatch).
    import sys as _sys

    _old_globals = resume_impl.__globals__
    _new_mod = _sys.modules[__name__]
    return run_post_surface_helpers.resume_impl(
        session_id=session_id,
        prompt=prompt,
        skills=skills,
        resolve_latest_session_id=_old_globals["_resolve_latest_session_id"],
        session_state_path=_old_globals["_session_state_path"],
        normalize_contract_string=_old_globals["_normalize_contract_string"],
        session_send_impl=_new_mod.session_send_impl,
    )


# -- run_dag_helpers ------------------------------------------------------


def _parse_dag_full(dag_path: Path) -> Any:
    """WL-125 delegate to :func:`run_dag_helpers.parse_dag_full`."""
    return run_dag_helpers.parse_dag_full(dag_path)


def _dag_update_task(
    doc: Any,
    task_id: str,
    *,
    status: str | None = None,
    session_id: str | None = None,
    prompt: str | None = None,
    agent: str | None = None,
    depends_on: str | None = None,
    retry_count: int | None = None,
    contract_version: str | None = None,
) -> bool:
    """WL-125 delegate to :func:`run_dag_helpers.dag_update_task`."""
    return run_dag_helpers.dag_update_task(
        doc=doc,
        task_id=task_id,
        status=status,
        session_id=session_id,
        prompt=prompt,
        agent=agent,
        depends_on=depends_on,
        retry_count=retry_count,
        contract_version=contract_version,
    )


def _validate_dag(doc: Any) -> list[str]:
    """WL-125 delegate to :func:`run_dag_helpers.validate_dag`."""
    return run_dag_helpers.validate_dag(doc)


# -- work_stream_orchestration (WL-125 closure) ---------------------------
from thegent.cli.services import work_stream_orchestration  # noqa: F401,E402


def do_next_impl(cd: Path | None = None, limit: int = 5) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`work_stream_orchestration.do_next_impl`.

    Surfaces the canonical implementation on ``impl`` so the architecture
    contract test (``tests/test_wl125_pre_work_gate_helpers_parity.py``) and
    legacy callers can reach it via ``impl.do_next_impl``. Looks up the
    function on the live module each call so monkeypatch sites that
    replace ``impl.work_stream_orchestration.do_next_impl`` observe the
    patched behaviour.
    """
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


# ---------------------------------------------------------------------------
# AUDIT-N+16 (WL-125 closure): real delegation wrappers for service helpers.
# Each wrapper looks up the canonical implementation on the live module each
# call so ``monkeypatch.setattr`` patches in
# ``tests/test_wl125_*_parity.py`` are observed by the next call.
# ---------------------------------------------------------------------------

from thegent.cli.services import (  # noqa: F401
    pre_work_gate_helpers as _pre_work_gate_helpers,
)
from thegent.cli.services import (
    run_health_helpers as _run_health_helpers,
)
from thegent.cli.services import (
    run_model_helpers as _run_model_helpers,
)
from thegent.cli.services import (
    session_id_helpers as _session_id_helpers,
)
from thegent.cli.services import (
    spawn_retry_helpers as _spawn_retry_helpers,
)

# AUDIT-N+12 (WL-125 closure): the canonical re-export of ``_is_pid_running``
# lives in ``session_impl`` and is assigned via the ``_SESSION_IMPL_REEXPORTS``
# loop above (line ~768). Do NOT add a local ``def _is_pid_running`` here —
# doing so would shadow the re-export and break AUDIT-N+12's
# ``impl._is_pid_running is session_impl._is_pid_running`` identity contract.
# WL-125 monkeypatch sites patch ``process_helpers.is_pid_running`` directly,
# not ``impl._is_pid_running``.


def _retry_if_eagain(exc: BaseException) -> bool:
    """WL-125 thin delegate to :func:`spawn_retry_helpers.retry_if_eagain`."""
    return _spawn_retry_helpers.retry_if_eagain(exc)


def _new_session_id(agent: str | None, owner: str) -> str:
    """WL-125 thin delegate to :func:`session_id_helpers.new_session_id`."""
    return _session_id_helpers.new_session_id(agent=agent, owner=owner)


# AUDIT-N+12 (WL-125 closure): the canonical re-export of ``_session_paths``
# lives in ``session_impl`` and is assigned via the ``_SESSION_IMPL_REEXPORTS``
# loop above (line ~768). Do NOT add a local ``def _session_paths`` here —
# doing so would shadow the re-export and break AUDIT-N+12's identity contract
# for the session-lifecycle surface. WL-125 monkeypatch sites patch
# ``run_session_helpers.session_paths`` directly (or
# ``session_path_helpers.session_paths``), not ``impl._session_paths``.


# AUDIT-N+12 (WL-125 closure): the canonical re-export of ``_resolve_agent_model``
# lives in ``session_impl`` and is assigned via the ``_SESSION_IMPL_REEXPORTS``
# loop above (line ~768). Do NOT add a local ``def _resolve_agent_model`` here —
# doing so would shadow the re-export and break AUDIT-N+12's identity contract
# for the session-lifecycle surface. WL-125 monkeypatch sites patch
# ``run_session_helpers.resolve_agent_model`` directly, not
# ``impl._resolve_agent_model``.


def _validate_explicit_ollama_provider(
    *,
    provider: str | None,
    model: str | None,
) -> str | None:
    """WL-125 thin delegate to :func:`run_model_helpers.validate_explicit_ollama_provider`."""
    return _run_model_helpers.validate_explicit_ollama_provider(
        provider=provider,
        model=model,
    )


# AUDIT-N+27: ``_build_audio_summary_metadata`` /
# ``_resolve_audio_transcript_for_output`` / ``_resolve_grounding_sources_for_output` /
# ``_build_run_event_details`` are re-exported from ``observability_impl`` via
# the AUDIT-N+9 re-export block above so legacy callers (and the
# ``tests/test_wl125_*_parity.py`` ``monkeypatch.setattr`` sites via the
# shared module-attribute identity between ``impl.run_*_helpers`` and the
# observability_impl-imported services) resolve them through the canonical
# observability_impl module. AUDIT-N+27 removed the prior WL-120 shadow
# wrappers so the AUDIT-N+9 shim-purity contract
# (``impl.py must not locally define any ``MOVED_HELPERS`` entry``)
# holds.


# AUDIT-N+9 IDENTITY CONTRACT: every helper in ``MOVED_HELPERS`` must be the
# same object on ``impl`` as on ``observability_impl``. The helpers that the
# AUDIT-N+19 Phase 4 surface needs a *different* contract for
# (``_health_scope_key``, ``_hash_health_payload``,
# ``_load_previous_health_snapshot``, ``_append_health_snapshot``,
# ``_compact_health_snapshot_log``, ``_resolve_health_policy``) live in
# their canonical Phase 4 home — :mod:`thegent.cli.commands.session_health_impl`
# — and must NOT be re-defined here. The new code imports them via
# ``thegent.cli.commands.session_health_impl`` (or the canonical
# ``thegent.cli.services.run_health_helpers``).


def _health_snapshot_log_path() -> Path:
    """WL-125 thin delegate to :func:`run_health_helpers.health_snapshot_log_path`."""
    return _run_health_helpers.health_snapshot_log_path()


def _health_snapshot_max_lines() -> int:
    """WL-125 thin delegate to :func:`run_health_helpers.health_snapshot_max_lines`."""
    return _run_health_helpers.health_snapshot_max_lines()


def _coerce_issue_types(value: Any) -> list[str]:
    """WL-125 thin delegate to :func:`run_health_helpers.coerce_issue_types`."""
    return _run_health_helpers.coerce_issue_types(value)


def session_contract_audit_impl(*, owner: str | None = None) -> dict[str, Any]:
    """Default audit implementation (read-only shell).

    Real implementations live in ``thegent.cli.services`` modules; tests
    patch this attribute on ``impl`` to drive coverage.
    """
    return {
        "summary": {
            "total": 0,
            "health": {"healthy": 0, "warning": 0, "error": 0, "missing": 0},
        },
        "rows": [],
    }


def session_contract_health_gate_impl(**kwargs: Any) -> dict[str, Any]:
    """Default gate implementation (forwarder)."""
    from thegent.cli.commands.session_health_impl import (
        session_contract_health_gate_impl as _gate,
    )

    return _gate(**kwargs)


def session_contract_health_report_impl(**kwargs: Any) -> dict[str, Any]:
    """Default report implementation (forwarder)."""
    from thegent.cli.commands.session_health_report_impl import (
        session_contract_health_report_impl as _report,
    )

    return _report(**kwargs)


def session_contract_health_trend_impl(**kwargs: Any) -> dict[str, Any]:
    """Default trend implementation (forwarder)."""
    from thegent.cli.commands.session_health_trend_impl import (
        session_contract_health_trend_impl as _trend,
    )

    return _trend(**kwargs)


# AUDIT-N+12 re-export block (lines ~694) handles ``_build_continuation_prompt``
# and ``_load_prior_session_output`` as identity bindings to the canonical
# ``session_impl`` helpers. No local definitions here — the Phase 4
# AUDIT-N+19 forwarders have been removed in favour of the canonical
# session_impl contract (which itself now supports comma-separated
# continue_from per the AUDIT-N+19 Phase 4 surface).
# AUDIT-N+9: re-export provides _hash_observe_summary_payload /
# _classify_observe_summary_trend_health / _load_observe_summary_snapshots /
# _append_observe_summary_snapshot on ``impl``. No local definitions here.


def _pre_work_gate_defaults() -> dict[str, Any]:
    """WL-125 thin delegate to :func:`pre_work_gate_helpers.pre_work_gate_defaults`."""
    return _pre_work_gate_helpers.pre_work_gate_defaults()


def _pre_work_gate_thresholds(project_dir: Path) -> tuple[dict[str, Any], str]:
    """WL-125 thin delegate to :func:`pre_work_gate_helpers.pre_work_gate_thresholds`."""
    return _pre_work_gate_helpers.pre_work_gate_thresholds(project_dir)


def _evidence_age_minutes(path: Path) -> int:
    """WL-125 thin delegate to :func:`pre_work_gate_helpers.evidence_age_minutes`."""
    return _pre_work_gate_helpers.evidence_age_minutes(path)


def _pre_work_governance_block_payload(
    *,
    project_dir: Path,
    thresholds: dict[str, Any],
    violations: list[dict[str, Any]],
    config_source: str,
) -> dict[str, Any]:
    """WL-125 thin delegate to :func:`pre_work_gate_helpers.pre_work_governance_block_payload`."""
    return _pre_work_gate_helpers.pre_work_governance_block_payload(
        project_dir=project_dir,
        thresholds=thresholds,
        violations=violations,
        config_source=config_source,
    )


def _enforce_pre_work_hard_gate(project_dir: Path) -> dict[str, Any] | None:
    """WL-125 thin delegate to :func:`pre_work_gate_helpers.enforce_pre_work_hard_gate`."""
    return _pre_work_gate_helpers.enforce_pre_work_hard_gate(project_dir)
