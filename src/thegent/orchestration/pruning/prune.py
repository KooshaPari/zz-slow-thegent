"""Pruning side-effect entry point (AUDIT-N+39 hardened).

This module exposes two surface areas:

* AUDIT-N+39 spec surface:
  - ``mcp_prune(session, pane=None)`` -- single-session prune that
    re-checks the protected-process guard and kills the session's
    PID via ``os.kill``. Returns a result dict. Used by the
    AUDIT-N+39 hardening spec.

* Dormant ``test_shadow_cleanup`` / WL-036 surface:
  - ``mcp_prune(*, dry_run=False, shadow_max_age_hours=24,
    caller_info=None, quality_log_max_age_days=7)`` -- bulk prune
    that walks running processes, kills eligible candidates, and
    sweeps stale ``.shadow-*`` and quality-log dirs. Used by the
    dormant shadow-cleanup tests.

  - ``_prune_stale_shadow_and_logs(dry_run, shadow_max_age_hours,
    quality_log_max_age_days)`` -- the shadow + quality-log sweep.

The single-session form is selected when ``session`` is a dict;
the bulk form is selected when called with keyword-only args.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from thegent.orchestration.pruning.smart_prune import _is_protected_process

__all__ = [
    "_prune_stale_shadow_and_logs",
    "is_orphan_by_ppid",
    "kill_process",
    "kill_session",
    "list_tmux_panes",
    "mcp_prune",
    "run_subprocess_optimized",
]


# ---------------------------------------------------------------------------
# AUDIT-N+39 spec surface
# ---------------------------------------------------------------------------


def kill_session(session: dict[str, Any], pane: str | None = None) -> dict[str, Any]:
    """Best-effort session termination for the AUDIT-N+39 spec.

    Returns a dict with ``status`` (``"killed"`` | ``"skipped"`` |
    ``"error"``) and a ``reason`` field on non-``killed`` outcomes.
    """
    agent = str(session.get("agent", ""))
    if _is_protected_process(agent):
        return {"status": "skipped", "reason": "protected_process", "agent": agent}

    pid = session.get("pid")
    if pid is None or not isinstance(pid, int):
        return {"status": "skipped", "reason": "no_pid", "agent": agent}

    try:
        os.kill(pid, signal.SIGTERM)
        return {"status": "killed", "pid": pid, "pane": pane}
    except ProcessLookupError:
        return {"status": "skipped", "reason": "already_exited", "pid": pid}
    except PermissionError:
        return {"status": "error", "reason": "permission_denied", "pid": pid}


# ---------------------------------------------------------------------------
# Dormant bulk-prune surface (test_shadow_cleanup / WL-036)
# ---------------------------------------------------------------------------


def run_subprocess_optimized(
    args: list[str],
    *,
    timeout: float | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Wrapper around ``subprocess.run`` so tests can patch it cleanly."""
    return subprocess.run(  # noqa: S603 -- caller-controlled args
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        **kwargs,
    )


def list_tmux_panes() -> list[dict[str, Any]]:
    """Return a list of tmux panes (stub returning empty list)."""
    return []


def is_orphan_by_ppid(pid: int, ppid: int) -> bool:
    """Heuristic: a process is orphan when its parent PID is 1."""
    return ppid == 1


