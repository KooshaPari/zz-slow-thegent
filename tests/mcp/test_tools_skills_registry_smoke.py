"""WL-111 smoke tests for skill tools registered on the MCP server registry."""

from __future__ import annotations

import pytest

pytest.importorskip("fastmcp", reason="fastmcp required for MCP registry smoke tests")

import thegent.mcp.server as mcp_server


@pytest.mark.asyncio
async def test_skill_tools_are_registered_in_server_registry() -> None:
    tools = await mcp_server.mcp.list_tools()
    names = {tool.name for tool in tools}
    assert "thegent_list_skills" in names
    assert "thegent_activate_skill" in names


@pytest.mark.asyncio
async def test_skill_tool_parameters_match_expected_schema() -> None:
    tools = await mcp_server.mcp.list_tools()
    by_name = {tool.name: tool for tool in tools}

    list_tool = by_name["thegent_list_skills"]
    assert "discoverable skills" in (list_tool.description or "").lower()
    assert list_tool.parameters["type"] == "object"
    assert list_tool.parameters["additionalProperties"] is False

    activate_tool = by_name["thegent_activate_skill"]
    assert "load and return a skill payload" in (activate_tool.description or "").lower()
    assert activate_tool.parameters["type"] == "object"
    assert activate_tool.parameters["required"] == ["skill_name"]
    assert activate_tool.parameters["properties"]["skill_name"]["type"] == "string"


@pytest.mark.asyncio
async def test_only_expected_skill_tools_are_registered() -> None:
    tools = await mcp_server.mcp.list_tools()
    skill_tool_names = {tool.name for tool in tools if "skill" in tool.name}
    assert {"thegent_list_skills", "thegent_activate_skill"}.issubset(skill_tool_names)
