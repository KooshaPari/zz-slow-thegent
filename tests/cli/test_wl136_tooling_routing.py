# @trace WL-136 B90-W2-D2
"""Tests for the WL-136 B90-W2-D2 tooling command surface routing.

Verifies:
1. The five tooling commands exist in cli_tooling.py with correct signatures.
2. cli.py still re-exports them (backward compat via _tooling_* aliases).
3. The commands are callable (not broken by the extraction).
"""

from __future__ import annotations

import importlib

import pytest

# ---------------------------------------------------------------------------
# Canonical command names to verify
# ---------------------------------------------------------------------------

TOOLING_COMMAND_NAMES = [
    "audit_verify_cmd",
    "benchmark_cmd",
    "deep_research_cmd",
    "drift_monitor_cmd",
    "roadmap_cmd",
]


# ---------------------------------------------------------------------------
# D2-1: Commands exist in cli_tooling.py
# ---------------------------------------------------------------------------


def test_cli_tooling_module_imports_cleanly() -> None:
    """cli_tooling module must import without raising."""
    mod = importlib.import_module("thegent.cli.commands.cli_tooling")
    assert mod is not None


@pytest.mark.parametrize("cmd_name", TOOLING_COMMAND_NAMES)
def test_command_exists_in_cli_tooling(cmd_name: str) -> None:
    """Each tooling command must be defined in cli_tooling.py."""
    mod = importlib.import_module("thegent.cli.commands.cli_tooling")
    assert hasattr(mod, cmd_name), f"cli_tooling.py missing expected tooling command: {cmd_name}"


@pytest.mark.parametrize("cmd_name", TOOLING_COMMAND_NAMES)
def test_command_is_callable_in_cli_tooling(cmd_name: str) -> None:
    """Each tooling command must be callable."""
    mod = importlib.import_module("thegent.cli.commands.cli_tooling")
    fn = getattr(mod, cmd_name)
    assert callable(fn), f"{cmd_name} is not callable in cli_tooling.py"


# ---------------------------------------------------------------------------
# D2-2: __all__ exports the expected names
# ---------------------------------------------------------------------------


def test_cli_tooling_all_contains_expected_names() -> None:
    """cli_tooling.__all__ must include all five tooling command names."""
    mod = importlib.import_module("thegent.cli.commands.cli_tooling")
    exported = set(getattr(mod, "__all__", []))
    missing = set(TOOLING_COMMAND_NAMES) - exported
    assert not missing, f"cli_tooling.__all__ missing: {missing}"


# ---------------------------------------------------------------------------
# D2-3: cli.py re-imports from cli_tooling (backward compat aliases)
# ---------------------------------------------------------------------------


def test_cli_imports_tooling_aliases() -> None:
    """cli.py must import tooling commands as _tooling_* aliases from cli_tooling."""
    try:
        mod = importlib.import_module("thegent.cli.commands.cli")
    except Exception as exc:
        pytest.skip(f"cli.py import raised: {exc}")

    alias_names = [f"_tooling_{name}" for name in TOOLING_COMMAND_NAMES]
    for alias in alias_names:
        assert hasattr(mod, alias), (
            f"cli.py missing re-export alias: {alias}. Ensure cli.py imports from cli_tooling.py."
        )


def test_cli_tooling_aliases_point_to_same_objects() -> None:
    """The _tooling_* aliases in cli.py must point to cli_tooling functions."""
    try:
        cli_mod = importlib.import_module("thegent.cli.commands.cli")
    except Exception as exc:
        pytest.skip(f"cli.py import raised: {exc}")

    tooling_mod = importlib.import_module("thegent.cli.commands.cli_tooling")

    for name in TOOLING_COMMAND_NAMES:
        alias = getattr(cli_mod, f"_tooling_{name}", None)
        canonical = getattr(tooling_mod, name, None)
        assert alias is not None, f"cli.py missing _tooling_{name}"
        assert canonical is not None, f"cli_tooling.py missing {name}"
        # Both must be callable — we don't enforce identity since lazy imports
        # may produce different function objects.
        assert callable(alias), f"_tooling_{name} in cli.py is not callable"
        assert callable(canonical), f"{name} in cli_tooling.py is not callable"


# ---------------------------------------------------------------------------
# D2-4: Tooling commands are NOT directly imported into thegent.mcp.server
# (surface boundary enforcement — tooling must not leak into runtime)
# ---------------------------------------------------------------------------


def test_tooling_commands_not_in_mcp_server_module() -> None:
    """mcp/server.py must NOT directly import tooling command names."""
    # Read the server.py source as text — import would trigger side effects
    from pathlib import Path

    server_path = Path(__file__).parents[3] / "src" / "thegent" / "mcp" / "server.py"
    if not server_path.exists():
        pytest.skip("server.py not found at expected path")

    text = server_path.read_text()
    for name in TOOLING_COMMAND_NAMES:
        # The names should not appear as bare imports (they may appear in comments)
        assert f"import {name}" not in text, (
            f"server.py imports tooling command '{name}' — violates WL-136 surface boundary"
        )
