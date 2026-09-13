"""ACP Server adapter.

Provides server-side ACP protocol handling with JSON-RPC interface.
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import typer
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

# Import RunResult for type checking
from thegent.agents.base import RunResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ACP_DEFAULT_PORT = 8080

# ---------------------------------------------------------------------------
# Global agent registry (populated at runtime)
# ---------------------------------------------------------------------------

AGENT_NAMES: list[str] = []

# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------


def _rpc_error(id_val: int | None, code: int, message: str) -> dict[str, Any]:
    """Build a JSON-RPC error response."""
    return {
        "jsonrpc": "2.0",
        "id": id_val,
        "error": {"code": code, "message": message},
    }


async def _await_maybe(coro_or_value: Any) -> Any:
    """Await a coroutine if needed, otherwise return the value directly."""
    if inspect.isawaitable(coro_or_value):
        return await coro_or_value
    return coro_or_value


# ---------------------------------------------------------------------------
# AgentSession
# ---------------------------------------------------------------------------


@dataclass
class AgentSession:
    """Represents an active agent session."""

    session_id: str
    runner: Any  # AgentRunner
    cwd: Path | None = None
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    is_running: bool = True
    _stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self) -> None:
        if self.cwd is None:
            self.cwd = Path.cwd()

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def stop(self) -> None:
        """Signal the session to stop."""
        self.is_running = False
        self._stop_event.set()


# ---------------------------------------------------------------------------
# SessionEndpoints
# ---------------------------------------------------------------------------


class SessionEndpoints:
    """Handles session management endpoints for ACP server."""

    def __init__(self, backend: Any = None) -> None:
        self._backend = backend
        self._backend_resolved = False

    @property
    def backend(self) -> Any:
        """Lazily resolve the session backend."""
        if self._backend is None and not self._backend_resolved:
            self._backend = resolve_session_backend()
            self._backend_resolved = True
        return self._backend

    def attach(self, session_name: str) -> dict[str, Any]:
        """Attach to or create a session."""
        b = self.backend
        if b is None:
            return {"status": "unavailable", "error": "No backend available"}

        # Check if session exists
        for sess in b.list():
            if sess.name == session_name:
                return {"session_id": session_name, "status": "attached"}

        # Create new session
        if not b.create(session_name, ["/bin/sh"]):
            return {"status": "error", "error": "Failed to create session"}

        return {"session_id": session_name, "status": "created"}

    def inspect(self, session_id: str, last_lines: int = 50) -> dict[str, Any]:
        """Inspect a session's output."""
        b = self.backend
        if b is None:
            return {"lines": [], "backend": "none", "error": "No backend available"}

        text = b.capture(session_id, last_lines)
        lines = text.split("\n") if text else []
        return {"lines": lines, "backend": getattr(b, "name", "unknown")}

    def send(self, session_id: str, text: str, enter: bool = False) -> dict[str, Any]:
        """Send text to a session."""
        b = self.backend
        if b is None:
            return {"success": False}

        send_keys = getattr(b, "send_keys", None)
        if send_keys is None:
            return {"success": False}

        if enter:
            text = text + "\n"

        try:
            result = send_keys(session_id, text)
            return {"success": bool(result)}
        except Exception:
            return {"success": False}


def resolve_session_backend() -> Any:
    """Resolve the session backend (zmx by default)."""
    try:
        from thegent.session.zmx_backend import ZmxBackend

        return ZmxBackend()
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# ACPServerAdapter
# ---------------------------------------------------------------------------


