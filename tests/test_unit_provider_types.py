"""Tests for provider type classification."""

import pytest

from thegent.utils.routing_impl.provider_types import (
    NATIVE_CLI_PROVIDERS,
    ExecutionPath,
    get_execution_path,
    normalize_provider_name,
)


class TestProviderClassification:
    """Test provider type classification for execution path routing."""

    def test_native_cli_providers_immutable(self):
        """Native CLI providers set is frozen."""
        with pytest.raises((AttributeError, TypeError)):
            NATIVE_CLI_PROVIDERS.add("new_provider")

    def test_codex_is_native_cli(self):
        """Codex uses native CLI execution."""
        assert get_execution_path("codex") == ExecutionPath.NATIVE_CLI

    def test_claude_is_native_cli(self):
        """Claude uses native CLI execution (interactive)."""
        assert get_execution_path("claude") == ExecutionPath.NATIVE_CLI

    def test_minimax_is_api_key(self):
        """Minimax uses LiteLLM direct API."""
        assert get_execution_path("minimax") == ExecutionPath.LITELLM_API

    def test_nim_is_api_key(self):
        """NIM uses LiteLLM direct API."""
        assert get_execution_path("nim") == ExecutionPath.LITELLM_API

    def test_glm_is_api_key(self):
        """GLM uses LiteLLM direct API."""
        assert get_execution_path("glm") == ExecutionPath.LITELLM_API

    def test_kilo_is_api_key(self):
        """Kilo uses LiteLLM direct API."""
        assert get_execution_path("kilo") == ExecutionPath.LITELLM_API

    def test_ollama_is_litellm_api(self):
        """Ollama uses LiteLLM execution path."""
        assert get_execution_path("ollama") == ExecutionPath.LITELLM_API

    def test_ollama_local_alias_normalizes(self):
        """`ollama-local` is accepted as alias for `ollama`."""
        assert normalize_provider_name("ollama-local") == "ollama"
        assert get_execution_path("ollama-local") == ExecutionPath.LITELLM_API

    @pytest.mark.parametrize("alias", ["local-ollama", "ollama-localhost", "ollama@localhost"])
    def test_additional_ollama_aliases_normalize(self, alias: str):
        """WL-118: additional local aliases normalize to canonical provider."""
        assert normalize_provider_name(alias) == "ollama"
        assert get_execution_path(alias) == ExecutionPath.LITELLM_API

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("  OLLAMA-LOCAL ", "ollama"),
            (" Local-Ollama", "ollama"),
            ("\tollama@localhost\n", "ollama"),
        ],
    )
    def test_ollama_alias_normalization_handles_case_and_whitespace(self, raw: str, expected: str):
        """WL-118: alias normalization should be deterministic for shell/user inputs."""
        assert normalize_provider_name(raw) == expected

    def test_unknown_provider_is_login_auth(self):
        """Unknown providers default to CLIProxyAPIPlus."""
        assert get_execution_path("unknown_provider") == ExecutionPath.CLIPROXY_API

    def test_antigravity_is_login_auth(self):
        """Antigravity uses CLIProxyAPIPlus (LOGIN auth)."""
        assert get_execution_path("antigravity") == ExecutionPath.CLIPROXY_API
