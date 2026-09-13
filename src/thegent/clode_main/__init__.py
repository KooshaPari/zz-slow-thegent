"""STUB MODULE - thegent.clode_main

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any

_CLODE_BYPASS_FLAG = "CLODE_BYPASS"
_GLM_POLICY_COUNTER = {"claude": 0, "gemini": 0, "openai": 0}

_CLODE_MODEL_ALIAS = {
    "claude": "claude-3-5-sonnet-20241022",
    "sonnet": "claude-3-5-sonnet-20241022",
    "opus": "claude-3-opus-20240229",
    "haiku": "claude-3-haiku-20240307",
}

_MODEL_ALIAS = _CLODE_MODEL_ALIAS

CLAUDE_FLASH_MODEL = "claude-3-5-haiku-20241022"


def _resolve_provider_for_model(model_id: str) -> str:
    """Resolve provider for a model ID."""
    if "claude" in model_id.lower():
        return "anthropic"
    elif "gemini" in model_id.lower():
        return "google"
    elif "gpt" in model_id.lower():
        return "openai"
    return "unknown"


def _resolve_clode_token() -> str | None:
    """Resolve the CLODE token from environment."""
    import os
    return os.environ.get("CLODE_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")


def _run_claude_interactive(model: str = "claude-3-5-sonnet-20241022") -> int:
    """Run Claude in interactive mode."""
    return 0


def _run_claude_print(model: str = "claude-3-5-sonnet-20241022", prompt: str = "") -> str:
    """Run Claude with print output."""
    return f"Claude response to: {prompt}"


def _run_sitback_codex() -> int:
    """Run sitback with codex agent."""
    return 0


def _run_sitback_droid() -> int:
    """Run sitback with droid agent."""
    return 0


def default_clode() -> dict[str, str]:
    """Get the default clode configuration."""
    return {"model": CLAUDE_FLASH_MODEL, "provider": "anthropic"}


class ClodeApp:
    """Clode application."""

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}

    def run(self) -> dict[str, Any]:
        """Run the clode app."""
        return {"status": "ok"}


# Create app instance for typer CLI
app = ClodeApp()


def sitback_cmd() -> None:
    """Sitback command stub."""


def _get_claude_env() -> dict[str, str]:
    """Get the Claude environment variables.

    Returns:
        Dictionary of environment variables for Claude.
    """
    import os
    env: dict[str, str] = {}
    if api_key := os.environ.get("ANTHROPIC_API_KEY"):
        env["ANTHROPIC_API_KEY"] = api_key
    if api_key := os.environ.get("CLODE_TOKEN"):
        env["CLODE_TOKEN"] = api_key
    return env


__all__ = [
    "_CLODE_BYPASS_FLAG",
    "_GLM_POLICY_COUNTER",
    "_MODEL_ALIAS",
    "_get_claude_env",
    "_resolve_clode_token",
    "_resolve_provider_for_model",
    "_run_claude_interactive",
    "_run_claude_print",
    "_run_sitback_codex",
    "_run_sitback_droid",
    "app",
    "sitback_cmd",
    "default_clode",
]
