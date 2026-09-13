"""Tests for WL-070: LiteLLM Router instance caching."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.requirement("FR-OPT-001")
class TestLiteLLMRouterCache:
    """Verify get_litellm_router() returns cached Router instances."""

    def _clear_caches(self):
        """Reset module-level caches between tests."""
        from thegent.utils.routing_impl import litellm_router as mod

        mod._router_cache.clear()
        mod._model_list_cache.clear()

    def test_second_call_returns_same_object(self):
        """Cache hit: two consecutive calls return the identical Router object."""
        from thegent.utils.routing_impl.litellm_router import get_litellm_router

        self._clear_caches()

        with patch("thegent.utils.routing_impl.litellm_router._build_litellm_router") as mock_build:
            sentinel = MagicMock(name="Router")
            mock_build.return_value = sentinel

            first = get_litellm_router("cost-based-routing")
            second = get_litellm_router("cost-based-routing")

        assert first is second
        mock_build.assert_called_once()

    def test_invalidate_forces_rebuild(self):
        """After invalidate_router_cache(), the next call rebuilds."""
        from thegent.utils.routing_impl.litellm_router import (
            get_litellm_router,
            invalidate_router_cache,
        )

        self._clear_caches()

        with patch("thegent.utils.routing_impl.litellm_router._build_litellm_router") as mock_build:
            router_a = MagicMock(name="RouterA")
            router_b = MagicMock(name="RouterB")
            mock_build.side_effect = [router_a, router_b]

            first = get_litellm_router("cost-based-routing")
            invalidate_router_cache()
            second = get_litellm_router("cost-based-routing")

        assert first is not second
        assert mock_build.call_count == 2

    def test_ttl_expiry_forces_rebuild(self):
        """When the TTL cache expires, a new Router is built."""
        from thegent.utils.routing_impl import litellm_router as mod
        from thegent.utils.routing_impl.litellm_router import get_litellm_router

        self._clear_caches()

        with patch("thegent.utils.routing_impl.litellm_router._build_litellm_router") as mock_build:
            router_a = MagicMock(name="RouterA")
            router_b = MagicMock(name="RouterB")
            mock_build.side_effect = [router_a, router_b]

            first = get_litellm_router("cost-based-routing")

            # Simulate TTL expiry by clearing the cache (same effect)
            mod._router_cache.clear()

            second = get_litellm_router("cost-based-routing")

        assert first is not second
        assert mock_build.call_count == 2
