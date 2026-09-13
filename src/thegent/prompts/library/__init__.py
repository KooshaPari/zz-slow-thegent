"""Stub module."""

from typing import Any


class PromptLibrary:
    """Prompt library."""

    def get(self, key: str) -> str:
        """Get a prompt by key."""
        return ""


def get_prompt_library() -> PromptLibrary:
    """Get the global prompt library instance."""
    return PromptLibrary()


__all__ = ["PromptLibrary", "get_prompt_library", "reset_prompt_library"]


def reset_prompt_library() -> None:
    """Reset the prompt library."""
