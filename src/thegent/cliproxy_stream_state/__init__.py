"""CLIProxy stream state management.

This module provides state management for streaming responses.
"""

from __future__ import annotations

from typing import Any


class ResponsesStreamState:
    """Manages state for streaming responses.

    This class tracks the state of a streaming response session,
    including accumulated content, tool calls, and usage metrics.
    """

    def __init__(self, request_id: str) -> None:
        """Initialize stream state.

        Args:
            request_id: The request identifier.
        """
        self.request_id = request_id
        self._content: list[str] = []
        self._tool_calls: list[dict[str, Any]] = []
        self._usage: dict[str, Any] = {}

    def add_content(self, content: str) -> None:
        """Add content to the stream.

        Args:
            content: Content to add.
        """
        self._content.append(content)

    def add_tool_call(self, tool_call: dict[str, Any]) -> None:
        """Add a tool call to the stream.

        Args:
            tool_call: Tool call to add.
        """
        self._tool_calls.append(tool_call)

    def set_usage(self, usage: dict[str, Any]) -> None:
        """Set usage metrics.

        Args:
            usage: Usage dictionary.
        """
        self._usage = usage

    @property
    def content(self) -> str:
        """Get accumulated content.

        Returns:
            Concatenated content string.
        """
        return "".join(self._content)

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        """Get accumulated tool calls.

        Returns:
            List of tool calls.
        """
        return self._tool_calls

    @property
    def usage(self) -> dict[str, Any]:
        """Get usage metrics.

        Returns:
            Usage dictionary.
        """
        return self._usage

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary.

        Returns:
            State dictionary.
        """
        return {
            "request_id": self.request_id,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "usage": self.usage,
        }


__all__ = [
    "ResponsesStreamState",
]
