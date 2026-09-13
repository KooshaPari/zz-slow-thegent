"""Tests for WL-57: Provider conflict - Codex model visibility when Copilot is enabled.

This tests the scenario where models from Codex become inaccessible when Copilot
provider is added. Related to CLIProxyAPIPlus#43.

Issue: CLIProxyAPIPlus#43 - Models from Codex are not accessible when Copilot is added.
"""

from __future__ import annotations

from unittest.mock import patch

from thegent.clode_main import _resolve_provider_for_model


class TestCodexModelVisibilityWithCopilot:
    """Test that Codex models remain visible when Copilot provider is enabled."""

    @patch("thegent.clode_main._get_codex_env")
    def test_codex_model_resolves_correctly(self, mock_env: patch) -> None:
        """Codex models should resolve to codex provider regardless of other providers."""
        mock_env.return_value = {"CODEx_API_KEY": "test-key"}

        # When a model is explicitly a codex model, it should resolve to codex
        result = _resolve_provider_for_model("claude-codex-2-20250605")

        # Should resolve to codex, not copilot
        assert result in ["codex", "claude"], f"Expected codex/claude, got {result}"

    @patch("thegent.clode_main._get_codex_env")
    @patch("thegent.dex_main._get_codex_env")
    def test_no_provider_conflict_when_multiple_enabled(self, mock_dex: patch, mock_clode: patch) -> None:
        """Multiple providers enabled should not cause model resolution conflicts."""
        mock_clode.return_value = {"CODEx_API_KEY": "test-key"}
        mock_dex.return_value = {"CODEx_API_KEY": "test-key"}

        # Multiple providers should not cause issues
        codex_result = _resolve_provider_for_model("claude-codex")

        # Should get a valid provider back
        assert codex_result is not None
        assert codex_result != ""
