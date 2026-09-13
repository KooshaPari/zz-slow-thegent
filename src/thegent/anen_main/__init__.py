"""STUB MODULE - thegent.anen_main

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

GEMINI_FLASH_MODEL = "gemini-2.0-flash"

_MODEL_ALIAS = {
    "flash": GEMINI_FLASH_MODEL,
    "pro": "gemini-2.0-pro",
    "ultra": "gemini-2.0-ultra",
    "dex": "gemini-2.0-pro",
    "high": "gemini-2.0-flash",
    "xhigh": "gemini-2.0-pro",
}


def default_anen(context: dict[str, Any] | None = None) -> dict[str, str]:
    """Get the default anen configuration."""
    return {"model": GEMINI_FLASH_MODEL, "provider": "google"}


def _run_anen_with_alias(alias: str) -> dict[str, str]:
    """Run anen with a model alias."""
    model = _MODEL_ALIAS.get(alias, GEMINI_FLASH_MODEL)
    return {"model": model, "provider": "google"}


def _resolve_anen_cmd() -> str:
    """Resolve the anen command path."""
    return "anen"


# Create a typer app for CLI
try:
    import typer
    app = typer.Typer()
except ImportError:
    # Fallback for when typer is not installed
    class FallbackApp:
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return None

        def main(self, *args: Any, **kwargs: Any) -> Any:
            return None

    app = FallbackApp()


__all__ = [
    "GEMINI_FLASH_MODEL",
    "_MODEL_ALIAS",
    "app",
    "default_anen",
    "_run_anen_with_alias",
    "subprocess",
    "shutil",
    "_resolve_anen_cmd",
]
