"""Contract tests for WL-104 JSON-RPC agent server behavior."""

from __future__ import annotations

import io
import json

import pytest

from thegent.protocols.jsonrpc_agent_server import (
    SERVER_STATE,
    SUPPORTED_METHODS,
    process_jsonrpc_line,
    process_jsonrpc_line_full,
    serve_stdio,
)


@pytest.fixture(autouse=True)
def reset_server_state() -> None:
    SERVER_STATE.session_counter = 0
    SERVER_STATE.turn_counter = 0
    SERVER_STATE.approval_counter = 0
    SERVER_STATE.tool_call_counter = 0
    SERVER_STATE.sessions.clear()
    SERVER_STATE.turns.clear()
    SERVER_STATE.approvals.clear()


def test_session_lifecycle_methods_return_concrete_payloads() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]
    assert session_id == "session-0001"
    assert started["result"]["session"]["status"] == "active"

    listed = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "session/list"}))
    assert listed is not None
    assert listed["result"]["sessions"][0]["id"] == session_id

    resumed = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "session/resume",
                "params": {"session_id": session_id},
            }
        )
    )
    assert resumed is not None
    assert resumed["result"]["session"]["id"] == session_id

    turn_response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "hello"},
            }
        )
    )
    assert turn_response is not None

    read = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "session/read",
                "params": {"session_id": session_id},
            }
        )
    )
    assert read is not None
    assert read["result"]["session"]["id"] == session_id
    assert len(read["result"]["turns"]) == 1
    assert read["result"]["turns"][0]["status"] == "completed"


def test_turn_submit_emits_expected_notifications_order() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "t",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "ship"},
            }
        )
    )
    assert response is not None
    assert response["result"]["turn"]["status"] == "completed"

    methods = [item["method"] for item in notifications]
    assert methods == [
        "turn/started",
        "item/agentMessage/delta",
        "item/toolCall/started",
        "item/toolCall/completed",
        "turn/completed",
    ]


def test_turn_cancel_marks_terminal_and_blocks_duplicate_cancel() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "deploy",
                    "requires_approval": True,
                    "unified_diff": "--- a/app.py\n+++ b/app.py\n@@\n-old\n+new\n",
                },
            }
        )
    )
    assert response is not None
    turn_id = response["result"]["turn"]["id"]
    assert notifications[-1]["method"] == "approval/requested"

    first_cancel = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "cancel-1",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )
    assert first_cancel is not None
    assert first_cancel["result"]["turn"]["status"] == "cancelled"

    second_cancel = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "cancel-2",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )
    assert second_cancel is not None
    assert second_cancel["error"]["code"] == -32003


def test_turn_submit_rejects_non_boolean_requires_approval() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "deploy", "requires_approval": "yes"},
            }
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "requires_approval_must_be_boolean"
    assert notifications == []


def test_turn_submit_rejects_whitespace_session_id() -> None:
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": "   ", "input": "deploy"},
            }
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "session_id_required"
    assert notifications == []


def test_turn_submit_requires_non_empty_diff_when_approval_is_required() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "deploy", "requires_approval": True},
            }
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "diff_required_when_requires_approval"
    assert notifications == []


def test_turn_submit_rejects_blank_diff_when_approval_is_required() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "deploy",
                    "requires_approval": True,
                    "unified_diff": "   ",
                },
            }
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "diff_must_be_non_empty_string"
    assert notifications == []


def test_request_with_invalid_id_type_returns_invalid_request() -> None:
    response = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": {"not": "scalar"}, "method": "health/check"}))
    assert response is not None
    assert response["error"]["code"] == -32600
    assert response["error"]["data"]["reason"] == "id"


