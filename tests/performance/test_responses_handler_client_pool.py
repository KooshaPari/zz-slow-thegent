"""Tests for WL-071: Persistent httpx.AsyncClient in litellm_responses_handler."""

from __future__ import annotations

import pytest


@pytest.mark.requirement("FR-OPT-002")
class TestResponsesHandlerClientPool:
    """Verify that the shared httpx.AsyncClient is reused across calls."""

    def _reset_client(self):
        """Reset the module-level client between tests."""
        from thegent.utils.routing_impl import litellm_responses_handler as mod

        mod._http_client = None

    def test_two_calls_return_same_client(self):
        """Two calls to _get_http_client() return the same instance."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _get_http_client,
        )

        self._reset_client()

        first = _get_http_client()
        second = _get_http_client()

        assert first is second
        assert not first.is_closed

    @pytest.mark.asyncio
    async def test_close_shared_client_resets_singleton(self):
        """close_http_client() sets the module-level client back to None."""
        from thegent.utils.routing_impl import litellm_responses_handler as mod
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _get_http_client,
            close_http_client,
        )

        self._reset_client()

        client = _get_http_client()
        assert client is not None

        await close_http_client()
        assert mod._http_client is None
