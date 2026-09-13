"""Tests validating impl_execution extraction boundary (WL-120 B90-W2-A2).

Validates:
- impl_execution module imports cleanly
- Each target function exists and is callable in impl_execution
- impl.py still exports the same names (re-export parity test)
"""
# @trace WL-120 B90-W2-A2

from __future__ import annotations

import importlib
import inspect
import types

EXECUTION_FUNCTIONS = [
    "run_impl",
    "bg_impl",
    "resume_impl",
    "loop_impl",
]


def test_impl_execution_module_imports_cleanly() -> None:
    """impl_execution module must import without errors."""
    mod = importlib.import_module("thegent.cli.commands.impl_execution")
    assert isinstance(mod, types.ModuleType)


def test_all_execution_functions_exist_in_impl_execution() -> None:
    """Each extracted function must exist in impl_execution."""
    import thegent.cli.commands.impl_execution as exec_mod

    for fn_name in EXECUTION_FUNCTIONS:
        assert hasattr(exec_mod, fn_name), f"Missing in impl_execution: {fn_name}"
        assert callable(getattr(exec_mod, fn_name)), f"Not callable: {fn_name}"


def test_impl_execution_all_exports_complete() -> None:
    """impl_execution.__all__ must list all execution function names."""
    import thegent.cli.commands.impl_execution as exec_mod

    assert hasattr(exec_mod, "__all__")
    for fn_name in EXECUTION_FUNCTIONS:
        assert fn_name in exec_mod.__all__, f"Missing from __all__: {fn_name}"


def test_impl_py_still_exports_same_names() -> None:
    """impl.py must still export run_impl, bg_impl, resume_impl, loop_impl (backward compat)."""
    import thegent.cli.commands.impl as impl_mod

    for fn_name in EXECUTION_FUNCTIONS:
        assert hasattr(impl_mod, fn_name), f"impl.py lost: {fn_name}"
        assert callable(getattr(impl_mod, fn_name)), f"impl.py {fn_name} not callable"


def test_impl_execution_functions_are_same_objects_as_impl() -> None:
    """impl_execution exports must reference the same objects as impl (re-export identity)."""
    import thegent.cli.commands.impl as impl_mod
    import thegent.cli.commands.impl_execution as exec_mod

    for fn_name in EXECUTION_FUNCTIONS:
        exec_fn = getattr(exec_mod, fn_name)
        impl_fn = getattr(impl_mod, fn_name)
        assert exec_fn is impl_fn, (
            f"impl_execution.{fn_name} is not the same object as impl.{fn_name}. "
            "impl_execution must re-export from impl, not redefine."
        )


def test_run_impl_signature_intact() -> None:
    """run_impl must accept prompt, audio_files, google_grounding and pass rest through **kwargs."""
    import thegent.cli.commands.impl_execution as exec_mod

    sig = inspect.signature(exec_mod.run_impl)
    # Explicit named params (pinned by tests/test_wl116_audio_inputs.py).
    for param in ("prompt", "audio_files", "google_grounding"):
        assert param in sig.parameters, f"run_impl missing explicit param: {param}"
    # agent, cd, model arrive through **kwargs.
    assert any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()), (
        "run_impl must accept **kwargs for agent/cd/model forwarding"
    )


def test_bg_impl_signature_intact() -> None:
    """bg_impl must have expected key parameters (agent, prompt, cd, timeout)."""
    import thegent.cli.commands.impl_execution as exec_mod

    sig = inspect.signature(exec_mod.bg_impl)
    for param in ("agent", "prompt", "cd", "timeout"):
        assert param in sig.parameters, f"bg_impl missing param: {param}"


def test_resume_impl_signature_intact() -> None:
    """resume_impl must have session_id, prompt parameters."""
    import thegent.cli.commands.impl_execution as exec_mod

    sig = inspect.signature(exec_mod.resume_impl)
    for param in ("session_id", "prompt"):
        assert param in sig.parameters, f"resume_impl missing param: {param}"


def test_loop_impl_signature_intact() -> None:
    """loop_impl must have agent, prompt, cd parameters."""
    import thegent.cli.commands.impl_execution as exec_mod

    sig = inspect.signature(exec_mod.loop_impl)
    for param in ("agent", "prompt", "cd"):
        assert param in sig.parameters, f"loop_impl missing param: {param}"
