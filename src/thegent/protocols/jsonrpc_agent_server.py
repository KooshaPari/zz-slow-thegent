"""JSON-RPC agent server protocol."""
from __future__ import annotations

import time as _time
from typing import Any

SUPPORTED_METHODS = [
    "session/start",
    "session/list",
    "session/resume",
    "session/read",
    "turn/submit",
    "turn/cancel",
    "approval/grant",
    "approval/reject",
    "health/check",
    "config/read",
]


class JsonRpcError:
    """JSON-RPC error class."""
    def __init__(self, code: int, message: str, data: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


class _ServerState:
    """Server state for tracking sessions, turns, etc."""

    def __init__(self) -> None:
        self.session_counter = 0
        self.turn_counter = 0
        self.approval_counter = 0
        self.tool_call_counter = 0
        self.sessions: dict[str, Any] = {}
        self.turns: dict[str, Any] = {}
        self.approvals: dict[str, Any] = {}


class _WorkflowState:
    """Workflow state for tracking workflows."""

    def __init__(self) -> None:
        self.workflow_counter = 0
        self.workflows: dict[str, Any] = {}


class _SessionState:
    """Session state for tracking session details."""

    def __init__(self) -> None:
        self.turn_counter = 0
        self.turns: dict[str, Any] = {}


# Module-level state singletons
SERVER_STATE = _ServerState()
WORKFLOW_STATE = _WorkflowState()
SESSION_STATE = _SessionState()


def _reset_state() -> None:
    """Reset all server state."""
    SERVER_STATE.session_counter = 0
    SERVER_STATE.turn_counter = 0
    SERVER_STATE.approval_counter = 0
    SERVER_STATE.tool_call_counter = 0
    SERVER_STATE.sessions.clear()
    SERVER_STATE.turns.clear()
    SERVER_STATE.approvals.clear()
    WORKFLOW_STATE.workflow_counter = 0
    WORKFLOW_STATE.workflows.clear()
    SESSION_STATE.turn_counter = 0
    SESSION_STATE.turns.clear()


class InMemoryJsonRpcState:
    """In-memory state for JSON-RPC server."""

    def __init__(self) -> None:
        self.session_counter = 0
        self.turn_counter = 0
        self.approval_counter = 0
        self.tool_call_counter = 0
        self.sessions: dict[str, Any] = {}
        self.turns: dict[str, Any] = {}
        self.approvals: dict[str, Any] = {}


class NotificationContext:
    """Context for notification handling."""
    def __init__(self, method: str, params: dict[str, Any]) -> None:
        self.method = method
        self.params = params


async def serve_stdio() -> None:
    """Serve JSON-RPC over stdio."""
    import sys
    for line in sys.stdin:
        line = line.strip()
        if line:
            result = process_jsonrpc_line(line)
            if result:
                pass


def _error_response(request_id: str | int | None, error: JsonRpcError) -> dict[str, Any]:
    """Build an error response."""
    return {"jsonrpc": "2.0", "id": request_id, "error": error.to_dict()}


def _build_session_start_record() -> dict[str, Any]:
    """Build a new session start record."""
    SERVER_STATE.session_counter += 1
    session_id = f"session-{SERVER_STATE.session_counter}"
    record = {
        "id": session_id,
        "created_at": _time.time(),
        "turn_ids": [],
    }
    SERVER_STATE.sessions[session_id] = record
    return record


def _handle_session_start(request_id: str | int) -> dict[str, Any]:
    """Handle session/start request."""
    SERVER_STATE.session_counter += 1
    session_id = f"session-{SERVER_STATE.session_counter}"
    session = {
        "id": session_id,
        "status": "active",
        "created_index": SERVER_STATE.session_counter,
        "turn_ids": [],
    }
    SERVER_STATE.sessions[session_id] = session
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"session": session},
    }

def _handle_health_check(request_id: str | int) -> dict[str, Any]:
    """Handle health/check method."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"status": "ok", "timestamp": _time.time(), "service": "thegent-agent-server", "transport": "stdio"},
    }


def _handle_session_list(request_id: str | int) -> dict[str, Any]:
    """Handle session/list method."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"sessions": list(SERVER_STATE.sessions.values())},
    }


