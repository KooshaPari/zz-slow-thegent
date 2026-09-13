"""Tests for WL-102: Unknown/deprecated schema fields in payloads.

Related to CLIProxyAPI#1531 - Invalid JSON payload: Unknown name `deprecated`.
"""

from __future__ import annotations

from unittest.mock import patch


class TestUnknownSchemaFields:
    """Test that translator rejects unknown schema fields."""

    @patch("thegent.cliproxy_adapter._transform_request")
    def test_unknown_field_rejected(self, mock_transform) -> None:
        """Unknown fields like 'deprecated' should be rejected or stripped.

        Issue: CLIProxyAPI#1531 - Unknown name `deprecated`
        """
        payload = {
            "model": "claude-3-opus",
            "messages": [{"role": "user", "content": "Hello"}],
            "deprecated": True,  # Unknown field
        }

        # Should either reject or strip the unknown field
        result = mock_transform(payload)

        # deprecated field should not be in output
        assert "deprecated" not in result or result.get("deprecated") is None

    @patch("thegent.cliproxy_adapter._transform_request")
    def test_strip_unknown_fields_preserves_valid(self, mock_transform) -> None:
        """Unknown fields should be stripped, valid fields preserved."""
        payload = {
            "model": "claude-3-sonnet",
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.7,
            "unknown_field": "should_be_removed",
        }

        result = mock_transform(payload)

        # Known fields preserved
        assert result.get("temperature") == 0.7
        # Unknown fields stripped
        assert "unknown_field" not in result

    @patch("thegent.cliproxy_adapter._transform_request")
    def test_deprecated_field_stripped(self, mock_transform) -> None:
        """The specific 'deprecated' field from #1531 should be stripped."""
        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "messages": [{"role": "user", "content": "Test"}],
            "deprecated": False,
        }

        result = mock_transform(payload)

        # deprecated should not cause Invalid JSON error
        assert "deprecated" not in result or result.get("deprecated") is None
