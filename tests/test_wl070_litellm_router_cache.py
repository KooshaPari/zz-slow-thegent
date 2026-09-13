"""Tests for WL-070: TTLCache on get_litellm_router().

Verifies that repeated calls within the TTL window return the same cached Router
instance, that the builder is called only once per TTL period, and that the cache
key is scoped per policy value.

# @trace WL-070
"""

from __future__ import annotations

from threading import Thread
from unittest.mock import MagicMock, patch


class TestGetLitellmRouterCaching:
    """WL-070: get_litellm_router() is cached via TTLCache for 5 minutes."""

    def _clear_cache(self):
        from thegent.utils.routing_impl.litellm_router import _router_cache

        _router_cache.clear()

    def test_repeated_calls_return_same_instance(self):
        """# @trace WL-070 — same Router object returned on two consecutive calls."""
        self._clear_cache()
        sentinel = MagicMock(name="router_sentinel")

        with patch(
            "thegent.utils.routing_impl.litellm_router._build_litellm_router",
            return_value=sentinel,
        ) as mock_build:
            from thegent.utils.routing_impl.litellm_router import get_litellm_router

            r1 = get_litellm_router("cost-based-routing")
            r2 = get_litellm_router("cost-based-routing")

        assert r1 is r2, "Cached instance must be identical on back-to-back calls"
        mock_build.assert_called_once_with("cost-based-routing")

    def test_builder_called_once_within_ttl(self):
        """# @trace WL-070 — _build_litellm_router called exactly once per policy within TTL."""
        self._clear_cache()
        sentinel = MagicMock(name="router_once")

        with patch(
            "thegent.utils.routing_impl.litellm_router._build_litellm_router",
            return_value=sentinel,
        ) as mock_build:
            from thegent.utils.routing_impl.litellm_router import get_litellm_router

            for _ in range(10):
                get_litellm_router("latency-based-routing")

        assert mock_build.call_count == 1, "Builder must not be called more than once within TTL"

    def test_different_policies_get_separate_cache_entries(self):
        """# @trace WL-070 — distinct policy strings produce distinct cached Router instances."""
        self._clear_cache()
        router_a = MagicMock(name="router_a")
        router_b = MagicMock(name="router_b")
        call_count = {"n": 0}

        def fake_build(policy):
            call_count["n"] += 1
            return router_a if policy == "cost-based-routing" else router_b

        with patch(
            "thegent.utils.routing_impl.litellm_router._build_litellm_router",
            side_effect=fake_build,
        ):
            from thegent.utils.routing_impl.litellm_router import get_litellm_router

            r1 = get_litellm_router("cost-based-routing")
            r2 = get_litellm_router("latency-based-routing")
            # Second calls must hit cache
            r3 = get_litellm_router("cost-based-routing")
            r4 = get_litellm_router("latency-based-routing")

        assert r1 is router_a
        assert r2 is router_b
        assert r3 is router_a
        assert r4 is router_b
        assert call_count["n"] == 2, "Builder should be called once per unique policy, not more"

    def test_cache_expiry_triggers_rebuild(self):
        """# @trace WL-070 — after TTL expires the builder is invoked again."""
        self._clear_cache()
        first = MagicMock(name="router_v1")
        second = MagicMock(name="router_v2")
        responses = [first, second]

        with patch(
            "thegent.utils.routing_impl.litellm_router._build_litellm_router",
            side_effect=responses,
        ) as mock_build:
            from thegent.utils.routing_impl.litellm_router import (
                _router_cache,
                get_litellm_router,
            )

            r1 = get_litellm_router("cost-based-routing")
            # Manually expire the cache entry to simulate TTL elapse
            _router_cache.clear()
            r2 = get_litellm_router("cost-based-routing")

        assert r1 is first
        assert r2 is second
        assert mock_build.call_count == 2, "Builder must be called again after cache is cleared/expired"

    def test_thread_safety_single_build_under_concurrency(self):
        """# @trace WL-070 — concurrent goroutines only trigger one build per policy."""
        self._clear_cache()
        build_count = {"n": 0}

        def fake_build(policy):
            build_count["n"] += 1
            return MagicMock(name=f"router_{build_count['n']}")

        with patch(
            "thegent.utils.routing_impl.litellm_router._build_litellm_router",
            side_effect=fake_build,
        ):
            from thegent.utils.routing_impl.litellm_router import get_litellm_router

            results = []

            def worker():
                results.append(get_litellm_router("cost-based-routing"))

            threads = [Thread(target=worker) for _ in range(20)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # All threads must receive the same cached instance
        first_result = results[0]
        assert all(r is first_result for r in results), "All threads must get the same cached Router"
        assert build_count["n"] == 1, "Builder must be called exactly once despite concurrent access"

    def test_build_litellm_router_private_function_exists(self):
        """# @trace WL-070 — _build_litellm_router is a callable private function."""
        from thegent.utils.routing_impl.litellm_router import _build_litellm_router

        assert callable(_build_litellm_router)

    def test_router_cache_module_level_object_has_correct_ttl(self):
        """# @trace WL-070 — _router_cache has TTL of 300 seconds."""
        from thegent.utils.routing_impl.litellm_router import _router_cache

        assert _router_cache.ttl == 300
