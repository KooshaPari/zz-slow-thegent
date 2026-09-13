"""Orchestration oversight module (AUDIT-N+39 hardened).

Tracks per-agent attempt counters persisted under
``<root>/.oversight/<agent>.json`` and exposes a simple
threshold-ladder action picker (``continue`` / ``pause`` /
``escalate``).
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

__all__ = [
    "DEFAULT_THRESHOLD",
    "get_oversight_action",
    "record_oversight_event",
    "should_trigger_oversight",
]


DEFAULT_THRESHOLD = 3


def _state_file(root: Path, agent: str) -> Path:
    safe = agent.replace("/", "_").replace(os.sep, "_")
    return root / ".oversight" / f"{safe}.json"


def _load_state(root: Path, agent: str) -> dict[str, Any]:
    f = _state_file(root, agent)
    if not f.exists():
        return {"agent": agent, "attempts": 0}
    try:
        return json.loads(f.read_text())
    except (OSError, json.JSONDecodeError):
        return {"agent": agent, "attempts": 0}


def _save_state(root: Path, agent: str, state: dict[str, Any]) -> None:
    f = _state_file(root, agent)
    f.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=f.parent, prefix=".oversight_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(state, fh)
        os.replace(tmp, f)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def should_trigger_oversight(
    path: Path,
    agent: str,
    attempts: int,
    threshold: int = DEFAULT_THRESHOLD,
) -> bool:
    """Return ``True`` when ``attempts >= threshold``.

    @trace FR-RES-005

    Note: does NOT persist; use ``record_oversight_event`` for that.
    """
    return attempts >= threshold


def record_oversight_event(
    path: Path,
    agent: str,
    attempts: int,
) -> dict[str, Any]:
    """Persist ``attempts`` for ``agent`` under ``<path>/.oversight/``.

    @trace FR-RES-005 (persistence arm)
    """
    state = {"agent": agent, "attempts": attempts}
    _save_state(path, agent, state)
    return state


def get_oversight_action(
    agent: int | str,
    context: dict[str, Any] | None = None,
) -> str:
    """Return the action label for the given escalation level.

    @trace FR-RES-006

    Ladder:
      * ``agent < 3``   -> ``"continue"``
      * ``3 <= agent < 5`` -> ``"pause"``
      * ``agent >= 5``  -> ``"escalate"``

    If ``context`` supplies ``forced_action`` and it is one of the
    three valid labels, that label is returned verbatim.
    """
    if context and isinstance(context, dict):
        forced = context.get("forced_action")
        if forced in {"continue", "pause", "escalate"}:
            return str(forced)
    if isinstance(agent, int):
        if agent >= 5:
            return "escalate"
        if agent >= 3:
            return "pause"
        return "continue"
    # String agent: derive a numeric level from the string length
    level = len(str(agent))
    if level >= 5:
        return "escalate"
    if level >= 3:
        return "pause"
    return "continue"