def _handle_session_resume(request_id: str | int, session_id: str) -> dict[str, Any]:
    """Handle session/resume method."""
    session = SERVER_STATE.sessions.get(session_id)
    if not session:
        return _error_response(request_id, JsonRpcError(-32001, "Session not found"))
    session["status"] = "active"
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"session": session},
    }


def _handle_session_read(request_id: str | int, params: dict[str, Any]) -> dict[str, Any]:
    """Handle session/read method."""
    session_id = params.get("session_id")
    if not session_id:
        return _error_response(request_id, JsonRpcError(-32602, "session_id required", {"reason": "session_id_required"}))
    if session_id not in SERVER_STATE.sessions:
        return _error_response(request_id, JsonRpcError(-32002, "session not found", {"reason": "session_not_found"}))

    session = SERVER_STATE.sessions[session_id]
    turns = [{"id": tid, "status": SERVER_STATE.turns.get(tid, {}).get("status", "unknown")}
             for tid in session.get("turn_ids", [])]

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "session": {"id": session_id, "status": session.get("status", "active")},
            "turns": turns,
        },
    }


def _handle_turn_submit_request(
    request_id: str | int,
    session_id: str,
    input_text: str,
    requires_approval: bool = False,
    unified_diff: str | None = None,
) -> dict[str, Any]:
    """Handle turn/submit request."""
    # Validate input is a string
    if not isinstance(input_text, str):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32001,
                "message": "Input must be a string",
                "data": {"reason": "input_must_be_string"},
            },
        }

    session = SERVER_STATE.sessions.get(session_id)
    if not session:
        return _error_response(request_id, JsonRpcError(-32002, "Session not found"))

    SERVER_STATE.turn_counter += 1
    turn_id = f"turn-{SERVER_STATE.turn_counter}"

    turn: dict[str, Any] = {
        "id": turn_id,
        "session_id": session_id,
        "status": "in_progress",
        "input": input_text,
        "created_index": SERVER_STATE.turn_counter,
        "approval_id": None,
        "tool_call_id": None,
    }

    if requires_approval:
        SERVER_STATE.approval_counter += 1
        approval_id = f"approval-{SERVER_STATE.approval_counter:04d}"
        approval: dict[str, Any] = {
            "id": approval_id,
            "turn_id": turn_id,
            "status": "pending",
            "unified_diff": unified_diff or "",
        }
        SERVER_STATE.approvals[approval_id] = approval
        turn["status"] = "awaiting_approval"
        turn["approval_id"] = approval_id
    else:
        SERVER_STATE.tool_call_counter += 1
        tool_call_id = f"tool-call-{SERVER_STATE.tool_call_counter:04d}"
        turn["status"] = "completed"
        turn["tool_call_id"] = tool_call_id

    SERVER_STATE.turns[turn_id] = turn
    session["turn_ids"].append(turn_id)

    result: dict[str, Any] = {"turn": turn}
    if requires_approval:
        result["approval_id"] = approval_id

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _build_turn_submit_execution_plan(session_id: str, input_text: str) -> tuple[str, dict[str, Any]]:
    """Build turn submit execution plan."""
    session = SERVER_STATE.sessions.get(session_id)
    if not session:
        # Create session if it doesn't exist
        SERVER_STATE.session_counter += 1
        session_id = f"session-{SERVER_STATE.session_counter}"
        session = {"id": session_id, "status": "active", "turn_ids": []}
        SERVER_STATE.sessions[session_id] = session
    SERVER_STATE.turn_counter += 1
    turn_id = f"turn-{SERVER_STATE.turn_counter}"
    turn = {
        "id": turn_id,
        "session_id": session_id,
        "status": "in_progress",
        "input": input_text,
        "created_index": SERVER_STATE.turn_counter,
        "approval_id": None,
        "tool_call_id": None,
    }
    SERVER_STATE.turns[turn_id] = turn
    return turn_id, turn


