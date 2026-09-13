"""Tests for SimulationReplayEngine.

Covers: load_session, replay, replay_from_event, compare_sessions,
        extract_tool_calls, generate_test_fixture, list_sessions,
        and related helpers.

# @trace FR-REPLAY-001, FR-REPLAY-002, FR-REPLAY-003, FR-REPLAY-004, FR-REPLAY-005
"""

from __future__ import annotations

import ast
import time
from pathlib import Path

import orjson as json
import pytest

from thegent.simulation.replay import (
    ReplayEvent,
    ReplaySession,
    SimulationReplayEngine,
    _event_to_dict,
    _parse_iso_to_float,
    _safe_repr,
    _try_parse_json,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_meta(tmp_path: Path, session_id: str = "sess-001", **extra) -> dict:
    """Build a minimal session metadata dict and write it to tmp_path."""
    meta = {
        "session_id": session_id,
        "agent": "copilot",
        "mode": "write",
        "status": "running",
        "started_at_utc": "2026-02-19T22:00:00.000000+00:00",
        "paths": {
            "stdout": str(tmp_path / f"{session_id}.stdout.log"),
            "stderr": str(tmp_path / f"{session_id}.stderr.log"),
        },
        **extra,
    }
    (tmp_path / f"{session_id}.json").write_text(json.dumps(meta).decode(), encoding="utf-8")
    return meta


def _make_engine(tmp_path: Path) -> SimulationReplayEngine:
    return SimulationReplayEngine(sessions_root=tmp_path)


# ---------------------------------------------------------------------------
# Test 1: load_session basic happy path
# ---------------------------------------------------------------------------


def test_load_session_returns_replay_session(tmp_path: Path) -> None:
    """FR-REPLAY-001: load_session returns a ReplaySession with correct session_id."""
    _make_meta(tmp_path, session_id="s1")
    engine = _make_engine(tmp_path)
    session = engine.load_session(tmp_path / "s1.json")
    assert isinstance(session, ReplaySession)
    assert session.session_id == "s1"


# ---------------------------------------------------------------------------
# Test 2: load_session populates metadata
# ---------------------------------------------------------------------------


def test_load_session_metadata(tmp_path: Path) -> None:
    """FR-REPLAY-001: load_session stores raw metadata in session.metadata."""
    _make_meta(tmp_path, session_id="s2", agent="gemini")
    engine = _make_engine(tmp_path)
    session = engine.load_session(tmp_path / "s2.json")
    assert session.metadata["agent"] == "gemini"


# ---------------------------------------------------------------------------
# Test 3: load_session raises FileNotFoundError for missing file
# ---------------------------------------------------------------------------


def test_load_session_missing_file(tmp_path: Path) -> None:
    """FR-REPLAY-001: load_session raises FileNotFoundError for absent file."""
    engine = _make_engine(tmp_path)
    with pytest.raises(FileNotFoundError):
        engine.load_session(tmp_path / "nonexistent.json")


# ---------------------------------------------------------------------------
# Test 4: load_session raises ValueError for invalid JSON
# ---------------------------------------------------------------------------


def test_load_session_invalid_json(tmp_path: Path) -> None:
    """FR-REPLAY-001: load_session raises ValueError on malformed JSON."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not-valid-json", encoding="utf-8")
    engine = _make_engine(tmp_path)
    with pytest.raises(ValueError, match="Cannot parse"):
        engine.load_session(bad)


# ---------------------------------------------------------------------------
# Test 5: load_session raises ValueError when session_id missing
# ---------------------------------------------------------------------------


def test_load_session_missing_session_id(tmp_path: Path) -> None:
    """FR-REPLAY-001: load_session raises ValueError when session_id absent."""
    no_id = tmp_path / "noid.json"
    no_id.write_text(json.dumps({"agent": "x"}).decode(), encoding="utf-8")
    engine = _make_engine(tmp_path)
    with pytest.raises(ValueError, match="missing 'session_id'"):
        engine.load_session(no_id)


# ---------------------------------------------------------------------------
# Test 6: load_session synthesises at least one event from metadata
# ---------------------------------------------------------------------------


def test_load_session_synthesises_events(tmp_path: Path) -> None:
    """FR-REPLAY-001: events are synthesised (at least 1) from session meta."""
    _make_meta(tmp_path, session_id="s6")
    engine = _make_engine(tmp_path)
    session = engine.load_session(tmp_path / "s6.json")
    assert len(session.events) >= 1


# ---------------------------------------------------------------------------
# Test 7: load_session parses stdout log
# ---------------------------------------------------------------------------


def test_load_session_parses_stdout_log(tmp_path: Path) -> None:
    """FR-REPLAY-001: events from stdout log are included in the session."""
    meta = _make_meta(tmp_path, session_id="s7")
    stdout = Path(meta["paths"]["stdout"])
    stdout.write_text("Hello world\nSecond line\n", encoding="utf-8")
    engine = _make_engine(tmp_path)
    session = engine.load_session(tmp_path / "s7.json")
    event_types = [e.event_type for e in session.events]
    assert "response" in event_types


# ---------------------------------------------------------------------------
# Test 8: load_session parses tool-call lines
# ---------------------------------------------------------------------------


def test_load_session_parses_tool_call_lines(tmp_path: Path) -> None:
    """FR-REPLAY-005: TOOL_CALL: lines become tool_call events."""
    meta = _make_meta(tmp_path, session_id="s8")
    stdout = Path(meta["paths"]["stdout"])
    stdout.write_text(
        'TOOL_CALL: {"tool": "read_file", "args": {"path": "/tmp/x"}}\n',
        encoding="utf-8",
    )
    engine = _make_engine(tmp_path)
    session = engine.load_session(tmp_path / "s8.json")
    tool_calls = [e for e in session.events if e.event_type == "tool_call"]
    assert len(tool_calls) == 1
    assert tool_calls[0].data["tool"] == "read_file"


# ---------------------------------------------------------------------------
# Test 9: load_session parses error lines from stderr
# ---------------------------------------------------------------------------


def test_load_session_parses_error_lines(tmp_path: Path) -> None:
    """FR-REPLAY-001: Error: lines in stderr become error events."""
    meta = _make_meta(tmp_path, session_id="s9")
    stderr = Path(meta["paths"]["stderr"])
    stderr.write_text("Error: something went wrong\n", encoding="utf-8")
    engine = _make_engine(tmp_path)
    session = engine.load_session(tmp_path / "s9.json")
    error_events = [e for e in session.events if e.event_type == "error"]
    assert len(error_events) >= 1


# ---------------------------------------------------------------------------
# Test 10: replay yields events in timestamp order
# ---------------------------------------------------------------------------


def test_replay_yields_in_order(tmp_path: Path) -> None:
    """FR-REPLAY-002: replay() yields events in ascending timestamp order."""
    events = [
        ReplayEvent(timestamp=2.0, event_type="response", data={"idx": 2}),
        ReplayEvent(timestamp=0.5, event_type="state_change", data={"idx": 0}),
        ReplayEvent(timestamp=1.0, event_type="tool_call", data={"idx": 1}),
    ]
    session = ReplaySession(session_id="order-test", events=events)
    engine = _make_engine(tmp_path)
    result = list(engine.replay(session, speed=0))
    timestamps = [e.timestamp for e in result]
    assert timestamps == sorted(timestamps)


# ---------------------------------------------------------------------------
# Test 11: replay with speed=0 does not sleep
# ---------------------------------------------------------------------------


def test_replay_no_sleep_when_speed_zero(tmp_path: Path) -> None:
    """FR-REPLAY-002: replay(speed=0) finishes near-instantly."""
    events = [ReplayEvent(timestamp=float(i), event_type="response", data={}) for i in range(5)]
    session = ReplaySession(session_id="speed-zero", events=events)
    engine = _make_engine(tmp_path)
    start = time.monotonic()
    list(engine.replay(session, speed=0))
    elapsed = time.monotonic() - start
    assert elapsed < 1.0, f"Replay took {elapsed:.2f}s with speed=0"


# ---------------------------------------------------------------------------
# Test 12: replay yields all events
# ---------------------------------------------------------------------------


def test_replay_yields_all_events(tmp_path: Path) -> None:
    """FR-REPLAY-002: replay() yields every event exactly once."""
    n = 7
    events = [ReplayEvent(timestamp=float(i), event_type="response", data={}) for i in range(n)]
    session = ReplaySession(session_id="all-events", events=events)
    engine = _make_engine(tmp_path)
    result = list(engine.replay(session, speed=0))
    assert len(result) == n


# ---------------------------------------------------------------------------
# Test 13: replay on empty session yields nothing
# ---------------------------------------------------------------------------


def test_replay_empty_session(tmp_path: Path) -> None:
    """FR-REPLAY-002: replay() on an empty session yields no events."""
    session = ReplaySession(session_id="empty", events=[])
    engine = _make_engine(tmp_path)
    result = list(engine.replay(session, speed=0))
    assert result == []


# ---------------------------------------------------------------------------
# Test 14: replay_from_event starts at correct index
# ---------------------------------------------------------------------------


def test_replay_from_event_starts_at_index(tmp_path: Path) -> None:
    """FR-REPLAY-002: replay_from_event(idx=2) skips the first 2 events."""
    events = [ReplayEvent(timestamp=float(i), event_type="response", data={"n": i}) for i in range(5)]
    session = ReplaySession(session_id="from-event", events=events)
    engine = _make_engine(tmp_path)
    result = list(engine.replay_from_event(session, 2))
    assert len(result) == 3
    assert result[0].data["n"] == 2


# ---------------------------------------------------------------------------
# Test 15: replay_from_event raises IndexError for out-of-range index
# ---------------------------------------------------------------------------


def test_replay_from_event_out_of_range(tmp_path: Path) -> None:
    """FR-REPLAY-002: replay_from_event raises IndexError when index >= len(events)."""
    session = ReplaySession(
        session_id="oor",
        events=[ReplayEvent(timestamp=0.0, event_type="response", data={})],
    )
    engine = _make_engine(tmp_path)
    with pytest.raises(IndexError):
        list(engine.replay_from_event(session, 10))


# ---------------------------------------------------------------------------
# Test 16: replay_from_event raises IndexError for negative index
# ---------------------------------------------------------------------------


def test_replay_from_event_negative_index(tmp_path: Path) -> None:
    """FR-REPLAY-002: replay_from_event raises IndexError for negative index."""
    session = ReplaySession(
        session_id="neg",
        events=[ReplayEvent(timestamp=0.0, event_type="response", data={})],
    )
    engine = _make_engine(tmp_path)
    with pytest.raises(IndexError):
        list(engine.replay_from_event(session, -1))


# ---------------------------------------------------------------------------
# Test 17: compare_sessions detects metadata changes
# ---------------------------------------------------------------------------


def test_compare_sessions_metadata_diff(tmp_path: Path) -> None:
    """FR-REPLAY-003: compare_sessions reports changed metadata fields."""
    a = ReplaySession("a", [], metadata={"agent": "copilot", "mode": "read"})
    b = ReplaySession("b", [], metadata={"agent": "gemini", "mode": "read"})
    engine = _make_engine(tmp_path)
    diff = engine.compare_sessions(a, b)
    assert "agent" in diff["metadata_diff"]
    assert diff["metadata_diff"]["agent"]["a"] == "copilot"
    assert diff["metadata_diff"]["agent"]["b"] == "gemini"


# ---------------------------------------------------------------------------
# Test 18: compare_sessions detects added events
# ---------------------------------------------------------------------------


def test_compare_sessions_events_added(tmp_path: Path) -> None:
    """FR-REPLAY-003: compare_sessions reports events added in session B."""
    ev = ReplayEvent(timestamp=1.0, event_type="response", data={})
    a = ReplaySession("a", [])
    b = ReplaySession("b", [ev])
    engine = _make_engine(tmp_path)
    diff = engine.compare_sessions(a, b)
    assert len(diff["events_added"]) == 1
    assert diff["events_removed"] == []


# ---------------------------------------------------------------------------
# Test 19: compare_sessions detects removed events
# ---------------------------------------------------------------------------


def test_compare_sessions_events_removed(tmp_path: Path) -> None:
    """FR-REPLAY-003: compare_sessions reports events removed from session A."""
    ev = ReplayEvent(timestamp=1.0, event_type="response", data={})
    a = ReplaySession("a", [ev])
    b = ReplaySession("b", [])
    engine = _make_engine(tmp_path)
    diff = engine.compare_sessions(a, b)
    assert len(diff["events_removed"]) == 1
    assert diff["events_added"] == []


# ---------------------------------------------------------------------------
# Test 20: compare_sessions detects changed events
# ---------------------------------------------------------------------------


def test_compare_sessions_events_changed(tmp_path: Path) -> None:
    """FR-REPLAY-003: compare_sessions reports positionally matched events that differ."""
    ev_a = ReplayEvent(timestamp=1.0, event_type="response", data={"msg": "hello"})
    ev_b = ReplayEvent(timestamp=1.0, event_type="response", data={"msg": "world"})
    a = ReplaySession("a", [ev_a])
    b = ReplaySession("b", [ev_b])
    engine = _make_engine(tmp_path)
    diff = engine.compare_sessions(a, b)
    assert len(diff["events_changed"]) == 1


# ---------------------------------------------------------------------------
# Test 21: compare_sessions identical sessions
# ---------------------------------------------------------------------------


def test_compare_sessions_identical(tmp_path: Path) -> None:
    """FR-REPLAY-003: compare_sessions reports empty diff for identical sessions."""
    ev = ReplayEvent(timestamp=1.0, event_type="response", data={"x": 1})
    a = ReplaySession("a", [ev], metadata={"agent": "x"})
    b = ReplaySession("a", [ev], metadata={"agent": "x"})
    engine = _make_engine(tmp_path)
    diff = engine.compare_sessions(a, b)
    assert diff["metadata_diff"] == {}
    assert diff["events_changed"] == []
    assert diff["events_added"] == []
    assert diff["events_removed"] == []


# ---------------------------------------------------------------------------
# Test 22: extract_tool_calls returns only tool_call events
# ---------------------------------------------------------------------------


def test_extract_tool_calls_filters_correctly(tmp_path: Path) -> None:
    """FR-REPLAY-005: extract_tool_calls returns only tool_call event data."""
    events = [
        ReplayEvent(timestamp=0.0, event_type="state_change", data={"state": "started"}),
        ReplayEvent(timestamp=1.0, event_type="tool_call", data={"tool": "read_file"}),
        ReplayEvent(timestamp=2.0, event_type="response", data={"content": "..."}),
        ReplayEvent(timestamp=3.0, event_type="tool_call", data={"tool": "write_file"}),
    ]
    session = ReplaySession("tc-test", events)
    engine = _make_engine(tmp_path)
    calls = engine.extract_tool_calls(session)
    assert len(calls) == 2
    assert calls[0]["tool"] == "read_file"
    assert calls[1]["tool"] == "write_file"


# ---------------------------------------------------------------------------
# Test 23: extract_tool_calls returns empty list when no tool calls
# ---------------------------------------------------------------------------


def test_extract_tool_calls_empty(tmp_path: Path) -> None:
    """FR-REPLAY-005: extract_tool_calls returns [] when no tool_call events exist."""
    session = ReplaySession(
        "no-tools",
        [ReplayEvent(timestamp=0.0, event_type="response", data={})],
    )
    engine = _make_engine(tmp_path)
    assert engine.extract_tool_calls(session) == []


# ---------------------------------------------------------------------------
# Test 24: generate_test_fixture creates a valid Python file
# ---------------------------------------------------------------------------


def test_generate_test_fixture_creates_file(tmp_path: Path) -> None:
    """FR-REPLAY-004: generate_test_fixture creates a .py file at the given path."""
    session = ReplaySession(
        session_id="fix-001",
        events=[ReplayEvent(timestamp=1.0, event_type="tool_call", data={"tool": "bash"})],
        metadata={"agent": "copilot"},
    )
    engine = _make_engine(tmp_path)
    out = tmp_path / "fixtures" / "test_fix001.py"
    engine.generate_test_fixture(session, out)
    assert out.exists()


# ---------------------------------------------------------------------------
# Test 25: generate_test_fixture file contains fixture names
# ---------------------------------------------------------------------------


def test_generate_test_fixture_contains_fixtures(tmp_path: Path) -> None:
    """FR-REPLAY-004: generated file contains pytest fixture definitions."""
    session = ReplaySession(
        session_id="fix-002",
        events=[],
        metadata={"mode": "read"},
    )
    engine = _make_engine(tmp_path)
    out = tmp_path / "conftest_fix002.py"
    engine.generate_test_fixture(session, out)
    content = out.read_text(encoding="utf-8")
    assert "def session_metadata" in content
    assert "def replay_events" in content
    assert "def tool_calls" in content
    assert "def replay_session" in content


# ---------------------------------------------------------------------------
# Test 26: generate_test_fixture embeds session_id
# ---------------------------------------------------------------------------


def test_generate_test_fixture_embeds_session_id(tmp_path: Path) -> None:
    """FR-REPLAY-004: generated file embeds the session_id as SESSION_ID constant."""
    session = ReplaySession(session_id="unique-session-42", events=[], metadata={})
    engine = _make_engine(tmp_path)
    out = tmp_path / "fix.py"
    engine.generate_test_fixture(session, out)
    content = out.read_text(encoding="utf-8")
    assert "unique-session-42" in content


# ---------------------------------------------------------------------------
# Test 27: list_sessions returns paths sorted
# ---------------------------------------------------------------------------


def test_list_sessions_sorted(tmp_path: Path) -> None:
    """FR-REPLAY-001: list_sessions returns a sorted list of .json paths."""
    for name in ("c.json", "a.json", "b.json"):
        (tmp_path / name).write_text(json.dumps({"session_id": name}).decode(), encoding="utf-8")
    engine = _make_engine(tmp_path)
    sessions = engine.list_sessions()
    names = [p.name for p in sessions]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# Test 28: list_sessions returns empty list when directory absent
# ---------------------------------------------------------------------------


def test_list_sessions_empty_when_no_root(tmp_path: Path) -> None:
    """FR-REPLAY-001: list_sessions returns [] when sessions_root does not exist."""
    engine = SimulationReplayEngine(sessions_root=tmp_path / "nonexistent")
    assert engine.list_sessions() == []


# ---------------------------------------------------------------------------
# Test 29: _event_to_dict helper
# ---------------------------------------------------------------------------


def test_event_to_dict() -> None:
    """_event_to_dict converts a ReplayEvent to a plain dict."""
    ev = ReplayEvent(timestamp=1.23, event_type="tool_call", data={"k": "v"})
    d = _event_to_dict(ev)
    assert d == {"timestamp": 1.23, "event_type": "tool_call", "data": {"k": "v"}}


# ---------------------------------------------------------------------------
# Test 30: _try_parse_json parses valid JSON
# ---------------------------------------------------------------------------


def test_try_parse_json_valid() -> None:
    """_try_parse_json returns dict for valid JSON object strings."""
    result = _try_parse_json('{"a": 1}')
    assert result == {"a": 1}


# ---------------------------------------------------------------------------
# Test 31: _try_parse_json returns None for invalid JSON
# ---------------------------------------------------------------------------


def test_try_parse_json_invalid() -> None:
    """_try_parse_json returns None for non-JSON strings."""
    assert _try_parse_json("not json") is None


# ---------------------------------------------------------------------------
# Test 32: _parse_iso_to_float parses UTC timestamps
# ---------------------------------------------------------------------------


def test_parse_iso_to_float_valid() -> None:
    """_parse_iso_to_float returns a non-zero float for a valid ISO timestamp."""
    ts = _parse_iso_to_float("2026-02-19T22:00:00.000000+00:00")
    assert isinstance(ts, float)
    assert ts > 0


# ---------------------------------------------------------------------------
# Test 33: _parse_iso_to_float returns 0.0 for garbage input
# ---------------------------------------------------------------------------


def test_parse_iso_to_float_garbage() -> None:
    """_parse_iso_to_float returns 0.0 for unparseable strings."""
    assert _parse_iso_to_float("not-a-date") == 0.0


# ---------------------------------------------------------------------------
# Test 34: _safe_repr produces evaluable Python
# ---------------------------------------------------------------------------


def test_safe_repr_dict() -> None:
    """_safe_repr produces a string that evaluates back to the original object."""
    obj = {"a": [1, 2, 3], "b": None}
    r = _safe_repr(obj)
    assert ast.literal_eval(r) == obj


# ---------------------------------------------------------------------------
# Test 35: compare_sessions tool_calls_diff
# ---------------------------------------------------------------------------


def test_compare_sessions_tool_calls_diff(tmp_path: Path) -> None:
    """FR-REPLAY-003: compare_sessions tool_calls_diff contains added/removed/changed keys."""
    ev_tc_a = ReplayEvent(timestamp=1.0, event_type="tool_call", data={"tool": "read"})
    ev_tc_b1 = ReplayEvent(timestamp=1.0, event_type="tool_call", data={"tool": "write"})
    ev_tc_b2 = ReplayEvent(timestamp=2.0, event_type="tool_call", data={"tool": "bash"})
    a = ReplaySession("a", [ev_tc_a])
    b = ReplaySession("b", [ev_tc_b1, ev_tc_b2])
    engine = _make_engine(tmp_path)
    diff = engine.compare_sessions(a, b)
    tc = diff["tool_calls_diff"]
    assert "added" in tc
    assert "removed" in tc
    assert "changed" in tc
    # 1 changed (idx 0 differs), 1 added (idx 1 in B)
    assert len(tc["added"]) == 1
    assert len(tc["changed"]) == 1
