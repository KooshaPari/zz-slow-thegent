"""Tests for AcpMcpBridge.

# @trace FR-ACP-002

Unit tests for the MCP <-> ACP bridge adapter covering:
- mcp_tool_to_acp_task round-trips
- acp_agent_to_mcp_tool round-trips
- get_mcp_tool_manifest returns correct format
- Error handling when ACP agent is unreachable
- ACPToolDescriptor serialisation
- Edge cases (empty args, bad URLs, empty manifests)
"""

from __future__ import annotations

from typing import Any, ClassVar
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.adapters.acp_client import (
    ACPClientError,
    ACPResult,
    ACPServerUnreachableError,
)
from thegent.adapters.acp_mcp_bridge import (
    ACPAgentCallError,
    AcpMcpBridge,
    ACPToolDescriptor,
    BridgeError,
    MCPToolNotFoundError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_acp_result(
    success: bool = True,
    result: str = "ok",
    agent_id: str = "remote-agent-1",
    elapsed_ms: float = 42.0,
) -> ACPResult:
    """Build a fake ACPResult.

    Args:
        success:    Whether the call succeeded.
        result:     Result text from the remote agent.
        agent_id:   Remote agent identifier.
        elapsed_ms: Simulated elapsed time.

    Returns:
        Populated :class:`ACPResult`.
    """
    return ACPResult(
        success=success, result=result, agent_id=agent_id, elapsed_ms=elapsed_ms
    )


def _make_mock_acp_client(
    result: ACPResult | None = None, side_effect: Exception | None = None
) -> AsyncMock:
    """Create an AsyncMock ACPClient.

    Args:
        result:      ACPResult to return from send_task.
        side_effect: If given, send_task raises this exception.

    Returns:
        Mock ACPClient with send_task and health_check configured.
    """
    mock = AsyncMock()
    mock._base_url = "http://mock-agent:8080"
    if side_effect is not None:
        mock.send_task = AsyncMock(side_effect=side_effect)
    else:
        mock.send_task = AsyncMock(return_value=result or _make_acp_result())
    mock.health_check = AsyncMock(return_value=True)
    return mock


def _make_mock_mcp_app(tools: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock FastMCP app with list_tools().

    Args:
        tools: Dict of tool_name -> tool_obj to return from list_tools() as
               a list of objects with .name set to the key.

    Returns:
        Mock FastMCP application.
    """
    app = MagicMock()
    tool_list = []
    for name, tool_obj in (tools or {}).items():
        tool_obj.name = name
        tool_list.append(tool_obj)
    app.get_tools.return_value = tools or {}
    app.list_tools.return_value = tool_list
    return app


def _make_tool_obj(
    description: str = "A tool description",
    parameters: dict[str, Any] | None = None,
) -> MagicMock:
    """Create a mock FastMCP tool object.

    Args:
        description: Description attribute value.
        parameters:  Parameters dict (schema).

    Returns:
        Mock tool object.
    """
    tool = MagicMock()
    tool.description = description
    tool.parameters = parameters or {"arg1": {"type": "string"}}
    tool.fn = None
    return tool


# ---------------------------------------------------------------------------
# ACPToolDescriptor
# ---------------------------------------------------------------------------


class TestACPToolDescriptor:
    """Tests for ACPToolDescriptor dataclass."""

    def test_to_dict_contains_required_keys(self) -> None:
        """to_dict includes name, description, parameters, version."""
        desc = ACPToolDescriptor(
            name="my_tool",
            description="does stuff",
            parameters={"x": {"type": "int"}},
        )
        d = desc.to_dict()
        assert d["name"] == "my_tool"
        assert d["description"] == "does stuff"
        assert d["parameters"] == {"x": {"type": "int"}}
        assert "version" in d

    def test_to_dict_default_version(self) -> None:
        """Default version is non-empty string."""
        desc = ACPToolDescriptor(name="t", description="d")
        assert isinstance(desc.to_dict()["version"], str)
        assert desc.to_dict()["version"]

    def test_to_dict_empty_parameters(self) -> None:
        """Empty parameters dict is preserved."""
        desc = ACPToolDescriptor(name="t", description="d", parameters={})
        assert desc.to_dict()["parameters"] == {}

    def test_to_dict_is_json_serialisable(self) -> None:
        """to_dict result can be JSON-serialised without error."""
        import json

        desc = ACPToolDescriptor(
            name="tool", description="desc", parameters={"p": {"type": "str"}}
        )
        json.dumps(desc.to_dict())  # must not raise


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    """Tests for bridge exception classes."""

    def test_bridge_error_is_exception(self) -> None:
        """BridgeError is an Exception subclass."""
        assert issubclass(BridgeError, Exception)

    def test_mcp_tool_not_found_is_bridge_error(self) -> None:
        """MCPToolNotFoundError is a BridgeError."""
        assert issubclass(MCPToolNotFoundError, BridgeError)

    def test_acp_agent_call_error_is_bridge_error(self) -> None:
        """ACPAgentCallError is a BridgeError."""
        assert issubclass(ACPAgentCallError, BridgeError)

    def test_mcp_tool_not_found_message(self) -> None:
        """MCPToolNotFoundError includes the tool name in message."""
        exc = MCPToolNotFoundError("my_tool")
        assert "my_tool" in str(exc)
        assert exc.tool_name == "my_tool"

    def test_acp_agent_call_error_message(self) -> None:
        """ACPAgentCallError includes agent_url and detail."""
        exc = ACPAgentCallError("http://agent:8080", "timeout")
        assert "http://agent:8080" in str(exc)
        assert "timeout" in str(exc)
        assert exc.agent_url == "http://agent:8080"


# ---------------------------------------------------------------------------
# AcpMcpBridge construction
# ---------------------------------------------------------------------------


class TestAcpMcpBridgeConstruction:
    """Tests for AcpMcpBridge.__init__."""

    def test_basic_construction(self) -> None:
        """Bridge can be created with just an ACPClient."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)
        assert bridge is not None

    def test_construction_with_mcp_app(self) -> None:
        """Bridge stores mcp_app reference."""
        client = _make_mock_acp_client()
        app = _make_mock_mcp_app()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)
        assert bridge._mcp_app is app

    def test_construction_with_mcp_server_url(self) -> None:
        """Bridge stores mcp_server_url."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_server_url="http://mcp:3847")
        assert bridge._mcp_server_url == "http://mcp:3847"

    def test_no_mcp_app_by_default(self) -> None:
        """mcp_app defaults to None."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)
        assert bridge._mcp_app is None


# ---------------------------------------------------------------------------
# mcp_tool_to_acp_task
# ---------------------------------------------------------------------------


class TestMcpToolToAcpTask:
    """Tests for AcpMcpBridge.mcp_tool_to_acp_task."""

    @pytest.mark.asyncio
    async def test_successful_call_returns_acp_result(self) -> None:
        """A successful tool call returns an ACPResult with success=True."""
        expected = _make_acp_result(success=True, result="42 sessions found")
        client = _make_mock_acp_client(result=expected)
        bridge = AcpMcpBridge(acp_client=client)

        result = await bridge.mcp_tool_to_acp_task("thegent_ps", {"all": True})

        assert result.success is True
        assert result.result == "42 sessions found"

    @pytest.mark.asyncio
    async def test_send_task_called_with_correct_task_description(self) -> None:
        """send_task receives a task description mentioning the tool name."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        await bridge.mcp_tool_to_acp_task("thegent_ps", {})

        call_args = client.send_task.call_args
        task_text: str = call_args.kwargs.get("task") or call_args.args[0]
        assert "thegent_ps" in task_text

    @pytest.mark.asyncio
    async def test_send_task_called_with_context_containing_tool_name(self) -> None:
        """send_task context includes tool_name field."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        await bridge.mcp_tool_to_acp_task("thegent_run", {"prompt": "hello"})

        call_args = client.send_task.call_args
        context = call_args.kwargs.get("context") or call_args.args[1]
        assert context["tool_name"] == "thegent_run"

    @pytest.mark.asyncio
    async def test_send_task_context_includes_args(self) -> None:
        """send_task context includes the args dict."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)
        args = {"limit": 10, "all": False}

        await bridge.mcp_tool_to_acp_task("thegent_ps", args)

        call_args = client.send_task.call_args
        context = call_args.kwargs.get("context") or call_args.args[1]
        assert context["args"] == args

    @pytest.mark.asyncio
    async def test_empty_args_dict_allowed(self) -> None:
        """Empty args dict is passed through without error."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        result = await bridge.mcp_tool_to_acp_task("thegent_ps", {})

        assert isinstance(result, ACPResult)

    @pytest.mark.asyncio
    async def test_propagates_acp_server_unreachable(self) -> None:
        """ACPServerUnreachableError propagates from mcp_tool_to_acp_task."""
        client = _make_mock_acp_client(
            side_effect=ACPServerUnreachableError("no route")
        )
        bridge = AcpMcpBridge(acp_client=client)

        with pytest.raises(ACPServerUnreachableError):
            await bridge.mcp_tool_to_acp_task("thegent_ps", {})

    @pytest.mark.asyncio
    async def test_propagates_acp_client_error(self) -> None:
        """ACPClientError propagates from mcp_tool_to_acp_task."""
        client = _make_mock_acp_client(side_effect=ACPClientError(404, "not found"))
        bridge = AcpMcpBridge(acp_client=client)

        with pytest.raises(ACPClientError):
            await bridge.mcp_tool_to_acp_task("thegent_ps", {})

    @pytest.mark.asyncio
    async def test_empty_tool_name_raises_value_error(self) -> None:
        """Empty tool_name raises ValueError."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        with pytest.raises(ValueError, match="tool_name"):
            await bridge.mcp_tool_to_acp_task("", {})

    @pytest.mark.asyncio
    async def test_custom_timeout_forwarded(self) -> None:
        """Custom timeout is forwarded to send_task."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        await bridge.mcp_tool_to_acp_task("thegent_ps", {}, timeout=99.0)

        call_args = client.send_task.call_args
        timeout = call_args.kwargs.get("timeout") or call_args.args[2]
        assert timeout == 99.0


# ---------------------------------------------------------------------------
# acp_agent_to_mcp_tool
# ---------------------------------------------------------------------------


class TestAcpAgentToMcpTool:
    """Tests for AcpMcpBridge.acp_agent_to_mcp_tool."""

    @pytest.mark.asyncio
    async def test_successful_call_returns_result_text(self) -> None:
        """Successful call returns the agent's result text."""
        expected_result = "Agent processed the task successfully"

        with patch("thegent.adapters.acp_mcp_bridge.ACPClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.send_task = AsyncMock(
                return_value=_make_acp_result(result=expected_result)
            )
            mock_cls.return_value = mock_instance

            client = _make_mock_acp_client()
            bridge = AcpMcpBridge(acp_client=client)

            result = await bridge.acp_agent_to_mcp_tool(
                agent_url="http://remote-agent:8080",
                task="Summarise the logs",
                payload={"key": "value"},
            )

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_one_shot_client_uses_agent_url(self) -> None:
        """A one-shot ACPClient is created targeting the given agent_url."""
        with patch("thegent.adapters.acp_mcp_bridge.ACPClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.send_task = AsyncMock(return_value=_make_acp_result())
            mock_cls.return_value = mock_instance

            client = _make_mock_acp_client()
            bridge = AcpMcpBridge(acp_client=client)

            await bridge.acp_agent_to_mcp_tool(
                agent_url="http://special-agent:9000",
                task="do work",
                payload={},
            )

            mock_cls.assert_called_once_with(base_url="http://special-agent:9000")

    @pytest.mark.asyncio
    async def test_unreachable_agent_raises_acp_server_unreachable(self) -> None:
        """ACPServerUnreachableError propagates unchanged."""
        with patch("thegent.adapters.acp_mcp_bridge.ACPClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.send_task = AsyncMock(
                side_effect=ACPServerUnreachableError("no route to host")
            )
            mock_cls.return_value = mock_instance

            client = _make_mock_acp_client()
            bridge = AcpMcpBridge(acp_client=client)

            with pytest.raises(ACPServerUnreachableError):
                await bridge.acp_agent_to_mcp_tool(
                    agent_url="http://dead-agent:9999",
                    task="any task",
                    payload={},
                )

    @pytest.mark.asyncio
    async def test_client_error_wrapped_as_acp_agent_call_error(self) -> None:
        """ACPClientError is re-raised as ACPAgentCallError."""
        with patch("thegent.adapters.acp_mcp_bridge.ACPClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.send_task = AsyncMock(
                side_effect=ACPClientError(500, "internal server error")
            )
            mock_cls.return_value = mock_instance

            client = _make_mock_acp_client()
            bridge = AcpMcpBridge(acp_client=client)

            with pytest.raises(ACPAgentCallError) as exc_info:
                await bridge.acp_agent_to_mcp_tool(
                    agent_url="http://error-agent:8080",
                    task="any task",
                    payload={},
                )

            assert "http://error-agent:8080" in exc_info.value.agent_url

    @pytest.mark.asyncio
    async def test_empty_agent_url_raises_value_error(self) -> None:
        """Empty agent_url raises ValueError."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        with pytest.raises(ValueError, match="agent_url"):
            await bridge.acp_agent_to_mcp_tool(
                agent_url="", task="any task", payload={}
            )

    @pytest.mark.asyncio
    async def test_empty_task_raises_value_error(self) -> None:
        """Empty task raises ValueError."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        with pytest.raises(ValueError, match="task"):
            await bridge.acp_agent_to_mcp_tool(
                agent_url="http://agent:8080", task="", payload={}
            )

    @pytest.mark.asyncio
    async def test_payload_forwarded_as_context(self) -> None:
        """The payload dict is forwarded to send_task as context."""
        with patch("thegent.adapters.acp_mcp_bridge.ACPClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.send_task = AsyncMock(return_value=_make_acp_result())
            mock_cls.return_value = mock_instance

            client = _make_mock_acp_client()
            bridge = AcpMcpBridge(acp_client=client)
            payload = {"project": "thegent", "tag": "v1"}

            await bridge.acp_agent_to_mcp_tool(
                agent_url="http://agent:8080",
                task="do something",
                payload=payload,
            )

            call_args = mock_instance.send_task.call_args
            context_arg = call_args.kwargs.get("context") or call_args.args[1]
            assert context_arg == payload


# ---------------------------------------------------------------------------
# get_mcp_tool_manifest
# ---------------------------------------------------------------------------


class TestGetMcpToolManifest:
    """Tests for AcpMcpBridge.get_mcp_tool_manifest."""

    def test_no_mcp_app_returns_empty_list(self) -> None:
        """Without mcp_app, manifest is empty."""
        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client)

        manifest = bridge.get_mcp_tool_manifest()

        assert manifest == []

    def test_manifest_has_correct_keys(self) -> None:
        """Each descriptor in the manifest has name, description, parameters, version."""
        tool_obj = _make_tool_obj(description="Does useful things")
        app = _make_mock_mcp_app(tools={"my_tool": tool_obj})

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert len(manifest) == 1
        d = manifest[0]
        assert d["name"] == "my_tool"
        assert "description" in d
        assert "parameters" in d
        assert "version" in d

    def test_manifest_description_from_tool_attribute(self) -> None:
        """Description is taken from the tool's description attribute."""
        tool_obj = _make_tool_obj(description="My great description")
        app = _make_mock_mcp_app(tools={"my_tool": tool_obj})

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert manifest[0]["description"] == "My great description"

    def test_manifest_parameters_from_tool_attribute(self) -> None:
        """Parameters are taken from the tool's parameters attribute."""
        params = {"limit": {"type": "integer"}, "all": {"type": "boolean"}}
        tool_obj = _make_tool_obj(parameters=params)
        app = _make_mock_mcp_app(tools={"my_tool": tool_obj})

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert manifest[0]["parameters"] == params

    def test_manifest_multiple_tools(self) -> None:
        """Manifest contains one entry per registered tool."""
        tools = {
            "tool_a": _make_tool_obj(description="Tool A"),
            "tool_b": _make_tool_obj(description="Tool B"),
            "tool_c": _make_tool_obj(description="Tool C"),
        }
        app = _make_mock_mcp_app(tools=tools)

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert len(manifest) == 3
        names = {d["name"] for d in manifest}
        assert names == {"tool_a", "tool_b", "tool_c"}

    def test_manifest_returns_empty_list_on_get_tools_failure(self) -> None:
        """If get_tools() raises, manifest is empty list (no crash)."""
        app = MagicMock()
        app.get_tools.side_effect = RuntimeError("introspection failed")

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert manifest == []

    def test_manifest_tool_with_no_description_attribute(self) -> None:
        """Tool with no description/doc attributes gets empty description."""

        class _NoDocTool:
            """Suppress any accidental __doc__ from MagicMock."""

            parameters: ClassVar[dict] = {}
            fn = None
            # No description, __doc__ deliberately set to None
            __doc__ = None

        tool_obj = _NoDocTool()
        app = _make_mock_mcp_app(tools={"bare_tool": tool_obj})

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert manifest[0]["description"] == ""

    def test_manifest_tool_falls_back_to_docstring(self) -> None:
        """Tool without description attribute but with __doc__ uses docstring."""
        tool_obj = MagicMock()
        del tool_obj.description  # force AttributeError path
        tool_obj.__doc__ = "Docstring description"
        tool_obj.parameters = {}
        tool_obj.fn = None
        app = _make_mock_mcp_app(tools={"doc_tool": tool_obj})

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert "Docstring" in manifest[0]["description"]

    def test_manifest_version_is_string(self) -> None:
        """version field in each descriptor is a non-empty string."""
        tool_obj = _make_tool_obj()
        app = _make_mock_mcp_app(tools={"t": tool_obj})

        client = _make_mock_acp_client()
        bridge = AcpMcpBridge(acp_client=client, mcp_app=app)

        manifest = bridge.get_mcp_tool_manifest()

        assert isinstance(manifest[0]["version"], str)
        assert manifest[0]["version"]