class ACPServerAdapter:
    """ACP server adapter with JSON-RPC and ACP message handling."""

    SUPPORTED_METHODS: ClassVar[list[str]] = [
        "initialize",
        "agent/spawn",
        "agent/message",
        "agent/stop",
        "session/attach",
        "session/inspect",
        "session/send",
    ]

    def __init__(self) -> None:
        self.agents: dict[str, Any] = {}
        self.sessions: dict[str, AgentSession] = {}
        self.session_endpoints = SessionEndpoints()

        # Load agents from registry
        for name in AGENT_NAMES:
            try:
                runner = get_runner(name)
                if runner is not None:
                    self.agents[name] = runner
            except Exception:
                # Skip agents that fail to load
                pass

    def _resolve_runner(self, name: str) -> Any:
        """Resolve an agent runner by name."""
        if name in self.agents:
            return self.agents[name]
        runner = get_runner(name)
        if runner is not None:
            self.agents[name] = runner
        return runner

    async def handle_acp_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Handle a native ACP message."""
        msg_type = message.get("type")
        payload = message.get("payload", {})
        agent_id = message.get("agent_id", "unknown")

        if msg_type == "task":
            agent_name = payload.get("agent")
            if agent_name is None:
                return {
                    "type": "error",
                    "error": {"code": "MISSING_AGENT", "message": "Agent name required"},
                    "agent_id": agent_id,
                }
            runner = self._resolve_runner(agent_name)
            if runner is None:
                return {
                    "type": "error",
                    "error": {"code": "AGENT_NOT_FOUND", "message": f"Agent {agent_name} not found"},
                    "agent_id": agent_id,
                }

            session_id = str(uuid.uuid4())
            session = AgentSession(session_id=session_id, runner=runner)
            self.sessions[session_id] = session

            try:
                result = await _await_maybe(runner.run(payload.get("prompt", ""), cwd=payload.get("cwd")))
                if isinstance(result, RunResult):
                    stdout = result.stdout
                    stderr = result.stderr
                    exit_code = result.exit_code
                else:
                    stdout = str(result) if result else ""
                    stderr = ""
                    exit_code = 0
                return {
                    "type": "result",
                    "result": {
                        "exit_code": exit_code,
                        "stdout": stdout,
                        "stderr": stderr,
                    },
                    "agent_id": session_id,
                }
            except Exception as e:
                return {
                    "type": "error",
                    "error": {"code": "EXECUTION_ERROR", "message": str(e)},
                    "agent_id": agent_id,
                }

        return {
            "type": "error",
            "error": {"code": "UNSUPPORTED_TYPE", "message": f"Type {msg_type} not supported"},
            "agent_id": agent_id,
        }

    async def handle_jsonrpc(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})
        msg_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "capabilities": {
                        "agents": list(self.agents.keys()),
                        "methods": self.SUPPORTED_METHODS,
                    }
                },
            }

        if method == "agent/spawn":
            agent_name = params.get("agent")
            if not agent_name:
                return _rpc_error(msg_id, -32602, "Missing 'agent' parameter")
            runner = self._resolve_runner(agent_name)
            if runner is None:
                return _rpc_error(msg_id, -32602, f"Agent {agent_name} not found")

            session_id = str(uuid.uuid4())
            session = AgentSession(session_id=session_id, runner=runner)

            # Set cwd if provided
            cwd_param = params.get("cwd")
            if cwd_param:
                session.cwd = Path(cwd_param)

            self.sessions[session_id] = session
            session.add_message("user", params.get("prompt", ""))

            try:
                result = await _await_maybe(runner.run(params.get("prompt", ""), cwd=params.get("cwd")))
                if isinstance(result, RunResult):
                    stdout = result.stdout
                    stderr = result.stderr
                    exit_code = result.exit_code
                else:
                    stdout = str(result) if result else ""
                    stderr = ""
                    exit_code = 0
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "agent_id": session_id,
                        "exit_code": exit_code,
                        "stdout": stdout,
                        "stderr": stderr,
                    },
                }
            except Exception as e:
                return _rpc_error(msg_id, -32603, str(e))

        if method == "agent/message":
            agent_id = params.get("agent_id")
            if not agent_id:
                return _rpc_error(msg_id, -32602, "Missing 'agent_id' parameter")
            session = self.sessions.get(agent_id)
            if session is None:
                return _rpc_error(msg_id, -32602, f"Session {agent_id} not found")

            message = params.get("message", "")
            session.add_message("user", message)

            try:
                runner = session.runner
                result = await _await_maybe(runner.run(message, cwd=session.cwd))
                if isinstance(result, RunResult):
                    stdout = result.stdout
                    stderr = result.stderr
                else:
                    stdout = str(result) if result else ""
                    stderr = ""
                session.add_message("assistant", stdout)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "stdout": stdout,
                        "stderr": stderr,
                    },
                }
            except Exception as e:
                return _rpc_error(msg_id, -32603, str(e))

        if method == "agent/stop":
            agent_id = params.get("agent_id")
            if not agent_id:
                return _rpc_error(msg_id, -32602, "Missing 'agent_id' parameter")
            session = self.sessions.get(agent_id)
            if session is None:
                return _rpc_error(msg_id, -32602, f"Session {agent_id} not found")

            session.stop()
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"stopped": True, "agent_id": agent_id},
            }

        if method == "session/attach":
            session_name = params.get("session_name")
            if not session_name:
                return _rpc_error(msg_id, -32602, "Missing 'session_name' parameter")
            result = self.session_endpoints.attach(session_name)
            if result.get("status") == "unavailable":
                return _rpc_error(msg_id, -32603, "Session backend unavailable")
            if result.get("status") == "error":
                return _rpc_error(msg_id, -32603, result.get("error", "Failed to attach"))
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}

        if method == "session/inspect":
            session_id = params.get("session_id")
            if not session_id:
                return _rpc_error(msg_id, -32602, "Missing 'session_id' parameter")
            result = self.session_endpoints.inspect(session_id, params.get("last_lines", 50))
            if result.get("error"):
                return _rpc_error(msg_id, -32603, result["error"])
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}

        if method == "session/send":
            session_id = params.get("session_id")
            if not session_id:
                return _rpc_error(msg_id, -32602, "Missing 'session_id' parameter")
            result = self.session_endpoints.send(
                session_id,
                params.get("text", ""),
                params.get("enter", False),
            )
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}

        return _rpc_error(msg_id, -32601, f"Method {method} not found")

    def build_starlette_app(self) -> Starlette:
        """Build the Starlette application for HTTP serving."""

        async def health(request):
            return PlainTextResponse("ok")

        async def rpc(request):
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)

            response = await self.handle_jsonrpc(body)

            # Return appropriate HTTP status based on JSON-RPC error
            if "error" in response:
                # Check if it's a method not found (-32601) or invalid params (-32602)
                error_code = response.get("error", {}).get("code", 0)
                if error_code in (-32601, -32602):
                    return JSONResponse(response, status_code=422)
                return JSONResponse(response, status_code=200)

            return JSONResponse(response)

        async def acp(request):
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)

            response = await self.handle_acp_message(body)

            # Return 422 for validation errors
            if response.get("type") == "error":
                error_code = response.get("error", {}).get("code", "")
                if error_code in ("MISSING_AGENT", "AGENT_NOT_FOUND", "UNSUPPORTED_TYPE"):
                    return JSONResponse(response, status_code=422)
                return JSONResponse(response, status_code=200)

            return JSONResponse(response)

        routes = [
            Route("/health", health),
            Route("/rpc", rpc, methods=["POST"]),
            Route("/acp", acp, methods=["POST"]),
        ]

        return Starlette(routes=routes)

    async def run_stdio(self) -> None:
        """Run the server in stdio mode."""
        import json
        import sys

        for line in sys.stdin:
            try:
                msg = json.loads(line)
                if msg.get("type") == "task":
                    await self.handle_acp_message(msg)
            except json.JSONDecodeError:
                pass
            except Exception:
                pass

    async def run_http(
        self,
        host: str = "0.0.0.0",  # noqa: S104 -- intentional all-interface bind for ACP reachability
        port: int = ACP_DEFAULT_PORT,
    ) -> None:
        """Run the server in HTTP mode."""
        import uvicorn

        config = uvicorn.Config(self.build_starlette_app(), host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


def get_runner(name: str) -> Any:
    """Get an agent runner by name from the registry."""
    from thegent.agents import registry

    return registry.get_runner(name)


# ---------------------------------------------------------------------------
# CLI App
# ---------------------------------------------------------------------------

app = typer.Typer(help="ACP Server CLI")


@app.command()
def serve(
    http: bool = typer.Option(False, "--http", help="Run HTTP server"),
    host: str = typer.Option(
        "0.0.0.0",  # noqa: S104 -- intentional all-interface bind for ACP reachability
        "--host",
        help="Host to bind",
    ),
    port: int = typer.Option(ACP_DEFAULT_PORT, "--port", help="Port to bind"),
) -> None:
    """Start the ACP server."""
    adapter = ACPServerAdapter()
    if http:
        # HTTP mode: call run_http synchronously
        # (run_http uses uvicorn which manages its own event loop)
        adapter.run_http(host=host, port=port)
    else:
        asyncio.run(adapter.run_stdio())


if __name__ == "__main__":
    app()
