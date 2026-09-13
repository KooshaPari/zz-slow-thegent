"""Contract tests for the extracted ``manage_cliproxy_login`` use_case.

The login module is the new home for the unified ``run_login`` /
``run_login_unified`` flows (plus the ``_LOGIN_FLAGS`` table). These
tests pin the public surface and the cross-module re-export contract via
``thegent.agents.cliproxy_manager`` (the legacy shim).
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

import pytest

from thegent.agents import cliproxy_manager  # noqa: F401

# Import targets — import them here so sys.modules lookup below works
from thegent.use_cases import manage_cliproxy_login  # noqa: F401

# ---------------------------------------------------------------------------
# Module surface
# ---------------------------------------------------------------------------


LOGIN_MODULE = "thegent.use_cases.manage_cliproxy_login"
SHIM_MODULE = "thegent.agents.cliproxy_manager"


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


PUBLIC_NAMES = (
    "run_login",
    "run_login_unified",
    "_LOGIN_FLAGS",
    "_preflight_login",
    "_resolve_factory_key",
    "_open_login_url",
    "_log_instructions",
    "_prompt_for_api_key",
    "_persist_and_restart",
    "_run_oauth_login",
    "_load_config",
)


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------


def test_login_module_imports_cleanly():
    """The login module should import without side effects."""
    mod = sys.modules[LOGIN_MODULE]
    assert mod is not None


@pytest.mark.parametrize("name", PUBLIC_NAMES)
def test_public_symbols_present(name):
    """Every public symbol on the login module must exist."""
    mod = sys.modules[LOGIN_MODULE]
    assert hasattr(mod, name), f"Login module missing {name!r}"


@pytest.mark.parametrize(
    "name", [("run_login",), ("run_login_unified",), ("_LOGIN_FLAGS",)]
)
def test_shim_reexports_login_symbols(name):
    """The legacy shim must re-export every login-flow symbol."""
    shim = sys.modules[SHIM_MODULE]
    assert hasattr(shim, name[0]), f"Shim missing {name[0]!r}"


def test_login_module_under_500_loc():
    """The login module must stay within the L1 size budget."""
    src = Path("src/thegent/use_cases/manage_cliproxy_login.py")
    line_count = sum(1 for _ in src.open())
    assert line_count <= 500, f"manage_cliproxy_login.py is {line_count}L (budget 500)"


def test_login_module_cc_budget():
    """Every function in the login module must be CC ≤ 12."""

    class V(ast.NodeVisitor):
        def __init__(self):
            self.cc = 1

        def visit_If(self, node):
            self.cc += 1
            self.generic_visit(node)

        def visit_For(self, node):
            self.cc += 1
            self.generic_visit(node)

        def visit_While(self, node):
            self.cc += 1
            self.generic_visit(node)

        def visit_Try(self, node):
            self.cc += 1
            self.generic_visit(node)

        def visit_With(self, node):
            self.cc += 1
            self.generic_visit(node)

        def visit_IfExp(self, node):
            self.cc += 1
            self.generic_visit(node)

        def visit_BoolOp(self, node):
            self.cc += len(node.values) - 1
            self.generic_visit(node)

        def visit_comprehension(self, node):
            self.cc += 1
            self.generic_visit(node)

    tree = ast.parse(Path("src/thegent/use_cases/manage_cliproxy_login.py").read_text())
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            v = V()
            v.visit(node)
            if v.cc > 12:
                offenders.append((v.cc, node.lineno, node.name))
    assert not offenders, f"CC > 12: {offenders}"


def test_login_module_function_lengths():
    """Public login functions should stay under the 40-line budget."""
    src = Path("src/thegent/use_cases/manage_cliproxy_login.py")
    tree = ast.parse(src.read_text())
    too_long = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body_lines = node.end_lineno - node.lineno + 1
            if body_lines > 40:
                too_long.append((node.name, body_lines))
    assert not too_long, f"Functions > 40L: {too_long}"


# ---------------------------------------------------------------------------
# Behavioural smoke tests
# ---------------------------------------------------------------------------


def test_login_flags_table_is_complete():
    """Every supported OAuth provider must have a login flag."""
    shim = sys.modules[SHIM_MODULE]
    flags = shim._LOGIN_FLAGS
    assert flags["claude"] == "-claude-login"
    assert flags["codex"] == "-codex-login"
    assert flags["gemini"] == "-login"
    assert flags["kiro"] == "-kiro-login"
    assert "kiro-aws-authcode" in flags
    assert isinstance(flags, dict)
    assert all(isinstance(v, str) and v.startswith("-") for v in flags.values())


def test_run_login_rejects_unknown_provider():
    """``run_login`` must raise ValueError on unknown providers."""
    from thegent.use_cases.manage_cliproxy_login import run_login

    with pytest.raises(ValueError, match="Unknown provider"):
        run_login(None, "totally-fake-provider")


def test_run_login_unified_rejects_unknown_provider():
    """``run_login_unified`` must raise ValueError on unknown providers."""
    from thegent.use_cases.manage_cliproxy_login import run_login_unified

    with pytest.raises(ValueError, match="Unknown provider"):
        run_login_unified(None, "totally-fake-provider")


def test_preflight_login_skips_when_credentials_present():
    """Preflight should return True when the config has credentials."""
    from thegent.use_cases.manage_cliproxy_login import _preflight_login

    config = {
        "openai-compatibility": [
            {"name": "qwen", "api-key-entries": [{"api-key": "sk-test"}]}
        ]
    }
    assert _preflight_login(config, "qwen", skip_if_configured=True) is True
    assert _preflight_login(config, "qwen", skip_if_configured=False) is False


def test_resolve_factory_key_auto_in_skip_mode():
    """In skip mode, factory key is auto-used without prompting."""
    from thegent.use_cases.manage_cliproxy_login import _resolve_factory_key

    calls = []

    def prompt(_):
        calls.append(_)
        return ""

    key, declined = _resolve_factory_key(
        "qwen", "Qwen", "/fake/path", "sk-factory", prompt, skip_if_configured=True
    )
    assert key == "sk-factory"
    assert declined is False
    assert calls == []  # prompt never invoked


def test_resolve_factory_key_yes_in_confirm_mode():
    """In confirm mode, 'yes' returns the factory key."""
    from thegent.use_cases.manage_cliproxy_login import _resolve_factory_key

    def prompt(_):
        return "y"

    key, _ = _resolve_factory_key(
        "qwen", "Qwen", "/fake/path", "sk-factory", prompt, skip_if_configured=False
    )
    assert key == "sk-factory"


def test_resolve_factory_key_no_in_confirm_mode():
    """In confirm mode, 'no' returns None with declined=False."""
    from thegent.use_cases.manage_cliproxy_login import _resolve_factory_key

    def prompt(_):
        return "n"

    key, _ = _resolve_factory_key(
        "qwen", "Qwen", "/fake/path", "sk-factory", prompt, skip_if_configured=False
    )
    assert key is None


def test_log_instructions_no_op_when_empty():
    """Empty instructions → debug-level no-op (no log.info lines)."""
    from thegent.use_cases.manage_cliproxy_login import _log_instructions

    # No assertion — just verify it doesn't raise on empty list
    _log_instructions("Test", [])


def test_prompt_for_api_key_returns_empty_string_on_skip():
    """Pressing Enter returns ``""`` (treated as skip by caller)."""
    from thegent.use_cases.manage_cliproxy_login import _prompt_for_api_key

    def prompt(_):
        return ""

    result = _prompt_for_api_key("qwen", "Qwen", [], "https://example.com", prompt)
    assert result == ""


def test_prompt_for_api_key_returns_key_when_entered():
    """Typed API key is returned verbatim."""
    from thegent.use_cases.manage_cliproxy_login import _prompt_for_api_key

    def prompt(_):
        return "sk-user-typed"

    result = _prompt_for_api_key("qwen", "Qwen", [], "https://example.com", prompt)
    assert result == "sk-user-typed"


def test_open_login_url_no_url_logs_warning():
    """Empty URL → warning, no exception."""
    from thegent.use_cases.manage_cliproxy_login import _open_login_url

    # No assertion — just verify it doesn't raise
    _open_login_url("", "Test")


def test_run_login_signature_unchanged():
    """``run_login`` signature must remain stable (legacy contract)."""
    from thegent.use_cases.manage_cliproxy_login import run_login

    sig = inspect.signature(run_login)
    params = list(sig.parameters)
    assert params[:4] == ["settings", "provider", "prompt_func", "force"]
    assert "login_timeout" in params


def test_run_login_unified_signature_unchanged():
    """``run_login_unified`` signature must remain stable."""
    from thegent.use_cases.manage_cliproxy_login import run_login_unified

    sig = inspect.signature(run_login_unified)
    params = list(sig.parameters)
    assert params[:3] == ["settings", "provider", "prompt_func"]
    assert "skip_if_configured" in params
