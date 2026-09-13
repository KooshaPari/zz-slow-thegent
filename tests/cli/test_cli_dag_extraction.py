"""Tests validating dag command extraction from cli.py into cli_dag.py.

B90-W2-A1 — WL-120: First cli.py extraction (dag command group).
"""
# @trace WL-120 B90-W2-A1

from __future__ import annotations

import importlib
import types

# --- A1: Module import check ---


def test_cli_dag_module_imports_cleanly() -> None:
    """cli_dag module must import without errors."""
    mod = importlib.import_module("thegent.cli.commands.cli_dag")
    assert isinstance(mod, types.ModuleType)


# --- A1: Each extracted function exists in cli_dag ---

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


def test_all_dag_cmd_functions_exist_in_cli_dag() -> None:
    """Each extracted dag_*_cmd function must exist in cli_dag."""
    import thegent.cli.commands.cli_dag as dag_mod

    for fn_name in DAG_CMD_FUNCTIONS:
        assert hasattr(dag_mod, fn_name), f"Missing function in cli_dag: {fn_name}"
        assert callable(getattr(dag_mod, fn_name)), f"Not callable: {fn_name}"


def test_dag_cmd_functions_are_callable() -> None:
    """All dag command functions must be callable objects."""
    import thegent.cli.commands.cli_dag as dag_mod

    for fn_name in DAG_CMD_FUNCTIONS:
        fn = getattr(dag_mod, fn_name)
        assert callable(fn), f"Expected callable for {fn_name}"


def test_terminal_statuses_constant_exists() -> None:
    """TERMINAL_STATUSES constant must be present in cli_dag."""
    import thegent.cli.commands.cli_dag as dag_mod

    assert hasattr(dag_mod, "TERMINAL_STATUSES")
    assert isinstance(dag_mod.TERMINAL_STATUSES, frozenset)
    assert "done" in dag_mod.TERMINAL_STATUSES
    assert "cancelled" in dag_mod.TERMINAL_STATUSES
    assert "skipped" in dag_mod.TERMINAL_STATUSES


# --- A1: __all__ re-export check ---


def test_cli_dag_exports_all_dag_cmd_names() -> None:
    """cli_dag.__all__ must include all dag command function names."""
    import thegent.cli.commands.cli_dag as dag_mod

    assert hasattr(dag_mod, "__all__")
    for fn_name in DAG_CMD_FUNCTIONS:
        assert fn_name in dag_mod.__all__, f"Missing from __all__: {fn_name}"


# --- A1: Import re-export test - cli.py still routes correctly ---


def test_cli_dag_functions_reachable_via_original_cli_module() -> None:
    """Functions exist in cli_dag AND cli.py still has dag_*_cmd via its own definitions."""
    import thegent.cli.commands.cli as cli_mod
    import thegent.cli.commands.cli_dag as dag_mod

    # cli_dag functions must be callable and present
    for fn_name in DAG_CMD_FUNCTIONS:
        dag_fn = getattr(dag_mod, fn_name)
        assert callable(dag_fn), f"cli_dag.{fn_name} not callable"

        # cli.py still defines these functions (original source remains)
        cli_fn = getattr(cli_mod, fn_name, None)
        assert cli_fn is not None, f"cli.{fn_name} no longer present after extraction"
        assert callable(cli_fn), f"cli.{fn_name} not callable"


def test_dag_cmd_function_signatures_have_correct_defaults() -> None:
    """dag_validate_cmd, dag_list_cmd must accept cd kwarg with None default."""
    import inspect

    import thegent.cli.commands.cli_dag as dag_mod

    sig_validate = inspect.signature(dag_mod.dag_validate_cmd)
    assert "cd" in sig_validate.parameters
    assert sig_validate.parameters["cd"].default is None

    sig_list = inspect.signature(dag_mod.dag_list_cmd)
    assert "cd" in sig_list.parameters
    assert sig_list.parameters["cd"].default is None
    assert "format" in sig_list.parameters

    sig_add = inspect.signature(dag_mod.dag_add_cmd)
    assert "task_id" in sig_add.parameters
    assert "agent" in sig_add.parameters
    assert "prompt" in sig_add.parameters

    sig_recover = inspect.signature(dag_mod.dag_recover_cmd)
    assert "action" in sig_recover.parameters
    assert sig_recover.parameters["action"].default == "retry-failed"
