"""Tests for ACP server session management endpoints.

Covers:
- SessionEndpoints.attach: new session, existing session, backend unavailable,
  backend create failure
- SessionEndpoints.inspect: captured lines, empty capture, no backend
- SessionEndpoints.send: send_keys present, send_keys absent, no backend
- ACPServerAdapter._rpc_session_attach: happy paths, missing param, error
- ACPServerAdapter._rpc_session_inspect: happy paths, missing param, no backend
- ACPServerAdapter._rpc_session_send: happy paths, missing param
- Starlette /rpc HTTP route for all three session methods
- initialize capabilities listing

Traces to: FR-SES-001 (Session backend must be pluggable and auto-detected)
           FR-ACP-001 (ACP Server Adapter)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from thegent.adapters.acp_server import (
    ACPServerAdapter,
    SessionEndpoints,
)
from thegent.session.zmx_backend import ZmxBackend, ZmxSession

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_backend(
    *,
    name: str = "zmx",
    available: bool = True,
    sessions: list[ZmxSession] | None = None,
    create_ok: bool = True,
    capture_text: str = "",
    has_send_keys: bool = False,
    send_keys_ok: bool = True,
) -> MagicMock:
    """Build a mock SessionBackend for unit tests."""
    backend = MagicMock(spec=ZmxBackend)
    backend.name = name
    backend.available = available
    backend.list.return_value = sessions or []
    backend.create.return_value = create_ok
    backend.capture.return_value = capture_text
    backend.attach.return_value = True

    if has_send_keys:
        backend.send_keys = MagicMock(return_value=send_keys_ok)
    else:
        # Ensure the attribute does not exist so getattr(..., None) returns None
        del backend.send_keys

    return backend


@pytest.fixture
def no_agent_adapter() -> ACPServerAdapter:
    """ACPServerAdapter with no real agents and a mock SessionEndpoints."""
    with (
        patch("thegent.adapters.acp_server.get_runner", return_value=None),
        patch("thegent.adapters.acp_server.AGENT_NAMES", []),
    ):
        return ACPServerAdapter()


@pytest.fixture
def adapter_with_mock_sessions(
    no_agent_adapter: ACPServerAdapter,
) -> tuple[ACPServerAdapter, MagicMock]:
    """Adapter paired with a mock backend wired into its SessionEndpoints."""
    backend = _make_backend()
    no_agent_adapter.session_endpoints = SessionEndpoints(backend=backend)
    return no_agent_adapter, backend


@pytest.fixture
def rpc_client(no_agent_adapter: ACPServerAdapter) -> TestClient:
    """Starlette TestClient for the adapter."""
    app = no_agent_adapter.build_starlette_app()
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# SessionEndpoints.attach
# ---------------------------------------------------------------------------


class TestSessionEndpointsAttach:
    """FR-SES-001: session/attach helper."""

    def test_attach_creates_new_session_when_name_not_found(self) -> None:
        backend = _make_backend(sessions=[], create_ok=True)
        ep = SessionEndpoints(backend=backend)

        result = ep.attach("my-session")

        assert result["session_id"] == "my-session"
        assert result["status"] == "created"
        backend.create.assert_called_once_with("my-session", ["/bin/sh"])

    def test_attach_returns_attached_when_session_exists(self) -> None:
        existing = ZmxSession(name="existing-session", state="running")
        backend = _make_backend(sessions=[existing], create_ok=True)
        ep = SessionEndpoints(backend=backend)

        result = ep.attach("existing-session")

        assert result["session_id"] == "existing-session"
        assert result["status"] == "attached"
        backend.create.assert_not_called()

    def test_attach_returns_unavailable_when_no_backend(self) -> None:
        ep = SessionEndpoints(backend=None)
        # Prevent lazy resolution from finding a real backend
        ep._backend_resolved = True

        result = ep.attach("any-session")

        assert result["status"] == "unavailable"
        assert "error" in result

    def test_attach_returns_error_when_create_fails(self) -> None:
        backend = _make_backend(sessions=[], create_ok=False)
        ep = SessionEndpoints(backend=backend)

        result = ep.attach("fail-session")

        assert result["status"] == "error"
        assert "error" in result

    def test_attach_does_not_create_when_session_already_exists(self) -> None:
        sessions = [ZmxSession(name="already-there", state="detached")]
        backend = _make_backend(sessions=sessions)
        ep = SessionEndpoints(backend=backend)

        ep.attach("already-there")

        backend.create.assert_not_called()

    def test_attach_lazy_resolves_backend_on_first_call(self) -> None:
        backend = _make_backend()
        ep = SessionEndpoints(backend=None)
        with patch(
            "thegent.adapters.acp_server.resolve_session_backend", return_value=backend
        ):
            result = ep.attach("lazy-session")

        assert result["status"] == "created"


# ---------------------------------------------------------------------------
# SessionEndpoints.inspect
# ---------------------------------------------------------------------------


class TestSessionEndpointsInspect:
    """FR-SES-001: session/inspect helper."""

    def test_inspect_returns_lines_list(self) -> None:
        backend = _make_backend(capture_text="line1\nline2\nline3")
        ep = SessionEndpoints(backend=backend)

        result = ep.inspect("my-session", 50)

        assert result["lines"] == ["line1", "line2", "line3"]
        assert result["backend"] == "zmx"

    def test_inspect_passes_last_lines_to_capture(self) -> None:
        backend = _make_backend(capture_text="only-one-line")
        ep = SessionEndpoints(backend=backend)

        ep.inspect("s1", 10)

        backend.capture.assert_called_once_with("s1", 10)

    def test_inspect_returns_empty_list_on_empty_capture(self) -> None:
        backend = _make_backend(capture_text="")
        ep = SessionEndpoints(backend=backend)

        result = ep.inspect("empty-session", 50)

        assert result["lines"] == []

    def test_inspect_returns_error_when_no_backend(self) -> None:
        ep = SessionEndpoints(backend=None)
        ep._backend_resolved = True

        result = ep.inspect("s", 5)

        assert result["lines"] == []
        assert "error" in result
        assert result["backend"] == "none"

    def test_inspect_backend_name_included_in_result(self) -> None:
        backend = _make_backend(name="custom-backend", capture_text="x")
        ep = SessionEndpoints(backend=backend)

        result = ep.inspect("s", 1)

        assert result["backend"] == "custom-backend"


# ---------------------------------------------------------------------------
# SessionEndpoints.send
# ---------------------------------------------------------------------------


class TestSessionEndpointsSend:
    """FR-SES-001: session/send helper."""

    def test_send_keys_called_with_text_when_backend_supports_it(self) -> None:
        backend = _make_backend(has_send_keys=True, send_keys_ok=True)
        ep = SessionEndpoints(backend=backend)

        result = ep.send("s1", "hello", enter=False)

        assert result == {"success": True}
        backend.send_keys.assert_called_once_with("s1", "hello")

    def test_send_keys_appends_newline_when_enter_is_true(self) -> None:
        backend = _make_backend(has_send_keys=True, send_keys_ok=True)
        ep = SessionEndpoints(backend=backend)

        ep.send("s1", "cmd", enter=True)

        backend.send_keys.assert_called_once_with("s1", "cmd\n")

    def test_send_returns_success_false_when_send_keys_fails(self) -> None:
        backend = _make_backend(has_send_keys=True, send_keys_ok=False)
        ep = SessionEndpoints(backend=backend)

        result = ep.send("s1", "cmd")

        assert result == {"success": False}

    def test_send_returns_false_when_backend_lacks_send_keys(self) -> None:
        backend = _make_backend(has_send_keys=False)
        ep = SessionEndpoints(backend=backend)

        result = ep.send("s1", "text")

        assert result == {"success": False}

    def test_send_returns_false_when_no_backend(self) -> None:
        ep = SessionEndpoints(backend=None)
        ep._backend_resolved = True

        result = ep.send("s1", "x")

        assert result == {"success": False}


# ---------------------------------------------------------------------------
# ACPServerAdapter._rpc_session_attach
# ---------------------------------------------------------------------------


class TestRpcSessionAttach:
    """FR-ACP-001: session/attach RPC method."""

    @pytest.mark.asyncio
    async def test_attach_missing_session_name_returns_error(
        self, no_agent_adapter: ACPServerAdapter
    ) -> None:
        resp = await no_agent_adapter.handle_jsonrpc(
            {"id": 1, "method": "session/attach", "params": {}}
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_attach_new_session_returns_created(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.list.return_value = []
        backend.create.return_value = True

        resp = await inst.handle_jsonrpc(
            {
                "id": 1,
                "method": "session/attach",
                "params": {"session_name": "new-sess"},
            }
        )

        assert "result" in resp
        assert resp["result"]["session_id"] == "new-sess"
        assert resp["result"]["status"] == "created"

    @pytest.mark.asyncio
    async def test_attach_existing_session_returns_attached(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.list.return_value = [ZmxSession(name="old-sess", state="running")]

        resp = await inst.handle_jsonrpc(
            {
                "id": 1,
                "method": "session/attach",
                "params": {"session_name": "old-sess"},
            }
        )

        assert resp["result"]["status"] == "attached"

    @pytest.mark.asyncio
    async def test_attach_backend_unavailable_returns_rpc_error(
        self, no_agent_adapter: ACPServerAdapter
    ) -> None:
        no_agent_adapter.session_endpoints = SessionEndpoints(backend=None)
        no_agent_adapter.session_endpoints._backend_resolved = True

        resp = await no_agent_adapter.handle_jsonrpc(
            {"id": 1, "method": "session/attach", "params": {"session_name": "s"}}
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_attach_create_failure_returns_rpc_error(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.list.return_value = []
        backend.create.return_value = False

        resp = await inst.handle_jsonrpc(
            {"id": 1, "method": "session/attach", "params": {"session_name": "fail"}}
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32603


# ---------------------------------------------------------------------------
# ACPServerAdapter._rpc_session_inspect
# ---------------------------------------------------------------------------


class TestRpcSessionInspect:
    """FR-ACP-001: session/inspect RPC method."""

    @pytest.mark.asyncio
    async def test_inspect_missing_session_id_returns_error(
        self, no_agent_adapter: ACPServerAdapter
    ) -> None:
        resp = await no_agent_adapter.handle_jsonrpc(
            {"id": 2, "method": "session/inspect", "params": {}}
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_inspect_returns_lines_from_backend(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.capture.return_value = "alpha\nbeta\ngamma"

        resp = await inst.handle_jsonrpc(
            {
                "id": 2,
                "method": "session/inspect",
                "params": {"session_id": "s1", "last_lines": 3},
            }
        )

        assert "result" in resp
        assert resp["result"]["lines"] == ["alpha", "beta", "gamma"]

    @pytest.mark.asyncio
    async def test_inspect_default_last_lines_is_50(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.capture.return_value = ""

        await inst.handle_jsonrpc(
            {"id": 2, "method": "session/inspect", "params": {"session_id": "s1"}}
        )

        backend.capture.assert_called_once_with("s1", 50)

    @pytest.mark.asyncio
    async def test_inspect_no_backend_returns_rpc_error(
        self, no_agent_adapter: ACPServerAdapter
    ) -> None:
        no_agent_adapter.session_endpoints = SessionEndpoints(backend=None)
        no_agent_adapter.session_endpoints._backend_resolved = True

        resp = await no_agent_adapter.handle_jsonrpc(
            {"id": 2, "method": "session/inspect", "params": {"session_id": "s"}}
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_inspect_backend_name_in_result(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.name = "zmx"
        backend.capture.return_value = "output"

        resp = await inst.handle_jsonrpc(
            {"id": 2, "method": "session/inspect", "params": {"session_id": "s1"}}
        )

        assert resp["result"]["backend"] == "zmx"


# ---------------------------------------------------------------------------
# ACPServerAdapter._rpc_session_send
# ---------------------------------------------------------------------------


class TestRpcSessionSend:
    """FR-ACP-001: session/send RPC method."""

    @pytest.mark.asyncio
    async def test_send_missing_session_id_returns_error(
        self, no_agent_adapter: ACPServerAdapter
    ) -> None:
        resp = await no_agent_adapter.handle_jsonrpc(
            {"id": 3, "method": "session/send", "params": {"text": "hello"}}
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_send_returns_success_true_when_send_keys_works(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.send_keys = MagicMock(return_value=True)

        resp = await inst.handle_jsonrpc(
            {
                "id": 3,
                "method": "session/send",
                "params": {"session_id": "s1", "text": "ls", "enter": True},
            }
        )

        assert "result" in resp
        assert resp["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_send_returns_success_false_when_send_keys_missing(
        self, no_agent_adapter: ACPServerAdapter
    ) -> None:
        # Use a backend that was built without send_keys
        backend = _make_backend(has_send_keys=False)
        no_agent_adapter.session_endpoints = SessionEndpoints(backend=backend)

        resp = await no_agent_adapter.handle_jsonrpc(
            {
                "id": 3,
                "method": "session/send",
                "params": {"session_id": "s1", "text": "ls"},
            }
        )

        assert resp["result"]["success"] is False

    @pytest.mark.asyncio
    async def test_send_no_backend_returns_success_false(
        self, no_agent_adapter: ACPServerAdapter
    ) -> None:
        no_agent_adapter.session_endpoints = SessionEndpoints(backend=None)
        no_agent_adapter.session_endpoints._backend_resolved = True

        resp = await no_agent_adapter.handle_jsonrpc(
            {
                "id": 3,
                "method": "session/send",
                "params": {"session_id": "s", "text": "x"},
            }
        )
        assert resp["result"]["success"] is False

    @pytest.mark.asyncio
    async def test_send_default_enter_is_false(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> None:
        inst, backend = adapter_with_mock_sessions
        backend.send_keys = MagicMock(return_value=True)

        await inst.handle_jsonrpc(
            {
                "id": 3,
                "method": "session/send",
                "params": {"session_id": "s1", "text": "cmd"},
            }
        )

        # With enter=False no newline should be appended
        backend.send_keys.assert_called_once_with("s1", "cmd")


# ---------------------------------------------------------------------------
# Starlette HTTP /rpc — session endpoints
# ---------------------------------------------------------------------------


class TestStarletteSessionRoutes:
    """FR-ACP-001: session methods accessible over HTTP /rpc."""

    @pytest.fixture
    def client(
        self, adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock]
    ) -> TestClient:
        inst, _ = adapter_with_mock_sessions
        app = inst.build_starlette_app()
        return TestClient(app, raise_server_exceptions=True)

    def test_rpc_session_attach_known_session(
        self,
        client: TestClient,
        adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock],
    ) -> None:
        _, backend = adapter_with_mock_sessions
        backend.list.return_value = [ZmxSession(name="web-session", state="running")]

        resp = client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 10,
                "method": "session/attach",
                "params": {"session_name": "web-session"},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["result"]["status"] == "attached"

    def test_rpc_session_inspect_returns_200(
        self,
        client: TestClient,
        adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock],
    ) -> None:
        _, backend = adapter_with_mock_sessions
        backend.capture.return_value = "line-a\nline-b"

        resp = client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 11,
                "method": "session/inspect",
                "params": {"session_id": "s1"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["lines"] == ["line-a", "line-b"]

    def test_rpc_session_send_returns_200(
        self,
        client: TestClient,
        adapter_with_mock_sessions: tuple[ACPServerAdapter, MagicMock],
    ) -> None:
        _, backend = adapter_with_mock_sessions
        backend.send_keys = MagicMock(return_value=True)

        resp = client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 12,
                "method": "session/send",
                "params": {"session_id": "s1", "text": "echo hi", "enter": True},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["success"] is True

    def test_rpc_missing_param_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/rpc",
            json={"jsonrpc": "2.0", "id": 13, "method": "session/attach", "params": {}},
        )
        assert resp.status_code == 422

    def test_initialize_lists_session_methods(self, client: TestClient) -> None:
        resp = client.post(
            "/rpc",
            json={"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}},
        )
        methods = resp.json()["result"]["capabilities"]["methods"]
        assert "session/attach" in methods
        assert "session/inspect" in methods
        assert "session/send" in methods
