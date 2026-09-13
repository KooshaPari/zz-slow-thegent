"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelMeta:
    """Model metadata."""

    name: str
    version: str = "1.0"


MODEL_METADATA: dict[str, dict] = {
    "default": {
        "name": "default",
        "version": "1.0",
        "max_tokens": 100000,
    }
}


__all__ = ["ModelMeta", "MODEL_METADATA"]
