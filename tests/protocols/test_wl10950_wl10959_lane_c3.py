"""Lane C3 regressions for WL-10950..WL-10959 on turn/submit response field extraction."""

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


def test_wl10950_extract_turn_submit_response_request_id_accepts_valid_id() -> None:
    # @trace WL-10950
    assert (
        server._extract_turn_submit_response_request_id(
            {"request_id": "req-1"}, request_has_id=True
        )
        == "req-1"
    )


def test_wl10951_extract_turn_submit_response_request_id_rejects_missing_when_response_expected() -> (
    None
):
    # @trace WL-10951
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id(
            {"request_id": None}, request_has_id=True
        )


def test_wl10952_extract_turn_submit_response_approval_id_accepts_none() -> None:
    # @trace WL-10952
    assert server._extract_turn_submit_response_approval_id(None) is None


def test_wl10953_extract_turn_submit_response_approval_id_rejects_non_string() -> None:
    # @trace WL-10953
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_approval_id(
            {"id": 123, "status": "requested"}
        )


def test_wl10954_extract_turn_submit_response_approval_status_accepts_none() -> None:
    # @trace WL-10954
    assert server._extract_turn_submit_response_approval_status(None) is None


def test_wl10955_extract_turn_submit_response_approval_status_rejects_non_string() -> (
    None
):
    # @trace WL-10955
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_approval_status(
            {"id": "approval-1", "status": 12}
        )


def test_wl10956_extract_turn_submit_response_approval_diff_accepts_string() -> None:
    # @trace WL-10956
    assert (
        server._extract_turn_submit_response_approval_diff(
            {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b\n"}
        )
        == "--- a\n+++ b\n"
    )


def test_wl10957_extract_turn_submit_response_approval_diff_rejects_non_string() -> (
    None
):
    # @trace WL-10957
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_approval_diff(
            {"id": "approval-1", "status": "requested", "diff": 99}
        )


def test_wl10958_resolve_turn_submit_response_approval_fields_returns_valid_tuple() -> (
    None
):
    # @trace WL-10958
    approval_id, approval_status, approval_diff = (
        server._resolve_turn_submit_response_approval_fields(
            {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b\n"}
        )
    )
    assert approval_id == "approval-1"
    assert approval_status == "requested"
    assert approval_diff == "--- a\n+++ b\n"


def test_wl10959_turn_submit_requires_approval_response_preserves_id_and_payload() -> (
    None
):
    # @trace WL-10959
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit-c3",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-c3",
                    "requires_approval": True,
                    "unified_diff": "--- a\n+++ b\n@@\n-old\n+new\n",
                },
            }
        )
    )
    assert response is not None
    assert response["id"] == "submit-c3"
    approval_payload = response["result"]["approval"]
    resolved = server._resolve_turn_submit_response_target(
        server._build_turn_submit_response_phase(
            True, response["id"], response["result"]["turn"], approval_payload
        )
    )
    assert resolved[0] is True
    assert resolved[1] == "submit-c3"
    assert resolved[3]["status"] == "requested"
    assert notifications[-1]["method"] == "approval/requested"
