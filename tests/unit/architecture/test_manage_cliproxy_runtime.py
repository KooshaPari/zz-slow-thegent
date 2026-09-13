"""Contract tests for the extracted ``manage_cliproxy_runtime`` use_case.

The runtime module is the new home for process management primitives
(resolve_binary, is_proxy_reachable, ensure_proxy_running, etc.). These
tests pin the public surface and the cross-module re-export contract via
``thegent.agents.cliproxy_manager`` (the legacy shim).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import targets
# ---------------------------------------------------------------------------


RUNTIME_MODULE = "thegent.use_cases.manage_cliproxy_runtime"
SHIM_MODULE = "thegent.agents.cliproxy_manager"


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


PUBLIC_FUNCTIONS = (
    "resolve_binary",
    "binary_available",
    "is_proxy_reachable",
    "is_adapter_running",
    "adapter_script_path",
    "is_adapter_fallback_allowed",
    "_start_raw_proxy",
    "_start_proxy_and_wait",
    "ensure_proxy_running",
    "start_proxy_managed",
    "kill_proxy",
    "_resolve_binary",
    "_binary_available",
    "_is_proxy_reachable",
    "_is_adapter_running",
    "_adapter_script_path",
    "_is_adapter_fallback_allowed",
)


def test_runtime_module_imports_clean() -> None:
    """The runtime module must import without side effects."""
    import importlib

    module = importlib.import_module(RUNTIME_MODULE)
    assert module.__file__ is not None
    # Must end in .py
    assert module.__file__.endswith(".py")


@pytest.mark.parametrize("symbol", PUBLIC_FUNCTIONS)
def test_runtime_exposes_public_symbols(symbol: str) -> None:
    """Every documented symbol must be importable from the runtime module."""
    import importlib

    module = importlib.import_module(RUNTIME_MODULE)
    assert hasattr(module, symbol), f"{RUNTIME_MODULE}.{symbol} is missing"
    assert callable(getattr(module, symbol)), f"{RUNTIME_MODULE}.{symbol} is not callable"


def test_runtime_underscore_aliases_match_public() -> None:
    """Underscore-prefixed aliases must reference the public functions (same identity)."""
    import importlib

    module = importlib.import_module(RUNTIME_MODULE)
    aliases = {
        "_resolve_binary": "resolve_binary",
        "_binary_available": "binary_available",
        "_is_proxy_reachable": "is_proxy_reachable",
        "_is_adapter_running": "is_adapter_running",
        "_adapter_script_path": "adapter_script_path",
        "_is_adapter_fallback_allowed": "is_adapter_fallback_allowed",
    }
    for alias, public in aliases.items():
        assert getattr(module, alias) is getattr(module, public), (
            f"{alias} must be the same function object as {public}"
        )


# ---------------------------------------------------------------------------
# Shim re-export contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("symbol", PUBLIC_FUNCTIONS)
def test_shim_reexports_runtime_symbols(symbol: str) -> None:
    """The legacy ``cliproxy_manager`` shim must re-export every runtime symbol."""
    import importlib

    shim = importlib.import_module(SHIM_MODULE)
    runtime = importlib.import_module(RUNTIME_MODULE)
    assert hasattr(shim, symbol), f"{SHIM_MODULE}.{symbol} is missing"
    # Underscore aliases are direct references; public names must match too.
    assert getattr(shim, symbol) is getattr(runtime, symbol), (
        f"{SHIM_MODULE}.{symbol} must re-export {RUNTIME_MODULE}.{symbol}"
    )


def test_shim_docstring_announces_deprecation() -> None:
    """The shim must carry a DEPRECATED docstring block."""
    import importlib

    shim = importlib.import_module(SHIM_MODULE)
    assert shim.__doc__ is not None
    assert "DEPRECATED" in shim.__doc__
    assert "manage_cliproxy_runtime" in shim.__doc__


# ---------------------------------------------------------------------------
# Behavioural smoke tests
# ---------------------------------------------------------------------------


def test_binary_available_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """binary_available('python') must succeed when the binary is on PATH."""
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    # Find a real binary
    real = sys.executable
    real_name = Path(real).name  # e.g. 'python3.11'
    assert runtime.binary_available(real_name) is True


def test_binary_available_missing(tmp_path: Path) -> None:
    """binary_available('definitely-not-a-binary-xyz') must return False."""
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    assert runtime.binary_available("definitely-not-a-binary-xyz-9999") is False


def test_resolve_binary_falls_back_to_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """resolve_binary must return settings.cliproxy_binary when on PATH."""
    import importlib
    import types

    runtime = importlib.import_module(RUNTIME_MODULE)
    # Build a fake settings object that knows its binary name and behaves
    # like a ThegentSettings — only .cliproxy_binary is needed by resolve_binary.
    fake_settings = types.SimpleNamespace(cliproxy_binary="cliproxy")
    result = runtime.resolve_binary(fake_settings)  # type: ignore[arg-type]
    assert result == "cliproxy"


def test_is_proxy_reachable_returns_false_for_unbound_port() -> None:
    """An unbound local port must be reported as not-reachable."""
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    # Port 1 is reserved and almost never bound; if it is, the test still
    # produces a meaningful result either way.
    assert runtime.is_proxy_reachable("http://127.0.0.1:1/v1") is False


def test_is_adapter_running_returns_false_for_unbound_port() -> None:
    """is_adapter_running must not crash on unreachable base URLs."""
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    assert runtime.is_adapter_running("http://127.0.0.1:1/v1") is False


def test_adapter_script_path_returns_path_or_none() -> None:
    """adapter_script_path must return Path | None without raising."""
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    result = runtime.adapter_script_path()
    assert result is None or isinstance(result, Path)


def test_is_adapter_fallback_allowed_returns_bool() -> None:
    """is_adapter_fallback_allowed must return a real boolean."""
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    result = runtime.is_adapter_fallback_allowed()
    assert isinstance(result, bool)


def test_kill_proxy_handles_unbound_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """kill_proxy must return False (no-op) when no process listens on the port."""
    import importlib
    import types

    runtime = importlib.import_module(RUNTIME_MODULE)
    fake_settings = types.SimpleNamespace(cliproxy_port=1)
    # Port 1 is reserved; lsof returns nothing.
    assert runtime.kill_proxy(fake_settings) is False  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Cyclomatic complexity (≤ 15 per function)
# ---------------------------------------------------------------------------


def test_all_functions_under_complexity_threshold() -> None:
    """No function in the runtime module may exceed CC=15 (project rule)."""
    import ast
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    source_path = Path(runtime.__file__)
    if source_path is None or not str(source_path).endswith(".py"):
        pytest.skip("Runtime module has no .py source")
    tree = ast.parse(source_path.read_text())

    class V(ast.NodeVisitor):
        def __init__(self) -> None:
            self.cc = 1

        def visit_If(self, node: ast.If) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_For(self, node: ast.For) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_While(self, node: ast.While) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_Try(self, node: ast.Try) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_With(self, node: ast.With) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_IfExp(self, node: ast.IfExp) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_comprehension(self, node: ast.comprehension) -> None:
            self.cc += 1
            self.generic_visit(node)

    offenders: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            v = V()
            v.visit(node)
            if v.cc > 15:
                offenders.append((node.name, v.cc, f"{source_path}:{node.lineno}"))
    assert offenders == [], f"Functions exceed CC=15: {offenders}. Project rule is CC ≤ 15."


# ---------------------------------------------------------------------------
# Module size
# ---------------------------------------------------------------------------


def test_runtime_module_size_within_budget() -> None:
    """Runtime module must be ≤ 500 LOC (project file-size rule)."""
    import importlib

    runtime = importlib.import_module(RUNTIME_MODULE)
    source_path = Path(str(runtime.__file__))
    line_count = sum(1 for _ in source_path.read_text().splitlines())
    assert line_count <= 500, f"Runtime module is {line_count} LOC; budget is 500. Split further."


# ---------------------------------------------------------------------------
# Provider alias patchers (WP-Y16 compat)
# ---------------------------------------------------------------------------


def test_alias_patchers_split_per_provider() -> None:
    """Each provider gets a dedicated patcher; coordinator dispatches via table."""
    shim = sys.modules[SHIM_MODULE]
    expected = {
        "_patch_minimax_provider",
        "_patch_glm_provider",
        "_patch_kilo_provider",
        "_patch_roo_provider",
        "_resolve_claude_aliases",
        "_PROVIDER_PATCHERS",
        "_patch_provider_aliases",
    }
    missing = expected - set(dir(shim))
    assert missing == set(), f"Alias-patcher helpers missing on shim: {missing}"


def test_alias_patcher_table_dispatches_per_provider() -> None:
    """The dispatcher table covers exactly the four known providers."""
    shim = sys.modules[SHIM_MODULE]
    table = shim._PROVIDER_PATCHERS
    assert set(table.keys()) == {"minimax", "glm", "kilo", "roo"}
    assert table["minimax"] is shim._patch_minimax_provider
    assert table["glm"] is shim._patch_glm_provider
    assert table["kilo"] is shim._patch_kilo_provider
    assert table["roo"] is shim._patch_roo_provider


def test_minimax_patcher_rewrites_host() -> None:
    """minimax.chat → minimax.io host rewrite for WP-Y16."""
    shim = sys.modules[SHIM_MODULE]
    p = {"name": "minimax", "base-url": "https://api.minimax.chat/v1"}
    shim._patch_minimax_provider(p)
    assert p["base-url"] == "https://api.minimax.io/v1"
    aliases = {m["alias"] for m in p["models"]}
    assert "minimax-m2.5" in aliases


def test_glm_patcher_registers_aliases() -> None:
    """GLM-5 gets the canonical + lowercase aliases for WP-Y16."""
    shim = sys.modules[SHIM_MODULE]
    p = {"name": "glm", "models": []}
    shim._patch_glm_provider(p)
    aliases = {m["alias"] for m in p["models"]}
    assert {"GLM-5", "glm-5", "z-ai/glm-5"} <= aliases


def test_kilo_and_roo_patchers_register_default_alias() -> None:
    """kilo/roo get a single default alias when none is present."""
    shim = sys.modules[SHIM_MODULE]
    kilo = {"name": "kilo", "model": "kilo-1", "models": []}
    shim._patch_kilo_provider(kilo)
    assert any(m["alias"] == "kilo-default" for m in kilo["models"])

    roo = {"name": "roo", "models": []}
    shim._patch_roo_provider(roo)
    assert any(m["alias"] == "roo-default" for m in roo["models"])


def test_alias_patchers_are_idempotent() -> None:
    """Re-applying a patcher is a no-op when the alias already exists."""
    shim = sys.modules[SHIM_MODULE]
    p = {"name": "glm", "models": [{"name": "GLM-5", "alias": "GLM-5"}]}
    shim._patch_glm_provider(p)
    names = [m["alias"] for m in p["models"]]
    assert names.count("GLM-5") == 1


def test_coordinator_skips_non_list_and_non_dict() -> None:
    """Coordinator no-ops when ``openai-compatibility`` is absent or malformed."""
    shim = sys.modules[SHIM_MODULE]
    # No openai-compatibility key
    shim._patch_provider_aliases({})
    # Wrong type
    shim._patch_provider_aliases({"openai-compatibility": "nope"})
    # Mixed-type list — skip non-dict entries but do not raise
    shim._patch_provider_aliases({"openai-compatibility": ["bad", 1, None]})


def test_coordinator_skips_unknown_providers() -> None:
    """Unknown provider names flow through ``_resolve_claude_aliases`` only."""
    shim = sys.modules[SHIM_MODULE]
    cfg = {
        "openai-compatibility": [
            {"name": "unknown", "model": "claude-opus-4-6", "models": []},
        ]
    }
    shim._patch_provider_aliases(cfg)
    providers = cfg["openai-compatibility"]
    assert providers[0]["models"]  # populated via _get_claude_aliases


def test_cliproxy_manager_patchers_under_cc_threshold() -> None:
    """All _patch_* helpers on the shim must be CC ≤ 15."""
    import ast

    shim = sys.modules[SHIM_MODULE]
    source_path = Path(str(shim.__file__))
    tree = ast.parse(source_path.read_text())

    class V(ast.NodeVisitor):
        def __init__(self) -> None:
            self.cc = 1

        def visit_If(self, node: ast.If) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_For(self, node: ast.For) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_While(self, node: ast.While) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_Try(self, node: ast.Try) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_With(self, node: ast.With) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_IfExp(self, node: ast.IfExp) -> None:
            self.cc += 1
            self.generic_visit(node)

        def visit_comprehension(self, node: ast.comprehension) -> None:
            self.cc += 1
            self.generic_visit(node)

    targets = {
        "_patch_provider_aliases",
        "_patch_minimax_provider",
        "_patch_glm_provider",
        "_patch_kilo_provider",
        "_patch_roo_provider",
        "_resolve_claude_aliases",
    }
    offenders: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in targets:
            v = V()
            v.visit(node)
            if v.cc > 15:
                offenders.append((node.name, v.cc, f"{source_path}:{node.lineno}"))
    assert offenders == [], f"Alias-patch helpers exceed CC=15: {offenders}"
