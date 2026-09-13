"""JSONL parsing utilities for execution logs."""

from __future__ import annotations

import json
from typing import Any

# Diagnostics state
_native_parse_diagnostics: dict[str, Any] = {
    "total_failures": 0,
    "by_parser": {},
    "last_error_type": None,
    "last_error_message": None,
}


def reset_native_parse_diagnostics() -> None:
    """Reset the native parse diagnostics counter."""
    global _native_parse_diagnostics
    _native_parse_diagnostics = {
        "total_failures": 0,
        "by_parser": {},
        "last_error_type": None,
        "last_error_message": None,
    }


def get_native_parse_diagnostics() -> dict[str, Any]:
    """Get the native parse diagnostics.

    Returns:
        Dictionary with total_failures, by_parser, last_error_type.
    """
    return _native_parse_diagnostics.copy()


def _get_native_parser():
    """Get the native parser class if available."""
    # Stub - would return actual native parser if available
    return


def parse_checkpoint_by_id(line: str, checkpoint_id: str) -> dict[str, Any] | None:
    """Parse a checkpoint from a JSONL line.

    Args:
        line: JSON line to parse
        checkpoint_id: Expected checkpoint ID

    Returns:
        Parsed checkpoint dict, or None if parsing fails
    """
    global _native_parse_diagnostics

    # Try native parser first
    native = _get_native_parser()
    if native:
        try:
            result = native.parse_checkpoint_by_id(line, checkpoint_id)
            if result is not None:
                return result
        except Exception as e:
            # Native parser failed, fall through to JSON parsing
            _native_parse_diagnostics["total_failures"] += 1
            _native_parse_diagnostics["by_parser"]["parse_checkpoint_by_id"] = (
                _native_parse_diagnostics["by_parser"].get("parse_checkpoint_by_id", 0)
                + 1
            )
            _native_parse_diagnostics["last_error_type"] = type(e).__name__
            _native_parse_diagnostics["last_error_message"] = str(e)

    # Fall back to JSON parsing
    try:
        data = json.loads(line)
        if isinstance(data, dict) and data.get("checkpoint_id") == checkpoint_id:
            return data
    except json.JSONDecodeError:
        pass

    return None


__all__ = [
    "reset_native_parse_diagnostics",
    "get_native_parse_diagnostics",
    "parse_checkpoint_by_id",
]
