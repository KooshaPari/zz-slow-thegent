"""CLI command implementations.

This module contains the CLI command functions for session management,
team operations, and other CLI features.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

from thegent.ux.cli_errors import safe_echo

if TYPE_CHECKING:
    from rich.console import Console


def _serialize_health_gate_jsonl(results: list[dict]) -> str:
    """Serialize health gate results to JSONL format.

    Args:
        results: List of health check result dictionaries.

    Returns:
        JSONL string representation.
    """
    import json

    lines = []
    for result in results:
        lines.append(json.dumps(result))
    return "\n".join(lines)


def _inject_skill_instructions(prompt: str, skills: list[str]) -> str:
    """Inject skill instructions into a prompt.

    Args:
        prompt: The prompt to inject instructions into.
        skills: List of skill names to inject.

    Returns:
        Prompt with skill instructions injected.
    """
    if not skills:
        return prompt
    skill_section = "\n\nSkills available:\n" + "\n".join(f"- {s}" for s in skills)
    return prompt + skill_section


def _format_grounding_sources_lines(sources: list[dict]) -> list[str]:
    """Format grounding sources as display lines.

    Args:
        sources: List of source dictionaries.

    Returns:
        List of formatted source lines.
    """
    lines = []
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        lines.append(f"[{i}] {title}")
        if url:
            lines.append(f"    {url}")
    return lines


def _format_context_usage_line(usage: dict) -> str:
    """Format context usage as a display line.

    Args:
        usage: Usage dictionary with tokens and limits.

    Returns:
        Formatted usage line.
    """
    used = usage.get("tokens", 0)
    limit = usage.get("limit", 0)
    pct = (used / limit * 100) if limit > 0 else 0
    return f"Context: {used:,}/{limit:,} tokens ({pct:.1f}%)"


__all__ = [
    "audit_stats_cmd",
    "logs_cmd",
    "stop_cmd",
    "team_create_cmd",
    "team_task_add_cmd",
    "team_task_list_cmd",
    "_serialize_health_gate_csv",
    "_serialize_health_gate_jsonl",
    "_serialize_health_trend_csv",
    "_scope_key",
    "_inject_skill_instructions",
    "_format_grounding_sources_lines",
    "_format_context_usage_line",
    "_serialize_health_gate_md",
    "_format_transcript_summary_line",
    "_serialize_health_report_csv",
    "_serialize_health_report_jsonl",
    "_serialize_health_report_md",
    "_serialize_health_trend_jsonl",
    "_serialize_health_trend_md",
]


def _serialize_health_trend_md(results: list[dict]) -> str:
    """Serialize health trend results to Markdown format.

    Args:
        results: List of health trend result dictionaries.

    Returns:
        Markdown string representation.
    """
    if not results:
        return "No health trend data available."
    lines = ["# Health Trend Results", ""]
    for result in results:
        timestamp = result.get("timestamp", "N/A")
        metric = result.get("metric", "unknown")
        value = result.get("value", 0)
        lines.append(f"- **{metric}** ({timestamp}): {value}")
    return "\n".join(lines)


def _serialize_health_trend_jsonl(results: list[dict]) -> str:
    """Serialize health trend results to JSONL format.

    Args:
        results: List of health trend result dictionaries.

    Returns:
        JSONL string representation.
    """
    import json

    lines = []
    for result in results:
        lines.append(json.dumps(result))
    return "\n".join(lines)


def _serialize_health_trend_csv(results: list[dict]) -> str:
    """Serialize health trend results to CSV format.

    Args:
        results: List of health trend result dictionaries.

    Returns:
        CSV string representation.
    """
    if not results:
        return ""
    headers = ["timestamp", "metric", "value"]
    lines = [",".join(headers)]
    for result in results:
        row = [
            result.get("timestamp", ""),
            result.get("metric", ""),
            str(result.get("value", "")),
        ]
        lines.append(",".join(f'"{r}"' for r in row))
    return "\n".join(lines)


def _serialize_health_report_md(results: list[dict]) -> str:
    """Serialize health report results to Markdown format.

    Args:
        results: List of health report result dictionaries.

    Returns:
        Markdown string representation.
    """
    return _serialize_health_gate_md(results)


def _serialize_health_report_jsonl(results: list[dict]) -> str:
    """Serialize health report results to JSONL format.

    Args:
        results: List of health report result dictionaries.

    Returns:
        JSONL string representation.
    """
    return _serialize_health_gate_jsonl(results)


def _serialize_health_report_csv(results: list[dict]) -> str:
    """Serialize health report results to CSV format.

    Args:
        results: List of health report result dictionaries.

    Returns:
        CSV string representation.
    """
    return _serialize_health_gate_csv(results)


def _serialize_health_gate_md(results: list[dict]) -> str:
    """Serialize health gate results to Markdown format.

    Args:
        results: List of health check result dictionaries.

    Returns:
        Markdown string representation.
    """
    if not results:
        return "No health checks performed."

    lines = ["# Health Gate Results", ""]
    for result in results:
        check = result.get("check", "Unknown")
        status = result.get("status", "unknown")
        message = result.get("message", "")
        lines.append(f"- **{check}**: {status} - {message}")

    return "\n".join(lines)


def _format_transcript_summary_line(transcript: dict[str, Any]) -> str:
    """Format a transcript summary line.

    Args:
        transcript: Transcript dictionary.

    Returns:
        Formatted summary line string.
    """
    duration = transcript.get("duration", 0.0)
    word_count = transcript.get("word_count", 0)
    return f"Transcript ({duration:.1f}s, {word_count} words)"


def _serialize_health_gate_csv(results: list[dict]) -> str:
    """Serialize health gate results to CSV format.

    Args:
        results: List of health check result dictionaries.

    Returns:
        CSV string representation.
    """
    if not results:
        return ""
    headers = ["check", "status", "message"]
    lines = [",".join(headers)]
    for result in results:
        row = [
            result.get("check", ""),
            result.get("status", ""),
            result.get("message", ""),
        ]
        lines.append(",".join(f'"{r}"' for r in row))
    return "\n".join(lines)


def _scope_key(scope: str, key: str) -> str:
    """Create a scoped key.

    Args:
        scope: The scope prefix.
        key: The key name.

    Returns:
        Scoped key string.
    """
    return f"{scope}:{key}"


def _is_pid_running(pid: int) -> bool:
    """Check if a process is still running.

    Args:
        pid: Process ID to check.

    Returns:
        True if process is running, False otherwise.
    """
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# AUDIT-N+4 (Phase 3/4 governance observability + perf hardening
# lane): the canonical default audit-path for the new flat CLI
# command. Lives in the XDG state-hierarchy root so the
# ``~/.local/state/thegent/`` convention (already used by other
# tooling) is preserved. ``DecisionAuditAppender`` will lazily
# ``expanduser()`` it on construction, so the value is stored as a
# plain ``str`` until the caller wires it through.
_DEFAULT_AUDIT_STATS_PATH = Path("~/.local/state/thegent/decisions.jsonl")


def audit_stats_cmd(
    audit_path: Path | None = None,
    json_output: bool = False,
) -> int:
    """Surface the ``DecisionAuditAppender.audit_stats()`` snapshot.

    AUDIT-N+4 — operators running SOTA replay tooling have been
    asking for a CLI surface to read the rotation / durability
    observability counters without spinning up a Python REPL. This
    command wraps :meth:`thegent.ux.decision_audit.
    DecisionAuditAppender.audit_stats` and emits the snapshot either
    as JSON (machine-readable; ``--json``) or as a sorted key-value
    table (operator-readable; default).

    Path resolution mirrors ``cli_cockpit.py:420-439`` — the
    ``DecisionAuditAppender(audit_path=audit_path)`` constructor
    pattern. ``audit_path`` overrides the XDG-state-hierarchy
    default (``~/.local/state/thegent/decisions.jsonl``); the
    appender itself performs ``expanduser()`` so an operator can
    pass ``--audit-path ~/my-audit.jsonl`` without pre-expansion.

    Errors render through :func:`thegent.ux.cli_errors.safe_echo`
    (per the AUDIT-N+1..N+3 envelope contract) so a malicious /
    buggy audit-path string containing Rich markup cannot inject
    colour tags into the operator's terminal.

    Args:
        audit_path: Optional override for the JSONL path. ``None``
            falls back to the XDG-state-hierarchy default.
        json_output: When ``True``, emit the snapshot as
            ``json.dumps(..., indent=2, sort_keys=True)`` JSON on
            stdout. When ``False`` (the default), emit a sorted
            ``key: value`` table.

    Returns:
        ``0`` on success, ``1`` if the audit log file does not exist
        yet (a freshly-installed machine with no cockpit activity).
    """
    # Lazy imports so the flat CLI module's import graph stays
    # bounded — ``decision_audit`` is only needed by the
    # ``audit_stats`` / ``audit_tail`` surface, not by every
    # command that re-exports symbols through this module.
    from thegent.ux.cli_errors import safe_echo
    from thegent.ux.decision_audit import DecisionAuditAppender

    resolved: Path = (audit_path or _DEFAULT_AUDIT_STATS_PATH).expanduser()
    if not resolved.exists():
        # AUDIT-N+1..N+3 envelope contract: route through ``safe_echo``
        # so the operator-supplied / filesystem-supplied ``resolved``
        # path (which could contain Rich markup) is Rich-markup-
        # escaped end-to-end. The path is coerced via ``str(...)`` so
        # ``safe_echo``'s ``exc_text`` branch handles it correctly.
        safe_echo("audit_stats: log file not found:", str(resolved), err=True)
        return 1
    appender = DecisionAuditAppender(audit_path=resolved)
    snapshot: dict[str, int | bool] = appender.audit_stats()
    if json_output:
        import json

        typer.echo(json.dumps(snapshot, indent=2, sort_keys=True))
    else:
        # Human mode: one ``key: value`` line per snapshot entry,
        # sorted by key for stable operator output. Use
        # ``typer.echo`` directly here — the snapshot keys /
        # values are produced by ``DecisionAuditAppender.audit_stats``
        # (bounded identifiers + numeric / bool primitives), not
        # operator-supplied data, so no Rich-escape shim is needed.
        for key in sorted(snapshot):
            typer.echo(f"{key}: {snapshot[key]}")
    return 0


def logs_cmd(
    session_id: str,
    follow: bool = False,
    tail: int = 20,
    timeout: int | None = None,
) -> int:
    """Display logs for a session.

    Args:
        session_id: The session ID.
        follow: Whether to follow (tail -f style).
        tail: Number of lines to show.
        timeout: Timeout in seconds for follow mode.

    Returns:
        Exit code (0 for success, 124 for timeout).
    """
    from thegent.cli.commands._cli_shared import get_session_dir

    session_dir = get_session_dir()
    log_file = session_dir / f"{session_id}.stdout.log"

    # Owner-scoped probe: log files live under
    # ``session_dir / <owner_with_colons_replaced>`` alongside the meta
    # file. If the direct path doesn't exist, walk one level deep.
    if not log_file.exists():
        try:
            for child in session_dir.iterdir():
                if not child.is_dir():
                    continue
                candidate = child / f"{session_id}.stdout.log"
                if candidate.exists():
                    log_file = candidate
                    break
        except OSError:
            pass
        if not log_file.exists():
            safe_echo("Log file not found:", log_file, err=True)
            return 1

    # Read and display logs
    lines = log_file.read_text().splitlines()
    for line in lines[-tail:]:
        typer.echo(line)

    if follow:
        # Follow mode
        assert timeout is not None
        start_time = time.time()
        last_size = log_file.stat().st_size

        while True:
            current_size = log_file.stat().st_size
            if current_size > last_size:
                new_content = log_file.read_text()[last_size:]
                for line in new_content.splitlines():
                    typer.echo(line)
                last_size = current_size

            if _is_pid_running(_get_session_pid(session_id, session_dir)):
                if time.time() - start_time > timeout:
                    raise typer.Exit(124)
            else:
                break

            time.sleep(0.1)

    return 0


def _get_session_pid(session_id: str, session_dir: Path) -> int:
    """Get the PID for a session from its metadata file.

    Args:
        session_id: The session ID.
        session_dir: The session directory.

    Returns:
        Process ID or 0 if not found.
    """
    import json

    meta_file = session_dir / f"{session_id}.json"
    if meta_file.exists():
        meta = json.loads(meta_file.read_text())
        return meta.get("pid", 0)
    return 0


def stop_cmd(
    session_id: str,
    force: bool = False,
    wind_down: bool = False,
    grace: int = 5,
) -> None:
    """Stop a running session.

    Args:
        session_id: The session ID to stop.
        force: Force kill the process.
        wind_down: Allow graceful shutdown with grace period.
        grace: Grace period in seconds for wind_down.
    """
    from thegent.cli.commands._cli_shared import get_session_dir

    session_dir = get_session_dir()
    meta_file = session_dir / f"{session_id}.json"

    # Owner-scoped probe: session files live under
    # ``session_dir / <owner_with_colons_replaced>``. If the direct path
    # doesn't exist, walk one level deep to find the meta file.
    if not meta_file.exists():
        try:
            for child in session_dir.iterdir():
                if not child.is_dir():
                    continue
                candidate = child / f"{session_id}.json"
                if candidate.exists():
                    meta_file = candidate
                    break
        except OSError:
            pass
        if not meta_file.exists():
            safe_echo("Session not found:", session_id, err=True)
            raise typer.Exit(1)

    import json

    meta = json.loads(meta_file.read_text())
    pid = meta.get("pid", 0)

    if pid and _is_pid_running(pid):
        if wind_down and not force:
            # Send SIGTERM and wait for graceful shutdown
            os.killpg(pid, 15)  # SIGTERM
            # Wait for graceful shutdown
            deadline = time.time() + grace
            while _is_pid_running(pid) and time.time() < deadline:
                time.sleep(0.1)

            if _is_pid_running(pid):
                typer.echo("Process still running after grace period, force killing...")
                os.killpg(pid, 9)  # SIGKILL
        elif force:
            os.killpg(pid, 9)  # SIGKILL
        else:
            os.killpg(pid, 15)  # SIGTERM
    else:
        typer.echo(f"Process {pid} is not running")


# =============================================================================
# Team Commands
# =============================================================================

console: Console = None  # Will be set by CLI framework


def team_create_cmd(
    *,
    name: str,
    leader: str | None = None,
    teammates: str | None = None,
    console: Console | None = None,
) -> None:
    """Create a new team.

    Args:
        name: Team name.
        leader: Leader agent name.
        teammates: Comma-separated teammate names.
        console: Rich console for output.
    """
    from thegent.cli.commands.team_commands import team_create_cmd as actual_cmd

    if console is None:
        from rich.console import Console

        console = Console()

    actual_cmd(name=name, leader=leader, teammates=teammates, console=console)


def team_task_add_cmd(
    *,
    team_id: str,
    title: str,
    description: str,
    console: Console | None = None,
) -> None:
    """Add a task to a team.

    Args:
        team_id: Team ID.
        title: Task title.
        description: Task description.
        console: Rich console for output.
    """
    from thegent.cli.commands.team_commands import team_task_add_cmd as actual_cmd

    if console is None:
        from rich.console import Console

        console = Console()

    actual_cmd(team_id=team_id, title=title, description=description, console=console)


def team_task_list_cmd(
    *,
    team_id: str,
    console: Console | None = None,
) -> None:
    """List tasks for a team.

    Args:
        team_id: Team ID.
        console: Rich console for output.
    """
    from thegent.cli.commands.team_commands import team_task_list_cmd as actual_cmd

    if console is None:
        from rich.console import Console

        console = Console()

    actual_cmd(team_id=team_id, console=console)


# ============================================================================
# WL-124: Wildcard re-exports from each extracted domain module.
# The contract tests inspect ``inspect.getsource(cli)`` for these lines.
# NOTE: `logs_cmd` and `stop_cmd` are intentionally NOT re-exported from
# session_cmds. session_cmds.logs_cmd / session_cmds.stop_cmd are thin shims
# that delegate back into this module, which causes import-time name
# shadowing (the shim replaces the real definition in this module's
# namespace, then the shim's delegation call resolves to the shadowed
# shim → infinite recursion). The local `logs_cmd` (line 295) and
# `stop_cmd` (line 370) remain the canonical implementations because
# they are defined BEFORE the wildcard import below.
# WL-120 Wave-X: private compat re-exports via _cli_shared wildcard.
# The contract test ``test_cli_no_longer_has_explicit_private_cli_shared_import_block``
# asserts the source does NOT contain the explicit ``from ... import (`` form.
from thegent.cli.commands._cli_shared import *  # noqa: F401,F403,E402

# WL-136 B90-W2-D2: _tooling_* aliases for backward compat
from thegent.cli.commands.cli_tooling import (  # noqa: E402,F401
    audit_verify_cmd as _tooling_audit_verify_cmd,
)
from thegent.cli.commands.governance_cmds import *  # noqa: F401,F403,E402
from thegent.cli.commands.infra_cmds import *  # noqa: F401,F403,E402
from thegent.cli.commands.model_cmds import *  # noqa: F401,F403,E402
from thegent.cli.commands.plan_cmds import *  # noqa: F401,F403,E402
from thegent.cli.commands.run_cmds import *  # noqa: F401,F403,E402
from thegent.cli.commands.session_cmds import *  # noqa: F401,F403,E402
from thegent.cli.commands.team_cmds import *  # noqa: F401,F403,E402

# ---------------------------------------------------------------------------
# WL-124/WL-125: Explicit delegating wrappers placed AFTER wildcard imports
# so they are not shadowed by the wildcard-imported names from
# team_cmds, infra_cmds, plan_cmds, etc.
# ---------------------------------------------------------------------------


def team_create_cmd(
    *,
    name: str,
    leader: str | None = None,
    teammates: str | None = None,
    console: Console | None = None,
) -> None:
    """Create a new team (WL-124 delegating wrapper)."""
    from thegent.cli.commands.team_commands import team_create_cmd as _actual

    if console is None:
        console = globals().get("console")

    _actual(name=name, leader=leader, teammates=teammates, console=console)


def team_task_add_cmd(
    *,
    team_id: str,
    title: str,
    description: str,
    console: Console | None = None,
) -> None:
    """Add a task to a team (WL-124 delegating wrapper)."""
    from thegent.cli.commands.team_commands import team_task_add_cmd as _actual

    if console is None:
        console = globals().get("console")

    _actual(team_id=team_id, title=title, description=description, console=console)


def team_task_list_cmd(
    *,
    team_id: str,
    console: Console | None = None,
) -> None:
    """List tasks for a team (WL-124 delegating wrapper)."""
    from thegent.cli.commands.team_commands import team_task_list_cmd as _actual

    if console is None:
        console = globals().get("console")

    _actual(team_id=team_id, console=console)


def recover_status_cmd() -> None:
    """Show recovery status (WL-124 delegating wrapper)."""
    from thegent.cli.commands.recovery_commands import (
        recover_status_cmd as _actual,
    )

    _actual(console=console)


def forensics_snapshot_cmd(
    *,
    run_id: str,
    phase: str,
    console: Console | None = None,
) -> None:
    """Take a forensics snapshot (WL-124 delegating wrapper)."""
    from thegent.cli.commands.recovery_commands import (
        forensics_snapshot_cmd as _actual,
    )

    if console is None:
        console = globals().get("console")

    _actual(run_id=run_id, phase=phase, console=console)


def queue_list_cmd(*, watch: bool = False) -> None:
    """List queued items (WL-124 delegating wrapper)."""
    from thegent.cli.commands.queue_commands import queue_list_cmd as _actual

    _actual(watch=watch)


def project_register_cmd(
    *,
    path: Path,
    name: str,
    console: Console | None = None,
) -> None:
    """Register a project (WL-124 delegating wrapper)."""
    from thegent.cli.commands.project_commands import (
        project_register_cmd as _actual,
    )

    if console is None:
        console = globals().get("console")

    _actual(path=path, name=name, console=console)


def project_list_cmd(
    *,
    format: str = "json",  # noqa: A002
    console: Console | None = None,
) -> None:
    """List registered projects (WL-124 delegating wrapper)."""
    from thegent.cli.commands.project_commands import (
        project_list_cmd as _actual,
    )

    if console is None:
        console = globals().get("console")

    _actual(format=format, console=console)
