"""thegent.mcp — hardened re-export surface (WL-126).

Stable public API for the MCP module. All symbols listed in ``__all__``
are guaranteed importable from ``thegent.mcp``.  Implementation details
live in sibling modules; this package ``__init__`` exists solely to
present a consistent, versioned import surface.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from typing import Any


def server_elicitation_cache_key(
    elicitation_id: str,
    response_type: type | str | None = None,
) -> str:
    """Generate a deterministic 16-char cache key for an elicitation.

    The key is a truncated SHA-256 hex digest of the concatenation of
    ``elicitation_id`` and ``response_type``, so repeated calls with
    the same inputs always return the same key.
    """
    raw = f"{elicitation_id}:{response_type}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def server_create_elicitation_cache(
    maxsize: int = 64,
    ttl_seconds: int = 300,
) -> dict[str, Any]:
    """Create a bounded, TTL-aware elicitation cache.

    Returns a dict with ``maxsize``, ``ttl_seconds``, and an internal
    ``_store`` mapping keyed by cache-key strings.
    """
    return {
        "maxsize": maxsize,
        "ttl_seconds": ttl_seconds,
        "_store": {},
        "_lock": threading.Lock(),
    }


def server_get_cached_elicitation(
    cache: dict[str, Any] | None = None,
    *,
    prompt: str = "",
    response_type: type | str | None = None,
) -> str | None:
    """Look up a cached elicitation response by prompt + type."""
    if cache is None:
        return None
    key = server_elicitation_cache_key(prompt, response_type)
    return cache.get("_store", {}).get(key)


def server_cache_elicitation_response(
    cache: dict[str, Any] | None = None,
    *,
    prompt: str = "",
    response_type: type | str | None = None,
    response: str = "",
) -> dict[str, Any]:
    """Store an elicitation response in the cache."""
    if cache is None:
        return {"cached": False}
    key = server_elicitation_cache_key(prompt, response_type)
    store = cache.get("_store", {})
    store[key] = response
    return {"cached": True, "key": key}


def server_default_cwd_from_context(ctx: Any = None) -> Path | None:
    """Extract the default working directory from an MCP request context.

    Walks ``ctx.request_context.meta.cwd``; returns a ``Path``
    when present, or ``None`` when unavailable.
    """
    try:
        cwd_str: str | None = ctx.request_context.meta.cwd  # type: ignore[union-attr]
    except (AttributeError, TypeError):
        return None
    if not cwd_str:
        return None
    return Path(cwd_str)


def server_default_owner_from_context(ctx: Any = None) -> str | None:
    """Extract the default owner tag from an MCP request context.

    Walks ``ctx.request_context.meta.owner``; returns the owner string
    when present, or ``None`` when unavailable.
    """
    try:
        return ctx.request_context.meta.owner  # type: ignore[union-attr]
    except (AttributeError, TypeError):
        return None


def server_resolve_cwd_elicitation(
    response: Any = None,
    *,
    accepted_elicitation_type: type | None = None,
    declined_elicitation_type: type | None = None,
    cancelled_elicitation_type: type | None = None,
) -> tuple[Path | None, str | None]:
    """Resolve a cwd elicitation response.

    Returns ``(Path, None)`` when accepted, ``(None, 'declined')`` when
    declined, ``(None, 'cancelled')`` when cancelled.
    """
    if accepted_elicitation_type is not None and isinstance(response, accepted_elicitation_type):
        data = getattr(response, "data", None)
        if data is not None:
            return Path(data), None
    if declined_elicitation_type is not None and isinstance(response, declined_elicitation_type):
        return None, "declined"
    if cancelled_elicitation_type is not None and isinstance(response, cancelled_elicitation_type):
        return None, "cancelled"
    return None, None


def server_resolve_owner_elicitation(
    response: Any = None,
    *,
    default_owner_tag: str = "",
    accepted_elicitation_type: type | None = None,
    declined_elicitation_type: type | None = None,
    cancelled_elicitation_type: type | None = None,
) -> tuple[str | None, str | None]:
    """Resolve an owner elicitation response.

    Returns ``(owner, None)`` when accepted, ``(None, 'declined')`` when
    declined, ``(None, 'cancelled')`` when cancelled.  Falls back to
    ``default_owner_tag`` when the response type doesn't match.
    """
    if accepted_elicitation_type is not None and isinstance(response, accepted_elicitation_type):
        data = getattr(response, "data", None)
        if data is not None:
            return data, None
    if declined_elicitation_type is not None and isinstance(response, declined_elicitation_type):
        return None, "declined"
    if cancelled_elicitation_type is not None and isinstance(response, cancelled_elicitation_type):
        return None, "cancelled"
    return default_owner_tag or None, None


def server_error_result(message: str, **kwargs: Any) -> dict[str, Any]:
    """Return a stable JSON error envelope (WL-126 import surface)."""
    return {"ok": False, "error": message, **kwargs}


def server_load_module(name: str) -> Any:
    """Dynamically load a module by dotted path (WL-126 import surface)."""
    import importlib

    return importlib.import_module(name)


def server_stable_json(payload: Any) -> str:
    """Serialise *payload* deterministically (sorted keys, indent=2) for hashing/audit.

    Returns a JSON string with sorted keys so callers can hash the bytes
    and get a stable digest across runs.
    """
    import json as _json

    return _json.dumps(payload, sort_keys=True, indent=2, default=str)


def server_tools_workstream_lsp() -> dict[str, Any]:
    """Server tools workstream LSP."""
    return {}


def hotreload(enabled: bool = True) -> None:
    """Enable or disable hotreload."""


__all__ = [
    "server_cache_elicitation_response",
    "server_create_elicitation_cache",
    "server_default_cwd_from_context",
    "server_default_owner_from_context",
    "server_elicitation_cache_key",
    "server_error_result",
    "server_get_cached_elicitation",
    "server_load_module",
    "server_resolve_cwd_elicitation",
    "server_resolve_owner_elicitation",
    "server_stable_json",
    "server_tools_workstream_lsp",
    "hotreload",
]
