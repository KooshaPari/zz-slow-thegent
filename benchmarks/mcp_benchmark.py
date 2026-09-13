"""MCP tool dispatch benchmarks.

Measures:
- ThegentSettings construction (pydantic-settings parse from env)
- BearerAuthMiddleware settings cache read (class-level attribute)

# @trace WL-078
# @trace FR-OPT-002
# @trace FR-OPT-005
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

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


@pytest.mark.requirement("FR-OPT-002")
def bench_thegent_settings_construction(benchmark):
    """Benchmark: ThegentSettings() construction (pydantic-settings env parse). # @trace FR-OPT-002"""
    from thegent.config import ThegentSettings

    benchmark(ThegentSettings)


@pytest.mark.requirement("FR-OPT-002")
def bench_bearer_auth_cached_settings_read(benchmark):
    """Benchmark: BearerAuthMiddleware cached settings attribute access. # @trace FR-OPT-002"""
    fake_settings = MagicMock()
    fake_settings.mcp_auth_mode = "none"
    BearerAuthMiddleware._settings = fake_settings

    def _read():
        return BearerAuthMiddleware._settings

    benchmark(_read)
    BearerAuthMiddleware._settings = None