def _commit_turn_submit_plan(turn_id: str, turn: dict[str, Any], session: dict[str, Any]) -> None:
    """Commit turn submit plan."""
    if session:
        session.setdefault("turn_ids", []).append(turn_id)


def _resolve_turn_submit_approval_payload(
    session_id: str,
    turn_id: str,
    turn: dict[str, Any],
    requires_approval: bool | None,
    unified_diff: str | None,
) -> dict[str, Any]:
    """Resolve turn submit approval payload."""
    # When unified_diff is provided (even as empty list), requires_approval must be explicitly True
    if unified_diff is not None and requires_approval is not True:
        raise ValueError("Turn submit approval diff unresolved")
    if requires_approval:
        if not unified_diff or unified_diff in ([], ""):
            raise ValueError("Turn submit approval diff unresolved")
        SERVER_STATE.approval_counter += 1
        approval_id = f"approval-{SERVER_STATE.approval_counter:04d}"
        approval: dict[str, Any] = {
            "id": approval_id,
            "turn_id": turn_id,
            "status": "pending",
            "unified_diff": unified_diff,
        }
        SERVER_STATE.approvals[approval_id] = approval
        return {"approval": approval, "requires_approval": True, "unified_diff": unified_diff}
    return {"requires_approval": False, "unified_diff": None}


