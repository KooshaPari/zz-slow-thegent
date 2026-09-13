"""Stub module for thegent.dex_main.

This module provides the CLI entry points for interacting with various AI coding assistants
(Codex, Gemini, Claude, etc.) through the thegent shim layer.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import typer

app = typer.Typer(help="thegent AI coding assistant CLI")

_DEX_BYPASS_FLAG = "--dangerously-bypass-approvals-and-sandbox"
_DEX_YOLO_FLAG = "--dangerously-enable-yolo-mode"

# Model alias mapping
_MODEL_ALIASES: dict[str, str] = {
    # Priority order matters for partial matching
    "dex": "dex-1",
    "high": "codex-high",
    "xhigh": "codex-xhigh",
    "max": "gemini-2.5-pro-preview-06-05",
    "glm": "glm-4",
    "haiku": "claude-3-haiku-20240307",
    "opus": "claude-3-opus-20240229",
    "sonnet": "claude-3-5-sonnet-20241022",
    "ultra": "gemini-ultra",
    "flash": "gemini-2.5-flash",
    "mini": "gpt-4o-mini",
    # composer variants
    "composer": "composer-1.5",
    "composer-1": "composer-1",
    "composer-1.5": "composer-1.5",
    "cursor": "cursor-1",
    "cursor-1": "cursor-1",
    "cursor-2": "cursor-2",
    # Additional aliases
    "claude": "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
    "gpt": "gpt-4o",
    "gpt-4": "gpt-4o",
    "gpt-4o": "gpt-4o",
    "gemini": "gemini-2-5-pro-preview-06-05",
    "gemini-2": "gemini-2-5-pro-preview-06-05",
    "o1": "o1-preview",
    "o1-preview": "o1-preview",
    "o1-mini": "o1-mini",
}


def _get_codex_env() -> dict[str, Any]:
    """Get the Codex environment variables.

    Returns:
        Dictionary of Codex-related environment variables.
    """
    return {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
    }


def resolve_codex_cli_path() -> str:
    """Resolve the path to the Codex CLI binary.

    Returns:
        Path to the codex CLI executable.
    """
    import shutil

    path = shutil.which("codex") or shutil.which("openai-codex")
    return path or "/usr/local/bin/codex"


def wrap_with_caffeinate(cmd: list[str], session_id: str) -> list[str]:
    """Wrap command with caffeinate to prevent idle sleep.

    Args:
        cmd: Command to wrap.
        session_id: Session identifier.

    Returns:
        Wrapped command list.
    """
    return ["caffeinate", "-i", "-s", "-m"] + cmd


def _resolve_provider_for_model(model_alias: str) -> str:
    """Resolve the provider for a model alias.

    Args:
        model_alias: The model alias to resolve.

    Returns:
        Provider name.
    """
    if model_alias in ("dex", "high", "xhigh"):
        return "codex"
    elif model_alias == "composer":
        return "cursor"
    elif model_alias == "step":
        return "nim"
    elif model_alias == "mini":
        return "copilot"
    elif model_alias == "flash":
        return "gemini"
    elif model_alias in ("haiku", "opus", "sonnet"):
        providers = ["claude", "antigravity"]
        import os

        idx = int(os.environ.get("THGGENT_ROUND_ROBIN_INDEX", "0")) % len(providers)
        return providers[idx]
    elif model_alias == "glm":
        providers = ["nim", "kilo", "minimax", "glm"]
        import os

        idx = int(os.environ.get("THGGENT_ROUND_ROBIN_INDEX", "0")) % len(providers)
        return providers[idx]
    elif model_alias == "max":
        providers = ["nim", "kilo", "minimax"]
        import os

        idx = int(os.environ.get("THGGENT_ROUND_ROBIN_INDEX", "0")) % len(providers)
        return providers[idx]
    return "openai"


def _exec_native_codex(args: list[str]) -> None:
    """Execute native codex CLI directly.

    Args:
        args: Arguments to pass to codex.
    """
    codex_path = resolve_codex_cli_path()
    os.execvpe(codex_path, [codex_path] + args, os.environ.copy())


def _run_codex_interactive(
    model: str,
    *,
    dangerously_bypass: bool = False,
    extra_args: list[str] | None = None,
) -> None:
    """Run codex in interactive mode with the specified model.

    Args:
        model: Model alias to use.
        dangerously_bypass: Whether to bypass safety checks.
        extra_args: Additional arguments to pass to codex.
    """

    provider = _resolve_provider_for_model(model)
    _MODEL_ALIAS.get(model, model)

    env = _get_codex_env()

    if provider == "codex":
        env["OPENAI_BASE_URL"] = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8317")
    elif provider == "copilot":
        env["GITHUB_COPILOT_API_URL"] = os.environ.get("GITHUB_COPILOT_API_URL", "http://127.0.0.1:8317")

    codex_path = resolve_codex_cli_path()

    cmd = [codex_path]
    cmd.extend(extra_args or [])

    if dangerously_bypass:
        if _DEX_YOLO_FLAG not in cmd:
            cmd.append(_DEX_YOLO_FLAG)
        if _DEX_BYPASS_FLAG not in cmd:
            cmd.append(_DEX_BYPASS_FLAG)

    wrapped_cmd = wrap_with_caffeinate(cmd, os.environ.get("THGGENT_SESSION_ID", ""))

    os.execvpe(wrapped_cmd[0], wrapped_cmd, env)


def _run_model_cmd(model_alias: str, prompt: str) -> None:
    """Run a model command with the specified alias.

    Args:
        model_alias: Model alias to use.
        prompt: Prompt to send.
    """
    from thegent.cli import run_cmd

    # Two-level lookup: CoMp -> composer-1.5 -> cursor
    canonical_model = _MODEL_ALIAS.get(model_alias, model_alias)
    # Check if the resolved model is also an alias
    canonical_model = _MODEL_ALIAS.get(canonical_model, canonical_model)
    run_cmd(model=canonical_model, prompt=prompt, remote=None)


@app.command()
def config() -> None:
    """Launch the configuration TUI."""
    from thegent.ux.models_providers_tui import run_models_providers_tui

    run_models_providers_tui()


def default_dex_callback(
    force: bool = False,
    native: bool = False,
) -> None:
    """Callback for default dex command."""
    _run_codex_interactive(
        prompt=None,
        model="flash",
        force=force,
        native=native,
        extra_args=["--fast"],
        dangerously_bypass=None,
        dangerously_yolo=None,
    )


@app.callback()
def default_dex(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
    extra_args: list[str] = typer.Option([], help="Extra arguments to pass to the command"),
) -> None:
    """Default command that runs flash model."""
    import sys

    if ctx.invoked_subcommand is not None:
        return

    model = "flash"

    # Check if extra_args were passed via --extra-args
    if extra_args:
        # Get the actual extra_args value (could be list or OptionInfo)
        if hasattr(extra_args, "__iter__") and not isinstance(extra_args, str):
            actual_extra = list(extra_args)
        else:
            actual_extra = []

    # Filter out the -- separator and model from extra_args before passing to codex
    filtered_extra = [arg for arg in actual_extra if arg not in ("--", "--model")]
    # Also remove the model value that follows --model
    cleaned_extra = []
    skip_next = False
    for arg in filtered_extra:
        if skip_next:
            skip_next = False
            continue
        if arg.startswith("--"):
            cleaned_extra.append(arg)
            if arg == "--model":
                skip_next = True

    _run_codex_interactive(model, dangerously_bypass=True, extra_args=cleaned_extra)


# Also expose the subcommands as separate commands
@app.command()
def dex(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run dex with default flash model."""
    if ctx.invoked_subcommand is not None:
        return
    default_dex(ctx, force=force, native=native)


