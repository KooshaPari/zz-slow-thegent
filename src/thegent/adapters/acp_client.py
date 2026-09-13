"""ACP HTTP client adapter.

Provides async HTTP client for communicating with ACP agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_AGENT_ID = "thegent"

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ACPClientError(Exception):
    """Raised when ACP client receives an error response from the server."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class ACPServerUnreachableError(Exception):
    """Raised when the ACP server cannot be reached."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ACPResult:
    """Result from an ACP agent call."""

    success: bool
    result: str
    agent_id: str
    elapsed_ms: float


# ---------------------------------------------------------------------------
# Retry logic helper
# ---------------------------------------------------------------------------


def _is_retryable(error: Exception) -> bool:
    """Determine if an exception is retryable.

    Args:
        error: The exception to check.

    Returns:
        True if the error should trigger a retry.
    """
    if isinstance(error, httpx.ConnectError):
        return True
    if isinstance(error, httpx.ReadTimeout):
        return True
    if isinstance(error, httpx.RemoteProtocolError):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        # Retry on rate limiting
        if error.response.status_code == 429:
            return True
        # Retry on service unavailable
        if error.response.status_code == 503:
            return True
    return False


# ---------------------------------------------------------------------------
# ACPClient
# ---------------------------------------------------------------------------


class ACPClient:
    """Async HTTP client for ACP agent communication."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        agent_id: str = DEFAULT_AGENT_ID,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the ACP client.

        Args:
            base_url: Base URL for the ACP server.
            agent_id: Identifier for this agent.
            timeout: Request timeout in seconds.
        """
        self._base_url = base_url.rstrip("/")
        self._agent_id = agent_id
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send_task(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ACPResult:
        """Send a task to the ACP server.

        Args:
            task: The task description.
            context: Optional context dictionary.
            timeout: Optional override for request timeout.

        Returns:
            ACPResult with the agent's response.

        Raises:
            ACPClientError: On HTTP error responses.
            ACPServerUnreachableError: On connection failures.
        """
        import time

        start = time.monotonic()

        payload: dict[str, Any] = {
            "task": task,
            "agent_id": self._agent_id,
        }
        if context is not None:
            payload["context"] = context

        try:
            client = await self._get_client()
            resp = await client.post(
                "/tasks",
                json=payload,
                timeout=timeout or self._timeout,
            )

            if not resp.is_success:
                raise ACPClientError(resp.status_code, resp.text)

            data = resp.json()
            elapsed = (time.monotonic() - start) * 1000

            return ACPResult(
                success=True,
                result=data.get("result", ""),
                agent_id=data.get("agent_id", "unknown"),
                elapsed_ms=elapsed,
            )

        except httpx.ConnectError as e:
            raise ACPServerUnreachableError(f"Cannot connect to {self._base_url}") from e
        except httpx.ReadTimeout as e:
            raise ACPServerUnreachableError("Request timed out") from e
        except httpx.RemoteProtocolError as e:
            raise ACPServerUnreachableError(f"Protocol error: {e}") from e
        except httpx.HTTPStatusError as e:
            if _is_retryable(e):
                raise ACPServerUnreachableError(f"Server error: {e.response.status_code}") from e
            raise ACPClientError(e.response.status_code, e.response.text) from e

    async def health_check(self) -> bool:
        """Check if the ACP server is healthy.

        Returns:
            True if the server responds successfully.
        """
        try:
            client = await self._get_client()
            resp = await client.get("/health")
            return resp.is_success
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"ACPClient(base_url={self._base_url!r}, agent_id={self._agent_id!r})"
