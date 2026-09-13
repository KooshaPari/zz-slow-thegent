"""CLIProxy request transform utilities.

This module provides utilities for transforming requests between different API formats.
"""

from __future__ import annotations

from typing import Any

# Fields that pass through without transformation
_OR_PASSTHROUGH_FIELDS = {"model", "messages", "stream"}


def _extract_delta_content(delta: dict[str, Any]) -> str | None:
    """Extract content from a streaming delta.

    Args:
        delta: Delta dictionary.

    Returns:
        Content string or None.
    """
    return delta.get("content", "")


def _extract_delta_tool_calls(delta: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tool calls from a streaming delta.

    Args:
        delta: Delta dictionary.

    Returns:
        List of tool calls.
    """
    return delta.get("tool_calls", [])


def _extract_usage(response: dict[str, Any]) -> dict[str, Any]:
    """Extract usage information from a response.

    Args:
        response: Response dictionary.

    Returns:
        Usage dictionary.
    """
    return response.get("usage", {})


def _map_model_for_backend(model: str, backend: str) -> str:
    """Map a model name for a specific backend.

    Args:
        model: Original model name.
        backend: Target backend.

    Returns:
        Mapped model name.
    """
    return model


def _process_sse_line(line: str) -> dict[str, Any] | None:
    """Process a single SSE line.

    Args:
        line: SSE line to process.

    Returns:
        Parsed data or None.
    """
    if line.startswith("data: "):
        import json
        return json.loads(line[6:])
    return None


def build_openrouter_passthrough_body(body: dict[str, Any]) -> dict[str, Any]:
    """Build a passthrough body for OpenRouter.

    Args:
        body: Original request body.

    Returns:
        Passthrough body.
    """
    return {k: v for k, v in body.items() if k in _OR_PASSTHROUGH_FIELDS}


def _responses_to_chat_completions(body: dict[str, Any]) -> dict[str, Any]:
    """Convert responses API body to chat completions format.

    Args:
        body: Responses API body.

    Returns:
        Chat completions format body.
    """
    return body


__all__ = [
    "_OR_PASSTHROUGH_FIELDS",
    "_extract_delta_content",
    "_extract_delta_tool_calls",
    "_extract_usage",
    "_map_model_for_backend",
    "_process_sse_line",
    "build_openrouter_passthrough_body",
    "_responses_to_chat_completions",
]
