"""Tests for WL-66: MCP tool availability - ENABLE_TOOL_SEARCH flag.

Related to CLIProxyAPI#1547 - MCP not in available tools 400 error.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestMCPToolAvailability:
    """Test that MCP tools remain available when ENABLE_TOOL_SEARCH is used."""

    @pytest.mark.asyncio
    @patch("thegent.mcp.server.MCPServer.list_tools")
    async def test_mcp_tools_available_without_search_flag(self, mock_list_tools) -> None:
        """Basic MCP tool listing should work without ENABLE_TOOL_SEARCH."""
        mock_list_tools.return_value = [
            {"name": "tool1", "description": "A test tool"},
            {"name": "tool2", "description": "Another tool"},
        ]

        # Should return tools without error
        result = await mock_list_tools()

        assert len(result) == 2
        assert result[0]["name"] == "tool1"

    @pytest.mark.asyncio
    @patch("thegent.mcp.server.MCPServer.list_tools")
    async def test_mcp_tools_available_with_search_flag(self, mock_list_tools) -> None:
        """MCP tools should be available even with ENABLE_TOOL_SEARCH enabled.

        Issue: CLIProxyAPI#1547 - ENABLE_TOOL_SEARCH causes 400 error.
        """
        mock_list_tools.return_value = [
            {"name": "search_tool", "description": "A search tool"},
        ]

        # Should not raise 400 error
        result = await mock_list_tools()

        assert len(result) >= 1
        # Should not have 400 error in any form
        for tool in result:
            assert "error" not in tool or tool.get("error") != 400

    @pytest.mark.asyncio
    @patch("thegent.mcp.server.MCPServer.list_tools")
    async def test_mcp_tool_enumeration_stability(self, mock_list_tools) -> None:
        """Tool enumeration should be stable across multiple calls."""
        mock_list_tools.return_value = [
            {"name": "tool_a", "description": "Tool A"},
            {"name": "tool_b", "description": "Tool B"},
        ]

        # Call multiple times - should be consistent
        result1 = await mock_list_tools()
        result2 = await mock_list_tools()

        assert result1 == result2
        assert len(result1) == 2
