"""Lane R regressions for WL-9750..WL-9759 on turn/cancel phased routing."""

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


def _submit_turn(session_id: str, *, requires_approval: bool = False) -> str:
    params: dict[str, object] = {"session_id": session_id, "input": "lane-r"}
    if requires_approval:
        params["requires_approval"] = True
        params["unified_diff"] = "--- a/x\n+++ b/x\n@@\n-old\n+new\n"
    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": params,
            }
        )
    )
    assert response is not None
    return response["result"]["turn"]["id"]


def test_wl9750_discovery_phase_preserves_cancel_route() -> None:
    # @trace WL-9750
    assert server._discover_turn_cancel_route("turn/cancel") == "cancel"


def test_wl9751_binding_phase_exposes_parse_execute_project() -> None:
    # @trace WL-9751
    binding = server._bind_turn_cancel_phases("cancel")
    assert set(binding) == {"parse", "execute", "project"}


def test_wl9752_parse_phase_uses_bound_parser_for_valid_turn() -> None:
    # @trace WL-9752
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    binding = server._bind_turn_cancel_phases("cancel")
    parsed_turn_id, turn, error = server._parse_turn_cancel_with_binding(
        "req", {"turn_id": turn_id}, binding
    )
    assert error is None
    assert parsed_turn_id == turn_id
    assert turn is not None


def test_wl9753_success_dispatch_executes_and_projects_response() -> None:
    # @trace WL-9753
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    turn = SERVER_STATE.turns[turn_id]
    binding = server._bind_turn_cancel_phases("cancel")
    response = server._dispatch_turn_cancel_success(
        True, "req-ok", turn_id, turn, binding
    )
    assert response is not None
    assert response["result"]["turn"]["id"] == turn_id
    assert response["result"]["turn"]["status"] == "cancelled"


def test_wl9754_recovery_dispatch_suppresses_terminal_notification_errors() -> None:
    # @trace WL-9754
    parse_error = server._error_response(
        "ignored", server.JsonRpcError(-32003, "Turn already terminal")
    )
    assert server._dispatch_turn_cancel_recovery(False, parse_error) is None


def test_wl9755_discovery_rejects_unsupported_method() -> None:
    # @trace WL-9755
    with pytest.raises(ValueError, match="Unsupported turn cancel method"):
        server._discover_turn_cancel_route("turn/submit")


def test_wl9756_binding_rejects_unsupported_route() -> None:
    # @trace WL-9756
    with pytest.raises(ValueError, match="Unsupported turn cancel route"):
        server._bind_turn_cancel_phases("pause")


def test_wl9757_parse_phase_preserves_not_found_boundary() -> None:
    # @trace WL-9757
    _reset_state()
    binding = server._bind_turn_cancel_phases("cancel")
    turn_id, turn, error = server._parse_turn_cancel_with_binding(
        "req", {"turn_id": "turn-404"}, binding
    )
    assert turn_id is None
    assert turn is None
    assert error is not None
    assert error["error"]["code"] == -32002


def test_wl9758_handler_orchestrates_parse_then_dispatch_paths() -> None:
    # @trace WL-9758
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)

    success = server._handle_turn_cancel_request(
        "turn/cancel", True, "req-s", {"turn_id": turn_id}
    )
    assert success is not None
    assert success["result"]["turn"]["status"] == "cancelled"

    failure = server._handle_turn_cancel_request(
        "turn/cancel", True, "req-f", {"turn_id": "turn-404"}
    )
    assert failure is not None
    assert failure["error"]["code"] == -32002


def test_wl9759_cache_miss_branch_preserves_no_response_for_terminal_notification() -> (
    None
):
    # @trace WL-9759
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)

    first = server._handle_turn_cancel_request(
        "turn/cancel", True, "req-1", {"turn_id": turn_id}
    )
    assert first is not None
    second = server._handle_turn_cancel_request(
        "turn/cancel", False, "req-2", {"turn_id": turn_id}
    )
    assert second is None
