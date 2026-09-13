"""Lane C9 regressions for WL-11000..WL-11009 on turn/submit response shaping and handler defaults."""

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


def _turn_payload() -> dict[str, object]:
    return {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "completed",
        "approval_id": None,
        "tool_call_id": "toolcall-0001",
    }


def test_wl11000_build_turn_submit_success_response_suppresses_output_without_request_id() -> None:
    # @trace WL-11000
    assert server._build_turn_submit_success_response(False, "req", _turn_payload(), None) is None


def test_wl11001_build_turn_submit_success_response_preserves_turn_without_approval_payload() -> None:
    # @trace WL-11001
    response = server._build_turn_submit_success_response(True, "submit", _turn_payload(), None)
    assert response is not None
    assert response["id"] == "submit"
    assert "approval" not in response["result"]
    assert response["result"]["turn"]["status"] == "completed"


def test_wl11002_extract_turn_submit_response_request_id_preserves_request_id_for_notification_path() -> None:
    # @trace WL-11002
    response_phase = server._build_turn_submit_response_phase(False, 9, _turn_payload(), None)
    assert server._extract_turn_submit_response_request_id(response_phase, request_has_id=False) == 9


def test_wl11003_extract_turn_submit_response_request_id_rejects_invalid_when_id_expected() -> None:
    # @trace WL-11003
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id({"request_id": True}, request_has_id=True)


def test_wl11004_extract_turn_submit_response_request_has_id_rejects_non_bool_type() -> None:
    # @trace WL-11004
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_has_id({"request_has_id": "yes"})


def test_wl11005_extract_turn_submit_response_approval_payload_accepts_none() -> None:
    # @trace WL-11005
    assert server._extract_turn_submit_response_approval_payload({"approval_payload": None}) is None


def test_wl11006_extract_turn_submit_response_approval_payload_rejects_non_dict() -> None:
    # @trace WL-11006
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_approval_payload({"approval_payload": 42})


def test_wl11007_extract_turn_submit_response_target_rejects_broken_approval_payload() -> None:
    # @trace WL-11007
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            server._build_turn_submit_response_phase(True, "submit", _turn_payload(), {"id": "", "status": "requested"})
        )


def test_wl11008_handle_turn_submit_request_defaults_input_to_empty_string() -> None:
    # @trace WL-11008
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit-empty",
                "method": "turn/submit",
                "params": {"session_id": session_id},
            }
        )
    )
    assert response is not None
    assert response["result"]["turn"]["input"] == ""
    assert response["result"]["turn"]["status"] == "completed"
    assert len(notifications) >= 4


def test_wl11009_extract_turn_submit_approval_payload_status_rejects_empty_string() -> None:
    # @trace WL-11009
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_status({"id": "approval-1", "status": ""})
