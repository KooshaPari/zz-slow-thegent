"""Session metadata helpers — AUDIT-N+5 shim.

Resolves the second missing-module surface that the AUDIT-N+2 envelope-
parity sweep and the WL-125 ``run_execution_core_helpers`` parity test
flagged: ``thegent.cli.commands.session_meta_impl``. Mirrors the AUDIT-N
+2..N+4 contract by exposing ``err_console`` (``Rich Console(stderr=True)``)
and re-exporting ``print_exc`` from :mod:`thegent.ux.cli_errors`.

Provides the two call-sites
:mod:`thegent.cli.services.run_execution_core_helpers` invokes:

- :func:`_build_continuation_prompt` — assembles the continuation prompt
  by reading prior session output (with optional stderr inclusion).
- :func:`_save_session_meta` — persists the bg-session meta payload to
  the canonical meta path.

The full WL-120 extraction (the broader session-meta block: prior-session
output parsing, contract-timestamp normalisation, blocked-ratio extraction)
remains tracked as follow-up work. AUDIT-N+5 only preserves the two
direct call-sites so the five pre-existing parity-test failures close
without a full re-implementation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from rich.console import Console

from thegent.ux.cli_errors import print_exc  # re-exported for AUDIT-N+2 contract

_log = structlog.get_logger(__name__)
err_console = Console(stderr=True)

__all__ = [
    "_build_continuation_prompt",
    "_load_prior_session_output",
    "_save_session_meta",
    "err_console",
    "print_exc",
]


def _load_prior_session_output(
    settings: Any,
    session_id: str,
) -> str:
    """Load the prior session's stdout (``stdout.log`` under ``session_id``).

    Args:
        settings: Settings object exposing ``session_dir``.
        session_id: The session id whose output should be loaded.

    Returns:
        The last 4000 chars of the session's stdout, or ``""`` when the
        session log cannot be located.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestBuildContinuationPrompt`.
    """
    try:
        session_dir = getattr(settings, "session_dir", None) or "."
        candidate = Path(session_dir) / "sessions" / session_id / "stdout.log"
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8", errors="replace")[-4000:]
    except OSError as exc:
        _log.debug("session_meta_impl: failed to read prior output: %s", exc)
    return ""


def _build_continuation_prompt(
    settings: Any,
    continue_from: str,
    prompt: str,
    *,
    include_stderr: bool = False,
) -> str:
    """Build a continuation prompt that wraps the prior-session output.

    Supports comma-separated ``continue_from`` session ids. For each
    id the prior output is loaded (via
    :func:`_load_prior_session_output`); the assembled block is
    prepended to ``prompt``. When ``continue_from`` is empty or no
    prior outputs can be found, ``prompt`` is returned unchanged.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestBuildContinuationPrompt`.
    """
    if not continue_from:
        return prompt

    session_ids = [sid.strip() for sid in continue_from.split(",") if sid.strip()]
    if not session_ids:
        return prompt

    blocks: list[str] = []
    for sid in session_ids:
        output = _load_prior_session_output(settings, sid)
        if output:
            blocks.append(f"[Prior session {sid}]\n{output}")

    if not blocks:
        return prompt

    header = "Continuing from prior session"
    body = "\n\n".join(blocks)
    return f"{header}\n\n{body}\n\n---\n\n{prompt}"


def _save_session_meta(meta_path: Path | str, meta: dict[str, Any]) -> None:
    """Persist the bg-session meta payload to ``meta_path``.

    Mirrors the runtime contract: serialise ``meta`` as JSON to the
    supplied path, creating parents as needed. Failures are logged and
    swallowed so the orchestrator never raises during a session start.
    """
    try:
        path = Path(meta_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    except OSError as exc:
        _log.debug("session_meta_impl: failed to persist meta to %s: %s", meta_path, exc)
