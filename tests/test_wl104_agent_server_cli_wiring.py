"""WL-104 CLI wiring contract for `thegent agent-server` command."""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from thegent.cli.apps.main import app as main_app


def _function_source(module_text: str, function_name: str) -> str:
    module = ast.parse(module_text)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(module_text, node) or ""
    raise AssertionError(f"Missing function: {function_name}")


def test_main_app_defines_agent_server_command_passthrough() -> None:
    main_path = Path(__file__).resolve().parents[1] / "src" / "thegent" / "cli" / "apps" / "main.py"
    text = main_path.read_text(encoding="utf-8")
    fn_src = _function_source(text, "agent_server_cmd")

    assert '@app.command("agent-server"' in text
    assert "from thegent.protocols.jsonrpc_agent_server import serve_stdio" in fn_src
    assert "raise typer.Exit(serve_stdio())" in fn_src


def test_agent_server_command_uses_serve_stdio_exit_code(monkeypatch) -> None:
    calls: list[object] = []

    def _fake_serve_stdio() -> int:
        calls.append(object())
        return 7

    from thegent.protocols import jsonrpc_agent_server

    monkeypatch.setattr(jsonrpc_agent_server, "serve_stdio", _fake_serve_stdio)
    result = CliRunner().invoke(main_app, ["agent-server"])
    assert result.exit_code == 7
    assert len(calls) == 1
