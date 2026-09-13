"""WL-106 top-level CLI passthrough contract checks."""

from __future__ import annotations

import ast
from pathlib import Path


def _function_source(module_text: str, function_name: str) -> str:
    module = ast.parse(module_text)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(module_text, node) or ""
    raise AssertionError(f"Missing function: {function_name}")


def test_main_app_defines_fork_and_rollback_shortcuts() -> None:
    main_path = Path(__file__).resolve().parents[1] / "src" / "thegent" / "cli" / "apps" / "main.py"
    text = main_path.read_text(encoding="utf-8")

    fork_fn = _function_source(text, "fork_top_level")
    rollback_fn = _function_source(text, "rollback_top_level")

    assert '@app.command("fork"' in text
    assert "from thegent.cli.apps.run import run_fork" in fork_fn
    assert "run_fork(session_id=session_id, from_turn=from_turn, new_session_id=new_session_id)" in fork_fn

    assert '@app.command("rollback"' in text
    assert "from thegent.cli.apps.run import run_rollback" in rollback_fn
    assert "run_rollback(session_id=session_id, n_turns=n_turns)" in rollback_fn
