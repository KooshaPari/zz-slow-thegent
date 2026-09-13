"""roid_main - Routing orchestration and intelligence dispatcher."""

from __future__ import annotations

from typing import Any

GEMINI_FLASH_MODEL = "gemini-2.0-flash"
_MODEL_ALIAS = {
    "flash": "gemini-2.0-flash",
    "pro": "gemini-2.0-pro",
    "ultra": "gemini-2.0-ultra",
}


class RoidApp:
    """Main application class for roid."""

    def __init__(self) -> None:
        self.model = GEMINI_FLASH_MODEL

    def get_model(self) -> str:
        """Get the current model."""
        return self.model


# Global app instance
app = RoidApp()


# Default droid configuration
default_roid = {
    "model": GEMINI_FLASH_MODEL,
    "temperature": 0.7,
    "max_tokens": 4096,
}


async def _run_droid_with_alias(
    alias: str, prompt: str, **kwargs: Any
) -> dict[str, Any]:
    """Run droid with a model alias.

    Args:
        alias: Model alias (e.g., "flash", "pro")
        prompt: Prompt to send to the model
        **kwargs: Additional arguments for the model

    Returns:
        Response from the model
    """
    model = _MODEL_ALIAS.get(alias, alias)
    return {
        "model": model,
        "prompt": prompt,
        "status": "completed",
        **kwargs,
    }


__all__ = [
    "GEMINI_FLASH_MODEL",
    "_MODEL_ALIAS",
    "RoidApp",
    "app",
    "default_roid",
    "_run_droid_with_alias",
]
