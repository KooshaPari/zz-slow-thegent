"""Smart session pruner (AUDIT-N+39 hardened).

Implements the Triple-Lock evaluation:

  1. Idle lock:  ``snap.idle_count >= IDLE_COUNT_THRESHOLD``
  2. Completion lock: agent output ends with a completion marker
     (``Task finished``, ``completed successfully``, ``Task
     complete.``, ``[done]``, ``Migration successful.``, ``Cursor
     turned off``, etc.)
  3. Docs lock: at least one ``*.md`` under ``<project_root>/docs/research/``
     (or ``<project_root>/docs/``) was modified after the cycle
     ``start_time``.

A protected-process guard (``_is_protected_process``) is enforced
before any side-effect. ``run_cycle`` is the cycle entry point and
returns ``{pruned, kept, dry_run}``. ``mcp_prune`` (from
``thegent.orchestration.pruning.prune``) is the actual side-effect;
it re-checks the guard before killing anything.
"""

from __future__ import annotations

import contextlib
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Lazy module-level attribute lookup for ``ThegentSettings`` /
# ``ps_impl`` / ``list_tmux_panes`` / ``capture_tmux_pane`` so tests
# can ``patch("thegent.orchestration.pruning.smart_prune.ThegentSettings")``
# even though we do not import these symbols at module load time.
def __getattr__(name: str) -> Any:
    """Resolve optional module-level attributes lazily."""
    if name == "ThegentSettings":
        try:
            from thegent.config.settings import ThegentSettings  # type: ignore
        except Exception:  # pragma: no cover - import guard
            ThegentSettings = None  # type: ignore
        return ThegentSettings
    if name == "ps_impl":
        try:
            from thegent.cli.commands.impl import ps_impl  # type: ignore
        except Exception:

            def ps_impl(**_kw: Any) -> list[dict[str, Any]]:
                return []

        return ps_impl
    if name in {"list_tmux_panes", "capture_tmux_pane"}:
        try:
            from thegent.skills import terminal as _term  # type: ignore

            if name == "list_tmux_panes":
                return _term.list_tmux_panes
            return _term.capture_tmux_pane
        except Exception:
            if name == "list_tmux_panes":

                def list_tmux_panes() -> list[str]:
                    return []

                return list_tmux_panes

            def capture_tmux_pane(_pane: str) -> str:
                return ""

            return capture_tmux_pane
    raise AttributeError(
        f"module 'thegent.orchestration.pruning.smart_prune' has no attribute {name!r}"
    )


IDLE_COUNT_THRESHOLD = 10
IDLE_THRESHOLD_SECONDS = 300
PROTECTED_PROCESS_NAMES: list[str] = [
    "cursor-agent",
    "claude",
    "codex",
    "droid",
    "thegent",
    "bash",
    "zsh",
    "ghostty",
    "terminal",
    "iterm",
]


_COMPLETION_MARKERS = (
    "Task finished",
    "completed successfully",
    "Task complete",
    "[done]",
    "Migration successful",
    "Cursor turned off",
    "Summary:",
    "Implementation finished",
    "(done)",
)


@dataclass
class SessionSnapshot:
    """Snapshot of session information for pruning."""

    session_id: str
    last_activity: float = 0.0
    owner: str = ""
    # AUDIT-N+39 additions (used by Triple-Lock)
    last_output: str = ""
    last_check_time: float = 0.0
    idle_count: int = 0
    platform: str = ""


__all__ = [
    "IDLE_COUNT_THRESHOLD",
    "IDLE_THRESHOLD_SECONDS",
    "PROTECTED_PROCESS_NAMES",
    "SessionSnapshot",
    "SmartPruner",
    "_is_protected_process",
    "smart_prune_main",
]


