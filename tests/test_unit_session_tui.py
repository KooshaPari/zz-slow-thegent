"""Unit tests for SessionTUI degraded diagnostics behavior."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import patch

import psutil
import pytest
from rich.console import Console

from thegent.ux.session_tui import SessionTUI


@pytest.mark.unit
def test_subagent_probe_failure_sets_degraded_diagnostics() -> None:
    tui = SessionTUI()

    with (
        patch(
            "thegent.ux.session_tui.session_meta_impl",
            return_value={"pid": 123, "status": "running"},
        ),
        patch("thegent.ux.session_tui._is_pid_running", return_value=True),
        patch(
            "thegent.ux.session_tui.psutil.Process",
            side_effect=psutil.AccessDenied(pid=123),
        ),
        patch(
            "thegent.ux.session_tui._find_session_meta",
            return_value=Path("/tmp/sess-1.json"),
        ),
    ):
        details = tui._get_session_details("sess-1")

    assert details.get("degraded") is True
    diagnostics = details.get("diagnostics", {})
    assert diagnostics["subagents"]["component"] == "subagents"
    assert diagnostics["subagents"]["session_id"] == "sess-1"


@pytest.mark.unit
def test_subagent_probe_success_returns_entries_without_degraded_state() -> None:
    tui = SessionTUI()

    class _ChildProc:
        pid = 222

        def ppid(self) -> int:
            return 123

        def cmdline(self) -> list[str]:
            return ["codex", "worker", "--lane"]

        def cpu_percent(self, interval: float = 0.1) -> float:
            return 1.5

        def memory_info(self) -> object:
            return type("Mem", (), {"rss": 10 * 1024 * 1024})()

        def status(self) -> str:
            return "running"

        def num_fds(self) -> int:
            return 8

        def create_time(self) -> float:
            return 1_700_000_000.0

    class _ParentProc:
        def children(self, recursive: bool = True) -> list[_ChildProc]:
            return [_ChildProc()]

    with (
        patch(
            "thegent.ux.session_tui.session_meta_impl",
            return_value={"pid": 123, "status": "running"},
        ),
        patch("thegent.ux.session_tui._is_pid_running", return_value=True),
        patch("thegent.ux.session_tui.psutil.Process", return_value=_ParentProc()),
        patch(
            "thegent.ux.session_tui._find_session_meta",
            return_value=Path("/tmp/sess-1.json"),
        ),
    ):
        details = tui._get_session_details("sess-1")

    assert details.get("degraded") is None
    assert details["subagents"]
    assert details["subagents"][0]["pid"] == 222
    assert details["subagents"][0]["agent"] == "codex"


def test_render_sessions_list_marks_subagent_probe_failures() -> None:
    tui = SessionTUI()

    with (
        patch(
            "thegent.ux.session_tui.ps_impl",
            return_value=[
                {
                    "id": "sess-fail",
                    "status": "running",
                    "agent": "dex",
                    "pid": 333,
                    "prompt_preview": "running work",
                }
            ],
        ),
        patch(
            "thegent.ux.session_tui.session_meta_impl",
            return_value={"pid": 333, "status": "running"},
        ),
        patch("thegent.ux.session_tui._is_pid_running", return_value=True),
        patch(
            "thegent.ux.session_tui.psutil.Process",
            side_effect=psutil.AccessDenied(pid=333),
        ),
    ):
        layout = tui.render_sessions_list()

    panel = layout["main"].renderable
    stream = StringIO()
    console = Console(file=stream, width=120)
    console.print(panel)
    assert "ERR" in stream.getvalue()


@pytest.mark.unit
def test_log_path_resolution_failure_sets_degraded_diagnostics() -> None:
    tui = SessionTUI()

    with (
        patch(
            "thegent.ux.session_tui.session_meta_impl",
            return_value={"pid": 0, "status": "exited"},
        ),
        patch.object(SessionTUI, "_get_subagents_for_session", return_value=[]),
        patch(
            "thegent.ux.session_tui._find_session_meta",
            side_effect=RuntimeError("bad meta path"),
        ),
    ):
        details = tui._get_session_details("sess-2")

    assert details.get("degraded") is True
    diagnostics = details.get("diagnostics", {})
    assert diagnostics["log_paths"]["component"] == "log_paths"
    assert diagnostics["log_paths"]["session_id"] == "sess-2"


def test_subagent_enumeration_failure_records_metadata_error() -> None:
    tui = SessionTUI()

    with patch("thegent.ux.session_tui.session_meta_impl", return_value={"error": "missing"}):
        subagents = tui._get_subagents_for_session("sess-4")

    assert subagents == []
    assert tui._last_diag is not None
    diagnostics = tui._last_diag
    assert diagnostics["failure_type"] == "metadata_error"
    assert diagnostics["error_message"] == "missing"
    assert diagnostics["session_id"] == "sess-4"


@pytest.mark.unit
def test_render_session_view_shows_degraded_badge() -> None:
    tui = SessionTUI()

    with patch.object(
        SessionTUI,
        "_get_session_details",
        return_value={
            "status": "running",
            "agent": "dex",
            "pid": 101,
            "degraded": True,
            "subagents": [],
        },
    ):
        layout = tui.render_session_view("sess-3")

    header_panel = layout["header"].renderable
    assert "DEGRADED" in str(header_panel.renderable)
