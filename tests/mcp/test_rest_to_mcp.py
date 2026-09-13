"""Tests for GW-66: REST-to-MCP adapter.

# @trace FR-MCP-066
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from thegent.mcp.rest_to_mcp import (
    RestToMcpAdapter,
    RestToolDef,
    RestToolResult,
    build_openai_tool_def,
)


def _make_tool(
    name: str = "search_products",
    url: str = "https://api.example.com/search?q={query}",
    method: str = "GET",
) -> RestToolDef:
    return RestToolDef(
        name=name,
        description="Search products by query",
        url=url,
        method=method,
        headers={"Accept": "application/json"},
        param_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "search term"},
            },
            "required": ["query"],
        },
        timeout_sec=5.0,
    )


@pytest.mark.requirement("FR-MCP-066")
def test_register_tool() -> None:
    adapter = RestToMcpAdapter()
    tool = _make_tool()
    adapter.register(tool)
    assert adapter.get_tool("search_products") is tool


@pytest.mark.requirement("FR-MCP-066")
def test_unregister_tool() -> None:
    adapter = RestToMcpAdapter()
    adapter.register(_make_tool())
    adapter.unregister("search_products")
    assert adapter.get_tool("search_products") is None
    with pytest.raises(KeyError):
        adapter.unregister("search_products")


@pytest.mark.requirement("FR-MCP-066")
def test_list_tools_empty() -> None:
    adapter = RestToMcpAdapter()
    assert adapter.list_tools() == []


@pytest.mark.requirement("FR-MCP-066")
def test_list_tools_multiple() -> None:
    adapter = RestToMcpAdapter()
    adapter.register(_make_tool("tool_a"))
    adapter.register(_make_tool("tool_b"))
    adapter.register(_make_tool("tool_c"))
    names = {t.name for t in adapter.list_tools()}
    assert names == {"tool_a", "tool_b", "tool_c"}


@pytest.mark.requirement("FR-MCP-066")
def test_get_tool_exists() -> None:
    adapter = RestToMcpAdapter()
    tool = _make_tool("my_tool")
    adapter.register(tool)
    assert adapter.get_tool("my_tool") is tool


@pytest.mark.requirement("FR-MCP-066")
def test_get_tool_missing() -> None:
    adapter = RestToMcpAdapter()
    assert adapter.get_tool("nonexistent") is None


@pytest.mark.requirement("FR-MCP-066")
def test_to_openai_tools_format() -> None:
    adapter = RestToMcpAdapter()
    adapter.register(_make_tool("search_products"))
    openai_tools = adapter.to_openai_tools()
    assert len(openai_tools) == 1
    item = openai_tools[0]
    assert item["type"] == "function"
    assert "function" in item
    fn = item["function"]
    assert fn["name"] == "search_products"
    assert "description" in fn
    assert "parameters" in fn


@pytest.mark.requirement("FR-MCP-066")
def test_build_openai_tool_def() -> None:
    tool = _make_tool("my_api")
    result = build_openai_tool_def(tool)
    assert result == {
        "type": "function",
        "function": {
            "name": "my_api",
            "description": tool.description,
            "parameters": tool.param_schema,
        },
    }


@pytest.mark.requirement("FR-MCP-066")
def test_call_url_substitution() -> None:
    adapter = RestToMcpAdapter()
    tool = _make_tool(
        name="search_products",
        url="https://api.example.com/search?q={query}",
        method="GET",
    )
    adapter.register(tool)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.request.return_value = mock_response

        result = adapter.call("search_products", {"query": "shoes"})

    assert isinstance(result, RestToolResult)
    assert result.error == ""
    assert result.status_code == 200
    # Verify the URL substitution was applied in the call.
    call_args = mock_client.request.call_args
    called_url = call_args[0][1] if call_args[0] else call_args[1].get("url", call_args[0][1])
    # The URL passed to client.request should have the query substituted.
    assert "shoes" in called_url


@pytest.mark.requirement("FR-MCP-066")
def test_call_http_error_returns_error_not_raise() -> None:
    adapter = RestToMcpAdapter()
    adapter.register(_make_tool())

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.request.side_effect = Exception("connection refused")

        result = adapter.call("search_products", {"query": "shoes"})

    assert isinstance(result, RestToolResult)
    assert result.error != ""
    assert "connection refused" in result.error
    assert result.status_code == 0


@pytest.mark.requirement("FR-MCP-066")
def test_call_unknown_tool_returns_error() -> None:
    adapter = RestToMcpAdapter()
    result = adapter.call("no_such_tool", {"arg": "val"})
    assert isinstance(result, RestToolResult)
    assert result.error != ""
    assert "no_such_tool" in result.error
    assert result.status_code == 0


@pytest.mark.requirement("FR-MCP-066")
def test_call_post_sends_json_body() -> None:
    adapter = RestToMcpAdapter()
    tool = RestToolDef(
        name="create_item",
        description="Create an item",
        url="https://api.example.com/items/{item_id}",
        method="POST",
        headers={},
        param_schema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "name": {"type": "string"},
                "price": {"type": "number"},
            },
        },
        timeout_sec=5.0,
    )
    adapter.register(tool)

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "42", "created": True}

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.request.return_value = mock_response

        result = adapter.call(
            "create_item",
            {"item_id": "42", "name": "Widget", "price": 9.99},
        )

    assert result.error == ""
    assert result.status_code == 201

    call_kwargs = mock_client.request.call_args[1]
    # The URL placeholder {item_id} should be substituted.
    called_url = mock_client.request.call_args[0][1]
    assert "42" in called_url
    # Remaining args (name, price) should be sent as JSON body.
    assert call_kwargs.get("json") == {"name": "Widget", "price": 9.99}
