"""CLIProxy header utilities.

This module provides utilities for handling headers in CLIProxy requests and responses.
"""

from __future__ import annotations

from typing import Any


def extract_websocket_forward_headers(headers: dict[str, str]) -> dict[str, str]:
    """Extract headers to forward for WebSocket connections.

    Args:
        headers: Original headers dictionary.

    Returns:
        Filtered headers for WebSocket forwarding.
    """
    return {k: v for k, v in headers.items() if k.lower() not in ("host", "connection")}


def filter_inbound_response_headers(headers: dict[str, str]) -> dict[str, str]:
    """Filter inbound response headers.

    Args:
        headers: Response headers.

    Returns:
        Filtered response headers.
    """
    return {k: v for k, v in headers.items() if k.lower() not in ("transfer-encoding", "connection")}


def sanitize_outbound_request_headers(headers: dict[str, str]) -> dict[str, str]:
    """Sanitize outbound request headers.

    Args:
        headers: Request headers.

    Returns:
        Sanitized request headers.
    """
    return {k: v for k, v in headers.items() if k.lower() not in ("x-forwarded-for", "x-real-ip")}


__all__ = [
    "extract_websocket_forward_headers",
    "filter_inbound_response_headers",
    "sanitize_outbound_request_headers",
]
