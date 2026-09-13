"""Stub module."""

from typing import Any


def lint_workstream_schema(schema: dict[str, Any]) -> list[str]:
    """Lint a workstream schema."""
    return []


__all__ = ["lint_workstream_schema", "normalize_workstream_sections"]


def normalize_workstream_sections(
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize workstream sections to a standard format."""
    return sections