def test_approval_requested_and_grant_reject_flow_works() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    gated_response, gated_notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "gated",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "run",
                    "requires_approval": True,
                    "unified_diff": "--- a/main.py\n+++ b/main.py\n@@\n-print('x')\n+print('y')\n",
                },
            }
        )
    )
    assert gated_response is not None
    approval_id = gated_response["result"]["approval"]["id"]
    assert gated_response["result"]["approval"]["diff"].startswith("--- a/main.py")
    assert gated_notifications[-1]["method"] == "approval/requested"
    assert gated_notifications[-1]["params"]["diff"].startswith("--- a/main.py")

    grant_response, grant_notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "grant",
                "method": "approval/grant",
                "params": {"approval_id": approval_id},
            }
        )
    )
    assert grant_response is not None
    assert grant_response["result"]["approval"]["status"] == "granted"
    assert [item["method"] for item in grant_notifications] == [
        "item/toolCall/started",
        "item/toolCall/completed",
        "turn/completed",
    ]

    reject_submit_response, reject_submit_notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "reject-submit",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "stop",
                    "requires_approval": True,
                    "diff": "--- a/main.py\n+++ b/main.py\n@@\n-stop\n+continue\n",
                },
            }
        )
    )
    assert reject_submit_response is not None
    assert reject_submit_notifications[-1]["method"] == "approval/requested"
    reject_approval_id = reject_submit_response["result"]["approval"]["id"]

    reject_response, reject_notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "reject",
                "method": "approval/reject",
                "params": {"approval_id": reject_approval_id},
            }
        )
    )
    assert reject_response is not None
    assert reject_response["result"]["approval"]["status"] == "rejected"
    assert [item["method"] for item in reject_notifications] == ["turn/completed"]


def test_serve_stdio_writes_response_and_notifications_as_jsonl() -> None:
    in_stream = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": "t",
                        "method": "turn/submit",
                        "params": {"session_id": "session-0001", "input": "hello"},
                    }
                ),
            ]
        )
        + "\n"
    )
    out_stream = io.StringIO()

    rc = serve_stdio(in_stream=in_stream, out_stream=out_stream)
    assert rc == 0

    lines = [json.loads(line) for line in out_stream.getvalue().splitlines() if line.strip()]
    assert len(lines) == 7
    assert lines[0]["id"] == "s"
    assert lines[1]["id"] == "t"
    assert [line["method"] for line in lines[2:]] == [
        "turn/started",
        "item/agentMessage/delta",
        "item/toolCall/started",
        "item/toolCall/completed",
        "turn/completed",
    ]


def test_fail_loud_jsonrpc_errors_are_preserved() -> None:
    unknown = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "bogus/method"}))
    assert unknown is not None
    assert unknown["error"]["code"] == -32601

    invalid = process_jsonrpc_line("{bad json")
    assert invalid is not None
    assert invalid["error"]["code"] == -32700


def test_turn_submit_notification_without_id_emits_notifications_only() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "hello from notification"},
            }
        )
    )
    assert response is None
    assert [item["method"] for item in notifications] == [
        "turn/started",
        "item/agentMessage/delta",
        "item/toolCall/started",
        "item/toolCall/completed",
        "turn/completed",
    ]

    read = process_jsonrpc_line(
        json.dumps({"jsonrpc": "2.0", "id": "read", "method": "session/read", "params": {"session_id": session_id}})
    )
    assert read is not None
    assert len(read["result"]["turns"]) == 1
    assert read["result"]["turns"][0]["status"] == "completed"


def test_invalid_params_type_returns_invalid_params_error() -> None:
    response = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "x", "method": "turn/submit", "params": []}))
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "params_must_be_object"


def test_approval_diff_must_be_string() -> None:
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "t",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "review", "requires_approval": True, "unified_diff": 123},
            }
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "diff_must_be_string"


def test_config_read_reports_canonical_supported_methods() -> None:
    response = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "cfg", "method": "config/read"}))
    assert response is not None
    assert response["result"]["supported_methods"] == sorted(SUPPORTED_METHODS)


def test_request_id_boolean_is_rejected_as_invalid_request() -> None:
    # @trace WL-9500
    response = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": True, "method": "health/check"}))
    assert response is not None
    assert response["error"]["code"] == -32600
    assert response["error"]["data"]["reason"] == "id"


