"""STUB MODULE - thegent.models

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any


class ModelCatalog:
    """Catalog of available models."""

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}

    def register(self, model_id: str, model_info: dict[str, Any]) -> None:
        """Register a model."""
        self._models[model_id] = model_info

    def get(self, model_id: str) -> dict[str, Any] | None:
        """Get a model by ID."""
        return self._models.get(model_id)


def normalize_model_id(model_id: str) -> str:
    """Normalize a model ID to canonical form."""
    return model_id.strip().lower()


def resolve_route(provider: str, model_id: str | None = None) -> dict[str, Any]:
    """Resolve routing information for a model."""
    return {
        "provider": provider,
        "model_id": model_id,
        "endpoint": f"https://api.{provider}.com",
    }


def route_contract(provider: str) -> dict[str, Any]:
    """Get the routing contract for a provider."""
    return {
        "provider": provider,
        "supports_streaming": True,
        "supports_function_calling": True,
    }


def resolve_route_contract(provider: str) -> dict[str, Any] | None:
    """Resolve routing contract for a provider. Returns None if not found."""
    if provider:
        return route_contract(provider)
    return None


def filter_models_for_provider(provider: str) -> list[str]:
    """Filter models by provider."""
    return []


__all__ = [
    "ModelCatalog",
    "filter_models_for_provider",
    "normalize_model_id",
    "resolve_route",
    "resolve_route_contract",
    "route_contract",
]