def kill_process(pid: int) -> bool:
    """Best-effort process termination. Returns True on success."""
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _prune_stale_shadow_and_logs(
    dry_run: bool = False,
    shadow_max_age_hours: int = 24,
    quality_log_max_age_days: int = 7,
) -> tuple[int, int]:
    """Sweep stale ``.shadow-*`` dirs and quality-log files.

    Returns ``(shadow_count, log_count)``. ``dry_run=True`` reports
    without deleting.
    """
    try:
        workspace = Path.cwd().resolve()
        root = workspace.parent
    except (OSError, FileNotFoundError):
        return 0, 0

    cutoff_shadow = time.time() - (shadow_max_age_hours * 3600)
    cutoff_log = time.time() - (quality_log_max_age_days * 86400)

    shadow_count = 0
    log_count = 0

    try:
        candidates = list(root.iterdir())
    except OSError:
        return 0, 0

    for entry in candidates:
        try:
            if entry.is_dir() and entry.name.startswith(".shadow-"):
                mtime = entry.stat().st_mtime
                if mtime < cutoff_shadow:
                    shadow_count += 1
                    if not dry_run:
                        try:
                            import shutil

                            shutil.rmtree(entry)
                        except OSError:
                            pass
        except OSError:
            continue

    try:
        for entry in candidates:
            if (
                entry.is_file()
                and entry.name.startswith("quality")
                and entry.suffix == ".log"
            ):
                mtime = entry.stat().st_mtime
                if mtime < cutoff_log:
                    log_count += 1
                    if not dry_run:
                        with contextlib.suppress(OSError):
                            entry.unlink()
    except OSError:
        pass

    return shadow_count, log_count


def _bulk_mcp_prune(
    *,
    dry_run: bool = False,
    shadow_max_age_hours: int = 24,
    caller_info: str | None = None,
    quality_log_max_age_days: int = 7,
) -> dict[str, Any]:
    """Bulk-prune implementation used when ``mcp_prune`` is called in
    keyword-only mode (dormant WL-036 corridor).
    """
    result: dict[str, Any] = {
        "dry_run": dry_run,
        "shadow_max_age_hours": shadow_max_age_hours,
        "caller_info": caller_info,
        "killed": 0,
        "kept": 0,
        "skipped_protected": 0,
    }

    panes = list_tmux_panes()
    if panes:
        result["tmux_panes"] = len(panes)

    try:
        ps = run_subprocess_optimized(["ps", "-axo", "pid,ppid,tty,rss,command"])
        stdout = ps.stdout or ""
    except (OSError, FileNotFoundError):
        stdout = ""

    protected_hits = 0
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("PID"):
            continue
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        command = parts[4]
        if _is_protected_process(command):
            protected_hits += 1
            continue
        if not is_orphan_by_ppid(pid, ppid):
            continue
        if dry_run:
            result["killed"] = int(result["killed"]) + 1  # type: ignore[assignment]
            continue
        if kill_process(pid):
            result["killed"] = int(result["killed"]) + 1  # type: ignore[assignment]
        else:
            result["kept"] = int(result["kept"]) + 1  # type: ignore[assignment]

    result["skipped_protected"] = protected_hits

    # Always run the shadow sweep (dry_run is passed through).
    shadow_count, _logs = _prune_stale_shadow_and_logs(
        dry_run=dry_run,
        shadow_max_age_hours=shadow_max_age_hours,
        quality_log_max_age_days=quality_log_max_age_days,
    )
    result["shadow_removed"] = shadow_count
    return result


def mcp_prune(
    session: dict[str, Any] | None = None,
    pane: str | None = None,
    *,
    dry_run: bool = False,
    shadow_max_age_hours: int = 24,
    caller_info: str | None = None,
    quality_log_max_age_days: int = 7,
) -> Any:
    """Two-shape entry point.

    @trace FR-RES-015

    * Spec shape: ``mcp_prune(session, pane=None)`` returns a result
      dict describing a single-session prune.
    * Dormant bulk shape: ``mcp_prune(dry_run=..., ...)`` returns a
      bulk result dict and runs the shadow sweep.
    """
    # Heuristic: if session is a dict (or any non-None positional) the
    # caller wants the spec-shape; otherwise dispatch to bulk.
    if session is not None or pane is not None:
        return kill_session(session or {}, pane=pane)
    return _bulk_mcp_prune(
        dry_run=dry_run,
        shadow_max_age_hours=shadow_max_age_hours,
        caller_info=caller_info,
        quality_log_max_age_days=quality_log_max_age_days,
    )