def test_session_resume_with_whitespace_session_id_fails_validation() -> None:
    # @trace WL-9501
    response = process_jsonrpc_line(
        json.dumps({"jsonrpc": "2.0", "id": "resume", "method": "session/resume", "params": {"session_id": "   "}})
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "session_id_required"


def test_turn_submit_rejects_non_string_input_during_parse_stage() -> None:
    # @trace WL-9502
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response = process_jsonrpc_line(
        json.dumps(
            {"jsonrpc": "2.0", "id": "t", "method": "turn/submit", "params": {"session_id": session_id, "input": 9}}
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "input_must_be_string"


def test_approval_grant_follows_success_path_and_completes_turn() -> None:
    # @trace WL-9503
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    gated = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "gated",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "ship",
                    "requires_approval": True,
                    "diff": "--- a/x\n+++ b/x\n@@\n-x\n+y\n",
                },
            }
        )
    )
    assert gated is not None
    approval_id = gated["result"]["approval"]["id"]

    granted, notifications = process_jsonrpc_line_full(
        json.dumps(
            {"jsonrpc": "2.0", "id": "grant", "method": "approval/grant", "params": {"approval_id": approval_id}}
        )
    )
    assert granted is not None
    assert granted["result"]["approval"]["status"] == "granted"
    assert [n["method"] for n in notifications][-1] == "turn/completed"


def test_session_read_for_missing_session_returns_not_found_branch() -> None:
    # @trace WL-9504
    response = process_jsonrpc_line(
        json.dumps({"jsonrpc": "2.0", "id": "read", "method": "session/read", "params": {"session_id": "session-9999"}})
    )
    assert response is not None
    assert response["error"]["code"] == -32001


def test_approval_requires_diff_when_enabled_discovery_phase() -> None:
    # @trace WL-9505
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    response = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "t",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "ship", "requires_approval": True},
            }
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "diff_required_when_requires_approval"


def test_turn_cancel_requires_turn_id_validation_gate() -> None:
    # @trace WL-9506
    response = process_jsonrpc_line(
        json.dumps({"jsonrpc": "2.0", "id": "cancel", "method": "turn/cancel", "params": {}})
    )
    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "turn_id_required"


def test_approval_reject_follows_recovery_path_and_rejects_turn() -> None:
    # @trace WL-9507
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    gated = process_jsonrpc_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "gated",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "ship",
                    "requires_approval": True,
                    "unified_diff": "--- a/x\n+++ b/x\n@@\n-x\n+y\n",
                },
            }
        )
    )
    assert gated is not None
    approval_id = gated["result"]["approval"]["id"]

    rejected, notifications = process_jsonrpc_line_full(
        json.dumps(
            {"jsonrpc": "2.0", "id": "reject", "method": "approval/reject", "params": {"approval_id": approval_id}}
        )
    )
    assert rejected is not None
    assert rejected["result"]["approval"]["status"] == "rejected"
    assert [n["method"] for n in notifications] == ["turn/completed"]


def test_session_resume_uses_existing_session_lookup_hit() -> None:
    # @trace WL-9508
    started = process_jsonrpc_line(json.dumps({"jsonrpc": "2.0", "id": "start", "method": "session/start"}))
    assert started is not None
    session_id = started["result"]["session"]["id"]

    resumed = process_jsonrpc_line(
        json.dumps({"jsonrpc": "2.0", "id": "resume", "method": "session/resume", "params": {"session_id": session_id}})
    )
    assert resumed is not None
    assert resumed["result"]["session"]["id"] == session_id


def test_session_resume_uses_missing_session_lookup_miss() -> None:
    # @trace WL-9509
    response = process_jsonrpc_line(
        json.dumps(
            {"jsonrpc": "2.0", "id": "resume", "method": "session/resume", "params": {"session_id": "session-4040"}}
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32001
