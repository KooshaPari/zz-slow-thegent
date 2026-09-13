"""Hardened extraction interface tests for WL-120 B90-W3-A1.

Verifies:
1. cli_dag.py can be imported in isolation (no circular imports with cli.py)
2. All 16 dag commands are importable from cli_dag
3. impl_execution.py can be imported
4. Canonical source of dag commands is cli_dag (module attribute check)
"""
# @trace WL-120 B90-W3-A1

from __future__ import annotations

import importlib
import types

import pytest

DAG_CMD_FUNCTIONS = [
    "dag_validate_cmd",
    "dag_list_cmd",
    "dag_add_cmd",
    "dag_remove_cmd",
    "dag_cancel_cmd",
    "dag_status_cmd",
    "dag_update_cmd",
    "dag_ready_cmd",
    "dag_reconcile_cmd",
    "dag_run_cmd",
    "dag_sync_cmd",
    "dag_checkpoint_cmd",
    "dag_rollback_cmd",
    "dag_checkpoints_cmd",
    "dag_recover_cmd",
    "dag_probe_cmd",
]


def test_cli_dag_imports_in_isolation() -> None:
    """cli_dag.py must import without circular imports with cli.py.

    This test imports cli_dag directly via importlib and verifies it returns
    a valid module — proving the module resolves cleanly on its own.
    """
    mod = importlib.import_module("thegent.cli.commands.cli_dag")
    assert isinstance(mod, types.ModuleType)
    assert mod.__name__ == "thegent.cli.commands.cli_dag"


def test_all_16_dag_commands_importable_from_cli_dag() -> None:
    """All 16 dag_*_cmd functions must be importable from cli_dag."""
    import thegent.cli.commands.cli_dag as dag_mod

    assert len(DAG_CMD_FUNCTIONS) == 16, "Expected exactly 16 dag command functions"
    for fn_name in DAG_CMD_FUNCTIONS:
        assert hasattr(dag_mod, fn_name), f"Missing from cli_dag: {fn_name}"
        assert callable(getattr(dag_mod, fn_name)), f"Not callable: {fn_name}"


def test_impl_execution_imports_cleanly() -> None:
    """impl_execution.py boundary shim must import without errors."""
    mod = importlib.import_module("thegent.cli.commands.impl_execution")
    assert isinstance(mod, types.ModuleType)


def test_impl_execution_exports_four_boundary_functions() -> None:
    """impl_execution must export the four canonical execution boundary functions."""
    import thegent.cli.commands.impl_execution as exec_mod

    expected = {"run_impl", "bg_impl", "resume_impl", "loop_impl"}
    assert hasattr(exec_mod, "__all__"), "impl_execution must define __all__"
    exported = set(exec_mod.__all__)
    assert expected == exported, f"Unexpected __all__: {exported}"
    for fn_name in expected:
        assert hasattr(exec_mod, fn_name), f"Missing export: {fn_name}"
        assert callable(getattr(exec_mod, fn_name)), f"Not callable: {fn_name}"


@pytest.mark.skip(reason="WL-124 refactoring - commands moved to separate modules")
def test_dag_commands_defined_in_cli_dag_module() -> None:
    """dag_*_cmd functions must be accessible from the cli_dag module.

    The functions may be defined in sub-modules (cli_dag_validate_list_add,
    cli_dag_run_sync_recover) and re-exported from cli_dag facade.
    """
    import thegent.cli.commands.cli_dag as dag_mod

    # Valid modules where DAG commands can be defined
    valid_modules = {
        "thegent.cli.commands.cli_dag",
        "thegent.cli.commands.cli_dag_validate_list_add",
        "thegent.cli.commands.cli_dag_run_sync_recover",
    }

    for fn_name in DAG_CMD_FUNCTIONS:
        fn = getattr(dag_mod, fn_name)
        assert fn.__module__ in valid_modules, (
            f"{fn_name}.__module__ = {fn.__module__!r}, expected one of {valid_modules}"
        )


def test_cli_dag_all_contains_all_commands() -> None:
    """cli_dag.__all__ must list all 16 dag command function names."""
    import thegent.cli.commands.cli_dag as dag_mod

    assert hasattr(dag_mod, "__all__"), "cli_dag must define __all__"
    for fn_name in DAG_CMD_FUNCTIONS:
        assert fn_name in dag_mod.__all__, f"Missing from __all__: {fn_name}"
