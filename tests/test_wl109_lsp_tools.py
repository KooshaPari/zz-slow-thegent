"""WL-109: Tests for MCP LSP tool implementations.

Covers the three MCP-exposed LSP tools backed by SharedLspManager/lsp_tools:
  - lsp_diagnostics_impl  -> thegent_lsp_diagnostics
  - lsp_symbol_lookup_impl -> thegent_lsp_symbol_lookup
  - lsp_hover_impl        -> thegent_lsp_hover

All tests mock the LspToolAdapter so no real LSP server process is required.

# @trace WL-109
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from thegent.mcp.lsp_tools import (
    Diagnostic,
    HoverInfo,
    SymbolInfo,
    _ensure_position,
    _validate_existing_file,
    lsp_diagnostics,
    lsp_diagnostics_impl,
    lsp_hover_impl,
    lsp_symbol_lookup,
    lsp_symbol_lookup_impl,
)
from thegent.mcp.server import _server_tools_workstream_lsp

# ---------------------------------------------------------------------------
# Fake LSP adapters
# ---------------------------------------------------------------------------


class _FakeAdapter:
    """Fake LSP adapter implementing the LspToolAdapter protocol."""

    def diagnostics(self, *, file_path: str) -> list[dict[str, Any]]:
        return [
            {
                "message": "unused import",
                "line": 2,
                "character": 0,
                "severity": "warning",
                "source": "pylint",
                "file_path": file_path,
            }
        ]

    def symbol_lookup(self, *, symbol_name: str, file_path: str | None) -> list[dict[str, Any]]:
        return [
            {
                "name": symbol_name,
                "kind": "function",
                "line": 10,
                "character": 0,
                "file_path": file_path or "",
            }
        ]

    def hover(self, *, file_path: str, line: int, character: int) -> dict[str, Any] | None:
        return {
            "symbol": "my_func",
            "line": line,
            "character": character,
            "detail": "function my_func defined at 10:0",
        }


class _HoverNoneAdapter:
    """Adapter whose hover returns None (symbol not found at position)."""

    def diagnostics(self, *, file_path: str) -> list[dict[str, Any]]:
        return []

    def symbol_lookup(self, *, symbol_name: str, file_path: str | None) -> list[dict[str, Any]]:
        return []

    def hover(self, *, file_path: str, line: int, character: int) -> dict[str, Any] | None:
        return None


class _EmptyAdapter:
    """Adapter that returns empty/clean results for every operation."""

    def diagnostics(self, *, file_path: str) -> list[dict[str, Any]]:
        return []

    def symbol_lookup(self, *, symbol_name: str, file_path: str | None) -> list[dict[str, Any]]:
        return []

    def hover(self, *, file_path: str, line: int, character: int) -> dict[str, Any] | None:
        return {"symbol": "x", "detail": "variable x"}


# ---------------------------------------------------------------------------
# 1. Typed dataclass smoke tests (WL-109 public contracts)
# ---------------------------------------------------------------------------


def test_diagnostic_dataclass_fields() -> None:
    # @trace WL-109
    d = Diagnostic(
        file_path="/tmp/foo.py",
        line=1,
        character=0,
        severity="error",
        message="syntax error",
        source="pyright",
    )
    assert d.file_path == "/tmp/foo.py"
    assert d.severity == "error"
    assert d.source == "pyright"


def test_diagnostic_dataclass_source_defaults_to_none() -> None:
    # @trace WL-109
    d = Diagnostic(file_path="/tmp/foo.py", line=1, character=0, severity="warning", message="lint")
    assert d.source is None


def test_symbol_info_dataclass_fields() -> None:
    # @trace WL-109
    s = SymbolInfo(name="MyClass", kind="class", file_path="/src/a.py", line=5)
    assert s.name == "MyClass"
    assert s.kind == "class"
    assert s.line == 5


def test_hover_info_dataclass_fields() -> None:
    # @trace WL-109
    h = HoverInfo(contents="int x = 1", range={"start": {"line": 0}, "end": {"line": 0}})
    assert h.contents == "int x = 1"
    assert h.range is not None


def test_hover_info_range_optional() -> None:
    # @trace WL-109
    h = HoverInfo(contents="some docs")
    assert h.range is None


# ---------------------------------------------------------------------------
# 2. _validate_existing_file guard
# ---------------------------------------------------------------------------


def test_validate_existing_file_passes_for_real_file(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "real.py"
    f.write_text("x = 1\n")
    result = _validate_existing_file(str(f))
    assert result.exists()


def test_validate_existing_file_raises_for_missing(tmp_path: Path) -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="File not found"):
        _validate_existing_file(str(tmp_path / "ghost.py"))


def test_validate_existing_file_raises_for_directory(tmp_path: Path) -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="File not found"):
        _validate_existing_file(str(tmp_path))


# ---------------------------------------------------------------------------
# 3. _ensure_position guard
# ---------------------------------------------------------------------------


def test_ensure_position_valid() -> None:
    # @trace WL-109
    line, char = _ensure_position(0, 0)
    assert line == 0
    assert char == 0


def test_ensure_position_rejects_negative_line() -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="line must be >= 0"):
        _ensure_position(-1, 0)


def test_ensure_position_rejects_negative_character() -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="character must be >= 0"):
        _ensure_position(0, -1)


def test_ensure_position_rejects_bool_line() -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="line must be an integer, not bool"):
        _ensure_position(True, 0)


def test_ensure_position_rejects_bool_character() -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="character must be an integer, not bool"):
        _ensure_position(0, False)


# ---------------------------------------------------------------------------
# 4. lsp_diagnostics_impl (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lsp_diagnostics_impl_returns_list(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    result = await lsp_diagnostics_impl(str(f), adapter=_FakeAdapter())
    assert isinstance(result, list)
    assert result[0]["severity"] == "warning"


@pytest.mark.asyncio
async def test_lsp_diagnostics_impl_file_not_found(tmp_path: Path) -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="File not found"):
        await lsp_diagnostics_impl(str(tmp_path / "missing.py"), adapter=_FakeAdapter())


@pytest.mark.asyncio
async def test_lsp_diagnostics_impl_empty_for_clean_file(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "clean.py"
    f.write_text("x = 1\n")
    result = await lsp_diagnostics_impl(str(f), adapter=_EmptyAdapter())
    assert result == []


@pytest.mark.asyncio
async def test_lsp_diagnostics_impl_raises_for_unavailable_backend(
    tmp_path: Path,
) -> None:
    # @trace WL-109 - fail loudly, no silent fallback
    f = tmp_path / "note.txt"
    f.write_text("hello\n")
    with pytest.raises(RuntimeError, match="LSP_BACKEND_UNAVAILABLE"):
        await lsp_diagnostics_impl(str(f))


@pytest.mark.asyncio
async def test_lsp_diagnostics_impl_python_syntax_error_detected(
    tmp_path: Path,
) -> None:
    # @trace WL-109 - default Python AST adapter detects syntax errors
    f = tmp_path / "bad.py"
    f.write_text("def broken(:\n")
    result = await lsp_diagnostics_impl(str(f))
    assert len(result) == 1
    assert result[0]["source"] == "python-compile"
    assert result[0]["severity"] == "error"


@pytest.mark.asyncio
async def test_lsp_diagnostics_impl_returns_source_field(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "b.py"
    f.write_text("x = 1\n")
    result = await lsp_diagnostics_impl(str(f), adapter=_FakeAdapter())
    assert result[0]["source"] == "pylint"


# ---------------------------------------------------------------------------
# 5. lsp_symbol_lookup_impl (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lsp_symbol_lookup_impl_returns_matches(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "module.py"
    f.write_text("def greet():\n    pass\n")
    result = await lsp_symbol_lookup_impl("greet", str(f), adapter=_FakeAdapter())
    assert isinstance(result, list)
    assert result[0]["name"] == "greet"
    assert result[0]["kind"] == "function"


@pytest.mark.asyncio
async def test_lsp_symbol_lookup_impl_rejects_empty_symbol() -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="non-empty"):
        await lsp_symbol_lookup_impl("   ", adapter=_FakeAdapter())


@pytest.mark.asyncio
async def test_lsp_symbol_lookup_impl_none_file_path_allowed() -> None:
    # @trace WL-109 - file_path=None is valid for some adapters
    result = await lsp_symbol_lookup_impl("some_func", None, adapter=_FakeAdapter())
    assert isinstance(result, list)
    assert result[0]["name"] == "some_func"


@pytest.mark.asyncio
async def test_lsp_symbol_lookup_impl_file_not_found(tmp_path: Path) -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="File not found"):
        await lsp_symbol_lookup_impl("func", str(tmp_path / "ghost.py"), adapter=_FakeAdapter())


@pytest.mark.asyncio
async def test_lsp_symbol_lookup_impl_raises_for_unavailable_backend(
    tmp_path: Path,
) -> None:
    # @trace WL-109 - fail loudly for non-Python files
    f = tmp_path / "script.sh"
    f.write_text("echo hello\n")
    with pytest.raises(RuntimeError, match="LSP_BACKEND_UNAVAILABLE"):
        await lsp_symbol_lookup_impl("func", str(f))


@pytest.mark.asyncio
async def test_lsp_symbol_lookup_impl_python_ast_finds_class(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "models.py"
    f.write_text("class UserModel:\n    pass\n")
    result = await lsp_symbol_lookup_impl("UserModel", str(f))
    assert any(m["kind"] == "class" for m in result)


@pytest.mark.asyncio
async def test_lsp_symbol_lookup_impl_empty_result_for_unknown_symbol(
    tmp_path: Path,
) -> None:
    # @trace WL-109
    f = tmp_path / "c.py"
    f.write_text("x = 1\n")
    result = await lsp_symbol_lookup_impl("NonExistentFn", str(f), adapter=_EmptyAdapter())
    assert result == []


# ---------------------------------------------------------------------------
# 6. lsp_hover_impl (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lsp_hover_impl_returns_hover_dict(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "code.py"
    f.write_text("def my_func():\n    pass\n\nmy_func()\n")
    result = await lsp_hover_impl(str(f), 3, 0, adapter=_FakeAdapter())
    assert "file_path" in result
    assert "line" in result
    assert "character" in result
    assert "hover" in result


@pytest.mark.asyncio
async def test_lsp_hover_impl_file_not_found(tmp_path: Path) -> None:
    # @trace WL-109
    with pytest.raises(ValueError, match="File not found"):
        await lsp_hover_impl(str(tmp_path / "missing.py"), 0, 0, adapter=_FakeAdapter())


@pytest.mark.asyncio
async def test_lsp_hover_impl_rejects_negative_line(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "x.py"
    f.write_text("x = 1\n")
    with pytest.raises(ValueError, match="line must be >= 0"):
        await lsp_hover_impl(str(f), -1, 0, adapter=_FakeAdapter())


@pytest.mark.asyncio
async def test_lsp_hover_impl_rejects_negative_character(tmp_path: Path) -> None:
    # @trace WL-109
    f = tmp_path / "x.py"
    f.write_text("x = 1\n")
    with pytest.raises(ValueError, match="character must be >= 0"):
        await lsp_hover_impl(str(f), 0, -1, adapter=_FakeAdapter())


@pytest.mark.asyncio
async def test_lsp_hover_impl_returns_none_hover_when_no_symbol(tmp_path: Path) -> None:
    # @trace WL-109 - hover=None when adapter returns None
    f = tmp_path / "y.py"
    f.write_text("x = 1\n")
    result = await lsp_hover_impl(str(f), 0, 0, adapter=_HoverNoneAdapter())
    assert result["hover"] is None


@pytest.mark.asyncio
async def test_lsp_hover_impl_raises_for_unavailable_backend(tmp_path: Path) -> None:
    # @trace WL-109 - fail loudly
    f = tmp_path / "data.json"
    f.write_text('{"key": 1}\n')
    with pytest.raises(RuntimeError, match="LSP_BACKEND_UNAVAILABLE"):
        await lsp_hover_impl(str(f), 0, 0)


@pytest.mark.asyncio
async def test_lsp_hover_impl_out_of_bounds_line_returns_none_hover(
    tmp_path: Path,
) -> None:
    # @trace WL-109 - line beyond end of file -> hover is None
    f = tmp_path / "small.py"
    f.write_text("x = 1\n")
    result = await lsp_hover_impl(str(f), 999, 0)
    assert result["hover"] is None


# ---------------------------------------------------------------------------
# 7. Dispatch helper integration (tools_workstream_lsp layer)
# ---------------------------------------------------------------------------


def test_lsp_diagnostics_tool_impl_maps_unavailable_error(tmp_path: Path) -> None:
    # @trace WL-109 - dispatch helper wraps errors with remediation
    f = tmp_path / "note.txt"
    f.write_text("hello\n")

    captured: dict[str, str] = {}

    def _error_result(error: str, remediation: str) -> dict[str, str]:
        captured["error"] = error
        captured["remediation"] = remediation
        return captured

    _server_tools_workstream_lsp.lsp_diagnostics_tool_impl(
        file_path=str(f),
        diagnostics_impl=lsp_diagnostics,
        error_result=_error_result,
    )
    assert "LSP_BACKEND_UNAVAILABLE" in captured["error"]
    assert "Configure THGENT_LSP_ADAPTER=python-ast" in captured["remediation"]


def test_lsp_symbol_lookup_tool_impl_maps_empty_symbol_error(tmp_path: Path) -> None:
    # @trace WL-109
    captured: dict[str, str] = {}

    def _error_result(error: str, remediation: str) -> dict[str, str]:
        captured["error"] = error
        captured["remediation"] = remediation
        return captured

    _server_tools_workstream_lsp.lsp_symbol_lookup_tool_impl(
        symbol_name="",
        file_path=None,
        symbol_lookup_impl=lsp_symbol_lookup,
        error_result=_error_result,
    )
    assert "non-empty" in captured["error"]
