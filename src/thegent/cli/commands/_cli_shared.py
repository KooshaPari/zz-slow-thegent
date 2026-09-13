"""Shared CLI utilities.

This module provides shared utilities used across CLI commands.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from rich.console import Console

from thegent.config import ThegentSettings

# Standard exit codes used by the CLI.
EXIT_TIMEOUT: int = 124
EXIT_HEALTH_GATE_FAILED: int = 1


console: Console = Console()


class RunRegistry:
    """Registry for tracking CLI runs.

    WL-124 stable import surface.
    """

    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}

    def register(self, run_id: str, info: dict[str, Any]) -> None:
        """Register a run."""
        self._runs[run_id] = info

    def lookup(self, run_id: str) -> dict[str, Any] | None:
        """Look up a run by id."""
        return self._runs.get(run_id)


def get_session_dir() -> Path:
    """Get the session directory from environment or default.

    Returns:
        Path to the session directory.
    """
    session_dir = os.environ.get("THGENT_SESSION_DIR", "/tmp/thegent/sessions")
    path = Path(session_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_owner_dir(owner: str, session_dir: Path | None = None) -> Path:
    """Resolve the directory for a specific owner.

    Args:
        owner: The owner tag.
        session_dir: Optional session directory.

    Returns:
        Path to the owner's session directory.
    """
    if session_dir is None:
        session_dir = get_session_dir()

    owner_dir = session_dir / owner.replace(":", "_")
    owner_dir.mkdir(parents=True, exist_ok=True)
    return owner_dir


def _lazy_import(module_name: str, attr_name: str | None = None) -> Any:
    """Lazily import a module or attribute.

    WL-124 stable import surface.

    Args:
        module_name: Module to import.
        attr_name: Optional attribute name to fetch.

    Returns:
        Imported module or attribute.
    """
    import importlib

    module = importlib.import_module(module_name)
    if attr_name is None:
        return module
    return getattr(module, attr_name)


def _resolve_run_id(run_id: str | None) -> str:
    """Resolve a run id (passthrough stub).

    WL-124 stable import surface.
    """
    return run_id or ""


def _resolve_session_id(session_id: str | None) -> str:
    """Resolve a session id (passthrough stub).

    WL-124 stable import surface.
    """
    return session_id or ""


def _normalize_output_format(value: str) -> str:
    """Normalize an output format string.

    WL-124 stable import surface.
    """
    value = value.lower().strip()
    if value in ("json", "jsonl"):
        return "json"
    if value == "csv":
        return "csv"
    if value in ("md", "markdown"):
        return "md"
    return value


def _format_context_usage_line(usage: dict[str, Any]) -> str:
    """Format context usage as a single display line.

    WL-124 stable import surface.
    """
    used = usage.get("tokens", 0)
    limit = usage.get("limit", 0)
    pct = (used / limit * 100) if limit > 0 else 0
    return f"Context: {used:,}/{limit:,} tokens ({pct:.1f}%)"


def _format_grounding_sources_lines(sources: list[dict[str, Any]]) -> list[str]:
    """Format grounding sources as display lines.

    WL-124 stable import surface.
    """
    lines: list[str] = []
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        lines.append(f"[{i}] {title}")
        if url:
            lines.append(f"    {url}")
    return lines


def _format_transcript_summary_line(transcript: dict[str, Any]) -> str:
    """Format a transcript summary line.

    WL-124 stable import surface.
    """
    duration = transcript.get("duration", 0.0)
    word_count = transcript.get("word_count", 0)
    return f"Transcript ({duration:.1f}s, {word_count} words)"


def _scope_key(scope: str, key: str) -> str:
    """Compose a scoped key.

    WL-124 stable import surface.
    """
    return f"{scope}:{key}"


def _compose_owner_tag(
    user: str,
    cwd: Path,
    scope: str | None = None,
) -> str:
    """Compose the owner tag for a session.

    WL-124 stable import surface.
    """
    base = f"{user}:{cwd.name}"
    if scope:
        scope = scope.replace("{pid}", str(os.getpid()))
        scope = scope.replace("{cwd}", cwd.name)
        return f"{base}:{scope}"
    return base


def _inject_skill_instructions(prompt: str, skills: list[str]) -> str:
    """Inject skill instructions into a prompt.

    WL-124 stable import surface.
    """
    if not skills:
        return prompt
    skill_section = "\n\nSkills available:\n" + "\n".join(f"- {s}" for s in skills)
    return prompt + skill_section


def _get_health_targets_path() -> Path:
    """Get the path to the health targets file.

    WL-124 stable import surface.
    """
    return Path(
        os.environ.get("THGENT_HEALTH_TARGETS", "/tmp/thegent/health_targets.yaml")
    )


def _health_targets_exists() -> bool:
    """Check whether the health targets file exists.

    WL-124 stable import surface.
    """
    return _get_health_targets_path().exists()


def _bootstrap_metric_contracts() -> dict[str, Any]:
    """Bootstrap metric contracts (stub).

    WL-124 stable import surface.
    """
    return {"contracts": []}


def _safe_dict(value: Any) -> dict[str, Any]:
    """Coerce a value into a dict, returning empty dict on failure.

    WL-124 stable import surface.
    """
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value: Any) -> list[Any]:
    """Coerce a value into a list, returning empty list on failure.

    WL-124 stable import surface.
    """
    if isinstance(value, list):
        return value
    return []


def _load_artifact(path: str | Path) -> dict[str, Any]:
    """Load an artifact from disk.

    WL-124 stable import surface.
    """
    import json

    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


_HEALTH_TARGETS_TEMPLATE: str = """# Health targets template (WL-124 stable import surface)
structural_budget_pct: 5.0
semantic_budget_pct: 10.0
fallback_rate_threshold: 0.1
"""

_METRIC_CONTRACTS_TEMPLATE: str = """# Metric contracts template (WL-124 stable import surface)
contracts: []
"""


def _atomic_write(path: Path, content: str, **kw: Any) -> None:
    """Atomic write helper (WL-124 stable import surface)."""
    from thegent.cli.commands.dag_impl import _atomic_write as _impl

    _impl(path, content, **kw)


def _serialize_health_report_md(results: list[dict]) -> str:
    """Serialize health report results to Markdown format."""
    from thegent.cli.commands.session_health_report_impl import (
        _serialize_health_report_md as _impl,
    )

    return _impl(results)


def _write_health_trend_export(
    path: Path,
    result: dict[str, Any],
    fmt: str,
    *,
    overwrite: bool = False,
) -> str:
    """Write health trend export to *path* in the given *fmt*.

    Returns the format string on success. Raises ``typer.BadParameter``
    for invalid paths or missing overwrite.
    """
    import typer as _typer

    p = Path(path)
    if p.is_dir():
        raise _typer.BadParameter(f"{p} is a directory")
    if p.exists() and not overwrite:
        raise _typer.BadParameter(f"{p} already exists")
    p.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "md":
        lines = ["# Health Trend\n"]
        for k, v in result.items():
            lines.append(f"**{k}**: {v}")
        p.write_text("\n".join(lines), encoding="utf-8")
    elif fmt == "csv":
        import csv as _csv

        with p.open("w", newline="", encoding="utf-8") as fh:
            writer = _csv.writer(fh)
            writer.writerow(["key", "value"])
            for k, v in result.items():
                writer.writerow([k, v])
    else:  # json / jsonl
        import orjson as _orjson

        p.write_text(
            _orjson.dumps(result, option=_orjson.OPT_INDENT_2).decode(),
            encoding="utf-8",
        )
        fmt = "json"
    return fmt


__all__ = [
    "console",
    "ThegentSettings",
    "RunRegistry",
    "_lazy_import",
    "_resolve_run_id",
    "_resolve_session_id",
    "_normalize_output_format",
    "EXIT_TIMEOUT",
    "EXIT_HEALTH_GATE_FAILED",
    "_format_context_usage_line",
    "_format_grounding_sources_lines",
    "_format_transcript_summary_line",
    "_scope_key",
    "_compose_owner_tag",
    "_inject_skill_instructions",
    "_get_health_targets_path",
    "_health_targets_exists",
    "_bootstrap_metric_contracts",
    "_safe_dict",
    "_safe_list",
    "_load_artifact",
    "_HEALTH_TARGETS_TEMPLATE",
    "_METRIC_CONTRACTS_TEMPLATE",
    "get_session_dir",
    "resolve_owner_dir",
    "_atomic_write",
    "_serialize_health_report_md",
    "_write_health_trend_export",
]
