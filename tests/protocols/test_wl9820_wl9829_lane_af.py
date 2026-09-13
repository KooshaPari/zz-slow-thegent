"""Lane AF regressions for WL-9820..WL-9829 against current JSON-RPC server contract."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl9820_commit_phase_extracts_target_tuple() -> None:
    # @trace WL-9820
    resolved = server._resolve_turn_submit_commit_target(
        {
            "turn": {"id": "turn-1"},
            "session": {"id": "session-1"},
        }
    )
    assert resolved == ("turn-1", {"id": "turn-1"}, {"id": "session-1"})


def test_wl9821_commit_target_resolution_is_typed_and_stable() -> None:
    # @trace WL-9821
    resolved = server._resolve_turn_submit_commit_target(
        {
            "turn": {
                "id": "turn-1",
                "session_id": "session-1",
                "input": "x",
            },
            "session": {"id": "session-1", "turn_ids": ["turn-1"]},
        }
    )
    assert resolved == (
        "turn-1",
        {"id": "turn-1", "session_id": "session-1", "input": "x"},
        {"id": "session-1", "turn_ids": ["turn-1"]},
    )


def test_wl9822_commit_target_fails_loudly_on_invalid_shape() -> None:
    # @trace WL-9822
    with pytest.raises(ValueError, match="commit_target"):
        server._resolve_turn_submit_commit_target({"turn": "not-a-dict"})


def test_wl9823_side_effects_phase_extracts_approval_tuple() -> None:
    # @trace WL-9823
    resolved = server._resolve_turn_submit_side_effects_target(
        {
            "approval": {"id": "approval-1", "status": "pending"},
        }
    )
    assert resolved == ("approval-1", "pending")


def test_wl9824_side_effects_target_resolution_preserves_approval_tuple() -> None:
    # @trace WL-9824
    resolved = server._resolve_turn_submit_side_effects_target(
        {
            "approval": {
                "id": "approval-2",
                "status": "granted",
                "diff": "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new",
            },
        }
    )
    assert resolved == (
        "approval-2",
        "granted",
        "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new",
    )


def test_wl9825_side_effects_target_fails_on_missing_approval() -> None:
    # @trace WL-9825
    with pytest.raises(ValueError, match="side-effects"):
        server._resolve_turn_submit_side_effects_target({})


def test_wl9826_response_phase_preserves_turn_and_optional_approval_payload() -> None:
    # @trace WL-9826
    turn = {"id": "turn-1"}
    resolved = server._resolve_turn_submit_response_target({"turn": turn, "approval": None})
    assert resolved == (turn, None)


def test_wl9827_response_target_fails_on_missing_turn() -> None:
    # @trace WL-9827
    with pytest.raises(ValueError, match="response_target"):
        server._resolve_turn_submit_response_target({})


def test_wl9828_commit_resolution_phase_routes_to_execution_target() -> None:
    # @trace WL-9828
    phase = server._build_turn_submit_commit_resolution_phase("commit", "req-1", {"id": "turn-1"}, {"id": "session-1"})
    assert phase["route"] == "commit"
    assert phase["request_id"] == "req-1"
    assert phase["turn"] == {"id": "turn-1"}
    assert phase["session"] == {"id": "session-1"}


def test_wl9829_resolution_phase_preserves_route_payload() -> None:
    # @trace WL-9829
    phase = server._build_turn_submit_commit_resolution_phase(
        "commit", "req-9829", {"id": "turn-9829"}, {"id": "session-9829"}
    )
    assert phase["route"] == "commit"
    assert phase["request_id"] == "req-9829"
    assert phase["turn"] == {"id": "turn-9829"}
    assert phase["session"] == {"id": "session-9829"}
