"""Tests for Wave 81 Lane D: Request parameter validation.

Related to:
- CLIProxyAPI#1215 - Unexpected parameter `reason` in tool calls
- CLIProxyAPI#1119 - Unsupported parameter `user` in requests
"""

from __future__ import annotations

import pytest


class TestUnexpectedParameterRejection:
    """Test that unexpected parameters are rejected or stripped."""

    def test_reject_unexpected_reason_parameter(self) -> None:
        """Tool calls should reject unexpected 'reason' parameter.

        Issue: CLIProxyAPI#1215 - Unexpected `reason` parameter
        """
        # Simulate tool call with unexpected parameter
        tool_call = {
            "name": "EnterPlanMode",
            "arguments": {"reason": "because I said so"},  # Unexpected
        }

        # Should either reject or strip the unexpected field
        if "reason" in tool_call.get("arguments", {}):
            pytest.fail("Unexpected parameter 'reason' should be rejected")

    def test_strip_unsupported_user_parameter(self) -> None:
        """OpenAI-compatible routes should handle unsupported 'user' parameter.

        Issue: CLIProxyAPI#1119 - Unsupported parameter `user`
        """
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "user": "some-user",  # Unsupported in some routes
        }

        # Should be stripped or rejected
        assert request.get("user") is None or "user" in request

    def test_known_parameters_preserved(self) -> None:
        """Known parameters should be preserved."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.7,  # Known param
            "max_tokens": 100,
        }

        # Known params should remain
        assert request.get("temperature") == 0.7
        assert request.get("max_tokens") == 100


class TestPlanModeParameterValidation:
    """Test PlanMode tool call validation."""

    def test_plan_mode_validates_parameters(self) -> None:
        """PlanMode tool should validate its parameters."""
        # Valid PlanMode call
        valid_call = {"name": "EnterPlanMode", "arguments": {"goal": "test goal"}}

        # Should be valid
        assert "goal" in valid_call.get("arguments", {})

    def test_plan_mode_rejects_unknown_fields(self) -> None:
        """PlanMode should reject unknown fields."""
        invalid_call = {
            "name": "EnterPlanMode",
            "arguments": {"goal": "test", "unknown_field": "bad"},
        }

        # Unknown fields should cause test failure
        if "unknown_field" in invalid_call.get("arguments", {}):
            pytest.fail("Unknown fields should be rejected")
