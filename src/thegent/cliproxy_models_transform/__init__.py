"""CLIProxy models transform utilities.

This module provides utilities for transforming model responses.
"""

from __future__ import annotations

from typing import Any


def _compute_models_etag(models: list[dict[str, Any]]) -> str:
    """Compute an ETag for models list.

    Args:
        models: List of model dictionaries.

    Returns:
        ETag string.
    """
    import hashlib

    content = str(sorted(models, key=lambda m: m.get("id", "")))
    return f'"{hashlib.md5(content.encode()).hexdigest()}"'


def transform_models_response(response: dict[str, Any]) -> dict[str, Any]:
    """Transform a models response.

    Args:
        response: Raw models response.

    Returns:
        Transformed response.
    """
    return response


class _LegacyModelsTransformResult(bytes):
    """Legacy compatibility class for models transform results."""

    def __init__(self, compact_body: bytes, full_body: bytes, etag: str) -> None:
        self._full_body = full_body
        self._etag = etag
        super().__init__()

    def __iter__(self):
        yield self._full_body
        yield self._etag


__all__ = [
    "_compute_models_etag",
    "transform_models_response",
    "_LegacyModelsTransformResult",
]
