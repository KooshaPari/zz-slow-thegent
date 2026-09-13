"""Tests for thegent ACP server adapter.

Covers:
- ACPServerAdapter initialisation and agent loading
- handle_acp_message: happy path (task -> result), bad type, unknown agent
- handle_jsonrpc: initialize, agent/spawn, agent/message, agent/stop,
  unknown method
- AgentSession: state management, stop signal
- Starlette HTTP app: /health, /rpc, /acp endpoints
- stdio dispatch: task envelope and JSON-RPC envelope routing
- _rpc_error helper

Traces to: FR-ACP-001 (ACP Server Adapter)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient
from typer.testing import CliRunner

from thegent.adapters.acp_server import (
    ACP_DEFAULT_PORT,
    ACPServerAdapter,
    AgentSession,
    _rpc_error,
)
from thegent.adapters.acp_server import (
    app as acp_cli_app,
)
from thegent.agents.base import AgentRunner, RunResult

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_runner(stdout: str = "done", stderr: str = "", exit_code: int = 0, timed_out: bool = False) -> AgentRunner:
    """Return a mock AgentRunner that returns a fixed RunResult."""
    runner = MagicMock(spec=AgentRunner)
    runner.run.return_value = RunResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
    )
    return runner


@pytest.fixture
def adapter() -> ACPServerAdapter:
    """Return an ACPServerAdapter with no real agents loaded."""
    with (
        patch("thegent.adapters.acp_server.get_runner", return_value=None),
        patch("thegent.adapters.acp_server.AGENT_NAMES", []),
    ):
        inst = ACPServerAdapter()
    return inst


@pytest.fixture
def adapter_with_agent() -> tuple[ACPServerAdapter, AgentRunner]:
    """Return an adapter pre-loaded with a mock 'claude' runner."""
    runner = _make_runner(stdout="Hello from claude")
    with (
        patch("thegent.adapters.acp_server.get_runner", return_value=None),
        patch("thegent.adapters.acp_server.AGENT_NAMES", []),
    ):
        inst = ACPServerAdapter()
    inst.agents["claude"] = runner
    return inst, runner


# ---------------------------------------------------------------------------
# AgentSession
# ---------------------------------------------------------------------------


class TestAgentSession:
    """FR-ACP-001: Session state management."""

    def test_add_message_appends_to_history(self) -> None:
        runner = _make_runner()
        session = AgentSession("s-1", runner)
        session.add_message("user", "Hello")
        session.add_message("assistant", "World")
        assert session.conversation_history == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "World"},
        ]

    def test_stop_sets_is_running_false(self) -> None:
        runner = _make_runner()
        session = AgentSession("s-2", runner)
        session.is_running = True
        session.stop()
        assert not session.is_running

    def test_stop_fires_stop_event(self) -> None:
        runner = _make_runner()
        session = AgentSession("s-3", runner)
        assert not session._stop_event.is_set()
        session.stop()
        assert session._stop_event.is_set()

    def test_session_stores_cwd(self) -> None:
        runner = _make_runner()
        cwd = Path("/tmp/workspace")
        session = AgentSession("s-4", runner, cwd=cwd)
        assert session.cwd == cwd


# ---------------------------------------------------------------------------
# _rpc_error helper
# ---------------------------------------------------------------------------


class TestRpcErrorHelper:
    """FR-ACP-001: JSON-RPC error envelope construction."""

    def test_returns_jsonrpc_error_envelope(self) -> None:
        result = _rpc_error(42, -32602, "bad param")
        assert result == {
            "jsonrpc": "2.0",
            "id": 42,
            "error": {"code": -32602, "message": "bad param"},
        }

    def test_none_id_preserved(self) -> None:
        result = _rpc_error(None, -32700, "parse error")
        assert result["id"] is None


class TestCliEntryPoint:
    """CLI wiring for module entrypoint."""

    def test_help_exits_zero(self) -> None:
        result = runner.invoke(acp_cli_app, ["--help"])
        assert result.exit_code == 0

    def test_default_mode_runs_stdio(self) -> None:
        with (
            patch("thegent.adapters.acp_server.ACPServerAdapter") as mock_adapter_cls,
            patch("thegent.adapters.acp_server.asyncio.run") as mock_asyncio_run,
        ):
            result = runner.invoke(acp_cli_app, [])

        assert result.exit_code == 0
        mock_adapter = mock_adapter_cls.return_value
        mock_asyncio_run.assert_called_once_with(mock_adapter.run_stdio.return_value)
        mock_adapter.run_http.assert_not_called()

    def test_http_mode_runs_http_server(self) -> None:
        with (
            patch("thegent.adapters.acp_server.ACPServerAdapter") as mock_adapter_cls,
            patch("thegent.adapters.acp_server.asyncio.run") as mock_asyncio_run,
        ):
            result = runner.invoke(
                acp_cli_app,
                ["--http", "--host", "0.0.0.0", "--port", str(ACP_DEFAULT_PORT + 1)],
            )

        assert result.exit_code == 0
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.run_http.assert_called_once_with(host="0.0.0.0", port=ACP_DEFAULT_PORT + 1)
        mock_asyncio_run.assert_not_called()


# ---------------------------------------------------------------------------
# ACPServerAdapter: agent loading
# ---------------------------------------------------------------------------


class TestAdapterAgentLoading:
    """FR-ACP-001: Agent registry loading on init."""

    def test_agents_dict_populated_from_registry(self) -> None:
        runner = _make_runner()
        with (
            patch("thegent.adapters.acp_server.AGENT_NAMES", ["claude", "gemini"]),
            patch("thegent.adapters.acp_server.get_runner", return_value=runner),
        ):
            inst = ACPServerAdapter()
        assert "claude" in inst.agents
        assert "gemini" in inst.agents

    def test_failed_agent_load_is_skipped(self) -> None:
        def _bad_runner(name: str) -> AgentRunner | None:
            if name == "bad":
                raise RuntimeError("boom")
            return _make_runner()

        with (
            patch("thegent.adapters.acp_server.AGENT_NAMES", ["bad", "claude"]),
            patch("thegent.adapters.acp_server.get_runner", side_effect=_bad_runner),
        ):
            inst = ACPServerAdapter()
        assert "bad" not in inst.agents
        assert "claude" in inst.agents

    def test_none_runner_is_excluded(self) -> None:
        with (
            patch("thegent.adapters.acp_server.AGENT_NAMES", ["claude"]),
            patch("thegent.adapters.acp_server.get_runner", return_value=None),
        ):
            inst = ACPServerAdapter()
        assert "claude" not in inst.agents


# ---------------------------------------------------------------------------
# handle_acp_message
# ---------------------------------------------------------------------------


class TestHandleAcpMessage:
    """FR-ACP-001: Native ACP message dispatch."""

    @pytest.mark.asyncio
    async def test_task_returns_result(self, adapter_with_agent: tuple) -> None:
        inst, _runner = adapter_with_agent
        response = await inst.handle_acp_message(
            {
                "type": "task",
                "payload": {"agent": "claude", "prompt": "hi"},
                "agent_id": "caller-1",
            }
        )
        assert response["type"] == "result"
        assert response["result"]["stdout"] == "Hello from claude"
        assert response["result"]["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_unsupported_type_returns_error(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_acp_message({"type": "unknown", "payload": {}, "agent_id": "x"})
        assert response["type"] == "error"
        assert "UNSUPPORTED_TYPE" in response["error"]["code"]

    @pytest.mark.asyncio
    async def test_unknown_agent_returns_error(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_acp_message(
            {
                "type": "task",
                "payload": {"agent": "nonexistent", "prompt": "hi"},
                "agent_id": "x",
            }
        )
        assert response["type"] == "error"
        assert "AGENT_NOT_FOUND" in response["error"]["code"]

    @pytest.mark.asyncio
    async def test_caller_agent_id_preserved_on_error(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_acp_message(
            {"type": "task", "payload": {"agent": "ghost"}, "agent_id": "caller-99"}
        )
        assert response["agent_id"] == "caller-99"

    @pytest.mark.asyncio
    async def test_session_created_in_sessions_dict(self, adapter_with_agent: tuple) -> None:
        inst, _ = adapter_with_agent
        await inst.handle_acp_message(
            {
                "type": "task",
                "payload": {"agent": "claude", "prompt": "go"},
                "agent_id": "c",
            }
        )
        assert len(inst.sessions) == 1

    @pytest.mark.asyncio
    async def test_runner_execution_error_returns_error_type(self, adapter: ACPServerAdapter) -> None:
        bad_runner = MagicMock(spec=AgentRunner)
        bad_runner.run.side_effect = RuntimeError("crash")
        adapter.agents["crasher"] = bad_runner

        response = await adapter.handle_acp_message(
            {
                "type": "task",
                "payload": {"agent": "crasher", "prompt": "boom"},
                "agent_id": "x",
            }
        )
        assert response["type"] == "error"


# ---------------------------------------------------------------------------
# handle_jsonrpc: initialize
# ---------------------------------------------------------------------------


class TestRpcInitialize:
    """FR-ACP-001: initialize method."""

    @pytest.mark.asyncio
    async def test_initialize_lists_agents(self, adapter_with_agent: tuple) -> None:
        inst, _ = adapter_with_agent
        response = await inst.handle_jsonrpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "agents" in response["result"]["capabilities"]
        assert "claude" in response["result"]["capabilities"]["agents"]

    @pytest.mark.asyncio
    async def test_initialize_includes_supported_methods(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc({"id": 1, "method": "initialize", "params": {}})
        methods = response["result"]["capabilities"]["methods"]
        assert "agent/spawn" in methods
        assert "agent/stop" in methods


# ---------------------------------------------------------------------------
# handle_jsonrpc: agent/spawn
# ---------------------------------------------------------------------------


class TestRpcSpawn:
    """FR-ACP-001: agent/spawn method."""

    @pytest.mark.asyncio
    async def test_spawn_known_agent_returns_result(self, adapter_with_agent: tuple) -> None:
        inst, _ = adapter_with_agent
        response = await inst.handle_jsonrpc(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "hello"},
            }
        )
        assert "result" in response
        assert response["result"]["stdout"] == "Hello from claude"
        assert "agent_id" in response["result"]

    @pytest.mark.asyncio
    async def test_spawn_unknown_agent_returns_error(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc({"id": 2, "method": "agent/spawn", "params": {"agent": "ghost"}})
        assert "error" in response
        assert response["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_spawn_creates_session(self, adapter_with_agent: tuple) -> None:
        inst, _ = adapter_with_agent
        await inst.handle_jsonrpc(
            {
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "go"},
            }
        )
        assert len(inst.sessions) == 1

    @pytest.mark.asyncio
    async def test_spawn_runner_exception_returns_error(self, adapter: ACPServerAdapter) -> None:
        bad = MagicMock(spec=AgentRunner)
        bad.run.side_effect = ValueError("oops")
        adapter.agents["oops"] = bad
        response = await adapter.handle_jsonrpc(
            {
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "oops", "prompt": "x"},
            }
        )
        assert "error" in response

    @pytest.mark.asyncio
    async def test_spawn_with_cwd(self, adapter_with_agent: tuple, tmp_path: Path) -> None:
        inst, _ = adapter_with_agent
        response = await inst.handle_jsonrpc(
            {
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "go", "cwd": str(tmp_path)},
            }
        )
        assert "result" in response
        # Verify the session captured the cwd
        session_id = response["result"]["agent_id"]
        assert inst.sessions[session_id].cwd == tmp_path


# ---------------------------------------------------------------------------
# handle_jsonrpc: agent/message
# ---------------------------------------------------------------------------


class TestRpcMessage:
    """FR-ACP-001: agent/message method."""

    @pytest.mark.asyncio
    async def test_message_requires_agent_id(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc({"id": 3, "method": "agent/message", "params": {"message": "hi"}})
        assert response["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_message_unknown_session(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc(
            {
                "id": 3,
                "method": "agent/message",
                "params": {"agent_id": "ghost-session", "message": "hi"},
            }
        )
        assert response["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_message_sends_to_existing_session(self, adapter_with_agent: tuple) -> None:
        inst, runner = adapter_with_agent
        # Spawn first
        spawn_resp = await inst.handle_jsonrpc(
            {
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "init"},
            }
        )
        session_id = spawn_resp["result"]["agent_id"]

        runner.run.return_value = RunResult(exit_code=0, stdout="follow-up reply", stderr="", timed_out=False)

        msg_resp = await inst.handle_jsonrpc(
            {
                "id": 3,
                "method": "agent/message",
                "params": {"agent_id": session_id, "message": "follow up"},
            }
        )
        assert msg_resp["result"]["stdout"] == "follow-up reply"

    @pytest.mark.asyncio
    async def test_message_appends_to_conversation_history(self, adapter_with_agent: tuple) -> None:
        inst, _ = adapter_with_agent
        spawn_resp = await inst.handle_jsonrpc(
            {
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "start"},
            }
        )
        session_id = spawn_resp["result"]["agent_id"]

        await inst.handle_jsonrpc(
            {
                "id": 3,
                "method": "agent/message",
                "params": {"agent_id": session_id, "message": "next"},
            }
        )

        session = inst.sessions[session_id]
        roles = [m["role"] for m in session.conversation_history]
        assert roles.count("user") >= 2


# ---------------------------------------------------------------------------
# handle_jsonrpc: agent/stop
# ---------------------------------------------------------------------------


class TestRpcStop:
    """FR-ACP-001: agent/stop method."""

    @pytest.mark.asyncio
    async def test_stop_requires_agent_id(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc({"id": 4, "method": "agent/stop", "params": {}})
        assert response["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_stop_unknown_session(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc({"id": 4, "method": "agent/stop", "params": {"agent_id": "ghost"}})
        assert response["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_stop_known_session(self, adapter_with_agent: tuple) -> None:
        inst, _ = adapter_with_agent
        spawn_resp = await inst.handle_jsonrpc(
            {
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "go"},
            }
        )
        session_id = spawn_resp["result"]["agent_id"]

        stop_resp = await inst.handle_jsonrpc({"id": 4, "method": "agent/stop", "params": {"agent_id": session_id}})
        assert stop_resp["result"]["stopped"] is True
        assert stop_resp["result"]["agent_id"] == session_id

    @pytest.mark.asyncio
    async def test_stop_marks_session_stopped(self, adapter_with_agent: tuple) -> None:
        inst, _ = adapter_with_agent
        spawn_resp = await inst.handle_jsonrpc(
            {
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "go"},
            }
        )
        session_id = spawn_resp["result"]["agent_id"]

        await inst.handle_jsonrpc({"id": 4, "method": "agent/stop", "params": {"agent_id": session_id}})

        assert inst.sessions[session_id]._stop_event.is_set()


# ---------------------------------------------------------------------------
# handle_jsonrpc: unknown method
# ---------------------------------------------------------------------------


class TestRpcUnknownMethod:
    """FR-ACP-001: unknown method returns -32601."""

    @pytest.mark.asyncio
    async def test_unknown_method_error_code(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc({"id": 99, "method": "nonexistent/method", "params": {}})
        assert response["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_none_method_error_code(self, adapter: ACPServerAdapter) -> None:
        response = await adapter.handle_jsonrpc({"id": 99})
        assert "error" in response


# ---------------------------------------------------------------------------
# Starlette HTTP app
# ---------------------------------------------------------------------------


class TestStarletteApp:
    """FR-ACP-001: HTTP endpoints via Starlette."""

    @pytest.fixture
    def client(self, adapter_with_agent: tuple) -> TestClient:
        inst, _ = adapter_with_agent
        app = inst.build_starlette_app()
        return TestClient(app, raise_server_exceptions=True)

    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_rpc_initialize(self, client: TestClient) -> None:
        resp = client.post(
            "/rpc",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "result" in body
        assert "capabilities" in body["result"]

    def test_rpc_invalid_json_returns_400(self, client: TestClient) -> None:
        resp = client.post("/rpc", content=b"not json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 400

    def test_rpc_spawn_known_agent(self, client: TestClient) -> None:
        resp = client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "claude", "prompt": "hi"},
            },
        )
        assert resp.status_code == 200
        assert "result" in resp.json()

    def test_rpc_spawn_unknown_agent_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "agent/spawn",
                "params": {"agent": "ghost"},
            },
        )
        assert resp.status_code == 422

    def test_acp_task_message(self, client: TestClient) -> None:
        resp = client.post(
            "/acp",
            json={
                "type": "task",
                "payload": {"agent": "claude", "prompt": "go"},
                "agent_id": "caller-1",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["type"] == "result"

    def test_acp_invalid_json_returns_400(self, client: TestClient) -> None:
        resp = client.post("/acp", content=b"bad", headers={"Content-Type": "application/json"})
        assert resp.status_code == 400

    def test_acp_error_type_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/acp",
            json={
                "type": "task",
                "payload": {"agent": "ghost", "prompt": "x"},
                "agent_id": "c",
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# resolve_runner: on-demand loading
# ---------------------------------------------------------------------------


class TestResolveRunner:
    """FR-ACP-001: On-demand runner resolution."""

    def test_resolve_known_agent_from_cache(self, adapter_with_agent: tuple) -> None:
        inst, runner = adapter_with_agent
        resolved = inst._resolve_runner("claude")
        assert resolved is runner

    def test_resolve_loads_from_registry_if_not_cached(self, adapter: ACPServerAdapter) -> None:
        runner = _make_runner()
        with patch("thegent.adapters.acp_server.get_runner", return_value=runner):
            resolved = adapter._resolve_runner("new-agent")
        assert resolved is runner
        assert "new-agent" in adapter.agents

    def test_resolve_returns_none_for_unknown(self, adapter: ACPServerAdapter) -> None:
        with patch("thegent.adapters.acp_server.get_runner", return_value=None):
            resolved = adapter._resolve_runner("nonexistent")
        assert resolved is None


# ---------------------------------------------------------------------------
# ACP_DEFAULT_PORT constant
# ---------------------------------------------------------------------------


class TestDefaultPort:
    """FR-ACP-001: Default port configuration."""

    def test_default_port_is_integer(self) -> None:
        assert isinstance(ACP_DEFAULT_PORT, int)

    def test_default_port_is_positive(self) -> None:
        assert ACP_DEFAULT_PORT > 0
