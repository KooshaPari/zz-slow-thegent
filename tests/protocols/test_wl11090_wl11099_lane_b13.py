"""Lane B13 regressions for WL-11090..WL-11099 on turn/submit parse/execution/side-effect helpers."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl11090_resolve_turn_submit_parse_error_returns_none_for_non_dict_payload() -> None:
    # @trace WL-11090
    assert server._resolve_turn_submit_parse_error({"parse_error": "bad"}) is None


def test_wl11091_build_turn_submit_parse_phase_preserves_plan_fields() -> None:
    # @trace WL-11091
    plan = {
        "parse_error": None,
        "session_id": "session-1",
        "session": {"id": "session-1"},
        "user_input": "hello",
        "requires_approval": True,
        "approval_diff": "--- a\n+++ b",
    }
    phase = server._build_turn_submit_parse_phase(plan)
    assert phase["parse_error"] is None
    assert phase["session_id"] == "session-1"
    assert phase["session"] == {"id": "session-1"}
    assert phase["user_input"] == "hello"
    assert phase["requires_approval"] is True
    assert phase["approval_diff"] == "--- a\n+++ b"


def test_wl11092_resolve_turn_submit_execution_target_returns_expected_tuple() -> None:
    # @trace WL-11092
    target = server._resolve_turn_submit_execution_target(
        {
            "session_id": "session-1",
            "session": {"id": "session-1"},
            "user_input": "hello",
            "requires_approval": False,
            "approval_diff": None,
        }
    )
    assert target == ("session-1", {"id": "session-1"}, "hello", False, None)


def test_wl11093_resolve_turn_submit_execution_target_rejects_non_bool_requires_approval() -> None:
    # @trace WL-11093
    with pytest.raises(ValueError, match="Turn submit execution target unresolved"):
        server._resolve_turn_submit_execution_target(
            {
                "session_id": "session-1",
                "session": {"id": "session-1"},
                "user_input": "hello",
                "requires_approval": "yes",
                "approval_diff": None,
            }
        )


def test_wl11094_resolve_turn_submit_commit_target_returns_expected_tuple() -> None:
    # @trace WL-11094
    turn = {"id": "turn-1"}
    session = {"id": "session-1", "turn_ids": []}
    assert server._resolve_turn_submit_commit_target({"turn_id": "turn-1", "turn": turn, "session": session}) == (
        "turn-1",
        turn,
        session,
    )


def test_wl11095_resolve_turn_submit_commit_target_rejects_non_dict_session() -> None:
    # @trace WL-11095
    with pytest.raises(ValueError, match="Turn submit commit target unresolved"):
        server._resolve_turn_submit_commit_target({"turn_id": "turn-1", "turn": {"id": "turn-1"}, "session": "bad"})


def test_wl11096_resolve_turn_submit_side_effects_target_returns_expected_tuple() -> None:
    # @trace WL-11096
    turn = {"id": "turn-1"}
    phase = {
        "session_id": "session-1",
        "turn_id": "turn-1",
        "turn": turn,
        "user_input": "hello",
        "requires_approval": True,
        "approval_diff": "--- a\n+++ b",
    }
    assert server._resolve_turn_submit_side_effects_target(phase) == (
        "session-1",
        "turn-1",
        turn,
        "hello",
        True,
        "--- a\n+++ b",
    )


def test_wl11097_resolve_turn_submit_side_effects_target_rejects_non_string_approval_diff() -> None:
    # @trace WL-11097
    with pytest.raises(ValueError, match="Turn submit side-effects target unresolved"):
        server._resolve_turn_submit_side_effects_target(
            {
                "session_id": "session-1",
                "turn_id": "turn-1",
                "turn": {"id": "turn-1"},
                "user_input": "hello",
                "requires_approval": True,
                "approval_diff": ["bad"],
            }
        )


def test_wl11098_resolve_turn_submit_approval_payload_rejects_non_string_diff() -> None:
    # @trace WL-11098
    with pytest.raises(ValueError, match="Turn submit approval diff unresolved"):
        server._resolve_turn_submit_approval_payload(
            "session-1",
            "turn-1",
            {"id": "turn-1"},
            None,
            [],
        )


def test_wl11099_build_turn_submit_result_payload_flat_omits_approval_when_absent() -> None:
    # @trace WL-11099
    result = server._build_turn_submit_result_payload_flat(
        {
            "id": "turn-1",
            "session_id": "session-1",
            "status": "completed",
            "input": "hello",
            "approval_id": None,
            "tool_call_id": "toolcall-1",
        },
        None,
    )
    assert result["turn"]["id"] == "turn-1"
    assert "approval" not in result
