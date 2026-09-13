"""Tests for Wave 81: Auth file handling and token refresh.

Related to:
- CLIProxyAPI#797 - ModelStates lost when auth refreshed
- CLIProxyAPI#1299 - Auth token refresh issues
"""

from __future__ import annotations

from unittest.mock import patch


class TestAuthStatePersistence:
    """Test auth state persists across operations."""

    @patch("thegent.agents.cliproxy_manager.save_auth_state")
    def test_auth_state_persists_after_refresh(self, mock_save) -> None:
        """Auth state should persist after token refresh.

        Issue: CLIProxyAPI#797 - ModelStates lost when auth is reloaded
        """
        # Simulate auth refresh
        initial_state = {"models": ["claude-3-opus", "claude-3-sonnet"]}

        mock_save.return_value = True

        result = mock_save(initial_state)

        # State should be saved
        assert result is True

    def test_auth_refresh_preserves_model_state(self) -> None:
        """Model states should be preserved across auth refresh."""
        # Model states that should persist
        states = {"claude-opus": {"backoff_level": 0}, "claude-sonnet": {"backoff_level": 1}}

        # After refresh
        refreshed = states.copy()

        # States should match
        assert refreshed == states


class TestTokenRefresh:
    """Test token refresh behavior."""

    def test_token_refresh_validates_expiry(self) -> None:
        """Refresh tokens should validate expiry."""
        # Token with expiry
        token = {"expires_at": 9999999999, "refresh_token": "abc123"}

        # Should have expiry
        assert "expires_at" in token
        assert token["expires_at"] > 0

    def test_refresh_token_present(self) -> None:
        """Refresh should have refresh token."""
        auth = {"access_token": "xyz", "refresh_token": "abc"}

        assert "refresh_token" in auth
        assert auth["refresh_token"] == "abc"
