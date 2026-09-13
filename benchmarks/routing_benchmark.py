"""Routing layer benchmarks.

Measures cache-hit latency for:
- LiteLLM router TTLCache lookup (FR-OPT-001)
- Cursor API reachability TTLCache lookup (FR-OPT-004)
- Bearer auth settings TTLCache lookup (FR-OPT-005)
- Context window dictionary lookup (FR-OPT-001)

# @trace WL-078
# @trace FR-OPT-001
# @trace FR-OPT-004
# @trace FR-OPT-005
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AUTH_MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "thegent" / "mcp" / "server" / "auth.py"


def _load_auth_module():
    spec = importlib.util.spec_from_file_location("thegent.mcp._server_auth", _AUTH_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load auth module from: {_AUTH_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_auth = _load_auth_module()
BearerAuthMiddleware = _auth.BearerAuthMiddleware


# ---------------------------------------------------------------------------
# FR-OPT-001: LiteLLM router cache lookup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=False)
def _prepopulate_router_cache():
    """Pre-populate router cache with a mock Router so bench hits cache path."""
    from thegent.routing import litellm_router as mod

    sentinel = MagicMock(name="MockRouter")
    mod._router_cache["cost-based-routing"] = sentinel
    yield
    mod._router_cache.clear()


@pytest.mark.requirement("FR-OPT-001")
def bench_router_cache_lookup(benchmark, _prepopulate_router_cache):
    """Benchmark: LiteLLM router TTLCache lookup (cache-hit path). # @trace FR-OPT-001"""
    from thegent.routing.litellm_router import get_litellm_router

    benchmark(get_litellm_router, "cost-based-routing")


@pytest.mark.requirement("FR-OPT-001")
def bench_context_window_lookup_exact(benchmark):
    """Benchmark: MODEL_CONTEXT_WINDOWS dict lookup for a known model. # @trace FR-OPT-001"""
    from thegent.routing.litellm_router import get_context_window

    benchmark(get_context_window, "gpt-4o")


@pytest.mark.requirement("FR-OPT-001")
def bench_context_window_lookup_normalized(benchmark):
    """Benchmark: context window lookup with normalization for unknown model. # @trace FR-OPT-001"""
    from thegent.routing.litellm_router import get_context_window

    benchmark(get_context_window, "GPT-4-Turbo")


# ---------------------------------------------------------------------------
# FR-OPT-004: Cursor API reachability cache lookup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=False)
def _prepopulate_reachability_cache():
    """Pre-populate reachability cache so bench hits the cache path."""
    from thegent.agents import cursor_api_runner as mod

    base_url = "http://localhost:8080"
    token = "bench-token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    cache_key = (base_url, token_hash)
    mod._reachability_cache[cache_key] = True
    yield
    mod._reachability_cache.clear()


@pytest.mark.requirement("FR-OPT-004")
def bench_cursor_reachability_cache_lookup(benchmark, _prepopulate_reachability_cache):
    """Benchmark: cursor reachability TTLCache lookup (cache-hit path). # @trace FR-OPT-004"""
    from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

    benchmark(_is_cursor_api_reachable, "http://localhost:8080", "bench-token")


# ---------------------------------------------------------------------------
# FR-OPT-005: BearerAuth settings cache lookup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=False)
def _prepopulate_bearer_auth_cache():
    """Pre-populate BearerAuthMiddleware._settings so dispatch hits cache."""
    fake_settings = MagicMock()
    fake_settings.mcp_auth_mode = "none"
    BearerAuthMiddleware._settings = fake_settings
    yield
    BearerAuthMiddleware._settings = None


@pytest.mark.requirement("FR-OPT-005")
def bench_bearer_auth_settings_cache_lookup(benchmark, _prepopulate_bearer_auth_cache):
    """Benchmark: BearerAuthMiddleware cached _settings attribute read. # @trace FR-OPT-005"""

    def _read_cached_settings():
        return BearerAuthMiddleware._settings

    benchmark(_read_cached_settings)
