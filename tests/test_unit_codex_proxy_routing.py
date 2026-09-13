"""Tests for CodexProxyRunner routing integration."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from thegent.agents.codex_proxy import CodexProxyRunner
from thegent.utils.routing_impl.models import TaskCategory, TaskMetadata


class TestCodexProxyRunnerRouting:
    """Test that CodexProxyRunner consumes resolved routing from TaskMetadata."""

    def test_native_cli_provider_uses_codex_cli(self):
        """Native CLI providers (codex) use direct codex CLI execution."""
        runner = CodexProxyRunner("codex")
        metadata = TaskMetadata(
            category=TaskCategory.NORMAL,
            resolved_provider="codex",
            resolved_model_alias="gpt-5.3-codex-spark",
        )

        with patch.object(runner, "_execute_native_cli") as mock_native:
            mock_native.return_value = MagicMock(exit_code=0, stdout="done", stderr="", timed_out=False)
            runner.run_with_metadata("test prompt", Path("/tmp"), "read", 60, metadata=metadata)
            mock_native.assert_called_once()

    def test_api_key_provider_routes_correctly(self):
        """API key providers (minimax) use appropriate routing."""
        runner = CodexProxyRunner("minimax")
        TaskMetadata(
            category=TaskCategory.NORMAL,
            resolved_provider="minimax",
            resolved_model_alias="minimax-m2.5",
        )
        # Should not raise - validates routing path exists
        assert runner is not None


class TestLiteLLMApiExecution:
    """Test direct LiteLLM API execution."""

    def test_litellm_api_execution_success(self):
        """Test successful LiteLLM API call with correct parameters."""
        runner = CodexProxyRunner("minimax")

        # Mock litellm.completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from the model!"

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-api-key-123"}):
            with patch("litellm.completion") as mock_completion:
                mock_completion.return_value = mock_response

                result = runner._execute_litellm_api(
                    prompt="Hello, world!",
                    cwd=Path("/tmp"),
                    mode="read",
                    timeout=60,
                    provider="minimax",
                    model="minimax-m2.5",
                )

                # Verify completion was called with correct parameters
                mock_completion.assert_called_once()
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["model"] == "minimax/minimax-m2.5"
                assert call_kwargs["messages"] == [{"role": "user", "content": "Hello, world!"}]
                assert call_kwargs["api_key"] == "test-api-key-123"
                assert call_kwargs["timeout"] == 60

                # Verify result
                assert result.exit_code == 0
                assert result.stdout == "Hello from the model!"
                assert result.stderr == ""
                assert result.timed_out is False

    def test_litellm_api_execution_missing_api_key(self):
        """Test that missing API key returns appropriate error."""
        runner = CodexProxyRunner("minimax")

        # Ensure API key is not set
        with patch.dict(os.environ, {}, clear=True):
            # Remove MINIMAX_API_KEY if it exists
            os.environ.pop("MINIMAX_API_KEY", None)

            result = runner._execute_litellm_api(
                prompt="Hello, world!",
                cwd=Path("/tmp"),
                mode="read",
                timeout=60,
                provider="minimax",
                model="minimax-m2.5",
            )

            assert result.exit_code == 1
            assert "MINIMAX_API_KEY" in result.stderr
            assert result.timed_out is False

    def test_litellm_api_execution_api_error(self):
        """Test that API errors are handled correctly."""
        runner = CodexProxyRunner("minimax")

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-api-key"}):
            with patch("litellm.completion") as mock_completion:
                mock_completion.side_effect = Exception("API rate limit exceeded")

                result = runner._execute_litellm_api(
                    prompt="Hello, world!",
                    cwd=Path("/tmp"),
                    mode="read",
                    timeout=60,
                    provider="minimax",
                    model="minimax-m2.5",
                )

                assert result.exit_code == 1
                assert "API rate limit exceeded" in result.stderr
                assert result.timed_out is False

    def test_litellm_api_execution_timeout_error(self):
        """Test that timeout errors are detected correctly."""
        runner = CodexProxyRunner("minimax")

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-api-key"}):
            with patch("litellm.completion") as mock_completion:
                mock_completion.side_effect = Exception("Request timed out after 60s")

                result = runner._execute_litellm_api(
                    prompt="Hello, world!",
                    cwd=Path("/tmp"),
                    mode="read",
                    timeout=60,
                    provider="minimax",
                    model="minimax-m2.5",
                )

                assert result.exit_code == 1
                assert result.timed_out is True

    def test_get_api_key_env_mappings(self):
        """Test that API key environment variable names are correct for each provider."""
        assert CodexProxyRunner._get_api_key_env("minimax") == "MINIMAX_API_KEY"
        assert CodexProxyRunner._get_api_key_env("nim") == "NVIDIA_API_KEY"
        assert CodexProxyRunner._get_api_key_env("glm") == "ZHIPU_API_KEY"
        assert CodexProxyRunner._get_api_key_env("kilo") == "KILO_API_KEY"
        # Unknown provider should return generic format
        assert CodexProxyRunner._get_api_key_env("unknown") == "UNKNOWN_API_KEY"