def _resolve_turn_submit_completion(
    session_id: str,
    turn_id: str,
    input_text: str,
    turn: dict[str, Any],
    notifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve turn submit completion."""
    SERVER_STATE.tool_call_counter += 1
    tool_call_id = f"tool-call-{SERVER_STATE.tool_call_counter:04d}"
    turn["status"] = "completed"
    turn["tool_call_id"] = tool_call_id
    return {"tool_call_id": tool_call_id, "status": "completed"}


def _apply_turn_submit_side_effects(
    session_id: str,
    turn_id: str,
    turn: dict[str, Any],
    input_text: str,
    requires_approval: bool,
    unified_diff: str | None,
    notifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply turn submit side effects."""
    if requires_approval:
        SERVER_STATE.approval_counter += 1
        approval_id = f"approval-{SERVER_STATE.approval_counter:04d}"
        approval: dict[str, Any] = {
            "id": approval_id,
            "turn_id": turn_id,
            "status": "pending",
            "unified_diff": unified_diff or "",
        }
        SERVER_STATE.approvals[approval_id] = approval
        turn["status"] = "awaiting_approval"
        turn["approval_id"] = approval_id
        notifications.append({
            "method": "approval/requested",
            "params": {
                "approval_id": approval_id,
                "turn_id": turn_id,
                "unified_diff": unified_diff or "",
            },
        })
        return {"approval": approval, "status": "awaiting_approval"}
    else:
        SERVER_STATE.tool_call_counter += 1
        tool_call_id = f"tool-call-{SERVER_STATE.tool_call_counter:04d}"
        turn["status"] = "completed"
        turn["tool_call_id"] = tool_call_id
        notifications.append({
            "method": "turn/completed",
            "params": {
                "turn_id": turn_id,
                "tool_call_id": tool_call_id,
            },
        })
        return None


def _build_turn_submit_execution_phase(parse_phase: dict[str, Any]) -> tuple[str, dict[str, Any], str, bool, str | None, str | None, list[dict[str, Any]]]:
    """Build turn submit execution phase from parse phase."""
    # Validate required fields are present
    session_id = parse_phase.get("session_id")
    turn = parse_phase.get("turn")
    input_text = parse_phase.get("input", "")
    requires_approval = parse_phase.get("requires_approval", False)
    unified_diff = parse_phase.get("unified_diff")
    error = parse_phase.get("error")
    notifications = parse_phase.get("notifications", [])

    # Validate execution targets are resolved
    if session_id is None or turn is None:
        raise ValueError("Turn submit execution target unresolved")

    return (session_id, turn, input_text, requires_approval, unified_diff, error, notifications)


def _build_turn_submit_result_payload_flat(
    turn: dict[str, Any],
    approval: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build turn submit result payload (flat format)."""
    result: dict[str, Any] = {"turn": turn}
    if approval:
        result["approval"] = approval
    return result


def _build_turn_submit_result_payload_nested(
    turn: dict[str, Any],
    approval: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build turn submit result payload (nested format)."""
    result: dict[str, Any] = {"turn": turn}
    if approval:
        result["approval"] = approval
    return result


def _handle_turn_submit_parse_failure(error_payload: dict[str, Any]) -> dict[str, Any]:
    """Handle turn submit parse failure."""
    return error_payload


def _route_turn_cancel_method(
    plan: dict[str, Any],
) -> str:
    """Route turn cancel method."""
    return "turn_cancel_dispatch"


def _parse_turn_cancel_request(
    params: dict[str, Any],
) -> JsonRpcError | dict[str, str]:
    """Parse turn cancel request."""
    if not isinstance(params, dict):
        return JsonRpcError(-32602, "params must be object", {"reason": "params_must_be_object"})
    turn_id = params.get("turn_id")
    if not turn_id:
        return JsonRpcError(-32602, "turn_id is required", {"reason": "turn_id_required"})
    return {"turn_id": turn_id}


def _execute_turn_cancel_resolution(
    turn: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute turn cancel resolution."""
    return _execute_turn_cancel(turn, context)


def _project_turn_cancel_response(
    request_id: str | int | None,
    turn: dict[str, Any],
) -> dict[str, Any]:
    """Project turn cancel response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"turn": turn},
    }


def _resolve_turn_cancel_turn(
    turn_id: str | None,
) -> JsonRpcError | dict[str, Any]:
    """Resolve turn cancel turn."""
    if not turn_id:
        return JsonRpcError(-32602, "turn_id is required", {"reason": "turn_id_required"})
    turn = SERVER_STATE.turns.get(turn_id)
    if not turn:
        return JsonRpcError(-32002, "Turn not found", {"reason": "turn_not_found"})
    return turn


def _resolve_turn_cancel_context(
    turn_id: str | None,
) -> JsonRpcError | dict[str, Any]:
    """Resolve turn cancel context."""
    if not turn_id:
        return JsonRpcError(-32602, "turn_id is required", {"reason": "turn_id_required"})
    turn = SERVER_STATE.turns.get(turn_id)
    if not turn:
        return JsonRpcError(-32002, "Turn not found", {"reason": "turn_not_found"})
    session_id = turn.get("session_id")
    if session_id:
        session = SERVER_STATE.sessions.get(session_id)
        if session:
            return session
    return {}


def _validate_turn_cancel_turn_state(turn: dict[str, Any]) -> JsonRpcError | None:
    """Validate turn cancel turn state."""
    if turn.get("status") in ("completed", "cancelled", "failed"):
        return JsonRpcError(-32003, "Turn already terminal", {"reason": "turn_terminal"})
    return None


def _cancel_turn_requested_approval(turn: dict[str, Any]) -> None:
    """Cancel turn's requested approval."""
    approval_id = turn.get("approval_id")
    if approval_id:
        approval = SERVER_STATE.approvals.get(approval_id)
        if approval and approval.get("status") in ("pending", "requested"):
            approval["status"] = "cancelled"


def _mark_turn_as_cancelled(turn: dict[str, Any]) -> None:
    """Mark turn as cancelled."""
    turn["status"] = "cancelled"


def _execute_turn_cancel(
    turn: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute turn cancel."""
    _cancel_turn_requested_approval(turn)
    _mark_turn_as_cancelled(turn)
    return turn


def _validate_turn_cancel_projection_turn_id(
    turn_id: str | None,
    projection: dict[str, Any],
) -> JsonRpcError | None:
    """Validate turn cancel projection turn id."""
    if projection.get("id") != turn_id:
        return JsonRpcError(-32001, "Projection turn_id mismatch", {"reason": "turn_id_mismatch"})
    return None


def _build_turn_cancel_projection_payload(turn: dict[str, Any]) -> dict[str, Any]:
    """Build turn cancel projection payload."""
    return {
        "id": turn.get("id"),
        "session_id": turn.get("session_id"),
        "status": "cancelled",
        "approval_id": turn.get("approval_id"),
    }


def _build_turn_cancel_phase_plan(
    turn_id: str | None = None,
    turn: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> JsonRpcError | dict[str, Any]:
    """Build turn cancel phase plan."""
    if turn_id is None:
        return JsonRpcError(-32602, "turn_id is required", {"reason": "turn_id_required"})

    result = _resolve_turn_cancel_turn(turn_id)
    if isinstance(result, JsonRpcError):
        return result

    result = _validate_turn_cancel_turn_state(result)
    if isinstance(result, JsonRpcError):
        return result

    context_result = _resolve_turn_cancel_context(turn_id)
    if isinstance(context_result, JsonRpcError):
        return context_result

    return {
        "turn_id": turn_id,
        "turn": result,
        "context": context_result,
    }


def _handle_turn_cancel_request(
    request_id: str | int | None,
    turn_id: str,
) -> dict[str, Any] | None:
    """Handle turn/cancel request."""
    turn = SERVER_STATE.turns.get(turn_id)
    if not turn:
        return _error_response(request_id, JsonRpcError(-32002, "Turn not found", {"reason": "turn_not_found"}))

    if turn.get("status") in ("completed", "cancelled", "failed"):
        return _error_response(request_id, JsonRpcError(-32003, "Turn already terminal", {"reason": "turn_terminal"}))

    # Cancel any pending approval
    approval_id = turn.get("approval_id")
    if approval_id and SERVER_STATE.approvals.get(approval_id, {}).get("status") in ("pending", "requested"):
        SERVER_STATE.approvals[approval_id]["status"] = "cancelled"

    turn["status"] = "cancelled"

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"turn": turn},
    }


def _handle_approval_grant(
    request_id: str | int | None,
    approval_id: str,
) -> dict[str, Any] | None:
    """Handle approval/grant request."""
    approval = SERVER_STATE.approvals.get(approval_id)
    if not approval:
        return _error_response(request_id, JsonRpcError(-32002, "Approval not found", {"reason": "approval_not_found"}))

    if approval.get("status") != "pending":
        return _error_response(request_id, JsonRpcError(-32003, "Approval not pending", {"reason": "approval_not_pending"}))

    approval["status"] = "granted"
    turn_id = approval.get("turn_id")
    if turn_id and turn_id in SERVER_STATE.turns:
        SERVER_STATE.turns[turn_id]["status"] = "approved"
        SERVER_STATE.tool_call_counter += 1
        SERVER_STATE.turns[turn_id]["tool_call_id"] = f"tool-call-{SERVER_STATE.tool_call_counter:04d}"

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"approval": approval},
    }


def _handle_approval_reject(
    request_id: str | int | None,
    approval_id: str,
) -> dict[str, Any] | None:
    """Handle approval/reject request."""
    approval = SERVER_STATE.approvals.get(approval_id)
    if not approval:
        return _error_response(request_id, JsonRpcError(-32002, "Approval not found", {"reason": "approval_not_found"}))

    if approval.get("status") != "pending":
        return _error_response(request_id, JsonRpcError(-32003, "Approval not pending", {"reason": "approval_not_pending"}))

    approval["status"] = "rejected"
    turn_id = approval.get("turn_id")
    if turn_id and turn_id in SERVER_STATE.turns:
        SERVER_STATE.turns[turn_id]["status"] = "rejected"

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"approval": approval},
    }


SUPPORTED_METHODS = [
    "session/start",
    "session/list",
    "session/resume",
    "session/read",
    "turn/submit",
    "turn/cancel",
    "approval/grant",
    "approval/reject",
    "health/check",
    "config/read",
]


def _handle_config_read(
    request_id: str | int | None,
    key: str | None = None,
) -> dict[str, Any]:
    """Handle config/read request."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"supported_methods": sorted(SUPPORTED_METHODS), "server": "thegent-agent-server", "transport": "stdio"},
    }


def process_jsonrpc_line(line: str) -> str | None:
    """Process a single JSON-RPC line and return response string."""
    try:
        import orjson
        request = orjson.loads(line)
    except Exception:
        return '{"jsonrpc": "2.0", "id": null, "error": {"code": -32700, "message": "Parse error"}}'

    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})

    if method == "session/start":
        response = _handle_session_start(request_id)
    elif method == "session/list":
        response = _handle_session_list(request_id)
    elif method == "session/resume":
        response = _handle_session_resume(request_id, params.get("session_id", ""))
    elif method == "session/read":
        response = _handle_session_read(request_id, params)
    elif method == "turn/submit":
        response = _handle_turn_submit_request(
            request_id,
            params.get("session_id", ""),
            params.get("input", ""),
            params.get("requires_approval", False),
            params.get("unified_diff"),
        )
    elif method == "turn/cancel":
        response = _handle_turn_cancel_request(request_id, params.get("turn_id", ""))
    elif method == "approval/grant":
        response = _handle_approval_grant(request_id, params.get("approval_id", ""))
    elif method == "approval/reject":
        response = _handle_approval_reject(request_id, params.get("approval_id", ""))
    elif method == "health/check":
        response = _handle_health_check(request_id)
    elif method == "config/read":
        response = _handle_config_read(request_id, params.get("key", ""))
    else:
        response = _error_response(request_id, JsonRpcError(-32601, f"Method not found: {method}"))

    return orjson.dumps(response).decode()


