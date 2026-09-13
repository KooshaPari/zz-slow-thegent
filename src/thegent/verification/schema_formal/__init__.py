"""Stub module."""

from typing import TYPE_CHECKING, Any


class SchemaEvolutionVerifier:
    """Schema evolution verifier stub."""

    def verify(self, old_schema: dict[str, Any], new_schema: dict[str, Any]) -> dict[str, Any]:
        return {"compatible": True}


__all__ = ["SchemaEvolutionVerifier"]
