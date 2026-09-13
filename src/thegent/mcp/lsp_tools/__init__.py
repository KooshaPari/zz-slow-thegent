"""Stub module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SymbolInfo:
    """LSP symbol information."""
    name: str = ""
    kind: int = 0
    location: dict = field(default_factory=dict)
    container_name: str = ""


@dataclass
class Diagnostic:
    """LSP diagnostic."""
    message: str
    severity: int = 1
    range_start: int = 0
    range_end: int = 0


__all__ = ["Diagnostic", "HoverInfo", "LspToolAdapter", "lsp_diagnostics", "lsp_diagnostics_impl", "SymbolInfo"]


def lsp_diagnostics_impl(uri: str, options: dict | None = None) -> list[Diagnostic]:
    """Get LSP diagnostics for a URI with additional options.

    Args:
        uri: The file URI to get diagnostics for.
        options: Additional diagnostic options.

    Returns:
        List of Diagnostic objects.
    """
    # Implementation stub - returns empty list
    return []


class LspToolAdapter:
    """Adapter for LSP tools."""

    def __init__(self) -> None:
        self.tools: dict = {}

    def register_tool(self, name: str, handler) -> None:
        """Register an LSP tool."""
        self.tools[name] = handler

    def execute(self, tool_name: str, params: dict) -> dict:
        """Execute an LSP tool."""
        handler = self.tools.get(tool_name)
        if handler:
            return handler(params)
        return {"error": f"Unknown tool: {tool_name}"}


@dataclass
class HoverInfo:
    """LSP hover information."""
    content: str = ""
    format: str = "plaintext"


def lsp_diagnostics(uri: str) -> list[Diagnostic]:
    """Get LSP diagnostics for a URI."""
    return []


def lsp_hover(uri: str, position: dict) -> HoverInfo:
    """Get LSP hover information for a position in a document.

    Args:
        uri: The file URI.
        position: Position dict with line and character.

    Returns:
        HoverInfo object with content and format.
    """
    return HoverInfo(content="", format="plaintext")


__all__ = [
    "Diagnostic",
    "HoverInfo",
    "LspToolAdapter",
    "lsp_diagnostics",
    "lsp_diagnostics_impl",
    "lsp_hover",
    "SymbolInfo",
    "lsp_hover_impl",
    "lsp_symbol_lookup",
    "lsp_symbol_lookup_impl",
    "_validate_existing_file",
    "_ensure_position",
]


def _ensure_position(position: dict[str, Any]) -> dict[str, int]:
    """Ensure position has valid line and character values.

    Args:
        position: Position dictionary.

    Returns:
        Validated position with line and character.
    """
    return {
        "line": max(0, position.get("line", 0)),
        "character": max(0, position.get("character", 0)),
    }


def _validate_existing_file(uri: str) -> bool:
    """Validate that an existing file is accessible.

    Args:
        uri: File URI to validate.

    Returns:
        True if the file exists and is accessible.
    """
    import os
    path = uri[7:] if uri.startswith("file://") else uri
    return os.path.exists(path)


def lsp_symbol_lookup_impl(symbol_name: str, uri: str | None = None) -> list[SymbolInfo]:
    """Implementation for LSP symbol lookup.

    Args:
        symbol_name: Name of the symbol to look up.
        uri: Optional file URI to search in.

    Returns:
        List of SymbolInfo objects.
    """
    return []


def lsp_hover_impl(uri: str, position: dict) -> HoverInfo:
    """Implementation for LSP hover command.

    Args:
        uri: The file URI.
        position: Position dict with line and character.

    Returns:
        HoverInfo object with content and format.
    """
    return HoverInfo(content="", format="plaintext")


def lsp_symbol_lookup(symbol_name: str, uri: str | None = None) -> list[SymbolInfo]:
    """Look up a symbol by name.

    Args:
        symbol_name: Name of the symbol to look up.
        uri: Optional file URI to search in.

    Returns:
        List of SymbolInfo objects.
    """
    return []
