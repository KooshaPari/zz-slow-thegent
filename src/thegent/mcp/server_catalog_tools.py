"""WL-126: server_catalog_tools stable import surface.

Catalog helpers for listing and invoking MCP server operations.  Stub
module that satisfies the WL-126 import-surface check; the real
implementation is expected to land in a follow-up slice alongside any
future MCP server catalog work.
"""

from __future__ import annotations

from typing import Any


def thegent_list_operations_impl(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Return catalog listing.  Stub returning an empty envelope."""
    return {"operations": [], "count": 0}


def register_catalog_tool(tool_name: str, *, description: str = "", handler: Any = None) -> dict[str, Any]:
    """Register a catalog tool (stub).

    Returns a confirmation envelope indicating the tool was registered.
    """
    return {"registered": True, "tool_name": tool_name, "description": description}


def invoke_catalog_tool(tool_name: str, *, args: Any = None) -> dict[str, Any]:
    """Invoke a registered catalog tool (stub).

    Returns an envelope with the invocation result.
    """
    return {"ok": True, "tool_name": tool_name, "result": None, "args": args}


__all__ = [
    "thegent_list_operations_impl",
    "register_catalog_tool",
    "invoke_catalog_tool",
]
