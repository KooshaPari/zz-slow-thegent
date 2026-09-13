"""Stub module."""

from typing import Any


class MAIFArtifactGenerator:
    """Generates MAIF artifacts."""

    def __init__(self) -> None:
        self.artifacts: list[Any] = []

    def generate(self, spec: dict[str, Any]) -> Any:
        """Generate an artifact from spec."""
        return {"generated": True}


__all__ = ["MAIFArtifactGenerator"]
