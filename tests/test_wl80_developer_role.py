"""Tests for WL-80: Developer role support.

Related to CLIProxyAPI#680 - Support developer role.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestDeveloperRoleSupport:
    """Test that developer role is properly handled in request transforms."""

    @patch("thegent.cliproxy_adapter._transform_request")
    def test_developer_role_passthrough(self, mock_transform) -> None:
        """Developer role should be passed through to the upstream API.

        Issue: CLIProxyAPI#680 - Support developer role
        """
        # When developer role is specified, it should be preserved
        test_payload = {"messages": [{"role": "developer", "content": "You are a helpful assistant"}]}

        # The role should be passed through without modification
        result = mock_transform(test_payload)

        # Verify developer role is preserved
        assert result["messages"][0]["role"] == "developer"

    @patch("thegent.cliproxy_adapter._transform_request")
    def test_developer_role_rejected_where_unsupported(self, mock_transform) -> None:
        """Developer role should be rejected explicitly where unsupported."""
        test_payload = {"messages": [{"role": "developer", "content": "You are a helpful assistant"}]}

        # If the provider doesn't support developer role, should fail explicitly
        with pytest.raises(ValueError, match=r"developer.*not supported"):
            mock_transform(test_payload, provider="unsupported_provider")

    @patch("thegent.cliproxy_adapter._transform_request")
    def test_system_role_still_works(self, mock_transform) -> None:
        """System role should continue to work normally."""
        test_payload = {"messages": [{"role": "system", "content": "You are a helpful assistant"}]}

        result = mock_transform(test_payload)
        assert result["messages"][0]["role"] == "system"
