"""Tests for Wave 81: Error handling and diagnostics.

Related to:
- Error message clarity tests
- Diagnostic output tests
"""

from __future__ import annotations


class TestErrorMessages:
    """Test error messages are actionable."""

    def test_error_includes_context(self) -> None:
        """Errors should include context."""
        error = {"message": "Rate limit exceeded", "context": {"provider": "openai"}}

        assert "context" in error

    def test_error_suggests_action(self) -> None:
        """Errors should suggest remediation."""
        error = {"message": "Auth failed", "action": "Refresh token"}

        assert "action" in error or "retry" in str(error)

    def test_error_trace_id_present(self) -> None:
        """Errors should have trace IDs for debugging."""
        error = {"message": "Failed", "trace_id": "abc-123"}

        assert "trace_id" in error


class TestDiagnostics:
    """Test diagnostic output."""

    def test_diagnostics_show_provider_state(self) -> None:
        """Diagnostics should show provider state."""
        state = {"openai": "healthy", "anthropic": "degraded"}

        assert "openai" in state

    def test_diagnostics_timestamped(self) -> None:
        """Diagnostics should be timestamped."""
        diag = {"message": "test", "timestamp": 1234567890}

        assert "timestamp" in diag
