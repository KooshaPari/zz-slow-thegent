"""Stub module."""

from typing import Any


def validate_required_fields(data: dict[str, Any], required: list[str]) -> tuple[bool, list[str]]:
    """Validate required fields in data."""
    missing = [f for f in required if f not in data]
    return (len(missing) == 0, missing)


__all__ = ["validate_required_fields"]
