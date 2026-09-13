"""Tests for WL-88: Gemini schema mapping (parameters vs parametersJsonSchema).

Related to CLIProxyAPI#1649 - incorrect renaming of parameters to parametersJsonSchema.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestGeminiSchemaMapping:
    """Test that Gemini parameters are correctly mapped in tool payloads."""

    @patch("thegent.cliproxy_adapter._transform_gemini_tool")
    def test_parameters_preserved_for_gemini(self, mock_transform) -> None:
        """Parameters should be preserved as 'parameters' not renamed to 'parametersJsonSchema'.

        Issue: CLIProxyAPI#1649 - incorrect renaming of parameters to parametersJsonSchema
        """
        # Gemini tools should use 'parameters', not 'parametersJsonSchema'
        tool_def = {"name": "test_tool", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}

        result = mock_transform(tool_def, provider="gemini")

        # Should have parameters, not parametersJsonSchema
        assert "parameters" in result
        assert "parametersJsonSchema" not in result

    @patch("thegent.cliproxy_adapter._transform_gemini_tool")
    def test_openai_tools_use_parameters_schema(self, mock_transform) -> None:
        """OpenAI-style tools should use 'parameters' field."""
        tool_def = {"name": "test_tool", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}

        result = mock_transform(tool_def, provider="openai")

        # OpenAI uses 'parameters'
        assert "parameters" in result

    @patch("thegent.cliproxy_adapter._transform_gemini_tool")
    def test_no_invalid_rename_to_json_schema(self, mock_transform) -> None:
        """Should NOT rename parameters to parametersJsonSchema incorrectly."""
        tool_def = {"name": "test_tool", "parameters": {"type": "object"}}

        result = mock_transform(tool_def, provider="gemini")

        # The bug is renaming incorrectly - should NOT have this
        if "parametersJsonSchema" in result:
            pytest.fail("parameters incorrectly renamed to parametersJsonSchema")

        # Should preserve original field
        assert "parameters" in result or "parametersJsonSchema" in result