class SmartPruner:
    """Smart session pruner implementing Triple-Lock.

    @trace FR-RES-005..FR-RES-015
    """

    def __init__(self, settings: Any = None, project_root: Path | None = None) -> None:
        # Default settings is None; concrete deps are pulled lazily
        # so unit tests can patch them via ``patch(...)``.
        self.settings = settings
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.state_file = self.project_root / ".smart_prune_state.json"
        self.snapshots: dict[str, SessionSnapshot] = {}

    # ------------------------------------------------------------------
    # FR-RES-009 -- protected-process guard
    # ------------------------------------------------------------------

    def should_prune(self, snapshot: SessionSnapshot) -> bool:
        """Legacy single-condition check: pure idle-age."""
        return (time.time() - snapshot.last_activity) > IDLE_THRESHOLD_SECONDS

    def detect_completion(self, output: str) -> bool:
        """Return ``True`` if the last 1000 chars contain a completion marker.

        @trace FR-RES-010
        """
        if not output:
            return False
        tail = output[-1000:]
        tail_lower = tail.lower()
        return any(marker.lower() in tail_lower for marker in _COMPLETION_MARKERS)

    def check_docs_written(self, start_time: float) -> bool:
        """Return ``True`` if any docs/research/*.md was modified after start_time.

        @trace FR-RES-011
        """
        candidates = [
            self.project_root / "docs" / "research",
            self.project_root / "docs",
        ]
        for research_dir in candidates:
            if not research_dir.exists():
                continue
            try:
                for md in research_dir.rglob("*.md"):
                    try:
                        if md.stat().st_mtime >= start_time:
                            return True
                    except OSError:
                        continue
            except OSError:
                continue
        return False

    def check_triple_lock(
        self,
        snap: SessionSnapshot,
        output: str,
        start_time: float,
        now: float,
    ) -> tuple[bool, bool, bool]:
        """Triple-Lock evaluation.

        @trace FR-RES-012
        """
        is_idle = snap.idle_count >= IDLE_COUNT_THRESHOLD
        is_complete = self.detect_completion(output)
        docs = self.check_docs_written(start_time)
        return is_idle, is_complete, docs

    # ------------------------------------------------------------------
    # FR-RES-013 -- run_cycle
    # ------------------------------------------------------------------

    def _get_output(self, session: dict[str, Any]) -> str:
        """Capture the latest pane output for a session, with fallback."""
        snap = self.snapshots.get(session.get("id", ""))
        if snap and snap.last_output:
            return snap.last_output
        try:
            from thegent.skills.terminal import capture_tmux_pane  # type: ignore
        except Exception:
            return ""
        try:
            pane = session.get("tty") or session.get("pane")
            if not pane:
                return ""
            return str(capture_tmux_pane(pane) or "")
        except Exception:
            return ""

    def _is_eligible(self, session: dict[str, Any]) -> bool:
        """Apply Triple-Lock to ``session``."""
        snap = self.snapshots.get(session.get("id", ""))
        if snap is None:
            return False
        output = self._get_output(session)
        now = time.time()
        is_idle, is_complete, docs = self.check_triple_lock(
            snap,
            output,
            start_time=snap.last_check_time,
            now=now,
        )
        return is_idle and is_complete and docs

    def _prune_session(
        self, session: dict[str, Any], pane: str | None = None
    ) -> dict[str, Any]:
        """Belt-and-suspenders: re-check guard, then mcp_prune."""
        agent = str(session.get("agent", ""))
        if _is_protected_process(agent):
            return {"status": "skipped", "reason": "protected_process", "agent": agent}
        # Local import keeps smart_prune importable without prune.mcp_prune
        from thegent.orchestration.pruning.prune import mcp_prune  # noqa: PLC0415

        return mcp_prune(session, pane=pane)

    def run_cycle(
        self,
        force_prune: bool = False,
        reprompt: bool = False,
        dry_run: bool = False,
        yes: bool = False,
    ) -> dict[str, Any]:
        """Run one prune cycle.

        @trace FR-RES-013

        Returns ``{pruned, kept, dry_run, error?}``.
        """
        # Use module-level attribute access so unit tests can
        # ``patch("thegent.orchestration.pruning.smart_prune.ps_impl")``
        # and the patched value is picked up at call time.
        import thegent.orchestration.pruning.smart_prune as _mod

        ps_impl = getattr(_mod, "ps_impl", lambda **_kw: [])
        list_tmux_panes = getattr(_mod, "list_tmux_panes", list)
        capture_tmux_pane = getattr(_mod, "capture_tmux_pane", lambda _pane: "")

        try:
            sessions = list(ps_impl() or [])
        except Exception:
            sessions = []
        with contextlib.suppress(Exception):
            list(list_tmux_panes() or [])

        results: dict[str, Any] = {"pruned": 0, "kept": 0, "dry_run": bool(dry_run)}
        for session in sessions:
            sid = session.get("id") or session.get("pid")
            agent = str(session.get("agent", ""))
            if _is_protected_process(agent):
                results["kept"] = int(results["kept"]) + 1
                continue

            # Refresh pane output via capture_tmux_pane (no-op when no pane).
            pane = session.get("tty") or session.get("pane")
            if pane:
                try:
                    self.snapshots.setdefault(
                        str(sid),
                        SessionSnapshot(session_id=str(sid)),
                    )
                    captured = str(capture_tmux_pane(pane) or "")
                    if captured:
                        snap = self.snapshots[str(sid)]
                        snap.last_output = captured
                        snap.last_check_time = time.time()
                except Exception:
                    pass

            eligible = force_prune and yes and self._is_eligible(session)
            if not eligible:
                results["kept"] = int(results["kept"]) + 1
                continue
            if dry_run:
                continue
            self._prune_session(session, pane=pane)
            results["pruned"] = int(results["pruned"]) + 1

        # reprompt hint (kept as a no-op side channel for future use)
        if reprompt:
            results["reprompt"] = True

        return results


def _is_protected_process(process_name: str) -> bool:
    """Return ``True`` when ``process_name`` matches a protected agent.

    @trace FR-RES-009

    Matching is case-insensitive substring against
    ``PROTECTED_PROCESS_NAMES``. An empty input returns ``False``.
    """
    if not process_name:
        return False
    lowered = process_name.lower()
    return any(protected.lower() in lowered for protected in PROTECTED_PROCESS_NAMES)


def smart_prune_main(
    force: bool = False,
    reprompt: bool = False,
    dry_run: bool = False,
    yes: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience entry point mirroring the legacy CLI surface.

    @trace FR-RES-014
    """
    try:
        from thegent.config.settings import ThegentSettings  # type: ignore
    except Exception:
        ThegentSettings = None  # type: ignore

    try:
        settings = ThegentSettings() if ThegentSettings else None
    except Exception:
        settings = None

    pruner = SmartPruner(settings=settings)
    return pruner.run_cycle(
        force_prune=force,
        reprompt=reprompt,
        dry_run=dry_run,
        yes=yes,
    )