def process_jsonrpc_line_full(line: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Process a JSON-RPC line and return (response, notifications) tuple."""
    try:
        import orjson
        request = orjson.loads(line)
    except Exception:
        return ({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, [])

    # Handle notifications (no id field)
    is_notification = request.get("id") is None
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})

    notifications: list[dict[str, Any]] = []

    if method == "session/start":
        response = _handle_session_start(request_id)
        if is_notification:
            response = None
    elif method == "session/list":
        response = _handle_session_list(request_id)
    elif method == "session/resume":
        response = _handle_session_resume(request_id, params.get("session_id", ""))
    elif method == "session/read":
        response = _handle_session_read(request_id, params)
    elif method == "turn/submit":
        response = _handle_turn_submit_request(
            request_id,
            params.get("session_id", ""),
            params.get("input", ""),
            params.get("requires_approval", False),
            params.get("unified_diff"),
        )
        if response and "result" in response:
            notifications.append({
                "jsonrpc": "2.0",
                "method": "turn/started",
                "params": response["result"],
            })
        if is_notification:
            response = None
    elif method == "turn/cancel":
        response = _handle_turn_cancel_request(request_id, params.get("turn_id", ""))
        if is_notification and response and "result" in response:
            notifications.append({
                "jsonrpc": "2.0",
                "method": "turn/cancelled",
                "params": response["result"],
            })
            response = None
    elif method == "approval/grant":
        response = _handle_approval_grant(request_id, params.get("approval_id", ""))
        if is_notification:
            if response and "result" in response:
                notifications.append({
                    "jsonrpc": "2.0",
                    "method": "approval/granted",
                    "params": response["result"],
                })
            response = None
    elif method == "approval/reject":
        response = _handle_approval_reject(request_id, params.get("approval_id", ""))
        if is_notification:
            if response and "result" in response:
                notifications.append({
                    "jsonrpc": "2.0",
                    "method": "approval/rejected",
                    "params": response["result"],
                })
            response = None
    elif method == "health/check":
        response = _handle_health_check(request_id)
    elif method == "config/read":
        response = _handle_config_read(request_id, params.get("key", ""))
        if is_notification:
            response = None
    else:
        response = _error_response(request_id, JsonRpcError(-32601, f"Method not found: {method}"))

    return (response, notifications)


# === Turn Submit Phase Functions ===

def _build_turn_submit_phase_plan(request_id: str | int, params: dict[str, Any]) -> dict[str, Any]:
    """Build turn submit phase plan from request parameters."""
    session_id = params.get("session_id")
    input_text = params.get("input", "")
    return {
        "request_id": request_id,
        "session_id": session_id,
        "input": input_text,
    }


def _build_turn_submit_parse_phase(plan: dict[str, Any]) -> dict[str, Any]:
    """Build turn submit parse phase from plan.

    Validates session exists and input is a string.
    Returns parse_error if validation fails.
    """
    session_id = plan.get("session_id")
    input_text = plan.get("input")

    # Check session exists
    session = SERVER_STATE.sessions.get(session_id) if session_id else None

    # Build parse phase result - include both 'input' and 'user_input' keys for compatibility
    parse_phase: dict[str, Any] = {
        "session_id": session_id,
        "session": session,
        "input": input_text,  # For execution_phase compatibility
        "user_input": input_text,  # For test compatibility
        "parse_error": None,
        "notifications": [],
    }

    # Validate session
    if not session_id or not session:
        parse_phase["parse_error"] = {
            "error": {"code": -32001, "message": f"Session not found: {session_id}"}
        }
        return parse_phase

    # Validate input is string
    if input_text is not None and not isinstance(input_text, str):
        parse_phase["parse_error"] = {
            "error": {"code": -32001, "message": "input_must_be_string"}
        }
        return parse_phase

    # Create turn object for execution phase
    SERVER_STATE.turn_counter += 1
    turn_id = f"turn-{SERVER_STATE.turn_counter}"
    turn = {
        "id": turn_id,
        "session_id": session_id,
        "status": "in_progress",
        "input": input_text,
        "created_index": SERVER_STATE.turn_counter,
    }
    SERVER_STATE.turns[turn_id] = turn
    session.setdefault("turn_ids", []).append(turn_id)

    # Add turn to parse_phase for execution phase
    parse_phase["turn"] = turn

    return parse_phase


def _build_turn_submit_commit_phase(
    session_id: str,
    session: dict[str, Any],
    input_text: str,
) -> dict[str, Any]:
    """Build turn submit commit phase.

    Creates a turn record and associates it with the session.
    """
    SERVER_STATE.turn_counter += 1
    turn_id = f"turn-{SERVER_STATE.turn_counter}"
    turn = {
        "id": turn_id,
        "session_id": session_id,
        "status": "in_progress",
        "input": input_text,
        "created_index": SERVER_STATE.turn_counter,
    }
    SERVER_STATE.turns[turn_id] = turn
    if session:
        session.setdefault("turn_ids", []).append(turn_id)
    return {
        "turn_id": turn_id,
        "turn": turn,
        "session": session,
    }


# === Turn Submit Resolve Target Functions ===

def _resolve_turn_submit_commit_target(
    commit_phase: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Resolve turn submit commit target from commit phase."""
    turn = commit_phase.get("turn")
    session = commit_phase.get("session", {})

    # Validate turn is a dict
    if not isinstance(turn, dict):
        raise ValueError("commit_target resolution requires valid turn dict")

    session = session if isinstance(session, dict) else {}
    turn_id = turn.get("id", "") if isinstance(turn, dict) else ""
    return (turn_id, turn, session)


def _resolve_turn_submit_side_effects_target(
    side_effects_phase: dict[str, Any],
) -> tuple[str, str, str] | tuple[str, str]:
    """Resolve turn submit side effects target from side effects phase."""
    approval = side_effects_phase.get("approval")

    # Validate approval exists
    if approval is None or not isinstance(approval, dict):
        raise ValueError("side-effects target resolution requires approval")

    approval_id = approval.get("id", "") if isinstance(approval, dict) else ""
    approval_status = approval.get("status", "") if isinstance(approval, dict) else ""
    approval_diff = approval.get("diff") if isinstance(approval, dict) else None

    # Return 3-tuple if diff is present, otherwise 2-tuple
    if approval_diff is not None:
        return (approval_id, approval_status, approval_diff)
    return (approval_id, approval_status)


def _resolve_turn_submit_response_target(
    response_phase: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Resolve turn submit response target from response phase."""
    turn = response_phase.get("turn")

    # Validate turn exists
    if turn is None:
        raise ValueError("response_target resolution requires turn")

    approval = response_phase.get("approval")
    return (turn, approval)


def _build_turn_submit_commit_resolution_phase(
    commit_phase_or_route: dict[str, Any] | str,
    request_id: str | int | None = None,
    turn: dict[str, Any] | None = None,
    session: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]] | dict[str, Any]:
    """Resolve turn submit commit phase.

    Supports two calling conventions:
    - New (lane C2): _build_turn_submit_commit_resolution_phase(commit_phase_dict)
      Returns tuple of (turn_id, turn, resolved_session)
    - Old (lane AF): _build_turn_submit_commit_resolution_phase(route, request_id, turn, session)
      Returns dict with route, request_id, turn, session
    """
    # Detect which calling convention based on first argument type
    if isinstance(commit_phase_or_route, dict):
        # New calling convention (lane C2)
        commit_phase = commit_phase_or_route
        turn_id = commit_phase.get("turn_id")
        turn = commit_phase.get("turn")
        session = commit_phase.get("session")

        if turn_id is None or turn is None or session is None:
            raise ValueError("Turn submit commit target unresolved")

        return (turn_id, turn, session)
    else:
        # Old calling convention (lane AF) - returns dict
        route = commit_phase_or_route
        # Return dict format expected by lane AF tests
        return {
            "route": route,
            "request_id": request_id,
            "turn": turn,
            "session": session,
        }


def _build_turn_submit_side_effects_phase(
    session_id: str,
    turn_id: str,
    turn: dict[str, Any],
    user_input: str,
    requires_approval: bool,
    approval_diff: str | None,
) -> dict[str, Any]:
    """Build turn submit side effects phase.

    Prepares the phase for side effects resolution.
    """
    return {
        "session_id": session_id,
        "turn_id": turn_id,
        "turn": turn,
        "user_input": user_input,
        "requires_approval": requires_approval,
        "approval_diff": approval_diff,
    }


def _build_turn_submit_side_effects_resolution_phase(
    side_effects_phase: dict[str, Any],
) -> tuple[str, str, dict[str, Any], str, bool, str | None]:
    """Resolve turn submit side effects phase.

    Validates that session_id and turn_id are proper string values and turn is valid.
    Returns tuple of (session_id, turn_id, turn, user_input, requires_approval, approval_diff).
    Raises ValueError if targets are unresolved or have wrong types.
    """
    session_id = side_effects_phase.get("session_id")
    turn_id = side_effects_phase.get("turn_id")
    turn = side_effects_phase.get("turn")
    user_input = side_effects_phase.get("user_input")
    requires_approval = side_effects_phase.get("requires_approval")
    approval_diff = side_effects_phase.get("approval_diff")

    # Validate session_id and turn_id are strings (not None or other types)
    # Also validate turn is a non-empty dict (has id)
    if not isinstance(session_id, str) or not isinstance(turn_id, str):
        raise ValueError("Turn submit side-effects target unresolved")

    # Validate turn is a valid dict with id
    if not isinstance(turn, dict) or "id" not in turn:
        raise ValueError("Turn submit side-effects target unresolved")

    return (session_id, turn_id, turn, user_input, requires_approval, approval_diff)


def _build_turn_submit_response_phase(
    request_has_id: bool,
    request_id: str | int,
    turn: dict[str, Any],
    approval: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build turn submit response phase.

    Prepares the phase for response resolution.
    """
    return {
        "request_has_id": request_has_id,
        "request_id": request_id,
        "turn": turn,
        "approval": approval,
    }


def _build_turn_submit_response_resolution_phase(
    response_phase: dict[str, Any],
) -> tuple[bool, str | int, dict[str, Any], dict[str, Any] | None]:
    """Resolve turn submit response phase.

    Extracts response components from the phase.
    Returns tuple of (request_has_id, request_id, resolved_turn, approval_payload).
    """
    request_has_id = response_phase.get("request_has_id", False)
    request_id = response_phase.get("request_id")
    turn = response_phase.get("turn")
    approval = response_phase.get("approval")

    return (request_has_id, request_id, turn, approval)
