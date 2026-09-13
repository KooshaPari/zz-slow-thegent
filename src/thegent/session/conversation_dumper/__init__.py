"""Stub module."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_DUMPS_DIR = Path("~/.thegent/dumps").expanduser()


class ConversationDumper:
    """Dumper for conversation history."""

    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []

    def dump(self) -> str:
        """Dump conversation history as JSON."""
        return json.dumps(self.history)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to history."""
        self.history.append({"role": role, "content": content})


__all__ = ["ConversationDumper", "ConversationRecord", "DEFAULT_DUMPS_DIR", "get_dumper"]


def get_dumper(dumper_type: str = "json") -> ConversationDumper:
    """Get a conversation dumper by type.

    Args:
        dumper_type: Type of dumper ("json", "text", etc.).

    Returns:
        A ConversationDumper instance.
    """
    return ConversationDumper()


@dataclass
class ConversationRecord:
    """Record of a conversation."""
    id: str = ""
    messages: list[dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.messages is None:
            self.messages = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append({"role": role, "content": content})
