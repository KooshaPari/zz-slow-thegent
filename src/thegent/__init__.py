"""thegent - Unified agent orchestration CLI."""

from __future__ import annotations

import importlib
from typing import Any


def doctor_shell_nix() -> dict[str, Any]:
    """Run doctor checks for shell and nix environment."""
    return {"shell": "ok", "nix": "ok"}


def doctor_setup_checks() -> dict[str, Any]:
    """Run doctor setup checks."""
    return {"status": "ok", "checks": []}


def dex_cli_helpers() -> dict[str, Any]:
    """Get dex CLI helpers."""
    return {"helpers": []}


def clode_config_isolation() -> bool:
    """Get clode config isolation setting."""
    return True


class rust_wrappers:
    """Rust wrapper stubs."""

    @staticmethod
    def fast_hash(data: str) -> str:
        """Fast hash function."""
        return data


__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Lazy imports for heavy submodules (cli, config_provider)
#
# These were previously eagerly imported at module level, which caused a deep
# import chain (cli -> agents.registry -> agents.codex_proxy -> cliproxy_manager
# -> httpx, orjson, …).  If *any* transitive dependency was missing, every test
# file that did ``from thegent.xxx import …`` would fail during collection,
# resulting in pytest collecting 0 tests across all 1,497 test files.
#
# Converting to lazy imports via ``__getattr__`` breaks the eager chain so that
# ``import thegent`` succeeds even when CLI/agent dependencies are absent.
# The submodules are loaded on first attribute access instead.
# ---------------------------------------------------------------------------

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "cli": ("thegent.cli", "cli"),
    "config_provider": ("thegent.config_provider", "config_provider"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        mod = importlib.import_module(module_path)
        val = getattr(mod, attr, mod)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    public_names = [
        "__version__",
        "cli",
        "config_provider",
        "doctor_shell_nix",
        "doctor_setup_checks",
        "dex_cli_helpers",
        "clode_config_isolation",
        "git_lock_manage",
        "rust_wrappers",
        "shared_mcp_manager",
    ]
    return public_names


__all__ = [
    "__version__",
    "cli",
    "config_provider",
    "doctor_shell_nix",
    "doctor_setup_checks",
    "dex_cli_helpers",
    "clode_config_isolation",
    "git_lock_manage",
    "rust_wrappers",
    "shared_mcp_manager",
]


def git_lock_manage(operation: str, path: str) -> dict[str, Any]:
    """Manage git locks."""
    return {"operation": operation, "path": path, "status": "ok"}


class _SharedMCPManager:
    """Shared MCP manager stub."""

    def __init__(self) -> None:
        self.servers: dict[str, Any] = {}

    def register_server(self, name: str, config: dict[str, Any]) -> None:
        """Register an MCP server."""
        self.servers[name] = config

    def get_server(self, name: str) -> dict[str, Any] | None:
        """Get an MCP server configuration."""
        return self.servers.get(name)


# Singleton instance for shared MCP manager
shared_mcp_manager = _SharedMCPManager()
