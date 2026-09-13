"""Tests for GW-64: MCP Gateway.

# @trace FR-MCP-064
"""

from __future__ import annotations

import threading
from unittest.mock import patch

import pytest

from thegent.mcp.gateway import (
    McpGateway,
    McpServerConfig,
    McpToolCall,
    McpToolResult,
    get_mcp_gateway,
    reset_mcp_gateway,
)


def _make_config(server_id: str = "fs") -> McpServerConfig:
    return McpServerConfig(
        server_id=server_id,
        command="npx -y @modelcontextprotocol/server-filesystem /tmp",
        env={},
        timeout_sec=30.0,
        description="Filesystem MCP server",
    )


@pytest.mark.requirement("FR-MCP-064")
def test_register_server() -> None:
    gw = McpGateway()
    cfg = _make_config("fs")
    gw.register_server(cfg)
    assert gw.get_server("fs") is cfg


@pytest.mark.requirement("FR-MCP-064")
def test_unregister_server() -> None:
    gw = McpGateway()
    cfg = _make_config("fs")
    gw.register_server(cfg)
    gw.unregister_server("fs")
    assert gw.get_server("fs") is None


@pytest.mark.requirement("FR-MCP-064")
def test_unregister_nonexistent_raises() -> None:
    gw = McpGateway()
    with pytest.raises(KeyError):
        gw.unregister_server("does_not_exist")


@pytest.mark.requirement("FR-MCP-064")
def test_list_servers_empty() -> None:
    gw = McpGateway()
    assert gw.list_servers() == []


@pytest.mark.requirement("FR-MCP-064")
def test_list_servers_multiple() -> None:
    gw = McpGateway()
    gw.register_server(_make_config("a"))
    gw.register_server(_make_config("b"))
    gw.register_server(_make_config("c"))
    ids = {cfg.server_id for cfg in gw.list_servers()}
    assert ids == {"a", "b", "c"}


@pytest.mark.requirement("FR-MCP-064")
def test_get_server_exists() -> None:
    gw = McpGateway()
    cfg = _make_config("myserver")
    gw.register_server(cfg)
    result = gw.get_server("myserver")
    assert result is cfg


@pytest.mark.requirement("FR-MCP-064")
def test_get_server_missing() -> None:
    gw = McpGateway()
    assert gw.get_server("nonexistent") is None


@pytest.mark.requirement("FR-MCP-064")
def test_execute_returns_result() -> None:
    gw = McpGateway()
    gw.register_server(_make_config("fs"))
    call = McpToolCall(
        server_id="fs",
        tool="read_file",
        arguments={"path": "/tmp/foo.txt"},
    )
    proc = type(
        "Proc",
        (),
        {
            "stdout": '{"jsonrpc":"2.0","result":{"ok":true}}\n',
            "returncode": 0,
            "stderr": "",
        },
    )()
    with patch("thegent.mcp.gateway.subprocess.run", return_value=proc):
        result = gw.execute(call)
    assert isinstance(result, McpToolResult)
    assert result.error == ""
    assert result.server_id == "fs"
    assert result.tool == "read_file"
    assert result.duration_ms >= 0.0
    assert result.result is not None


@pytest.mark.requirement("FR-MCP-064")
def test_execute_unknown_server_returns_error() -> None:
    gw = McpGateway()
    call = McpToolCall(
        server_id="no_such_server",
        tool="do_thing",
        arguments={},
    )
    result = gw.execute(call)
    assert isinstance(result, McpToolResult)
    assert result.error != ""
    assert "no_such_server" in result.error


@pytest.mark.requirement("FR-MCP-064")
def test_singleton_same_instance() -> None:
    reset_mcp_gateway()
    gw1 = get_mcp_gateway()
    gw2 = get_mcp_gateway()
    assert gw1 is gw2


@pytest.mark.requirement("FR-MCP-064")
def test_reset_gateway_new_instance() -> None:
    gw1 = get_mcp_gateway()
    reset_mcp_gateway()
    gw2 = get_mcp_gateway()
    assert gw1 is not gw2


@pytest.mark.requirement("FR-MCP-064")
def test_gateway_thread_safe_register() -> None:
    gw = McpGateway()
    errors: list[Exception] = []

    def register_many(prefix: str) -> None:
        try:
            for i in range(50):
                gw.register_server(_make_config(f"{prefix}-{i}"))
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=register_many, args=(f"t{j}",)) for j in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Thread errors: {errors}"
    # 4 threads × 50 = 200 servers
    assert len(gw.list_servers()) == 200
