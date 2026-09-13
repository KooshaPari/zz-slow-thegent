"""Lane B2 regressions for WL-10940..WL-10949 on turn/submit response target extraction."""

from __future__ import annotations

import orjson as json
import pytest

from thegent.protocols import jsonrpc_agent_server as server
from thegent.protocols.jsonrpc_agent_server import (
    SERVER_STATE,
    process_jsonrpc_line_full,
)


def _reset_state() -> None:
    SERVER_STATE.session_counter = 0
    SERVER_STATE.turn_counter = 0
    SERVER_STATE.approval_counter = 0
    SERVER_STATE.tool_call_counter = 0
    SERVER_STATE.sessions.clear()
    SERVER_STATE.turns.clear()
    SERVER_STATE.approvals.clear()


def _start_session() -> str:
    response, _notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "start", "method": "session/start"})
    )
    assert response is not None
    return response["result"]["session"]["id"]


def test_wl10940_extract_turn_submit_response_request_has_id_accepts_bool() -> None:
    # @trace WL-10940
    assert server._extract_turn_submit_response_request_has_id({"request_has_id": True}) is True


def test_wl10941_extract_turn_submit_response_request_has_id_rejects_non_bool() -> None:
    # @trace WL-10941
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_has_id({"request_has_id": "yes"})


def test_wl10942_extract_turn_submit_response_turn_accepts_dict() -> None:
    # @trace WL-10942
    turn = {"id": "turn-1"}
    assert server._extract_turn_submit_response_turn({"turn": turn}) is turn


def test_wl10943_extract_turn_submit_response_turn_rejects_non_dict() -> None:
    # @trace WL-10943
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_turn({"turn": "turn-1"})


def test_wl10944_extract_turn_submit_response_approval_payload_accepts_none() -> None:
    # @trace WL-10944
    assert server._extract_turn_submit_response_approval_payload({"approval_payload": None}) is None


def test_wl10945_extract_turn_submit_response_approval_payload_rejects_non_dict() -> None:
    # @trace WL-10945
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_approval_payload({"approval_payload": "bad"})


def test_wl10946_extract_turn_submit_approval_payload_id_rejects_missing() -> None:
    # @trace WL-10946
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_id({"status": "requested"})


def test_wl10947_extract_turn_submit_approval_payload_status_rejects_missing() -> None:
    # @trace WL-10947
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_status({"id": "approval-1"})


def test_wl10948_extract_turn_submit_approval_payload_diff_rejects_non_string() -> None:
    # @trace WL-10948
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_diff({"id": "approval-1", "status": "requested", "diff": 12})


def test_wl10949_turn_submit_notification_requires_approval_emits_side_effects_without_response() -> None:
    # @trace WL-10949
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-b2",
                    "requires_approval": True,
                    "unified_diff": "--- a\n+++ b\n@@\n-old\n+new\n",
                },
            }
        )
    )
    assert response is None
    assert notifications[0]["method"] == "turn/started"
    assert notifications[-1]["method"] == "approval/requested"