@app.command()
def composer(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run composer model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("composer", dangerously_bypass=True, extra_args=["--search"])


@app.command()
def max(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run max model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("max", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def glm(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run GLM model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("glm", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def haiku(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run Haiku model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("haiku", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def opus(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run Opus model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("opus", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def sonnet(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run Sonnet model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("sonnet", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def ultra(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run Ultra model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("ultra", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def high(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run high model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("high", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def xhigh(
    ctx: typer.Context,
    force: bool = False,
    native: bool = False,
) -> None:
    """Run xhigh model."""
    if ctx.invoked_subcommand is not None:
        return
    _run_codex_interactive("xhigh", dangerously_bypass=force, extra_args=["--search"])


@app.command()
def run(
    model_alias: str,
    prompt: str,
    remote: str | None = None,
) -> None:
    """Run a model with a prompt."""
    # Check if model is known
    if model_alias not in _MODEL_ALIAS:
        allowed = sorted(set(_MODEL_ALIAS.values()))
        typer.echo(f"Error: Unknown model '{model_alias}'")
        typer.echo(f"Allowed: {', '.join(allowed)}")
        raise typer.Abort()
    _run_model_cmd(model_alias, prompt)


@app.command()
def bg(
    model_alias: str,
    prompt: str,
    remote: str | None = None,
    owner: str | None = None,
) -> None:
    """Run a model in background."""
    # Check if model is known
    if model_alias not in _MODEL_ALIAS:
        allowed = sorted(set(_MODEL_ALIAS.values()))
        typer.echo(f"Error: Unknown model '{model_alias}'")
        typer.echo(f"Allowed: {', '.join(allowed)}")
        raise typer.Abort()
    from thegent.cli import bg_cmd

    canonical_model = _MODEL_ALIAS.get(model_alias, model_alias)
    bg_cmd(model=canonical_model, prompt=prompt, remote=remote, owner=owner)


@app.command()
def resume(
    ctx: typer.Context,
    args: list[str] = typer.Argument(["--last"]),
) -> None:
    """Resume previous codex session."""
    _exec_native_codex(["resume"] + args)


@app.command()
def fork(
    ctx: typer.Context,
) -> None:
    """Fork current codex session."""
    _exec_native_codex(["fork"])


__all__ = [
    "app",
    "_DEX_BYPASS_FLAG",
    "_DEX_YOLO_FLAG",
    "_MODEL_ALIAS",
    "_get_codex_env",
    "_resolve_provider_for_model",
    "_run_codex_interactive",
    "_run_model_cmd",
    "_exec_native_codex",
    "resolve_codex_cli_path",
    "wrap_with_caffeinate",
    "default_dex",
]
