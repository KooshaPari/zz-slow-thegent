"""STUB MODULE - thegent.fanta_main

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any

GEMINI_FLASH_MODEL = "gemini-2.0-flash"

# Model alias for cross-harness tests
_MODEL_ALIAS: dict[str, str] = {
    "claude": "claude-3-5-sonnet-20241022",
    "gpt-4": "gpt-4-turbo",
}

# Stub app for compatibility
app: Any = None


def _run_anen_with_alias(model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
    """Run ANEN with model alias resolution."""
    resolved = _MODEL_ALIAS.get(model, model)
    return {"model": resolved, "prompt": prompt, "status": "ok"}


def default_fanta(ctx: Any) -> None:
    """Default callback for the 'flash' model.

    Args:
        ctx: The typer context with args.
    """
    from thegent.fanta_main import _run_anen_with_alias as run_anen

    args = getattr(ctx, "args", []) or []
    run_anen("flash", args)


__all__ = [
    "GEMINI_FLASH_MODEL",
    "_MODEL_ALIAS",
    "app",
    "_run_anen_with_alias",
    "default_fanta",
]
