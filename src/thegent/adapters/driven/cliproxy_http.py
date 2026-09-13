"""CLIProxy HTTP client adapter.

This module provides the HTTP client adapter for CLIProxy.
"""

from __future__ import annotations

from typing import Any


class CliproxyHTTPClient:
    """HTTP client for CLIProxy."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize the HTTP client.

        Args:
            base_url: Base URL for the CLIProxy service.
        """
        self.base_url = base_url or "http://localhost:8080"

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Perform a GET request.

        Args:
            path: API path.
            **kwargs: Additional request options.

        Returns:
            Response dictionary.
        """
        return {}

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Perform a POST request.

        Args:
            path: API path.
            **kwargs: Additional request options.

        Returns:
            Response dictionary.
        """
        return {}


class CliproxyResponseTransformer:
    """Transforms CLIProxy responses."""

    def transform(self, response: dict[str, Any]) -> dict[str, Any]:
        """Transform a response.

        Args:
            response: Raw response.

        Returns:
            Transformed response.
        """
        return response


class CliproxyHeaderManager:
    """Manages headers for CLIProxy requests."""

    def __init__(self) -> None:
        """Initialize the header manager."""

    def get_headers(self) -> dict[str, str]:
        """Get default headers.

        Returns:
            Header dictionary.
        """
        return {}


__all__ = [
    "CliproxyHTTPClient",
    "CliproxyResponseTransformer",
    "CliproxyHeaderManager",
]
